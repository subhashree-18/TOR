"""
Cross-Case Correlation Engine
Compares investigations to detect shared infrastructure and patterns.

Analyzes:
- Shared guard node usage
- Temporal overlaps in activity
- Exit node similarities
- Behavioral pattern matching
- Statistical linkage scoring

Enables law enforcement multi-case analysis and pattern detection.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class SharedInfrastructure:
    """Shared infrastructure between two cases."""
    guard_nodes: List[str] = field(default_factory=list)
    exit_nodes: List[str] = field(default_factory=list)
    middle_nodes: List[str] = field(default_factory=list)
    shared_asns: List[str] = field(default_factory=list)
    
    def get_total_shared(self) -> int:
        """Count total shared infrastructure elements."""
        return len(self.guard_nodes) + len(self.exit_nodes) + len(self.middle_nodes)


@dataclass
class TemporalOverlap:
    """Temporal overlap analysis between cases."""
    case1_period: Tuple[datetime, datetime]
    case2_period: Tuple[datetime, datetime]
    overlap_start: Optional[datetime] = None
    overlap_end: Optional[datetime] = None
    overlap_days: float = 0.0
    overlap_percentage: float = 0.0  # 0-1, percentage of minimum duration
    
    def calculate(self) -> None:
        """Calculate temporal overlap metrics."""
        start1, end1 = self.case1_period
        start2, end2 = self.case2_period
        
        # Find overlap window
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start < overlap_end:
            self.overlap_start = overlap_start
            self.overlap_end = overlap_end
            self.overlap_days = (overlap_end - overlap_start).total_seconds() / 86400
            
            # Calculate as percentage of minimum case duration
            min_duration = min(
                (end1 - start1).total_seconds(),
                (end2 - start2).total_seconds()
            )
            if min_duration > 0:
                self.overlap_percentage = self.overlap_days * 86400 / min_duration


@dataclass
class CrossCaseLink:
    """Link between two investigations."""
    case_id_1: str
    case_id_2: str
    linkage_score: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    
    shared_infrastructure: SharedInfrastructure = field(default_factory=SharedInfrastructure)
    temporal_overlap: Optional[TemporalOverlap] = None
    behavioral_similarity: float = 0.0  # 0.0-1.0
    
    # Scoring breakdown
    guard_node_score: float = 0.0
    exit_node_score: float = 0.0
    temporal_score: float = 0.0
    behavioral_score: float = 0.0
    
    reasons: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.utcnow)


class CrossCaseCorrelationEngine:
    """
    Correlates TOR investigations across multiple cases.
    
    Identifies shared infrastructure, temporal patterns, and behavioral
    similarities to support multi-case investigations.
    """
    
    def __init__(self, db: Optional[Any] = None):
        self.db = db
        self.cases_collection = "investigations"
        self.links_collection = "cross_case_links"
        self.GUARD_WEIGHT = 0.35  # Guard node reuse is significant
        self.EXIT_WEIGHT = 0.25   # Exit is common, less discriminating
        self.TEMPORAL_WEIGHT = 0.20  # Timing overlap
        self.BEHAVIORAL_WEIGHT = 0.20  # Behavior pattern matching
    
    def _calculate_guard_score(self, shared_guards: List[str], total_guards_1: int, total_guards_2: int) -> Tuple[float, str]:
        """
        Score based on shared guard nodes.
        
        Guards are rare and reused - strong indicator of linkage.
        Normalized by case sizes to avoid bias.
        """
        if not shared_guards or total_guards_1 == 0 or total_guards_2 == 0:
            return 0.0, "No shared guards"
        
        # Normalize by case sizes
        min_total = min(total_guards_1, total_guards_2)
        shared_ratio = len(shared_guards) / min_total if min_total > 0 else 0
        
        score = 0.0
        reason = ""
        
        if shared_ratio > 0.7:  # >70% of minimum case guards shared
            score = 0.95
            reason = f"Very high guard reuse ({shared_ratio:.1%})"
        elif shared_ratio > 0.5:  # >50%
            score = 0.8
            reason = f"High guard reuse ({shared_ratio:.1%})"
        elif shared_ratio > 0.3:  # >30%
            score = 0.6
            reason = f"Moderate guard reuse ({shared_ratio:.1%})"
        elif shared_ratio > 0.1:  # >10%
            score = 0.3
            reason = f"Some guard reuse ({shared_ratio:.1%})"
        else:
            score = 0.1
            reason = f"Minimal guard reuse ({shared_ratio:.1%})"
        
        return score, reason
    
    def _calculate_exit_score(self, shared_exits: List[str], total_exits_1: int, total_exits_2: int) -> Tuple[float, str]:
        """
        Score based on shared exit nodes.
        
        Exits are more common than guards, but still indicative.
        Less weight than guard sharing.
        """
        if not shared_exits or total_exits_1 == 0 or total_exits_2 == 0:
            return 0.0, "No shared exits"
        
        min_total = min(total_exits_1, total_exits_2)
        shared_ratio = len(shared_exits) / min_total if min_total > 0 else 0
        
        score = 0.0
        reason = ""
        
        if shared_ratio > 0.6:
            score = 0.7
            reason = f"Multiple shared exits ({shared_ratio:.1%})"
        elif shared_ratio > 0.3:
            score = 0.5
            reason = f"Some shared exits ({shared_ratio:.1%})"
        elif shared_ratio > 0.1:
            score = 0.2
            reason = f"Few shared exits ({shared_ratio:.1%})"
        else:
            score = 0.05
            reason = f"Minimal exit sharing ({shared_ratio:.1%})"
        
        return score, reason
    
    def _calculate_temporal_score(self, overlap: TemporalOverlap) -> Tuple[float, str]:
        """
        Score based on temporal overlap.
        
        Cases active simultaneously may indicate related activity.
        Heavy weighting on degree of overlap.
        """
        if overlap.overlap_percentage == 0:
            return 0.0, "No temporal overlap"
        
        score = 0.0
        reason = ""
        
        if overlap.overlap_percentage > 0.8:  # >80% overlap
            score = 0.9
            reason = f"Nearly simultaneous ({overlap.overlap_days:.1f} days overlap)"
        elif overlap.overlap_percentage > 0.5:  # >50%
            score = 0.7
            reason = f"Significant overlap ({overlap.overlap_days:.1f} days)"
        elif overlap.overlap_percentage > 0.2:  # >20%
            score = 0.4
            reason = f"Partial overlap ({overlap.overlap_days:.1f} days)"
        else:
            score = 0.1
            reason = f"Minimal overlap ({overlap.overlap_days:.1f} days)"
        
        return score, reason
    
    def _calculate_behavioral_score(self, behavior_1: str, behavior_2: str) -> Tuple[float, str]:
        """
        Score based on behavioral pattern similarity.
        
        Same behavior types indicate related activity.
        """
        if behavior_1 == behavior_2 and behavior_1 != "unknown":
            score = 0.8
            reason = f"Matching behavior: {behavior_1}"
        elif behavior_1 != "unknown" and behavior_2 != "unknown":
            score = 0.2
            reason = f"Different behaviors: {behavior_1} vs {behavior_2}"
        else:
            score = 0.0
            reason = "Insufficient behavioral data"
        
        return score, reason
    
    def correlate_cases(
        self,
        case_id_1: str,
        case_data_1: Dict,  # Case document with nodes, timeline, behavior
        case_id_2: str,
        case_data_2: Dict,
    ) -> CrossCaseLink:
        """
        Correlate two investigation cases.
        
        Args:
            case_id_1: First case ID
            case_data_1: First case data including nodes, dates, behavior
            case_id_2: Second case ID
            case_data_2: Second case data
        
        Returns:
            CrossCaseLink with correlation analysis
        """
        link = CrossCaseLink(
            case_id_1=case_id_1,
            case_id_2=case_id_2,
            linkage_score=0.0,
            confidence=0.0,
        )
        
        # Extract infrastructure
        guards_1 = set(case_data_1.get("guard_nodes", []))
        guards_2 = set(case_data_2.get("guard_nodes", []))
        exits_1 = set(case_data_1.get("exit_nodes", []))
        exits_2 = set(case_data_2.get("exit_nodes", []))
        
        link.shared_infrastructure.guard_nodes = list(guards_1 & guards_2)
        link.shared_infrastructure.exit_nodes = list(exits_1 & exits_2)
        
        # Calculate infrastructure scores
        link.guard_node_score, guard_reason = self._calculate_guard_score(
            link.shared_infrastructure.guard_nodes,
            len(guards_1),
            len(guards_2)
        )
        if guard_reason:
            link.reasons.append(guard_reason)
        
        link.exit_node_score, exit_reason = self._calculate_exit_score(
            link.shared_infrastructure.exit_nodes,
            len(exits_1),
            len(exits_2)
        )
        if exit_reason:
            link.reasons.append(exit_reason)
        
        # Calculate temporal overlap
        start_1 = case_data_1.get("created_at")
        end_1 = case_data_1.get("analysis_completed_at") or datetime.utcnow()
        start_2 = case_data_2.get("created_at")
        end_2 = case_data_2.get("analysis_completed_at") or datetime.utcnow()
        
        if start_1 and start_2:
            link.temporal_overlap = TemporalOverlap(
                case1_period=(start_1, end_1),
                case2_period=(start_2, end_2)
            )
            link.temporal_overlap.calculate()
            
            link.temporal_score, temporal_reason = self._calculate_temporal_score(link.temporal_overlap)
            if temporal_reason:
                link.reasons.append(temporal_reason)
        
        # Calculate behavioral similarity
        behavior_1 = case_data_1.get("behavior_type", "unknown")
        behavior_2 = case_data_2.get("behavior_type", "unknown")
        link.behavioral_score, behavioral_reason = self._calculate_behavioral_score(behavior_1, behavior_2)
        if behavioral_reason:
            link.reasons.append(behavioral_reason)
        
        # Calculate overall linkage score (weighted average)
        weighted_score = (
            link.guard_node_score * self.GUARD_WEIGHT +
            link.exit_node_score * self.EXIT_WEIGHT +
            link.temporal_score * self.TEMPORAL_WEIGHT +
            link.behavioral_score * self.BEHAVIORAL_WEIGHT
        )
        
        link.linkage_score = weighted_score
        
        # Calculate confidence based on amount of supporting evidence
        evidence_count = 0
        if link.guard_node_score > 0:
            evidence_count += 1
        if link.exit_node_score > 0:
            evidence_count += 1
        if link.temporal_score > 0:
            evidence_count += 1
        if link.behavioral_score > 0:
            evidence_count += 1
        
        link.confidence = min(0.5 + (evidence_count * 0.125), 1.0)
        
        # Only consider linked if score > 0.3
        if link.linkage_score <= 0.3:
            link.reasons.insert(0, "Insufficient linkage evidence")
        else:
            link.reasons.insert(0, f"Linkage score: {link.linkage_score:.2f}")
        
        return link
    
    def store_link(self, link: CrossCaseLink) -> bool:
        """Store cross-case link in MongoDB."""
        if self.db is None:
            return False
        
        try:
            link_dict = {
                "case_id_1": link.case_id_1,
                "case_id_2": link.case_id_2,
                "linkage_score": link.linkage_score,
                "confidence": link.confidence,
                "shared_guards": link.shared_infrastructure.guard_nodes,
                "shared_exits": link.shared_infrastructure.exit_nodes,
                "guard_node_score": link.guard_node_score,
                "exit_node_score": link.exit_node_score,
                "temporal_score": link.temporal_score,
                "behavioral_score": link.behavioral_score,
                "reasons": link.reasons,
                "detected_at": link.detected_at,
            }
            
            if link.temporal_overlap:
                link_dict["temporal_overlap_days"] = link.temporal_overlap.overlap_days
                link_dict["temporal_overlap_percentage"] = link.temporal_overlap.overlap_percentage
            
            self.db[self.links_collection].insert_one(link_dict)
            logger.info(f"Stored cross-case link: {link.case_id_1} <-> {link.case_id_2}")
            return True
        except Exception as e:
            logger.error(f"Error storing cross-case link: {e}")
            return False
    
    def get_related_cases(self, case_id: str, min_score: float = 0.3) -> List[Tuple[str, float]]:
        """
        Get cases related to the given case.
        
        Args:
            case_id: Case to find relationships for
            min_score: Minimum linkage score to include
        
        Returns:
            List of (related_case_id, linkage_score) tuples
        """
        if self.db is None:
            return []
        
        try:
            related = []
            
            # Find links where case appears in either position
            cursor = self.db[self.links_collection].find({
                "$or": [
                    {"case_id_1": case_id},
                    {"case_id_2": case_id}
                ],
                "linkage_score": {"$gte": min_score}
            })
            
            for doc in cursor:
                # Get the other case ID
                other_id = doc["case_id_2"] if doc["case_id_1"] == case_id else doc["case_id_1"]
                score = doc["linkage_score"]
                related.append((other_id, score))
            
            # Sort by score descending
            related.sort(key=lambda x: x[1], reverse=True)
            return related
        except Exception as e:
            logger.error(f"Error getting related cases: {e}")
            return []
    
    def get_link_details(self, case_id_1: str, case_id_2: str) -> Optional[CrossCaseLink]:
        """Get detailed link information between two cases."""
        if self.db is None:
            return None
        
        try:
            doc = self.db[self.links_collection].find_one({
                "$or": [
                    {"case_id_1": case_id_1, "case_id_2": case_id_2},
                    {"case_id_1": case_id_2, "case_id_2": case_id_1}
                ]
            })
            
            if not doc:
                return None
            
            link = CrossCaseLink(
                case_id_1=doc["case_id_1"],
                case_id_2=doc["case_id_2"],
                linkage_score=doc["linkage_score"],
                confidence=doc["confidence"],
            )
            link.shared_infrastructure.guard_nodes = doc.get("shared_guards", [])
            link.shared_infrastructure.exit_nodes = doc.get("shared_exits", [])
            link.guard_node_score = doc.get("guard_node_score", 0)
            link.exit_node_score = doc.get("exit_node_score", 0)
            link.temporal_score = doc.get("temporal_score", 0)
            link.behavioral_score = doc.get("behavioral_score", 0)
            link.reasons = doc.get("reasons", [])
            
            return link
        except Exception as e:
            logger.error(f"Error getting link details: {e}")
            return None


# Singleton instance
_correlation_engine = None


def get_cross_case_correlation_engine(db: Optional[Any] = None) -> 'CrossCaseCorrelationEngine':
    """Get or create singleton instance of correlation engine."""
    global _correlation_engine
    if _correlation_engine is None:
        _correlation_engine = CrossCaseCorrelationEngine(db)
    return _correlation_engine
