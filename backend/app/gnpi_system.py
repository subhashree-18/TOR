"""
Guard Node Reputation & Persistence Index (GNPI) System

This module implements a reputation tracking system for TOR guard nodes based on:
- Frequency of appearance across investigations
- Persistence/longevity (how long a guard remains active)
- Reliability scoring
- Historical behavior patterns

The GNPI score becomes a factor in overall origin confidence calculation,
penalizing short-lived guards and rewarding long-lived recurring nodes.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import json

from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


class PersistenceLevel(Enum):
    """Persistence levels for guard nodes."""
    LOW = "LOW"           # < 7 days active
    MEDIUM = "MEDIUM"     # 7-30 days active
    HIGH = "HIGH"         # > 30 days active
    CRITICAL = "CRITICAL" # > 90 days, multiple cases


@dataclass
class GuardNodeReputation:
    """Tracks reputation metrics for a single guard node."""
    guard_fingerprint: str
    first_seen: datetime
    last_seen: datetime
    appearance_count: int = 1  # How many investigations has this guard appeared in?
    reliability_score: float = 0.5  # 0.0 (unreliable) to 1.0 (highly reliable)
    persistence_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    gnpi_score: float = 0.0  # Guard Node Persistence Index (0.0-1.0)
    successful_correlations: int = 0
    failed_correlations: int = 0
    average_uptime_percentage: float = 0.0
    country: str = "UNKNOWN"
    asn: int = 0
    last_updated: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to MongoDB-compatible dictionary."""
        return {
            "guard_fingerprint": self.guard_fingerprint,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "appearance_count": self.appearance_count,
            "reliability_score": self.reliability_score,
            "persistence_level": self.persistence_level,
            "gnpi_score": self.gnpi_score,
            "successful_correlations": self.successful_correlations,
            "failed_correlations": self.failed_correlations,
            "average_uptime_percentage": self.average_uptime_percentage,
            "country": self.country,
            "asn": self.asn,
            "last_updated": self.last_updated,
            "notes": self.notes
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'GuardNodeReputation':
        """Create from MongoDB document."""
        return GuardNodeReputation(
            guard_fingerprint=data.get("guard_fingerprint", ""),
            first_seen=data.get("first_seen", datetime.utcnow()),
            last_seen=data.get("last_seen", datetime.utcnow()),
            appearance_count=data.get("appearance_count", 1),
            reliability_score=data.get("reliability_score", 0.5),
            persistence_level=data.get("persistence_level", "LOW"),
            gnpi_score=data.get("gnpi_score", 0.0),
            successful_correlations=data.get("successful_correlations", 0),
            failed_correlations=data.get("failed_correlations", 0),
            average_uptime_percentage=data.get("average_uptime_percentage", 0.0),
            country=data.get("country", "UNKNOWN"),
            asn=data.get("asn", 0),
            last_updated=data.get("last_updated", datetime.utcnow()),
            notes=data.get("notes", "")
        )


class GNPISystem:
    """Guard Node Reputation & Persistence Index System."""
    
    def __init__(self, db=None):
        """Initialize GNPI system with MongoDB connection."""
        self.db = db
        self._init_collections()
    
    def _init_collections(self):
        """Initialize MongoDB collections with proper indexing."""
        if self.db is None:
            logger.warning("Database not initialized for GNPI system")
            return
        
        try:
            # Create guard_node_reputation collection with indexes
            if "guard_node_reputation" not in self.db.list_collection_names():
                self.db.create_collection("guard_node_reputation")
            
            collection = self.db["guard_node_reputation"]
            
            # Create indexes for fast lookup
            collection.create_index([("guard_fingerprint", ASCENDING)], unique=True)
            collection.create_index([("gnpi_score", DESCENDING)])
            collection.create_index([("persistence_level", ASCENDING)])
            collection.create_index([("appearance_count", DESCENDING)])
            collection.create_index([("last_seen", DESCENDING)])
            collection.create_index([("reliability_score", DESCENDING)])
            
            logger.info("GNPI collections initialized with indexes")
        except PyMongoError as e:
            logger.error(f"Error initializing GNPI collections: {e}")
    
    def calculate_persistence_level(self, guard_rep: GuardNodeReputation) -> str:
        """
        Calculate persistence level based on active duration.
        
        LOW:      < 7 days
        MEDIUM:   7-30 days
        HIGH:     30-90 days
        CRITICAL: > 90 days
        """
        if guard_rep.first_seen is None or guard_rep.last_seen is None:
            return "LOW"
        
        duration = guard_rep.last_seen - guard_rep.first_seen
        days_active = duration.days
        
        if days_active >= 90:
            return "CRITICAL"
        elif days_active >= 30:
            return "HIGH"
        elif days_active >= 7:
            return "MEDIUM"
        else:
            return "LOW"
    
    def calculate_gnpi_score(self, guard_rep: GuardNodeReputation) -> float:
        """
        Calculate Guard Node Persistence Index (GNPI) score.
        
        Factors:
        - Persistence level (40%): How long the guard has been active
        - Appearance frequency (30%): How many investigations it appears in
        - Reliability (20%): Successful correlation rate
        - Uptime (10%): Average uptime percentage
        
        Returns: Score from 0.0 (untrusted) to 1.0 (highly trusted)
        """
        try:
            # 1. Persistence component (40%)
            persistence_scores = {
                "LOW": 0.2,
                "MEDIUM": 0.5,
                "HIGH": 0.8,
                "CRITICAL": 1.0
            }
            persistence_score = persistence_scores.get(guard_rep.persistence_level, 0.2)
            
            # 2. Appearance frequency component (30%)
            # Normalize: 1-5 appearances = 0.2-1.0
            appearance_score = min(1.0, max(0.1, guard_rep.appearance_count / 5.0))
            
            # 3. Reliability component (20%)
            total_correlations = guard_rep.successful_correlations + guard_rep.failed_correlations
            if total_correlations > 0:
                reliability_score = guard_rep.successful_correlations / total_correlations
            else:
                reliability_score = 0.5  # Neutral if no data
            
            # 4. Uptime component (10%)
            uptime_score = guard_rep.average_uptime_percentage / 100.0
            
            # Weighted combination
            gnpi_score = (
                (persistence_score * 0.40) +
                (appearance_score * 0.30) +
                (reliability_score * 0.20) +
                (uptime_score * 0.10)
            )
            
            return round(gnpi_score, 4)
        except Exception as e:
            logger.error(f"Error calculating GNPI score: {e}")
            return 0.5  # Return neutral score on error
    
    def record_guard_observation(
        self,
        guard_fingerprint: str,
        case_id: str,
        country: str = "UNKNOWN",
        asn: int = 0,
        uptime_percentage: float = 100.0
    ) -> GuardNodeReputation:
        """
        Record observation of a guard node in an investigation.
        
        Updates or creates guard node reputation entry.
        """
        try:
            collection = self.db["guard_node_reputation"]
            
            # Try to find existing guard
            existing = collection.find_one({"guard_fingerprint": guard_fingerprint})
            
            now = datetime.utcnow()
            
            if existing:
                # Update existing guard
                guard_rep = GuardNodeReputation.from_dict(existing)
                guard_rep.last_seen = now
                guard_rep.appearance_count += 1
                guard_rep.country = country if country != "UNKNOWN" else guard_rep.country
                guard_rep.asn = asn if asn > 0 else guard_rep.asn
                
                # Update average uptime
                total_seen = guard_rep.appearance_count
                prev_uptime_sum = guard_rep.average_uptime_percentage * (total_seen - 1)
                guard_rep.average_uptime_percentage = (prev_uptime_sum + uptime_percentage) / total_seen
            else:
                # Create new guard reputation
                guard_rep = GuardNodeReputation(
                    guard_fingerprint=guard_fingerprint,
                    first_seen=now,
                    last_seen=now,
                    appearance_count=1,
                    reliability_score=0.5,  # Start neutral
                    persistence_level="LOW",
                    country=country,
                    asn=asn,
                    average_uptime_percentage=uptime_percentage
                )
            
            # Recalculate persistence and GNPI
            guard_rep.persistence_level = self.calculate_persistence_level(guard_rep)
            guard_rep.gnpi_score = self.calculate_gnpi_score(guard_rep)
            guard_rep.last_updated = now
            
            # Store in MongoDB
            collection.update_one(
                {"guard_fingerprint": guard_fingerprint},
                {"$set": guard_rep.to_dict()},
                upsert=True
            )
            
            logger.info(f"Guard {guard_fingerprint[:16]}... updated: "
                       f"GNPI={guard_rep.gnpi_score:.3f}, "
                       f"Level={guard_rep.persistence_level}")
            
            return guard_rep
        except PyMongoError as e:
            logger.error(f"Error recording guard observation: {e}")
            raise
    
    def record_correlation_outcome(
        self,
        guard_fingerprint: str,
        successful: bool,
        confidence_score: float = 0.5
    ) -> bool:
        """
        Record correlation outcome for a guard node.
        
        Updates reliability score based on actual correlation success.
        """
        try:
            collection = self.db["guard_node_reputation"]
            
            existing = collection.find_one({"guard_fingerprint": guard_fingerprint})
            if not existing:
                logger.warning(f"Guard {guard_fingerprint} not found in GNPI system")
                return False
            
            guard_rep = GuardNodeReputation.from_dict(existing)
            
            if successful:
                guard_rep.successful_correlations += 1
            else:
                guard_rep.failed_correlations += 1
            
            # Update reliability score
            total = guard_rep.successful_correlations + guard_rep.failed_correlations
            guard_rep.reliability_score = guard_rep.successful_correlations / total
            
            # Recalculate GNPI
            guard_rep.gnpi_score = self.calculate_gnpi_score(guard_rep)
            guard_rep.last_updated = datetime.utcnow()
            
            # Update MongoDB
            collection.update_one(
                {"guard_fingerprint": guard_fingerprint},
                {"$set": guard_rep.to_dict()}
            )
            
            return True
        except PyMongoError as e:
            logger.error(f"Error recording correlation outcome: {e}")
            return False
    
    def get_guard_reputation(self, guard_fingerprint: str) -> Optional[GuardNodeReputation]:
        """Retrieve reputation for a specific guard."""
        try:
            collection = self.db["guard_node_reputation"]
            doc = collection.find_one({"guard_fingerprint": guard_fingerprint})
            
            if doc:
                return GuardNodeReputation.from_dict(doc)
            return None
        except PyMongoError as e:
            logger.error(f"Error retrieving guard reputation: {e}")
            return None
    
    def get_top_guards_by_gnpi(
        self,
        limit: int = 10,
        min_gnpi: float = 0.0
    ) -> List[GuardNodeReputation]:
        """
        Get top guard nodes by GNPI score.
        
        Useful for identifying most trusted/persistent guards.
        """
        try:
            collection = self.db["guard_node_reputation"]
            docs = collection.find(
                {"gnpi_score": {"$gte": min_gnpi}}
            ).sort("gnpi_score", DESCENDING).limit(limit)
            
            return [GuardNodeReputation.from_dict(doc) for doc in docs]
        except PyMongoError as e:
            logger.error(f"Error getting top guards: {e}")
            return []
    
    def get_guards_by_persistence(self, level: str) -> List[GuardNodeReputation]:
        """Get all guards at a specific persistence level."""
        try:
            collection = self.db["guard_node_reputation"]
            docs = collection.find(
                {"persistence_level": level}
            ).sort("gnpi_score", DESCENDING)
            
            return [GuardNodeReputation.from_dict(doc) for doc in docs]
        except PyMongoError as e:
            logger.error(f"Error getting guards by persistence: {e}")
            return []
    
    def get_suspicious_guards(self) -> List[GuardNodeReputation]:
        """
        Get suspicious guards (low GNPI, high failure rate).
        
        Returns guards that frequently appear but have poor correlations.
        """
        try:
            collection = self.db["guard_node_reputation"]
            
            # High appearance count but low GNPI = suspicious
            docs = collection.find({
                "appearance_count": {"$gte": 3},
                "gnpi_score": {"$lt": 0.3},
                "reliability_score": {"$lt": 0.4}
            }).sort("reliability_score", ASCENDING)
            
            return [GuardNodeReputation.from_dict(doc) for doc in docs]
        except PyMongoError as e:
            logger.error(f"Error getting suspicious guards: {e}")
            return []
    
    def get_critical_guards(self) -> List[GuardNodeReputation]:
        """Get highly trusted guards (CRITICAL persistence, high GNPI)."""
        try:
            collection = self.db["guard_node_reputation"]
            docs = collection.find({
                "persistence_level": "CRITICAL",
                "gnpi_score": {"$gte": 0.8}
            }).sort("gnpi_score", DESCENDING)
            
            return [GuardNodeReputation.from_dict(doc) for doc in docs]
        except PyMongoError as e:
            logger.error(f"Error getting critical guards: {e}")
            return []
    
    def get_gnpi_statistics(self, days: int = 30) -> Dict:
        """
        Get overall GNPI system statistics.
        
        Returns aggregate metrics about guard reputation distribution.
        """
        try:
            collection = self.db["guard_node_reputation"]
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all recent guards
            all_guards = list(collection.find({
                "last_seen": {"$gte": cutoff_date}
            }))
            
            if not all_guards:
                return {
                    "total_guards": 0,
                    "average_gnpi": 0.0,
                    "by_persistence": {},
                    "reliability_distribution": {}
                }
            
            # Calculate statistics
            gnpi_scores = [g.get("gnpi_score", 0.0) for g in all_guards]
            persistence_levels = {}
            reliability_bins = {
                "0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0,
                "0.6-0.8": 0, "0.8-1.0": 0
            }
            
            for guard in all_guards:
                level = guard.get("persistence_level", "UNKNOWN")
                persistence_levels[level] = persistence_levels.get(level, 0) + 1
                
                reliability = guard.get("reliability_score", 0.5)
                if reliability < 0.2:
                    reliability_bins["0.0-0.2"] += 1
                elif reliability < 0.4:
                    reliability_bins["0.2-0.4"] += 1
                elif reliability < 0.6:
                    reliability_bins["0.4-0.6"] += 1
                elif reliability < 0.8:
                    reliability_bins["0.6-0.8"] += 1
                else:
                    reliability_bins["0.8-1.0"] += 1
            
            return {
                "total_guards": len(all_guards),
                "average_gnpi": round(sum(gnpi_scores) / len(gnpi_scores), 4),
                "gnpi_range": {
                    "min": round(min(gnpi_scores), 4),
                    "max": round(max(gnpi_scores), 4)
                },
                "by_persistence": persistence_levels,
                "reliability_distribution": reliability_bins,
                "period_days": days,
                "timestamp": datetime.utcnow().isoformat()
            }
        except PyMongoError as e:
            logger.error(f"Error getting GNPI statistics: {e}")
            return {}


# Singleton instance
_gnpi_instance: Optional[GNPISystem] = None


def get_gnpi_system(db=None) -> GNPISystem:
    """Get or create GNPI system instance."""
    global _gnpi_instance
    if _gnpi_instance is None or db is not None:
        _gnpi_instance = GNPISystem(db)
    return _gnpi_instance


def init_gnpi_system(db) -> GNPISystem:
    """Initialize GNPI system with database connection."""
    global _gnpi_instance
    _gnpi_instance = GNPISystem(db)
    return _gnpi_instance
