"""
Probabilistic Hypothesis Modeling for TOR Path Inference
=========================================================

This module maintains and updates multiple TOR path hypotheses using Bayesian
reasoning as new exit observations are added. It models TOR guard node behavior
including guard persistence and penalizes unlikely guard rotation patterns.

CRITICAL DISCLAIMER:
--------------------
This system performs probabilistic inference based on observable network metadata.
It does NOT deanonymize TOR users. All outputs are ranked hypotheses that require
independent verification and cannot be used as sole evidence for identification.

Key Principles:
1. GUARD PERSISTENCE: Guards are reused for extended periods (weeks to months)
2. MULTIPLE HYPOTHESES: Always maintain competing hypotheses
3. UNCERTAINTY TRACKING: Explicit entropy and evidence strength metrics
4. EVIDENCE DECAY: Stale evidence loses weight over time

Author: TOR-Unveil Project (TN Police Hackathon 2025)
License: For authorized law enforcement forensic use only
"""

from __future__ import annotations

import uuid
import math
import logging
from datetime import datetime, timedelta
from typing import (
    List, Dict, Any, Optional, Tuple,
    Set, DefaultDict, NamedTuple
)
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum, auto
import statistics

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

class HypothesisConfig:
    """
    Configuration for hypothesis modeling.
    Based on documented TOR guard behavior.
    """
    # Guard persistence parameters (based on TOR specification)
    # Guards are typically used for 2-3 months before rotation
    GUARD_PERSISTENCE_DAYS: float = 60.0  # Expected guard lifetime
    GUARD_MIN_PERSISTENCE_DAYS: float = 14.0  # Minimum expected persistence
    GUARD_ROTATION_PENALTY_FACTOR: float = 0.3  # Penalty for frequent rotation
    
    # Evidence decay parameters
    EVIDENCE_HALF_LIFE_HOURS: float = 24.0  # Evidence strength halves after this time
    STALE_EVIDENCE_THRESHOLD_HOURS: float = 168.0  # 1 week - evidence becomes very weak
    
    # Hypothesis management
    MAX_ACTIVE_HYPOTHESES: int = 100  # Maximum hypotheses to maintain
    MIN_HYPOTHESIS_PROBABILITY: float = 0.001  # Prune below this threshold
    PRIOR_SMOOTHING_FACTOR: float = 0.01  # Laplace smoothing for priors
    
    # Entropy thresholds
    HIGH_ENTROPY_THRESHOLD: float = 3.0  # Bits - high uncertainty
    LOW_ENTROPY_THRESHOLD: float = 1.0   # Bits - good convergence
    
    # Bayesian update parameters
    LIKELIHOOD_SENSITIVITY: float = 2.0  # Exponent for likelihood scaling


class EvidenceStrength(Enum):
    """Classification of evidence strength."""
    VERY_STRONG = auto()  # Multiple corroborating observations
    STRONG = auto()       # Clear supporting evidence
    MODERATE = auto()     # Some supporting evidence
    WEAK = auto()         # Limited evidence
    VERY_WEAK = auto()    # Minimal or conflicting evidence
    STALE = auto()        # Evidence has decayed significantly


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class ExitObservation:
    """
    A single exit node observation that updates hypotheses.
    """
    observation_id: str
    exit_fingerprint: str
    exit_nickname: str
    timestamp: datetime
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_score: float = 0.5  # 0-1, quality of this observation
    
    def age_hours(self, reference_time: datetime = None) -> float:
        """Calculate age of observation in hours."""
        ref = reference_time or datetime.utcnow()
        return (ref - self.timestamp).total_seconds() / 3600.0
    
    def decay_factor(self, config: HypothesisConfig = None) -> float:
        """
        Calculate evidence decay factor based on age.
        Uses exponential decay with configurable half-life.
        """
        config = config or HypothesisConfig()
        age = self.age_hours()
        
        if age > config.STALE_EVIDENCE_THRESHOLD_HOURS:
            return 0.1  # Very stale
        
        # Exponential decay
        decay = math.exp(-0.693 * age / config.EVIDENCE_HALF_LIFE_HOURS)
        return max(0.1, decay)


@dataclass
class GuardHypothesis:
    """
    A hypothesis about which guard node is being used.
    
    Each hypothesis represents: "Guard G is the entry point for observed traffic"
    """
    hypothesis_id: str
    guard_fingerprint: str
    guard_nickname: str
    
    # Bayesian components
    prior_probability: float
    likelihood: float
    posterior_probability: float
    
    # Evidence tracking
    exit_observations: List[ExitObservation] = field(default_factory=list)
    first_observation: Optional[datetime] = None
    last_observation: Optional[datetime] = None
    
    # Guard behavior modeling
    estimated_guard_start: Optional[datetime] = None
    guard_rotation_count: int = 0  # Number of times guard changed
    
    # Derived metrics
    evidence_count: int = 0
    effective_evidence_count: float = 0.0  # Decay-adjusted
    evidence_strength: EvidenceStrength = EvidenceStrength.VERY_WEAK
    
    # Uncertainty metrics
    entropy_contribution: float = 0.0  # Bits
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def exit_nodes_seen(self) -> Set[str]:
        """Unique exit nodes observed with this guard hypothesis."""
        return {obs.exit_fingerprint for obs in self.exit_observations}
    
    @property
    def observation_span_hours(self) -> float:
        """Time span from first to last observation."""
        if self.first_observation and self.last_observation:
            return (self.last_observation - self.first_observation).total_seconds() / 3600.0
        return 0.0
    
    def compute_effective_evidence(self, config: HypothesisConfig = None) -> float:
        """
        Compute decay-adjusted effective evidence count.
        Recent observations count more than older ones.
        """
        config = config or HypothesisConfig()
        
        if not self.exit_observations:
            return 0.0
        
        total = sum(
            obs.evidence_score * obs.decay_factor(config)
            for obs in self.exit_observations
        )
        return total
    
    def update_evidence_strength(self, config: HypothesisConfig = None) -> None:
        """Update evidence strength classification based on current state."""
        config = config or HypothesisConfig()
        
        effective = self.compute_effective_evidence(config)
        self.effective_evidence_count = effective
        
        # Check for staleness first
        if self.exit_observations:
            newest = max(obs.timestamp for obs in self.exit_observations)
            age_hours = (datetime.utcnow() - newest).total_seconds() / 3600.0
            if age_hours > config.STALE_EVIDENCE_THRESHOLD_HOURS:
                self.evidence_strength = EvidenceStrength.STALE
                return
        
        # Classify based on effective evidence
        if effective >= 5.0:
            self.evidence_strength = EvidenceStrength.VERY_STRONG
        elif effective >= 3.0:
            self.evidence_strength = EvidenceStrength.STRONG
        elif effective >= 1.5:
            self.evidence_strength = EvidenceStrength.MODERATE
        elif effective >= 0.5:
            self.evidence_strength = EvidenceStrength.WEAK
        else:
            self.evidence_strength = EvidenceStrength.VERY_WEAK
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize hypothesis for API response."""
        return {
            "hypothesis_id": self.hypothesis_id,
            "guard_node": {
                "fingerprint": self.guard_fingerprint,
                "nickname": self.guard_nickname,
            },
            "exit_nodes_seen": list(self.exit_nodes_seen),
            "prior_probability": round(self.prior_probability, 6),
            "likelihood": round(self.likelihood, 6),
            "posterior_probability": round(self.posterior_probability, 6),
            "evidence_count": self.evidence_count,
            "effective_evidence_count": round(self.effective_evidence_count, 2),
            "evidence_strength": self.evidence_strength.name,
            "entropy_contribution": round(self.entropy_contribution, 4),
            "observation_span_hours": round(self.observation_span_hours, 2),
            "first_observation": self.first_observation.isoformat() if self.first_observation else None,
            "last_observation": self.last_observation.isoformat() if self.last_observation else None,
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class HypothesisExplanation:
    """
    Human-readable explanation for a hypothesis ranking.
    """
    summary: str
    supporting_factors: List[str]
    weakening_factors: List[str]
    uncertainty_notes: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RankedHypothesis:
    """
    A hypothesis with ranking information for output.
    """
    rank: int
    hypothesis: GuardHypothesis
    explanation: HypothesisExplanation
    
    def to_dict(self) -> Dict[str, Any]:
        result = self.hypothesis.to_dict()
        result["rank"] = self.rank
        result["explanation"] = self.explanation.to_dict()
        return result


# =============================================================================
# BAYESIAN HYPOTHESIS ENGINE
# =============================================================================

class BayesianHypothesisEngine:
    """
    Maintains and updates multiple guard hypotheses using Bayesian inference.
    
    Key behaviors:
    1. Guard persistence modeling - penalizes frequent rotation
    2. Incremental updates - new observations update posteriors
    3. Entropy tracking - monitors convergence
    4. Hypothesis pruning - removes low-probability hypotheses
    """
    
    def __init__(self, config: HypothesisConfig = None):
        self.config = config or HypothesisConfig()
        
        # Active hypotheses indexed by guard fingerprint
        self.hypotheses: Dict[str, GuardHypothesis] = {}
        
        # Guard priors (from consensus weights or uniform)
        self.guard_priors: Dict[str, float] = {}
        
        # Observation history
        self.all_observations: List[ExitObservation] = []
        self.observations_by_exit: DefaultDict[str, List[ExitObservation]] = defaultdict(list)
        
        # Tracking metrics
        self.total_updates: int = 0
        self.entropy_history: List[Tuple[datetime, float]] = []
        
        # Guard rotation tracking
        self.current_dominant_guard: Optional[str] = None
        self.guard_rotation_timestamps: List[datetime] = []
    
    def set_guard_priors(
        self,
        guards: List[Dict[str, Any]],
        use_consensus_weights: bool = True
    ) -> None:
        """
        Set prior probabilities for guard nodes.
        
        Args:
            guards: List of guard relay dictionaries
            use_consensus_weights: If True, weight by consensus/bandwidth
        """
        if not guards:
            logger.warning("No guards provided for priors")
            return
        
        if use_consensus_weights:
            # Use consensus weight or bandwidth as proxy
            weights = {}
            for g in guards:
                fp = g.get("fingerprint")
                if not fp:
                    continue
                weight = g.get("consensus_weight") or g.get("advertised_bandwidth", 1.0) or 1.0
                weights[fp] = float(weight)
            
            # Normalize with smoothing
            total = sum(weights.values()) + len(weights) * self.config.PRIOR_SMOOTHING_FACTOR
            self.guard_priors = {
                fp: (w + self.config.PRIOR_SMOOTHING_FACTOR) / total
                for fp, w in weights.items()
            }
        else:
            # Uniform priors
            n = len(guards)
            self.guard_priors = {
                g["fingerprint"]: 1.0 / n
                for g in guards
                if g.get("fingerprint")
            }
        
        logger.info(f"Set priors for {len(self.guard_priors)} guard nodes")
    
    def get_or_create_hypothesis(
        self,
        guard_fingerprint: str,
        guard_nickname: str = "unknown"
    ) -> GuardHypothesis:
        """
        Get existing hypothesis or create new one for a guard.
        """
        if guard_fingerprint in self.hypotheses:
            return self.hypotheses[guard_fingerprint]
        
        # Get prior probability
        prior = self.guard_priors.get(
            guard_fingerprint,
            self.config.PRIOR_SMOOTHING_FACTOR
        )
        
        hypothesis = GuardHypothesis(
            hypothesis_id=str(uuid.uuid4()),
            guard_fingerprint=guard_fingerprint,
            guard_nickname=guard_nickname,
            prior_probability=prior,
            likelihood=1.0,  # Start neutral
            posterior_probability=prior,
        )
        
        self.hypotheses[guard_fingerprint] = hypothesis
        return hypothesis
    
    def compute_likelihood(
        self,
        hypothesis: GuardHypothesis,
        observation: ExitObservation,
        guard_metadata: Dict[str, Any] = None
    ) -> float:
        """
        Compute likelihood P(observation | hypothesis).
        
        Factors:
        1. Evidence quality from observation
        2. Guard persistence consistency
        3. Exit node diversity (TOR uses different exits)
        """
        guard_metadata = guard_metadata or {}
        
        # Base likelihood from observation quality
        base_likelihood = observation.evidence_score
        
        # Guard persistence factor
        # If this guard has been seen before, increased likelihood
        # If new guard after long gap, penalize for rotation
        persistence_factor = 1.0
        
        if hypothesis.exit_observations:
            last_obs_time = hypothesis.last_observation
            if last_obs_time:
                gap_hours = observation.age_hours(last_obs_time)
                
                # Short gap (< 1 hour) - consistent with guard persistence
                if gap_hours < 1.0:
                    persistence_factor = 1.2
                # Medium gap (1-24 hours) - still reasonable
                elif gap_hours < 24.0:
                    persistence_factor = 1.0
                # Long gap (1-7 days) - slightly less likely same guard
                elif gap_hours < 168.0:
                    persistence_factor = 0.8
                # Very long gap - possible guard rotation
                else:
                    persistence_factor = 0.5
        else:
            # First observation for this hypothesis
            # Check if another hypothesis was dominant
            if self.current_dominant_guard and self.current_dominant_guard != hypothesis.guard_fingerprint:
                # Switching guards is penalized
                persistence_factor = self.config.GUARD_ROTATION_PENALTY_FACTOR
        
        # Exit diversity factor
        # TOR clients use different exit nodes, so seeing different exits
        # with the same guard is expected
        exit_diversity_factor = 1.0
        seen_exits = hypothesis.exit_nodes_seen
        if observation.exit_fingerprint in seen_exits:
            # Same exit seen again - slightly less informative
            exit_diversity_factor = 0.9
        elif len(seen_exits) > 0:
            # New exit with same guard - expected behavior
            exit_diversity_factor = 1.1
        
        # Combine factors
        likelihood = (
            base_likelihood *
            persistence_factor *
            exit_diversity_factor
        )
        
        # Apply sensitivity scaling
        likelihood = math.pow(likelihood, self.config.LIKELIHOOD_SENSITIVITY)
        
        return max(0.001, min(1.0, likelihood))
    
    def update_with_observation(
        self,
        observation: ExitObservation,
        candidate_guards: List[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Update all hypotheses with a new exit observation.
        
        Args:
            observation: The exit observation
            candidate_guards: Optional list of candidate guard nodes
                             If provided, creates hypotheses for each
        
        Returns:
            Dict mapping guard fingerprint to updated posterior
        """
        self.total_updates += 1
        self.all_observations.append(observation)
        self.observations_by_exit[observation.exit_fingerprint].append(observation)
        
        # Create hypotheses for candidate guards if provided
        if candidate_guards:
            for guard in candidate_guards:
                fp = guard.get("fingerprint")
                if fp and fp not in self.hypotheses:
                    self.get_or_create_hypothesis(
                        fp,
                        guard.get("nickname", "unknown")
                    )
        
        if not self.hypotheses:
            logger.warning("No hypotheses to update")
            return {}
        
        # Compute likelihoods for all hypotheses
        likelihoods = {}
        for fp, hypothesis in self.hypotheses.items():
            likelihood = self.compute_likelihood(
                hypothesis,
                observation,
                candidate_guards[0] if candidate_guards else None
            )
            likelihoods[fp] = likelihood
            hypothesis.likelihood = likelihood
        
        # Bayesian update: posterior ??? prior ?? likelihood
        unnormalized_posteriors = {}
        for fp, hypothesis in self.hypotheses.items():
            unnormalized = hypothesis.prior_probability * likelihoods[fp]
            unnormalized_posteriors[fp] = unnormalized
        
        # Normalize to get valid probability distribution
        total = sum(unnormalized_posteriors.values())
        if total <= 0:
            total = 1.0  # Avoid division by zero
        
        posteriors = {}
        for fp, unnorm in unnormalized_posteriors.items():
            posterior = unnorm / total
            posteriors[fp] = posterior
            
            hypothesis = self.hypotheses[fp]
            hypothesis.posterior_probability = posterior
            hypothesis.updated_at = datetime.utcnow()
            
            # Update observation tracking
            hypothesis.exit_observations.append(observation)
            hypothesis.evidence_count += 1
            
            if hypothesis.first_observation is None:
                hypothesis.first_observation = observation.timestamp
            hypothesis.last_observation = observation.timestamp
            
            # Update evidence strength
            hypothesis.update_evidence_strength(self.config)
        
        # Update dominant guard tracking
        self._update_dominant_guard()
        
        # Compute and track entropy
        entropy = self.compute_entropy()
        self.entropy_history.append((datetime.utcnow(), entropy))
        
        # Update entropy contributions
        for fp, hypothesis in self.hypotheses.items():
            p = hypothesis.posterior_probability
            if p > 0:
                hypothesis.entropy_contribution = -p * math.log2(p)
            else:
                hypothesis.entropy_contribution = 0.0
        
        # Prune low-probability hypotheses
        self._prune_hypotheses()
        
        # Update priors for next iteration (moving average)
        self._update_priors_from_posteriors()
        
        return posteriors
    
    def _update_dominant_guard(self) -> None:
        """Track which guard hypothesis is currently dominant."""
        if not self.hypotheses:
            return
        
        # Find hypothesis with highest posterior
        best_fp = max(
            self.hypotheses.keys(),
            key=lambda fp: self.hypotheses[fp].posterior_probability
        )
        
        if self.current_dominant_guard != best_fp:
            if self.current_dominant_guard is not None:
                # Guard rotation detected
                self.guard_rotation_timestamps.append(datetime.utcnow())
                
                # Update rotation count for the old dominant
                if self.current_dominant_guard in self.hypotheses:
                    self.hypotheses[self.current_dominant_guard].guard_rotation_count += 1
            
            self.current_dominant_guard = best_fp
    
    def _prune_hypotheses(self) -> None:
        """Remove hypotheses with negligible probability."""
        to_remove = []
        
        for fp, hypothesis in self.hypotheses.items():
            if hypothesis.posterior_probability < self.config.MIN_HYPOTHESIS_PROBABILITY:
                # Only prune if evidence is also weak
                if hypothesis.evidence_strength in (
                    EvidenceStrength.VERY_WEAK,
                    EvidenceStrength.STALE
                ):
                    to_remove.append(fp)
        
        for fp in to_remove:
            del self.hypotheses[fp]
            logger.debug(f"Pruned hypothesis for guard {fp}")
        
        # Limit total hypotheses
        if len(self.hypotheses) > self.config.MAX_ACTIVE_HYPOTHESES:
            # Keep top hypotheses by posterior probability
            sorted_fps = sorted(
                self.hypotheses.keys(),
                key=lambda fp: self.hypotheses[fp].posterior_probability,
                reverse=True
            )
            
            for fp in sorted_fps[self.config.MAX_ACTIVE_HYPOTHESES:]:
                del self.hypotheses[fp]
    
    def _update_priors_from_posteriors(self, learning_rate: float = 0.1) -> None:
        """
        Update priors using exponential moving average of posteriors.
        This allows the model to learn from accumulated evidence.
        """
        for fp, hypothesis in self.hypotheses.items():
            old_prior = hypothesis.prior_probability
            new_prior = (1 - learning_rate) * old_prior + learning_rate * hypothesis.posterior_probability
            hypothesis.prior_probability = new_prior
            
            # Also update global priors
            if fp in self.guard_priors:
                self.guard_priors[fp] = new_prior
    
    def compute_entropy(self) -> float:
        """
        Compute Shannon entropy of the posterior distribution.
        
        H = -?? p(i) ?? log2(p(i))
        
        Higher entropy = more uncertainty
        Lower entropy = convergence toward specific hypotheses
        """
        if not self.hypotheses:
            return float('inf')
        
        entropy = 0.0
        for hypothesis in self.hypotheses.values():
            p = hypothesis.posterior_probability
            if p > 0:
                entropy -= p * math.log2(p)
        
        return entropy
    
    def entropy_reduction_rate(self) -> Optional[float]:
        """
        Compute rate of entropy reduction (bits per observation).
        Positive = uncertainty decreasing (good)
        Negative = uncertainty increasing (conflicting evidence)
        """
        if len(self.entropy_history) < 2:
            return None
        
        # Compare recent entropy to earlier
        recent = self.entropy_history[-1][1]
        earlier = self.entropy_history[0][1]
        
        n_updates = len(self.entropy_history)
        
        if n_updates > 1:
            rate = (earlier - recent) / n_updates
            return rate
        
        return 0.0
    
    def get_ranked_hypotheses(
        self,
        top_k: int = 10,
        include_explanations: bool = True
    ) -> List[RankedHypothesis]:
        """
        Get hypotheses ranked by posterior probability.
        
        Args:
            top_k: Number of top hypotheses to return
            include_explanations: Whether to generate explanations
        
        Returns:
            List of RankedHypothesis objects
        """
        # Sort by posterior probability
        sorted_hypotheses = sorted(
            self.hypotheses.values(),
            key=lambda h: h.posterior_probability,
            reverse=True
        )[:top_k]
        
        ranked = []
        for i, hypothesis in enumerate(sorted_hypotheses):
            explanation = self._generate_explanation(hypothesis) if include_explanations else HypothesisExplanation(
                summary="",
                supporting_factors=[],
                weakening_factors=[],
                uncertainty_notes=[]
            )
            
            ranked.append(RankedHypothesis(
                rank=i + 1,
                hypothesis=hypothesis,
                explanation=explanation
            ))
        
        return ranked
    
    def _generate_explanation(self, hypothesis: GuardHypothesis) -> HypothesisExplanation:
        """Generate human-readable explanation for a hypothesis."""
        supporting = []
        weakening = []
        uncertainty = []
        
        # Evidence strength
        if hypothesis.evidence_strength == EvidenceStrength.VERY_STRONG:
            supporting.append("Multiple corroborating observations support this hypothesis")
        elif hypothesis.evidence_strength == EvidenceStrength.STRONG:
            supporting.append("Strong supporting evidence from observations")
        elif hypothesis.evidence_strength == EvidenceStrength.STALE:
            weakening.append("Evidence is stale and may no longer be reliable")
        elif hypothesis.evidence_strength == EvidenceStrength.VERY_WEAK:
            weakening.append("Limited evidence available")
        
        # Exit node diversity
        n_exits = len(hypothesis.exit_nodes_seen)
        if n_exits > 5:
            supporting.append(f"Observed with {n_exits} different exit nodes (consistent with TOR behavior)")
        elif n_exits == 1:
            uncertainty.append("Only one exit node observed; pattern not yet established")
        
        # Observation span
        span = hypothesis.observation_span_hours
        if span > 24:
            supporting.append(f"Evidence spans {span:.1f} hours (consistent with guard persistence)")
        elif span < 1 and hypothesis.evidence_count > 1:
            uncertainty.append("All observations within short time window")
        
        # Posterior probability
        posterior = hypothesis.posterior_probability
        if posterior > 0.5:
            supporting.append(f"High posterior probability ({posterior:.1%})")
        elif posterior < 0.1:
            weakening.append(f"Low posterior probability ({posterior:.1%})")
        else:
            uncertainty.append(f"Moderate posterior probability ({posterior:.1%})")
        
        # Guard rotation
        if hypothesis.guard_rotation_count > 0:
            weakening.append(f"Guard rotation detected {hypothesis.guard_rotation_count} time(s)")
        
        # Summary
        if hypothesis.evidence_strength in (EvidenceStrength.VERY_STRONG, EvidenceStrength.STRONG):
            summary = f"Strong hypothesis: Guard {hypothesis.guard_nickname} with {hypothesis.evidence_count} observations"
        elif hypothesis.evidence_strength == EvidenceStrength.STALE:
            summary = f"Stale hypothesis: Guard {hypothesis.guard_nickname} - evidence is old"
        else:
            summary = f"Hypothesis: Guard {hypothesis.guard_nickname} with {hypothesis.evidence_count} observation(s)"
        
        return HypothesisExplanation(
            summary=summary,
            supporting_factors=supporting,
            weakening_factors=weakening,
            uncertainty_notes=uncertainty
        )
    
    def get_state_summary(self) -> Dict[str, Any]:
        """Get summary of current hypothesis state."""
        entropy = self.compute_entropy()
        entropy_rate = self.entropy_reduction_rate()
        
        # Uncertainty classification
        if entropy > self.config.HIGH_ENTROPY_THRESHOLD:
            uncertainty_level = "high"
            uncertainty_description = "Many competing hypotheses; more evidence needed"
        elif entropy < self.config.LOW_ENTROPY_THRESHOLD:
            uncertainty_level = "low"
            uncertainty_description = "Convergence toward specific hypothesis/hypotheses"
        else:
            uncertainty_level = "moderate"
            uncertainty_description = "Some differentiation between hypotheses"
        
        return {
            "total_hypotheses": len(self.hypotheses),
            "total_observations": len(self.all_observations),
            "total_updates": self.total_updates,
            "entropy": round(entropy, 4),
            "entropy_reduction_rate": round(entropy_rate, 4) if entropy_rate else None,
            "uncertainty_level": uncertainty_level,
            "uncertainty_description": uncertainty_description,
            "dominant_guard": self.current_dominant_guard,
            "guard_rotations_detected": len(self.guard_rotation_timestamps),
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export complete state for persistence."""
        return {
            "hypotheses": {
                fp: {
                    "hypothesis_id": h.hypothesis_id,
                    "guard_fingerprint": h.guard_fingerprint,
                    "guard_nickname": h.guard_nickname,
                    "prior_probability": h.prior_probability,
                    "likelihood": h.likelihood,
                    "posterior_probability": h.posterior_probability,
                    "evidence_count": h.evidence_count,
                    "effective_evidence_count": h.effective_evidence_count,
                    "evidence_strength": h.evidence_strength.name,
                    "exit_observations": [
                        {
                            "observation_id": obs.observation_id,
                            "exit_fingerprint": obs.exit_fingerprint,
                            "exit_nickname": obs.exit_nickname,
                            "timestamp": obs.timestamp.isoformat(),
                            "evidence_score": obs.evidence_score,
                        }
                        for obs in h.exit_observations
                    ],
                    "first_observation": h.first_observation.isoformat() if h.first_observation else None,
                    "last_observation": h.last_observation.isoformat() if h.last_observation else None,
                    "guard_rotation_count": h.guard_rotation_count,
                    "created_at": h.created_at.isoformat(),
                    "updated_at": h.updated_at.isoformat(),
                }
                for fp, h in self.hypotheses.items()
            },
            "guard_priors": self.guard_priors,
            "total_updates": self.total_updates,
            "current_dominant_guard": self.current_dominant_guard,
            "guard_rotation_timestamps": [ts.isoformat() for ts in self.guard_rotation_timestamps],
            "entropy_history": [
                {"timestamp": ts.isoformat(), "entropy": e}
                for ts, e in self.entropy_history[-100:]  # Keep last 100
            ],
            "exported_at": datetime.utcnow().isoformat(),
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """Import state from persistence."""
        if not state:
            return
        
        self.guard_priors = state.get("guard_priors", {})
        self.total_updates = state.get("total_updates", 0)
        self.current_dominant_guard = state.get("current_dominant_guard")
        
        # Import rotation timestamps
        self.guard_rotation_timestamps = [
            datetime.fromisoformat(ts)
            for ts in state.get("guard_rotation_timestamps", [])
        ]
        
        # Import entropy history
        self.entropy_history = [
            (datetime.fromisoformat(item["timestamp"]), item["entropy"])
            for item in state.get("entropy_history", [])
        ]
        
        # Import hypotheses
        for fp, h_data in state.get("hypotheses", {}).items():
            # Parse observations
            observations = [
                ExitObservation(
                    observation_id=obs["observation_id"],
                    exit_fingerprint=obs["exit_fingerprint"],
                    exit_nickname=obs["exit_nickname"],
                    timestamp=datetime.fromisoformat(obs["timestamp"]),
                    evidence_score=obs["evidence_score"],
                )
                for obs in h_data.get("exit_observations", [])
            ]
            
            hypothesis = GuardHypothesis(
                hypothesis_id=h_data["hypothesis_id"],
                guard_fingerprint=h_data["guard_fingerprint"],
                guard_nickname=h_data["guard_nickname"],
                prior_probability=h_data["prior_probability"],
                likelihood=h_data["likelihood"],
                posterior_probability=h_data["posterior_probability"],
                exit_observations=observations,
                first_observation=datetime.fromisoformat(h_data["first_observation"]) if h_data.get("first_observation") else None,
                last_observation=datetime.fromisoformat(h_data["last_observation"]) if h_data.get("last_observation") else None,
                evidence_count=h_data["evidence_count"],
                effective_evidence_count=h_data["effective_evidence_count"],
                guard_rotation_count=h_data.get("guard_rotation_count", 0),
                created_at=datetime.fromisoformat(h_data["created_at"]),
                updated_at=datetime.fromisoformat(h_data["updated_at"]),
            )
            
            # Set evidence strength enum
            strength_name = h_data.get("evidence_strength", "VERY_WEAK")
            hypothesis.evidence_strength = EvidenceStrength[strength_name]
            
            self.hypotheses[fp] = hypothesis
            
            # Also add observations to tracking
            for obs in observations:
                self.all_observations.append(obs)
                self.observations_by_exit[obs.exit_fingerprint].append(obs)


# =============================================================================
# HIGH-LEVEL INFERENCE MANAGER
# =============================================================================

class ProbabilisticPathInference:
    """
    High-level manager for probabilistic TOR path inference.
    
    Integrates:
    - BayesianHypothesisEngine for hypothesis management
    - Guard metadata tracking
    - Result formatting for API responses
    """
    
    def __init__(self, config: HypothesisConfig = None):
        self.config = config or HypothesisConfig()
        self.engine = BayesianHypothesisEngine(self.config)
        
        # Guard metadata cache
        self.guard_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Session tracking
        self.session_observations: DefaultDict[str, List[str]] = defaultdict(list)
    
    def initialize_guards(
        self,
        guards: List[Dict[str, Any]],
        use_consensus_weights: bool = True
    ) -> None:
        """
        Initialize with guard relay list.
        
        Args:
            guards: List of guard relay dictionaries
            use_consensus_weights: Weight priors by consensus/bandwidth
        """
        self.engine.set_guard_priors(guards, use_consensus_weights)
        
        # Cache guard metadata
        for guard in guards:
            fp = guard.get("fingerprint")
            if fp:
                self.guard_metadata[fp] = {
                    "nickname": guard.get("nickname", "unknown"),
                    "fingerprint": fp,
                    "country": guard.get("country"),
                    "as": guard.get("as"),
                    "bandwidth": guard.get("advertised_bandwidth"),
                    "flags": guard.get("flags", []),
                }
    
    def add_exit_observation(
        self,
        exit_fingerprint: str,
        exit_nickname: str = "unknown",
        evidence_score: float = 0.5,
        session_id: Optional[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, float]:
        """
        Add a new exit observation and update hypotheses.
        
        Args:
            exit_fingerprint: Fingerprint of observed exit node
            exit_nickname: Nickname of exit node
            evidence_score: Quality of observation (0-1)
            session_id: Optional session identifier
            metadata: Additional metadata
        
        Returns:
            Dict mapping guard fingerprints to updated posteriors
        """
        observation = ExitObservation(
            observation_id=str(uuid.uuid4()),
            exit_fingerprint=exit_fingerprint,
            exit_nickname=exit_nickname,
            timestamp=datetime.utcnow(),
            session_metadata=metadata or {},
            evidence_score=evidence_score,
        )
        
        # Create hypotheses for all known guards if needed
        candidate_guards = list(self.guard_metadata.values())
        
        posteriors = self.engine.update_with_observation(
            observation,
            candidate_guards=candidate_guards
        )
        
        # Track session
        if session_id:
            self.session_observations[session_id].append(observation.observation_id)
        
        return posteriors
    
    def add_path_observation(
        self,
        exit_relay: Dict[str, Any],
        evidence_metrics: Dict[str, float] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Add observation with optional evidence metrics.
        
        Args:
            exit_relay: Exit relay information
            evidence_metrics: Optional dict with timing_score, traffic_score, etc.
            session_id: Optional session identifier
        
        Returns:
            Updated posteriors
        """
        # Compute evidence score from metrics if provided
        evidence_score = 0.5
        if evidence_metrics:
            scores = [
                evidence_metrics.get("timing_score", 0.5),
                evidence_metrics.get("traffic_score", 0.5),
                evidence_metrics.get("stability_score", 0.5),
            ]
            evidence_score = sum(scores) / len(scores)
        
        return self.add_exit_observation(
            exit_fingerprint=exit_relay.get("fingerprint", "unknown"),
            exit_nickname=exit_relay.get("nickname", "unknown"),
            evidence_score=evidence_score,
            session_id=session_id,
            metadata=evidence_metrics
        )
    
    def get_ranked_hypotheses(
        self,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get ranked hypotheses as serializable dictionaries.
        """
        ranked = self.engine.get_ranked_hypotheses(top_k, include_explanations=True)
        
        results = []
        for rh in ranked:
            result = rh.to_dict()
            
            # Enrich with guard metadata
            fp = rh.hypothesis.guard_fingerprint
            if fp in self.guard_metadata:
                result["guard_metadata"] = self.guard_metadata[fp]
            
            results.append(result)
        
        return results
    
    def get_inference_result(self, top_k: int = 10) -> Dict[str, Any]:
        """
        Get complete inference result for API response.
        """
        ranked = self.get_ranked_hypotheses(top_k)
        state_summary = self.engine.get_state_summary()
        
        return {
            "hypotheses": ranked,
            "summary": state_summary,
            "entropy": state_summary["entropy"],
            "uncertainty_level": state_summary["uncertainty_level"],
            "total_observations": state_summary["total_observations"],
            "inference_timestamp": datetime.utcnow().isoformat(),
            "_disclaimer": (
                "These hypotheses represent probabilistic correlations based on "
                "observable network metadata. They are NOT identifications and require "
                "independent verification. Multiple competing hypotheses are maintained."
            ),
            "_methodology": {
                "approach": "Bayesian hypothesis updating",
                "guard_persistence_modeling": True,
                "evidence_decay": True,
                "uncertainty_tracking": "Shannon entropy",
            }
        }
    
    def export_state(self) -> Dict[str, Any]:
        """Export complete state for persistence."""
        return {
            "engine_state": self.engine.export_state(),
            "guard_metadata": self.guard_metadata,
            "config": {
                "guard_persistence_days": self.config.GUARD_PERSISTENCE_DAYS,
                "evidence_half_life_hours": self.config.EVIDENCE_HALF_LIFE_HOURS,
                "max_active_hypotheses": self.config.MAX_ACTIVE_HYPOTHESES,
            }
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """Import state from persistence."""
        if not state:
            return
        
        self.guard_metadata = state.get("guard_metadata", {})
        self.engine.import_state(state.get("engine_state", {}))


# =============================================================================
# RESULT STRUCTURES FOR API
# =============================================================================

@dataclass
class ProbabilisticPathResult:
    """
    Complete response structure for probabilistic path inference API.
    """
    hypotheses: List[Dict[str, Any]]
    summary: Dict[str, Any]
    entropy: float
    uncertainty_level: str
    total_observations: int
    inference_timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "hypotheses": self.hypotheses,
            "summary": self.summary,
            "entropy": round(self.entropy, 4),
            "uncertainty_level": self.uncertainty_level,
            "total_observations": self.total_observations,
            "inference_timestamp": self.inference_timestamp,
            "_disclaimer": (
                "This system performs probabilistic forensic correlation using metadata "
                "and lawful network evidence. It does not de-anonymize TOR users. "
                "Multiple competing hypotheses are always maintained to reflect uncertainty."
            ),
            "_analysis_notice": {
                "type": "bayesian_hypothesis_inference",
                "interpretation": "Results are ranked hypotheses, not definitive identifications",
                "verification": "Independent verification required before any investigative action",
                "key_features": [
                    "Guard persistence modeling based on TOR specification",
                    "Evidence decay over time",
                    "Entropy-based uncertainty tracking",
                    "Multiple competing hypotheses maintained",
                ],
                "limitations": [
                    "Probability scores indicate relative likelihood only",
                    "False positives and negatives are possible",
                    "No content inspection or user identification performed",
                    "Guard rotation may invalidate older hypotheses",
                ],
            },
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_inference_engine(
    guards: List[Dict[str, Any]] = None,
    config: HypothesisConfig = None
) -> ProbabilisticPathInference:
    """
    Create and initialize a probabilistic path inference engine.
    
    Args:
        guards: Optional list of guard relays
        config: Optional configuration
    
    Returns:
        Initialized ProbabilisticPathInference instance
    """
    engine = ProbabilisticPathInference(config)
    
    if guards:
        engine.initialize_guards(guards)
    
    return engine


def compute_entropy(probabilities: List[float]) -> float:
    """
    Compute Shannon entropy for a probability distribution.
    
    Args:
        probabilities: List of probabilities (should sum to 1.0)
    
    Returns:
        Entropy in bits
    """
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def normalize_probabilities(values: List[float]) -> List[float]:
    """
    Normalize values to form a valid probability distribution.
    """
    total = sum(values)
    if total <= 0:
        # Return uniform distribution
        n = len(values)
        return [1.0 / n] * n if n > 0 else []
    
    return [v / total for v in values]


# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================

def generate_probabilistic_paths(
    guards: List[Dict[str, Any]],
    middles: List[Dict[str, Any]] = None,
    exits: List[Dict[str, Any]] = None,
    top_k: int = 50
) -> Dict[str, Any]:
    """
    Legacy function for backward compatibility.
    
    DEPRECATED: Use ProbabilisticPathInference class directly.
    """
    engine = create_inference_engine(guards)
    
    # Add exit observations if provided
    if exits:
        for exit_relay in exits[:10]:  # Limit for legacy compat
            engine.add_path_observation(exit_relay)
    
    return engine.get_inference_result(top_k)


# =============================================================================
# MODULE EXPORTS
# =============================================================================

__all__ = [
    # Configuration
    "HypothesisConfig",
    "EvidenceStrength",
    
    # Data structures
    "ExitObservation",
    "GuardHypothesis",
    "HypothesisExplanation",
    "RankedHypothesis",
    "ProbabilisticPathResult",
    
    # Engines
    "BayesianHypothesisEngine",
    "ProbabilisticPathInference",
    
    # Convenience functions
    "create_inference_engine",
    "compute_entropy",
    "normalize_probabilities",
    
    # Legacy
    "generate_probabilistic_paths",
]
