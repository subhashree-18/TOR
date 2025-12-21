"""
Unified Probabilistic Confidence Engine for TOR Correlation
============================================================

A comprehensive multi-factor scoring system that correlates TOR guard, middle, 
and exit nodes using:
- Time overlap between exit activity and guard uptime
- Bandwidth similarity
- Historical recurrence of the same guard node
- Geographic/ASN consistency
- Optional PCAP timing evidence

Each factor produces a normalized score (0-1), which are combined using weighted 
aggregation. Confidence evolves over time with new exit observations.

Author: TOR-Unveil Project
Purpose: Forensic correlation for law enforcement (metadata only, no deanonymization)
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import statistics
import math
from enum import Enum

try:
    from .database import get_db
except (ImportError, ModuleNotFoundError):
    # For testing purposes when module is imported directly
    get_db = lambda: None

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

class ConfidenceLevel(Enum):
    """Confidence assessment levels"""
    HIGH = "High"      # >= 0.75
    MEDIUM = "Medium"  # >= 0.50
    LOW = "Low"        # < 0.50


@dataclass
class FactorScore:
    """A single normalized factor score with metadata"""
    name: str
    value: float  # 0.0 to 1.0
    weight: float  # Importance weight (0.0 to 1.0)
    reasoning: str  # Explanation of this factor
    data_points: Dict[str, any] = field(default_factory=dict)  # Supporting data
    
    def validate(self) -> bool:
        """Validate score is in valid range"""
        return 0.0 <= self.value <= 1.0 and 0.0 <= self.weight <= 1.0


@dataclass
class GuardNodeCandidate:
    """A possible guard node with confidence score"""
    guard_fingerprint: str
    guard_nickname: str
    guard_country: str
    guard_bandwidth_mbps: float
    
    # Confidence metrics
    composite_score: float  # 0.0-1.0, final confidence
    confidence_level: ConfidenceLevel
    
    # Factor breakdown
    factors: List[FactorScore]
    
    # Time tracking
    last_updated: datetime
    observation_count: int  # How many times this correlation was confirmed
    
    # Evidence chain
    time_overlap_score: float
    bandwidth_sim_score: float
    historical_recurrence_score: float
    geo_asn_score: float
    pcap_timing_score: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "guard_fingerprint": self.guard_fingerprint,
            "guard_nickname": self.guard_nickname,
            "guard_country": self.guard_country,
            "guard_bandwidth_mbps": self.guard_bandwidth_mbps,
            "composite_score": round(self.composite_score, 4),
            "confidence_level": self.confidence_level.value,
            "factors": [
                {
                    "name": f.name,
                    "value": round(f.value, 4),
                    "weight": round(f.weight, 4),
                    "reasoning": f.reasoning,
                    "data_points": f.data_points
                }
                for f in self.factors
            ],
            "last_updated": self.last_updated.isoformat(),
            "observation_count": self.observation_count,
            "evidence_chain": {
                "time_overlap": round(self.time_overlap_score, 4),
                "bandwidth_similarity": round(self.bandwidth_sim_score, 4),
                "historical_recurrence": round(self.historical_recurrence_score, 4),
                "geo_asn_consistency": round(self.geo_asn_score, 4),
                "pcap_timing": round(self.pcap_timing_score, 4)
            }
        }


@dataclass
class ConfidenceEvolution:
    """Time-series record of confidence for a guard-exit pair"""
    guard_fingerprint: str
    exit_fingerprint: str
    investigation_id: str
    
    # History of observations
    observation_timestamps: List[datetime] = field(default_factory=list)
    confidence_scores: List[float] = field(default_factory=list)
    observations: List[Dict] = field(default_factory=list)
    
    # Aggregate statistics
    observation_count: int = 0
    confidence_trend: float = 0.0  # +1.0 to -1.0 (increasing/decreasing)
    
    def add_observation(self, score: float, evidence: Dict):
        """Add a new observation to the time-series"""
        self.observation_timestamps.append(datetime.utcnow())
        self.confidence_scores.append(score)
        self.observations.append(evidence)
        self.observation_count = len(self.confidence_scores)
        self._compute_trend()
    
    def _compute_trend(self):
        """Compute whether confidence is increasing or decreasing"""
        if len(self.confidence_scores) < 2:
            self.confidence_trend = 0.0
            return
        
        # Simple linear regression slope
        n = len(self.confidence_scores)
        if n < 2:
            self.confidence_trend = 0.0
            return
        
        x = list(range(n))
        y = self.confidence_scores
        
        mean_x = sum(x) / n
        mean_y = sum(y) / n
        
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        if denominator == 0:
            self.confidence_trend = 0.0
        else:
            slope = numerator / denominator
            # Normalize to -1.0 to 1.0
            self.confidence_trend = max(-1.0, min(1.0, slope))
    
    def get_current_confidence(self) -> float:
        """Get most recent confidence score"""
        return self.confidence_scores[-1] if self.confidence_scores else 0.0
    
    def get_average_confidence(self) -> float:
        """Get average confidence across all observations"""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)


# ============================================================================
# FACTOR CALCULATORS (MODULAR & TESTABLE)
# ============================================================================

class TimeOverlapFactor:
    """
    Score based on temporal overlap between exit activity and guard uptime.
    
    If exit is active during time window T, and guard is up during T,
    overlap increases confidence.
    """
    
    @staticmethod
    def calculate(
        exit_activity_window: Tuple[datetime, datetime],
        guard_uptime_windows: List[Tuple[datetime, datetime]],
        guard_first_seen: datetime,
        guard_last_seen: datetime
    ) -> FactorScore:
        """
        Calculate time overlap score.
        
        Args:
            exit_activity_window: (start, end) of observed exit activity
            guard_uptime_windows: List of (start, end) periods when guard was up
            guard_first_seen: When guard was first observed in TOR network
            guard_last_seen: When guard was last observed
        
        Returns:
            FactorScore with normalized value 0.0-1.0
        """
        exit_start, exit_end = exit_activity_window
        exit_duration = (exit_end - exit_start).total_seconds()
        
        if exit_duration <= 0:
            return FactorScore(
                name="Time Overlap",
                value=0.0,
                weight=0.25,
                reasoning="Invalid exit activity window",
                data_points={}
            )
        
        # Calculate overlap with guard uptime periods
        total_overlap_seconds = 0.0
        
        for guard_start, guard_end in guard_uptime_windows:
            # Find intersection
            overlap_start = max(exit_start, guard_start)
            overlap_end = min(exit_end, guard_end)
            
            if overlap_start < overlap_end:
                overlap_duration = (overlap_end - overlap_start).total_seconds()
                total_overlap_seconds += overlap_duration
        
        # Overlap ratio
        overlap_ratio = min(1.0, total_overlap_seconds / exit_duration)
        
        # Check if guard existed during exit window
        guard_existed = guard_first_seen <= exit_end and guard_last_seen >= exit_start
        existence_bonus = 0.2 if guard_existed else -0.2
        
        final_score = max(0.0, min(1.0, overlap_ratio + existence_bonus))
        
        return FactorScore(
            name="Time Overlap",
            value=final_score,
            weight=0.25,
            reasoning=f"Exit window overlap: {overlap_ratio:.1%}, guard existed during: {guard_existed}",
            data_points={
                "exit_duration_sec": exit_duration,
                "overlap_seconds": total_overlap_seconds,
                "overlap_ratio": overlap_ratio,
                "guard_existed_during_exit": guard_existed
            }
        )


class BandwidthSimilarityFactor:
    """
    Score based on similarity between exit and guard bandwidth.
    
    Guards and exits with similar bandwidth profiles are more likely
    to be part of same user's path.
    """
    
    @staticmethod
    def calculate(
        exit_bandwidth_mbps: float,
        guard_bandwidth_mbps: float,
        exit_advertised_bandwidth: float
    ) -> FactorScore:
        """
        Calculate bandwidth similarity score.
        
        Args:
            exit_bandwidth_mbps: Observed exit node bandwidth
            guard_bandwidth_mbps: Guard node bandwidth from TOR directory
            exit_advertised_bandwidth: Exit's advertised bandwidth
        
        Returns:
            FactorScore with normalized value 0.0-1.0
        """
        if guard_bandwidth_mbps <= 0 or exit_bandwidth_mbps <= 0:
            return FactorScore(
                name="Bandwidth Similarity",
                value=0.5,
                weight=0.20,
                reasoning="Missing or invalid bandwidth data",
                data_points={}
            )
        
        # Calculate ratio
        ratio = min(exit_bandwidth_mbps, guard_bandwidth_mbps) / max(exit_bandwidth_mbps, guard_bandwidth_mbps)
        
        # Penalize very different bandwidths
        # If one is 10x larger, ratio is 0.1 - low similarity
        # If within 20%, ratio is 0.8 - high similarity
        
        # Apply curve: similar bandwidths (ratio close to 1.0) get high scores
        # Different bandwidths (ratio close to 0.0) get low scores
        similarity_score = ratio ** 0.5  # Square root to increase sensitivity
        
        # Bonus if exit's advertised bandwidth is similar
        advertised_bonus = 0.1 if abs(exit_advertised_bandwidth - guard_bandwidth_mbps) < (guard_bandwidth_mbps * 0.3) else 0.0
        
        final_score = min(1.0, similarity_score + advertised_bonus)
        
        return FactorScore(
            name="Bandwidth Similarity",
            value=final_score,
            weight=0.20,
            reasoning=f"Exit {exit_bandwidth_mbps}Mbps vs Guard {guard_bandwidth_mbps}Mbps (ratio: {ratio:.2f})",
            data_points={
                "exit_bandwidth_mbps": exit_bandwidth_mbps,
                "guard_bandwidth_mbps": guard_bandwidth_mbps,
                "ratio": ratio,
                "similarity_score": similarity_score
            }
        )


class HistoricalRecurrenceFactor:
    """
    Score based on how often this guard-exit pair has been seen together.
    
    If same guard node repeatedly routes to the same exit node across
    multiple user sessions, recurrence score increases.
    """
    
    @staticmethod
    def calculate(
        guard_exit_co_occurrences: int,
        total_guard_paths: int,
        total_exit_observations: int,
        days_tracking: float
    ) -> FactorScore:
        """
        Calculate historical recurrence score.
        
        Args:
            guard_exit_co_occurrences: Times guard & exit appeared together
            total_guard_paths: Total paths guard has been in
            total_exit_observations: Total times exit was observed
            days_tracking: Days of data available
        
        Returns:
            FactorScore with normalized value 0.0-1.0
        """
        if total_guard_paths == 0 or total_exit_observations == 0:
            return FactorScore(
                name="Historical Recurrence",
                value=0.0,
                weight=0.20,
                reasoning="Insufficient historical data",
                data_points={}
            )
        
        # Probability of seeing this pair by chance
        expected_co_occurrences = (total_guard_paths / 100.0) * (total_exit_observations / 100.0)  # Rough estimate
        
        # Observed vs expected ratio
        if expected_co_occurrences > 0:
            recurrence_ratio = min(1.0, guard_exit_co_occurrences / max(1, expected_co_occurrences))
        else:
            recurrence_ratio = 0.5 if guard_exit_co_occurrences > 0 else 0.0
        
        # Time decay: older observations matter less
        time_decay = 1.0 / (1.0 + (365.0 / max(1, days_tracking)))
        
        final_score = recurrence_ratio * time_decay
        
        return FactorScore(
            name="Historical Recurrence",
            value=final_score,
            weight=0.20,
            reasoning=f"Co-occurrences: {guard_exit_co_occurrences}, expected: {expected_co_occurrences:.1f}, days tracking: {days_tracking:.1f}",
            data_points={
                "co_occurrences": guard_exit_co_occurrences,
                "total_guard_paths": total_guard_paths,
                "total_exit_observations": total_exit_observations,
                "recurrence_ratio": recurrence_ratio,
                "days_tracking": days_tracking,
                "time_decay": time_decay
            }
        )


class GeoASNConsistencyFactor:
    """
    Score based on geographic and ASN (Autonomous System Number) consistency.
    
    If guard and exit are in same country/ASN, they're more likely related.
    If in different countries, they're more diverse (expected in TOR).
    """
    
    @staticmethod
    def calculate(
        guard_country: str,
        exit_country: str,
        guard_asn: Optional[str],
        exit_asn: Optional[str],
        guard_city: Optional[str],
        exit_city: Optional[str]
    ) -> FactorScore:
        """
        Calculate geographic/ASN consistency score.
        
        Args:
            guard_country: Country code of guard
            exit_country: Country code of exit
            guard_asn: ASN of guard provider
            exit_asn: ASN of exit provider
            guard_city: City of guard (optional)
            exit_city: City of exit (optional)
        
        Returns:
            FactorScore with normalized value 0.0-1.0
        """
        if not guard_country or not exit_country:
            return FactorScore(
                name="Geo/ASN Consistency",
                value=0.5,
                weight=0.15,
                reasoning="Missing geographic data",
                data_points={}
            )
        
        score = 0.5  # Start neutral
        reasoning_parts = []
        
        # Same country slightly increases score (some users route domestically)
        if guard_country == exit_country:
            score += 0.1
            reasoning_parts.append(f"Same country ({guard_country})")
        else:
            reasoning_parts.append(f"Different countries (Guard: {guard_country}, Exit: {exit_country})")
        
        # Same ASN increases score (fewer independent providers)
        if guard_asn and exit_asn:
            if guard_asn == exit_asn:
                score += 0.2
                reasoning_parts.append(f"Same ASN ({guard_asn})")
            else:
                reasoning_parts.append(f"Different ASNs")
        
        # Different cities in same country adds some correlation
        if guard_country == exit_country and guard_city and exit_city:
            if guard_city != exit_city:
                score += 0.05
                reasoning_parts.append(f"Different cities in same country")
        
        final_score = max(0.0, min(1.0, score))
        
        return FactorScore(
            name="Geo/ASN Consistency",
            value=final_score,
            weight=0.15,
            reasoning="; ".join(reasoning_parts),
            data_points={
                "guard_country": guard_country,
                "exit_country": exit_country,
                "guard_asn": guard_asn,
                "exit_asn": exit_asn,
                "same_country": guard_country == exit_country,
                "same_asn": guard_asn == exit_asn if guard_asn and exit_asn else None
            }
        )


class PCAPTimingFactor:
    """
    Score based on PCAP timing analysis (inter-packet timing patterns).
    
    If PCAP data is available, timing patterns on guard and exit
    may show correlation.
    """
    
    @staticmethod
    def calculate(
        pcap_data_available: bool,
        inter_packet_timing_correlation: Optional[float] = None,
        packet_size_correlation: Optional[float] = None
    ) -> FactorScore:
        """
        Calculate PCAP timing score.
        
        Args:
            pcap_data_available: Whether PCAP analysis was performed
            inter_packet_timing_correlation: Correlation of IPT between guard and exit (0-1)
            packet_size_correlation: Correlation of packet sizes (0-1)
        
        Returns:
            FactorScore with normalized value 0.0-1.0
        """
        if not pcap_data_available:
            return FactorScore(
                name="PCAP Timing",
                value=0.0,
                weight=0.10,
                reasoning="PCAP data not available",
                data_points={"pcap_available": False}
            )
        
        # If we have timing correlation data, use it
        if inter_packet_timing_correlation is not None:
            ipt_score = max(0.0, min(1.0, inter_packet_timing_correlation))
        else:
            ipt_score = 0.5
        
        if packet_size_correlation is not None:
            ps_score = max(0.0, min(1.0, packet_size_correlation))
        else:
            ps_score = 0.5
        
        # Average the two correlations
        final_score = (ipt_score + ps_score) / 2.0
        
        return FactorScore(
            name="PCAP Timing",
            value=final_score,
            weight=0.10,
            reasoning=f"IPT correlation: {ipt_score:.2f}, Packet size correlation: {ps_score:.2f}",
            data_points={
                "pcap_available": True,
                "ipt_correlation": inter_packet_timing_correlation,
                "packet_size_correlation": packet_size_correlation
            }
        )


# ============================================================================
# WEIGHTED AGGREGATION
# ============================================================================

class ConfidenceAggregator:
    """
    Combines multiple factor scores using weighted aggregation.
    """
    
    @staticmethod
    def aggregate_factors(factors: List[FactorScore]) -> Tuple[float, str]:
        """
        Compute weighted average of factors.
        
        Args:
            factors: List of FactorScore objects
        
        Returns:
            (composite_score, reasoning)
        """
        if not factors:
            return 0.0, "No factors provided"
        
        # Validate all factors
        for factor in factors:
            if not factor.validate():
                logger.warning(f"Invalid factor: {factor.name}")
        
        # Calculate weighted average
        total_weight = sum(f.weight for f in factors)
        
        if total_weight == 0:
            # Fallback to simple average
            return sum(f.value for f in factors) / len(factors), "Equal weighting (no weights specified)"
        
        weighted_sum = sum(f.value * f.weight for f in factors)
        composite = weighted_sum / total_weight
        
        # Clamp to 0.0-1.0
        composite = max(0.0, min(1.0, composite))
        
        # Build reasoning
        factor_details = ", ".join([f"{f.name}: {f.value:.2f}" for f in factors])
        reasoning = f"Weighted aggregation: {factor_details}"
        
        return composite, reasoning
    
    @staticmethod
    def compute_confidence_level(score: float) -> ConfidenceLevel:
        """Map numeric score to confidence level"""
        if score >= 0.75:
            return ConfidenceLevel.HIGH
        elif score >= 0.50:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW


# ============================================================================
# UNIFIED CONFIDENCE ENGINE
# ============================================================================

class UnifiedProbabilisticConfidenceEngine:
    """
    Main engine that orchestrates multi-factor correlation analysis.
    
    Integrates with:
    - TOR relay data fetchers
    - Database models
    - Investigation tracking
    - Time-series confidence history
    """
    
    def __init__(self):
        """Initialize the engine"""
        self.db = get_db()
        self.logger = logging.getLogger(__name__)
    
    def correlate_guard_exit_pair(
        self,
        exit_node: Dict,
        guard_node: Dict,
        investigation_id: str,
        pcap_timing_data: Optional[Dict] = None
    ) -> GuardNodeCandidate:
        """
        Correlate a specific guard-exit pair and compute confidence.
        
        Args:
            exit_node: Exit relay data from TOR directory
            guard_node: Guard relay candidate data
            investigation_id: Investigation case ID
            pcap_timing_data: Optional PCAP analysis results
        
        Returns:
            GuardNodeCandidate with full confidence breakdown
        """
        # Extract data from relay dictionaries
        exit_fingerprint = exit_node.get("fingerprint", "unknown")
        guard_fingerprint = guard_node.get("fingerprint", "unknown")
        guard_nickname = guard_node.get("nickname", "unknown")
        guard_country = guard_node.get("country", "unknown")
        guard_bandwidth_mbps = guard_node.get("bandwidth_mbps", 0.0)
        
        # Calculate each factor
        time_overlap = self._calculate_time_overlap(exit_node, guard_node)
        bandwidth_sim = self._calculate_bandwidth_similarity(exit_node, guard_node)
        historical_recurrence = self._calculate_historical_recurrence(
            exit_fingerprint, guard_fingerprint, investigation_id
        )
        geo_asn = self._calculate_geo_asn(exit_node, guard_node)
        pcap_timing = self._calculate_pcap_timing(pcap_timing_data)
        
        # Collect factors
        factors = [
            time_overlap,
            bandwidth_sim,
            historical_recurrence,
            geo_asn,
            pcap_timing
        ]
        
        # Aggregate to composite score
        composite_score, aggregation_reasoning = ConfidenceAggregator.aggregate_factors(factors)
        confidence_level = ConfidenceAggregator.compute_confidence_level(composite_score)
        
        # Create candidate object
        candidate = GuardNodeCandidate(
            guard_fingerprint=guard_fingerprint,
            guard_nickname=guard_nickname,
            guard_country=guard_country,
            guard_bandwidth_mbps=guard_bandwidth_mbps,
            composite_score=composite_score,
            confidence_level=confidence_level,
            factors=factors,
            last_updated=datetime.utcnow(),
            observation_count=1,
            time_overlap_score=time_overlap.value,
            bandwidth_sim_score=bandwidth_sim.value,
            historical_recurrence_score=historical_recurrence.value,
            geo_asn_score=geo_asn.value,
            pcap_timing_score=pcap_timing.value
        )
        
        # Store in time-series history
        self._store_confidence_evolution(
            guard_fingerprint,
            exit_fingerprint,
            investigation_id,
            composite_score,
            factors
        )
        
        return candidate
    
    def rank_guard_candidates(
        self,
        exit_node: Dict,
        investigation_id: str,
        top_k: int = 5
    ) -> List[GuardNodeCandidate]:
        """
        Rank all possible guard nodes for a given exit observation.
        
        Args:
            exit_node: Observed exit node
            investigation_id: Investigation case ID
            top_k: Return top K candidates
        
        Returns:
            Sorted list of GuardNodeCandidate objects (highest confidence first)
        """
        # Get all known guard nodes from database
        try:
            all_guards = list(self.db.relays.find({"is_guard": True}))
        except Exception as e:
            self.logger.error(f"Failed to fetch guard nodes: {e}")
            return []
        
        if not all_guards:
            self.logger.warning("No guard nodes found in database")
            return []
        
        # Correlate exit with each guard
        candidates = []
        for guard_node in all_guards:
            try:
                candidate = self.correlate_guard_exit_pair(
                    exit_node,
                    guard_node,
                    investigation_id
                )
                candidates.append(candidate)
            except Exception as e:
                self.logger.warning(f"Failed to correlate guard {guard_node.get('nickname')}: {e}")
                continue
        
        # Sort by composite score (descending)
        candidates.sort(key=lambda c: c.composite_score, reverse=True)
        
        return candidates[:top_k]
    
    def _calculate_time_overlap(self, exit_node: Dict, guard_node: Dict) -> FactorScore:
        """Helper to calculate time overlap factor"""
        exit_first = exit_node.get("first_seen")
        exit_last = exit_node.get("last_seen")
        
        if exit_first and exit_last:
            exit_first = self._parse_datetime(exit_first)
            exit_last = self._parse_datetime(exit_last)
            exit_window = (exit_first, exit_last)
        else:
            # Use current time window
            now = datetime.utcnow()
            exit_window = (now - timedelta(hours=1), now)
        
        guard_first = self._parse_datetime(guard_node.get("first_seen"))
        guard_last = self._parse_datetime(guard_node.get("last_seen"))
        guard_windows = [(guard_first, guard_last)] if guard_first and guard_last else []
        
        return TimeOverlapFactor.calculate(
            exit_window,
            guard_windows,
            guard_first or datetime.utcnow(),
            guard_last or datetime.utcnow()
        )
    
    def _calculate_bandwidth_similarity(self, exit_node: Dict, guard_node: Dict) -> FactorScore:
        """Helper to calculate bandwidth similarity factor"""
        exit_bw = exit_node.get("bandwidth_mbps", 1.0)
        guard_bw = guard_node.get("bandwidth_mbps", 1.0)
        exit_advertised = exit_node.get("advertised_bandwidth_mbps", exit_bw)
        
        return BandwidthSimilarityFactor.calculate(
            exit_bw,
            guard_bw,
            exit_advertised
        )
    
    def _calculate_historical_recurrence(
        self,
        exit_fingerprint: str,
        guard_fingerprint: str,
        investigation_id: str
    ) -> FactorScore:
        """Helper to calculate historical recurrence factor"""
        # Query database for historical data
        try:
            co_occur = self.db.path_candidates.count_documents({
                "entry.fingerprint": guard_fingerprint,
                "exit.fingerprint": exit_fingerprint
            })
            guard_total = self.db.path_candidates.count_documents({
                "entry.fingerprint": guard_fingerprint
            })
            exit_total = self.db.path_candidates.count_documents({
                "exit.fingerprint": exit_fingerprint
            })
        except Exception as e:
            self.logger.warning(f"Failed to fetch historical data: {e}")
            co_occur = guard_total = exit_total = 0
        
        # Estimate days of tracking (query database creation time)
        days = 30  # Default to 30 days
        try:
            oldest_doc = self.db.path_candidates.find_one(
                {},
                sort=[("generated_at", 1)]
            )
            if oldest_doc and oldest_doc.get("generated_at"):
                oldest_time = self._parse_datetime(oldest_doc["generated_at"])
                days = max(1, (datetime.utcnow() - oldest_time).days)
        except:
            pass
        
        return HistoricalRecurrenceFactor.calculate(
            co_occur,
            max(1, guard_total),
            max(1, exit_total),
            float(days)
        )
    
    def _calculate_geo_asn(self, exit_node: Dict, guard_node: Dict) -> FactorScore:
        """Helper to calculate geographic/ASN consistency factor"""
        return GeoASNConsistencyFactor.calculate(
            guard_node.get("country", "XX"),
            exit_node.get("country", "XX"),
            guard_node.get("asn"),
            exit_node.get("asn"),
            guard_node.get("city"),
            exit_node.get("city")
        )
    
    def _calculate_pcap_timing(self, pcap_data: Optional[Dict]) -> FactorScore:
        """Helper to calculate PCAP timing factor"""
        if not pcap_data:
            return PCAPTimingFactor.calculate(False)
        
        return PCAPTimingFactor.calculate(
            True,
            pcap_data.get("ipt_correlation"),
            pcap_data.get("packet_size_correlation")
        )
    
    def _store_confidence_evolution(
        self,
        guard_fingerprint: str,
        exit_fingerprint: str,
        investigation_id: str,
        score: float,
        factors: List[FactorScore]
    ):
        """Store confidence score in time-series database"""
        try:
            # Query or create confidence evolution record
            evolution_key = f"{guard_fingerprint}:{exit_fingerprint}:{investigation_id}"
            
            evolution_doc = self.db.confidence_evolution.find_one({
                "guard_fingerprint": guard_fingerprint,
                "exit_fingerprint": exit_fingerprint,
                "investigation_id": investigation_id
            })
            
            if evolution_doc:
                # Update existing
                self.db.confidence_evolution.update_one(
                    {"_id": evolution_doc["_id"]},
                    {
                        "$push": {
                            "observation_timestamps": datetime.utcnow(),
                            "confidence_scores": score,
                            "observations": {
                                "timestamp": datetime.utcnow().isoformat(),
                                "score": score,
                                "factors": [asdict(f) for f in factors]
                            }
                        },
                        "$set": {
                            "last_updated": datetime.utcnow(),
                            "observation_count": evolution_doc.get("observation_count", 0) + 1
                        }
                    }
                )
            else:
                # Create new
                self.db.confidence_evolution.insert_one({
                    "guard_fingerprint": guard_fingerprint,
                    "exit_fingerprint": exit_fingerprint,
                    "investigation_id": investigation_id,
                    "observation_timestamps": [datetime.utcnow()],
                    "confidence_scores": [score],
                    "observation_count": 1,
                    "last_updated": datetime.utcnow(),
                    "observations": [{
                        "timestamp": datetime.utcnow().isoformat(),
                        "score": score,
                        "factors": [asdict(f) for f in factors]
                    }]
                })
        except Exception as e:
            self.logger.warning(f"Failed to store confidence evolution: {e}")
    
    def get_confidence_history(
        self,
        guard_fingerprint: str,
        exit_fingerprint: str,
        investigation_id: str
    ) -> Optional[Dict]:
        """
        Retrieve confidence evolution history for a guard-exit pair.
        
        Returns:
            Dictionary with confidence history and trend analysis
        """
        try:
            evolution = self.db.confidence_evolution.find_one({
                "guard_fingerprint": guard_fingerprint,
                "exit_fingerprint": exit_fingerprint,
                "investigation_id": investigation_id
            })
            
            if not evolution:
                return None
            
            # Remove MongoDB _id field
            evolution.pop("_id", None)
            
            return evolution
        except Exception as e:
            self.logger.error(f"Failed to retrieve confidence history: {e}")
            return None
    
    def _parse_datetime(self, dt_input) -> datetime:
        """Parse datetime from various formats"""
        if isinstance(dt_input, datetime):
            return dt_input
        
        if isinstance(dt_input, str):
            try:
                from dateutil import parser as date_parser
                return date_parser.parse(dt_input)
            except:
                return datetime.utcnow()
        
        return datetime.utcnow()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_confidence_engine() -> UnifiedProbabilisticConfidenceEngine:
    """Factory function to create engine instance"""
    return UnifiedProbabilisticConfidenceEngine()
