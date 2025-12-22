"""
TOR Behavior Signature Library
Behavioral pattern detection and classification for TOR sessions.

Classifies TOR activity into behavioral categories based on:
- Packet timing patterns
- Session duration
- Request frequency
- Protocol usage
- Traffic symmetry

Supports law enforcement behavioral analysis and session fingerprinting.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Tuple, Optional, Any
from datetime import datetime, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)


class BehaviorType(Enum):
    """Classification of TOR behavioral patterns."""
    EMAIL = "email"                    # Email/messaging protocols
    INTERACTIVE_BROWSING = "browsing"  # Real-time web browsing
    AUTOMATED_BOT = "automated"        # Bot/automated traffic
    DARK_WEB_SERVICE = "dark_web"      # Hidden service access
    STREAMING = "streaming"             # Video/media streaming
    FILE_TRANSFER = "file_transfer"     # Large data transfers
    UNKNOWN = "unknown"                 # Unclassifiable


class PacketPattern(Enum):
    """Packet timing patterns."""
    BURSTY = "bursty"              # Irregular bursts (user clicks)
    CONSTANT = "constant"          # Regular intervals (automated)
    STREAMING = "streaming"        # Continuous flow
    BIDIRECTIONAL = "bidirectional"  # Balanced send/receive
    UNIDIRECTIONAL = "unidirectional"  # One-way dominant


@dataclass
class TimingMetrics:
    """Packet timing statistics for a session."""
    inter_packet_times: List[float] = field(default_factory=list)  # ms between packets
    mean_iat: float = 0.0  # Mean inter-arrival time
    std_dev_iat: float = 0.0  # Standard deviation
    min_iat: float = 0.0  # Minimum gap
    max_iat: float = 0.0  # Maximum gap
    coefficient_variation: float = 0.0  # std_dev / mean
    
    def calculate(self) -> None:
        """Calculate timing statistics from inter-packet times."""
        if len(self.inter_packet_times) < 2:
            return
        
        self.mean_iat = statistics.mean(self.inter_packet_times)
        self.min_iat = min(self.inter_packet_times)
        self.max_iat = max(self.inter_packet_times)
        
        if len(self.inter_packet_times) > 1:
            self.std_dev_iat = statistics.stdev(self.inter_packet_times)
            if self.mean_iat > 0:
                self.coefficient_variation = self.std_dev_iat / self.mean_iat


@dataclass
class TrafficMetrics:
    """Traffic volume and characteristics."""
    total_packets: int = 0
    total_bytes: int = 0
    uplink_packets: int = 0
    downlink_packets: int = 0
    uplink_bytes: int = 0
    downlink_bytes: int = 0
    
    def get_symmetry_ratio(self) -> float:
        """Calculate traffic symmetry (0-1, 0.5 = balanced)."""
        if self.total_bytes == 0:
            return 0.0
        min_bytes = min(self.uplink_bytes, self.downlink_bytes)
        max_bytes = max(self.uplink_bytes, self.downlink_bytes)
        if max_bytes == 0:
            return 0.0
        return min_bytes / max_bytes
    
    def get_packet_rate(self, duration_ms: float) -> float:
        """Calculate packets per second."""
        if duration_ms == 0:
            return 0.0
        return (self.total_packets * 1000.0) / duration_ms
    
    def get_throughput_mbps(self, duration_ms: float) -> float:
        """Calculate throughput in Mbps."""
        if duration_ms == 0:
            return 0.0
        return (self.total_bytes * 8.0 * 1000.0) / (duration_ms * 1_000_000.0)


@dataclass
class BehaviorSignature:
    """Complete behavioral signature for a TOR session."""
    session_id: str
    case_id: str
    behavior_type: BehaviorType
    confidence: float  # 0.0-1.0
    
    # Timing analysis
    timing_metrics: TimingMetrics = field(default_factory=TimingMetrics)
    packet_pattern: PacketPattern = PacketPattern.UNKNOWN
    
    # Traffic analysis
    traffic_metrics: TrafficMetrics = field(default_factory=TrafficMetrics)
    duration_ms: float = 0.0
    
    # Protocol analysis
    protocols: List[str] = field(default_factory=list)
    dominant_protocol: Optional[str] = None
    
    # Behavioral indicators
    indicators: Dict[str, float] = field(default_factory=dict)  # Indicator name -> score
    reason: str = ""
    
    # Metadata
    detected_at: datetime = field(default_factory=datetime.utcnow)
    signature_version: str = "1.0"


class BehaviorSignatureLibrary:
    """
    Library for detecting and classifying TOR behavioral signatures.
    
    Analyzes session characteristics to determine user behavior type,
    providing forensic evidence for investigative purposes.
    """
    
    def __init__(self, db: Optional[Any] = None):
        self.db = db
        self.collection_name = "behavior_signatures"
    
    def _calculate_timing_pattern(self, timing: TimingMetrics) -> Tuple[PacketPattern, float]:
        """
        Determine packet timing pattern and confidence.
        
        Bursty: High variation (user clicks) - CV > 1.0
        Constant: Low variation (automated) - CV < 0.5
        Streaming: Regular intervals - CV 0.3-0.6
        """
        cv = timing.coefficient_variation
        
        if cv > 1.5:
            return PacketPattern.BURSTY, 0.9
        elif cv < 0.4:
            return PacketPattern.CONSTANT, 0.85
        elif 0.3 < cv < 0.7:
            return PacketPattern.STREAMING, 0.8
        else:
            return PacketPattern.UNKNOWN, 0.5
    
    def _calculate_symmetry_pattern(self, traffic: TrafficMetrics) -> Tuple[PacketPattern, float]:
        """Determine if traffic is directional or bidirectional."""
        symmetry = traffic.get_symmetry_ratio()
        
        if symmetry > 0.7:  # Balanced
            return PacketPattern.BIDIRECTIONAL, 0.85
        elif symmetry < 0.3:  # Skewed
            return PacketPattern.UNIDIRECTIONAL, 0.8
        else:
            return PacketPattern.BIDIRECTIONAL, 0.6
    
    def _detect_email_signature(self, signature: BehaviorSignature) -> float:
        """
        Detect email/messaging behavior.
        
        Indicators:
        - Bursty packet pattern (user actions)
        - Medium packet rate (50-500 pps)
        - TCP/TLS protocol
        - Periodic check-ins
        """
        score = 0.0
        indicators = {}
        
        # Pattern check
        if signature.packet_pattern == PacketPattern.BURSTY:
            score += 0.3
            indicators["bursty_pattern"] = 0.3
        
        # Packet rate (50-500 pps for email)
        packet_rate = signature.traffic_metrics.get_packet_rate(signature.duration_ms)
        if 50 < packet_rate < 500:
            score += 0.25
            indicators["typical_email_rate"] = 0.25
        
        # Protocol check (SMTP, IMAP, POP3)
        email_protocols = {"smtp", "imap", "pop3", "tls"}
        if signature.dominant_protocol and signature.dominant_protocol.lower() in email_protocols:
            score += 0.25
            indicators["email_protocol"] = 0.25
        
        # Duration pattern (short sessions, multiple daily)
        if 60_000 < signature.duration_ms < 600_000:  # 1-10 minutes
            score += 0.2
            indicators["email_duration"] = 0.2
        
        signature.indicators = indicators
        return min(score, 1.0)
    
    def _detect_browsing_signature(self, signature: BehaviorSignature) -> float:
        """
        Detect interactive web browsing behavior.
        
        Indicators:
        - Very bursty pattern (user clicks)
        - Variable packet rate
        - HTTP/HTTPS protocol
        - Long session duration
        - Bidirectional traffic
        """
        score = 0.0
        indicators = {}
        
        # Pattern check
        if signature.packet_pattern == PacketPattern.BURSTY:
            score += 0.25
            indicators["bursty_pattern"] = 0.25
        
        # Protocol check (HTTP/HTTPS)
        if signature.dominant_protocol and signature.dominant_protocol.lower() in {"http", "https"}:
            score += 0.3
            indicators["http_protocol"] = 0.3
        
        # Session duration (typically 30min-2hrs)
        if 1_800_000 < signature.duration_ms < 7_200_000:
            score += 0.2
            indicators["browsing_duration"] = 0.2
        
        # Bidirectional traffic
        symmetry = signature.traffic_metrics.get_symmetry_ratio()
        if 0.4 < symmetry < 0.9:
            score += 0.25
            indicators["bidirectional_traffic"] = 0.25
        
        signature.indicators = indicators
        return min(score, 1.0)
    
    def _detect_bot_signature(self, signature: BehaviorSignature) -> float:
        """
        Detect automated bot/crawler behavior.
        
        Indicators:
        - Constant packet pattern (regular intervals)
        - High packet rate (1000+ pps)
        - Very low timing variation (CV < 0.2)
        - Unidirectional traffic
        - Consistent protocol
        """
        score = 0.0
        indicators = {}
        
        # Pattern check
        if signature.packet_pattern == PacketPattern.CONSTANT:
            score += 0.35
            indicators["constant_pattern"] = 0.35
        
        # Timing regularity
        if signature.timing_metrics.coefficient_variation < 0.2:
            score += 0.25
            indicators["high_timing_regularity"] = 0.25
        
        # Packet rate (high for bots)
        packet_rate = signature.traffic_metrics.get_packet_rate(signature.duration_ms)
        if packet_rate > 1000:
            score += 0.2
            indicators["high_packet_rate"] = 0.2
        
        # Unidirectional or scanning pattern
        symmetry = signature.traffic_metrics.get_symmetry_ratio()
        if symmetry < 0.3:
            score += 0.2
            indicators["unidirectional_traffic"] = 0.2
        
        signature.indicators = indicators
        return min(score, 1.0)
    
    def _detect_dark_web_signature(self, signature: BehaviorSignature) -> float:
        """
        Detect dark web service access (hidden service).
        
        Indicators:
        - Connection to onion address (port 80/443 to hidden service)
        - Consistent connection pattern
        - Medium traffic volume
        - Long session duration
        - Specific timing characteristics
        """
        score = 0.0
        indicators = {}
        
        # Check for .onion characteristics (would be in protocol/domain)
        if signature.dominant_protocol and ".onion" in signature.dominant_protocol:
            score += 0.4
            indicators["onion_service"] = 0.4
        
        # Session duration (can be long for service hosting)
        if signature.duration_ms > 600_000:  # >10 minutes
            score += 0.2
            indicators["long_duration"] = 0.2
        
        # Pattern consistency
        if signature.packet_pattern == PacketPattern.CONSTANT:
            score += 0.2
            indicators["consistent_pattern"] = 0.2
        
        # Traffic volume (moderate for services)
        throughput = signature.traffic_metrics.get_throughput_mbps(signature.duration_ms)
        if 0.1 < throughput < 10.0:
            score += 0.2
            indicators["typical_service_throughput"] = 0.2
        
        signature.indicators = indicators
        return min(score, 1.0)
    
    def classify_session(
        self,
        session_id: str,
        case_id: str,
        packets: List[Dict],  # List of packet dicts with timestamp, size, direction
        protocols: List[str] = None
    ) -> BehaviorSignature:
        """
        Classify a TOR session behavioral signature.
        
        Args:
            session_id: Unique session identifier
            case_id: Associated investigation case ID
            packets: List of packet data with timing and size info
            protocols: Detected protocols used in session
        
        Returns:
            BehaviorSignature with classification and confidence
        """
        signature = BehaviorSignature(
            session_id=session_id,
            case_id=case_id,
            behavior_type=BehaviorType.UNKNOWN,
            confidence=0.0,
            protocols=protocols or []
        )
        
        if not packets:
            signature.reason = "No packet data available"
            return signature
        
        # Calculate timing metrics
        timing_data = []
        total_duration = 0
        for i in range(1, len(packets)):
            prev_ts = packets[i-1].get("timestamp", 0)
            curr_ts = packets[i].get("timestamp", 0)
            if curr_ts > prev_ts:
                gap = (curr_ts - prev_ts) * 1000  # Convert to ms
                timing_data.append(gap)
        
        signature.timing_metrics.inter_packet_times = timing_data
        signature.timing_metrics.calculate()
        
        # Determine timing pattern
        timing_pattern, timing_conf = self._calculate_timing_pattern(signature.timing_metrics)
        signature.packet_pattern = timing_pattern
        
        # Calculate traffic metrics
        signature.duration_ms = (packets[-1].get("timestamp", 0) - packets[0].get("timestamp", 0)) * 1000
        
        for packet in packets:
            size = packet.get("size", 0)
            direction = packet.get("direction", "down")  # "up" or "down"
            
            signature.traffic_metrics.total_packets += 1
            signature.traffic_metrics.total_bytes += size
            
            if direction.lower() == "up":
                signature.traffic_metrics.uplink_packets += 1
                signature.traffic_metrics.uplink_bytes += size
            else:
                signature.traffic_metrics.downlink_packets += 1
                signature.traffic_metrics.downlink_bytes += size
        
        # Determine symmetry pattern
        symmetry_pattern, _ = self._calculate_symmetry_pattern(signature.traffic_metrics)
        
        # Set dominant protocol
        if signature.protocols:
            signature.dominant_protocol = max(signature.protocols, key=str)
        
        # Classify behavior
        scores = {
            BehaviorType.EMAIL: self._detect_email_signature(signature),
            BehaviorType.INTERACTIVE_BROWSING: self._detect_browsing_signature(signature),
            BehaviorType.AUTOMATED_BOT: self._detect_bot_signature(signature),
            BehaviorType.DARK_WEB_SERVICE: self._detect_dark_web_signature(signature),
        }
        
        # Find best match
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # Only classify if confidence > 0.4
        if best_score > 0.4:
            signature.behavior_type = best_type
            signature.confidence = best_score
            signature.reason = f"Matched {best_type.value} signature with {best_score:.1%} confidence"
        else:
            signature.behavior_type = BehaviorType.UNKNOWN
            signature.confidence = max(scores.values())
            signature.reason = "No behavior signature matched with sufficient confidence"
        
        return signature
    
    def store_signature(self, signature: BehaviorSignature) -> bool:
        """Store behavior signature in MongoDB."""
        if self.db is None:
            return False
        
        try:
            sig_dict = {
                "session_id": signature.session_id,
                "case_id": signature.case_id,
                "behavior_type": signature.behavior_type.value,
                "confidence": signature.confidence,
                "timing_metrics": {
                    "mean_iat": signature.timing_metrics.mean_iat,
                    "std_dev_iat": signature.timing_metrics.std_dev_iat,
                    "coefficient_variation": signature.timing_metrics.coefficient_variation,
                },
                "traffic_metrics": {
                    "total_packets": signature.traffic_metrics.total_packets,
                    "total_bytes": signature.traffic_metrics.total_bytes,
                    "symmetry_ratio": signature.traffic_metrics.get_symmetry_ratio(),
                },
                "packet_pattern": signature.packet_pattern.value,
                "duration_ms": signature.duration_ms,
                "protocols": signature.protocols,
                "indicators": signature.indicators,
                "reason": signature.reason,
                "detected_at": signature.detected_at,
            }
            
            self.db[self.collection_name].insert_one(sig_dict)
            logger.info(f"Stored behavior signature for session {signature.session_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing behavior signature: {e}")
            return False
    
    def get_signature(self, session_id: str) -> Optional[BehaviorSignature]:
        """Retrieve stored behavior signature."""
        if self.db is None:
            return None
        
        try:
            sig_doc = self.db[self.collection_name].find_one({"session_id": session_id})
            if not sig_doc:
                return None
            
            # Reconstruct BehaviorSignature from document
            timing = TimingMetrics(
                mean_iat=sig_doc.get("timing_metrics", {}).get("mean_iat", 0),
                std_dev_iat=sig_doc.get("timing_metrics", {}).get("std_dev_iat", 0),
                coefficient_variation=sig_doc.get("timing_metrics", {}).get("coefficient_variation", 0),
            )
            
            traffic = TrafficMetrics(
                total_packets=sig_doc.get("traffic_metrics", {}).get("total_packets", 0),
                total_bytes=sig_doc.get("traffic_metrics", {}).get("total_bytes", 0),
            )
            
            signature = BehaviorSignature(
                session_id=sig_doc.get("session_id", ""),
                case_id=sig_doc.get("case_id", ""),
                behavior_type=BehaviorType(sig_doc.get("behavior_type", "unknown")),
                confidence=sig_doc.get("confidence", 0),
                timing_metrics=timing,
                packet_pattern=PacketPattern(sig_doc.get("packet_pattern", "unknown")),
                traffic_metrics=traffic,
                duration_ms=sig_doc.get("duration_ms", 0),
                protocols=sig_doc.get("protocols", []),
                indicators=sig_doc.get("indicators", {}),
                reason=sig_doc.get("reason", ""),
            )
            return signature
        except Exception as e:
            logger.error(f"Error retrieving behavior signature: {e}")
            return None
    
    def get_case_behaviors(self, case_id: str) -> List[BehaviorSignature]:
        """Retrieve all behavior signatures for a case."""
        if self.db is None:
            return []
        
        try:
            signatures = []
            cursor = self.db[self.collection_name].find({"case_id": case_id})
            for doc in cursor:
                timing = TimingMetrics(
                    mean_iat=doc.get("timing_metrics", {}).get("mean_iat", 0),
                    std_dev_iat=doc.get("timing_metrics", {}).get("std_dev_iat", 0),
                )
                
                signature = BehaviorSignature(
                    session_id=doc.get("session_id", ""),
                    case_id=case_id,
                    behavior_type=BehaviorType(doc.get("behavior_type", "unknown")),
                    confidence=doc.get("confidence", 0),
                    timing_metrics=timing,
                    reason=doc.get("reason", ""),
                )
                signatures.append(signature)
            
            return signatures
        except Exception as e:
            logger.error(f"Error retrieving case behaviors: {e}")
            return []


# Singleton instance
_behavior_library = None


def get_behavior_signature_library(db: Optional[Any] = None) -> 'BehaviorSignatureLibrary':
    """Get or create singleton instance of behavior signature library."""
    global _behavior_library
    if _behavior_library is None:
        _behavior_library = BehaviorSignatureLibrary(db)
    return _behavior_library
