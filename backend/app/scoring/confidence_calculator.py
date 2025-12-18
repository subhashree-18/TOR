"""
Derived Confidence Calculation Module

This module implements a sophisticated confidence calculation system that derives
confidence levels from evidence strength, consistency metrics, and supporting
forensic data rather than using hard-coded assignments.

Key Components:
1. Evidence Strength: Average quality of observed evidence
2. Session Consistency: Corroboration across multiple observations
3. Path Convergence: Agreement across different path observations
4. Forensic Support: Presence of PCAP or other direct evidence

Confidence naturally ranges from 0.0 (very low) to 1.0 (very high) without
artificial caps or discrete bucketing.

Usage:
    from backend.app.scoring.confidence_calculator import ConfidenceCalculator
    
    calculator = ConfidenceCalculator()
    
    # Calculate confidence from evidence
    confidence = calculator.compute_derived_confidence(
        evidence_scores=[0.8, 0.75, 0.85],  # time, traffic, stability
        observation_count=5,
        session_consistency=0.92,
        path_convergence=0.88,
        has_pcap_support=True,
    )
    
    # Returns float between 0.0-1.0
    print(f"Confidence: {confidence:.4f}")
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import math
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class EvidenceMetrics:
    """Container for evidence strength metrics"""
    time_overlap: float = 0.0        # 0.0-1.0
    traffic_similarity: float = 0.0  # 0.0-1.0
    stability: float = 0.0           # 0.0-1.0
    path_consistency: float = 0.0    # 0.0-1.0 (optional)
    geo_plausibility: float = 0.0    # 0.0-1.0 (optional)
    
    @property
    def available_metrics(self) -> int:
        """Count non-zero metrics"""
        return sum(1 for v in [
            self.time_overlap,
            self.traffic_similarity,
            self.stability,
            self.path_consistency,
            self.geo_plausibility,
        ] if v > 0)
    
    @property
    def average(self) -> float:
        """Calculate average of all available metrics"""
        metrics = [v for v in [
            self.time_overlap,
            self.traffic_similarity,
            self.stability,
            self.path_consistency,
            self.geo_plausibility,
        ] if v > 0]
        return sum(metrics) / len(metrics) if metrics else 0.0
    
    @property
    def min_score(self) -> float:
        """Get minimum metric score"""
        metrics = [v for v in [
            self.time_overlap,
            self.traffic_similarity,
            self.stability,
            self.path_consistency,
            self.geo_plausibility,
        ] if v > 0]
        return min(metrics) if metrics else 0.0
    
    @property
    def std_dev(self) -> float:
        """Calculate standard deviation of metrics (consistency)"""
        metrics = [v for v in [
            self.time_overlap,
            self.traffic_similarity,
            self.stability,
            self.path_consistency,
            self.geo_plausibility,
        ] if v > 0]
        
        if len(metrics) < 2:
            return 0.0
        
        mean = sum(metrics) / len(metrics)
        variance = sum((x - mean) ** 2 for x in metrics) / len(metrics)
        return math.sqrt(variance)


@dataclass
class SessionObservation:
    """Single observation session with metadata"""
    session_id: str
    timestamp: datetime
    evidence_metrics: EvidenceMetrics
    exit_node_observed: str
    has_pcap_data: bool = False
    pcap_packets_captured: int = 0
    session_duration_seconds: float = 0.0
    path_hops: int = 3  # Default TOR path (entry, middle, exit)


@dataclass
class PathObservation:
    """Path-specific observation for convergence analysis"""
    path_id: str
    entry_fingerprint: str
    middle_fingerprint: str
    exit_fingerprint: str
    evidence_metrics: EvidenceMetrics
    observation_timestamp: datetime
    prior_probability: float = 0.5


# ============================================================================
# MAIN CONFIDENCE CALCULATOR
# ============================================================================

class ConfidenceCalculator:
    """
    Calculate derived confidence based on:
    1. Evidence strength (average quality of metrics)
    2. Session consistency (agreement across observations)
    3. Path convergence (consistency across different paths)
    4. Forensic support (PCAP or other direct evidence)
    """
    
    def __init__(
        self,
        evidence_weight: float = 0.40,
        consistency_weight: float = 0.30,
        convergence_weight: float = 0.20,
        forensic_weight: float = 0.10,
    ):
        """
        Initialize confidence calculator with component weights.
        
        Args:
            evidence_weight: Weight for evidence strength (0.0-1.0)
            consistency_weight: Weight for session consistency (0.0-1.0)
            convergence_weight: Weight for path convergence (0.0-1.0)
            forensic_weight: Weight for forensic support (0.0-1.0)
        
        Note: Weights should sum to approximately 1.0
        """
        total = evidence_weight + consistency_weight + convergence_weight + forensic_weight
        
        if not (0.95 <= total <= 1.05):
            logger.warning(
                f"Confidence weights sum to {total}, not 1.0. "
                "Consider normalizing for interpretability."
            )
        
        self.evidence_weight = evidence_weight
        self.consistency_weight = consistency_weight
        self.convergence_weight = convergence_weight
        self.forensic_weight = forensic_weight
        
        # Store observations for consistency analysis
        self.observations: Dict[str, List[SessionObservation]] = defaultdict(list)
        self.path_observations: Dict[str, List[PathObservation]] = defaultdict(list)
    
    # ========================================================================
    # 1. EVIDENCE STRENGTH CALCULATION
    # ========================================================================
    
    def calculate_evidence_confidence(
        self,
        evidence_metrics: EvidenceMetrics,
    ) -> Tuple[float, Dict]:
        """
        Calculate confidence component from evidence metric strength.
        
        Considers:
        - Average score of all evidence metrics
        - Minimum score (weakest evidence)
        - Consistency between metrics (low variance = high consistency)
        - Number of available evidence types
        
        Args:
            evidence_metrics: EvidenceMetrics object with all scores
        
        Returns:
            (confidence_score, details_dict) tuple
        """
        avg_score = evidence_metrics.average
        min_score = evidence_metrics.min_score
        std_dev = evidence_metrics.std_dev
        num_metrics = evidence_metrics.available_metrics
        
        # Component 1: Average evidence quality
        # 0.0-1.0 directly maps to confidence
        avg_confidence = avg_score
        
        # Component 2: Minimum score (chain is only as strong as weakest link)
        # Penalize if any evidence is weak
        min_penalty = (1.0 - min_score) * 0.15 if min_score < 0.6 else 0.0
        
        # Component 3: Metric consistency (low std dev = high consistency)
        # High variance means metrics disagree
        # Normalize std dev: ~0.2 = expected for normal variation
        consistency_bonus = max(0.0, 1.0 - (std_dev / 0.3)) * 0.1
        
        # Component 4: Multiple evidence types (more = better)
        # Each additional metric type adds confidence
        metric_bonus = (num_metrics - 1) * 0.05 if num_metrics > 1 else 0.0
        
        # Combine components
        evidence_confidence = min(
            1.0,
            max(0.0, avg_confidence - min_penalty + consistency_bonus + metric_bonus)
        )
        
        details = {
            "average_score": round(avg_score, 4),
            "minimum_score": round(min_score, 4),
            "metric_consistency_std_dev": round(std_dev, 4),
            "metric_count": num_metrics,
            "min_penalty": round(min_penalty, 4),
            "consistency_bonus": round(consistency_bonus, 4),
            "metric_bonus": round(metric_bonus, 4),
            "final_score": round(evidence_confidence, 4),
        }
        
        return evidence_confidence, details
    
    # ========================================================================
    # 2. SESSION CONSISTENCY CALCULATION
    # ========================================================================
    
    def add_session_observation(
        self,
        relay_fingerprint: str,
        observation: SessionObservation,
    ) -> None:
        """
        Record an observation session for consistency analysis.
        
        Args:
            relay_fingerprint: The relay being analyzed
            observation: SessionObservation with metrics and metadata
        """
        self.observations[relay_fingerprint].append(observation)
        logger.debug(
            f"Added observation for {relay_fingerprint}: "
            f"evidence_avg={observation.evidence_metrics.average:.3f}"
        )
    
    def calculate_session_consistency(
        self,
        relay_fingerprint: str,
        min_observations: int = 2,
    ) -> Tuple[float, Dict]:
        """
        Calculate consistency of evidence across multiple sessions.
        
        Sessions are corroborating observations of the same relay.
        High consistency = evidence agrees across different sessions/contexts.
        
        Considers:
        - Score agreement across sessions (low variance = high consistency)
        - Exit node diversity (consistent evidence despite different exits)
        - Temporal stability (scores stable over time)
        - Session metadata quality (duration, packet count)
        
        Args:
            relay_fingerprint: Relay to analyze
            min_observations: Minimum sessions needed for high confidence
        
        Returns:
            (consistency_score, details_dict) tuple
        """
        sessions = self.observations.get(relay_fingerprint, [])
        
        if len(sessions) < 2:
            # Single observation: can't assess consistency
            return 0.5, {
                "session_count": len(sessions),
                "consistency_basis": "insufficient_data",
                "final_score": 0.5,
            }
        
        # Extract evidence averages from each session
        session_averages = [s.evidence_metrics.average for s in sessions]
        
        # Calculate agreement: low variance = high agreement
        mean_avg = sum(session_averages) / len(session_averages)
        variance = sum((x - mean_avg) ** 2 for x in session_averages) / len(session_averages)
        std_dev = math.sqrt(variance)
        
        # Normalize variance to 0-1 confidence
        # std_dev < 0.1 = excellent agreement
        # std_dev > 0.3 = poor agreement
        agreement_confidence = max(0.0, 1.0 - (std_dev / 0.3))
        
        # Check exit node diversity
        exit_nodes = set(s.exit_node_observed for s in sessions)
        diversity_bonus = min(len(exit_nodes) / len(sessions), 1.0) * 0.1
        
        # Check temporal stability
        if len(sessions) >= 3:
            timestamps = [s.timestamp for s in sessions]
            time_diffs = []
            for i in range(len(timestamps) - 1):
                diff = (timestamps[i + 1] - timestamps[i]).total_seconds()
                if diff > 0:
                    time_diffs.append(diff)
            
            if time_diffs:
                # Stability: similar scores despite time gaps
                first_third = session_averages[:len(session_averages)//3 + 1]
                last_third = session_averages[-len(session_averages)//3:]
                temporal_drift = abs(sum(first_third)/len(first_third) - sum(last_third)/len(last_third))
                temporal_bonus = max(0.0, 1.0 - temporal_drift) * 0.05
            else:
                temporal_bonus = 0.0
        else:
            temporal_bonus = 0.0
        
        # Check PCAP support density
        pcap_sessions = sum(1 for s in sessions if s.has_pcap_data)
        pcap_density = pcap_sessions / len(sessions)
        
        # Combine components
        consistency_score = min(
            1.0,
            agreement_confidence + diversity_bonus + temporal_bonus
        )
        
        # Bonus if we have enough high-quality observations
        observation_bonus = min(len(sessions) / min_observations, 0.1)
        consistency_score = min(1.0, consistency_score + observation_bonus)
        
        details = {
            "session_count": len(sessions),
            "agreement_std_dev": round(std_dev, 4),
            "agreement_confidence": round(agreement_confidence, 4),
            "exit_diversity": len(exit_nodes),
            "diversity_bonus": round(diversity_bonus, 4),
            "temporal_bonus": round(temporal_bonus, 4),
            "observation_bonus": round(observation_bonus, 4),
            "pcap_density": round(pcap_density, 4),
            "final_score": round(consistency_score, 4),
        }
        
        return consistency_score, details
    
    # ========================================================================
    # 3. PATH CONVERGENCE CALCULATION
    # ========================================================================
    
    def add_path_observation(
        self,
        entry_fingerprint: str,
        observation: PathObservation,
    ) -> None:
        """
        Record a path observation for convergence analysis.
        
        Args:
            entry_fingerprint: Entry relay being analyzed
            observation: PathObservation with path info and evidence
        """
        self.path_observations[entry_fingerprint].append(observation)
        logger.debug(
            f"Added path observation for {entry_fingerprint}: "
            f"path_id={observation.path_id}"
        )
    
    def calculate_path_convergence(
        self,
        relay_fingerprint: str,
    ) -> Tuple[float, Dict]:
        """
        Calculate evidence convergence across different observed paths.
        
        Path convergence measures whether multiple different paths containing
        this relay show consistent evidence patterns.
        
        Considers:
        - Consensus across paths (all paths agree on evidence strength)
        - Posterior probability clustering (posteriors are stable)
        - Entry-exit diversity (evidence holds despite path variations)
        - Evidence consensus (all evidence types agree)
        
        Args:
            relay_fingerprint: Relay to analyze
        
        Returns:
            (convergence_score, details_dict) tuple
        """
        paths = self.path_observations.get(relay_fingerprint, [])
        
        if len(paths) < 2:
            return 0.5, {
                "path_count": len(paths),
                "convergence_basis": "insufficient_data",
                "final_score": 0.5,
            }
        
        # Extract evidence from each path
        evidence_scores = [p.evidence_metrics.average for p in paths]
        
        # Consensus: how close are the evidence scores?
        mean_score = sum(evidence_scores) / len(evidence_scores)
        variance = sum((x - mean_score) ** 2 for x in evidence_scores) / len(evidence_scores)
        std_dev = math.sqrt(variance)
        
        # Convert variance to convergence (low variance = high convergence)
        consensus_confidence = max(0.0, 1.0 - (std_dev / 0.25))
        
        # Check posterior clustering
        posteriors = [p.prior_probability for p in paths]
        if posteriors:
            posterior_mean = sum(posteriors) / len(posteriors)
            posterior_var = sum((p - posterior_mean) ** 2 for p in posteriors) / len(posteriors)
            posterior_std = math.sqrt(posterior_var)
            
            # Tight posterior clustering increases confidence
            posterior_bonus = max(0.0, 1.0 - (posterior_std / 0.2)) * 0.1
        else:
            posterior_bonus = 0.0
        
        # Check path diversity (consistent evidence across different paths)
        unique_exits = len(set(p.exit_fingerprint for p in paths))
        unique_middles = len(set(p.middle_fingerprint for p in paths))
        path_diversity = (unique_exits + unique_middles) / (len(paths) * 2)
        diversity_bonus = path_diversity * 0.05
        
        # Check evidence component agreement
        all_metrics = [p.evidence_metrics for p in paths]
        metric_agreements = []
        
        for metric_name in ['time_overlap', 'traffic_similarity', 'stability']:
            metric_values = [getattr(m, metric_name) for m in all_metrics if getattr(m, metric_name) > 0]
            if metric_values:
                metric_mean = sum(metric_values) / len(metric_values)
                metric_var = sum((v - metric_mean) ** 2 for v in metric_values) / len(metric_values)
                metric_std = math.sqrt(metric_var)
                agreement = max(0.0, 1.0 - (metric_std / 0.2))
                metric_agreements.append(agreement)
        
        component_agreement = sum(metric_agreements) / len(metric_agreements) if metric_agreements else 0.0
        component_bonus = component_agreement * 0.05
        
        # Combine components
        convergence_score = min(
            1.0,
            consensus_confidence + posterior_bonus + diversity_bonus + component_bonus
        )
        
        details = {
            "path_count": len(paths),
            "evidence_std_dev": round(std_dev, 4),
            "consensus_confidence": round(consensus_confidence, 4),
            "posterior_std_dev": round(posterior_std if posteriors else 0.0, 4),
            "posterior_bonus": round(posterior_bonus, 4),
            "path_diversity": round(path_diversity, 4),
            "diversity_bonus": round(diversity_bonus, 4),
            "component_agreement": round(component_agreement, 4),
            "component_bonus": round(component_bonus, 4),
            "final_score": round(convergence_score, 4),
        }
        
        return convergence_score, details
    
    # ========================================================================
    # 4. FORENSIC SUPPORT CALCULATION
    # ========================================================================
    
    def calculate_forensic_support(
        self,
        relay_fingerprint: str,
        has_pcap_data: bool = False,
        pcap_packet_count: int = 0,
        supporting_evidence: Optional[List[str]] = None,
    ) -> Tuple[float, Dict]:
        """
        Calculate confidence boost from forensic/direct evidence.
        
        PCAP data (packet capture files) provide direct network evidence
        independent of inference. Presence of PCAP data significantly
        increases confidence.
        
        Supports:
        - PCAP evidence (strongest)
        - Multiple evidence sources
        - Cross-validation data
        
        Args:
            relay_fingerprint: Relay being analyzed
            has_pcap_data: Whether PCAP data available
            pcap_packet_count: Number of packets in PCAP
            supporting_evidence: List of other supporting evidence types
        
        Returns:
            (forensic_support_score, details_dict) tuple
        """
        forensic_score = 0.0
        
        # PCAP presence: strong evidence boost
        if has_pcap_data:
            forensic_score += 0.6
            
            # PCAP packet volume: more packets = stronger evidence
            if pcap_packet_count > 1000:
                forensic_score += 0.3  # Large capture
            elif pcap_packet_count > 100:
                forensic_score += 0.15  # Medium capture
            elif pcap_packet_count > 10:
                forensic_score += 0.05  # Small capture
        
        # Supporting evidence types
        if supporting_evidence:
            evidence_types = {
                "flow_analysis": 0.15,
                "timing_analysis": 0.10,
                "bandwidth_analysis": 0.12,
                "route_tracing": 0.10,
                "dns_correlation": 0.08,
                "tls_fingerprint": 0.12,
            }
            
            for evidence_type in supporting_evidence:
                if evidence_type in evidence_types:
                    forensic_score += evidence_types[evidence_type]
        
        # Cap at 1.0
        forensic_score = min(1.0, forensic_score)
        
        details = {
            "has_pcap": has_pcap_data,
            "pcap_packet_count": pcap_packet_count,
            "supporting_evidence_types": len(supporting_evidence) if supporting_evidence else 0,
            "pcap_score": 0.6 if has_pcap_data else 0.0,
            "supporting_evidence_score": forensic_score - (0.6 if has_pcap_data else 0.0),
            "final_score": round(forensic_score, 4),
        }
        
        return forensic_score, details
    
    # ========================================================================
    # 5. COMBINED DERIVED CONFIDENCE
    # ========================================================================
    
    def compute_derived_confidence(
        self,
        evidence_scores: Optional[List[float]] = None,
        evidence_metrics: Optional[EvidenceMetrics] = None,
        observation_count: int = 1,
        session_consistency: Optional[float] = None,
        path_convergence: Optional[float] = None,
        has_pcap_support: bool = False,
        pcap_packet_count: int = 0,
        relay_fingerprint: Optional[str] = None,
        return_breakdown: bool = False,
    ) -> Dict:
        """
        Compute final derived confidence from all components.
        
        Main entry point for confidence calculation. Combines:
        1. Evidence strength (quality of observed metrics)
        2. Session consistency (agreement across observations)
        3. Path convergence (consistency across paths)
        4. Forensic support (PCAP/direct evidence)
        
        Args:
            evidence_scores: List of evidence values (0.0-1.0)
            evidence_metrics: EvidenceMetrics object (alternative to scores list)
            observation_count: Number of corroborating sessions
            session_consistency: Pre-computed consistency (optional)
            path_convergence: Pre-computed convergence (optional)
            has_pcap_support: Whether PCAP data available
            pcap_packet_count: Number of packets in PCAP
            relay_fingerprint: Relay ID for historical data lookup
            return_breakdown: If True, return component breakdown
        
        Returns:
            {
                "confidence": 0.0-1.0,  # Final confidence score
                "components": {           # Component scores if return_breakdown=True
                    "evidence_strength": 0.0-1.0,
                    "session_consistency": 0.0-1.0,
                    "path_convergence": 0.0-1.0,
                    "forensic_support": 0.0-1.0,
                },
                "details": {...},        # Detailed calculations
            }
        """
        
        # Step 1: Evidence strength
        if evidence_metrics is None:
            if evidence_scores:
                evidence_metrics = EvidenceMetrics(
                    time_overlap=evidence_scores[0] if len(evidence_scores) > 0 else 0.0,
                    traffic_similarity=evidence_scores[1] if len(evidence_scores) > 1 else 0.0,
                    stability=evidence_scores[2] if len(evidence_scores) > 2 else 0.0,
                    path_consistency=evidence_scores[3] if len(evidence_scores) > 3 else 0.0,
                    geo_plausibility=evidence_scores[4] if len(evidence_scores) > 4 else 0.0,
                )
            else:
                # Default: neutral confidence
                return {
                    "confidence": 0.5,
                    "components": {
                        "evidence_strength": 0.5,
                        "session_consistency": 0.5,
                        "path_convergence": 0.5,
                        "forensic_support": 0.0,
                    },
                    "details": {"error": "No evidence data provided"},
                }
        
        evidence_confidence, evidence_details = self.calculate_evidence_confidence(
            evidence_metrics
        )
        
        # Step 2: Session consistency
        if session_consistency is None and relay_fingerprint:
            session_consistency, consistency_details = self.calculate_session_consistency(
                relay_fingerprint
            )
        else:
            session_consistency = session_consistency or 0.5
            consistency_details = {"provided": True, "final_score": session_consistency}
        
        # Step 3: Path convergence
        if path_convergence is None and relay_fingerprint:
            path_convergence, convergence_details = self.calculate_path_convergence(
                relay_fingerprint
            )
        else:
            path_convergence = path_convergence or 0.5
            convergence_details = {"provided": True, "final_score": path_convergence}
        
        # Step 4: Forensic support
        forensic_support, forensic_details = self.calculate_forensic_support(
            relay_fingerprint=relay_fingerprint or "unknown",
            has_pcap_data=has_pcap_support,
            pcap_packet_count=pcap_packet_count,
        )
        
        # Step 5: Combine components with weights
        combined_confidence = (
            self.evidence_weight * evidence_confidence +
            self.consistency_weight * session_consistency +
            self.convergence_weight * path_convergence +
            self.forensic_weight * forensic_support
        )
        
        # Apply observation count boost
        # More observations = higher confidence (diminishing returns)
        observation_boost = min(
            (observation_count - 1) / 10.0,  # Max 0.1 boost
            0.1
        )
        final_confidence = min(1.0, combined_confidence + observation_boost)
        
        result = {
            "confidence": round(final_confidence, 4),
            "components": {
                "evidence_strength": round(evidence_confidence, 4),
                "session_consistency": round(session_consistency, 4),
                "path_convergence": round(path_convergence, 4),
                "forensic_support": round(forensic_support, 4),
            },
            "observation_count": observation_count,
            "observation_boost": round(observation_boost, 4),
        }
        
        if return_breakdown:
            result["details"] = {
                "evidence": evidence_details,
                "consistency": consistency_details,
                "convergence": convergence_details,
                "forensic": forensic_details,
                "weights": {
                    "evidence": self.evidence_weight,
                    "consistency": self.consistency_weight,
                    "convergence": self.convergence_weight,
                    "forensic": self.forensic_weight,
                },
            }
        
        return result
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def confidence_to_category(self, confidence: float) -> str:
        """
        Convert continuous confidence to categorical level.
        
        This is optional - can display as either continuous or categorical.
        
        Returns:
            "very_low", "low", "medium", "high", "very_high"
        """
        if confidence >= 0.85:
            return "very_high"
        elif confidence >= 0.70:
            return "high"
        elif confidence >= 0.50:
            return "medium"
        elif confidence >= 0.30:
            return "low"
        else:
            return "very_low"
    
    def get_observations_summary(self, relay_fingerprint: str) -> Dict:
        """Get summary of all observations for a relay"""
        sessions = self.observations.get(relay_fingerprint, [])
        paths = self.path_observations.get(relay_fingerprint, [])
        
        return {
            "session_count": len(sessions),
            "path_count": len(paths),
            "total_observations": len(sessions) + len(paths),
            "pcap_sessions": sum(1 for s in sessions if s.has_pcap_data),
            "total_pcap_packets": sum(s.pcap_packets_captured for s in sessions),
        }
