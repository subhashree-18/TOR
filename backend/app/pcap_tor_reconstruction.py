"""
PCAP-to-TOR Session Reconstruction (Forensic Layer)

This module implements forensic PCAP processing to extract TOR-like traffic patterns
and reconstruct probable TOR sessions. It uses:

1. Packet Burst Timing Analysis
   - TOR uses fixed-size cells (~514 bytes) in bursts
   - Analyze inter-packet timing patterns

2. TLS Record Size Patterns
   - TLS typically uses fixed record sizes (16KB)
   - Extract record boundaries from TCP streams

3. Directional Packet Symmetry
   - TOR maintains consistent upload/download ratios
   - Bidirectional flow analysis

4. Fingerprint Generation
   - Create session signatures from traffic patterns
   - Enable correlation with known relay timelines
"""

import logging
import struct
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, BinaryIO
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class TrafficDirection(Enum):
    """Direction of network traffic."""
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class TORLikeTrafficPattern(Enum):
    """Identified TOR-like traffic patterns."""
    FIXED_SIZE_CELLS = "FIXED_SIZE_CELLS"          # ~514 byte packets
    BURST_TIMING = "BURST_TIMING"                   # Regular packet bursts
    TLS_RECORD_PATTERNS = "TLS_RECORD_PATTERNS"     # TLS record structure
    SYMMETRIC_FLOW = "SYMMETRIC_FLOW"               # Bidirectional symmetry
    ONION_ROUTING_SIGNATURE = "ONION_ROUTING_SIGNATURE"  # Multi-layer pattern


@dataclass
class PCAPPacket:
    """Represents a single network packet from PCAP."""
    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str  # TCP, UDP, etc.
    payload_size: int
    direction: TrafficDirection
    is_tls: bool = False
    tls_version: Optional[str] = None
    tcp_flags: Optional[str] = None


@dataclass
class TORSessionFingerprint:
    """Fingerprint of a probable TOR session extracted from PCAP."""
    fingerprint_hash: str  # SHA256 hash of normalized pattern
    session_id: str  # Unique session identifier
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    packet_count: int
    total_bytes: int
    upstream_bytes: int
    downstream_bytes: int
    patterns_detected: List[str]  # Detected TOR-like patterns
    burst_count: int  # Number of packet bursts
    burst_intervals: List[float]  # Intervals between bursts (milliseconds)
    tls_records_detected: int
    guard_candidate_ips: List[str]  # Likely guard node IPs
    exit_candidate_ips: List[str]   # Likely exit node IPs
    confidence_score: float  # 0.0-1.0 how TOR-like is this session
    notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to MongoDB-compatible dictionary."""
        return {
            "fingerprint_hash": self.fingerprint_hash,
            "session_id": self.session_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration_seconds,
            "packet_count": self.packet_count,
            "total_bytes": self.total_bytes,
            "upstream_bytes": self.upstream_bytes,
            "downstream_bytes": self.downstream_bytes,
            "patterns_detected": self.patterns_detected,
            "burst_count": self.burst_count,
            "burst_intervals": self.burst_intervals,
            "tls_records_detected": self.tls_records_detected,
            "guard_candidate_ips": self.guard_candidate_ips,
            "exit_candidate_ips": self.exit_candidate_ips,
            "confidence_score": self.confidence_score,
            "notes": self.notes,
            "indexed_at": datetime.utcnow()
        }


@dataclass
class PCAPMetadata:
    """Metadata about a PCAP file and its analysis."""
    case_id: str
    file_name: str
    file_size: int
    upload_timestamp: datetime
    capture_start: datetime
    capture_end: datetime
    total_packets: int
    tor_like_sessions: int
    metadata_storage_id: str = ""
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to MongoDB-compatible dictionary."""
        return {
            "case_id": self.case_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "upload_timestamp": self.upload_timestamp,
            "capture_start": self.capture_start,
            "capture_end": self.capture_end,
            "total_packets": self.total_packets,
            "tor_like_sessions": self.tor_like_sessions,
            "analysis_timestamp": self.analysis_timestamp,
            "notes": self.notes
        }


class PCAPTORReconstruction:
    """Reconstructs probable TOR sessions from PCAP files."""
    
    # TOR cell size is typically 514 bytes (header + payload)
    TOR_CELL_SIZE = 514
    TOR_CELL_TOLERANCE = 50  # Allow 50 byte variance
    
    # Typical TOR burst timing (milliseconds)
    TOR_BURST_MIN_INTERVAL = 10
    TOR_BURST_MAX_INTERVAL = 200
    
    # TLS record size patterns
    TLS_RECORD_SIZE = 16384  # 16KB typical
    
    def __init__(self, db=None):
        """Initialize PCAP reconstruction with MongoDB connection."""
        self.db = db
        self._init_collections()
    
    def _init_collections(self):
        """Initialize MongoDB collections for PCAP analysis."""
        if self.db is None:
            logger.warning("Database not initialized for PCAP reconstruction")
            return
        
        try:
            # Create PCAP session collection
            if "pcap_tor_sessions" not in self.db.list_collection_names():
                self.db.create_collection("pcap_tor_sessions")
            
            sessions_collection = self.db["pcap_tor_sessions"]
            sessions_collection.create_index([("case_id", ASCENDING)])
            sessions_collection.create_index([("fingerprint_hash", ASCENDING)], unique=True)
            sessions_collection.create_index([("confidence_score", DESCENDING)])
            sessions_collection.create_index([("start_time", DESCENDING)])
            
            # Create PCAP metadata collection
            if "pcap_metadata" not in self.db.list_collection_names():
                self.db.create_collection("pcap_metadata")
            
            metadata_collection = self.db["pcap_metadata"]
            metadata_collection.create_index([("case_id", ASCENDING)])
            metadata_collection.create_index([("upload_timestamp", DESCENDING)])
            metadata_collection.create_index([("file_name", ASCENDING)])
            
            logger.info("PCAP collections initialized with indexes")
        except PyMongoError as e:
            logger.error(f"Error initializing PCAP collections: {e}")
    
    def detect_fixed_size_cells(self, packets: List[PCAPPacket]) -> Tuple[bool, float]:
        """
        Detect TOR-like fixed-size cell patterns.
        
        Returns: (detected, confidence_score)
        """
        if not packets:
            return False, 0.0
        
        # Count packets near TOR cell size
        tor_like_count = 0
        for packet in packets:
            if (self.TOR_CELL_SIZE - self.TOR_CELL_TOLERANCE <= 
                packet.payload_size <= 
                self.TOR_CELL_SIZE + self.TOR_CELL_TOLERANCE):
                tor_like_count += 1
        
        # If >30% of packets are near TOR cell size, likely TOR
        ratio = tor_like_count / len(packets)
        detected = ratio > 0.3
        confidence = min(1.0, ratio)
        
        return detected, confidence
    
    def detect_burst_timing(self, packets: List[PCAPPacket]) -> Tuple[bool, float, List[float]]:
        """
        Detect TOR-like burst timing patterns.
        
        TOR creates regular bursts of fixed-size cells.
        Returns: (detected, confidence_score, burst_intervals)
        """
        if len(packets) < 5:
            return False, 0.0, []
        
        # Calculate inter-packet intervals
        intervals = []
        for i in range(1, len(packets)):
            delta = (packets[i].timestamp - packets[i-1].timestamp).total_seconds() * 1000
            intervals.append(delta)
        
        # Count intervals in TOR burst range
        burst_like = sum(1 for i in intervals 
                        if self.TOR_BURST_MIN_INTERVAL <= i <= self.TOR_BURST_MAX_INTERVAL)
        
        ratio = burst_like / len(intervals) if intervals else 0
        detected = ratio > 0.4  # >40% of intervals in burst range
        
        return detected, min(1.0, ratio), intervals
    
    def detect_tls_records(self, packets: List[PCAPPacket]) -> Tuple[bool, float]:
        """
        Detect TLS record size patterns common in TOR.
        
        Returns: (detected, confidence_score)
        """
        tls_like_count = sum(1 for p in packets if p.is_tls)
        if not packets:
            return False, 0.0
        
        detected = tls_like_count > 0
        confidence = min(1.0, tls_like_count / len(packets))
        
        return detected, confidence
    
    def detect_symmetric_flow(self, packets: List[PCAPPacket]) -> Tuple[bool, float]:
        """
        Detect bidirectional symmetric packet flow.
        
        TOR maintains relatively balanced upstream/downstream traffic.
        Returns: (detected, confidence_score)
        """
        upstream = sum(p.payload_size for p in packets 
                      if p.direction == TrafficDirection.OUTBOUND)
        downstream = sum(p.payload_size for p in packets 
                        if p.direction == TrafficDirection.INBOUND)
        
        if upstream + downstream == 0:
            return False, 0.0
        
        # Calculate ratio (should be close to 0.5 for symmetric flow)
        ratio = upstream / (upstream + downstream) if (upstream + downstream) > 0 else 0.5
        symmetry = 1.0 - abs(ratio - 0.5) * 2  # 0.0-1.0, closer to 0.5 = better
        
        detected = symmetry > 0.6  # Reasonably balanced
        
        return detected, symmetry
    
    def extract_candidate_ips(
        self,
        packets: List[PCAPPacket],
        suspected_direction: str = "guard"  # "guard" or "exit"
    ) -> List[str]:
        """
        Extract candidate IP addresses for guard or exit nodes.
        
        Guard candidates: sources of inbound connections
        Exit candidates: destinations of outbound connections
        """
        candidates = set()
        
        if suspected_direction == "guard":
            # Guard nodes typically receive outbound connections
            for packet in packets:
                if packet.direction == TrafficDirection.OUTBOUND:
                    candidates.add(packet.dst_ip)
        else:  # exit
            # Exit nodes are typically destinations of traffic
            for packet in packets:
                if packet.direction == TrafficDirection.OUTBOUND:
                    candidates.add(packet.dst_ip)
        
        return list(candidates)
    
    def generate_session_fingerprint(
        self,
        session_packets: List[PCAPPacket],
        case_id: str
    ) -> TORSessionFingerprint:
        """
        Generate fingerprint for a probable TOR session.
        
        Fingerprint includes:
        - Normalized traffic pattern
        - Session characteristics
        - Detected patterns
        - IP candidates
        """
        if not session_packets:
            raise ValueError("No packets provided for fingerprint generation")
        
        # Sort packets by timestamp
        session_packets.sort(key=lambda p: p.timestamp)
        
        # Calculate basic metrics
        start_time = session_packets[0].timestamp
        end_time = session_packets[-1].timestamp
        duration = (end_time - start_time).total_seconds()
        packet_count = len(session_packets)
        
        total_bytes = sum(p.payload_size for p in session_packets)
        upstream_bytes = sum(p.payload_size for p in session_packets 
                            if p.direction == TrafficDirection.OUTBOUND)
        downstream_bytes = sum(p.payload_size for p in session_packets 
                              if p.direction == TrafficDirection.INBOUND)
        
        # Detect TOR-like patterns
        patterns_detected = []
        pattern_scores = {}
        
        # Check each pattern
        fixed_size_detected, fixed_size_conf = self.detect_fixed_size_cells(session_packets)
        if fixed_size_detected:
            patterns_detected.append(TORLikeTrafficPattern.FIXED_SIZE_CELLS.value)
            pattern_scores["fixed_size"] = fixed_size_conf
        
        burst_detected, burst_conf, burst_intervals = self.detect_burst_timing(session_packets)
        if burst_detected:
            patterns_detected.append(TORLikeTrafficPattern.BURST_TIMING.value)
            pattern_scores["burst"] = burst_conf
        
        tls_detected, tls_conf = self.detect_tls_records(session_packets)
        if tls_detected:
            patterns_detected.append(TORLikeTrafficPattern.TLS_RECORD_PATTERNS.value)
            pattern_scores["tls"] = tls_conf
        
        symmetric_detected, symmetric_conf = self.detect_symmetric_flow(session_packets)
        if symmetric_detected:
            patterns_detected.append(TORLikeTrafficPattern.SYMMETRIC_FLOW.value)
            pattern_scores["symmetric"] = symmetric_conf
        
        # Calculate overall TOR-like confidence
        if pattern_scores:
            confidence_score = sum(pattern_scores.values()) / len(pattern_scores)
        else:
            confidence_score = 0.0
        
        # Extract candidate IPs
        guard_candidates = self.extract_candidate_ips(session_packets, "guard")
        exit_candidates = self.extract_candidate_ips(session_packets, "exit")
        
        # Generate fingerprint hash
        fingerprint_data = (
            f"{packet_count}_{int(duration)}_{total_bytes}_"
            f"{len(patterns_detected)}_{'_'.join(sorted(patterns_detected))}"
        )
        fingerprint_hash = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        
        # Create session ID
        session_id = f"{case_id}_{start_time.isoformat()}_{fingerprint_hash[:8]}"
        
        return TORSessionFingerprint(
            fingerprint_hash=fingerprint_hash,
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            packet_count=packet_count,
            total_bytes=total_bytes,
            upstream_bytes=upstream_bytes,
            downstream_bytes=downstream_bytes,
            patterns_detected=patterns_detected,
            burst_count=len(burst_intervals) if burst_intervals else 0,
            burst_intervals=burst_intervals if burst_intervals else [],
            tls_records_detected=sum(1 for p in session_packets if p.is_tls),
            guard_candidate_ips=guard_candidates,
            exit_candidate_ips=exit_candidates,
            confidence_score=round(confidence_score, 4)
        )
    
    def store_session_fingerprint(
        self,
        fingerprint: TORSessionFingerprint,
        case_id: str
    ) -> bool:
        """Store extracted session fingerprint in MongoDB."""
        try:
            collection = self.db["pcap_tor_sessions"]
            collection.insert_one(fingerprint.to_dict())
            logger.info(f"Stored TOR session fingerprint: {fingerprint.session_id}")
            return True
        except PyMongoError as e:
            logger.error(f"Error storing session fingerprint: {e}")
            return False
    
    def store_pcap_metadata(
        self,
        metadata: PCAPMetadata
    ) -> str:
        """Store PCAP file metadata and return storage ID."""
        try:
            collection = self.db["pcap_metadata"]
            result = collection.insert_one(metadata.to_dict())
            storage_id = str(result.inserted_id)
            logger.info(f"Stored PCAP metadata: {storage_id}")
            return storage_id
        except PyMongoError as e:
            logger.error(f"Error storing PCAP metadata: {e}")
            return ""
    
    def get_tor_sessions_for_case(self, case_id: str) -> List[TORSessionFingerprint]:
        """Retrieve all TOR-like sessions extracted from a case."""
        try:
            collection = self.db["pcap_tor_sessions"]
            docs = collection.find({"case_id": case_id}).sort("confidence_score", DESCENDING)
            return [self._doc_to_fingerprint(doc) for doc in docs]
        except PyMongoError as e:
            logger.error(f"Error retrieving TOR sessions: {e}")
            return []
    
    def get_high_confidence_sessions(self, min_confidence: float = 0.7) -> List[TORSessionFingerprint]:
        """Get high-confidence TOR-like sessions."""
        try:
            collection = self.db["pcap_tor_sessions"]
            docs = collection.find(
                {"confidence_score": {"$gte": min_confidence}}
            ).sort("confidence_score", DESCENDING)
            return [self._doc_to_fingerprint(doc) for doc in docs]
        except PyMongoError as e:
            logger.error(f"Error retrieving high-confidence sessions: {e}")
            return []
    
    @staticmethod
    def _doc_to_fingerprint(doc: Dict) -> TORSessionFingerprint:
        """Convert MongoDB document to TORSessionFingerprint."""
        return TORSessionFingerprint(
            fingerprint_hash=doc.get("fingerprint_hash", ""),
            session_id=doc.get("session_id", ""),
            start_time=doc.get("start_time", datetime.utcnow()),
            end_time=doc.get("end_time", datetime.utcnow()),
            duration_seconds=doc.get("duration_seconds", 0.0),
            packet_count=doc.get("packet_count", 0),
            total_bytes=doc.get("total_bytes", 0),
            upstream_bytes=doc.get("upstream_bytes", 0),
            downstream_bytes=doc.get("downstream_bytes", 0),
            patterns_detected=doc.get("patterns_detected", []),
            burst_count=doc.get("burst_count", 0),
            burst_intervals=doc.get("burst_intervals", []),
            tls_records_detected=doc.get("tls_records_detected", 0),
            guard_candidate_ips=doc.get("guard_candidate_ips", []),
            exit_candidate_ips=doc.get("exit_candidate_ips", []),
            confidence_score=doc.get("confidence_score", 0.0),
            notes=doc.get("notes", "")
        )
    
    def get_pcap_statistics(self, case_id: str) -> Dict:
        """Get statistics about PCAP analysis for a case."""
        try:
            sessions = self.get_tor_sessions_for_case(case_id)
            if not sessions:
                return {"total_sessions": 0, "average_confidence": 0.0}
            
            confidence_scores = [s.confidence_score for s in sessions]
            
            return {
                "total_sessions": len(sessions),
                "average_confidence": round(sum(confidence_scores) / len(confidence_scores), 4),
                "high_confidence_count": sum(1 for s in sessions if s.confidence_score >= 0.7),
                "total_extracted_packets": sum(s.packet_count for s in sessions),
                "total_extracted_bytes": sum(s.total_bytes for s in sessions),
                "patterns_summary": self._count_patterns(sessions)
            }
        except Exception as e:
            logger.error(f"Error getting PCAP statistics: {e}")
            return {}
    
    @staticmethod
    def _count_patterns(sessions: List[TORSessionFingerprint]) -> Dict[str, int]:
        """Count pattern occurrences across all sessions."""
        pattern_counts = {}
        for session in sessions:
            for pattern in session.patterns_detected:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        return pattern_counts


# Singleton instance
_pcap_instance: Optional[PCAPTORReconstruction] = None


def get_pcap_system(db=None) -> PCAPTORReconstruction:
    """Get or create PCAP reconstruction system instance."""
    global _pcap_instance
    if _pcap_instance is None or db is not None:
        _pcap_instance = PCAPTORReconstruction(db)
    return _pcap_instance


def init_pcap_system(db) -> PCAPTORReconstruction:
    """Initialize PCAP system with database connection."""
    global _pcap_instance
    _pcap_instance = PCAPTORReconstruction(db)
    return _pcap_instance
