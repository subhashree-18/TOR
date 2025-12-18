"""
Confidence Evolution Tracker

Tracks confidence value changes over time as new evidence is correlated.
Maintains a chronological timeline demonstrating accuracy improvement
with increasing evidence from exit nodes and sessions.

This module provides:
1. ConfidenceSnapshot - Point-in-time confidence state
2. ConfidenceEvolutionTracker - Tracks confidence evolution per entry node
3. InvestigationConfidenceManager - Manages confidence across investigation

Author: TOR-Unveil Team
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import math
import logging
import uuid

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class ConfidenceChangeReason(Enum):
    """Reasons for confidence value changes"""
    INITIAL = "initial"  # First observation
    NEW_EXIT_NODE = "new_exit_node"  # New exit node correlated
    NEW_SESSION = "new_session"  # New session observed
    PCAP_EVIDENCE = "pcap_evidence"  # PCAP data correlated
    EVIDENCE_CONVERGENCE = "evidence_convergence"  # Multiple evidence types agree
    EVIDENCE_DIVERGENCE = "evidence_divergence"  # Conflicting evidence
    TIME_DECAY = "time_decay"  # Confidence decay over time
    MANUAL_ADJUSTMENT = "manual_adjustment"  # Investigator override
    BAYESIAN_UPDATE = "bayesian_update"  # Bayesian posterior update


class ConfidenceTrend(Enum):
    """Overall confidence trend direction"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ConfidenceSnapshot:
    """
    Point-in-time capture of confidence state.
    
    Represents confidence value at a specific moment with
    context about what triggered the change.
    """
    timestamp: datetime
    confidence_value: float  # 0.0 to 1.0
    confidence_level: str  # "high", "medium", "low", "insufficient"
    
    # Change context
    change_reason: ConfidenceChangeReason
    change_delta: float  # +/- change from previous
    
    # Evidence context at this point
    observation_count: int
    exit_nodes_observed: int
    sessions_observed: int
    
    # Supporting metrics
    evidence_strength: float  # Aggregate evidence quality
    evidence_consistency: float  # How consistent is evidence
    posterior_probability: float  # Current Bayesian posterior
    
    # Optional details
    trigger_exit_node: Optional[str] = None  # Exit node that triggered update
    trigger_session_id: Optional[str] = None  # Session that triggered update
    notes: Optional[str] = None  # Additional context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "confidence_value": round(self.confidence_value, 6),
            "confidence_level": self.confidence_level,
            "change_reason": self.change_reason.value,
            "change_delta": round(self.change_delta, 6),
            "observation_count": self.observation_count,
            "exit_nodes_observed": self.exit_nodes_observed,
            "sessions_observed": self.sessions_observed,
            "evidence_strength": round(self.evidence_strength, 4),
            "evidence_consistency": round(self.evidence_consistency, 4),
            "posterior_probability": round(self.posterior_probability, 6),
            "trigger_exit_node": self.trigger_exit_node,
            "trigger_session_id": self.trigger_session_id,
            "notes": self.notes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceSnapshot":
        """Create from dictionary"""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            confidence_value=data["confidence_value"],
            confidence_level=data["confidence_level"],
            change_reason=ConfidenceChangeReason(data["change_reason"]),
            change_delta=data["change_delta"],
            observation_count=data["observation_count"],
            exit_nodes_observed=data["exit_nodes_observed"],
            sessions_observed=data["sessions_observed"],
            evidence_strength=data["evidence_strength"],
            evidence_consistency=data["evidence_consistency"],
            posterior_probability=data["posterior_probability"],
            trigger_exit_node=data.get("trigger_exit_node"),
            trigger_session_id=data.get("trigger_session_id"),
            notes=data.get("notes"),
        )


@dataclass
class ConfidenceTimeline:
    """
    Chronological sequence of confidence snapshots for an entry node.
    
    Tracks the complete evolution of confidence for a specific
    entry node candidate across all observations.
    """
    entry_fingerprint: str
    entry_nickname: str
    
    # Timeline data
    snapshots: List[ConfidenceSnapshot] = field(default_factory=list)
    
    # Aggregate statistics
    initial_confidence: float = 0.0
    current_confidence: float = 0.0
    peak_confidence: float = 0.0
    min_confidence: float = 1.0
    
    # Evolution metrics
    total_updates: int = 0
    positive_updates: int = 0  # Confidence increased
    negative_updates: int = 0  # Confidence decreased
    
    # Timestamps
    first_observation: Optional[datetime] = None
    last_update: Optional[datetime] = None
    
    def add_snapshot(self, snapshot: ConfidenceSnapshot) -> None:
        """Add a new snapshot to the timeline"""
        self.snapshots.append(snapshot)
        self.total_updates += 1
        
        if snapshot.change_delta > 0:
            self.positive_updates += 1
        elif snapshot.change_delta < 0:
            self.negative_updates += 1
        
        self.current_confidence = snapshot.confidence_value
        self.peak_confidence = max(self.peak_confidence, snapshot.confidence_value)
        self.min_confidence = min(self.min_confidence, snapshot.confidence_value)
        
        if self.first_observation is None:
            self.first_observation = snapshot.timestamp
            self.initial_confidence = snapshot.confidence_value
        
        self.last_update = snapshot.timestamp
    
    def get_trend(self, window_size: int = 5) -> ConfidenceTrend:
        """
        Determine confidence trend from recent snapshots.
        
        Args:
            window_size: Number of recent snapshots to analyze
            
        Returns:
            ConfidenceTrend enum value
        """
        if len(self.snapshots) < 2:
            return ConfidenceTrend.STABLE
        
        recent = self.snapshots[-window_size:]
        deltas = [s.change_delta for s in recent]
        
        if not deltas:
            return ConfidenceTrend.STABLE
        
        avg_delta = sum(deltas) / len(deltas)
        
        # Check for volatility (high variance in deltas)
        variance = sum((d - avg_delta) ** 2 for d in deltas) / len(deltas)
        std_dev = math.sqrt(variance)
        
        if std_dev > 0.1:  # High variance threshold
            return ConfidenceTrend.VOLATILE
        elif avg_delta > 0.01:
            return ConfidenceTrend.IMPROVING
        elif avg_delta < -0.01:
            return ConfidenceTrend.DECLINING
        else:
            return ConfidenceTrend.STABLE
    
    def get_improvement_rate(self) -> float:
        """
        Calculate rate of confidence improvement per observation.
        
        Returns:
            Average confidence gain per observation
        """
        if self.total_updates <= 1:
            return 0.0
        
        total_change = self.current_confidence - self.initial_confidence
        return total_change / (self.total_updates - 1)
    
    def get_convergence_score(self) -> float:
        """
        Measure how much confidence has converged (stabilized).
        
        Returns:
            0.0 (volatile) to 1.0 (fully converged)
        """
        if len(self.snapshots) < 3:
            return 0.0
        
        # Look at recent delta magnitudes
        recent = self.snapshots[-5:]
        delta_magnitudes = [abs(s.change_delta) for s in recent]
        avg_magnitude = sum(delta_magnitudes) / len(delta_magnitudes)
        
        # Map to convergence score (small deltas = high convergence)
        # 0.05 delta -> 0.5 convergence, 0.01 delta -> 0.9 convergence
        convergence = 1.0 - min(avg_magnitude * 10, 1.0)
        return round(convergence, 4)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "entry_fingerprint": self.entry_fingerprint,
            "entry_nickname": self.entry_nickname,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "initial_confidence": round(self.initial_confidence, 6),
            "current_confidence": round(self.current_confidence, 6),
            "peak_confidence": round(self.peak_confidence, 6),
            "min_confidence": round(self.min_confidence, 6),
            "total_updates": self.total_updates,
            "positive_updates": self.positive_updates,
            "negative_updates": self.negative_updates,
            "first_observation": self.first_observation.isoformat() if self.first_observation else None,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "trend": self.get_trend().value,
            "improvement_rate": round(self.get_improvement_rate(), 6),
            "convergence_score": self.get_convergence_score(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceTimeline":
        """Create from dictionary"""
        timeline = cls(
            entry_fingerprint=data["entry_fingerprint"],
            entry_nickname=data["entry_nickname"],
            initial_confidence=data.get("initial_confidence", 0.0),
            current_confidence=data.get("current_confidence", 0.0),
            peak_confidence=data.get("peak_confidence", 0.0),
            min_confidence=data.get("min_confidence", 1.0),
            total_updates=data.get("total_updates", 0),
            positive_updates=data.get("positive_updates", 0),
            negative_updates=data.get("negative_updates", 0),
            first_observation=datetime.fromisoformat(data["first_observation"]) if data.get("first_observation") else None,
            last_update=datetime.fromisoformat(data["last_update"]) if data.get("last_update") else None,
        )
        timeline.snapshots = [
            ConfidenceSnapshot.from_dict(s) for s in data.get("snapshots", [])
        ]
        return timeline


# ============================================================================
# CONFIDENCE EVOLUTION TRACKER
# ============================================================================

class ConfidenceEvolutionTracker:
    """
    Tracks confidence evolution for entry node candidates.
    
    Maintains chronological timelines showing how confidence
    improves (or degrades) as more evidence is correlated.
    
    Example usage:
        tracker = ConfidenceEvolutionTracker()
        
        # Record initial observation
        tracker.record_update(
            entry_fingerprint="ABC123...",
            entry_nickname="RelayOne",
            new_confidence=0.3,
            posterior=0.15,
            reason=ConfidenceChangeReason.INITIAL,
            exit_node="EXIT123...",
        )
        
        # Record subsequent correlation
        tracker.record_update(
            entry_fingerprint="ABC123...",
            entry_nickname="RelayOne",
            new_confidence=0.45,
            posterior=0.22,
            reason=ConfidenceChangeReason.NEW_EXIT_NODE,
            exit_node="EXIT456...",
        )
        
        # Get timeline
        timeline = tracker.get_timeline("ABC123...")
        print(timeline.get_trend())  # ConfidenceTrend.IMPROVING
    """
    
    def __init__(self):
        """Initialize tracker with empty timelines"""
        self._timelines: Dict[str, ConfidenceTimeline] = {}
        self._exit_nodes_seen: Dict[str, set] = {}  # fingerprint -> set of exit fingerprints
        self._sessions_seen: Dict[str, set] = {}  # fingerprint -> set of session IDs
        self._global_observation_count = 0
    
    def record_update(
        self,
        entry_fingerprint: str,
        entry_nickname: str,
        new_confidence: float,
        posterior: float,
        reason: ConfidenceChangeReason,
        evidence_strength: float = 0.5,
        evidence_consistency: float = 0.5,
        exit_node: Optional[str] = None,
        session_id: Optional[str] = None,
        notes: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> ConfidenceSnapshot:
        """
        Record a confidence update for an entry node.
        
        Args:
            entry_fingerprint: Entry relay fingerprint
            entry_nickname: Entry relay nickname
            new_confidence: New confidence value (0.0-1.0)
            posterior: Bayesian posterior probability
            reason: Reason for the update
            evidence_strength: Quality of evidence (0.0-1.0)
            evidence_consistency: Consistency of evidence (0.0-1.0)
            exit_node: Exit node fingerprint that triggered update
            session_id: Session ID that triggered update
            notes: Additional context
            timestamp: Timestamp (defaults to now)
            
        Returns:
            The created ConfidenceSnapshot
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)
        
        # Get or create timeline
        if entry_fingerprint not in self._timelines:
            self._timelines[entry_fingerprint] = ConfidenceTimeline(
                entry_fingerprint=entry_fingerprint,
                entry_nickname=entry_nickname,
            )
            self._exit_nodes_seen[entry_fingerprint] = set()
            self._sessions_seen[entry_fingerprint] = set()
        
        timeline = self._timelines[entry_fingerprint]
        
        # Track exit nodes and sessions
        if exit_node:
            self._exit_nodes_seen[entry_fingerprint].add(exit_node)
        if session_id:
            self._sessions_seen[entry_fingerprint].add(session_id)
        
        # Calculate change delta
        previous_confidence = timeline.current_confidence if timeline.snapshots else 0.0
        change_delta = new_confidence - previous_confidence
        
        # Determine confidence level
        confidence_level = self._confidence_to_level(new_confidence)
        
        # Increment observation count
        self._global_observation_count += 1
        
        # Create snapshot
        snapshot = ConfidenceSnapshot(
            timestamp=timestamp,
            confidence_value=new_confidence,
            confidence_level=confidence_level,
            change_reason=reason,
            change_delta=change_delta,
            observation_count=self._global_observation_count,
            exit_nodes_observed=len(self._exit_nodes_seen[entry_fingerprint]),
            sessions_observed=len(self._sessions_seen[entry_fingerprint]),
            evidence_strength=evidence_strength,
            evidence_consistency=evidence_consistency,
            posterior_probability=posterior,
            trigger_exit_node=exit_node,
            trigger_session_id=session_id,
            notes=notes,
        )
        
        # Add to timeline
        timeline.add_snapshot(snapshot)
        
        logger.debug(
            f"Recorded confidence update for {entry_nickname}: "
            f"{previous_confidence:.4f} -> {new_confidence:.4f} ({change_delta:+.4f}) "
            f"[{reason.value}]"
        )
        
        return snapshot
    
    def _confidence_to_level(self, confidence: float) -> str:
        """Convert confidence value to level string"""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        elif confidence >= 0.2:
            return "low"
        else:
            return "insufficient"
    
    def get_timeline(self, entry_fingerprint: str) -> Optional[ConfidenceTimeline]:
        """Get confidence timeline for an entry node"""
        return self._timelines.get(entry_fingerprint)
    
    def get_all_timelines(self) -> Dict[str, ConfidenceTimeline]:
        """Get all confidence timelines"""
        return self._timelines.copy()
    
    def get_current_confidence(self, entry_fingerprint: str) -> Optional[float]:
        """Get current confidence value for an entry node"""
        timeline = self._timelines.get(entry_fingerprint)
        if timeline:
            return timeline.current_confidence
        return None
    
    def get_top_candidates(self, top_k: int = 10) -> List[Tuple[str, float, ConfidenceTrend]]:
        """
        Get top entry node candidates by current confidence.
        
        Args:
            top_k: Number of top candidates to return
            
        Returns:
            List of (fingerprint, confidence, trend) tuples
        """
        candidates = [
            (fp, tl.current_confidence, tl.get_trend())
            for fp, tl in self._timelines.items()
        ]
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:top_k]
    
    def get_improving_candidates(self) -> List[str]:
        """Get fingerprints of candidates with improving confidence"""
        return [
            fp for fp, tl in self._timelines.items()
            if tl.get_trend() == ConfidenceTrend.IMPROVING
        ]
    
    def get_converged_candidates(self, threshold: float = 0.7) -> List[str]:
        """
        Get fingerprints of candidates with converged (stable) confidence.
        
        Args:
            threshold: Minimum convergence score to consider converged
            
        Returns:
            List of fingerprints with high convergence
        """
        return [
            fp for fp, tl in self._timelines.items()
            if tl.get_convergence_score() >= threshold
        ]
    
    def compute_accuracy_improvement(self, entry_fingerprint: str) -> Dict[str, Any]:
        """
        Compute detailed accuracy improvement metrics for an entry node.
        
        Args:
            entry_fingerprint: Entry relay fingerprint
            
        Returns:
            Dictionary with improvement metrics
        """
        timeline = self._timelines.get(entry_fingerprint)
        if not timeline or len(timeline.snapshots) < 2:
            return {
                "has_data": False,
                "message": "Insufficient data for accuracy analysis",
            }
        
        snapshots = timeline.snapshots
        
        # Calculate improvement at key milestones
        milestones = {}
        for i, s in enumerate(snapshots):
            if s.exit_nodes_observed in [1, 2, 3, 5, 10]:
                milestones[f"after_{s.exit_nodes_observed}_exit_nodes"] = s.confidence_value
        
        # Calculate improvement by evidence type
        by_reason = {}
        for s in snapshots:
            reason = s.change_reason.value
            if reason not in by_reason:
                by_reason[reason] = {"count": 0, "total_delta": 0.0}
            by_reason[reason]["count"] += 1
            by_reason[reason]["total_delta"] += s.change_delta
        
        # Calculate rolling improvement rate
        window_size = min(5, len(snapshots))
        recent_deltas = [s.change_delta for s in snapshots[-window_size:]]
        recent_improvement_rate = sum(recent_deltas) / len(recent_deltas)
        
        return {
            "has_data": True,
            "initial_confidence": timeline.initial_confidence,
            "current_confidence": timeline.current_confidence,
            "total_improvement": timeline.current_confidence - timeline.initial_confidence,
            "improvement_percentage": (
                ((timeline.current_confidence - timeline.initial_confidence) / max(timeline.initial_confidence, 0.01)) * 100
                if timeline.initial_confidence > 0 else 0
            ),
            "total_updates": timeline.total_updates,
            "positive_updates": timeline.positive_updates,
            "negative_updates": timeline.negative_updates,
            "positive_ratio": timeline.positive_updates / max(timeline.total_updates, 1),
            "trend": timeline.get_trend().value,
            "convergence_score": timeline.get_convergence_score(),
            "improvement_rate_per_observation": timeline.get_improvement_rate(),
            "recent_improvement_rate": recent_improvement_rate,
            "milestones": milestones,
            "by_change_reason": by_reason,
            "exit_nodes_observed": len(self._exit_nodes_seen.get(entry_fingerprint, set())),
            "sessions_observed": len(self._sessions_seen.get(entry_fingerprint, set())),
        }
    
    def export_state(self) -> Dict[str, Any]:
        """
        Export tracker state for persistence.
        
        Returns:
            Dictionary with all tracker state
        """
        return {
            "timelines": {
                fp: tl.to_dict() for fp, tl in self._timelines.items()
            },
            "exit_nodes_seen": {
                fp: list(exits) for fp, exits in self._exit_nodes_seen.items()
            },
            "sessions_seen": {
                fp: list(sessions) for fp, sessions in self._sessions_seen.items()
            },
            "global_observation_count": self._global_observation_count,
            "export_timestamp": datetime.now(timezone.utc).isoformat(),
        }
    
    def import_state(self, state: Dict[str, Any]) -> None:
        """
        Import tracker state from persistence.
        
        Args:
            state: Dictionary with tracker state from export_state()
        """
        # Import timelines
        self._timelines = {
            fp: ConfidenceTimeline.from_dict(tl_data)
            for fp, tl_data in state.get("timelines", {}).items()
        }
        
        # Import exit nodes seen
        self._exit_nodes_seen = {
            fp: set(exits) for fp, exits in state.get("exit_nodes_seen", {}).items()
        }
        
        # Import sessions seen
        self._sessions_seen = {
            fp: set(sessions) for fp, sessions in state.get("sessions_seen", {}).items()
        }
        
        # Import observation count
        self._global_observation_count = state.get("global_observation_count", 0)
        
        logger.info(
            f"Imported confidence evolution state: "
            f"{len(self._timelines)} timelines, "
            f"{self._global_observation_count} observations"
        )
    
    def reset(self) -> None:
        """Reset all tracking state"""
        self._timelines.clear()
        self._exit_nodes_seen.clear()
        self._sessions_seen.clear()
        self._global_observation_count = 0


# ============================================================================
# INVESTIGATION CONFIDENCE MANAGER
# ============================================================================

class InvestigationConfidenceManager:
    """
    Manages confidence evolution across an entire investigation.
    
    Coordinates confidence tracking with investigation persistence,
    enabling confidence timelines to be saved and restored.
    """
    
    def __init__(
        self,
        investigation_id: Optional[str] = None,
        tracker: Optional[ConfidenceEvolutionTracker] = None,
    ):
        """
        Initialize manager.
        
        Args:
            investigation_id: Unique investigation identifier
            tracker: Existing tracker to use (creates new if None)
        """
        self.investigation_id = investigation_id or str(uuid.uuid4())
        self.tracker = tracker or ConfidenceEvolutionTracker()
        self._created_at = datetime.now(timezone.utc)
        self._last_activity = self._created_at
    
    def record_exit_node_correlation(
        self,
        entry_fingerprint: str,
        entry_nickname: str,
        exit_fingerprint: str,
        new_confidence: float,
        posterior: float,
        evidence_strength: float,
        evidence_consistency: float,
        session_id: Optional[str] = None,
    ) -> ConfidenceSnapshot:
        """
        Record confidence update when a new exit node is correlated.
        
        Args:
            entry_fingerprint: Entry relay fingerprint
            entry_nickname: Entry relay nickname
            exit_fingerprint: Correlated exit node fingerprint
            new_confidence: Updated confidence value
            posterior: Bayesian posterior probability
            evidence_strength: Quality of evidence
            evidence_consistency: Consistency of evidence
            session_id: Optional session identifier
            
        Returns:
            Created ConfidenceSnapshot
        """
        self._last_activity = datetime.now(timezone.utc)
        
        # Determine if this is initial or subsequent
        timeline = self.tracker.get_timeline(entry_fingerprint)
        if timeline is None or len(timeline.snapshots) == 0:
            reason = ConfidenceChangeReason.INITIAL
        else:
            reason = ConfidenceChangeReason.NEW_EXIT_NODE
        
        return self.tracker.record_update(
            entry_fingerprint=entry_fingerprint,
            entry_nickname=entry_nickname,
            new_confidence=new_confidence,
            posterior=posterior,
            reason=reason,
            evidence_strength=evidence_strength,
            evidence_consistency=evidence_consistency,
            exit_node=exit_fingerprint,
            session_id=session_id,
        )
    
    def record_session_correlation(
        self,
        entry_fingerprint: str,
        entry_nickname: str,
        session_id: str,
        new_confidence: float,
        posterior: float,
        evidence_strength: float,
        evidence_consistency: float,
        exit_fingerprint: Optional[str] = None,
    ) -> ConfidenceSnapshot:
        """
        Record confidence update when a new session is correlated.
        
        Args:
            entry_fingerprint: Entry relay fingerprint
            entry_nickname: Entry relay nickname
            session_id: Session identifier
            new_confidence: Updated confidence value
            posterior: Bayesian posterior probability
            evidence_strength: Quality of evidence
            evidence_consistency: Consistency of evidence
            exit_fingerprint: Optional exit node in session
            
        Returns:
            Created ConfidenceSnapshot
        """
        self._last_activity = datetime.now(timezone.utc)
        
        return self.tracker.record_update(
            entry_fingerprint=entry_fingerprint,
            entry_nickname=entry_nickname,
            new_confidence=new_confidence,
            posterior=posterior,
            reason=ConfidenceChangeReason.NEW_SESSION,
            evidence_strength=evidence_strength,
            evidence_consistency=evidence_consistency,
            exit_node=exit_fingerprint,
            session_id=session_id,
        )
    
    def record_pcap_evidence(
        self,
        entry_fingerprint: str,
        entry_nickname: str,
        new_confidence: float,
        posterior: float,
        evidence_strength: float,
        pcap_details: Optional[str] = None,
    ) -> ConfidenceSnapshot:
        """
        Record confidence update when PCAP evidence is correlated.
        
        Args:
            entry_fingerprint: Entry relay fingerprint
            entry_nickname: Entry relay nickname
            new_confidence: Updated confidence value
            posterior: Bayesian posterior probability
            evidence_strength: Quality of PCAP evidence
            pcap_details: Description of PCAP evidence
            
        Returns:
            Created ConfidenceSnapshot
        """
        self._last_activity = datetime.now(timezone.utc)
        
        return self.tracker.record_update(
            entry_fingerprint=entry_fingerprint,
            entry_nickname=entry_nickname,
            new_confidence=new_confidence,
            posterior=posterior,
            reason=ConfidenceChangeReason.PCAP_EVIDENCE,
            evidence_strength=evidence_strength,
            evidence_consistency=0.9,  # PCAP is highly consistent
            notes=pcap_details,
        )
    
    def record_bayesian_update(
        self,
        entry_fingerprint: str,
        entry_nickname: str,
        new_confidence: float,
        posterior: float,
        evidence_strength: float,
        evidence_consistency: float,
        notes: Optional[str] = None,
    ) -> ConfidenceSnapshot:
        """
        Record general Bayesian inference update.
        
        Args:
            entry_fingerprint: Entry relay fingerprint
            entry_nickname: Entry relay nickname
            new_confidence: Updated confidence value
            posterior: Bayesian posterior probability
            evidence_strength: Quality of evidence
            evidence_consistency: Consistency of evidence
            notes: Additional context
            
        Returns:
            Created ConfidenceSnapshot
        """
        self._last_activity = datetime.now(timezone.utc)
        
        return self.tracker.record_update(
            entry_fingerprint=entry_fingerprint,
            entry_nickname=entry_nickname,
            new_confidence=new_confidence,
            posterior=posterior,
            reason=ConfidenceChangeReason.BAYESIAN_UPDATE,
            evidence_strength=evidence_strength,
            evidence_consistency=evidence_consistency,
            notes=notes,
        )
    
    def get_investigation_summary(self) -> Dict[str, Any]:
        """
        Get summary of confidence evolution across the investigation.
        
        Returns:
            Dictionary with investigation-level metrics
        """
        timelines = self.tracker.get_all_timelines()
        
        if not timelines:
            return {
                "investigation_id": self.investigation_id,
                "has_data": False,
                "message": "No confidence data recorded",
            }
        
        # Aggregate statistics
        all_confidences = [tl.current_confidence for tl in timelines.values()]
        all_improvements = [
            tl.current_confidence - tl.initial_confidence
            for tl in timelines.values()
        ]
        
        # Count by trend
        trends = [tl.get_trend() for tl in timelines.values()]
        trend_counts = {
            "improving": sum(1 for t in trends if t == ConfidenceTrend.IMPROVING),
            "stable": sum(1 for t in trends if t == ConfidenceTrend.STABLE),
            "declining": sum(1 for t in trends if t == ConfidenceTrend.DECLINING),
            "volatile": sum(1 for t in trends if t == ConfidenceTrend.VOLATILE),
        }
        
        # Get top candidate
        top_candidates = self.tracker.get_top_candidates(top_k=5)
        
        return {
            "investigation_id": self.investigation_id,
            "has_data": True,
            "created_at": self._created_at.isoformat(),
            "last_activity": self._last_activity.isoformat(),
            "entry_nodes_tracked": len(timelines),
            "total_observations": self.tracker._global_observation_count,
            "confidence_stats": {
                "mean": sum(all_confidences) / len(all_confidences),
                "max": max(all_confidences),
                "min": min(all_confidences),
            },
            "improvement_stats": {
                "mean": sum(all_improvements) / len(all_improvements),
                "max": max(all_improvements),
                "min": min(all_improvements),
            },
            "trend_distribution": trend_counts,
            "top_candidates": [
                {
                    "fingerprint": fp,
                    "confidence": conf,
                    "trend": trend.value,
                }
                for fp, conf, trend in top_candidates
            ],
            "converged_count": len(self.tracker.get_converged_candidates()),
        }
    
    def export_for_investigation(self) -> Dict[str, Any]:
        """
        Export confidence evolution data for investigation persistence.
        
        Returns:
            Dictionary suitable for MongoDB storage
        """
        return {
            "investigation_id": self.investigation_id,
            "created_at": self._created_at.isoformat(),
            "last_activity": self._last_activity.isoformat(),
            "tracker_state": self.tracker.export_state(),
        }
    
    @classmethod
    def from_investigation(cls, data: Dict[str, Any]) -> "InvestigationConfidenceManager":
        """
        Create manager from investigation persistence data.
        
        Args:
            data: Dictionary from export_for_investigation()
            
        Returns:
            Restored InvestigationConfidenceManager
        """
        tracker = ConfidenceEvolutionTracker()
        tracker.import_state(data.get("tracker_state", {}))
        
        manager = cls(
            investigation_id=data.get("investigation_id"),
            tracker=tracker,
        )
        
        if data.get("created_at"):
            manager._created_at = datetime.fromisoformat(data["created_at"])
        if data.get("last_activity"):
            manager._last_activity = datetime.fromisoformat(data["last_activity"])
        
        return manager
