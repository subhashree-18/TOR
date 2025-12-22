"""
Anti-False-Positive Validation Layer
Suppresses false correlations and improves confidence scoring accuracy.

Implements:
- CDN exit node exclusion lists
- Benign/research TOR relay blocklists
- Penalization for weak temporal overlaps
- One-time relay appearance filtering
- Confidence score adjustments
- Audit logging of suppressed correlations

Ensures forensic defensibility and transparency.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Set, Tuple, Any
from datetime import datetime, timedelta
import logging

try:
    from motor.motor_asyncio import AsyncIOMotorDatabase
except ImportError:
    AsyncIOMotorDatabase = Any

logger = logging.getLogger(__name__)


class ExclusionReason(Enum):
    """Reason for excluding a relay from correlation."""
    CDN_EXIT = "cdn_exit"                           # Known CDN exit node
    RESEARCH_RELAY = "research_relay"               # Academic/research relay
    VPNGATE = "vpngate"                             # VPN gate public exit
    TOR_PROJECT = "tor_project"                     # Official Tor Project relay
    BENIGN_EXIT = "benign_exit"                     # Known benign exit
    EXIT_COUNTRY_COMMON = "exit_country_common"     # Too many exits from same country
    MISSING_FINGERPRINT = "missing_fingerprint"     # No valid fingerprint


class TemporalPenalty(Enum):
    """Penalty categories for temporal analysis."""
    NO_OVERLAP = "no_overlap"                       # No time overlap
    VERY_SHORT_OVERLAP = "very_short_overlap"       # < 1 hour overlap
    SHORT_OVERLAP = "short_overlap"                 # 1-6 hours overlap
    MODERATE_OVERLAP = "moderate_overlap"           # 6-24 hours overlap
    EXTENDED_OVERLAP = "extended_overlap"           # > 24 hours overlap


@dataclass
class ExcludedRelay:
    """Excluded relay from correlation analysis."""
    fingerprint: str
    reason: ExclusionReason
    category: str  # "exit", "guard", "middle"
    details: str  # Description
    added_date: datetime = field(default_factory=datetime.utcnow)
    source: str = "manual"  # manual, automatic, research


@dataclass
class ValidationResult:
    """Result of false-positive validation."""
    relay_id: str
    should_exclude: bool = False
    exclusion_reason: Optional[ExclusionReason] = None
    confidence_adjustment: float = 0.0  # -0.3 to 0.0 (negative adjustment)
    penalty_factor: float = 1.0  # 0.0-1.0, multiplies base score
    reasons: List[str] = field(default_factory=list)
    audit_entry: Optional[Dict] = None


@dataclass
class TemporalValidation:
    """Validation of temporal overlap."""
    overlap_hours: float
    penalty: TemporalPenalty
    penalty_factor: float  # 0.0-1.0
    reason: str


class FalsePositiveValidator:
    """
    Validates correlations and filters false positives.
    
    Maintains exclusion lists and applies penalties to suppress
    unreliable correlations while maintaining audit trail.
    """
    
    def __init__(self, db: Optional[Any] = None):
        self.db = db
        self.exclusions_collection = "excluded_relays"
        self.audit_collection = "validation_audit"
        
        # Hard-coded known exclusions (can be updated)
        self.cdn_exits = self._initialize_cdn_exits()
        self.research_relays = self._initialize_research_relays()
        self.benign_relays = self._initialize_benign_relays()
    
    def _initialize_cdn_exits(self) -> Set[str]:
        """Initialize set of known CDN exit nodes."""
        return {
            "akamai_exit_1", "cloudflare_exit_1", "cloudflare_exit_2",
            "fastly_exit_1", "limelight_exit_1", "cdn77_exit_1"
        }
    
    def _initialize_research_relays(self) -> Set[str]:
        """Initialize set of known research/academic relays."""
        return {
            "mit_exit_1", "stanford_exit_1", "carnegie_exit_1",
            "berkeley_exit_1", "caltech_exit_1", "tor_project_exit_1"
        }
    
    def _initialize_benign_relays(self) -> Set[str]:
        """Initialize set of known benign relays."""
        return {
            "ispmail_exit", "public_proxy_exit", "isp_default_exit"
        }
    
    def _calculate_temporal_penalty(self, overlap_hours: float) -> TemporalValidation:
        """
        Calculate penalty for weak temporal overlap.
        
        Strong evidence requires significant time overlap.
        """
        if overlap_hours == 0:
            return TemporalValidation(
                overlap_hours=0,
                penalty=TemporalPenalty.NO_OVERLAP,
                penalty_factor=0.0,
                reason="No temporal overlap - exclude"
            )
        elif overlap_hours < 1:
            return TemporalValidation(
                overlap_hours=overlap_hours,
                penalty=TemporalPenalty.VERY_SHORT_OVERLAP,
                penalty_factor=0.2,
                reason="Very short overlap (< 1 hour) - weak evidence"
            )
        elif overlap_hours < 6:
            return TemporalValidation(
                overlap_hours=overlap_hours,
                penalty=TemporalPenalty.SHORT_OVERLAP,
                penalty_factor=0.5,
                reason="Short overlap (1-6 hours) - moderate evidence"
            )
        elif overlap_hours < 24:
            return TemporalValidation(
                overlap_hours=overlap_hours,
                penalty=TemporalPenalty.MODERATE_OVERLAP,
                penalty_factor=0.8,
                reason="Moderate overlap (6-24 hours) - good evidence"
            )
        else:
            return TemporalValidation(
                overlap_hours=overlap_hours,
                penalty=TemporalPenalty.EXTENDED_OVERLAP,
                penalty_factor=1.0,
                reason="Extended overlap (> 24 hours) - strong evidence"
            )
    
    def validate_relay(
        self,
        relay_id: str,
        fingerprint: str,
        relay_category: str,  # "guard", "exit", "middle"
        country: str = None,
        bandwidth_mbps: float = None,
        first_seen: Optional[datetime] = None,
        last_seen: Optional[datetime] = None,
    ) -> ValidationResult:
        """
        Validate a relay for use in correlation.
        
        Args:
            relay_id: Relay identifier
            fingerprint: Relay fingerprint
            relay_category: Type of relay
            country: Relay country
            bandwidth_mbps: Relay bandwidth
            first_seen: When relay first appeared
            last_seen: When relay was last active
        
        Returns:
            ValidationResult with exclusion and penalty info
        """
        result = ValidationResult(relay_id=relay_id)
        
        # Check for missing fingerprint
        if not fingerprint or fingerprint == "unknown":
            result.should_exclude = True
            result.exclusion_reason = ExclusionReason.MISSING_FINGERPRINT
            result.reasons.append("No valid fingerprint")
            return result
        
        # Check CDN exclusions (for exits only)
        if relay_category == "exit":
            if fingerprint in self.cdn_exits:
                result.should_exclude = True
                result.exclusion_reason = ExclusionReason.CDN_EXIT
                result.reasons.append("Known CDN exit node")
                return result
            
            # Check research/academic relays
            if fingerprint in self.research_relays:
                result.should_exclude = True
                result.exclusion_reason = ExclusionReason.RESEARCH_RELAY
                result.reasons.append("Known research/academic relay")
                return result
            
            # Check benign relays
            if fingerprint in self.benign_relays:
                result.should_exclude = True
                result.exclusion_reason = ExclusionReason.BENIGN_EXIT
                result.reasons.append("Known benign exit node")
                return result
        
        # Check if relay appeared only once (weak evidence)
        if first_seen and last_seen:
            appearance_duration = (last_seen - first_seen).total_seconds() / 3600
            if appearance_duration < 1:  # < 1 hour
                result.confidence_adjustment = -0.15
                result.reasons.append("Relay appeared for < 1 hour (weak evidence)")
        
        # Penalize low bandwidth exits
        if relay_category == "exit" and bandwidth_mbps and bandwidth_mbps < 1.0:
            result.confidence_adjustment -= 0.1
            result.reasons.append(f"Low bandwidth exit ({bandwidth_mbps} Mbps)")
        
        # Check exit country concentration
        if relay_category == "exit" and country:
            # Very common exit countries are less discriminating
            common_exit_countries = {"US", "NL", "DE", "FR", "RO", "GB"}
            if country in common_exit_countries:
                result.confidence_adjustment -= 0.05
                result.penalty_factor = 0.9
                result.reasons.append(f"Exit from common country ({country})")
        
        return result
    
    def validate_temporal_overlap(self, overlap_hours: float) -> TemporalValidation:
        """
        Validate temporal overlap between cases.
        
        Short overlaps are weak evidence and receive penalties.
        """
        return self._calculate_temporal_penalty(overlap_hours)
    
    def validate_correlation(
        self,
        case_id_1: str,
        case_id_2: str,
        shared_relays: Dict[str, List[str]],  # "guards" -> [fingerprints]
        overlap_hours: float,
        base_score: float,
        additional_validations: Dict = None
    ) -> Dict:
        """
        Comprehensive validation of a correlation.
        
        Args:
            case_id_1: First case
            case_id_2: Second case
            shared_relays: Shared relay fingerprints by category
            overlap_hours: Temporal overlap
            base_score: Original correlation score
            additional_validations: Additional validation data
        
        Returns:
            Validation result with adjusted score and suppression flags
        """
        result = {
            "case_id_1": case_id_1,
            "case_id_2": case_id_2,
            "original_score": base_score,
            "adjusted_score": base_score,
            "confidence_adjustment": 0.0,
            "suppress": False,
            "suppression_reason": None,
            "audit_entries": [],
            "validations": []
        }
        
        # Validate each shared relay
        excluded_count = 0
        total_relays = 0
        
        for category, relays in (shared_relays or {}).items():
            for relay_fp in relays:
                total_relays += 1
                relay_validation = self.validate_relay(
                    relay_id=relay_fp,
                    fingerprint=relay_fp,
                    relay_category=category
                )
                
                if relay_validation.should_exclude:
                    excluded_count += 1
                    result["audit_entries"].append({
                        "relay_id": relay_fp,
                        "reason": relay_validation.exclusion_reason.value,
                        "timestamp": datetime.utcnow()
                    })
                
                result["confidence_adjustment"] += relay_validation.confidence_adjustment
                result["validations"].append({
                    "relay": relay_fp,
                    "excluded": relay_validation.should_exclude,
                    "reasons": relay_validation.reasons
                })
        
        # Suppress if too many relays excluded
        if total_relays > 0 and excluded_count / total_relays > 0.5:
            result["suppress"] = True
            result["suppression_reason"] = f">{50}% of shared relays excluded"
            result["adjusted_score"] = 0.0
            return result
        
        # Validate temporal overlap
        temporal_val = self.validate_temporal_overlap(overlap_hours)
        
        if temporal_val.penalty == TemporalPenalty.NO_OVERLAP:
            result["suppress"] = True
            result["suppression_reason"] = "No temporal overlap"
            result["adjusted_score"] = 0.0
            return result
        
        # Apply temporal penalty
        result["adjusted_score"] = base_score * temporal_val.penalty_factor
        result["validations"].append({
            "type": "temporal",
            "overlap_hours": overlap_hours,
            "penalty_factor": temporal_val.penalty_factor,
            "reason": temporal_val.reason
        })
        
        # Final suppression check
        if result["adjusted_score"] < 0.2:
            result["suppress"] = True
            result["suppression_reason"] = f"Adjusted score too low ({result['adjusted_score']:.2f})"
        
        return result
    
    def log_suppressed_correlation(
        self,
        suppression_reason: str,
        original_score: float,
        adjusted_score: float,
        case_ids: Tuple[str, str],
        details: Dict = None
    ) -> bool:
        """
        Log a suppressed correlation for audit trail.
        
        Args:
            suppression_reason: Why correlation was suppressed
            original_score: Original correlation score
            adjusted_score: Adjusted score after validation
            case_ids: Tuple of (case_id_1, case_id_2)
            details: Additional details
        
        Returns:
            Success status
        """
        if self.db is None:
            return False
        
        try:
            audit_entry = {
                "case_id_1": case_ids[0],
                "case_id_2": case_ids[1],
                "suppression_reason": suppression_reason,
                "original_score": original_score,
                "adjusted_score": adjusted_score,
                "details": details or {},
                "timestamp": datetime.utcnow(),
                "logged_by": "validator"
            }
            
            self.db[self.audit_collection].insert_one(audit_entry)
            logger.info(
                f"Logged suppressed correlation: {case_ids[0]} <-> {case_ids[1]} "
                f"({original_score:.2f} -> {adjusted_score:.2f})"
            )
            return True
        except Exception as e:
            logger.error(f"Error logging suppressed correlation: {e}")
            return False
    
    def get_suppressed_correlations(
        self,
        case_id: str = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Retrieve suppressed correlations from audit log.
        
        Useful for reviewing why correlations were rejected.
        """
        if self.db is None:
            return []
        
        try:
            query = {}
            if case_id:
                query["$or"] = [
                    {"case_id_1": case_id},
                    {"case_id_2": case_id}
                ]
            if start_date or end_date:
                query["timestamp"] = {}
                if start_date:
                    query["timestamp"]["$gte"] = start_date
                if end_date:
                    query["timestamp"]["$lte"] = end_date
            
            cursor = self.db[self.audit_collection].find(query).limit(limit)
            results = []
            for doc in cursor:
                doc.pop("_id", None)
                results.append(doc)
            
            return results
        except Exception as e:
            logger.error(f"Error retrieving suppressed correlations: {e}")
            return []
    
    def add_exclusion(self, exclusion: ExcludedRelay) -> bool:
        """Add a relay to the exclusion list."""
        if self.db is None:
            return False
        
        try:
            exclusion_dict = {
                "fingerprint": exclusion.fingerprint,
                "reason": exclusion.reason.value,
                "category": exclusion.category,
                "details": exclusion.details,
                "added_date": exclusion.added_date,
                "source": exclusion.source,
            }
            
            self.db[self.exclusions_collection].insert_one(exclusion_dict)
            logger.info(f"Added exclusion: {exclusion.fingerprint} ({exclusion.reason.value})")
            return True
        except Exception as e:
            logger.error(f"Error adding exclusion: {e}")
            return False
    
    def get_exclusions(self, category: str = None) -> List[ExcludedRelay]:
        """Get all exclusions, optionally filtered by category."""
        if self.db is None:
            return []
        
        try:
            query = {}
            if category:
                query["category"] = category
            
            exclusions = []
            logger.info(f"Accessing database collection: {self.exclusions_collection}")
            logger.info(f"Database object type: {type(self.db)}")
            cursor = self.db[self.exclusions_collection].find(query)
            logger.info(f"Cursor type: {type(cursor)}")
            for doc in cursor:
                exclusion = ExcludedRelay(
                    fingerprint=doc["fingerprint"],
                    reason=ExclusionReason(doc["reason"]),
                    category=doc["category"],
                    details=doc["details"],
                    added_date=doc.get("added_date", datetime.utcnow()),
                    source=doc.get("source", "manual")
                )
                exclusions.append(exclusion)
            
            return exclusions
        except Exception as e:
            logger.error(f"Error retrieving exclusions: {e}", exc_info=True)
            return []


# Singleton instance
_validator = None


def get_false_positive_validator(db: Optional[Any] = None) -> FalsePositiveValidator:
    """Get or create singleton instance of validator."""
    global _validator
    if _validator is None or db is not None:
        _validator = FalsePositiveValidator(db)
    return _validator
