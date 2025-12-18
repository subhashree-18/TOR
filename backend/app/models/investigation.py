# backend/app/models/investigation.py
"""
MongoDB Schema for Investigation Persistence

This module defines the data models and repository classes for persisting
TOR investigation history across sessions. It supports:

1. Observed exit nodes with metadata
2. Evolving entry-node probabilities with history tracking
3. Confidence timelines for analysis progression
4. Supporting evidence snapshots from each analysis
5. PCAP file references and forensic data links
6. Incremental Bayesian updates that refine previous estimates

Design Principles:
- Immutable history: Previous probability estimates are preserved
- Incremental updates: New analyses refine existing probabilities
- Audit trail: Full traceability of how conclusions evolved
- Evidence linking: Connect all supporting data to conclusions
"""

from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field, asdict
import os
import logging
import uuid

# Optional MongoDB imports - allows models to be used without MongoDB installed
try:
    from pymongo import MongoClient, ASCENDING, DESCENDING
    from pymongo.collection import Collection
    from pymongo.database import Database
    from bson import ObjectId
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    MongoClient = None
    ASCENDING = 1
    DESCENDING = -1
    Collection = None
    Database = None
    
    class ObjectId:
        """Mock ObjectId for testing without MongoDB"""
        def __init__(self, oid=None):
            self._id = oid or "507f1f77bcf86cd799439011"
        def __str__(self):
            return str(self._id)

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class InvestigationStatus(str, Enum):
    """Status of an investigation"""
    ACTIVE = "active"           # Ongoing investigation
    PAUSED = "paused"           # Temporarily paused
    COMPLETED = "completed"     # Investigation concluded
    ARCHIVED = "archived"       # Historical record


class EvidenceType(str, Enum):
    """Types of evidence in an investigation"""
    TEMPORAL = "temporal"           # Time-based correlation
    TRAFFIC = "traffic"             # Traffic pattern analysis
    GEOGRAPHIC = "geographic"       # GeoIP correlation
    BEHAVIORAL = "behavioral"       # Exit node behavior patterns
    PCAP_FLOW = "pcap_flow"        # PCAP flow analysis
    FORENSIC = "forensic"          # Forensic artifact analysis
    CONSENSUS = "consensus"        # TOR consensus data


class ConfidenceLevel(str, Enum):
    """Qualitative confidence levels"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


# ============================================================================
# DATA STRUCTURES - Subdocuments
# ============================================================================

@dataclass
class ExitNodeObservation:
    """
    Record of an observed exit node during investigation.
    
    Each exit node observation captures when and how an exit relay
    was identified as potentially part of the traffic path.
    """
    fingerprint: str
    nickname: str
    observed_at: datetime
    ip_address: str
    country_code: str
    
    # Evidence that led to this observation
    source: str  # "pcap", "netflow", "manual", "consensus"
    
    # Optional metadata
    observed_bandwidth: Optional[int] = None
    consensus_weight: Optional[float] = None
    flags: List[str] = field(default_factory=list)
    
    # Link to PCAP if observed from traffic capture
    pcap_reference_id: Optional[str] = None
    
    # Flow metadata if from PCAP analysis
    flow_metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        d = asdict(self)
        # Ensure datetime is timezone-aware
        if self.observed_at and self.observed_at.tzinfo is None:
            d["observed_at"] = self.observed_at.replace(tzinfo=timezone.utc)
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExitNodeObservation:
        """Create from MongoDB document"""
        return cls(
            fingerprint=data["fingerprint"],
            nickname=data["nickname"],
            observed_at=data["observed_at"],
            ip_address=data["ip_address"],
            country_code=data["country_code"],
            source=data["source"],
            observed_bandwidth=data.get("observed_bandwidth"),
            consensus_weight=data.get("consensus_weight"),
            flags=data.get("flags", []),
            pcap_reference_id=data.get("pcap_reference_id"),
            flow_metadata=data.get("flow_metadata"),
        )


@dataclass
class ProbabilityHistoryEntry:
    """
    Historical record of a probability estimate at a point in time.
    
    Preserves the evolution of probability estimates as new evidence arrives.
    """
    timestamp: datetime
    prior_probability: float
    posterior_probability: float
    likelihood: float
    
    # What triggered this update
    update_reason: str  # "new_evidence", "batch_update", "recalibration"
    
    # Evidence that influenced this update
    evidence_summary: Dict[str, float]  # {"time_overlap": 0.8, "traffic": 0.7, ...}
    
    # Number of observations at this point
    observation_count: int
    
    # Exit nodes observed at time of update
    exit_nodes_at_update: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        d = asdict(self)
        if self.timestamp and self.timestamp.tzinfo is None:
            d["timestamp"] = self.timestamp.replace(tzinfo=timezone.utc)
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ProbabilityHistoryEntry:
        """Create from MongoDB document"""
        return cls(
            timestamp=data["timestamp"],
            prior_probability=data["prior_probability"],
            posterior_probability=data["posterior_probability"],
            likelihood=data["likelihood"],
            update_reason=data["update_reason"],
            evidence_summary=data["evidence_summary"],
            observation_count=data["observation_count"],
            exit_nodes_at_update=data.get("exit_nodes_at_update", []),
        )


@dataclass
class EntryNodeProbability:
    """
    Probability estimate for a potential entry node.
    
    Tracks the current probability and full history of how
    the estimate evolved over time.
    """
    fingerprint: str
    nickname: str
    
    # Current probability estimate
    current_prior: float
    current_posterior: float
    
    # Latest update timestamp
    last_updated: datetime
    
    # Total number of evidence updates
    update_count: int
    
    # Full history of probability evolution
    history: List[ProbabilityHistoryEntry] = field(default_factory=list)
    
    # Average evidence scores (running averages)
    avg_time_overlap: float = 0.0
    avg_traffic_similarity: float = 0.0
    avg_stability: float = 0.0
    avg_pcap_evidence: float = 0.0
    
    # Exit nodes observed with this entry
    associated_exit_nodes: List[str] = field(default_factory=list)
    
    # Confidence in this estimate
    confidence_level: ConfidenceLevel = ConfidenceLevel.VERY_LOW
    
    # Relay metadata for reference
    relay_metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        result = {
            "fingerprint": self.fingerprint,
            "nickname": self.nickname,
            "current_prior": self.current_prior,
            "current_posterior": self.current_posterior,
            "last_updated": self.last_updated if self.last_updated.tzinfo else self.last_updated.replace(tzinfo=timezone.utc),
            "update_count": self.update_count,
            "history": [h.to_dict() for h in self.history],
            "avg_time_overlap": self.avg_time_overlap,
            "avg_traffic_similarity": self.avg_traffic_similarity,
            "avg_stability": self.avg_stability,
            "avg_pcap_evidence": self.avg_pcap_evidence,
            "associated_exit_nodes": self.associated_exit_nodes,
            "confidence_level": self.confidence_level.value,
            "relay_metadata": self.relay_metadata,
        }
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EntryNodeProbability:
        """Create from MongoDB document"""
        return cls(
            fingerprint=data["fingerprint"],
            nickname=data["nickname"],
            current_prior=data["current_prior"],
            current_posterior=data["current_posterior"],
            last_updated=data["last_updated"],
            update_count=data["update_count"],
            history=[ProbabilityHistoryEntry.from_dict(h) for h in data.get("history", [])],
            avg_time_overlap=data.get("avg_time_overlap", 0.0),
            avg_traffic_similarity=data.get("avg_traffic_similarity", 0.0),
            avg_stability=data.get("avg_stability", 0.0),
            avg_pcap_evidence=data.get("avg_pcap_evidence", 0.0),
            associated_exit_nodes=data.get("associated_exit_nodes", []),
            confidence_level=ConfidenceLevel(data.get("confidence_level", "very_low")),
            relay_metadata=data.get("relay_metadata"),
        )


@dataclass
class ConfidenceTimelineEntry:
    """
    Snapshot of overall investigation confidence at a point in time.
    
    Tracks how confident we are in the investigation conclusions
    as evidence accumulates.
    """
    timestamp: datetime
    
    # Overall confidence value (0.0-1.0)
    confidence_value: float
    
    # Qualitative level
    confidence_level: ConfidenceLevel
    
    # Components contributing to confidence
    components: Dict[str, float]  # {"evidence_quality": 0.8, "consistency": 0.7, ...}
    
    # What triggered this entry
    trigger: str  # "analysis_run", "evidence_added", "manual_review"
    
    # Top entry candidates at this point
    top_entry_candidates: List[Dict[str, float]] = field(default_factory=list)  # [{"fp": ..., "prob": ...}]
    
    # Number of evidence items at this point
    total_evidence_count: int = 0
    
    # Note for context
    note: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        d = asdict(self)
        if self.timestamp and self.timestamp.tzinfo is None:
            d["timestamp"] = self.timestamp.replace(tzinfo=timezone.utc)
        d["confidence_level"] = self.confidence_level.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConfidenceTimelineEntry:
        """Create from MongoDB document"""
        return cls(
            timestamp=data["timestamp"],
            confidence_value=data["confidence_value"],
            confidence_level=ConfidenceLevel(data["confidence_level"]),
            components=data["components"],
            trigger=data["trigger"],
            top_entry_candidates=data.get("top_entry_candidates", []),
            total_evidence_count=data.get("total_evidence_count", 0),
            note=data.get("note"),
        )


@dataclass
class EvidenceSnapshot:
    """
    Snapshot of evidence collected during an analysis run.
    
    Captures all evidence types and their scores from a single
    analysis session for audit and refinement purposes.
    """
    snapshot_id: str
    captured_at: datetime
    
    # Evidence type and source
    evidence_type: EvidenceType
    source_description: str
    
    # Evidence scores and metrics
    scores: Dict[str, float]  # Flexible score storage
    
    # Raw data reference (not the data itself)
    raw_data_reference: Optional[str] = None
    
    # Entry node this evidence relates to
    related_entry_fingerprint: Optional[str] = None
    
    # Exit node this evidence relates to
    related_exit_fingerprint: Optional[str] = None
    
    # PCAP reference if applicable
    pcap_reference_id: Optional[str] = None
    
    # Analysis metadata
    analysis_metadata: Optional[Dict[str, Any]] = None
    
    # Weight applied to this evidence in overall score
    weight_applied: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        d = asdict(self)
        if self.captured_at and self.captured_at.tzinfo is None:
            d["captured_at"] = self.captured_at.replace(tzinfo=timezone.utc)
        d["evidence_type"] = self.evidence_type.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceSnapshot:
        """Create from MongoDB document"""
        return cls(
            snapshot_id=data["snapshot_id"],
            captured_at=data["captured_at"],
            evidence_type=EvidenceType(data["evidence_type"]),
            source_description=data["source_description"],
            scores=data["scores"],
            raw_data_reference=data.get("raw_data_reference"),
            related_entry_fingerprint=data.get("related_entry_fingerprint"),
            related_exit_fingerprint=data.get("related_exit_fingerprint"),
            pcap_reference_id=data.get("pcap_reference_id"),
            analysis_metadata=data.get("analysis_metadata"),
            weight_applied=data.get("weight_applied", 1.0),
        )


@dataclass
class PCAPReference:
    """
    Reference to a PCAP file and its analysis results.
    
    Does not store the PCAP itself, but metadata and analysis
    results for linking evidence back to source data.
    """
    reference_id: str
    
    # File information
    original_filename: str
    file_hash_sha256: str
    file_size_bytes: int
    upload_timestamp: datetime
    
    # Storage location (GridFS ID or path)
    storage_location: str
    storage_type: str  # "gridfs", "filesystem", "s3"
    
    # Analysis results summary
    analysis_timestamp: Optional[datetime] = None
    total_packets: int = 0
    total_flows: int = 0
    tor_related_flows: int = 0
    
    # Flow statistics
    flow_summary: Optional[Dict[str, Any]] = None
    
    # Exit nodes identified in this PCAP
    identified_exit_nodes: List[str] = field(default_factory=list)
    
    # Analysis mode used
    analysis_mode: str = "offline"  # "offline" or "realtime"
    
    # Forensic evidence extracted
    forensic_evidence: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        d = asdict(self)
        if self.upload_timestamp and self.upload_timestamp.tzinfo is None:
            d["upload_timestamp"] = self.upload_timestamp.replace(tzinfo=timezone.utc)
        if self.analysis_timestamp and self.analysis_timestamp.tzinfo is None:
            d["analysis_timestamp"] = self.analysis_timestamp.replace(tzinfo=timezone.utc)
        return d
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> PCAPReference:
        """Create from MongoDB document"""
        return cls(
            reference_id=data["reference_id"],
            original_filename=data["original_filename"],
            file_hash_sha256=data["file_hash_sha256"],
            file_size_bytes=data["file_size_bytes"],
            upload_timestamp=data["upload_timestamp"],
            storage_location=data["storage_location"],
            storage_type=data["storage_type"],
            analysis_timestamp=data.get("analysis_timestamp"),
            total_packets=data.get("total_packets", 0),
            total_flows=data.get("total_flows", 0),
            tor_related_flows=data.get("tor_related_flows", 0),
            flow_summary=data.get("flow_summary"),
            identified_exit_nodes=data.get("identified_exit_nodes", []),
            analysis_mode=data.get("analysis_mode", "offline"),
            forensic_evidence=data.get("forensic_evidence"),
        )


# ============================================================================
# MAIN DOCUMENT - Investigation
# ============================================================================

@dataclass
class Investigation:
    """
    Main investigation document stored in MongoDB.
    
    This is the primary schema for persisting investigation history.
    It contains all observed data, probability estimates, evidence
    snapshots, and confidence tracking for a single investigation.
    
    Schema Design:
    - Supports incremental Bayesian updates
    - Preserves full history of probability evolution
    - Links all evidence to conclusions
    - Enables investigation resumption across sessions
    """
    # Identifiers
    investigation_id: str
    case_reference: Optional[str] = None  # External case ID
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: InvestigationStatus = InvestigationStatus.ACTIVE
    
    # Investigator info (for audit)
    created_by: Optional[str] = None
    assigned_to: Optional[str] = None
    
    # Target information
    target_description: Optional[str] = None
    target_ip_addresses: List[str] = field(default_factory=list)
    target_time_range_start: Optional[datetime] = None
    target_time_range_end: Optional[datetime] = None
    
    # Observed exit nodes
    exit_node_observations: List[ExitNodeObservation] = field(default_factory=list)
    
    # Entry node probabilities (keyed by fingerprint)
    entry_node_probabilities: Dict[str, EntryNodeProbability] = field(default_factory=dict)
    
    # Confidence timeline
    confidence_timeline: List[ConfidenceTimelineEntry] = field(default_factory=list)
    
    # Evidence snapshots
    evidence_snapshots: List[EvidenceSnapshot] = field(default_factory=list)
    
    # PCAP references
    pcap_references: List[PCAPReference] = field(default_factory=list)
    
    # Bayesian inference state (for incremental updates)
    bayesian_state: Optional[Dict[str, Any]] = None
    
    # Analysis statistics
    total_analysis_runs: int = 0
    last_analysis_timestamp: Optional[datetime] = None
    
    # Current top candidates
    current_top_candidates: List[Dict[str, Any]] = field(default_factory=list)
    
    # Overall investigation confidence
    current_confidence: float = 0.0
    current_confidence_level: ConfidenceLevel = ConfidenceLevel.VERY_LOW
    
    # Notes and annotations
    notes: List[Dict[str, Any]] = field(default_factory=list)
    
    # Tags for organization
    tags: List[str] = field(default_factory=list)
    
    # MongoDB internal ID (set by repository)
    _id: Optional[ObjectId] = field(default=None, repr=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        result = {
            "investigation_id": self.investigation_id,
            "case_reference": self.case_reference,
            "created_at": self.created_at if self.created_at.tzinfo else self.created_at.replace(tzinfo=timezone.utc),
            "updated_at": self.updated_at if self.updated_at.tzinfo else self.updated_at.replace(tzinfo=timezone.utc),
            "status": self.status.value,
            "created_by": self.created_by,
            "assigned_to": self.assigned_to,
            "target_description": self.target_description,
            "target_ip_addresses": self.target_ip_addresses,
            "target_time_range_start": self.target_time_range_start,
            "target_time_range_end": self.target_time_range_end,
            "exit_node_observations": [e.to_dict() for e in self.exit_node_observations],
            "entry_node_probabilities": {
                fp: p.to_dict() for fp, p in self.entry_node_probabilities.items()
            },
            "confidence_timeline": [c.to_dict() for c in self.confidence_timeline],
            "evidence_snapshots": [e.to_dict() for e in self.evidence_snapshots],
            "pcap_references": [p.to_dict() for p in self.pcap_references],
            "bayesian_state": self.bayesian_state,
            "total_analysis_runs": self.total_analysis_runs,
            "last_analysis_timestamp": self.last_analysis_timestamp,
            "current_top_candidates": self.current_top_candidates,
            "current_confidence": self.current_confidence,
            "current_confidence_level": self.current_confidence_level.value,
            "notes": self.notes,
            "tags": self.tags,
            "_disclaimer": (
                "This investigation uses probabilistic forensic correlation based on "
                "metadata and lawful network evidence. It does not de-anonymize TOR users. "
                "All results represent statistical correlations requiring independent verification."
            ),
            "_methodology": "Bayesian inference with evidence metrics (temporal, traffic, stability)",
            "_legal_notice": (
                "For authorized law enforcement use only. Results are investigative support "
                "and should be corroborated with independent evidence before any legal action."
            ),
        }
        
        if self._id:
            result["_id"] = self._id
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Investigation:
        """Create Investigation from MongoDB document"""
        return cls(
            _id=data.get("_id"),
            investigation_id=data["investigation_id"],
            case_reference=data.get("case_reference"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            status=InvestigationStatus(data["status"]),
            created_by=data.get("created_by"),
            assigned_to=data.get("assigned_to"),
            target_description=data.get("target_description"),
            target_ip_addresses=data.get("target_ip_addresses", []),
            target_time_range_start=data.get("target_time_range_start"),
            target_time_range_end=data.get("target_time_range_end"),
            exit_node_observations=[
                ExitNodeObservation.from_dict(e) 
                for e in data.get("exit_node_observations", [])
            ],
            entry_node_probabilities={
                fp: EntryNodeProbability.from_dict(p)
                for fp, p in data.get("entry_node_probabilities", {}).items()
            },
            confidence_timeline=[
                ConfidenceTimelineEntry.from_dict(c)
                for c in data.get("confidence_timeline", [])
            ],
            evidence_snapshots=[
                EvidenceSnapshot.from_dict(e)
                for e in data.get("evidence_snapshots", [])
            ],
            pcap_references=[
                PCAPReference.from_dict(p)
                for p in data.get("pcap_references", [])
            ],
            bayesian_state=data.get("bayesian_state"),
            total_analysis_runs=data.get("total_analysis_runs", 0),
            last_analysis_timestamp=data.get("last_analysis_timestamp"),
            current_top_candidates=data.get("current_top_candidates", []),
            current_confidence=data.get("current_confidence", 0.0),
            current_confidence_level=ConfidenceLevel(
                data.get("current_confidence_level", "very_low")
            ),
            notes=data.get("notes", []),
            tags=data.get("tags", []),
        )
    
    def add_exit_node_observation(self, observation: ExitNodeObservation) -> None:
        """Add a new exit node observation"""
        self.exit_node_observations.append(observation)
        self.updated_at = datetime.now(timezone.utc)
    
    def update_entry_probability(
        self,
        entry: EntryNodeProbability,
        reason: str = "new_evidence",
    ) -> None:
        """
        Update entry node probability with history preservation.
        
        If entry already exists, preserves current state in history.
        """
        fp = entry.fingerprint
        
        if fp in self.entry_node_probabilities:
            # Preserve history
            existing = self.entry_node_probabilities[fp]
            entry.history = existing.history + entry.history
        
        self.entry_node_probabilities[fp] = entry
        self.updated_at = datetime.now(timezone.utc)
    
    def add_confidence_entry(self, entry: ConfidenceTimelineEntry) -> None:
        """Add a confidence timeline entry"""
        self.confidence_timeline.append(entry)
        self.current_confidence = entry.confidence_value
        self.current_confidence_level = entry.confidence_level
        self.updated_at = datetime.now(timezone.utc)
    
    def add_evidence_snapshot(self, snapshot: EvidenceSnapshot) -> None:
        """Add an evidence snapshot"""
        self.evidence_snapshots.append(snapshot)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_pcap_reference(self, reference: PCAPReference) -> None:
        """Add a PCAP reference"""
        self.pcap_references.append(reference)
        self.updated_at = datetime.now(timezone.utc)
    
    def increment_analysis_count(self) -> None:
        """Increment analysis run count"""
        self.total_analysis_runs += 1
        self.last_analysis_timestamp = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)


# ============================================================================
# REPOSITORY - MongoDB Operations
# ============================================================================

class InvestigationRepository:
    """
    MongoDB repository for Investigation documents.
    
    Provides CRUD operations and specialized queries for
    investigation persistence.
    
    Note: Requires pymongo to be installed.
    """
    
    COLLECTION_NAME = "investigations"
    
    def __init__(self, db):
        """
        Initialize repository with MongoDB database.
        
        Args:
            db: MongoDB database instance
        
        Raises:
            ImportError: If pymongo is not installed
        """
        if not PYMONGO_AVAILABLE:
            raise ImportError(
                "pymongo is required for InvestigationRepository. "
                "Install with: pip install pymongo"
            )
        
        self.db = db
        self.collection = db[self.COLLECTION_NAME]
        self._ensure_indexes()
    
    def _ensure_indexes(self) -> None:
        """Create necessary indexes for efficient queries"""
        # Unique index on investigation_id
        self.collection.create_index(
            [("investigation_id", ASCENDING)],
            unique=True,
            name="idx_investigation_id",
        )
        
        # Index on status for filtering
        self.collection.create_index(
            [("status", ASCENDING)],
            name="idx_status",
        )
        
        # Compound index for time-based queries
        self.collection.create_index(
            [("created_at", DESCENDING)],
            name="idx_created_at",
        )
        
        # Index on case reference
        self.collection.create_index(
            [("case_reference", ASCENDING)],
            name="idx_case_reference",
            sparse=True,  # Only index documents with case_reference
        )
        
        # Index on assigned user
        self.collection.create_index(
            [("assigned_to", ASCENDING)],
            name="idx_assigned_to",
            sparse=True,
        )
        
        # Text index for search
        self.collection.create_index(
            [
                ("target_description", "text"),
                ("notes.text", "text"),
                ("tags", "text"),
            ],
            name="idx_text_search",
        )
        
        logger.info(f"Ensured indexes on {self.COLLECTION_NAME} collection")
    
    def create(self, investigation: Investigation) -> str:
        """
        Create a new investigation.
        
        Args:
            investigation: Investigation to create
        
        Returns:
            investigation_id of created document
        
        Raises:
            ValueError: If investigation_id already exists
        """
        doc = investigation.to_dict()
        
        # Remove MongoDB _id if None to let MongoDB generate it
        if "_id" in doc and doc["_id"] is None:
            del doc["_id"]
        
        try:
            result = self.collection.insert_one(doc)
            logger.info(f"Created investigation {investigation.investigation_id}")
            return investigation.investigation_id
        except Exception as e:
            if "duplicate key" in str(e).lower():
                raise ValueError(
                    f"Investigation {investigation.investigation_id} already exists"
                )
            raise
    
    def get_by_id(self, investigation_id: str) -> Optional[Investigation]:
        """
        Get investigation by investigation_id.
        
        Args:
            investigation_id: Unique investigation identifier
        
        Returns:
            Investigation if found, None otherwise
        """
        doc = self.collection.find_one({"investigation_id": investigation_id})
        if doc:
            return Investigation.from_dict(doc)
        return None
    
    def update(self, investigation: Investigation) -> bool:
        """
        Update an existing investigation.
        
        Args:
            investigation: Investigation to update
        
        Returns:
            True if updated, False if not found
        """
        investigation.updated_at = datetime.now(timezone.utc)
        doc = investigation.to_dict()
        
        # Remove _id from update document
        doc.pop("_id", None)
        
        result = self.collection.update_one(
            {"investigation_id": investigation.investigation_id},
            {"$set": doc},
        )
        
        if result.modified_count > 0:
            logger.info(f"Updated investigation {investigation.investigation_id}")
            return True
        return False
    
    def delete(self, investigation_id: str) -> bool:
        """
        Delete an investigation (soft delete by setting status to archived).
        
        Args:
            investigation_id: Investigation to delete
        
        Returns:
            True if deleted, False if not found
        """
        result = self.collection.update_one(
            {"investigation_id": investigation_id},
            {
                "$set": {
                    "status": InvestigationStatus.ARCHIVED.value,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return result.modified_count > 0
    
    def hard_delete(self, investigation_id: str) -> bool:
        """
        Permanently delete an investigation.
        
        Args:
            investigation_id: Investigation to delete
        
        Returns:
            True if deleted, False if not found
        """
        result = self.collection.delete_one({"investigation_id": investigation_id})
        return result.deleted_count > 0
    
    def list_investigations(
        self,
        status: Optional[InvestigationStatus] = None,
        assigned_to: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Investigation]:
        """
        List investigations with optional filtering.
        
        Args:
            status: Filter by status
            assigned_to: Filter by assigned user
            skip: Number of documents to skip
            limit: Maximum documents to return
        
        Returns:
            List of matching investigations
        """
        query = {}
        
        if status:
            query["status"] = status.value
        
        if assigned_to:
            query["assigned_to"] = assigned_to
        
        cursor = self.collection.find(query).sort(
            "updated_at", DESCENDING
        ).skip(skip).limit(limit)
        
        return [Investigation.from_dict(doc) for doc in cursor]
    
    def search(
        self,
        text_query: str,
        limit: int = 20,
    ) -> List[Investigation]:
        """
        Full-text search across investigations.
        
        Args:
            text_query: Search query
            limit: Maximum results
        
        Returns:
            Matching investigations
        """
        cursor = self.collection.find(
            {"$text": {"$search": text_query}},
            {"score": {"$meta": "textScore"}},
        ).sort(
            [("score", {"$meta": "textScore"})]
        ).limit(limit)
        
        return [Investigation.from_dict(doc) for doc in cursor]
    
    def find_by_exit_node(self, fingerprint: str) -> List[Investigation]:
        """
        Find investigations that observed a specific exit node.
        
        Args:
            fingerprint: Exit node fingerprint
        
        Returns:
            List of investigations
        """
        cursor = self.collection.find({
            "exit_node_observations.fingerprint": fingerprint,
        })
        
        return [Investigation.from_dict(doc) for doc in cursor]
    
    def find_by_entry_candidate(
        self,
        fingerprint: str,
        min_probability: float = 0.0,
    ) -> List[Investigation]:
        """
        Find investigations with a specific entry node candidate.
        
        Args:
            fingerprint: Entry node fingerprint
            min_probability: Minimum posterior probability
        
        Returns:
            List of investigations
        """
        cursor = self.collection.find({
            f"entry_node_probabilities.{fingerprint}.current_posterior": {
                "$gte": min_probability
            },
        })
        
        return [Investigation.from_dict(doc) for doc in cursor]


# ============================================================================
# SERVICE - Business Logic
# ============================================================================

class InvestigationService:
    """
    Service layer for investigation operations.
    
    Provides high-level business logic and integrates with
    the Bayesian inference engine for incremental updates.
    """
    
    def __init__(self, repository: InvestigationRepository):
        """
        Initialize service with repository.
        
        Args:
            repository: InvestigationRepository instance
        """
        self.repository = repository
    
    def create_investigation(
        self,
        case_reference: Optional[str] = None,
        created_by: Optional[str] = None,
        target_description: Optional[str] = None,
        target_ips: Optional[List[str]] = None,
    ) -> Investigation:
        """
        Create a new investigation.
        
        Args:
            case_reference: External case reference
            created_by: User creating the investigation
            target_description: Description of investigation target
            target_ips: Target IP addresses
        
        Returns:
            Created Investigation
        """
        investigation = Investigation(
            investigation_id=f"inv_{uuid.uuid4().hex[:12]}",
            case_reference=case_reference,
            created_by=created_by,
            target_description=target_description,
            target_ip_addresses=target_ips or [],
        )
        
        self.repository.create(investigation)
        
        logger.info(f"Created investigation {investigation.investigation_id}")
        return investigation
    
    def add_exit_observation(
        self,
        investigation_id: str,
        fingerprint: str,
        nickname: str,
        ip_address: str,
        country_code: str,
        source: str,
        **kwargs,
    ) -> Investigation:
        """
        Add an exit node observation to an investigation.
        
        Args:
            investigation_id: Target investigation
            fingerprint: Exit node fingerprint
            nickname: Exit node nickname
            ip_address: Exit node IP
            country_code: Exit node country
            source: Source of observation
            **kwargs: Additional observation metadata
        
        Returns:
            Updated Investigation
        """
        investigation = self.repository.get_by_id(investigation_id)
        if not investigation:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        observation = ExitNodeObservation(
            fingerprint=fingerprint,
            nickname=nickname,
            observed_at=datetime.now(timezone.utc),
            ip_address=ip_address,
            country_code=country_code,
            source=source,
            observed_bandwidth=kwargs.get("observed_bandwidth"),
            consensus_weight=kwargs.get("consensus_weight"),
            flags=kwargs.get("flags", []),
            pcap_reference_id=kwargs.get("pcap_reference_id"),
            flow_metadata=kwargs.get("flow_metadata"),
        )
        
        investigation.add_exit_node_observation(observation)
        self.repository.update(investigation)
        
        return investigation
    
    def update_entry_probability_incremental(
        self,
        investigation_id: str,
        fingerprint: str,
        nickname: str,
        new_prior: float,
        new_posterior: float,
        new_likelihood: float,
        evidence_summary: Dict[str, float],
        exit_nodes_involved: List[str],
    ) -> Investigation:
        """
        Incrementally update entry node probability.
        
        This method preserves the history of probability updates
        and supports incremental Bayesian refinement.
        
        Args:
            investigation_id: Target investigation
            fingerprint: Entry node fingerprint
            nickname: Entry node nickname
            new_prior: Updated prior probability
            new_posterior: Updated posterior probability
            new_likelihood: Computed likelihood
            evidence_summary: Evidence scores used
            exit_nodes_involved: Exit nodes observed with this entry
        
        Returns:
            Updated Investigation
        """
        investigation = self.repository.get_by_id(investigation_id)
        if not investigation:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        now = datetime.now(timezone.utc)
        
        # Create history entry
        history_entry = ProbabilityHistoryEntry(
            timestamp=now,
            prior_probability=new_prior,
            posterior_probability=new_posterior,
            likelihood=new_likelihood,
            update_reason="incremental_bayesian_update",
            evidence_summary=evidence_summary,
            observation_count=len(exit_nodes_involved),
            exit_nodes_at_update=exit_nodes_involved,
        )
        
        # Get or create entry probability record
        if fingerprint in investigation.entry_node_probabilities:
            entry_prob = investigation.entry_node_probabilities[fingerprint]
            entry_prob.history.append(history_entry)
            entry_prob.current_prior = new_prior
            entry_prob.current_posterior = new_posterior
            entry_prob.last_updated = now
            entry_prob.update_count += 1
            
            # Update running averages
            n = entry_prob.update_count
            for key in ["time_overlap", "traffic_similarity", "stability", "pcap_evidence"]:
                if key in evidence_summary:
                    attr = f"avg_{key}"
                    old_avg = getattr(entry_prob, attr, 0.0)
                    new_avg = (old_avg * (n - 1) + evidence_summary[key]) / n
                    setattr(entry_prob, attr, new_avg)
            
            # Update associated exits
            for exit_fp in exit_nodes_involved:
                if exit_fp not in entry_prob.associated_exit_nodes:
                    entry_prob.associated_exit_nodes.append(exit_fp)
        else:
            # Create new entry probability
            entry_prob = EntryNodeProbability(
                fingerprint=fingerprint,
                nickname=nickname,
                current_prior=new_prior,
                current_posterior=new_posterior,
                last_updated=now,
                update_count=1,
                history=[history_entry],
                avg_time_overlap=evidence_summary.get("time_overlap", 0.0),
                avg_traffic_similarity=evidence_summary.get("traffic_similarity", 0.0),
                avg_stability=evidence_summary.get("stability", 0.0),
                avg_pcap_evidence=evidence_summary.get("pcap_evidence", 0.0),
                associated_exit_nodes=exit_nodes_involved,
            )
        
        # Assess confidence level
        entry_prob.confidence_level = self._assess_confidence_level(
            entry_prob.update_count,
            new_posterior,
            new_prior,
        )
        
        investigation.entry_node_probabilities[fingerprint] = entry_prob
        investigation.updated_at = now
        
        self.repository.update(investigation)
        
        return investigation
    
    def _assess_confidence_level(
        self,
        observation_count: int,
        posterior: float,
        prior: float,
    ) -> ConfidenceLevel:
        """
        Assess confidence level for an entry node estimate.
        
        Args:
            observation_count: Number of observations
            posterior: Current posterior probability
            prior: Prior probability
        
        Returns:
            ConfidenceLevel enum value
        """
        if observation_count == 0:
            return ConfidenceLevel.VERY_LOW
        
        # Certainty: how far from 0.5?
        certainty = abs(posterior - 0.5) * 2
        
        # Bayes factor
        import math
        if prior > 0:
            bf = posterior / prior
            log_bf = math.log(max(bf, 0.001))
        else:
            log_bf = 0.0
        
        # Combined score
        score = (
            0.3 * min(1.0, observation_count / 10.0) +  # More observations = better
            0.4 * certainty +  # Higher certainty = better
            0.3 * min(1.0, abs(log_bf) / 3.0)  # Evidence impact
        )
        
        if score >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif score >= 0.6:
            return ConfidenceLevel.HIGH
        elif score >= 0.4:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.2:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def add_confidence_snapshot(
        self,
        investigation_id: str,
        confidence_value: float,
        components: Dict[str, float],
        trigger: str,
        note: Optional[str] = None,
    ) -> Investigation:
        """
        Add a confidence timeline snapshot.
        
        Args:
            investigation_id: Target investigation
            confidence_value: Overall confidence (0.0-1.0)
            components: Confidence components
            trigger: What triggered this entry
            note: Optional note
        
        Returns:
            Updated Investigation
        """
        investigation = self.repository.get_by_id(investigation_id)
        if not investigation:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        # Determine confidence level
        if confidence_value >= 0.8:
            level = ConfidenceLevel.VERY_HIGH
        elif confidence_value >= 0.6:
            level = ConfidenceLevel.HIGH
        elif confidence_value >= 0.4:
            level = ConfidenceLevel.MEDIUM
        elif confidence_value >= 0.2:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.VERY_LOW
        
        # Get top candidates
        top_candidates = []
        for fp, entry in sorted(
            investigation.entry_node_probabilities.items(),
            key=lambda x: x[1].current_posterior,
            reverse=True,
        )[:5]:
            top_candidates.append({
                "fingerprint": fp,
                "probability": entry.current_posterior,
            })
        
        entry = ConfidenceTimelineEntry(
            timestamp=datetime.now(timezone.utc),
            confidence_value=confidence_value,
            confidence_level=level,
            components=components,
            trigger=trigger,
            top_entry_candidates=top_candidates,
            total_evidence_count=len(investigation.evidence_snapshots),
            note=note,
        )
        
        investigation.add_confidence_entry(entry)
        self.repository.update(investigation)
        
        return investigation
    
    def save_bayesian_state(
        self,
        investigation_id: str,
        priors: Dict[str, float],
        observations: Dict[str, List[Dict]],
        stats: Dict[str, Dict],
    ) -> Investigation:
        """
        Save Bayesian inference engine state for resumption.
        
        This enables incremental updates across sessions by
        preserving the inference engine's internal state.
        
        Args:
            investigation_id: Target investigation
            priors: Prior probabilities
            observations: Observation history
            stats: Aggregated statistics
        
        Returns:
            Updated Investigation
        """
        investigation = self.repository.get_by_id(investigation_id)
        if not investigation:
            raise ValueError(f"Investigation {investigation_id} not found")
        
        investigation.bayesian_state = {
            "priors": priors,
            "observations": observations,
            "stats": stats,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        
        self.repository.update(investigation)
        
        return investigation
    
    def load_bayesian_state(
        self,
        investigation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Load saved Bayesian state for resumption.
        
        Args:
            investigation_id: Target investigation
        
        Returns:
            Saved Bayesian state or None
        """
        investigation = self.repository.get_by_id(investigation_id)
        if not investigation:
            return None
        
        return investigation.bayesian_state
    
    def get_probability_evolution(
        self,
        investigation_id: str,
        fingerprint: str,
    ) -> List[Dict[str, Any]]:
        """
        Get the full probability evolution for an entry node.
        
        Args:
            investigation_id: Target investigation
            fingerprint: Entry node fingerprint
        
        Returns:
            List of probability snapshots over time
        """
        investigation = self.repository.get_by_id(investigation_id)
        if not investigation:
            return []
        
        if fingerprint not in investigation.entry_node_probabilities:
            return []
        
        entry = investigation.entry_node_probabilities[fingerprint]
        
        return [
            {
                "timestamp": h.timestamp.isoformat(),
                "prior": h.prior_probability,
                "posterior": h.posterior_probability,
                "likelihood": h.likelihood,
                "observation_count": h.observation_count,
                "evidence": h.evidence_summary,
            }
            for h in entry.history
        ]


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def get_mongo_client():
    """
    Get MongoDB client from environment.
    
    Returns:
        MongoClient instance
    
    Raises:
        ImportError: If pymongo is not installed
    """
    if not PYMONGO_AVAILABLE:
        raise ImportError(
            "pymongo is required. Install with: pip install pymongo"
        )
    mongo_url = os.getenv("MONGO_URL", "mongodb://mongo:27017/torunveil")
    return MongoClient(mongo_url)


def get_investigation_repository(db=None) -> InvestigationRepository:
    """
    Get InvestigationRepository instance.
    
    Args:
        db: Optional database instance. If not provided,
            creates connection from environment.
    
    Returns:
        InvestigationRepository instance
    
    Raises:
        ImportError: If pymongo is not installed
    """
    if db is None:
        client = get_mongo_client()
        db = client["torunveil"]
    
    return InvestigationRepository(db)


def get_investigation_service(
    repository: Optional[InvestigationRepository] = None,
) -> InvestigationService:
    """
    Get InvestigationService instance.
    
    Args:
        repository: Optional repository instance
    
    Returns:
        InvestigationService instance
    """
    if repository is None:
        repository = get_investigation_repository()
    
    return InvestigationService(repository)
