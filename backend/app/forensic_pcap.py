"""
Forensic PCAP Analysis Module for TOR Unveil

This module provides advanced flow-level metadata extraction from PCAP files,
including timestamps, packet burst patterns, and directionality analysis.
The extracted evidence integrates into the scoring pipeline to strengthen
or weaken path inference.

Key Features:
- Flow-level metadata extraction (5-tuple flows)
- Packet burst pattern detection
- Directionality analysis (upload vs download)
- Real-time and offline analysis modes
- TOR-specific traffic pattern recognition

Usage:
    from backend.app.forensic_pcap import ForensicPCAPAnalyzer, FlowEvidence
    
    # Offline analysis
    analyzer = ForensicPCAPAnalyzer()
    evidence = analyzer.analyze_pcap(pcap_bytes)
    
    # Real-time analysis
    analyzer = ForensicPCAPAnalyzer(mode="realtime")
    analyzer.add_packet(packet_data, timestamp)
    evidence = analyzer.get_current_evidence()
"""

import struct
import logging
import math
from typing import Dict, List, Optional, Tuple, Any, Iterator
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import hashlib

logger = logging.getLogger("tor_unveil.forensic_pcap")


# ============================================================================
# CONSTANTS
# ============================================================================

# TOR standard ports
TOR_PORTS = {9001, 9030, 9050, 9051, 9150, 443}

# TOR cell sizes (in bytes)
TOR_CELL_SIZE = 512
TOR_CELL_SIZE_TOLERANCE = 50

# Burst detection thresholds
BURST_MIN_PACKETS = 5
BURST_MAX_GAP_MS = 100  # Max inter-arrival time within a burst
BURST_MIN_DURATION_MS = 10

# Analysis mode
class AnalysisMode(Enum):
    OFFLINE = "offline"
    REALTIME = "realtime"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class FlowKey:
    """5-tuple flow identifier"""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: int
    
    def __hash__(self):
        return hash((self.src_ip, self.dst_ip, self.src_port, self.dst_port, self.protocol))
    
    def __eq__(self, other):
        if not isinstance(other, FlowKey):
            return False
        return (self.src_ip == other.src_ip and 
                self.dst_ip == other.dst_ip and
                self.src_port == other.src_port and
                self.dst_port == other.dst_port and
                self.protocol == other.protocol)
    
    def reverse(self) -> "FlowKey":
        """Get reverse flow key"""
        return FlowKey(
            src_ip=self.dst_ip,
            dst_ip=self.src_ip,
            src_port=self.dst_port,
            dst_port=self.src_port,
            protocol=self.protocol
        )
    
    def canonical(self) -> Tuple["FlowKey", bool]:
        """
        Return canonical (sorted) flow key and direction indicator.
        Returns (canonical_key, is_forward) where is_forward=True means
        original direction matches canonical.
        """
        if (self.src_ip, self.src_port) <= (self.dst_ip, self.dst_port):
            return self, True
        return self.reverse(), False


@dataclass
class PacketInfo:
    """Individual packet metadata"""
    timestamp: datetime
    size: int
    direction: int  # 1 = forward (to dst), -1 = reverse (to src)
    tcp_flags: Optional[int] = None
    payload_size: int = 0
    
    @property
    def is_tor_cell_sized(self) -> bool:
        """Check if packet matches TOR cell size pattern"""
        return abs(self.payload_size - TOR_CELL_SIZE) <= TOR_CELL_SIZE_TOLERANCE


@dataclass
class Burst:
    """Packet burst (rapid succession of packets)"""
    start_time: datetime
    end_time: datetime
    packet_count: int
    total_bytes: int
    direction: int  # +1 forward dominant, -1 reverse dominant, 0 mixed
    inter_arrival_times: List[float] = field(default_factory=list)
    
    @property
    def duration_ms(self) -> float:
        """Burst duration in milliseconds"""
        return (self.end_time - self.start_time).total_seconds() * 1000
    
    @property
    def packets_per_second(self) -> float:
        """Packets per second during burst"""
        duration_s = self.duration_ms / 1000
        return self.packet_count / duration_s if duration_s > 0 else 0
    
    @property
    def avg_inter_arrival_ms(self) -> float:
        """Average inter-arrival time in ms"""
        if not self.inter_arrival_times:
            return 0.0
        return sum(self.inter_arrival_times) / len(self.inter_arrival_times)


@dataclass
class FlowStatistics:
    """Comprehensive flow statistics"""
    flow_key: FlowKey
    first_seen: datetime
    last_seen: datetime
    packet_count: int = 0
    byte_count: int = 0
    forward_packets: int = 0
    reverse_packets: int = 0
    forward_bytes: int = 0
    reverse_bytes: int = 0
    bursts: List[Burst] = field(default_factory=list)
    packets: List[PacketInfo] = field(default_factory=list)
    tor_cell_packets: int = 0
    
    @property
    def duration_seconds(self) -> float:
        """Flow duration in seconds"""
        return (self.last_seen - self.first_seen).total_seconds()
    
    @property
    def packets_per_second(self) -> float:
        """Average packets per second"""
        return self.packet_count / self.duration_seconds if self.duration_seconds > 0 else 0
    
    @property
    def bytes_per_second(self) -> float:
        """Average bytes per second"""
        return self.byte_count / self.duration_seconds if self.duration_seconds > 0 else 0
    
    @property
    def directionality_ratio(self) -> float:
        """
        Ratio of forward to total packets.
        0.5 = balanced, >0.5 = more forward, <0.5 = more reverse
        """
        total = self.forward_packets + self.reverse_packets
        return self.forward_packets / total if total > 0 else 0.5
    
    @property
    def tor_cell_ratio(self) -> float:
        """Ratio of TOR cell-sized packets"""
        return self.tor_cell_packets / self.packet_count if self.packet_count > 0 else 0
    
    @property
    def is_likely_tor(self) -> bool:
        """Heuristic: likely TOR traffic based on patterns"""
        # Check port
        port_match = (self.flow_key.src_port in TOR_PORTS or 
                     self.flow_key.dst_port in TOR_PORTS)
        # Check cell size pattern
        cell_match = self.tor_cell_ratio > 0.3
        # Check for bidirectional traffic (TOR circuits are bidirectional)
        bidirectional = 0.2 < self.directionality_ratio < 0.8
        
        return (port_match and cell_match) or (cell_match and bidirectional)


@dataclass
class FlowEvidence:
    """
    Evidence extracted from PCAP for scoring integration.
    
    This structure is designed to plug into the evidence scoring pipeline.
    """
    # Basic metadata
    total_flows: int = 0
    total_packets: int = 0
    total_bytes: int = 0
    capture_duration_seconds: float = 0.0
    
    # TOR-specific metrics
    tor_likely_flows: int = 0
    tor_cell_ratio: float = 0.0
    tor_port_matches: int = 0
    
    # Timing evidence
    first_packet_time: Optional[datetime] = None
    last_packet_time: Optional[datetime] = None
    inter_flow_gaps: List[float] = field(default_factory=list)
    
    # Burst evidence
    total_bursts: int = 0
    avg_burst_size: float = 0.0
    burst_frequency: float = 0.0  # bursts per second
    dominant_burst_direction: int = 0  # +1 upload, -1 download, 0 mixed
    
    # Directionality evidence
    overall_directionality: float = 0.5  # 0.5 = balanced
    upload_bytes: int = 0
    download_bytes: int = 0
    
    # Flow patterns
    unique_source_ips: int = 0
    unique_dest_ips: int = 0
    unique_ports: int = 0
    
    # Confidence indicators
    data_quality: float = 1.0  # 0.0-1.0, degraded if issues
    analysis_completeness: float = 1.0  # 0.0-1.0, lower if truncated
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "total_flows": self.total_flows,
            "total_packets": self.total_packets,
            "total_bytes": self.total_bytes,
            "capture_duration_seconds": round(self.capture_duration_seconds, 3),
            "tor_likely_flows": self.tor_likely_flows,
            "tor_cell_ratio": round(self.tor_cell_ratio, 4),
            "tor_port_matches": self.tor_port_matches,
            "first_packet_time": self.first_packet_time.isoformat() if self.first_packet_time else None,
            "last_packet_time": self.last_packet_time.isoformat() if self.last_packet_time else None,
            "total_bursts": self.total_bursts,
            "avg_burst_size": round(self.avg_burst_size, 2),
            "burst_frequency": round(self.burst_frequency, 4),
            "dominant_burst_direction": self.dominant_burst_direction,
            "overall_directionality": round(self.overall_directionality, 4),
            "upload_bytes": self.upload_bytes,
            "download_bytes": self.download_bytes,
            "unique_source_ips": self.unique_source_ips,
            "unique_dest_ips": self.unique_dest_ips,
            "unique_ports": self.unique_ports,
            "data_quality": round(self.data_quality, 4),
            "analysis_completeness": round(self.analysis_completeness, 4),
        }


# ============================================================================
# MAIN ANALYZER CLASS
# ============================================================================

class ForensicPCAPAnalyzer:
    """
    Advanced PCAP analyzer for forensic evidence extraction.
    
    Supports both offline (complete file) and real-time (streaming) modes.
    """
    
    def __init__(
        self,
        mode: AnalysisMode = AnalysisMode.OFFLINE,
        max_packets: int = 100000,
        max_flows: int = 10000,
    ):
        """
        Initialize forensic PCAP analyzer.
        
        Args:
            mode: Analysis mode (OFFLINE or REALTIME)
            max_packets: Maximum packets to process (prevent memory issues)
            max_flows: Maximum flows to track
        """
        self.mode = mode
        self.max_packets = max_packets
        self.max_flows = max_flows
        
        # Flow tracking
        self.flows: Dict[FlowKey, FlowStatistics] = {}
        self.packet_count = 0
        self.byte_count = 0
        
        # Time tracking
        self.first_packet_time: Optional[datetime] = None
        self.last_packet_time: Optional[datetime] = None
        
        # Real-time mode state
        self._current_burst: Dict[FlowKey, List[PacketInfo]] = defaultdict(list)
        self._last_packet_time: Dict[FlowKey, datetime] = {}
        
        # Analysis results cache
        self._evidence_cache: Optional[FlowEvidence] = None
        self._cache_valid = False
    
    # ========================================================================
    # OFFLINE ANALYSIS
    # ========================================================================
    
    def analyze_pcap(self, pcap_data: bytes) -> FlowEvidence:
        """
        Analyze complete PCAP file (offline mode).
        
        Args:
            pcap_data: Raw PCAP file bytes
            
        Returns:
            FlowEvidence with extracted metrics
        """
        from .pcap_analyzer import PCAPAnalyzer
        
        # Parse PCAP using existing analyzer
        analyzer = PCAPAnalyzer(pcap_data)
        result = analyzer.parse()
        
        if not result.get('success'):
            logger.error(f"PCAP parse failed: {result.get('error')}")
            return FlowEvidence(data_quality=0.0, analysis_completeness=0.0)
        
        # Process parsed packets
        packets = result.get('packets', [])
        total_packets_available = result.get('total_packets', len(packets))
        
        for packet in packets:
            self._process_packet(packet)
            
            if self.packet_count >= self.max_packets:
                logger.warning(f"Reached max packets limit ({self.max_packets})")
                break
        
        # Detect bursts in all flows
        self._detect_all_bursts()
        
        # Calculate analysis completeness
        completeness = len(packets) / total_packets_available if total_packets_available > 0 else 1.0
        
        # Build evidence
        evidence = self._build_evidence()
        evidence.analysis_completeness = completeness
        
        return evidence
    
    def _process_packet(self, packet: Dict[str, Any]) -> None:
        """Process a single parsed packet into flow tracking"""
        # Extract flow key components
        src_ip = packet.get('src_ip')
        dst_ip = packet.get('dst_ip')
        src_port = packet.get('src_port', 0)
        dst_port = packet.get('dst_port', 0)
        protocol = packet.get('protocol', 0)
        
        if not src_ip or not dst_ip:
            return
        
        # Parse timestamp
        timestamp_str = packet.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()
        
        # Update global time tracking
        if self.first_packet_time is None or timestamp < self.first_packet_time:
            self.first_packet_time = timestamp
        if self.last_packet_time is None or timestamp > self.last_packet_time:
            self.last_packet_time = timestamp
        
        # Create flow key and determine direction
        flow_key = FlowKey(src_ip, dst_ip, src_port, dst_port, protocol)
        canonical_key, is_forward = flow_key.canonical()
        
        # Get or create flow
        if len(self.flows) >= self.max_flows and canonical_key not in self.flows:
            return  # Skip if too many flows
        
        if canonical_key not in self.flows:
            self.flows[canonical_key] = FlowStatistics(
                flow_key=canonical_key,
                first_seen=timestamp,
                last_seen=timestamp,
            )
        
        flow = self.flows[canonical_key]
        
        # Create packet info
        size = packet.get('captured_len', 0)
        payload_size = packet.get('original_len', size) - 40  # Rough estimate
        
        packet_info = PacketInfo(
            timestamp=timestamp,
            size=size,
            direction=1 if is_forward else -1,
            payload_size=max(0, payload_size),
        )
        
        # Update flow statistics
        flow.packet_count += 1
        flow.byte_count += size
        flow.last_seen = timestamp
        flow.packets.append(packet_info)
        
        if is_forward:
            flow.forward_packets += 1
            flow.forward_bytes += size
        else:
            flow.reverse_packets += 1
            flow.reverse_bytes += size
        
        if packet_info.is_tor_cell_sized:
            flow.tor_cell_packets += 1
        
        # Update global counters
        self.packet_count += 1
        self.byte_count += size
        
        # Invalidate cache
        self._cache_valid = False
    
    # ========================================================================
    # REAL-TIME ANALYSIS
    # ========================================================================
    
    def add_packet(
        self,
        src_ip: str,
        dst_ip: str,
        src_port: int,
        dst_port: int,
        protocol: int,
        size: int,
        timestamp: Optional[datetime] = None,
        payload_size: Optional[int] = None,
    ) -> None:
        """
        Add a single packet for real-time analysis.
        
        Args:
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port
            dst_port: Destination port
            protocol: IP protocol number
            size: Total packet size
            timestamp: Packet timestamp (defaults to now)
            payload_size: Application layer payload size
        """
        if self.mode != AnalysisMode.REALTIME:
            logger.warning("add_packet called but not in realtime mode")
        
        timestamp = timestamp or datetime.utcnow()
        payload_size = payload_size if payload_size is not None else max(0, size - 40)
        
        # Build packet dict and process
        packet = {
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': src_port,
            'dst_port': dst_port,
            'protocol': protocol,
            'captured_len': size,
            'original_len': size,
            'timestamp': timestamp.isoformat(),
        }
        
        self._process_packet(packet)
        
        # Real-time burst detection
        flow_key = FlowKey(src_ip, dst_ip, src_port, dst_port, protocol)
        canonical_key, is_forward = flow_key.canonical()
        
        self._update_realtime_burst(canonical_key, timestamp, size, 1 if is_forward else -1)
    
    def _update_realtime_burst(
        self,
        flow_key: FlowKey,
        timestamp: datetime,
        size: int,
        direction: int,
    ) -> None:
        """Update real-time burst detection for a flow"""
        last_time = self._last_packet_time.get(flow_key)
        
        if last_time is not None:
            gap_ms = (timestamp - last_time).total_seconds() * 1000
            
            if gap_ms <= BURST_MAX_GAP_MS:
                # Continue current burst
                self._current_burst[flow_key].append(PacketInfo(
                    timestamp=timestamp,
                    size=size,
                    direction=direction,
                ))
            else:
                # End current burst if it meets criteria
                self._finalize_burst(flow_key)
                # Start new burst
                self._current_burst[flow_key] = [PacketInfo(
                    timestamp=timestamp,
                    size=size,
                    direction=direction,
                )]
        else:
            # First packet for this flow
            self._current_burst[flow_key] = [PacketInfo(
                timestamp=timestamp,
                size=size,
                direction=direction,
            )]
        
        self._last_packet_time[flow_key] = timestamp
    
    def _finalize_burst(self, flow_key: FlowKey) -> None:
        """Finalize and record a burst for a flow"""
        burst_packets = self._current_burst.get(flow_key, [])
        
        if len(burst_packets) >= BURST_MIN_PACKETS:
            # Calculate burst statistics
            start_time = burst_packets[0].timestamp
            end_time = burst_packets[-1].timestamp
            duration_ms = (end_time - start_time).total_seconds() * 1000
            
            if duration_ms >= BURST_MIN_DURATION_MS:
                total_bytes = sum(p.size for p in burst_packets)
                
                # Calculate inter-arrival times
                inter_arrivals = []
                for i in range(1, len(burst_packets)):
                    gap = (burst_packets[i].timestamp - burst_packets[i-1].timestamp).total_seconds() * 1000
                    inter_arrivals.append(gap)
                
                # Determine dominant direction
                forward_count = sum(1 for p in burst_packets if p.direction > 0)
                reverse_count = len(burst_packets) - forward_count
                
                if forward_count > reverse_count * 1.5:
                    direction = 1
                elif reverse_count > forward_count * 1.5:
                    direction = -1
                else:
                    direction = 0
                
                burst = Burst(
                    start_time=start_time,
                    end_time=end_time,
                    packet_count=len(burst_packets),
                    total_bytes=total_bytes,
                    direction=direction,
                    inter_arrival_times=inter_arrivals,
                )
                
                # Add to flow
                if flow_key in self.flows:
                    self.flows[flow_key].bursts.append(burst)
        
        # Clear burst buffer
        self._current_burst[flow_key] = []
    
    def get_current_evidence(self) -> FlowEvidence:
        """
        Get current evidence snapshot (for real-time mode).
        
        Returns:
            Current FlowEvidence based on packets processed so far
        """
        # Finalize any pending bursts
        for flow_key in list(self._current_burst.keys()):
            self._finalize_burst(flow_key)
        
        return self._build_evidence()
    
    # ========================================================================
    # BURST DETECTION (OFFLINE)
    # ========================================================================
    
    def _detect_all_bursts(self) -> None:
        """Detect bursts in all flows (offline analysis)"""
        for flow_key, flow in self.flows.items():
            self._detect_flow_bursts(flow)
    
    def _detect_flow_bursts(self, flow: FlowStatistics) -> None:
        """Detect packet bursts within a single flow"""
        if len(flow.packets) < BURST_MIN_PACKETS:
            return
        
        # Sort packets by timestamp
        sorted_packets = sorted(flow.packets, key=lambda p: p.timestamp)
        
        current_burst: List[PacketInfo] = []
        
        for i, packet in enumerate(sorted_packets):
            if not current_burst:
                current_burst.append(packet)
                continue
            
            # Calculate gap from previous packet
            gap_ms = (packet.timestamp - current_burst[-1].timestamp).total_seconds() * 1000
            
            if gap_ms <= BURST_MAX_GAP_MS:
                current_burst.append(packet)
            else:
                # End current burst
                self._record_burst(flow, current_burst)
                current_burst = [packet]
        
        # Handle final burst
        self._record_burst(flow, current_burst)
    
    def _record_burst(self, flow: FlowStatistics, packets: List[PacketInfo]) -> None:
        """Record a burst if it meets criteria"""
        if len(packets) < BURST_MIN_PACKETS:
            return
        
        start_time = packets[0].timestamp
        end_time = packets[-1].timestamp
        duration_ms = (end_time - start_time).total_seconds() * 1000
        
        if duration_ms < BURST_MIN_DURATION_MS:
            return
        
        total_bytes = sum(p.size for p in packets)
        
        # Calculate inter-arrival times
        inter_arrivals = []
        for i in range(1, len(packets)):
            gap = (packets[i].timestamp - packets[i-1].timestamp).total_seconds() * 1000
            inter_arrivals.append(gap)
        
        # Determine dominant direction
        forward_count = sum(1 for p in packets if p.direction > 0)
        reverse_count = len(packets) - forward_count
        
        if forward_count > reverse_count * 1.5:
            direction = 1
        elif reverse_count > forward_count * 1.5:
            direction = -1
        else:
            direction = 0
        
        burst = Burst(
            start_time=start_time,
            end_time=end_time,
            packet_count=len(packets),
            total_bytes=total_bytes,
            direction=direction,
            inter_arrival_times=inter_arrivals,
        )
        
        flow.bursts.append(burst)
    
    # ========================================================================
    # EVIDENCE BUILDING
    # ========================================================================
    
    def _build_evidence(self) -> FlowEvidence:
        """Build FlowEvidence from current state"""
        if self._cache_valid and self._evidence_cache:
            return self._evidence_cache
        
        evidence = FlowEvidence()
        
        # Basic metrics
        evidence.total_flows = len(self.flows)
        evidence.total_packets = self.packet_count
        evidence.total_bytes = self.byte_count
        evidence.first_packet_time = self.first_packet_time
        evidence.last_packet_time = self.last_packet_time
        
        if self.first_packet_time and self.last_packet_time:
            evidence.capture_duration_seconds = (
                self.last_packet_time - self.first_packet_time
            ).total_seconds()
        
        # Aggregate flow statistics
        total_forward = 0
        total_reverse = 0
        total_tor_cells = 0
        total_flow_packets = 0
        all_bursts: List[Burst] = []
        source_ips = set()
        dest_ips = set()
        ports = set()
        
        for flow in self.flows.values():
            total_forward += flow.forward_bytes
            total_reverse += flow.reverse_bytes
            total_tor_cells += flow.tor_cell_packets
            total_flow_packets += flow.packet_count
            all_bursts.extend(flow.bursts)
            
            source_ips.add(flow.flow_key.src_ip)
            dest_ips.add(flow.flow_key.dst_ip)
            ports.add(flow.flow_key.src_port)
            ports.add(flow.flow_key.dst_port)
            
            # Check TOR indicators
            if flow.is_likely_tor:
                evidence.tor_likely_flows += 1
            
            if (flow.flow_key.src_port in TOR_PORTS or 
                flow.flow_key.dst_port in TOR_PORTS):
                evidence.tor_port_matches += 1
        
        # Directionality
        evidence.upload_bytes = total_forward
        evidence.download_bytes = total_reverse
        total_bytes_dir = total_forward + total_reverse
        evidence.overall_directionality = (
            total_forward / total_bytes_dir if total_bytes_dir > 0 else 0.5
        )
        
        # TOR cell ratio
        evidence.tor_cell_ratio = (
            total_tor_cells / total_flow_packets if total_flow_packets > 0 else 0.0
        )
        
        # Burst statistics
        evidence.total_bursts = len(all_bursts)
        if all_bursts:
            evidence.avg_burst_size = (
                sum(b.packet_count for b in all_bursts) / len(all_bursts)
            )
            if evidence.capture_duration_seconds > 0:
                evidence.burst_frequency = (
                    len(all_bursts) / evidence.capture_duration_seconds
                )
            
            # Dominant burst direction
            forward_bursts = sum(1 for b in all_bursts if b.direction > 0)
            reverse_bursts = sum(1 for b in all_bursts if b.direction < 0)
            
            if forward_bursts > reverse_bursts * 1.5:
                evidence.dominant_burst_direction = 1
            elif reverse_bursts > forward_bursts * 1.5:
                evidence.dominant_burst_direction = -1
            else:
                evidence.dominant_burst_direction = 0
        
        # Unique counts
        evidence.unique_source_ips = len(source_ips)
        evidence.unique_dest_ips = len(dest_ips)
        evidence.unique_ports = len(ports)
        
        # Data quality assessment
        evidence.data_quality = self._assess_data_quality()
        
        # Cache result
        self._evidence_cache = evidence
        self._cache_valid = True
        
        return evidence
    
    def _assess_data_quality(self) -> float:
        """Assess quality of captured data (0.0-1.0)"""
        quality = 1.0
        
        # Penalize if too few packets
        if self.packet_count < 10:
            quality *= 0.3
        elif self.packet_count < 100:
            quality *= 0.7
        elif self.packet_count < 1000:
            quality *= 0.9
        
        # Penalize if too few flows
        if len(self.flows) < 1:
            quality *= 0.1
        elif len(self.flows) < 5:
            quality *= 0.6
        
        # Penalize if capture duration too short
        if self.first_packet_time and self.last_packet_time:
            duration = (self.last_packet_time - self.first_packet_time).total_seconds()
            if duration < 1:
                quality *= 0.5
            elif duration < 10:
                quality *= 0.8
        
        return min(1.0, max(0.0, quality))
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_flow_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all tracked flows"""
        summaries = []
        
        for flow_key, flow in self.flows.items():
            summaries.append({
                "src_ip": flow_key.src_ip,
                "dst_ip": flow_key.dst_ip,
                "src_port": flow_key.src_port,
                "dst_port": flow_key.dst_port,
                "protocol": flow_key.protocol,
                "packet_count": flow.packet_count,
                "byte_count": flow.byte_count,
                "duration_seconds": round(flow.duration_seconds, 3),
                "directionality": round(flow.directionality_ratio, 4),
                "burst_count": len(flow.bursts),
                "is_likely_tor": flow.is_likely_tor,
                "tor_cell_ratio": round(flow.tor_cell_ratio, 4),
            })
        
        return sorted(summaries, key=lambda x: x['packet_count'], reverse=True)
    
    def get_burst_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all detected bursts"""
        summaries = []
        
        for flow_key, flow in self.flows.items():
            for i, burst in enumerate(flow.bursts):
                summaries.append({
                    "flow_src": flow_key.src_ip,
                    "flow_dst": flow_key.dst_ip,
                    "burst_index": i,
                    "packet_count": burst.packet_count,
                    "total_bytes": burst.total_bytes,
                    "duration_ms": round(burst.duration_ms, 2),
                    "packets_per_second": round(burst.packets_per_second, 2),
                    "avg_inter_arrival_ms": round(burst.avg_inter_arrival_ms, 3),
                    "direction": burst.direction,
                    "start_time": burst.start_time.isoformat(),
                })
        
        return sorted(summaries, key=lambda x: x['start_time'])
    
    def reset(self) -> None:
        """Reset analyzer state for reuse"""
        self.flows.clear()
        self.packet_count = 0
        self.byte_count = 0
        self.first_packet_time = None
        self.last_packet_time = None
        self._current_burst.clear()
        self._last_packet_time.clear()
        self._evidence_cache = None
        self._cache_valid = False


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def analyze_pcap_forensic(pcap_data: bytes) -> FlowEvidence:
    """
    Convenience function for offline PCAP analysis.
    
    Args:
        pcap_data: Raw PCAP file bytes
        
    Returns:
        FlowEvidence with extracted metrics
    """
    analyzer = ForensicPCAPAnalyzer(mode=AnalysisMode.OFFLINE)
    return analyzer.analyze_pcap(pcap_data)


def create_realtime_analyzer() -> ForensicPCAPAnalyzer:
    """
    Create a real-time PCAP analyzer.
    
    Returns:
        ForensicPCAPAnalyzer configured for real-time analysis
    """
    return ForensicPCAPAnalyzer(mode=AnalysisMode.REALTIME)


def flow_evidence_to_scoring_metrics(evidence: FlowEvidence) -> Dict[str, float]:
    """
    Convert FlowEvidence to scoring metrics for integration.
    
    Returns metrics suitable for use in the evidence scoring pipeline:
    - pcap_tor_likelihood: 0.0-1.0 likelihood traffic is TOR
    - pcap_data_quality: 0.0-1.0 quality of captured data
    - pcap_directionality_balance: 0.0-1.0 (0.5 = balanced)
    - pcap_burst_intensity: 0.0-1.0 normalized burst activity
    - pcap_timing_coverage: 0.0-1.0 based on capture duration
    """
    # TOR likelihood based on multiple indicators
    tor_flow_ratio = (
        evidence.tor_likely_flows / evidence.total_flows 
        if evidence.total_flows > 0 else 0.0
    )
    tor_port_ratio = (
        evidence.tor_port_matches / evidence.total_flows
        if evidence.total_flows > 0 else 0.0
    )
    
    pcap_tor_likelihood = min(1.0, (
        0.4 * evidence.tor_cell_ratio +
        0.3 * tor_flow_ratio +
        0.3 * tor_port_ratio
    ))
    
    # Directionality balance (0.5 = perfectly balanced)
    directionality_balance = 1.0 - abs(evidence.overall_directionality - 0.5) * 2
    
    # Burst intensity (normalized)
    # Expected: 0-10 bursts per second for typical TOR traffic
    burst_intensity = min(1.0, evidence.burst_frequency / 10.0)
    
    # Timing coverage (longer captures = higher confidence)
    # 60 seconds = full coverage, scale down below
    timing_coverage = min(1.0, evidence.capture_duration_seconds / 60.0)
    
    return {
        "pcap_tor_likelihood": round(pcap_tor_likelihood, 4),
        "pcap_data_quality": round(evidence.data_quality, 4),
        "pcap_directionality_balance": round(directionality_balance, 4),
        "pcap_burst_intensity": round(burst_intensity, 4),
        "pcap_timing_coverage": round(timing_coverage, 4),
    }
