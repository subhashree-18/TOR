"""
TOR Traffic Correlation Engine for Forensic Analysis
=====================================================

This module performs PROBABILISTIC FORENSIC CORRELATION between TOR exit traffic
observations and possible entry (guard) nodes using timing and behavioral analysis.

CRITICAL DISCLAIMER:
--------------------
This system performs probabilistic inference based on observable network metadata.
It does NOT deanonymize TOR users. All outputs are correlation hypotheses that
require independent verification and cannot be used as sole evidence for identification.

The correlation scores represent statistical similarity measures, NOT identification
confidence. Multiple hypotheses may be generated for any given observation.

Author: TOR-Unveil Project (TN Police Hackathon 2025)
License: For authorized law enforcement forensic use only
"""

from __future__ import annotations

import uuid
import math
import hashlib
from datetime import datetime, timedelta
from typing import (
    List, Dict, Any, Optional, Tuple, 
    NamedTuple, Protocol, TypeVar, Generic
)
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from abc import ABC, abstractmethod
import statistics
import os

from dateutil import parser as date_parser
from .database import get_db


# =============================================================================
# DATABASE CONNECTION
# =============================================================================

def get_database():
    """Get unified database connection from database module."""
    return get_db()


# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

class CorrelationConfig:
    """
    Configuration parameters for correlation analysis.
    All thresholds are evidence-based and documented.
    """
    # TOR circuit lifetime constraints (RFC-documented)
    MIN_CIRCUIT_LIFETIME_SEC: float = 10.0  # Minimum realistic circuit lifetime
    MAX_CIRCUIT_LIFETIME_SEC: float = 600.0  # 10 minutes - typical maximum
    TYPICAL_CIRCUIT_LIFETIME_SEC: float = 180.0  # 3 minutes - common default
    
    # Timing analysis parameters
    TIMING_WINDOW_TOLERANCE_SEC: float = 2.0  # Network jitter tolerance
    MIN_PACKETS_FOR_TIMING_ANALYSIS: int = 10  # Minimum packets for reliable timing
    
    # Inter-packet timing analysis
    IPT_SIMILARITY_BANDS: int = 20  # Number of histogram bins for IPT comparison
    IPT_MAX_DELAY_MS: float = 5000.0  # Maximum inter-packet delay to consider
    
    # Session overlap thresholds
    MIN_SESSION_OVERLAP_RATIO: float = 0.1  # Minimum overlap to consider correlation
    
    # Evidence weight bounds (not confidence - these are relative weights)
    MAX_EVIDENCE_WEIGHT: float = 1.0
    MIN_EVIDENCE_WEIGHT: float = 0.0


class UncertaintyLevel(Enum):
    """
    Uncertainty classification for correlation hypotheses.
    Higher uncertainty = less reliable correlation.
    """
    VERY_HIGH = auto()  # Multiple confounding factors, minimal evidence
    HIGH = auto()       # Significant uncertainty, partial evidence
    MODERATE = auto()   # Some supporting evidence, notable gaps
    LOW = auto()        # Strong supporting evidence, few gaps
    VERY_LOW = auto()   # Multiple independent evidence sources align


class EvidenceType(Enum):
    """Types of evidence that support or weaken a correlation hypothesis."""
    TIMING_SIMILARITY = "timing_similarity"
    SESSION_OVERLAP = "session_overlap"
    PACKET_PATTERN = "packet_pattern"
    BANDWIDTH_FEASIBILITY = "bandwidth_feasibility"
    CIRCUIT_LIFETIME_PLAUSIBILITY = "circuit_lifetime_plausibility"
    BEHAVIORAL_CONSISTENCY = "behavioral_consistency"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass(frozen=True)
class TimingVector:
    """
    Represents inter-packet timing characteristics of a traffic session.
    Immutable to ensure forensic integrity.
    """
    inter_packet_times_ms: Tuple[float, ...]  # Inter-packet delays in milliseconds
    mean_ipt_ms: float
    std_ipt_ms: float
    median_ipt_ms: float
    min_ipt_ms: float
    max_ipt_ms: float
    packet_count: int
    
    @classmethod
    def from_timestamps(cls, timestamps: List[float]) -> Optional['TimingVector']:
        """
        Construct TimingVector from packet timestamps.
        
        Args:
            timestamps: List of packet arrival times in seconds (epoch)
            
        Returns:
            TimingVector if sufficient data, None otherwise
        """
        if len(timestamps) < CorrelationConfig.MIN_PACKETS_FOR_TIMING_ANALYSIS:
            return None
        
        sorted_ts = sorted(timestamps)
        ipt_ms = tuple(
            (sorted_ts[i+1] - sorted_ts[i]) * 1000.0 
            for i in range(len(sorted_ts) - 1)
        )
        
        if not ipt_ms:
            return None
        
        return cls(
            inter_packet_times_ms=ipt_ms,
            mean_ipt_ms=statistics.mean(ipt_ms),
            std_ipt_ms=statistics.stdev(ipt_ms) if len(ipt_ms) > 1 else 0.0,
            median_ipt_ms=statistics.median(ipt_ms),
            min_ipt_ms=min(ipt_ms),
            max_ipt_ms=max(ipt_ms),
            packet_count=len(timestamps)
        )
    
    @classmethod
    def from_ipt_list(cls, ipt_ms_list: List[float]) -> Optional['TimingVector']:
        """Construct from pre-computed inter-packet times."""
        if len(ipt_ms_list) < CorrelationConfig.MIN_PACKETS_FOR_TIMING_ANALYSIS - 1:
            return None
        
        ipt_tuple = tuple(ipt_ms_list)
        return cls(
            inter_packet_times_ms=ipt_tuple,
            mean_ipt_ms=statistics.mean(ipt_tuple),
            std_ipt_ms=statistics.stdev(ipt_tuple) if len(ipt_tuple) > 1 else 0.0,
            median_ipt_ms=statistics.median(ipt_tuple),
            min_ipt_ms=min(ipt_tuple),
            max_ipt_ms=max(ipt_tuple),
            packet_count=len(ipt_ms_list) + 1
        )
    
    def to_histogram(self, bins: int = None) -> List[float]:
        """
        Convert timing vector to normalized histogram for comparison.
        Uses fixed bins to enable consistent comparisons.
        """
        bins = bins or CorrelationConfig.IPT_SIMILARITY_BANDS
        max_delay = CorrelationConfig.IPT_MAX_DELAY_MS
        bin_width = max_delay / bins
        
        histogram = [0.0] * bins
        for ipt in self.inter_packet_times_ms:
            bin_idx = min(int(ipt / bin_width), bins - 1)
            histogram[bin_idx] += 1
        
        # Normalize
        total = sum(histogram)
        if total > 0:
            histogram = [h / total for h in histogram]
        
        return histogram


@dataclass
class TrafficSession:
    """
    Represents a captured traffic session with timing and behavioral data.
    """
    session_id: str
    start_time: datetime
    end_time: datetime
    packet_count: int
    total_bytes: int
    avg_packet_size: float
    timing_vector: Optional[TimingVector] = None
    source_ip_hash: Optional[str] = None  # Privacy-preserving hash
    destination_port: Optional[int] = None
    protocol: str = "unknown"
    
    @property
    def duration_seconds(self) -> float:
        """Session duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def packets_per_second(self) -> float:
        """Average packet rate."""
        duration = self.duration_seconds
        return self.packet_count / duration if duration > 0 else 0.0
    
    @property
    def bytes_per_second(self) -> float:
        """Average throughput."""
        duration = self.duration_seconds
        return self.total_bytes / duration if duration > 0 else 0.0
    
    def overlaps_with(self, other: 'TrafficSession') -> bool:
        """Check if sessions have temporal overlap."""
        return not (self.end_time < other.start_time or self.start_time > other.end_time)
    
    def overlap_ratio(self, other: 'TrafficSession') -> float:
        """
        Calculate overlap ratio between sessions.
        Returns value between 0 (no overlap) and 1 (complete overlap).
        """
        if not self.overlaps_with(other):
            return 0.0
        
        overlap_start = max(self.start_time, other.start_time)
        overlap_end = min(self.end_time, other.end_time)
        overlap_duration = (overlap_end - overlap_start).total_seconds()
        
        # Normalize by the shorter session
        min_duration = min(self.duration_seconds, other.duration_seconds)
        if min_duration <= 0:
            return 0.0
        
        return min(1.0, overlap_duration / min_duration)


@dataclass
class RelayActivityWindow:
    """
    Represents a guard node's observed activity window.
    """
    relay_fingerprint: str
    relay_nickname: str
    window_start: datetime
    window_end: datetime
    observed_sessions: List[TrafficSession] = field(default_factory=list)
    bandwidth_bytes_per_sec: Optional[float] = None
    flags: List[str] = field(default_factory=list)
    autonomous_system: Optional[str] = None
    country_code: Optional[str] = None
    
    @property
    def is_guard(self) -> bool:
        return "Guard" in self.flags
    
    @property
    def window_duration_seconds(self) -> float:
        return (self.window_end - self.window_start).total_seconds()


@dataclass
class ExitObservation:
    """
    Represents an exit relay traffic observation to correlate.
    """
    observation_id: str
    exit_fingerprint: str
    exit_nickname: str
    observed_session: TrafficSession
    destination_info: Optional[str] = None  # Anonymized destination category
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class EvidenceItem:
    """
    A single piece of evidence supporting or weakening a hypothesis.
    """
    evidence_type: EvidenceType
    description: str
    measured_value: float
    reference_range: Tuple[float, float]  # Expected range for this metric
    weight: float  # Relative importance (0-1), NOT confidence
    supports_hypothesis: bool  # True if evidence supports, False if contradicts
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.evidence_type.value,
            "description": self.description,
            "measured_value": round(self.measured_value, 4),
            "reference_range": [round(r, 4) for r in self.reference_range],
            "weight": round(self.weight, 4),
            "supports_hypothesis": self.supports_hypothesis
        }


@dataclass
class CorrelationHypothesis:
    """
    A correlation hypothesis between exit observation and potential guard node.
    
    IMPORTANT: This represents a HYPOTHESIS, not an identification.
    Multiple hypotheses may exist for any observation.
    """
    hypothesis_id: str
    guard_node_fingerprint: str
    guard_node_nickname: str
    exit_node_fingerprint: str
    exit_node_nickname: str
    timing_similarity_score: float  # Normalized 0-1, higher = more similar
    session_overlap_score: float    # Normalized 0-1, higher = more overlap
    evidence_summary: List[EvidenceItem]
    uncertainty_level: UncertaintyLevel
    circuit_lifetime_estimate_sec: Optional[float] = None
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Forensic metadata
    analysis_method: str = "timing_behavioral_correlation"
    requires_verification: bool = True
    
    _DISCLAIMER: str = field(
        default=(
            "This hypothesis represents probabilistic correlation based on "
            "observable network metadata. It is NOT identification and requires "
            "independent verification. Multiple alternative hypotheses may exist."
        ),
        repr=False
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize hypothesis for API response."""
        return {
            "hypothesis_id": self.hypothesis_id,
            "guard_node_fingerprint": self.guard_node_fingerprint,
            "guard_node_nickname": self.guard_node_nickname,
            "exit_node_fingerprint": self.exit_node_fingerprint,
            "exit_node_nickname": self.exit_node_nickname,
            "timing_similarity_score": round(self.timing_similarity_score, 4),
            "session_overlap_score": round(self.session_overlap_score, 4),
            "evidence_summary": [e.to_dict() for e in self.evidence_summary],
            "uncertainty_level": self.uncertainty_level.name,
            "circuit_lifetime_estimate_sec": (
                round(self.circuit_lifetime_estimate_sec, 2) 
                if self.circuit_lifetime_estimate_sec else None
            ),
            "generated_at": self.generated_at.isoformat() + "Z",
            "analysis_method": self.analysis_method,
            "requires_verification": self.requires_verification,
            "_disclaimer": self._DISCLAIMER
        }
    
    @property
    def combined_evidence_weight(self) -> float:
        """
        Calculate combined evidence weight (NOT confidence).
        This is a measure of evidence strength, not identification certainty.
        """
        if not self.evidence_summary:
            return 0.0
        
        supporting = [e for e in self.evidence_summary if e.supports_hypothesis]
        contradicting = [e for e in self.evidence_summary if not e.supports_hypothesis]
        
        support_weight = sum(e.weight for e in supporting)
        contradict_weight = sum(e.weight for e in contradicting)
        
        total_weight = support_weight + contradict_weight
        if total_weight == 0:
            return 0.0
        
        # Net support ratio
        return (support_weight - contradict_weight) / total_weight


# =============================================================================
# TIMING ANALYSIS ENGINE
# =============================================================================

class TimingSimilarityAnalyzer:
    """
    Analyzes timing similarity between traffic sessions.
    Uses multiple metrics for robust comparison.
    """
    
    @staticmethod
    def histogram_distance(hist1: List[float], hist2: List[float]) -> float:
        """
        Calculate normalized histogram distance (Bhattacharyya distance).
        Returns value between 0 (identical) and 1 (completely different).
        """
        if len(hist1) != len(hist2):
            raise ValueError("Histograms must have same length")
        
        # Bhattacharyya coefficient
        bc = sum(math.sqrt(h1 * h2) for h1, h2 in zip(hist1, hist2))
        
        # Convert to distance (1 - coefficient)
        return 1.0 - bc
    
    @staticmethod
    def statistical_distance(tv1: TimingVector, tv2: TimingVector) -> float:
        """
        Calculate statistical distance between timing vectors.
        Uses multiple statistical moments for comparison.
        """
        # Normalize differences by reasonable scales
        mean_diff = abs(tv1.mean_ipt_ms - tv2.mean_ipt_ms) / max(tv1.mean_ipt_ms, tv2.mean_ipt_ms, 1.0)
        
        std_diff = abs(tv1.std_ipt_ms - tv2.std_ipt_ms) / max(tv1.std_ipt_ms, tv2.std_ipt_ms, 1.0)
        
        median_diff = abs(tv1.median_ipt_ms - tv2.median_ipt_ms) / max(tv1.median_ipt_ms, tv2.median_ipt_ms, 1.0)
        
        # Weighted combination (mean is most reliable)
        distance = 0.5 * mean_diff + 0.3 * std_diff + 0.2 * median_diff
        
        return min(1.0, distance)
    
    @classmethod
    def calculate_similarity(
        cls,
        exit_timing: TimingVector,
        guard_timing: TimingVector
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate timing similarity score between exit and guard timing vectors.
        
        Returns:
            Tuple of (similarity_score, component_scores)
            - similarity_score: 0-1, higher = more similar
            - component_scores: breakdown of individual metrics
        """
        # Histogram-based comparison
        exit_hist = exit_timing.to_histogram()
        guard_hist = guard_timing.to_histogram()
        hist_distance = cls.histogram_distance(exit_hist, guard_hist)
        hist_similarity = 1.0 - hist_distance
        
        # Statistical comparison
        stat_distance = cls.statistical_distance(exit_timing, guard_timing)
        stat_similarity = 1.0 - stat_distance
        
        # Packet rate similarity (within expected TOR relay behavior)
        # TOR adds latency, so guard should have slightly higher packet rate
        rate_ratio = exit_timing.packet_count / max(guard_timing.packet_count, 1)
        # Expect exit to have 0.8-1.0x the packets of guard (some loss expected)
        rate_similarity = 1.0 - min(1.0, abs(rate_ratio - 0.9) / 0.5)
        
        # Combined score (histogram is most reliable for timing patterns)
        combined_similarity = (
            0.5 * hist_similarity +
            0.35 * stat_similarity +
            0.15 * rate_similarity
        )
        
        component_scores = {
            "histogram_similarity": round(hist_similarity, 4),
            "statistical_similarity": round(stat_similarity, 4),
            "packet_rate_similarity": round(rate_similarity, 4)
        }
        
        return round(combined_similarity, 4), component_scores


# =============================================================================
# SESSION OVERLAP ANALYZER
# =============================================================================

class SessionOverlapAnalyzer:
    """
    Analyzes temporal overlap between exit observations and guard activity windows.
    """
    
    @staticmethod
    def calculate_overlap_score(
        exit_session: TrafficSession,
        guard_window: RelayActivityWindow
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate session overlap score.
        
        Returns:
            Tuple of (overlap_score, analysis_details)
        """
        # Create a pseudo-session for the guard window
        guard_pseudo_session = TrafficSession(
            session_id="guard_window",
            start_time=guard_window.window_start,
            end_time=guard_window.window_end,
            packet_count=0,
            total_bytes=0,
            avg_packet_size=0.0
        )
        
        # Basic temporal overlap
        base_overlap = exit_session.overlap_ratio(guard_pseudo_session)
        
        if base_overlap < CorrelationConfig.MIN_SESSION_OVERLAP_RATIO:
            return 0.0, {
                "base_overlap_ratio": round(base_overlap, 4),
                "reason": "insufficient_temporal_overlap"
            }
        
        # Check against guard's observed sessions for more precise matching
        session_match_score = 0.0
        best_matching_session = None
        
        for guard_session in guard_window.observed_sessions:
            session_overlap = exit_session.overlap_ratio(guard_session)
            if session_overlap > session_match_score:
                session_match_score = session_overlap
                best_matching_session = guard_session.session_id
        
        # Combined score
        if session_match_score > 0:
            # Weight session-level matches more heavily
            combined_score = 0.4 * base_overlap + 0.6 * session_match_score
        else:
            # Fall back to window-level overlap only
            combined_score = base_overlap * 0.7  # Discount for lack of session data
        
        analysis_details = {
            "base_overlap_ratio": round(base_overlap, 4),
            "session_match_score": round(session_match_score, 4),
            "best_matching_session_id": best_matching_session,
            "combined_overlap_score": round(combined_score, 4)
        }
        
        return round(combined_score, 4), analysis_details


# =============================================================================
# CIRCUIT LIFETIME ANALYZER
# =============================================================================

class CircuitLifetimeAnalyzer:
    """
    Analyzes whether inferred circuit lifetime is realistic.
    Penalizes correlations requiring unrealistic TOR circuit durations.
    """
    
    @staticmethod
    def estimate_circuit_lifetime(
        exit_session: TrafficSession,
        guard_session: TrafficSession
    ) -> Tuple[float, str]:
        """
        Estimate the implied circuit lifetime for this correlation.
        
        Returns:
            Tuple of (estimated_lifetime_sec, feasibility_assessment)
        """
        # Circuit must have existed from when traffic started at guard
        # to when it ended at exit
        earliest_guard = guard_session.start_time
        latest_exit = exit_session.end_time
        
        implied_lifetime = (latest_exit - earliest_guard).total_seconds()
        
        # Add typical TOR relay processing delays
        implied_lifetime += CorrelationConfig.TIMING_WINDOW_TOLERANCE_SEC * 3
        
        # Assess feasibility
        if implied_lifetime < CorrelationConfig.MIN_CIRCUIT_LIFETIME_SEC:
            feasibility = "implausible_too_short"
        elif implied_lifetime > CorrelationConfig.MAX_CIRCUIT_LIFETIME_SEC:
            feasibility = "implausible_too_long"
        elif implied_lifetime > CorrelationConfig.TYPICAL_CIRCUIT_LIFETIME_SEC:
            feasibility = "plausible_extended"
        else:
            feasibility = "plausible_typical"
        
        return implied_lifetime, feasibility
    
    @staticmethod
    def lifetime_plausibility_weight(
        lifetime_sec: float,
        feasibility: str
    ) -> float:
        """
        Calculate evidence weight based on circuit lifetime plausibility.
        """
        if feasibility == "implausible_too_short":
            return 0.0
        elif feasibility == "implausible_too_long":
            # Exponential decay for very long lifetimes
            excess = lifetime_sec - CorrelationConfig.MAX_CIRCUIT_LIFETIME_SEC
            return max(0.0, 0.3 * math.exp(-excess / 600.0))
        elif feasibility == "plausible_extended":
            # Linear decay from typical to max
            ratio = (lifetime_sec - CorrelationConfig.TYPICAL_CIRCUIT_LIFETIME_SEC) / (
                CorrelationConfig.MAX_CIRCUIT_LIFETIME_SEC - CorrelationConfig.TYPICAL_CIRCUIT_LIFETIME_SEC
            )
            return max(0.5, 1.0 - 0.5 * ratio)
        else:  # plausible_typical
            return 1.0


# =============================================================================
# BANDWIDTH FEASIBILITY ANALYZER
# =============================================================================

class BandwidthFeasibilityAnalyzer:
    """
    Checks whether observed traffic is feasible given relay bandwidth constraints.
    """
    
    @staticmethod
    def assess_feasibility(
        exit_session: TrafficSession,
        guard_bandwidth_bps: Optional[float]
    ) -> Tuple[bool, float, str]:
        """
        Assess whether the exit session traffic is feasible through the guard.
        
        Returns:
            Tuple of (is_feasible, feasibility_score, explanation)
        """
        if guard_bandwidth_bps is None or guard_bandwidth_bps <= 0:
            return True, 0.5, "guard_bandwidth_unknown"
        
        required_bps = exit_session.bytes_per_second
        
        # TOR overhead factor (encryption, cell padding)
        overhead_factor = 1.15
        required_with_overhead = required_bps * overhead_factor
        
        if required_with_overhead > guard_bandwidth_bps:
            ratio = required_with_overhead / guard_bandwidth_bps
            return False, max(0.0, 1.0 - (ratio - 1.0)), "exceeds_guard_bandwidth"
        
        # Score based on utilization (very low utilization is less likely)
        utilization = required_with_overhead / guard_bandwidth_bps
        
        if utilization < 0.001:
            # Very small fraction - could be anything
            score = 0.3
            explanation = "minimal_bandwidth_utilization"
        elif utilization < 0.1:
            score = 0.5 + utilization * 3
            explanation = "low_bandwidth_utilization"
        else:
            score = min(1.0, 0.8 + utilization * 0.2)
            explanation = "reasonable_bandwidth_utilization"
        
        return True, round(score, 4), explanation


# =============================================================================
# UNCERTAINTY CALCULATOR
# =============================================================================

class UncertaintyCalculator:
    """
    Calculates overall uncertainty level for a correlation hypothesis.
    """
    
    @staticmethod
    def calculate(evidence_items: List[EvidenceItem]) -> UncertaintyLevel:
        """
        Determine uncertainty level based on evidence quality and consistency.
        """
        if not evidence_items:
            return UncertaintyLevel.VERY_HIGH
        
        supporting = [e for e in evidence_items if e.supports_hypothesis]
        contradicting = [e for e in evidence_items if not e.supports_hypothesis]
        
        support_weight = sum(e.weight for e in supporting)
        contradict_weight = sum(e.weight for e in contradicting)
        
        # Count evidence types
        evidence_types = set(e.evidence_type for e in evidence_items)
        type_diversity = len(evidence_types)
        
        # Calculate consistency (variance in support/contradict)
        all_weights = [e.weight * (1 if e.supports_hypothesis else -1) for e in evidence_items]
        weight_variance = statistics.variance(all_weights) if len(all_weights) > 1 else 1.0
        
        # Decision logic
        if contradict_weight > support_weight * 1.5:
            return UncertaintyLevel.VERY_HIGH
        
        if type_diversity < 2:
            return UncertaintyLevel.VERY_HIGH
        
        if contradict_weight > support_weight:
            return UncertaintyLevel.HIGH
        
        if type_diversity < 3 or weight_variance > 0.3:
            return UncertaintyLevel.HIGH
        
        if support_weight < 1.5:
            return UncertaintyLevel.MODERATE
        
        if type_diversity >= 4 and support_weight > contradict_weight * 2:
            return UncertaintyLevel.LOW
        
        if type_diversity >= 5 and support_weight > contradict_weight * 3 and weight_variance < 0.1:
            return UncertaintyLevel.VERY_LOW
        
        return UncertaintyLevel.MODERATE


# =============================================================================
# MAIN CORRELATION ENGINE
# =============================================================================

class ForensicCorrelationEngine:
    """
    Main engine for performing forensic correlation analysis.
    
    This engine generates HYPOTHESES, not identifications.
    All outputs require independent verification.
    """
    
    def __init__(self, config: CorrelationConfig = None):
        self.config = config or CorrelationConfig()
        self.timing_analyzer = TimingSimilarityAnalyzer()
        self.overlap_analyzer = SessionOverlapAnalyzer()
        self.lifetime_analyzer = CircuitLifetimeAnalyzer()
        self.bandwidth_analyzer = BandwidthFeasibilityAnalyzer()
        self.uncertainty_calculator = UncertaintyCalculator()
    
    def correlate(
        self,
        exit_observation: ExitObservation,
        guard_activity_windows: List[RelayActivityWindow],
        max_hypotheses: int = 10
    ) -> List[CorrelationHypothesis]:
        """
        Generate correlation hypotheses for an exit observation.
        
        Args:
            exit_observation: The exit traffic observation to correlate
            guard_activity_windows: List of potential guard node activity windows
            max_hypotheses: Maximum number of hypotheses to return
            
        Returns:
            List of CorrelationHypothesis objects, sorted by evidence strength
        """
        hypotheses: List[CorrelationHypothesis] = []
        exit_session = exit_observation.observed_session
        
        for guard_window in guard_activity_windows:
            # Skip if guard is not actually a guard node
            if not guard_window.is_guard:
                continue
            
            # Skip if no temporal overlap possible
            if (guard_window.window_end < exit_session.start_time or
                guard_window.window_start > exit_session.end_time):
                continue
            
            # Collect evidence for this guard
            evidence_items: List[EvidenceItem] = []
            
            # 1. Session overlap analysis
            overlap_score, overlap_details = self.overlap_analyzer.calculate_overlap_score(
                exit_session, guard_window
            )
            
            if overlap_score < self.config.MIN_SESSION_OVERLAP_RATIO:
                continue  # Skip if insufficient overlap
            
            evidence_items.append(EvidenceItem(
                evidence_type=EvidenceType.SESSION_OVERLAP,
                description=f"Session temporal overlap: {overlap_details.get('reason', 'computed')}",
                measured_value=overlap_score,
                reference_range=(0.3, 1.0),
                weight=overlap_score * 0.8,
                supports_hypothesis=overlap_score >= 0.3
            ))
            
            # 2. Timing similarity analysis
            timing_score = 0.0
            timing_components = {}
            
            if exit_session.timing_vector and guard_window.observed_sessions:
                # Find best matching guard session
                best_timing_score = 0.0
                for guard_session in guard_window.observed_sessions:
                    if guard_session.timing_vector:
                        score, components = self.timing_analyzer.calculate_similarity(
                            exit_session.timing_vector,
                            guard_session.timing_vector
                        )
                        if score > best_timing_score:
                            best_timing_score = score
                            timing_components = components
                
                timing_score = best_timing_score
                
                evidence_items.append(EvidenceItem(
                    evidence_type=EvidenceType.TIMING_SIMILARITY,
                    description=f"Inter-packet timing pattern similarity",
                    measured_value=timing_score,
                    reference_range=(0.4, 1.0),
                    weight=timing_score * 0.9,  # Timing is strong evidence
                    supports_hypothesis=timing_score >= 0.4
                ))
            else:
                # No timing data available
                evidence_items.append(EvidenceItem(
                    evidence_type=EvidenceType.TIMING_SIMILARITY,
                    description="Timing data unavailable for comparison",
                    measured_value=0.0,
                    reference_range=(0.4, 1.0),
                    weight=0.1,
                    supports_hypothesis=False
                ))
            
            # 3. Circuit lifetime analysis
            circuit_lifetime = None
            if guard_window.observed_sessions:
                # Use the best overlapping session
                for guard_session in guard_window.observed_sessions:
                    if exit_session.overlaps_with(guard_session):
                        lifetime, feasibility = self.lifetime_analyzer.estimate_circuit_lifetime(
                            exit_session, guard_session
                        )
                        circuit_lifetime = lifetime
                        plausibility_weight = self.lifetime_analyzer.lifetime_plausibility_weight(
                            lifetime, feasibility
                        )
                        
                        evidence_items.append(EvidenceItem(
                            evidence_type=EvidenceType.CIRCUIT_LIFETIME_PLAUSIBILITY,
                            description=f"Implied circuit lifetime: {feasibility}",
                            measured_value=lifetime,
                            reference_range=(
                                self.config.MIN_CIRCUIT_LIFETIME_SEC,
                                self.config.MAX_CIRCUIT_LIFETIME_SEC
                            ),
                            weight=plausibility_weight * 0.7,
                            supports_hypothesis=feasibility.startswith("plausible")
                        ))
                        break
            
            # 4. Bandwidth feasibility
            is_feasible, bw_score, bw_explanation = self.bandwidth_analyzer.assess_feasibility(
                exit_session, guard_window.bandwidth_bytes_per_sec
            )
            
            evidence_items.append(EvidenceItem(
                evidence_type=EvidenceType.BANDWIDTH_FEASIBILITY,
                description=f"Bandwidth feasibility: {bw_explanation}",
                measured_value=bw_score,
                reference_range=(0.5, 1.0),
                weight=bw_score * 0.5,
                supports_hypothesis=is_feasible
            ))
            
            # 5. Behavioral consistency (packet size patterns)
            if guard_window.observed_sessions:
                best_behavioral_match = 0.0
                for guard_session in guard_window.observed_sessions:
                    if guard_session.avg_packet_size > 0 and exit_session.avg_packet_size > 0:
                        # TOR cells are typically 512 bytes, but application data varies
                        size_ratio = min(
                            exit_session.avg_packet_size / guard_session.avg_packet_size,
                            guard_session.avg_packet_size / exit_session.avg_packet_size
                        )
                        best_behavioral_match = max(best_behavioral_match, size_ratio)
                
                if best_behavioral_match > 0:
                    evidence_items.append(EvidenceItem(
                        evidence_type=EvidenceType.BEHAVIORAL_CONSISTENCY,
                        description="Packet size pattern consistency",
                        measured_value=best_behavioral_match,
                        reference_range=(0.3, 1.0),
                        weight=best_behavioral_match * 0.4,
                        supports_hypothesis=best_behavioral_match >= 0.3
                    ))
            
            # Calculate uncertainty level
            uncertainty = self.uncertainty_calculator.calculate(evidence_items)
            
            # Create hypothesis
            hypothesis = CorrelationHypothesis(
                hypothesis_id=str(uuid.uuid4()),
                guard_node_fingerprint=guard_window.relay_fingerprint,
                guard_node_nickname=guard_window.relay_nickname,
                exit_node_fingerprint=exit_observation.exit_fingerprint,
                exit_node_nickname=exit_observation.exit_nickname,
                timing_similarity_score=timing_score,
                session_overlap_score=overlap_score,
                evidence_summary=evidence_items,
                uncertainty_level=uncertainty,
                circuit_lifetime_estimate_sec=circuit_lifetime
            )
            
            hypotheses.append(hypothesis)
        
        # Sort by combined evidence weight (strongest evidence first)
        hypotheses.sort(key=lambda h: h.combined_evidence_weight, reverse=True)
        
        return hypotheses[:max_hypotheses]
    
    def correlate_batch(
        self,
        exit_observations: List[ExitObservation],
        guard_activity_windows: List[RelayActivityWindow],
        max_hypotheses_per_observation: int = 5
    ) -> Dict[str, List[CorrelationHypothesis]]:
        """
        Correlate multiple exit observations.
        
        Returns:
            Dict mapping observation_id to list of hypotheses
        """
        results = {}
        
        for observation in exit_observations:
            hypotheses = self.correlate(
                observation,
                guard_activity_windows,
                max_hypotheses=max_hypotheses_per_observation
            )
            results[observation.observation_id] = hypotheses
        
        return results


# =============================================================================
# DATABASE INTEGRATION HELPERS
# =============================================================================

def parse_datetime(value: Any) -> Optional[datetime]:
    """Parse datetime from various formats."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return date_parser.parse(str(value))
    except Exception:
        return None


def build_guard_activity_window_from_relay(
    relay: Dict[str, Any],
    sessions: List[Dict[str, Any]] = None
) -> RelayActivityWindow:
    """
    Build a RelayActivityWindow from relay document and optional session data.
    """
    first_seen = parse_datetime(relay.get("first_seen"))
    last_seen = parse_datetime(relay.get("last_seen"))
    
    # Default to last 24 hours if no timestamps
    if not first_seen:
        first_seen = datetime.utcnow() - timedelta(days=1)
    if not last_seen:
        last_seen = datetime.utcnow()
    
    # Convert sessions
    traffic_sessions = []
    if sessions:
        for sess in sessions:
            timing_vec = None
            if "inter_packet_times_ms" in sess:
                timing_vec = TimingVector.from_ipt_list(sess["inter_packet_times_ms"])
            
            traffic_sessions.append(TrafficSession(
                session_id=sess.get("session_id", str(uuid.uuid4())),
                start_time=parse_datetime(sess.get("start_time")) or first_seen,
                end_time=parse_datetime(sess.get("end_time")) or last_seen,
                packet_count=sess.get("packet_count", 0),
                total_bytes=sess.get("total_bytes", 0),
                avg_packet_size=sess.get("avg_packet_size", 0.0),
                timing_vector=timing_vec
            ))
    
    return RelayActivityWindow(
        relay_fingerprint=relay.get("fingerprint", "unknown"),
        relay_nickname=relay.get("nickname", "unknown"),
        window_start=first_seen,
        window_end=last_seen,
        observed_sessions=traffic_sessions,
        bandwidth_bytes_per_sec=relay.get("advertised_bandwidth"),
        flags=relay.get("flags", []),
        autonomous_system=relay.get("as"),
        country_code=relay.get("country")
    )


def build_exit_observation_from_pcap_session(
    session_data: Dict[str, Any],
    exit_relay: Dict[str, Any]
) -> ExitObservation:
    """
    Build an ExitObservation from PCAP session data and exit relay info.
    """
    timing_vec = None
    if "inter_packet_times_ms" in session_data:
        timing_vec = TimingVector.from_ipt_list(session_data["inter_packet_times_ms"])
    elif "packet_timestamps" in session_data:
        timing_vec = TimingVector.from_timestamps(session_data["packet_timestamps"])
    
    start_time = parse_datetime(session_data.get("start_time")) or datetime.utcnow()
    end_time = parse_datetime(session_data.get("end_time")) or datetime.utcnow()
    
    traffic_session = TrafficSession(
        session_id=session_data.get("session_id", str(uuid.uuid4())),
        start_time=start_time,
        end_time=end_time,
        packet_count=session_data.get("packet_count", 0),
        total_bytes=session_data.get("total_bytes", 0),
        avg_packet_size=session_data.get("avg_packet_size", 0.0),
        timing_vector=timing_vec,
        destination_port=session_data.get("destination_port"),
        protocol=session_data.get("protocol", "unknown")
    )
    
    return ExitObservation(
        observation_id=str(uuid.uuid4()),
        exit_fingerprint=exit_relay.get("fingerprint", "unknown"),
        exit_nickname=exit_relay.get("nickname", "unknown"),
        observed_session=traffic_session,
        destination_info=session_data.get("destination_category"),
        timestamp=datetime.utcnow()
    )


# =============================================================================
# HIGH-LEVEL API FUNCTIONS
# =============================================================================

def correlate_exit_traffic(
    pcap_sessions: List[Dict[str, Any]],
    exit_relay_info: Dict[str, Any],
    guard_candidates: List[Dict[str, Any]] = None,
    max_hypotheses: int = 10
) -> List[Dict[str, Any]]:
    """
    High-level API for correlating exit traffic with potential guard nodes.
    
    Args:
        pcap_sessions: List of PCAP-derived session data
        exit_relay_info: Exit relay information
        guard_candidates: Optional list of guard relay candidates.
                          If None, fetches from database.
        max_hypotheses: Maximum hypotheses to return
        
    Returns:
        List of correlation hypothesis dictionaries
        
    DISCLAIMER:
        Results are probabilistic hypotheses requiring independent verification.
        This is forensic correlation, NOT identification.
    """
    db = get_database()
    engine = ForensicCorrelationEngine()
    
    # Build exit observations
    exit_observations = [
        build_exit_observation_from_pcap_session(sess, exit_relay_info)
        for sess in pcap_sessions
    ]
    
    # Get guard candidates
    if guard_candidates is None:
        guard_candidates = list(db.relays.find(
            {"is_guard": True, "running": True}
        ).limit(200))
    
    # Build guard activity windows
    guard_windows = [
        build_guard_activity_window_from_relay(relay)
        for relay in guard_candidates
    ]
    
    # Perform correlation
    all_hypotheses = []
    for observation in exit_observations:
        hypotheses = engine.correlate(observation, guard_windows, max_hypotheses)
        all_hypotheses.extend([h.to_dict() for h in hypotheses])
    
    # Sort by combined evidence and return top results
    all_hypotheses.sort(
        key=lambda h: sum(
            e["weight"] * (1 if e["supports_hypothesis"] else -1)
            for e in h["evidence_summary"]
        ),
        reverse=True
    )
    
    return all_hypotheses[:max_hypotheses]


def store_correlation_results(
    hypotheses: List[Dict[str, Any]],
    investigation_id: str = None
) -> str:
    """
    Store correlation results in database for forensic record.
    
    Returns:
        The investigation ID
    """
    db = get_database()
    
    if investigation_id is None:
        investigation_id = str(uuid.uuid4())
    
    record = {
        "investigation_id": investigation_id,
        "hypotheses": hypotheses,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "hypothesis_count": len(hypotheses),
        "_disclaimer": (
            "These results are probabilistic forensic correlations, "
            "NOT identifications. Independent verification required."
        )
    }
    
    db.correlation_results.insert_one(record)
    
    return investigation_id


def get_correlation_results(investigation_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve stored correlation results."""
    db = get_database()
    result = db.correlation_results.find_one(
        {"investigation_id": investigation_id},
        {"_id": 0}
    )
    return result


# =============================================================================
# LEGACY COMPATIBILITY LAYER
# =============================================================================

def generate_candidate_paths() -> List[Dict[str, Any]]:
    """
    Legacy function for backward compatibility.
    Returns path candidates in the old format.
    
    DEPRECATED: Use correlate_exit_traffic() for new implementations.
    """
    db = get_database()
    
    # Fetch relays
    guards = list(db.relays.find(
        {"is_guard": True, "running": True}
    ).sort("advertised_bandwidth", -1).limit(50))
    
    middles = list(db.relays.find(
        {"is_guard": False, "is_exit": False, "running": True}
    ).sort("advertised_bandwidth", -1).limit(100))
    
    exits = list(db.relays.find(
        {"is_exit": True, "running": True}
    ).sort("advertised_bandwidth", -1).limit(50))
    
    candidates = []
    
    for g in guards[:30]:
        for m in middles[:30]:
            if g["fingerprint"] == m["fingerprint"]:
                continue
            
            for x in exits[:20]:
                if x["fingerprint"] in {g["fingerprint"], m["fingerprint"]}:
                    continue
                
                candidate = {
                    "id": str(uuid.uuid4()),
                    "entry": g["fingerprint"],
                    "middle": m["fingerprint"],
                    "exit": x["fingerprint"],
                    "entry_nickname": g.get("nickname", "unknown"),
                    "middle_nickname": m.get("nickname", "unknown"),
                    "exit_nickname": x.get("nickname", "unknown"),
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                    "_notice": "Legacy format - use correlation API for forensic analysis"
                }
                candidates.append(candidate)
                
                if len(candidates) >= 500:
                    break
            if len(candidates) >= 500:
                break
        if len(candidates) >= 500:
            break
    
    # Store for compatibility
    if candidates:
        db.path_candidates.delete_many({})
        db.path_candidates.insert_many(candidates)
    
    return candidates


def top_candidate_paths(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Legacy function for backward compatibility.
    
    DEPRECATED: Use get_correlation_results() for new implementations.
    """
    db = get_database()
    return list(db.path_candidates.find({}, {"_id": 0}).limit(limit))


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Configuration
    "CorrelationConfig",
    "UncertaintyLevel",
    "EvidenceType",
    
    # Data structures
    "TimingVector",
    "TrafficSession",
    "RelayActivityWindow",
    "ExitObservation",
    "EvidenceItem",
    "CorrelationHypothesis",
    
    # Analyzers
    "TimingSimilarityAnalyzer",
    "SessionOverlapAnalyzer",
    "CircuitLifetimeAnalyzer",
    "BandwidthFeasibilityAnalyzer",
    "UncertaintyCalculator",
    
    # Main engine
    "ForensicCorrelationEngine",
    
    # High-level API
    "correlate_exit_traffic",
    "store_correlation_results",
    "get_correlation_results",
    
    # Helper functions
    "build_guard_activity_window_from_relay",
    "build_exit_observation_from_pcap_session",
    
    # Legacy compatibility
    "generate_candidate_paths",
    "top_candidate_paths",
]
