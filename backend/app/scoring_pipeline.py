"""
Unified Scoring Pipeline for TOR Unveil
Provides single source of truth for all scoring and confidence calculations
"""

import logging
import statistics
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScoringFactors:
    """Factors used in scoring calculation"""
    evidence_count: int
    timing_similarity: float  # 0.0-1.0
    session_overlap: float    # 0.0-1.0
    additional_evidence_count: int = 0
    prior_uploads: int = 0


class UnifiedScoringEngine:
    """
    Single source of truth for all scoring operations
    Combines evidence volume, timing, overlap, and Bayesian priors
    """
    
    # Confidence level thresholds
    HIGH_CONFIDENCE_THRESHOLD = 0.75
    MEDIUM_CONFIDENCE_THRESHOLD = 0.50
    LOW_CONFIDENCE_THRESHOLD = 0.0
    
    # Evidence volume weights (in basis points)
    VERY_STRONG_EVIDENCE = 50000      # > 50k evidence
    STRONG_EVIDENCE = 20000           # > 20k evidence
    MODERATE_EVIDENCE = 5000          # > 5k evidence
    WEAK_EVIDENCE = 1000              # > 1k evidence
    MINIMAL_EVIDENCE = 0              # < 1k evidence
    
    @staticmethod
    def compute_confidence_level(
        factors: ScoringFactors,
        debug: bool = False
    ) -> str:
        """
        Compute confidence level from multiple evidence sources.
        
        Combines:
        - Evidence volume (evidence_count)
        - Timing correlation (timing_similarity, 0-1)
        - Session overlap (session_overlap, 0-1)
        - Bayesian prior (from additional uploads)
        
        Args:
            factors: ScoringFactors with all evidence sources
            debug: If True, log scoring breakdown
            
        Returns:
            "High", "Medium", or "Low" confidence level
        """
        scores = []
        weights = []
        
        # 1. Evidence volume factor (40% weight)
        evidence_score = UnifiedScoringEngine._score_evidence_volume(
            factors.evidence_count
        )
        scores.append(evidence_score)
        weights.append(0.40)
        
        if debug:
            logger.info(f"Evidence volume score: {evidence_score:.2f} "
                       f"({factors.evidence_count} evidence points)")
        
        # 2. Timing similarity factor (35% weight)
        timing_score = max(0.0, min(1.0, factors.timing_similarity))
        scores.append(timing_score)
        weights.append(0.35)
        
        if debug:
            logger.info(f"Timing similarity score: {timing_score:.2f}")
        
        # 3. Session overlap factor (15% weight)
        overlap_score = max(0.0, min(1.0, factors.session_overlap))
        scores.append(overlap_score)
        weights.append(0.15)
        
        if debug:
            logger.info(f"Session overlap score: {overlap_score:.2f}")
        
        # 4. Bayesian prior (10% weight) - improves with additional evidence
        if factors.additional_evidence_count > 0:
            prior_score = UnifiedScoringEngine._compute_bayesian_prior(
                factors.additional_evidence_count,
                factors.prior_uploads
            )
            scores.append(prior_score)
            weights.append(0.10)
            
            if debug:
                logger.info(f"Bayesian prior score: {prior_score:.2f} "
                           f"({factors.additional_evidence_count} additional evidence)")
        
        # Weighted average
        if len(scores) == 0:
            combined_score = 0.0
        else:
            total_weight = sum(weights)
            combined_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        
        if debug:
            logger.info(f"Combined confidence score: {combined_score:.2f}")
        
        # Map to confidence level
        if combined_score >= UnifiedScoringEngine.HIGH_CONFIDENCE_THRESHOLD:
            confidence = "High"
        elif combined_score >= UnifiedScoringEngine.MEDIUM_CONFIDENCE_THRESHOLD:
            confidence = "Medium"
        else:
            confidence = "Low"
        
        if debug:
            logger.info(f"Final confidence level: {confidence}")
        
        return confidence
    
    @staticmethod
    def _score_evidence_volume(evidence_count: int) -> float:
        """
        Score evidence based on volume
        
        Args:
            evidence_count: Number of evidence points
            
        Returns:
            Score from 0.0 to 1.0
        """
        if evidence_count >= UnifiedScoringEngine.VERY_STRONG_EVIDENCE:
            return 1.0
        elif evidence_count >= UnifiedScoringEngine.STRONG_EVIDENCE:
            return 0.85
        elif evidence_count >= UnifiedScoringEngine.MODERATE_EVIDENCE:
            return 0.70
        elif evidence_count >= UnifiedScoringEngine.WEAK_EVIDENCE:
            return 0.50
        elif evidence_count > 0:
            return 0.25
        else:
            return 0.0
    
    @staticmethod
    def _compute_bayesian_prior(
        evidence_count: int,
        prior_uploads: int
    ) -> float:
        """
        Compute Bayesian prior based on additional evidence
        
        Implements Bayesian update: as more evidence is uploaded for same case,
        confidence increases (up to a limit of 0.95 to avoid overconfidence)
        
        Args:
            evidence_count: New evidence being processed
            prior_uploads: Number of previous uploads for this case
            
        Returns:
            Prior score from 0.0 to 1.0
        """
        # Base: strength of new evidence
        base_score = 0.5 if evidence_count > 0 else 0.0
        
        # Boost from prior uploads (diminishing returns)
        if prior_uploads > 0:
            # Each prior upload adds 0.1 (up to max 5 priors = 0.5)
            prior_boost = min(prior_uploads * 0.1, 0.5)
            combined = base_score + prior_boost
        else:
            combined = base_score
        
        # Cap at 0.95 to avoid overconfidence
        return min(combined, 0.95)
    
    @staticmethod
    def combine_correlation_scores(
        timing_score: float,
        overlap_score: float,
        weight_timing: float = 0.6,
        weight_overlap: float = 0.4
    ) -> float:
        """
        Properly combine timing and overlap correlation scores
        
        Args:
            timing_score: Timing similarity (0.0-1.0)
            overlap_score: Session overlap (0.0-1.0)
            weight_timing: Weight for timing score (default 0.6 = 60%)
            weight_overlap: Weight for overlap score (default 0.4 = 40%)
            
        Returns:
            Combined score (0.0-1.0)
        """
        # Normalize weights
        total_weight = weight_timing + weight_overlap
        norm_timing = weight_timing / total_weight
        norm_overlap = weight_overlap / total_weight
        
        # Clamp individual scores to 0-1 range
        timing_clamped = max(0.0, min(1.0, timing_score))
        overlap_clamped = max(0.0, min(1.0, overlap_score))
        
        # Combine
        combined = (timing_clamped * norm_timing) + (overlap_clamped * norm_overlap)
        
        return combined
    
    @staticmethod
    def get_confidence_bar_width(confidence_level: str) -> int:
        """
        Get UI bar width percentage for confidence level
        
        Args:
            confidence_level: "High", "Medium", or "Low"
            
        Returns:
            Width percentage (0-100)
        """
        if confidence_level.lower() == "high":
            return 85
        elif confidence_level.lower() == "medium":
            return 55
        elif confidence_level.lower() == "low":
            return 25
        else:
            return 0
    
    @staticmethod
    def compute_uncertainty_margins(
        confidence_level: str,
        evidence_count: int
    ) -> Dict[str, int]:
        """
        Compute uncertainty margins for confidence level
        
        Args:
            confidence_level: "High", "Medium", or "Low"
            evidence_count: Number of evidence points
            
        Returns:
            Dict with upper and lower margin percentages
        """
        base_margin = {
            "High": 8,      # ±8%
            "Medium": 12,   # ±12%
            "Low": 25,      # ±25%
        }
        
        margin = base_margin.get(confidence_level, 15)
        
        # Adjust based on evidence volume
        if evidence_count > 50000:
            margin = max(5, margin - 3)  # Reduce uncertainty with strong evidence
        elif evidence_count < 5000:
            margin = min(30, margin + 5)  # Increase uncertainty with weak evidence
        
        return {
            "upper_margin": margin,
            "lower_margin": margin,
            "confidence_range_min": max(0, 100 - margin),
            "confidence_range_max": min(100, 100 + margin),
        }
    
    @staticmethod
    def estimate_false_positive_rate(
        confidence_level: str,
        evidence_count: int
    ) -> float:
        """
        Estimate false positive rate for confidence level
        
        Args:
            confidence_level: "High", "Medium", or "Low"
            evidence_count: Number of evidence points
            
        Returns:
            Estimated false positive rate (0.0-1.0)
        """
        base_rate = {
            "High": 0.12,    # ~12% FPR
            "Medium": 0.18,  # ~18% FPR
            "Low": 0.35,     # ~35% FPR
        }
        
        fpr = base_rate.get(confidence_level, 0.25)
        
        # Adjust based on evidence volume
        if evidence_count > 50000:
            fpr *= 0.5   # Half the FPR with strong evidence
        elif evidence_count < 5000:
            fpr *= 1.5   # Higher FPR with weak evidence
        
        return min(1.0, max(0.0, fpr))


# Convenience function for quick scoring
def score_correlation_hypothesis(
    evidence_count: int,
    timing_similarity: float,
    session_overlap: float,
    additional_evidence: int = 0,
    prior_uploads: int = 0
) -> Dict:
    """
    Score a correlation hypothesis with all factors
    
    Args:
        evidence_count: Number of evidence points
        timing_similarity: Timing correlation (0.0-1.0)
        session_overlap: Session overlap ratio (0.0-1.0)
        additional_evidence: Additional evidence pieces
        prior_uploads: Number of previous uploads
        
    Returns:
        Dictionary with confidence, bar_width, margins, and FPR
    """
    factors = ScoringFactors(
        evidence_count=evidence_count,
        timing_similarity=timing_similarity,
        session_overlap=session_overlap,
        additional_evidence_count=additional_evidence,
        prior_uploads=prior_uploads
    )
    
    confidence = UnifiedScoringEngine.compute_confidence_level(factors)
    
    return {
        "confidence_level": confidence,
        "bar_width": UnifiedScoringEngine.get_confidence_bar_width(confidence),
        "uncertainty_margins": UnifiedScoringEngine.compute_uncertainty_margins(
            confidence, evidence_count
        ),
        "estimated_fpr": UnifiedScoringEngine.estimate_false_positive_rate(
            confidence, evidence_count
        ),
    }
