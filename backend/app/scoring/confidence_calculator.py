"""
Forensic Confidence Scoring Engine for Probabilistic TOR Traffic Analysis

This module translates accumulated forensic evidence into an explainable
confidence metric suitable for investigative decision support.

CRITICAL DESIGN PRINCIPLES:

1. CONFIDENCE ≠ PROBABILITY
   - Confidence measures the QUALITY and CONSISTENCY of evidence
   - Confidence does NOT represent likelihood of identification
   - High confidence means: "evidence is strong and consistent"
   - It does NOT mean: "this is probably the right person"

2. CONSERVATIVE BY DESIGN
   - Confidence STARTS LOW (baseline ~15%)
   - Confidence increases ONLY with independent corroborating evidence
   - Diminishing returns prevent overconfidence
   - Explicit decay when evidence is missing or contradictory
   - Hard upper bound at 85% (never "certain")

3. EXPLAINABILITY REQUIREMENT
   - Every score component maps to plain English explanation
   - No cosmetic scaling or arbitrary weights
   - All contributing and limiting factors documented

4. FORENSIC INTEGRITY
   - Cannot be used for definitive identification
   - Explicit uncertainty language in all outputs
   - Designed for investigative PRIORITIZATION, not conclusion

Usage:
    from backend.app.scoring.confidence_calculator import ForensicConfidenceEngine
    
    engine = ForensicConfidenceEngine()
    
    result = engine.compute_confidence(
        correlation_hypothesis={...},
        timing_similarity=0.72,
        session_overlap=0.65,
        evidence_count=5,
        evidence_diversity=3,
        hypothesis_entropy=1.2,
    )
    
    # Returns structured result with explainability
    print(f"Confidence: {result['confidence_score']}/100")
    print(f"Level: {result['confidence_level']}")
    print(f"Contributing: {result['contributing_factors']}")
    print(f"Limiting: {result['limiting_factors']}")
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
import logging
import math
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS - Forensic Scoring Boundaries
# ============================================================================

# Confidence starts from this baseline with zero evidence
BASELINE_CONFIDENCE = 15.0

# Maximum achievable confidence (prevents overconfidence)
MAX_CONFIDENCE = 85.0

# Minimum evidence count to move beyond baseline
MIN_EVIDENCE_FOR_INCREASE = 2

# Entropy threshold above which confidence is penalized
HIGH_ENTROPY_THRESHOLD = 2.0

# Evidence diversity threshold for bonus
DIVERSITY_THRESHOLD = 3


class ConfidenceLevel(Enum):
    """
    Confidence levels with explicit interpretations.
    
    These are QUALITATIVE assessments of evidence quality,
    NOT probability statements about identification accuracy.
    """
    LOW = "Low"           # 0-40: Insufficient or inconsistent evidence
    MEDIUM = "Medium"     # 40-65: Some corroborating evidence, significant uncertainty
    HIGH = "High"         # 65-85: Strong corroborating evidence, still probabilistic


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class EvidenceInput:
    """
    Container for evidence metrics fed into confidence computation.
    
    Each metric should be normalized to 0.0-1.0 range.
    """
    timing_similarity: float = 0.0       # How well timing patterns match
    session_overlap: float = 0.0         # Temporal session overlap ratio
    traffic_pattern_match: float = 0.0   # Traffic signature similarity
    bandwidth_feasibility: float = 0.0   # Bandwidth constraints satisfied
    circuit_lifetime_valid: float = 0.0  # Within TOR circuit lifetime bounds
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "timing_similarity": self.timing_similarity,
            "session_overlap": self.session_overlap,
            "traffic_pattern_match": self.traffic_pattern_match,
            "bandwidth_feasibility": self.bandwidth_feasibility,
            "circuit_lifetime_valid": self.circuit_lifetime_valid,
        }
    
    @property
    def available_metrics(self) -> List[Tuple[str, float]]:
        """Return list of (name, value) for non-zero metrics."""
        metrics = []
        if self.timing_similarity > 0:
            metrics.append(("timing_similarity", self.timing_similarity))
        if self.session_overlap > 0:
            metrics.append(("session_overlap", self.session_overlap))
        if self.traffic_pattern_match > 0:
            metrics.append(("traffic_pattern_match", self.traffic_pattern_match))
        if self.bandwidth_feasibility > 0:
            metrics.append(("bandwidth_feasibility", self.bandwidth_feasibility))
        if self.circuit_lifetime_valid > 0:
            metrics.append(("circuit_lifetime_valid", self.circuit_lifetime_valid))
        return metrics


@dataclass
class CorrelationHypothesisInput:
    """
    Correlation hypothesis data fed into confidence computation.
    """
    hypothesis_id: str
    guard_fingerprint: str
    exit_fingerprint: str
    evidence_items: List[Dict[str, Any]] = field(default_factory=list)
    uncertainty_level: str = "high"
    
    @property
    def evidence_count(self) -> int:
        return len(self.evidence_items)
    
    @property
    def evidence_types(self) -> set:
        """Unique evidence types present."""
        return set(e.get("type", "unknown") for e in self.evidence_items)
    
    @property
    def evidence_diversity(self) -> int:
        """Number of distinct evidence types."""
        return len(self.evidence_types)


@dataclass
class ConfidenceResult:
    """
    Structured output from confidence computation.
    
    Includes score, level, contributing/limiting factors, and explainability notes.
    """
    confidence_score: float              # 0-100 scale
    confidence_level: ConfidenceLevel    # Categorical interpretation
    contributing_factors: List[Dict[str, Any]]  # What increased confidence
    limiting_factors: List[Dict[str, Any]]      # What prevented higher confidence
    explainability_notes: List[str]      # Plain English explanations
    uncertainty_statement: str           # Explicit uncertainty disclaimer
    
    # Internal computation details
    computation_breakdown: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "confidence_score": round(self.confidence_score, 1),
            "confidence_level": self.confidence_level.value,
            "contributing_factors": self.contributing_factors,
            "limiting_factors": self.limiting_factors,
            "explainability_notes": self.explainability_notes,
            "uncertainty_statement": self.uncertainty_statement,
            "computation_breakdown": self.computation_breakdown,
        }


# ============================================================================
# LEGACY DATA STRUCTURES (for backward compatibility)
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
# FORENSIC CONFIDENCE ENGINE - Core Implementation
# ============================================================================

class ForensicConfidenceEngine:
    """
    Forensic Confidence Scoring Engine for TOR Traffic Analysis.
    
    This engine translates accumulated forensic evidence into an explainable
    confidence metric. It is designed for investigative decision support,
    NOT for definitive identification.
    
    KEY PRINCIPLES:
    - Confidence starts LOW and increases only with corroborating evidence
    - Diminishing returns prevent overconfidence
    - All scores are explainable in plain English
    - Explicit uncertainty language throughout
    
    CONFIDENCE ≠ PROBABILITY
    High confidence means the evidence is strong and consistent.
    It does NOT mean the hypothesis is correct.
    """
    
    def __init__(self):
        """Initialize the forensic confidence engine."""
        # No static weights - all scoring is evidence-driven
        pass
    
    # ========================================================================
    # MAIN ENTRY POINT
    # ========================================================================
    
    def compute_confidence(
        self,
        correlation_hypothesis: Optional[Dict[str, Any]] = None,
        timing_similarity: float = 0.0,
        session_overlap: float = 0.0,
        evidence_count: int = 0,
        evidence_diversity: int = 0,
        hypothesis_entropy: float = 0.0,
        evidence_input: Optional[EvidenceInput] = None,
        has_contradictory_evidence: bool = False,
        missing_expected_evidence: bool = False,
    ) -> ConfidenceResult:
        """
        Compute forensic confidence score from accumulated evidence.
        
        Args:
            correlation_hypothesis: Dict with hypothesis data (optional)
            timing_similarity: How well timing patterns match (0.0-1.0)
            session_overlap: Temporal session overlap ratio (0.0-1.0)
            evidence_count: Number of independent evidence items
            evidence_diversity: Number of distinct evidence types
            hypothesis_entropy: Entropy of hypothesis distribution (higher = more uncertainty)
            evidence_input: Structured evidence input (alternative to individual params)
            has_contradictory_evidence: Whether any evidence contradicts the hypothesis
            missing_expected_evidence: Whether expected evidence is absent
        
        Returns:
            ConfidenceResult with score, level, factors, and explanations
        """
        # Initialize tracking
        contributing_factors: List[Dict[str, Any]] = []
        limiting_factors: List[Dict[str, Any]] = []
        explainability_notes: List[str] = []
        computation_breakdown: Dict[str, Any] = {}
        
        # ====================================================================
        # STEP 1: Start from baseline (confidence starts LOW)
        # ====================================================================
        confidence = BASELINE_CONFIDENCE
        explainability_notes.append(
            f"Baseline confidence: {BASELINE_CONFIDENCE}% (all hypotheses start here)"
        )
        computation_breakdown["baseline"] = BASELINE_CONFIDENCE
        
        # ====================================================================
        # STEP 2: Process evidence inputs
        # ====================================================================
        if evidence_input is not None:
            timing_similarity = max(timing_similarity, evidence_input.timing_similarity)
            session_overlap = max(session_overlap, evidence_input.session_overlap)
        
        # ====================================================================
        # STEP 3: Evidence count contribution (with diminishing returns)
        # ====================================================================
        evidence_contribution = self._compute_evidence_count_contribution(
            evidence_count=evidence_count,
            contributing_factors=contributing_factors,
            limiting_factors=limiting_factors,
            explainability_notes=explainability_notes,
        )
        confidence += evidence_contribution
        computation_breakdown["evidence_count_contribution"] = evidence_contribution
        
        # ====================================================================
        # STEP 4: Evidence diversity contribution
        # ====================================================================
        diversity_contribution = self._compute_diversity_contribution(
            evidence_diversity=evidence_diversity,
            contributing_factors=contributing_factors,
            limiting_factors=limiting_factors,
            explainability_notes=explainability_notes,
        )
        confidence += diversity_contribution
        computation_breakdown["diversity_contribution"] = diversity_contribution
        
        # ====================================================================
        # STEP 5: Timing similarity contribution
        # ====================================================================
        timing_contribution = self._compute_timing_contribution(
            timing_similarity=timing_similarity,
            contributing_factors=contributing_factors,
            limiting_factors=limiting_factors,
            explainability_notes=explainability_notes,
        )
        confidence += timing_contribution
        computation_breakdown["timing_contribution"] = timing_contribution
        
        # ====================================================================
        # STEP 6: Session overlap contribution
        # ====================================================================
        session_contribution = self._compute_session_overlap_contribution(
            session_overlap=session_overlap,
            contributing_factors=contributing_factors,
            limiting_factors=limiting_factors,
            explainability_notes=explainability_notes,
        )
        confidence += session_contribution
        computation_breakdown["session_overlap_contribution"] = session_contribution
        
        # ====================================================================
        # STEP 7: Apply entropy penalty (high entropy = high uncertainty)
        # ====================================================================
        entropy_penalty = self._compute_entropy_penalty(
            hypothesis_entropy=hypothesis_entropy,
            contributing_factors=contributing_factors,
            limiting_factors=limiting_factors,
            explainability_notes=explainability_notes,
        )
        confidence -= entropy_penalty
        computation_breakdown["entropy_penalty"] = entropy_penalty
        
        # ====================================================================
        # STEP 8: Apply decay for missing/contradictory evidence
        # ====================================================================
        decay_penalty = self._compute_evidence_decay(
            has_contradictory_evidence=has_contradictory_evidence,
            missing_expected_evidence=missing_expected_evidence,
            contributing_factors=contributing_factors,
            limiting_factors=limiting_factors,
            explainability_notes=explainability_notes,
        )
        confidence -= decay_penalty
        computation_breakdown["decay_penalty"] = decay_penalty
        
        # ====================================================================
        # STEP 9: Enforce conservative bounds
        # ====================================================================
        pre_bound_confidence = confidence
        confidence = max(0.0, min(MAX_CONFIDENCE, confidence))
        
        if pre_bound_confidence > MAX_CONFIDENCE:
            limiting_factors.append({
                "factor": "conservative_ceiling",
                "impact": pre_bound_confidence - MAX_CONFIDENCE,
                "explanation": f"Confidence capped at {MAX_CONFIDENCE}% to prevent overconfidence",
            })
            explainability_notes.append(
                f"Confidence capped at {MAX_CONFIDENCE}% (forensic ceiling - "
                "probabilistic analysis cannot achieve certainty)"
            )
        
        if pre_bound_confidence < 0:
            confidence = 0.0
            explainability_notes.append(
                "Confidence floored at 0% due to severe evidence issues"
            )
        
        computation_breakdown["pre_bound_confidence"] = pre_bound_confidence
        computation_breakdown["final_confidence"] = confidence
        
        # ====================================================================
        # STEP 10: Determine confidence level
        # ====================================================================
        confidence_level = self._determine_confidence_level(confidence)
        
        # ====================================================================
        # STEP 11: Generate uncertainty statement
        # ====================================================================
        uncertainty_statement = self._generate_uncertainty_statement(
            confidence=confidence,
            confidence_level=confidence_level,
            evidence_count=evidence_count,
        )
        
        return ConfidenceResult(
            confidence_score=round(confidence, 1),
            confidence_level=confidence_level,
            contributing_factors=contributing_factors,
            limiting_factors=limiting_factors,
            explainability_notes=explainability_notes,
            uncertainty_statement=uncertainty_statement,
            computation_breakdown=computation_breakdown,
        )
    
    # ========================================================================
    # COMPONENT COMPUTATION METHODS
    # ========================================================================
    
    def _compute_evidence_count_contribution(
        self,
        evidence_count: int,
        contributing_factors: List[Dict],
        limiting_factors: List[Dict],
        explainability_notes: List[str],
    ) -> float:
        """
        Compute confidence contribution from evidence count.
        
        Uses logarithmic scaling to implement diminishing returns:
        - First few pieces of evidence have largest impact
        - Additional evidence provides progressively less boost
        - Prevents gaming through evidence quantity alone
        
        Formula: contribution = 10 * ln(1 + evidence_count) for count >= MIN_EVIDENCE
        Max contribution capped at 25 points
        """
        if evidence_count < MIN_EVIDENCE_FOR_INCREASE:
            limiting_factors.append({
                "factor": "insufficient_evidence_count",
                "value": evidence_count,
                "threshold": MIN_EVIDENCE_FOR_INCREASE,
                "impact": 0,
                "explanation": (
                    f"Only {evidence_count} evidence item(s) found. "
                    f"Need at least {MIN_EVIDENCE_FOR_INCREASE} for confidence increase."
                ),
            })
            explainability_notes.append(
                f"Insufficient evidence: {evidence_count} item(s) found, "
                f"minimum {MIN_EVIDENCE_FOR_INCREASE} required for increase"
            )
            return 0.0
        
        # Logarithmic scaling: ln(1 + count) * 10
        # This gives diminishing returns as evidence accumulates
        raw_contribution = 10.0 * math.log(1 + evidence_count)
        
        # Cap maximum contribution from evidence count alone
        max_count_contribution = 25.0
        contribution = min(raw_contribution, max_count_contribution)
        
        contributing_factors.append({
            "factor": "evidence_count",
            "value": evidence_count,
            "raw_contribution": round(raw_contribution, 2),
            "capped_contribution": round(contribution, 2),
            "explanation": (
                f"{evidence_count} independent evidence items corroborate hypothesis. "
                f"Logarithmic scaling applied (diminishing returns)."
            ),
        })
        
        explainability_notes.append(
            f"Evidence count ({evidence_count} items) adds {contribution:.1f} points "
            "(diminishing returns applied)"
        )
        
        return contribution
    
    def _compute_diversity_contribution(
        self,
        evidence_diversity: int,
        contributing_factors: List[Dict],
        limiting_factors: List[Dict],
        explainability_notes: List[str],
    ) -> float:
        """
        Compute confidence contribution from evidence diversity.
        
        Multiple independent evidence TYPES are more valuable than
        multiple instances of the same type (reduces correlation risk).
        
        Each evidence type beyond the first adds 5 points, capped at 15 points.
        """
        if evidence_diversity <= 1:
            limiting_factors.append({
                "factor": "low_evidence_diversity",
                "value": evidence_diversity,
                "impact": 0,
                "explanation": (
                    f"Only {evidence_diversity} evidence type(s). "
                    "Multiple independent evidence types increase reliability."
                ),
            })
            explainability_notes.append(
                f"Single evidence type limits confidence (diversity: {evidence_diversity})"
            )
            return 0.0
        
        # Each additional type adds 5 points
        additional_types = evidence_diversity - 1
        raw_contribution = additional_types * 5.0
        
        # Cap at 15 points (so 4+ types all give same max bonus)
        max_diversity_contribution = 15.0
        contribution = min(raw_contribution, max_diversity_contribution)
        
        contributing_factors.append({
            "factor": "evidence_diversity",
            "value": evidence_diversity,
            "additional_types": additional_types,
            "contribution": round(contribution, 2),
            "explanation": (
                f"{evidence_diversity} distinct evidence types provide "
                "independent corroboration (reduces correlation risk)."
            ),
        })
        
        explainability_notes.append(
            f"Evidence diversity ({evidence_diversity} types) adds {contribution:.1f} points"
        )
        
        return contribution
    
    def _compute_timing_contribution(
        self,
        timing_similarity: float,
        contributing_factors: List[Dict],
        limiting_factors: List[Dict],
        explainability_notes: List[str],
    ) -> float:
        """
        Compute confidence contribution from timing similarity.
        
        Timing similarity measures how well observed timing patterns
        match expected patterns for the hypothesized path.
        
        Contribution scales with similarity but requires threshold:
        - Below 0.3: No contribution (too weak)
        - 0.3-0.7: Partial contribution (modest evidence)
        - 0.7-1.0: Full contribution (strong evidence)
        
        Max contribution: 15 points
        """
        if timing_similarity < 0.3:
            limiting_factors.append({
                "factor": "weak_timing_similarity",
                "value": round(timing_similarity, 3),
                "threshold": 0.3,
                "impact": 0,
                "explanation": (
                    f"Timing similarity ({timing_similarity:.1%}) below threshold. "
                    "Timing patterns do not meaningfully correlate."
                ),
            })
            explainability_notes.append(
                f"Timing similarity ({timing_similarity:.1%}) too weak to contribute"
            )
            return 0.0
        
        # Scale contribution based on similarity
        # 0.3 maps to 0, 1.0 maps to 15
        normalized = (timing_similarity - 0.3) / 0.7  # Normalize to 0-1
        contribution = normalized * 15.0
        
        strength = "strong" if timing_similarity >= 0.7 else "moderate"
        
        contributing_factors.append({
            "factor": "timing_similarity",
            "value": round(timing_similarity, 3),
            "strength": strength,
            "contribution": round(contribution, 2),
            "explanation": (
                f"Timing patterns show {timing_similarity:.1%} similarity. "
                f"This provides {strength} evidence of correlation."
            ),
        })
        
        explainability_notes.append(
            f"Timing similarity ({timing_similarity:.1%}) adds {contribution:.1f} points "
            f"({strength} correlation)"
        )
        
        return contribution
    
    def _compute_session_overlap_contribution(
        self,
        session_overlap: float,
        contributing_factors: List[Dict],
        limiting_factors: List[Dict],
        explainability_notes: List[str],
    ) -> float:
        """
        Compute confidence contribution from session overlap.
        
        Session overlap measures temporal co-occurrence of traffic
        at guard and exit nodes.
        
        Contribution requires minimum threshold:
        - Below 0.2: No contribution (likely coincidental)
        - 0.2-0.6: Partial contribution
        - 0.6-1.0: Strong contribution
        
        Max contribution: 15 points
        """
        if session_overlap < 0.2:
            limiting_factors.append({
                "factor": "weak_session_overlap",
                "value": round(session_overlap, 3),
                "threshold": 0.2,
                "impact": 0,
                "explanation": (
                    f"Session overlap ({session_overlap:.1%}) below threshold. "
                    "Temporal co-occurrence may be coincidental."
                ),
            })
            explainability_notes.append(
                f"Session overlap ({session_overlap:.1%}) too weak to contribute"
            )
            return 0.0
        
        # Scale contribution
        # 0.2 maps to 0, 1.0 maps to 15
        normalized = (session_overlap - 0.2) / 0.8
        contribution = normalized * 15.0
        
        strength = "strong" if session_overlap >= 0.6 else "moderate"
        
        contributing_factors.append({
            "factor": "session_overlap",
            "value": round(session_overlap, 3),
            "strength": strength,
            "contribution": round(contribution, 2),
            "explanation": (
                f"Session overlap of {session_overlap:.1%} indicates "
                f"{strength} temporal correlation between guard and exit traffic."
            ),
        })
        
        explainability_notes.append(
            f"Session overlap ({session_overlap:.1%}) adds {contribution:.1f} points"
        )
        
        return contribution
    
    def _compute_entropy_penalty(
        self,
        hypothesis_entropy: float,
        contributing_factors: List[Dict],
        limiting_factors: List[Dict],
        explainability_notes: List[str],
    ) -> float:
        """
        Compute confidence penalty from high hypothesis entropy.
        
        High entropy means many hypotheses have similar probabilities,
        indicating the evidence does not clearly distinguish between them.
        
        Penalty increases linearly above threshold:
        - Below 1.0: No penalty (evidence is discriminating)
        - 1.0-2.0: Moderate penalty
        - Above 2.0: Severe penalty (evidence is not discriminating)
        
        Max penalty: 20 points
        """
        if hypothesis_entropy <= 1.0:
            # Low entropy is good - evidence discriminates well
            if hypothesis_entropy < 0.5:
                contributing_factors.append({
                    "factor": "low_entropy",
                    "value": round(hypothesis_entropy, 3),
                    "contribution": 5.0,
                    "explanation": (
                        f"Low entropy ({hypothesis_entropy:.2f}) indicates evidence "
                        "strongly discriminates between hypotheses."
                    ),
                })
                explainability_notes.append(
                    f"Low entropy ({hypothesis_entropy:.2f}) adds 5 points "
                    "(evidence is discriminating)"
                )
                return -5.0  # Negative penalty = bonus
            return 0.0
        
        # Penalty scales with entropy above threshold
        excess_entropy = hypothesis_entropy - 1.0
        
        # Each point of excess entropy adds 10 points of penalty
        raw_penalty = excess_entropy * 10.0
        max_entropy_penalty = 20.0
        penalty = min(raw_penalty, max_entropy_penalty)
        
        severity = "severe" if hypothesis_entropy > HIGH_ENTROPY_THRESHOLD else "moderate"
        
        limiting_factors.append({
            "factor": "high_entropy",
            "value": round(hypothesis_entropy, 3),
            "threshold": 1.0,
            "penalty": round(penalty, 2),
            "explanation": (
                f"High entropy ({hypothesis_entropy:.2f}) indicates {severity} "
                "uncertainty - evidence does not clearly distinguish between hypotheses."
            ),
        })
        
        explainability_notes.append(
            f"High entropy ({hypothesis_entropy:.2f}) reduces confidence by "
            f"{penalty:.1f} points ({severity} uncertainty)"
        )
        
        return penalty
    
    def _compute_evidence_decay(
        self,
        has_contradictory_evidence: bool,
        missing_expected_evidence: bool,
        contributing_factors: List[Dict],
        limiting_factors: List[Dict],
        explainability_notes: List[str],
    ) -> float:
        """
        Compute confidence penalty for problematic evidence patterns.
        
        Applies decay when:
        - Contradictory evidence exists (different evidence points to different conclusions)
        - Expected evidence is missing (should see something but don't)
        
        Each issue applies a separate penalty.
        """
        total_penalty = 0.0
        
        if has_contradictory_evidence:
            contradiction_penalty = 15.0
            total_penalty += contradiction_penalty
            
            limiting_factors.append({
                "factor": "contradictory_evidence",
                "penalty": contradiction_penalty,
                "explanation": (
                    "Some evidence contradicts the hypothesis. "
                    "This significantly reduces confidence."
                ),
            })
            
            explainability_notes.append(
                f"Contradictory evidence detected: -{contradiction_penalty:.1f} points"
            )
        
        if missing_expected_evidence:
            missing_penalty = 10.0
            total_penalty += missing_penalty
            
            limiting_factors.append({
                "factor": "missing_expected_evidence",
                "penalty": missing_penalty,
                "explanation": (
                    "Expected corroborating evidence is absent. "
                    "This reduces confidence in the hypothesis."
                ),
            })
            
            explainability_notes.append(
                f"Expected evidence missing: -{missing_penalty:.1f} points"
            )
        
        return total_penalty
    
    def _determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """
        Map numeric confidence to categorical level.
        
        Thresholds:
        - LOW: 0-40 (insufficient or inconsistent evidence)
        - MEDIUM: 40-65 (some corroboration, significant uncertainty)
        - HIGH: 65-85 (strong corroboration, still probabilistic)
        """
        if confidence >= 65:
            return ConfidenceLevel.HIGH
        elif confidence >= 40:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_uncertainty_statement(
        self,
        confidence: float,
        confidence_level: ConfidenceLevel,
        evidence_count: int,
    ) -> str:
        """
        Generate explicit uncertainty disclaimer for the result.
        
        This statement is REQUIRED for all outputs to prevent
        misuse as definitive identification.
        """
        base_statement = (
            "IMPORTANT: This confidence score reflects evidence quality and consistency, "
            "NOT the probability that this hypothesis identifies the actual source. "
        )
        
        if confidence_level == ConfidenceLevel.LOW:
            return (
                base_statement +
                f"With {confidence_level.value} confidence ({confidence:.1f}/100), "
                "the available evidence is insufficient for investigative prioritization. "
                "This hypothesis should not be acted upon without additional evidence."
            )
        elif confidence_level == ConfidenceLevel.MEDIUM:
            return (
                base_statement +
                f"With {confidence_level.value} confidence ({confidence:.1f}/100), "
                "there is some corroborating evidence but significant uncertainty remains. "
                "This hypothesis may warrant further investigation but requires "
                "additional independent verification before any conclusions."
            )
        else:  # HIGH
            return (
                base_statement +
                f"With {confidence_level.value} confidence ({confidence:.1f}/100), "
                "the evidence shows strong correlation. However, this is probabilistic "
                "analysis based on observable patterns - it is NOT definitive identification. "
                "Further forensic investigation is required before any conclusions. "
                f"Based on {evidence_count} evidence item(s)."
            )


# ============================================================================
# LEGACY CONFIDENCE CALCULATOR (Backward Compatibility Wrapper)
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


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def compute_forensic_confidence(
    timing_similarity: float = 0.0,
    session_overlap: float = 0.0,
    evidence_count: int = 0,
    evidence_diversity: int = 0,
    hypothesis_entropy: float = 0.0,
    has_contradictory_evidence: bool = False,
    missing_expected_evidence: bool = False,
) -> Dict[str, Any]:
    """
    Convenience function to compute forensic confidence.
    
    Creates a ForensicConfidenceEngine instance and computes confidence.
    
    Args:
        timing_similarity: How well timing patterns match (0.0-1.0)
        session_overlap: Temporal session overlap ratio (0.0-1.0)
        evidence_count: Number of independent evidence items
        evidence_diversity: Number of distinct evidence types
        hypothesis_entropy: Entropy of hypothesis distribution
        has_contradictory_evidence: Whether any evidence contradicts
        missing_expected_evidence: Whether expected evidence is absent
    
    Returns:
        Dictionary with confidence_score, confidence_level, factors, and notes
    """
    engine = ForensicConfidenceEngine()
    result = engine.compute_confidence(
        timing_similarity=timing_similarity,
        session_overlap=session_overlap,
        evidence_count=evidence_count,
        evidence_diversity=evidence_diversity,
        hypothesis_entropy=hypothesis_entropy,
        has_contradictory_evidence=has_contradictory_evidence,
        missing_expected_evidence=missing_expected_evidence,
    )
    return result.to_dict()


def create_evidence_input(
    timing_similarity: float = 0.0,
    session_overlap: float = 0.0,
    traffic_pattern_match: float = 0.0,
    bandwidth_feasibility: float = 0.0,
    circuit_lifetime_valid: float = 0.0,
) -> EvidenceInput:
    """
    Create an EvidenceInput object for structured input.
    
    Args:
        timing_similarity: How well timing patterns match (0.0-1.0)
        session_overlap: Temporal session overlap ratio (0.0-1.0)
        traffic_pattern_match: Traffic signature similarity (0.0-1.0)
        bandwidth_feasibility: Bandwidth constraints satisfied (0.0-1.0)
        circuit_lifetime_valid: Within TOR circuit lifetime bounds (0.0-1.0)
    
    Returns:
        EvidenceInput dataclass instance
    """
    return EvidenceInput(
        timing_similarity=timing_similarity,
        session_overlap=session_overlap,
        traffic_pattern_match=traffic_pattern_match,
        bandwidth_feasibility=bandwidth_feasibility,
        circuit_lifetime_valid=circuit_lifetime_valid,
    )


def explain_confidence_score(confidence_result: ConfidenceResult) -> str:
    """
    Generate a human-readable explanation of a confidence result.
    
    Args:
        confidence_result: ConfidenceResult from compute_confidence()
    
    Returns:
        Multi-line string explaining the confidence score
    """
    lines = [
        f"FORENSIC CONFIDENCE ASSESSMENT",
        f"=" * 40,
        f"Score: {confidence_result.confidence_score}/100 ({confidence_result.confidence_level.value})",
        f"",
        f"CONTRIBUTING FACTORS:",
    ]
    
    for factor in confidence_result.contributing_factors:
        lines.append(f"  + {factor.get('factor', 'unknown')}: {factor.get('explanation', '')}")
    
    if not confidence_result.contributing_factors:
        lines.append("  (none)")
    
    lines.append("")
    lines.append("LIMITING FACTORS:")
    
    for factor in confidence_result.limiting_factors:
        lines.append(f"  - {factor.get('factor', 'unknown')}: {factor.get('explanation', '')}")
    
    if not confidence_result.limiting_factors:
        lines.append("  (none)")
    
    lines.append("")
    lines.append("NOTES:")
    for note in confidence_result.explainability_notes:
        lines.append(f"  • {note}")
    
    lines.append("")
    lines.append("UNCERTAINTY STATEMENT:")
    lines.append(f"  {confidence_result.uncertainty_statement}")
    
    return "\n".join(lines)


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Main engine
    "ForensicConfidenceEngine",
    
    # Data structures
    "EvidenceInput",
    "CorrelationHypothesisInput",
    "ConfidenceResult",
    "ConfidenceLevel",
    
    # Legacy (backward compatibility)
    "ConfidenceCalculator",
    "EvidenceMetrics",
    "SessionObservation",
    "PathObservation",
    
    # Convenience functions
    "compute_forensic_confidence",
    "create_evidence_input",
    "explain_confidence_score",
    
    # Constants
    "BASELINE_CONFIDENCE",
    "MAX_CONFIDENCE",
    "MIN_EVIDENCE_FOR_INCREASE",
    "HIGH_ENTROPY_THRESHOLD",
    "DIVERSITY_THRESHOLD",
]
