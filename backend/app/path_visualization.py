"""
Path Visualization System

Provides data structures and methods for:
1. Timeline-driven onion peel visualization (TOR path evolution)
2. Probabilistic origin zone mapping (geographic likelihood)

This module generates visualization-friendly data structures for D3.js
and map-based visualizations.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import hashlib
from pymongo.database import Database
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & TYPES
# ============================================================================

class PathLayer(Enum):
    """TOR path layers for onion peel visualization."""
    CLIENT = "client"
    GUARD = "guard"
    MIDDLE = "middle"
    EXIT = "exit"
    DESTINATION = "destination"


class NodeTransitionType(Enum):
    """Types of node transitions in path evolution."""
    INITIAL = "initial"              # First appearance
    STABLE = "stable"                # No change
    REPLACED = "replaced"            # Node changed
    FAILED = "failed"                # Connection failed
    RECOVERED = "recovered"          # Restored after failure


# ============================================================================
# DATA CLASSES - PATH EVOLUTION
# ============================================================================

@dataclass
class PathNode:
    """Represents a single node in TOR path."""
    fingerprint: str
    nickname: Optional[str] = None
    ip_address: Optional[str] = None
    country: Optional[str] = None
    asn: Optional[str] = None
    flags: List[str] = field(default_factory=list)  # guard, exit, fast, stable, etc.
    uptime_percentage: float = 100.0
    bandwidth_mbps: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class PathSnapshot:
    """Represents complete path at a specific point in time."""
    timestamp: datetime
    session_id: str
    client_node: Optional[PathNode] = None
    guard_node: Optional[PathNode] = None
    middle_node: Optional[PathNode] = None
    exit_node: Optional[PathNode] = None
    destination_node: Optional[PathNode] = None
    
    # Metadata
    rtt_milliseconds: Optional[float] = None  # Round trip time
    packet_count: int = 0
    bytes_transferred: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "client": self.client_node.to_dict() if self.client_node else None,
            "guard": self.guard_node.to_dict() if self.guard_node else None,
            "middle": self.middle_node.to_dict() if self.middle_node else None,
            "exit": self.exit_node.to_dict() if self.exit_node else None,
            "destination": self.destination_node.to_dict() if self.destination_node else None,
            "rtt_ms": self.rtt_milliseconds,
            "packet_count": self.packet_count,
            "bytes": self.bytes_transferred
        }


@dataclass
class NodeTransition:
    """Represents a change in a path layer."""
    layer: PathLayer
    timestamp: datetime
    transition_type: NodeTransitionType
    old_node: Optional[PathNode] = None
    new_node: Optional[PathNode] = None
    confidence_score: float = 1.0
    reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "layer": self.layer.value,
            "timestamp": self.timestamp.isoformat(),
            "type": self.transition_type.value,
            "old_node": self.old_node.to_dict() if self.old_node else None,
            "new_node": self.new_node.to_dict() if self.new_node else None,
            "confidence": self.confidence_score,
            "reason": self.reason
        }


@dataclass
class PathEvolution:
    """Complete path evolution timeline."""
    case_id: str
    session_id: str
    start_time: datetime
    end_time: datetime
    
    snapshots: List[PathSnapshot] = field(default_factory=list)
    transitions: List[NodeTransition] = field(default_factory=list)
    
    # Aggregate statistics
    total_duration_seconds: float = 0.0
    guard_changes: int = 0
    exit_changes: int = 0
    middle_changes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "case_id": self.case_id,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.total_duration_seconds,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "transitions": [t.to_dict() for t in self.transitions],
            "guard_changes": self.guard_changes,
            "exit_changes": self.exit_changes,
            "middle_changes": self.middle_changes,
            "snapshot_count": len(self.snapshots),
            "transition_count": len(self.transitions)
        }


# ============================================================================
# DATA CLASSES - PROBABILISTIC MAPPING
# ============================================================================

@dataclass
class ASNCluster:
    """Aggregate data for an ASN cluster."""
    asn: str
    asn_name: str
    country: str
    
    guard_node_count: int = 0
    total_confidence: float = 0.0
    avg_confidence: float = 0.0
    
    # Geographic bounds
    lat_min: float = 0.0
    lat_max: float = 0.0
    lon_min: float = 0.0
    lon_max: float = 0.0
    
    # Center point for visualization
    center_lat: float = 0.0
    center_lon: float = 0.0
    
    # Probabilistic data
    probability_weight: float = 0.0  # 0.0-1.0
    color_intensity: float = 0.0      # 0.0-1.0 for heatmap
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ISPLikelihoodZone:
    """Aggregate data for an ISP likelihood zone."""
    isp_name: str
    country: str
    primary_asns: List[str] = field(default_factory=list)
    
    associated_guards: int = 0
    total_confidence: float = 0.0
    avg_confidence: float = 0.0
    
    # Geographic representation
    lat: float = 0.0
    lon: float = 0.0
    radius_km: float = 100.0
    
    # Probabilistic weight
    probability_weight: float = 0.0
    heatmap_intensity: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ProbabilityZone:
    """Geographic zone with probability of origin."""
    zone_id: str
    zone_name: str
    zone_type: str  # "asn", "isp", "country", "region"
    
    # Geographic data
    latitude: float
    longitude: float
    radius_km: float = 50.0
    
    # Confidence/probability
    confidence_score: float = 0.0  # 0.0-1.0
    probability: float = 0.0        # 0.0-1.0
    
    # For heatmap rendering
    color_hex: str = "#FF0000"
    opacity: float = 0.5
    
    # Associated data
    guard_count: int = 0
    sources: List[str] = field(default_factory=list)  # ["guard1", "guard2", ...]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "type": self.zone_type,
            "lat": self.latitude,
            "lon": self.longitude,
            "radius_km": self.radius_km,
            "confidence": self.confidence_score,
            "probability": self.probability,
            "color": self.color_hex,
            "opacity": self.opacity,
            "guard_count": self.guard_count,
            "sources": self.sources
        }


@dataclass
class ProbabilityMap:
    """Complete probabilistic origin map."""
    case_id: str
    generated_at: datetime
    
    zones: List[ProbabilityZone] = field(default_factory=list)
    asn_clusters: List[ASNCluster] = field(default_factory=list)
    isp_zones: List[ISPLikelihoodZone] = field(default_factory=list)
    
    # Overall statistics
    total_probability: float = 0.0
    most_likely_country: Optional[str] = None
    confidence_level: str = "LOW"  # LOW, MEDIUM, HIGH
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "case_id": self.case_id,
            "generated_at": self.generated_at.isoformat(),
            "zones": [z.to_dict() for z in self.zones],
            "asn_clusters": [c.to_dict() for c in self.asn_clusters],
            "isp_zones": [iz.to_dict() for iz in self.isp_zones],
            "total_probability": self.total_probability,
            "most_likely_country": self.most_likely_country,
            "confidence_level": self.confidence_level,
            "zone_count": len(self.zones)
        }


# ============================================================================
# PATH VISUALIZATION SYSTEM
# ============================================================================

class PathVisualizationSystem:
    """
    Generates visualization data for TOR path evolution and probabilistic mapping.
    """
    
    _instance = None
    
    def __init__(self, db: Optional[Database] = None):
        self.db = db
        if db is not None:
            self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create necessary MongoDB indexes."""
        if self.db is None:
            return
        
        # Path evolution indexes
        self.db.path_evolution.create_index([("case_id", 1), ("session_id", 1)], unique=True)
        self.db.path_evolution.create_index([("start_time", 1)])
        self.db.path_evolution.create_index([("case_id", 1)])
        
        # Probability map indexes
        self.db.probability_maps.create_index([("case_id", 1)], unique=True)
        self.db.probability_maps.create_index([("generated_at", 1)])
        
        logger.info("Path visualization indexes created")
    
    def generate_path_evolution(
        self,
        case_id: str,
        session_id: str,
        snapshots: List[PathSnapshot]
    ) -> PathEvolution:
        """
        Generate path evolution from snapshots.
        
        Args:
            case_id: Investigation case ID
            session_id: TOR session ID
            snapshots: List of path snapshots over time
        
        Returns:
            PathEvolution object with timeline and transitions
        """
        if not snapshots:
            raise ValueError("At least one snapshot required")
        
        # Sort by timestamp
        snapshots_sorted = sorted(snapshots, key=lambda s: s.timestamp)
        start_time = snapshots_sorted[0].timestamp
        end_time = snapshots_sorted[-1].timestamp
        duration = (end_time - start_time).total_seconds()
        
        # Detect transitions
        transitions = self._detect_transitions(snapshots_sorted)
        
        # Count changes
        guard_changes = sum(1 for t in transitions if t.layer == PathLayer.GUARD)
        exit_changes = sum(1 for t in transitions if t.layer == PathLayer.EXIT)
        middle_changes = sum(1 for t in transitions if t.layer == PathLayer.MIDDLE)
        
        path_evolution = PathEvolution(
            case_id=case_id,
            session_id=session_id,
            start_time=start_time,
            end_time=end_time,
            snapshots=snapshots_sorted,
            transitions=transitions,
            total_duration_seconds=duration,
            guard_changes=guard_changes,
            exit_changes=exit_changes,
            middle_changes=middle_changes
        )
        
        # Store in MongoDB
        self._store_path_evolution(path_evolution)
        
        return path_evolution
    
    def _detect_transitions(self, snapshots: List[PathSnapshot]) -> List[NodeTransition]:
        """Detect node transitions between snapshots."""
        transitions = []
        
        if not snapshots:
            return transitions
        
        # Check each layer for changes
        for i in range(1, len(snapshots)):
            prev = snapshots[i - 1]
            curr = snapshots[i]
            
            # Check guard node
            if prev.guard_node != curr.guard_node:
                transitions.append(NodeTransition(
                    layer=PathLayer.GUARD,
                    timestamp=curr.timestamp,
                    transition_type=NodeTransitionType.REPLACED if prev.guard_node else NodeTransitionType.INITIAL,
                    old_node=prev.guard_node,
                    new_node=curr.guard_node,
                    confidence_score=0.9
                ))
            
            # Check exit node
            if prev.exit_node != curr.exit_node:
                transitions.append(NodeTransition(
                    layer=PathLayer.EXIT,
                    timestamp=curr.timestamp,
                    transition_type=NodeTransitionType.REPLACED if prev.exit_node else NodeTransitionType.INITIAL,
                    old_node=prev.exit_node,
                    new_node=curr.exit_node,
                    confidence_score=0.9
                ))
            
            # Check middle node
            if prev.middle_node != curr.middle_node:
                transitions.append(NodeTransition(
                    layer=PathLayer.MIDDLE,
                    timestamp=curr.timestamp,
                    transition_type=NodeTransitionType.REPLACED if prev.middle_node else NodeTransitionType.INITIAL,
                    old_node=prev.middle_node,
                    new_node=curr.middle_node,
                    confidence_score=0.9
                ))
        
        return transitions
    
    def _store_path_evolution(self, evolution: PathEvolution):
        """Store path evolution in MongoDB."""
        if self.db is None:
            return
        
        try:
            self.db.path_evolution.update_one(
                {"case_id": evolution.case_id, "session_id": evolution.session_id},
                {"$set": evolution.to_dict()},
                upsert=True
            )
            logger.info(f"Stored path evolution for {evolution.case_id}/{evolution.session_id}")
        except Exception as e:
            logger.error(f"Failed to store path evolution: {e}")
    
    def get_path_evolution(
        self,
        case_id: str,
        session_id: Optional[str] = None
    ) -> Optional[PathEvolution]:
        """
        Retrieve stored path evolution.
        
        Args:
            case_id: Investigation case ID
            session_id: Optional session ID for specific session
        
        Returns:
            PathEvolution object or None if not found
        """
        if self.db is None:
            return None
        
        try:
            query = {"case_id": case_id}
            if session_id:
                query["session_id"] = session_id
            
            data = self.db.path_evolution.find_one(query)
            if not data:
                return None
            
            # Reconstruct object (simplified for now)
            return data
        except Exception as e:
            logger.error(f"Failed to retrieve path evolution: {e}")
            return None
    
    def generate_probability_map(
        self,
        case_id: str,
        guard_data: Dict[str, Dict[str, Any]]
    ) -> ProbabilityMap:
        """
        Generate probabilistic origin map from guard data.
        
        Args:
            case_id: Investigation case ID
            guard_data: Dict of guard fingerprint -> guard info
                {
                    "fp1": {"country": "US", "asn": "AS1234", "confidence": 0.9},
                    ...
                }
        
        Returns:
            ProbabilityMap with zones and clusters
        """
        prob_map = ProbabilityMap(
            case_id=case_id,
            generated_at=datetime.utcnow()
        )
        
        # Aggregate by country
        country_data = {}
        for fp, data in guard_data.items():
            country = data.get("country", "UNKNOWN")
            confidence = data.get("confidence", 0.5)
            
            if country not in country_data:
                country_data[country] = {
                    "count": 0,
                    "total_confidence": 0.0,
                    "fps": []
                }
            
            country_data[country]["count"] += 1
            country_data[country]["total_confidence"] += confidence
            country_data[country]["fps"].append(fp)
        
        # Create zones from country data
        zone_id_counter = 0
        for country, cdata in country_data.items():
            avg_confidence = cdata["total_confidence"] / cdata["count"]
            
            # Create zone
            zone = ProbabilityZone(
                zone_id=f"zone_{zone_id_counter}",
                zone_name=f"{country} ({cdata['count']} guards)",
                zone_type="country",
                latitude=self._get_country_center_lat(country),
                longitude=self._get_country_center_lon(country),
                radius_km=500.0,
                confidence_score=avg_confidence,
                probability=avg_confidence,
                color_hex=self._confidence_to_color(avg_confidence),
                opacity=0.3 + (avg_confidence * 0.4),
                guard_count=cdata["count"],
                sources=cdata["fps"]
            )
            
            prob_map.zones.append(zone)
            zone_id_counter += 1
        
        # Normalize probabilities
        total_prob = sum(z.probability for z in prob_map.zones)
        if total_prob > 0:
            for zone in prob_map.zones:
                zone.probability = zone.probability / total_prob
        
        prob_map.total_probability = sum(z.probability for z in prob_map.zones)
        
        # Determine confidence level
        max_prob = max((z.probability for z in prob_map.zones), default=0.0)
        if max_prob > 0.7:
            prob_map.confidence_level = "HIGH"
        elif max_prob > 0.4:
            prob_map.confidence_level = "MEDIUM"
        else:
            prob_map.confidence_level = "LOW"
        
        # Store in MongoDB
        self._store_probability_map(prob_map)
        
        return prob_map
    
    def _confidence_to_color(self, confidence: float) -> str:
        """
        Convert confidence score to heatmap color (red for high confidence).
        
        Args:
            confidence: Confidence score 0.0-1.0
        
        Returns:
            Hex color string
        """
        # Red (#FF0000) for high, yellow (#FFFF00) for medium, green (#00FF00) for low
        if confidence > 0.7:
            # Red shades
            r = int(255)
            g = int(255 * (1 - confidence))
            b = 0
        elif confidence > 0.4:
            # Yellow shades
            r = int(255)
            g = int(255)
            b = 0
        else:
            # Green shades
            r = 0
            g = int(255 * confidence)
            b = 0
        
        return f"#{r:02X}{g:02X}{b:02X}"
    
    def _get_country_center_lat(self, country_code: str) -> float:
        """Get approximate center latitude for country."""
        # Simplified country center mapping
        centers = {
            "US": 39.8283,
            "GB": 55.3781,
            "DE": 51.1657,
            "FR": 46.2276,
            "CN": 35.8617,
            "IN": 20.5937,
            "JP": 36.2048,
            "RU": 61.5240,
            "AU": -25.2744,
            "CA": 56.1304,
        }
        return centers.get(country_code, 0.0)
    
    def _get_country_center_lon(self, country_code: str) -> float:
        """Get approximate center longitude for country."""
        centers = {
            "US": -95.7129,
            "GB": -3.4360,
            "DE": 10.4515,
            "FR": 2.2137,
            "CN": 104.1954,
            "IN": 78.9629,
            "JP": 138.2529,
            "RU": 105.3188,
            "AU": 133.7751,
            "CA": -106.3468,
        }
        return centers.get(country_code, 0.0)
    
    def _store_probability_map(self, prob_map: ProbabilityMap):
        """Store probability map in MongoDB."""
        if self.db is None:
            return
        
        try:
            self.db.probability_maps.update_one(
                {"case_id": prob_map.case_id},
                {"$set": prob_map.to_dict()},
                upsert=True
            )
            logger.info(f"Stored probability map for {prob_map.case_id}")
        except Exception as e:
            logger.error(f"Failed to store probability map: {e}")
    
    def get_probability_map(self, case_id: str) -> Optional[ProbabilityMap]:
        """
        Retrieve stored probability map.
        
        Args:
            case_id: Investigation case ID
        
        Returns:
            ProbabilityMap object or None
        """
        if self.db is None:
            return None
        
        try:
            data = self.db.probability_maps.find_one({"case_id": case_id})
            return data if data else None
        except Exception as e:
            logger.error(f"Failed to retrieve probability map: {e}")
            return None


def get_path_visualization_system(db: Optional[Database] = None) -> PathVisualizationSystem:
    """
    Get singleton instance of PathVisualizationSystem.
    
    Args:
        db: MongoDB database connection
    
    Returns:
        PathVisualizationSystem singleton
    """
    if PathVisualizationSystem._instance is None or db is not None:
        PathVisualizationSystem._instance = PathVisualizationSystem(db)
    return PathVisualizationSystem._instance
