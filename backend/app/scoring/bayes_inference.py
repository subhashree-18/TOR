"""
Bayesian Inference Module for TOR Entry Node Analysis

This module implements Bayesian inference to compute posterior probabilities
of TOR entry (guard) nodes using relay consensus weights as priors and
combining evidence likelihoods from multiple evidence metrics.

Key Components:
1. Prior: Relay consensus weight (probability of being used)
2. Likelihoods: Evidence metrics (time_overlap, traffic_similarity, stability)
3. Posterior: P(entry | evidence) = P(evidence | entry) * P(entry) / P(evidence)

The module supports dynamic updates as new exit nodes are observed and
provides interpretable probability estimates for investigative analysis.

Usage:
    from backend.app.scoring.bayes_inference import BayesianEntryInference
    
    inference = BayesianEntryInference()
    inference.update_evidence(entry_relay, evidence_dict)
    posterior = inference.posterior_probability(entry_relay_id)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging
import math
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class RelayInfo:
    """Information about a relay used in Bayesian inference"""
    fingerprint: str
    consensus_weight: float  # Prior probability
    uptime_days: int
    flags: List[str] = field(default_factory=list)
    
    @property
    def is_guard(self) -> bool:
        """Check if relay has Guard flag"""
        return "Guard" in self.flags


@dataclass
class EvidenceObservation:
    """A single observation of evidence for an entry relay"""
    timestamp: datetime
    time_overlap_likelihood: float  # 0.0-1.0
    traffic_similarity_likelihood: float  # 0.0-1.0
    stability_likelihood: float  # 0.0-1.0
    exit_node_observed: str  # Fingerprint of exit node observed with this entry


class BayesianEntryInference:
    """
    Bayesian inference engine for computing posterior probabilities
    of TOR entry nodes given observed evidence.
    
    The inference engine maintains:
    1. Prior probabilities from relay consensus weights
    2. Likelihood distributions from evidence metrics
    3. Posterior estimates updated as new evidence arrives
    4. Observation history for each entry relay
    """
    
    def __init__(
        self,
        likelihood_weight_time: float = 0.35,
        likelihood_weight_traffic: float = 0.40,
        likelihood_weight_stability: float = 0.25,
        smoothing_factor: float = 0.01,
    ):
        """
        Initialize Bayesian inference engine.
        
        Args:
            likelihood_weight_time: Weight for time overlap evidence (0.0-1.0)
            likelihood_weight_traffic: Weight for traffic similarity evidence (0.0-1.0)
            likelihood_weight_stability: Weight for stability evidence (0.0-1.0)
            smoothing_factor: Laplace smoothing to prevent zero probabilities (default 0.01)
        
        Note: Weights should sum to approximately 1.0 for normalized interpretation
        """
        # Validate weights
        total_weight = likelihood_weight_time + likelihood_weight_traffic + likelihood_weight_stability
        if not (0.95 <= total_weight <= 1.05):
            logger.warning(
                f"Likelihood weights sum to {total_weight}, not 1.0. "
                "Consider normalizing for interpretability."
            )
        
        self.likelihood_weight_time = likelihood_weight_time
        self.likelihood_weight_traffic = likelihood_weight_traffic
        self.likelihood_weight_stability = likelihood_weight_stability
        self.smoothing_factor = smoothing_factor
        
        # Prior probabilities (keyed by fingerprint)
        self.priors: Dict[str, float] = {}
        
        # Observations for each entry relay
        self.observations: Dict[str, List[EvidenceObservation]] = defaultdict(list)
        
        # Cached posteriors (fingerprint -> posterior probability)
        self._posterior_cache: Dict[str, float] = {}
        
        # Cache validity tracking
        self._cache_valid = False
        
        # Observation statistics for diagnostics
        self.stats: Dict[str, Dict] = defaultdict(lambda: {
            "observation_count": 0,
            "avg_time_likelihood": 0.0,
            "avg_traffic_likelihood": 0.0,
            "avg_stability_likelihood": 0.0,
            "exit_nodes_observed_with": set(),
        })
    
    def set_priors(self, relay_list: List[RelayInfo]) -> None:
        """
        Set prior probabilities from relay consensus weights.
        
        The prior for each relay is its normalized consensus weight,
        representing the probability of it being used in TOR circuits
        based on network consensus.
        
        Args:
            relay_list: List of RelayInfo objects with consensus weights
        
        Raises:
            ValueError: If relay list is empty or all weights are zero
        """
        if not relay_list:
            raise ValueError("relay_list cannot be empty")
        
        # Sum consensus weights
        total_weight = sum(relay.consensus_weight for relay in relay_list)
        
        if total_weight <= 0:
            raise ValueError("Total consensus weight must be positive")
        
        # Normalize to probability distribution
        self.priors = {}
        for relay in relay_list:
            # Add smoothing factor to prevent absolute zeros
            normalized_weight = relay.consensus_weight / total_weight
            self.priors[relay.fingerprint] = normalized_weight + self.smoothing_factor
        
        # Re-normalize after smoothing
        total_with_smoothing = sum(self.priors.values())
        self.priors = {fp: p / total_with_smoothing for fp, p in self.priors.items()}
        
        logger.info(f"Set priors for {len(relay_list)} relays. Total weight: {total_weight}")
        
        # Invalidate posterior cache
        self._cache_valid = False
    
    def update_evidence(
        self,
        entry_relay: RelayInfo,
        time_overlap: float,
        traffic_similarity: float,
        stability: float,
        exit_node_observed: str,
    ) -> None:
        """
        Update beliefs about an entry relay with new evidence observation.
        
        This method adds a new observation to the inference engine and
        invalidates cached posteriors to ensure next computation is current.
        
        Args:
            entry_relay: RelayInfo object for the entry relay
            time_overlap: Likelihood value for time overlap (0.0-1.0)
            traffic_similarity: Likelihood value for traffic similarity (0.0-1.0)
            stability: Likelihood value for relay stability (0.0-1.0)
            exit_node_observed: Fingerprint of exit node in this observation
        
        Raises:
            ValueError: If any likelihood value is outside [0.0, 1.0]
            ValueError: If entry_relay has no prior probability set
        """
        # Validate inputs
        for likelihood, name in [
            (time_overlap, "time_overlap"),
            (traffic_similarity, "traffic_similarity"),
            (stability, "stability"),
        ]:
            if not (0.0 <= likelihood <= 1.0):
                raise ValueError(f"{name} must be in [0.0, 1.0], got {likelihood}")
        
        fingerprint = entry_relay.fingerprint
        
        if fingerprint not in self.priors:
            raise ValueError(
                f"Entry relay {fingerprint} has no prior. "
                "Call set_priors() first."
            )
        
        # Create observation
        observation = EvidenceObservation(
            timestamp=datetime.utcnow(),
            time_overlap_likelihood=time_overlap,
            traffic_similarity_likelihood=traffic_similarity,
            stability_likelihood=stability,
            exit_node_observed=exit_node_observed,
        )
        
        # Add to observations
        self.observations[fingerprint].append(observation)
        
        # Update statistics
        self.stats[fingerprint]["observation_count"] += 1
        self.stats[fingerprint]["exit_nodes_observed_with"].add(exit_node_observed)
        
        # Update running averages
        n = self.stats[fingerprint]["observation_count"]
        old_avg_time = self.stats[fingerprint]["avg_time_likelihood"]
        old_avg_traffic = self.stats[fingerprint]["avg_traffic_likelihood"]
        old_avg_stability = self.stats[fingerprint]["avg_stability_likelihood"]
        
        self.stats[fingerprint]["avg_time_likelihood"] = (
            (old_avg_time * (n - 1) + time_overlap) / n
        )
        self.stats[fingerprint]["avg_traffic_likelihood"] = (
            (old_avg_traffic * (n - 1) + traffic_similarity) / n
        )
        self.stats[fingerprint]["avg_stability_likelihood"] = (
            (old_avg_stability * (n - 1) + stability) / n
        )
        
        # Invalidate cache
        self._cache_valid = False
        
        logger.debug(
            f"Updated evidence for entry {fingerprint}: "
            f"time={time_overlap:.3f}, traffic={traffic_similarity:.3f}, "
            f"stability={stability:.3f}, exit={exit_node_observed}"
        )
    
    def _compute_likelihood(self, fingerprint: str) -> float:
        """
        Compute average likelihood for an entry relay given observations.
        
        Combines time overlap, traffic similarity, and stability evidence
        using weighted averaging. Uses running averages from statistics
        to avoid recomputation.
        
        Args:
            fingerprint: Relay fingerprint
        
        Returns:
            Combined likelihood (0.0-1.0)
        """
        if fingerprint not in self.stats or self.stats[fingerprint]["observation_count"] == 0:
            # No observations: uniform likelihood (0.5)
            return 0.5
        
        stats = self.stats[fingerprint]
        
        combined_likelihood = (
            self.likelihood_weight_time * stats["avg_time_likelihood"] +
            self.likelihood_weight_traffic * stats["avg_traffic_likelihood"] +
            self.likelihood_weight_stability * stats["avg_stability_likelihood"]
        )
        
        return min(1.0, max(0.0, combined_likelihood))
    
    def posterior_probability(self, fingerprint: str) -> float:
        """
        Compute posterior probability P(entry | evidence) for a relay.
        
        Uses Bayes' theorem: P(E|D) = P(D|E) * P(E) / P(D)
        where:
        - E: entry relay hypothesis
        - D: observed evidence
        - P(E): prior from consensus weight
        - P(D|E): likelihood from combined evidence
        - P(D): evidence probability (normalizing constant)
        
        Args:
            fingerprint: Relay fingerprint
        
        Returns:
            Posterior probability (0.0-1.0)
        
        Raises:
            ValueError: If fingerprint not in priors
        """
        if fingerprint not in self.priors:
            raise ValueError(f"Relay {fingerprint} has no prior probability")
        
        # Return cached if valid
        if self._cache_valid and fingerprint in self._posterior_cache:
            return self._posterior_cache[fingerprint]
        
        # Recompute all posteriors if cache invalid
        if not self._cache_valid:
            self._recompute_posteriors()
        
        return self._posterior_cache.get(fingerprint, self.priors[fingerprint])
    
    def _recompute_posteriors(self) -> None:
        """
        Recompute all posterior probabilities from priors and evidence.
        
        This method implements Bayes' theorem:
        P(entry_i | evidence) = P(evidence | entry_i) * P(entry_i) / P(evidence)
        
        The denominator P(evidence) is the sum of numerators for normalization.
        """
        posteriors = {}
        
        # Compute numerator for each relay: P(D|E) * P(E)
        for fingerprint in self.priors:
            likelihood = self._compute_likelihood(fingerprint)
            prior = self.priors[fingerprint]
            
            # Numerator of Bayes' theorem
            numerator = likelihood * prior
            posteriors[fingerprint] = numerator
        
        # Normalize: divide by evidence probability (sum of numerators)
        total = sum(posteriors.values())
        
        if total > 0:
            self._posterior_cache = {fp: p / total for fp, p in posteriors.items()}
        else:
            # If all numerators are 0, use priors
            self._posterior_cache = self.priors.copy()
        
        self._cache_valid = True
        
        logger.debug(
            f"Recomputed posteriors for {len(self._posterior_cache)} relays"
        )
    
    def posterior_probabilities(self) -> Dict[str, float]:
        """
        Get posterior probabilities for all relays.
        
        Returns:
            Dictionary mapping fingerprint -> posterior probability
        """
        if not self._cache_valid:
            self._recompute_posteriors()
        
        return self._posterior_cache.copy()
    
    def ranked_entries(self, top_k: Optional[int] = None) -> List[Tuple[str, float]]:
        """
        Get entry relays ranked by posterior probability (highest first).
        
        Args:
            top_k: If provided, return only top k entries
        
        Returns:
            List of (fingerprint, posterior_probability) tuples sorted descending
        """
        posteriors = self.posterior_probabilities()
        
        # Sort by probability descending
        ranked = sorted(posteriors.items(), key=lambda x: x[1], reverse=True)
        
        if top_k is not None:
            ranked = ranked[:top_k]
        
        return ranked
    
    def entry_summary(self, fingerprint: str) -> Dict:
        """
        Get detailed summary for an entry relay including posterior,
        supporting evidence, and diagnostic information.
        
        Args:
            fingerprint: Relay fingerprint
        
        Returns:
            Dictionary with posterior, evidence stats, and diagnostics
        
        Raises:
            ValueError: If fingerprint not in priors
        """
        if fingerprint not in self.priors:
            raise ValueError(f"Relay {fingerprint} has no prior probability")
        
        posterior = self.posterior_probability(fingerprint)
        prior = self.priors[fingerprint]
        stats = self.stats[fingerprint]
        
        # Compute likelihood ratio (posterior / prior)
        likelihood_ratio = posterior / prior if prior > 0 else 1.0
        
        return {
            "fingerprint": fingerprint,
            "prior_probability": round(prior, 6),
            "posterior_probability": round(posterior, 6),
            "likelihood_ratio": round(likelihood_ratio, 4),
            "observation_count": stats["observation_count"],
            "average_evidence": {
                "time_overlap": round(stats["avg_time_likelihood"], 4),
                "traffic_similarity": round(stats["avg_traffic_likelihood"], 4),
                "stability": round(stats["avg_stability_likelihood"], 4),
            },
            "unique_exit_nodes_observed": len(stats["exit_nodes_observed_with"]),
            "confidence_level": self._assess_confidence(
                stats["observation_count"],
                posterior,
                prior,
            ),
        }
    
    def _assess_confidence(
        self,
        observation_count: int,
        posterior: float,
        prior: float,
    ) -> str:
        """
        Assess confidence in posterior probability estimate.
        
        Confidence depends on:
        1. Number of observations (more = higher confidence)
        2. Posterior certainty (0.5 = low, 0.0/1.0 = high)
        3. Deviation from prior (large change = lower confidence)
        
        Returns:
            "very_high", "high", "medium", "low", or "very_low"
        """
        if observation_count == 0:
            return "very_low"
        
        # Certainty: how far from 0.5 (neutral)?
        certainty = abs(posterior - 0.5) * 2  # 0.0 (uncertain) to 1.0 (certain)
        
        # Stability: how much did we change from prior?
        if prior > 0:
            bayesian_factor = posterior / prior
            # Log Bayes factor: how much evidence updated us
            log_bf = math.log(max(bayesian_factor, 0.001))  # Avoid log(0)
            stability = min(1.0, abs(log_bf) / 5.0)  # Normalize: 5 = threshold
        else:
            stability = 0.0
        
        # Combine: observations + certainty + stability
        combined_score = (
            min(observation_count / 10, 1.0) * 0.4 +  # More observations better
            certainty * 0.4 +  # Certainty matters
            stability * 0.2  # But don't over-emphasize stability
        )
        
        if combined_score >= 0.85:
            return "very_high"
        elif combined_score >= 0.70:
            return "high"
        elif combined_score >= 0.50:
            return "medium"
        elif combined_score >= 0.30:
            return "low"
        else:
            return "very_low"
    
    def dynamic_update_on_exit(
        self,
        exit_fingerprint: str,
        entry_candidates: List[Tuple[RelayInfo, float, float, float]],
    ) -> Dict[str, float]:
        """
        Dynamically update entry node probabilities when a new exit node is observed.
        
        This is the main user-facing API for updating beliefs as exit nodes
        are discovered during path analysis.
        
        Args:
            exit_fingerprint: Fingerprint of observed exit node
            entry_candidates: List of (entry_relay, time_overlap, traffic_similarity, stability)
                            tuples from path analysis
        
        Returns:
            Dictionary mapping entry fingerprint -> posterior probability
        
        Example:
            >>> entry_list = [relay_a, relay_b, relay_c]
            >>> candidates = [
            ...     (relay_a, 0.8, 0.7, 0.9),  # time, traffic, stability scores
            ...     (relay_b, 0.6, 0.4, 0.7),
            ...     (relay_c, 0.5, 0.6, 0.5),
            ... ]
            >>> posteriors = bayes.dynamic_update_on_exit(exit_fp, candidates)
        """
        if not entry_candidates:
            logger.warning("No entry candidates provided for update")
            return {}
        
        # Update evidence for each candidate
        updated_count = 0
        for entry_relay, time_overlap, traffic_similarity, stability in entry_candidates:
            try:
                self.update_evidence(
                    entry_relay=entry_relay,
                    time_overlap=time_overlap,
                    traffic_similarity=traffic_similarity,
                    stability=stability,
                    exit_node_observed=exit_fingerprint,
                )
                updated_count += 1
            except ValueError as e:
                logger.warning(f"Failed to update evidence for {entry_relay.fingerprint}: {e}")
        
        logger.info(
            f"Updated {updated_count} entry candidates for exit node {exit_fingerprint}"
        )
        
        # Return updated posteriors
        return self.posterior_probabilities()
    
    def get_highest_probability_entry(self) -> Optional[Tuple[str, float]]:
        """
        Get entry relay with highest posterior probability.
        
        Returns:
            (fingerprint, probability) tuple or None if no entries
        """
        ranked = self.ranked_entries(top_k=1)
        return ranked[0] if ranked else None
    
    def entropy(self) -> float:
        """
        Compute Shannon entropy of posterior distribution.
        
        Lower entropy = more certainty (peaked distribution)
        Higher entropy = more uncertainty (uniform-like distribution)
        
        Returns:
            Entropy in nats (0.0 to ln(n) where n=number of relays)
        """
        posteriors = self.posterior_probabilities()
        
        if not posteriors:
            return 0.0
        
        entropy_value = 0.0
        for p in posteriors.values():
            if p > 0:
                entropy_value -= p * math.log(p)
        
        return entropy_value
    
    def diagnostic_report(self) -> Dict:
        """
        Generate comprehensive diagnostic report for inference engine state.
        
        Returns:
            Dictionary with engine state, statistics, and diagnostics
        """
        posteriors = self.posterior_probabilities()
        ranked = self.ranked_entries(top_k=5)
        
        return {
            "engine_state": {
                "total_relays": len(self.priors),
                "relays_with_observations": len(self.stats),
                "total_observations": sum(s["observation_count"] for s in self.stats.values()),
                "cache_valid": self._cache_valid,
            },
            "likelihood_weights": {
                "time_overlap": self.likelihood_weight_time,
                "traffic_similarity": self.likelihood_weight_traffic,
                "stability": self.likelihood_weight_stability,
            },
            "posterior_distribution": {
                "mean": sum(posteriors.values()) / len(posteriors) if posteriors else 0.0,
                "min": min(posteriors.values()) if posteriors else 0.0,
                "max": max(posteriors.values()) if posteriors else 0.0,
                "entropy": self.entropy(),
            },
            "top_5_entries": [
                {
                    "fingerprint": fp,
                    "posterior": round(prob, 6),
                    "observations": self.stats[fp]["observation_count"],
                }
                for fp, prob in ranked
            ],
            "prior_posterior_correlation": self._compute_correlation(),
        }
    
    def _compute_correlation(self) -> float:
        """
        Compute correlation between prior and posterior distributions.
        
        Returns:
            Pearson correlation coefficient (-1.0 to 1.0)
        """
        if not self.priors:
            return 0.0
        
        priors = [self.priors.get(fp, 0.0) for fp in self.priors]
        posteriors = [self.posterior_probability(fp) for fp in self.priors]
        
        # Compute mean
        mean_prior = sum(priors) / len(priors)
        mean_posterior = sum(posteriors) / len(posteriors)
        
        # Compute covariance
        cov = sum(
            (p - mean_prior) * (q - mean_posterior)
            for p, q in zip(priors, posteriors)
        ) / len(priors)
        
        # Compute standard deviations
        std_prior = math.sqrt(
            sum((p - mean_prior) ** 2 for p in priors) / len(priors)
        )
        std_posterior = math.sqrt(
            sum((q - mean_posterior) ** 2 for q in posteriors) / len(posteriors)
        )
        
        # Avoid division by zero
        if std_prior == 0 or std_posterior == 0:
            return 0.0
        
        return cov / (std_prior * std_posterior)

    # ========================================================================
    # PERSISTENCE METHODS - Integration with Investigation Model
    # ========================================================================
    
    def export_state(self) -> Dict:
        """
        Export the current inference state for persistence.
        
        This method serializes the entire inference engine state to a dictionary
        that can be stored in MongoDB and later restored via `import_state()`.
        
        Returns:
            Dictionary containing:
            - priors: Prior probability distribution
            - observations: Full observation history (serialized)
            - stats: Aggregated statistics
            - config: Engine configuration parameters
        """
        # Serialize observations
        serialized_observations = {}
        for fp, obs_list in self.observations.items():
            serialized_observations[fp] = [
                {
                    "timestamp": obs.timestamp.isoformat(),
                    "time_overlap_likelihood": obs.time_overlap_likelihood,
                    "traffic_similarity_likelihood": obs.traffic_similarity_likelihood,
                    "stability_likelihood": obs.stability_likelihood,
                    "exit_node_observed": obs.exit_node_observed,
                }
                for obs in obs_list
            ]
        
        # Serialize stats (convert sets to lists for JSON)
        serialized_stats = {}
        for fp, stat in self.stats.items():
            serialized_stats[fp] = {
                "observation_count": stat["observation_count"],
                "avg_time_likelihood": stat["avg_time_likelihood"],
                "avg_traffic_likelihood": stat["avg_traffic_likelihood"],
                "avg_stability_likelihood": stat["avg_stability_likelihood"],
                "exit_nodes_observed_with": list(stat["exit_nodes_observed_with"]),
            }
        
        return {
            "priors": self.priors.copy(),
            "observations": serialized_observations,
            "stats": serialized_stats,
            "config": {
                "likelihood_weight_time": self.likelihood_weight_time,
                "likelihood_weight_traffic": self.likelihood_weight_traffic,
                "likelihood_weight_stability": self.likelihood_weight_stability,
                "smoothing_factor": self.smoothing_factor,
            },
        }
    
    def import_state(self, state: Dict) -> None:
        """
        Restore inference engine state from a persisted dictionary.
        
        This method allows resuming an investigation from saved state,
        enabling incremental updates across sessions.
        
        Args:
            state: Dictionary from export_state() or Investigation.bayesian_state
        
        Raises:
            ValueError: If state format is invalid
        """
        if not state:
            raise ValueError("Cannot import empty state")
        
        # Restore priors
        if "priors" in state:
            self.priors = state["priors"].copy()
        
        # Restore configuration if present
        if "config" in state:
            config = state["config"]
            self.likelihood_weight_time = config.get(
                "likelihood_weight_time", self.likelihood_weight_time
            )
            self.likelihood_weight_traffic = config.get(
                "likelihood_weight_traffic", self.likelihood_weight_traffic
            )
            self.likelihood_weight_stability = config.get(
                "likelihood_weight_stability", self.likelihood_weight_stability
            )
            self.smoothing_factor = config.get(
                "smoothing_factor", self.smoothing_factor
            )
        
        # Restore observations
        if "observations" in state:
            self.observations.clear()
            for fp, obs_list in state["observations"].items():
                for obs_data in obs_list:
                    # Parse timestamp
                    timestamp = datetime.fromisoformat(obs_data["timestamp"])
                    
                    observation = EvidenceObservation(
                        timestamp=timestamp,
                        time_overlap_likelihood=obs_data["time_overlap_likelihood"],
                        traffic_similarity_likelihood=obs_data["traffic_similarity_likelihood"],
                        stability_likelihood=obs_data["stability_likelihood"],
                        exit_node_observed=obs_data["exit_node_observed"],
                    )
                    self.observations[fp].append(observation)
        
        # Restore stats
        if "stats" in state:
            self.stats.clear()
            for fp, stat in state["stats"].items():
                self.stats[fp] = {
                    "observation_count": stat["observation_count"],
                    "avg_time_likelihood": stat["avg_time_likelihood"],
                    "avg_traffic_likelihood": stat["avg_traffic_likelihood"],
                    "avg_stability_likelihood": stat["avg_stability_likelihood"],
                    "exit_nodes_observed_with": set(stat["exit_nodes_observed_with"]),
                }
        
        # Invalidate cache to recompute posteriors
        self._cache_valid = False
        
        logger.info(
            f"Imported state: {len(self.priors)} priors, "
            f"{sum(len(v) for v in self.observations.values())} observations"
        )
    
    def merge_with_investigation(
        self,
        investigation_entry_probs: Dict[str, Dict],
    ) -> None:
        """
        Merge investigation entry node probabilities into inference engine.
        
        This method allows combining historical probability data from an
        Investigation model with the current inference engine state.
        
        Args:
            investigation_entry_probs: Dict from Investigation.entry_node_probabilities
                Each value should have: current_prior, avg_time_overlap, etc.
        """
        for fp, entry_data in investigation_entry_probs.items():
            # Set prior if not already set
            if fp not in self.priors:
                self.priors[fp] = entry_data.get("current_prior", 0.001)
            
            # Merge statistics
            if fp not in self.stats or self.stats[fp]["observation_count"] == 0:
                self.stats[fp] = {
                    "observation_count": entry_data.get("update_count", 0),
                    "avg_time_likelihood": entry_data.get("avg_time_overlap", 0.5),
                    "avg_traffic_likelihood": entry_data.get("avg_traffic_similarity", 0.5),
                    "avg_stability_likelihood": entry_data.get("avg_stability", 0.5),
                    "exit_nodes_observed_with": set(
                        entry_data.get("associated_exit_nodes", [])
                    ),
                }
        
        # Invalidate cache
        self._cache_valid = False
        
        logger.info(f"Merged {len(investigation_entry_probs)} entries from investigation")
    
    def get_observation_count(self, fingerprint: Optional[str] = None) -> int:
        """
        Get count of observations.
        
        Args:
            fingerprint: If provided, return count for specific relay.
                        Otherwise, return total across all relays.
        
        Returns:
            Number of observations
        """
        if fingerprint:
            return self.stats.get(fingerprint, {}).get("observation_count", 0)
        return sum(len(obs) for obs in self.observations.values())


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_relay_info(
    fingerprint: str,
    consensus_weight: float,
    uptime_days: int,
    flags: Optional[List[str]] = None,
) -> RelayInfo:
    """
    Create a RelayInfo object from relay data.
    
    Convenience function for creating relay objects for Bayesian inference.
    """
    return RelayInfo(
        fingerprint=fingerprint,
        consensus_weight=consensus_weight,
        uptime_days=uptime_days,
        flags=flags or [],
    )


def posterior_probability_given_evidence(
    entry_relay: RelayInfo,
    all_relays: List[RelayInfo],
    time_overlap: float,
    traffic_similarity: float,
    stability: float,
    exit_observed: str,
) -> float:
    """
    Compute posterior probability for a single entry relay given evidence.
    
    This is a convenience function that creates a temporary inference engine,
    sets up priors, adds evidence, and returns the posterior.
    
    Args:
        entry_relay: The entry relay of interest
        all_relays: All candidate entry relays (for setting priors)
        time_overlap: Time overlap evidence (0.0-1.0)
        traffic_similarity: Traffic similarity evidence (0.0-1.0)
        stability: Stability evidence (0.0-1.0)
        exit_observed: Exit node fingerprint
    
    Returns:
        Posterior probability (0.0-1.0)
    """
    inference = BayesianEntryInference()
    inference.set_priors(all_relays)
    inference.update_evidence(
        entry_relay=entry_relay,
        time_overlap=time_overlap,
        traffic_similarity=traffic_similarity,
        stability=stability,
        exit_node_observed=exit_observed,
    )
    return inference.posterior_probability(entry_relay.fingerprint)


def create_inference_from_investigation(
    investigation_state: Dict,
) -> BayesianEntryInference:
    """
    Create a BayesianEntryInference engine from saved investigation state.
    
    This is a convenience function for resuming investigations.
    
    Args:
        investigation_state: Bayesian state from Investigation.bayesian_state
    
    Returns:
        Initialized BayesianEntryInference engine
    """
    inference = BayesianEntryInference()
    
    if investigation_state:
        inference.import_state(investigation_state)
    
    return inference
