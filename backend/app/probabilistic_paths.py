# backend/app/probabilistic_paths.py
"""
Probabilistic Path Inference Module

This module provides structured probabilistic inference results for TOR path
analysis, integrating Bayesian inference, derived confidence, and evidence
metrics into a frontend-ready format.

Key Features:
1. Entry-node posterior probabilities via Bayesian inference
2. Derived confidence from ConfidenceCalculator
3. Evidence metric breakdowns for visualization
4. Ranked entry candidates with supporting data

Usage:
    from backend.app.probabilistic_paths import (
        generate_probabilistic_paths,
        ProbabilisticPathResult,
    )
    
    results = generate_probabilistic_paths(
        guards=guards_list,
        middles=middles_list,
        exits=exits_list,
        top_k=50,
    )
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
import logging
import math
from collections import defaultdict

from .scoring.bayes_inference import (
    BayesianEntryInference,
    RelayInfo,
    create_relay_info,
)
from .scoring.confidence_calculator import (
    ConfidenceCalculator,
    EvidenceMetrics,
)
from .scoring.evidence import (
    time_overlap_score,
    traffic_similarity_score,
    relay_stability_score,
    path_consistency_score,
    geo_plausibility_score,
)
from .scoring.confidence_evolution import (
    ConfidenceEvolutionTracker,
    InvestigationConfidenceManager,
    ConfidenceChangeReason,
    ConfidenceTrend,
    ConfidenceSnapshot,
    ConfidenceTimeline,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class EvidenceBreakdown:
    """
    Breakdown of contributing evidence metrics for frontend visualization.
    
    Each metric is normalized to 0.0-1.0 and includes human-readable labels.
    """
    time_overlap: float
    time_overlap_label: str
    
    traffic_similarity: float
    traffic_similarity_label: str
    
    stability: float
    stability_label: str
    
    path_consistency: float
    path_consistency_label: str
    
    geo_plausibility: float
    geo_plausibility_label: str
    
    # Aggregate scores
    weighted_average: float
    min_score: float
    consistency_score: float  # How consistent evidence is across metrics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @staticmethod
    def score_to_label(score: float) -> str:
        """Convert numeric score to human-readable label"""
        if score >= 0.9:
            return "very_strong"
        elif score >= 0.75:
            return "strong"
        elif score >= 0.6:
            return "moderate"
        elif score >= 0.4:
            return "weak"
        elif score >= 0.2:
            return "very_weak"
        else:
            return "insufficient"


@dataclass
class EntryNodeInference:
    """
    Probabilistic inference result for a single entry node candidate.
    
    Contains posterior probability, derived confidence, and evidence breakdown.
    """
    fingerprint: str
    nickname: str
    
    # Bayesian inference
    prior_probability: float
    posterior_probability: float
    likelihood_ratio: float  # posterior / prior
    
    # Derived confidence
    confidence: float
    confidence_level: str  # "very_high", "high", "medium", "low", "very_low"
    
    # Evidence breakdown
    evidence: EvidenceBreakdown
    
    # Relay metadata
    country: str
    autonomous_system: str
    bandwidth_mbps: float
    uptime_days: float
    flags: List[str]
    is_guard: bool
    
    # Observation metadata
    observation_count: int
    exit_nodes_observed_with: List[str]
    
    # Ranking
    rank: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = asdict(self)
        result["evidence"] = self.evidence.to_dict()
        return result


@dataclass
class PathInferenceResult:
    """
    Complete path with entry inference and path-level components.
    """
    path_id: str
    
    # Entry inference
    entry: EntryNodeInference
    
    # Middle and exit node info (simplified)
    middle: Dict[str, Any]
    exit: Dict[str, Any]
    
    # Path-level analysis
    path_components: Dict[str, Any]
    
    # Overall path plausibility
    path_plausibility: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "path_id": self.path_id,
            "entry": self.entry.to_dict(),
            "middle": self.middle,
            "exit": self.exit,
            "path_components": self.path_components,
            "path_plausibility": self.path_plausibility,
        }


@dataclass
class ProbabilisticPathResult:
    """
    Complete response structure for probabilistic path inference.
    
    Designed for frontend visualization with ranked entry candidates
    and aggregate statistics.
    """
    # Top entry node candidates with full inference
    entry_candidates: List[EntryNodeInference]
    
    # Top paths with entry inference
    paths: List[PathInferenceResult]
    
    # Aggregate statistics for visualization
    aggregate_stats: Dict[str, Any]
    
    # Inference metadata
    inference_metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "entry_candidates": [e.to_dict() for e in self.entry_candidates],
            "paths": [p.to_dict() for p in self.paths],
            "aggregate_stats": self.aggregate_stats,
            "inference_metadata": self.inference_metadata,
            "_disclaimer": (
                "This system performs probabilistic forensic correlation using metadata "
                "and lawful network evidence. It does not de-anonymize TOR users."
            ),
            "_analysis_notice": {
                "type": "probabilistic_inference",
                "interpretation": "Results are statistical correlations, not definitive identifications",
                "verification": "Independent verification required before any investigative action",
                "limitations": [
                    "Probability scores indicate correlation strength only",
                    "False positives and negatives are possible",
                    "No content inspection or user identification performed",
                ],
            },
        }


# ============================================================================
# INFERENCE ENGINE
# ============================================================================

class ProbabilisticPathInference:
    """
    Engine for computing probabilistic path inference results.
    
    Combines:
    1. Bayesian entry node inference
    2. Derived confidence calculation
    3. Evidence metric computation
    """
    
    def __init__(
        self,
        time_weight: float = 0.35,
        traffic_weight: float = 0.30,
        stability_weight: float = 0.20,
        consistency_weight: float = 0.10,
        geo_weight: float = 0.05,
    ):
        """
        Initialize inference engine.
        
        Args:
            time_weight: Weight for time overlap evidence
            traffic_weight: Weight for traffic similarity evidence
            stability_weight: Weight for stability evidence
            consistency_weight: Weight for path consistency evidence
            geo_weight: Weight for geographic plausibility evidence
        """
        self.weights = {
            "time_overlap": time_weight,
            "traffic_similarity": traffic_weight,
            "stability": stability_weight,
            "path_consistency": consistency_weight,
            "geo_plausibility": geo_weight,
        }
        
        # Ensure weights sum to 1.0
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            self.weights = {k: v / total for k, v in self.weights.items()}
        
        self.bayesian_engine = BayesianEntryInference(
            likelihood_weight_time=time_weight,
            likelihood_weight_traffic=traffic_weight,
            likelihood_weight_stability=stability_weight,
        )
        
        self.confidence_calculator = ConfidenceCalculator()
        
        # Confidence evolution tracking
        self.confidence_tracker = ConfidenceEvolutionTracker()
        
        # Track observations
        self.entry_observations: Dict[str, List[Dict]] = defaultdict(list)
        self.exit_nodes_by_entry: Dict[str, set] = defaultdict(set)
    
    def compute_evidence_for_path(
        self,
        entry: Dict[str, Any],
        middle: Dict[str, Any],
        exit: Dict[str, Any],
    ) -> EvidenceBreakdown:
        """
        Compute evidence metrics for a path.
        
        Args:
            entry: Entry relay data
            middle: Middle relay data
            exit: Exit relay data
        
        Returns:
            EvidenceBreakdown with all metrics
        """
        # Parse uptime windows
        def parse_uptime(relay: Dict) -> Tuple[Optional[datetime], Optional[datetime]]:
            first_seen = relay.get("first_seen")
            last_seen = relay.get("last_seen")
            
            if isinstance(first_seen, str):
                try:
                    from dateutil import parser
                    first_seen = parser.parse(first_seen)
                except:
                    first_seen = None
            
            if isinstance(last_seen, str):
                try:
                    from dateutil import parser
                    last_seen = parser.parse(last_seen)
                except:
                    last_seen = None
            
            return first_seen, last_seen
        
        entry_uptime = parse_uptime(entry)
        middle_uptime = parse_uptime(middle)
        exit_uptime = parse_uptime(exit)
        
        # Time overlap
        time_result = time_overlap_score(
            entry_uptime=entry_uptime,
            middle_uptime=middle_uptime,
            exit_uptime=exit_uptime,
        )
        time_score = time_result.get("value", 0.0) if isinstance(time_result, dict) else 0.0
        
        # Traffic similarity (based on bandwidth balance)
        # Use observed bandwidth if available, else fall back to advertised
        entry_observed_bw = entry.get("observed_bandwidth", entry.get("advertised_bandwidth", 0)) or 0
        middle_observed_bw = middle.get("observed_bandwidth", middle.get("advertised_bandwidth", 0)) or 0
        exit_observed_bw = exit.get("observed_bandwidth", exit.get("advertised_bandwidth", 0)) or 0
        
        entry_advertised_bw = entry.get("advertised_bandwidth")
        middle_advertised_bw = middle.get("advertised_bandwidth")
        exit_advertised_bw = exit.get("advertised_bandwidth")
        
        traffic_result = traffic_similarity_score(
            entry_observed_bandwidth=entry_observed_bw,
            middle_observed_bandwidth=middle_observed_bw,
            exit_observed_bandwidth=exit_observed_bw,
            entry_advertised_bandwidth=entry_advertised_bw,
            middle_advertised_bandwidth=middle_advertised_bw,
            exit_advertised_bandwidth=exit_advertised_bw,
        )
        traffic_score = traffic_result.get("value", 0.0) if isinstance(traffic_result, dict) else 0.0
        
        # Stability
        def uptime_days(uptime_tuple) -> float:
            first, last = uptime_tuple
            if first and last:
                return (last - first).total_seconds() / 86400.0
            return 0.0
        
        stability_result = relay_stability_score(
            entry_uptime_days=uptime_days(entry_uptime),
            middle_uptime_days=uptime_days(middle_uptime),
            exit_uptime_days=uptime_days(exit_uptime),
            entry_tor_flags=entry.get("flags", []),
            middle_tor_flags=middle.get("flags", []),
            exit_tor_flags=exit.get("flags", []),
        )
        stability_score = stability_result.get("value", 0.0) if isinstance(stability_result, dict) else 0.0
        
        # Path consistency - uses AS and country diversity
        # Extract AS and country info
        entry_as = entry.get("as", "") or ""
        middle_as = middle.get("as", "") or ""
        exit_as = exit.get("as", "") or ""
        
        entry_country = entry.get("country", "") or ""
        middle_country = middle.get("country", "") or ""
        exit_country = exit.get("country", "") or ""
        
        # Check family independence
        entry_family = set(entry.get("effective_family", []))
        middle_family = set(middle.get("effective_family", []))
        exit_family = set(exit.get("effective_family", []))
        family_independent = not bool(entry_family & middle_family or middle_family & exit_family or entry_family & exit_family)
        
        consistency_result = path_consistency_score(
            entry_exit_as_different=(entry_as != exit_as) if entry_as and exit_as else True,
            entry_middle_as_different=(entry_as != middle_as) if entry_as and middle_as else True,
            middle_exit_as_different=(middle_as != exit_as) if middle_as and exit_as else True,
            entry_exit_country_different=(entry_country != exit_country) if entry_country and exit_country else True,
            entry_middle_country_different=(entry_country != middle_country) if entry_country and middle_country else True,
            middle_exit_country_different=(middle_country != exit_country) if middle_country and exit_country else True,
            family_independent=family_independent,
            entry_exit_same_provider_risk=self._same_subnet(
                entry.get("or_addresses", []),
                exit.get("or_addresses", []),
            ),
        )
        consistency_score = consistency_result.get("value", 0.0) if isinstance(consistency_result, dict) else 0.0
        
        # Geographic plausibility
        geo_result = geo_plausibility_score(
            entry_country=entry_country,
            middle_country=middle_country,
            exit_country=exit_country,
        )
        geo_score = geo_result.get("value", 0.0) if isinstance(geo_result, dict) else 0.0
        
        # Compute weighted average
        weighted_avg = (
            time_score * self.weights["time_overlap"] +
            traffic_score * self.weights["traffic_similarity"] +
            stability_score * self.weights["stability"] +
            consistency_score * self.weights["path_consistency"] +
            geo_score * self.weights["geo_plausibility"]
        )
        
        # Compute consistency (inverse of standard deviation)
        scores = [time_score, traffic_score, stability_score, consistency_score, geo_score]
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        std_dev = math.sqrt(variance)
        consistency = 1.0 - min(std_dev, 0.5) * 2  # Map 0-0.5 std to 1.0-0.0 consistency
        
        return EvidenceBreakdown(
            time_overlap=round(time_score, 4),
            time_overlap_label=EvidenceBreakdown.score_to_label(time_score),
            traffic_similarity=round(traffic_score, 4),
            traffic_similarity_label=EvidenceBreakdown.score_to_label(traffic_score),
            stability=round(stability_score, 4),
            stability_label=EvidenceBreakdown.score_to_label(stability_score),
            path_consistency=round(consistency_score, 4),
            path_consistency_label=EvidenceBreakdown.score_to_label(consistency_score),
            geo_plausibility=round(geo_score, 4),
            geo_plausibility_label=EvidenceBreakdown.score_to_label(geo_score),
            weighted_average=round(weighted_avg, 4),
            min_score=round(min(scores), 4),
            consistency_score=round(consistency, 4),
        )
    
    def _same_subnet(self, addrs1: List[str], addrs2: List[str]) -> bool:
        """Check if addresses share same /24 subnet"""
        def extract_prefix(addr: str) -> str:
            try:
                ip = addr.split(":")[0]
                parts = ip.split(".")
                if len(parts) >= 3:
                    return ".".join(parts[:3])
            except:
                pass
            return ""
        
        prefixes1 = {extract_prefix(a) for a in addrs1 if a}
        prefixes2 = {extract_prefix(a) for a in addrs2 if a}
        
        return bool(prefixes1 & prefixes2)
    
    def add_path_observation(
        self,
        entry: Dict[str, Any],
        middle: Dict[str, Any],
        exit: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> EvidenceBreakdown:
        """
        Add a path observation and update Bayesian inference.
        
        Args:
            entry: Entry relay data
            middle: Middle relay data
            exit: Exit relay data
            session_id: Optional session identifier for tracking
        
        Returns:
            Evidence breakdown for this path
        """
        evidence = self.compute_evidence_for_path(entry, middle, exit)
        
        # Create RelayInfo for Bayesian engine
        entry_relay = create_relay_info(
            fingerprint=entry.get("fingerprint", ""),
            consensus_weight=entry.get("consensus_weight", entry.get("advertised_bandwidth", 0) or 1.0),
            uptime_days=int(evidence.stability * 365),  # Approximate
            flags=entry.get("flags", []),
        )
        
        # Ensure prior exists
        if entry_relay.fingerprint not in self.bayesian_engine.priors:
            # Add to priors dynamically
            current_priors = dict(self.bayesian_engine.priors)
            current_priors[entry_relay.fingerprint] = entry_relay.consensus_weight
            total = sum(current_priors.values())
            self.bayesian_engine.priors = {fp: w / total for fp, w in current_priors.items()}
        
        # Update Bayesian evidence
        try:
            self.bayesian_engine.update_evidence(
                entry_relay=entry_relay,
                time_overlap=evidence.time_overlap,
                traffic_similarity=evidence.traffic_similarity,
                stability=evidence.stability,
                exit_node_observed=exit.get("fingerprint", ""),
            )
        except ValueError:
            # Handle edge cases
            pass
        
        # Track observation
        exit_fingerprint = exit.get("fingerprint", "")
        self.entry_observations[entry_relay.fingerprint].append({
            "exit_fingerprint": exit_fingerprint,
            "middle_fingerprint": middle.get("fingerprint"),
            "evidence": evidence.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
        })
        
        self.exit_nodes_by_entry[entry_relay.fingerprint].add(exit_fingerprint)
        
        # Update confidence evolution tracking
        posterior = self.bayesian_engine.posterior_probability(entry_relay.fingerprint)
        confidence_result = self.confidence_calculator.compute_derived_confidence(
            evidence_scores=[
                evidence.time_overlap,
                evidence.traffic_similarity,
                evidence.stability,
            ],
            observation_count=len(self.entry_observations[entry_relay.fingerprint]),
            session_consistency=evidence.consistency_score,
            path_convergence=evidence.weighted_average,
            has_pcap_support=False,
        )
        confidence = confidence_result.get("confidence", 0.5) if isinstance(confidence_result, dict) else 0.5
        
        # Determine change reason
        timeline = self.confidence_tracker.get_timeline(entry_relay.fingerprint)
        if timeline is None or len(timeline.snapshots) == 0:
            reason = ConfidenceChangeReason.INITIAL
        elif exit_fingerprint and exit_fingerprint not in self.exit_nodes_by_entry[entry_relay.fingerprint]:
            reason = ConfidenceChangeReason.NEW_EXIT_NODE
        elif session_id:
            reason = ConfidenceChangeReason.NEW_SESSION
        else:
            reason = ConfidenceChangeReason.BAYESIAN_UPDATE
        
        # Record confidence update
        self.confidence_tracker.record_update(
            entry_fingerprint=entry_relay.fingerprint,
            entry_nickname=entry.get("nickname", "unknown"),
            new_confidence=confidence,
            posterior=posterior,
            reason=reason,
            evidence_strength=evidence.weighted_average,
            evidence_consistency=evidence.consistency_score,
            exit_node=exit_fingerprint,
            session_id=session_id,
        )
        
        return evidence
    
    def set_entry_priors(self, guards: List[Dict[str, Any]]) -> None:
        """
        Set prior probabilities from guard relay list.
        
        Args:
            guards: List of guard relay dictionaries
        """
        relay_list = [
            create_relay_info(
                fingerprint=g.get("fingerprint", ""),
                consensus_weight=g.get("consensus_weight", g.get("advertised_bandwidth", 0) or 1.0),
                uptime_days=0,
                flags=g.get("flags", []),
            )
            for g in guards
            if g.get("fingerprint")
        ]
        
        if relay_list:
            self.bayesian_engine.set_priors(relay_list)
    
    def compute_entry_inference(
        self,
        entry: Dict[str, Any],
        rank: int,
    ) -> Optional[EntryNodeInference]:
        """
        Compute full inference result for an entry node.
        
        Args:
            entry: Entry relay data
            rank: Ranking position
        
        Returns:
            EntryNodeInference or None if insufficient data
        """
        fingerprint = entry.get("fingerprint", "")
        
        if not fingerprint:
            return None
        
        # Get observations for this entry
        observations = self.entry_observations.get(fingerprint, [])
        exit_nodes = list(self.exit_nodes_by_entry.get(fingerprint, []))
        
        # Get Bayesian results
        if fingerprint in self.bayesian_engine.priors:
            prior = self.bayesian_engine.priors[fingerprint]
            posterior = self.bayesian_engine.posterior_probability(fingerprint)
        else:
            prior = 0.001
            posterior = 0.001
        
        likelihood_ratio = posterior / prior if prior > 0 else 1.0
        
        # Compute average evidence across observations
        if observations:
            avg_evidence = self._average_evidence(observations)
        else:
            avg_evidence = EvidenceBreakdown(
                time_overlap=0.0, time_overlap_label="insufficient",
                traffic_similarity=0.0, traffic_similarity_label="insufficient",
                stability=0.0, stability_label="insufficient",
                path_consistency=0.0, path_consistency_label="insufficient",
                geo_plausibility=0.0, geo_plausibility_label="insufficient",
                weighted_average=0.0, min_score=0.0, consistency_score=0.0,
            )
        
        # Compute derived confidence
        confidence_result = self.confidence_calculator.compute_derived_confidence(
            evidence_scores=[
                avg_evidence.time_overlap,
                avg_evidence.traffic_similarity,
                avg_evidence.stability,
            ],
            observation_count=len(observations),
            session_consistency=avg_evidence.consistency_score,
            path_convergence=avg_evidence.weighted_average,
            has_pcap_support=False,
        )
        confidence = confidence_result.get("confidence", 0.5) if isinstance(confidence_result, dict) else 0.5
        
        confidence_level = self._confidence_to_level(confidence)
        
        # Extract relay metadata
        bandwidth = entry.get("advertised_bandwidth", 0) or 0
        
        return EntryNodeInference(
            fingerprint=fingerprint,
            nickname=entry.get("nickname", "unknown"),
            prior_probability=round(prior, 6),
            posterior_probability=round(posterior, 6),
            likelihood_ratio=round(likelihood_ratio, 4),
            confidence=round(confidence, 4),
            confidence_level=confidence_level,
            evidence=avg_evidence,
            country=entry.get("country", ""),
            autonomous_system=entry.get("as", ""),
            bandwidth_mbps=round(bandwidth / 1_000_000, 2),
            uptime_days=0,  # Would need calculation
            flags=entry.get("flags", []),
            is_guard=entry.get("is_guard", False) or "Guard" in entry.get("flags", []),
            observation_count=len(observations),
            exit_nodes_observed_with=exit_nodes[:10],  # Limit for response size
            rank=rank,
        )
    
    def _average_evidence(self, observations: List[Dict]) -> EvidenceBreakdown:
        """Average evidence across multiple observations"""
        if not observations:
            return EvidenceBreakdown(
                time_overlap=0.0, time_overlap_label="insufficient",
                traffic_similarity=0.0, traffic_similarity_label="insufficient",
                stability=0.0, stability_label="insufficient",
                path_consistency=0.0, path_consistency_label="insufficient",
                geo_plausibility=0.0, geo_plausibility_label="insufficient",
                weighted_average=0.0, min_score=0.0, consistency_score=0.0,
            )
        
        n = len(observations)
        
        avg_time = sum(o.get("evidence", {}).get("time_overlap", 0) for o in observations) / n
        avg_traffic = sum(o.get("evidence", {}).get("traffic_similarity", 0) for o in observations) / n
        avg_stability = sum(o.get("evidence", {}).get("stability", 0) for o in observations) / n
        avg_consistency = sum(o.get("evidence", {}).get("path_consistency", 0) for o in observations) / n
        avg_geo = sum(o.get("evidence", {}).get("geo_plausibility", 0) for o in observations) / n
        avg_weighted = sum(o.get("evidence", {}).get("weighted_average", 0) for o in observations) / n
        avg_min = sum(o.get("evidence", {}).get("min_score", 0) for o in observations) / n
        avg_cons_score = sum(o.get("evidence", {}).get("consistency_score", 0) for o in observations) / n
        
        return EvidenceBreakdown(
            time_overlap=round(avg_time, 4),
            time_overlap_label=EvidenceBreakdown.score_to_label(avg_time),
            traffic_similarity=round(avg_traffic, 4),
            traffic_similarity_label=EvidenceBreakdown.score_to_label(avg_traffic),
            stability=round(avg_stability, 4),
            stability_label=EvidenceBreakdown.score_to_label(avg_stability),
            path_consistency=round(avg_consistency, 4),
            path_consistency_label=EvidenceBreakdown.score_to_label(avg_consistency),
            geo_plausibility=round(avg_geo, 4),
            geo_plausibility_label=EvidenceBreakdown.score_to_label(avg_geo),
            weighted_average=round(avg_weighted, 4),
            min_score=round(avg_min, 4),
            consistency_score=round(avg_cons_score, 4),
        )
    
    def _confidence_to_level(self, confidence: float) -> str:
        """Convert confidence value to level string"""
        if confidence >= 0.8:
            return "very_high"
        elif confidence >= 0.6:
            return "high"
        elif confidence >= 0.4:
            return "medium"
        elif confidence >= 0.2:
            return "low"
        else:
            return "very_low"
    
    def get_ranked_entries(
        self,
        guards: List[Dict[str, Any]],
        top_k: int = 20,
    ) -> List[EntryNodeInference]:
        """
        Get ranked entry candidates by posterior probability.
        
        Args:
            guards: List of guard relay data
            top_k: Number of top entries to return
        
        Returns:
            List of EntryNodeInference sorted by posterior
        """
        # Build inference for all guards with observations
        entries = []
        
        for guard in guards:
            fp = guard.get("fingerprint", "")
            if fp in self.bayesian_engine.priors:
                inference = self.compute_entry_inference(guard, rank=0)
                if inference:
                    entries.append(inference)
        
        # Sort by posterior probability
        entries.sort(key=lambda x: x.posterior_probability, reverse=True)
        
        # Assign ranks
        for i, entry in enumerate(entries):
            entry.rank = i + 1
        
        return entries[:top_k]
    
    def compute_aggregate_stats(self) -> Dict[str, Any]:
        """Compute aggregate statistics for visualization"""
        posteriors = list(self.bayesian_engine.posterior_probabilities().values())
        
        if not posteriors:
            return {
                "total_entries_analyzed": 0,
                "total_observations": 0,
                "posterior_distribution": {},
                "confidence_distribution": {},
                "evidence_quality": {},
            }
        
        # Posterior distribution stats
        posterior_stats = {
            "mean": round(sum(posteriors) / len(posteriors), 6),
            "max": round(max(posteriors), 6),
            "min": round(min(posteriors), 6),
            "std_dev": round(
                math.sqrt(sum((p - sum(posteriors)/len(posteriors))**2 for p in posteriors) / len(posteriors)),
                6
            ),
        }
        
        # Confidence level distribution
        total_obs = sum(len(obs) for obs in self.entry_observations.values())
        
        return {
            "total_entries_analyzed": len(self.bayesian_engine.priors),
            "total_observations": total_obs,
            "unique_entry_candidates": len(self.entry_observations),
            "posterior_distribution": posterior_stats,
            "entropy": round(self.bayesian_engine.entropy(), 4),
        }
    
    # ========================================================================
    # CONFIDENCE EVOLUTION METHODS
    # ========================================================================
    
    def get_confidence_timeline(self, entry_fingerprint: str) -> Optional[Dict[str, Any]]:
        """
        Get confidence evolution timeline for an entry node.
        
        Args:
            entry_fingerprint: Entry relay fingerprint
            
        Returns:
            Dictionary with timeline data or None if not tracked
        """
        timeline = self.confidence_tracker.get_timeline(entry_fingerprint)
        if timeline:
            return timeline.to_dict()
        return None
    
    def get_all_confidence_timelines(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all confidence timelines.
        
        Returns:
            Dictionary mapping fingerprints to timeline data
        """
        return {
            fp: tl.to_dict()
            for fp, tl in self.confidence_tracker.get_all_timelines().items()
        }
    
    def get_accuracy_improvement(self, entry_fingerprint: str) -> Dict[str, Any]:
        """
        Get detailed accuracy improvement metrics for an entry node.
        
        Shows how confidence evolved as more evidence was correlated.
        
        Args:
            entry_fingerprint: Entry relay fingerprint
            
        Returns:
            Dictionary with improvement metrics
        """
        return self.confidence_tracker.compute_accuracy_improvement(entry_fingerprint)
    
    def get_improving_candidates(self) -> List[str]:
        """Get fingerprints of candidates with improving confidence trend"""
        return self.confidence_tracker.get_improving_candidates()
    
    def get_converged_candidates(self, threshold: float = 0.7) -> List[str]:
        """
        Get fingerprints of candidates with converged (stable) confidence.
        
        Args:
            threshold: Minimum convergence score
            
        Returns:
            List of converged candidate fingerprints
        """
        return self.confidence_tracker.get_converged_candidates(threshold)
    
    def get_confidence_evolution_summary(self) -> Dict[str, Any]:
        """
        Get summary of confidence evolution across all tracked entries.
        
        Returns:
            Dictionary with evolution summary metrics
        """
        timelines = self.confidence_tracker.get_all_timelines()
        
        if not timelines:
            return {
                "has_data": False,
                "message": "No confidence evolution data",
            }
        
        # Collect statistics
        all_confidences = [tl.current_confidence for tl in timelines.values()]
        all_improvements = [
            tl.current_confidence - tl.initial_confidence
            for tl in timelines.values()
        ]
        all_convergences = [tl.get_convergence_score() for tl in timelines.values()]
        
        # Trend distribution
        trends = [tl.get_trend() for tl in timelines.values()]
        trend_dist = {
            "improving": sum(1 for t in trends if t == ConfidenceTrend.IMPROVING),
            "stable": sum(1 for t in trends if t == ConfidenceTrend.STABLE),
            "declining": sum(1 for t in trends if t == ConfidenceTrend.DECLINING),
            "volatile": sum(1 for t in trends if t == ConfidenceTrend.VOLATILE),
        }
        
        return {
            "has_data": True,
            "entries_tracked": len(timelines),
            "confidence_stats": {
                "mean": round(sum(all_confidences) / len(all_confidences), 4),
                "max": round(max(all_confidences), 4),
                "min": round(min(all_confidences), 4),
            },
            "improvement_stats": {
                "mean": round(sum(all_improvements) / len(all_improvements), 4),
                "max": round(max(all_improvements), 4),
                "min": round(min(all_improvements), 4),
                "positive_count": sum(1 for i in all_improvements if i > 0),
            },
            "convergence_stats": {
                "mean": round(sum(all_convergences) / len(all_convergences), 4),
                "converged_count": sum(1 for c in all_convergences if c >= 0.7),
            },
            "trend_distribution": trend_dist,
            "top_improving": self.confidence_tracker.get_top_candidates(5),
        }
    
    def export_confidence_state(self) -> Dict[str, Any]:
        """
        Export confidence evolution state for persistence.
        
        Returns:
            Dictionary with full tracker state
        """
        return self.confidence_tracker.export_state()
    
    def import_confidence_state(self, state: Dict[str, Any]) -> None:
        """
        Import confidence evolution state from persistence.
        
        Args:
            state: State dictionary from export_confidence_state()
        """
        self.confidence_tracker.import_state(state)


# ============================================================================
# API FUNCTIONS
# ============================================================================

def generate_probabilistic_paths(
    guards: List[Dict[str, Any]],
    middles: List[Dict[str, Any]],
    exits: List[Dict[str, Any]],
    top_k: int = 50,
    max_paths: int = 500,
) -> ProbabilisticPathResult:
    """
    Generate probabilistic path inference results.
    
    Args:
        guards: List of guard relay data
        middles: List of middle relay data
        exits: List of exit relay data
        top_k: Number of top entry candidates to return
        max_paths: Maximum paths to analyze
    
    Returns:
        ProbabilisticPathResult with full inference data
    """
    import random
    import uuid
    
    engine = ProbabilisticPathInference()
    
    # Set priors from guards
    engine.set_entry_priors(guards)
    
    # Shuffle for variety
    random.shuffle(guards)
    random.shuffle(middles)
    random.shuffle(exits)
    
    # Generate and analyze paths
    paths_analyzed = 0
    path_results = []
    
    guard_map = {g.get("fingerprint"): g for g in guards}
    
    for g in guards[:min(len(guards), 30)]:
        for m in middles[:min(len(middles), 50)]:
            if g.get("fingerprint") == m.get("fingerprint"):
                continue
            
            for x in exits[:min(len(exits), 40)]:
                if x.get("fingerprint") in {g.get("fingerprint"), m.get("fingerprint")}:
                    continue
                
                # Add observation
                evidence = engine.add_path_observation(g, m, x)
                
                paths_analyzed += 1
                
                if paths_analyzed > max_paths:
                    break
            
            if paths_analyzed > max_paths:
                break
        
        if paths_analyzed > max_paths:
            break
    
    # Get ranked entry candidates
    entry_candidates = engine.get_ranked_entries(guards, top_k=top_k)
    
    # Build top paths with entry inference
    for i, entry in enumerate(entry_candidates[:20]):
        if entry.fingerprint in guard_map:
            guard_data = guard_map[entry.fingerprint]
            
            # Find a sample path for this entry
            for m in middles[:5]:
                for x in exits[:5]:
                    if x.get("fingerprint") != entry.fingerprint and m.get("fingerprint") != entry.fingerprint:
                        evidence = engine.compute_evidence_for_path(guard_data, m, x)
                        
                        path_result = PathInferenceResult(
                            path_id=str(uuid.uuid4()),
                            entry=entry,
                            middle={
                                "fingerprint": m.get("fingerprint"),
                                "nickname": m.get("nickname"),
                                "country": m.get("country"),
                                "bandwidth_mbps": round((m.get("advertised_bandwidth") or 0) / 1_000_000, 2),
                            },
                            exit={
                                "fingerprint": x.get("fingerprint"),
                                "nickname": x.get("nickname"),
                                "country": x.get("country"),
                                "bandwidth_mbps": round((x.get("advertised_bandwidth") or 0) / 1_000_000, 2),
                            },
                            path_components={
                                "evidence": evidence.to_dict(),
                            },
                            path_plausibility=evidence.weighted_average,
                        )
                        
                        path_results.append(path_result)
                        break
                
                if len(path_results) > i:
                    break
    
    # Compute aggregate stats
    aggregate_stats = engine.compute_aggregate_stats()
    
    # Get confidence evolution summary
    confidence_evolution = engine.get_confidence_evolution_summary()
    
    # Build metadata
    inference_metadata = {
        "algorithm": "bayesian_entry_inference",
        "version": "1.1.0",
        "weights": engine.weights,
        "paths_analyzed": paths_analyzed,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "confidence_evolution": confidence_evolution,
    }
    
    return ProbabilisticPathResult(
        entry_candidates=entry_candidates,
        paths=path_results,
        aggregate_stats=aggregate_stats,
        inference_metadata=inference_metadata,
    )


def create_path_inference_engine() -> ProbabilisticPathInference:
    """Factory function to create inference engine"""
    return ProbabilisticPathInference()
