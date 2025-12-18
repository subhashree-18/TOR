# tests/test_investigation_models.py
"""
Tests for MongoDB Investigation Models

Tests cover:
1. Data structure serialization/deserialization
2. Repository CRUD operations (with mocked MongoDB)
3. Service layer business logic
4. Incremental Bayesian update workflows
5. History preservation and evolution tracking
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch

# Import models
import sys
sys.path.insert(0, "/home/subha/Downloads/tor-unveil")

# Mock bson if not available (for testing without MongoDB)
try:
    from bson import ObjectId
except ImportError:
    class ObjectId:
        """Mock ObjectId for testing"""
        def __init__(self, oid=None):
            self._id = oid or "507f1f77bcf86cd799439011"
        def __str__(self):
            return self._id

from backend.app.models.investigation import (
    Investigation,
    InvestigationStatus,
    ExitNodeObservation,
    EntryNodeProbability,
    ProbabilityHistoryEntry,
    ConfidenceTimelineEntry,
    EvidenceSnapshot,
    PCAPReference,
    InvestigationRepository,
    InvestigationService,
    EvidenceType,
    ConfidenceLevel,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_exit_observation():
    """Sample exit node observation"""
    return ExitNodeObservation(
        fingerprint="ABCD1234" * 5,
        nickname="ExitRelay1",
        observed_at=datetime.now(timezone.utc),
        ip_address="192.168.1.100",
        country_code="DE",
        source="pcap",
        observed_bandwidth=50_000_000,
        consensus_weight=0.0012,
        flags=["Exit", "Fast", "Stable", "Valid"],
        pcap_reference_id="pcap_001",
        flow_metadata={"flow_count": 15, "total_bytes": 1024000},
    )


@pytest.fixture
def sample_probability_history():
    """Sample probability history entry"""
    return ProbabilityHistoryEntry(
        timestamp=datetime.now(timezone.utc),
        prior_probability=0.001,
        posterior_probability=0.015,
        likelihood=0.75,
        update_reason="new_evidence",
        evidence_summary={
            "time_overlap": 0.8,
            "traffic_similarity": 0.7,
            "stability": 0.85,
        },
        observation_count=3,
        exit_nodes_at_update=["exit1", "exit2", "exit3"],
    )


@pytest.fixture
def sample_entry_probability(sample_probability_history):
    """Sample entry node probability"""
    return EntryNodeProbability(
        fingerprint="ENTRY123" * 5,
        nickname="GuardRelay1",
        current_prior=0.001,
        current_posterior=0.025,
        last_updated=datetime.now(timezone.utc),
        update_count=5,
        history=[sample_probability_history],
        avg_time_overlap=0.78,
        avg_traffic_similarity=0.72,
        avg_stability=0.82,
        avg_pcap_evidence=0.65,
        associated_exit_nodes=["exit1", "exit2"],
        confidence_level=ConfidenceLevel.MEDIUM,
        relay_metadata={"guard_probability": 0.0015},
    )


@pytest.fixture
def sample_confidence_entry():
    """Sample confidence timeline entry"""
    return ConfidenceTimelineEntry(
        timestamp=datetime.now(timezone.utc),
        confidence_value=0.65,
        confidence_level=ConfidenceLevel.HIGH,
        components={
            "evidence_quality": 0.7,
            "consistency": 0.65,
            "sample_size": 0.6,
        },
        trigger="analysis_run",
        top_entry_candidates=[
            {"fingerprint": "entry1", "probability": 0.025},
            {"fingerprint": "entry2", "probability": 0.018},
        ],
        total_evidence_count=12,
        note="Initial analysis complete",
    )


@pytest.fixture
def sample_evidence_snapshot():
    """Sample evidence snapshot"""
    return EvidenceSnapshot(
        snapshot_id="snap_001",
        captured_at=datetime.now(timezone.utc),
        evidence_type=EvidenceType.TEMPORAL,
        source_description="Time overlap analysis",
        scores={
            "overlap_days": 45.5,
            "concurrent_uptime": 0.85,
            "first_seen_delta": 3.2,
        },
        related_entry_fingerprint="ENTRY123" * 5,
        related_exit_fingerprint="ABCD1234" * 5,
        weight_applied=0.35,
    )


@pytest.fixture
def sample_pcap_reference():
    """Sample PCAP reference"""
    return PCAPReference(
        reference_id="pcap_001",
        original_filename="capture_20240115.pcap",
        file_hash_sha256="abc123" * 10 + "ab",
        file_size_bytes=15_000_000,
        upload_timestamp=datetime.now(timezone.utc),
        storage_location="gridfs://captures/pcap_001",
        storage_type="gridfs",
        analysis_timestamp=datetime.now(timezone.utc),
        total_packets=50000,
        total_flows=250,
        tor_related_flows=45,
        flow_summary={"avg_duration": 12.5, "total_bytes": 2500000},
        identified_exit_nodes=["exit1", "exit2"],
        analysis_mode="offline",
    )


@pytest.fixture
def sample_investigation(
    sample_exit_observation,
    sample_entry_probability,
    sample_confidence_entry,
    sample_evidence_snapshot,
    sample_pcap_reference,
):
    """Complete sample investigation"""
    return Investigation(
        investigation_id="inv_test123456",
        case_reference="CASE-2024-001",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        status=InvestigationStatus.ACTIVE,
        created_by="officer_001",
        assigned_to="officer_002",
        target_description="Investigation of suspicious TOR traffic",
        target_ip_addresses=["10.0.0.1", "10.0.0.2"],
        target_time_range_start=datetime.now(timezone.utc) - timedelta(days=30),
        target_time_range_end=datetime.now(timezone.utc),
        exit_node_observations=[sample_exit_observation],
        entry_node_probabilities={
            sample_entry_probability.fingerprint: sample_entry_probability
        },
        confidence_timeline=[sample_confidence_entry],
        evidence_snapshots=[sample_evidence_snapshot],
        pcap_references=[sample_pcap_reference],
        total_analysis_runs=3,
        current_confidence=0.65,
        current_confidence_level=ConfidenceLevel.HIGH,
        tags=["priority", "tor-exit"],
    )


@pytest.fixture
def mock_collection():
    """Mock MongoDB collection"""
    collection = MagicMock()
    collection.create_index = MagicMock()
    return collection


@pytest.fixture
def mock_db(mock_collection):
    """Mock MongoDB database"""
    db = MagicMock()
    db.__getitem__ = MagicMock(return_value=mock_collection)
    return db


# ============================================================================
# DATA STRUCTURE TESTS
# ============================================================================

class TestExitNodeObservation:
    """Tests for ExitNodeObservation dataclass"""
    
    def test_to_dict_basic(self, sample_exit_observation):
        """Test basic serialization"""
        d = sample_exit_observation.to_dict()
        
        assert d["fingerprint"] == sample_exit_observation.fingerprint
        assert d["nickname"] == "ExitRelay1"
        assert d["ip_address"] == "192.168.1.100"
        assert d["country_code"] == "DE"
        assert d["source"] == "pcap"
        assert d["observed_bandwidth"] == 50_000_000
        assert "Exit" in d["flags"]
    
    def test_from_dict_roundtrip(self, sample_exit_observation):
        """Test roundtrip serialization"""
        d = sample_exit_observation.to_dict()
        restored = ExitNodeObservation.from_dict(d)
        
        assert restored.fingerprint == sample_exit_observation.fingerprint
        assert restored.nickname == sample_exit_observation.nickname
        assert restored.source == sample_exit_observation.source
        assert restored.flags == sample_exit_observation.flags
    
    def test_minimal_observation(self):
        """Test observation with minimal required fields"""
        obs = ExitNodeObservation(
            fingerprint="FP123",
            nickname="Relay",
            observed_at=datetime.now(timezone.utc),
            ip_address="1.2.3.4",
            country_code="US",
            source="manual",
        )
        
        d = obs.to_dict()
        assert d["fingerprint"] == "FP123"
        assert d["observed_bandwidth"] is None
        assert d["flags"] == []
    
    def test_timezone_handling(self):
        """Test that naive datetimes get timezone"""
        naive_dt = datetime.now()  # No timezone
        obs = ExitNodeObservation(
            fingerprint="FP123",
            nickname="Relay",
            observed_at=naive_dt,
            ip_address="1.2.3.4",
            country_code="US",
            source="manual",
        )
        
        d = obs.to_dict()
        assert d["observed_at"].tzinfo is not None


class TestProbabilityHistoryEntry:
    """Tests for ProbabilityHistoryEntry dataclass"""
    
    def test_to_dict(self, sample_probability_history):
        """Test serialization"""
        d = sample_probability_history.to_dict()
        
        assert d["prior_probability"] == 0.001
        assert d["posterior_probability"] == 0.015
        assert d["likelihood"] == 0.75
        assert d["update_reason"] == "new_evidence"
        assert d["observation_count"] == 3
        assert len(d["exit_nodes_at_update"]) == 3
    
    def test_roundtrip(self, sample_probability_history):
        """Test roundtrip"""
        d = sample_probability_history.to_dict()
        restored = ProbabilityHistoryEntry.from_dict(d)
        
        assert restored.prior_probability == sample_probability_history.prior_probability
        assert restored.evidence_summary == sample_probability_history.evidence_summary


class TestEntryNodeProbability:
    """Tests for EntryNodeProbability dataclass"""
    
    def test_to_dict_with_history(self, sample_entry_probability):
        """Test serialization includes history"""
        d = sample_entry_probability.to_dict()
        
        assert d["fingerprint"] == sample_entry_probability.fingerprint
        assert d["current_posterior"] == 0.025
        assert d["update_count"] == 5
        assert len(d["history"]) == 1
        assert d["confidence_level"] == "medium"
    
    def test_roundtrip(self, sample_entry_probability):
        """Test roundtrip preserves all data"""
        d = sample_entry_probability.to_dict()
        restored = EntryNodeProbability.from_dict(d)
        
        assert restored.fingerprint == sample_entry_probability.fingerprint
        assert restored.current_posterior == sample_entry_probability.current_posterior
        assert len(restored.history) == len(sample_entry_probability.history)
        assert restored.confidence_level == sample_entry_probability.confidence_level
    
    def test_average_evidence_scores(self, sample_entry_probability):
        """Test average evidence scores are preserved"""
        d = sample_entry_probability.to_dict()
        
        assert d["avg_time_overlap"] == 0.78
        assert d["avg_traffic_similarity"] == 0.72
        assert d["avg_stability"] == 0.82
        assert d["avg_pcap_evidence"] == 0.65


class TestConfidenceTimelineEntry:
    """Tests for ConfidenceTimelineEntry dataclass"""
    
    def test_to_dict(self, sample_confidence_entry):
        """Test serialization"""
        d = sample_confidence_entry.to_dict()
        
        assert d["confidence_value"] == 0.65
        assert d["confidence_level"] == "high"
        assert d["trigger"] == "analysis_run"
        assert len(d["top_entry_candidates"]) == 2
    
    def test_roundtrip(self, sample_confidence_entry):
        """Test roundtrip"""
        d = sample_confidence_entry.to_dict()
        restored = ConfidenceTimelineEntry.from_dict(d)
        
        assert restored.confidence_value == sample_confidence_entry.confidence_value
        assert restored.confidence_level == sample_confidence_entry.confidence_level


class TestEvidenceSnapshot:
    """Tests for EvidenceSnapshot dataclass"""
    
    def test_to_dict(self, sample_evidence_snapshot):
        """Test serialization"""
        d = sample_evidence_snapshot.to_dict()
        
        assert d["snapshot_id"] == "snap_001"
        assert d["evidence_type"] == "temporal"
        assert "overlap_days" in d["scores"]
    
    def test_evidence_types(self):
        """Test all evidence types"""
        for etype in EvidenceType:
            snap = EvidenceSnapshot(
                snapshot_id="test",
                captured_at=datetime.now(timezone.utc),
                evidence_type=etype,
                source_description="test",
                scores={"test": 0.5},
            )
            d = snap.to_dict()
            assert d["evidence_type"] == etype.value


class TestPCAPReference:
    """Tests for PCAPReference dataclass"""
    
    def test_to_dict(self, sample_pcap_reference):
        """Test serialization"""
        d = sample_pcap_reference.to_dict()
        
        assert d["reference_id"] == "pcap_001"
        assert d["total_packets"] == 50000
        assert d["tor_related_flows"] == 45
    
    def test_roundtrip(self, sample_pcap_reference):
        """Test roundtrip"""
        d = sample_pcap_reference.to_dict()
        restored = PCAPReference.from_dict(d)
        
        assert restored.reference_id == sample_pcap_reference.reference_id
        assert restored.total_flows == sample_pcap_reference.total_flows


# ============================================================================
# INVESTIGATION DOCUMENT TESTS
# ============================================================================

class TestInvestigation:
    """Tests for Investigation document"""
    
    def test_to_dict_complete(self, sample_investigation):
        """Test complete investigation serialization"""
        d = sample_investigation.to_dict()
        
        assert d["investigation_id"] == "inv_test123456"
        assert d["case_reference"] == "CASE-2024-001"
        assert d["status"] == "active"
        assert len(d["exit_node_observations"]) == 1
        assert len(d["entry_node_probabilities"]) == 1
        assert len(d["confidence_timeline"]) == 1
        assert d["total_analysis_runs"] == 3
    
    def test_roundtrip(self, sample_investigation):
        """Test complete roundtrip"""
        d = sample_investigation.to_dict()
        restored = Investigation.from_dict(d)
        
        assert restored.investigation_id == sample_investigation.investigation_id
        assert restored.status == sample_investigation.status
        assert len(restored.exit_node_observations) == 1
        assert len(restored.entry_node_probabilities) == 1
    
    def test_add_exit_observation(self, sample_investigation):
        """Test adding exit observation updates timestamp"""
        old_updated = sample_investigation.updated_at
        
        new_obs = ExitNodeObservation(
            fingerprint="NEWEXITFP" * 4,
            nickname="NewExit",
            observed_at=datetime.now(timezone.utc),
            ip_address="5.6.7.8",
            country_code="NL",
            source="manual",
        )
        
        sample_investigation.add_exit_node_observation(new_obs)
        
        assert len(sample_investigation.exit_node_observations) == 2
        assert sample_investigation.updated_at >= old_updated
    
    def test_add_confidence_entry(self, sample_investigation):
        """Test adding confidence entry updates current values"""
        new_entry = ConfidenceTimelineEntry(
            timestamp=datetime.now(timezone.utc),
            confidence_value=0.85,
            confidence_level=ConfidenceLevel.VERY_HIGH,
            components={"test": 0.9},
            trigger="manual_review",
        )
        
        sample_investigation.add_confidence_entry(new_entry)
        
        assert sample_investigation.current_confidence == 0.85
        assert sample_investigation.current_confidence_level == ConfidenceLevel.VERY_HIGH
    
    def test_increment_analysis_count(self, sample_investigation):
        """Test analysis count increment"""
        initial_count = sample_investigation.total_analysis_runs
        
        sample_investigation.increment_analysis_count()
        
        assert sample_investigation.total_analysis_runs == initial_count + 1
        assert sample_investigation.last_analysis_timestamp is not None
    
    def test_minimal_investigation(self):
        """Test investigation with minimal fields"""
        inv = Investigation(investigation_id="inv_minimal")
        
        d = inv.to_dict()
        assert d["investigation_id"] == "inv_minimal"
        assert d["status"] == "active"
        assert d["exit_node_observations"] == []
    
    def test_update_entry_probability_preserves_history(self):
        """Test that updating entry probability preserves history"""
        inv = Investigation(investigation_id="inv_test")
        
        # Add initial entry
        history1 = ProbabilityHistoryEntry(
            timestamp=datetime.now(timezone.utc),
            prior_probability=0.001,
            posterior_probability=0.01,
            likelihood=0.5,
            update_reason="initial",
            evidence_summary={},
            observation_count=1,
        )
        
        entry1 = EntryNodeProbability(
            fingerprint="FP123",
            nickname="Guard1",
            current_prior=0.001,
            current_posterior=0.01,
            last_updated=datetime.now(timezone.utc),
            update_count=1,
            history=[history1],
        )
        
        inv.update_entry_probability(entry1)
        
        # Update with new entry
        history2 = ProbabilityHistoryEntry(
            timestamp=datetime.now(timezone.utc),
            prior_probability=0.001,
            posterior_probability=0.02,
            likelihood=0.7,
            update_reason="update",
            evidence_summary={},
            observation_count=2,
        )
        
        entry2 = EntryNodeProbability(
            fingerprint="FP123",
            nickname="Guard1",
            current_prior=0.001,
            current_posterior=0.02,
            last_updated=datetime.now(timezone.utc),
            update_count=2,
            history=[history2],
        )
        
        inv.update_entry_probability(entry2)
        
        # History should have both entries
        assert len(inv.entry_node_probabilities["FP123"].history) == 2


# ============================================================================
# REPOSITORY TESTS (Mocked MongoDB)
# ============================================================================

# Check if pymongo is available for repository tests
try:
    import pymongo
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

# Skip repository tests if pymongo is not installed
@pytest.mark.skipif(not PYMONGO_AVAILABLE, reason="pymongo not installed")
class TestInvestigationRepository:
    """Tests for InvestigationRepository"""
    
    def test_init_creates_indexes(self, mock_db):
        """Test repository creates indexes on init"""
        repo = InvestigationRepository(mock_db)
        
        # Should have created multiple indexes
        assert mock_db["investigations"].create_index.call_count >= 5
    
    def test_create_investigation(self, mock_db, sample_investigation):
        """Test creating investigation"""
        mock_db["investigations"].insert_one = MagicMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        
        repo = InvestigationRepository(mock_db)
        result = repo.create(sample_investigation)
        
        assert result == sample_investigation.investigation_id
        mock_db["investigations"].insert_one.assert_called_once()
    
    def test_create_duplicate_raises(self, mock_db, sample_investigation):
        """Test creating duplicate raises ValueError"""
        mock_db["investigations"].insert_one = MagicMock(
            side_effect=Exception("duplicate key error")
        )
        
        repo = InvestigationRepository(mock_db)
        
        with pytest.raises(ValueError, match="already exists"):
            repo.create(sample_investigation)
    
    def test_get_by_id_found(self, mock_db, sample_investigation):
        """Test getting investigation by ID"""
        mock_db["investigations"].find_one = MagicMock(
            return_value=sample_investigation.to_dict()
        )
        
        repo = InvestigationRepository(mock_db)
        result = repo.get_by_id("inv_test123456")
        
        assert result is not None
        assert result.investigation_id == "inv_test123456"
    
    def test_get_by_id_not_found(self, mock_db):
        """Test getting non-existent investigation"""
        mock_db["investigations"].find_one = MagicMock(return_value=None)
        
        repo = InvestigationRepository(mock_db)
        result = repo.get_by_id("nonexistent")
        
        assert result is None
    
    def test_update_investigation(self, mock_db, sample_investigation):
        """Test updating investigation"""
        mock_db["investigations"].update_one = MagicMock(
            return_value=MagicMock(modified_count=1)
        )
        
        repo = InvestigationRepository(mock_db)
        result = repo.update(sample_investigation)
        
        assert result is True
        mock_db["investigations"].update_one.assert_called_once()
    
    def test_delete_soft(self, mock_db):
        """Test soft delete (archive)"""
        mock_db["investigations"].update_one = MagicMock(
            return_value=MagicMock(modified_count=1)
        )
        
        repo = InvestigationRepository(mock_db)
        result = repo.delete("inv_test")
        
        assert result is True
        # Check that status was set to archived
        call_args = mock_db["investigations"].update_one.call_args
        assert call_args[0][1]["$set"]["status"] == "archived"
    
    def test_hard_delete(self, mock_db):
        """Test hard delete"""
        mock_db["investigations"].delete_one = MagicMock(
            return_value=MagicMock(deleted_count=1)
        )
        
        repo = InvestigationRepository(mock_db)
        result = repo.hard_delete("inv_test")
        
        assert result is True
    
    def test_list_investigations(self, mock_db, sample_investigation):
        """Test listing investigations"""
        cursor_mock = MagicMock()
        cursor_mock.sort.return_value = cursor_mock
        cursor_mock.skip.return_value = cursor_mock
        cursor_mock.limit.return_value = [sample_investigation.to_dict()]
        
        mock_db["investigations"].find = MagicMock(return_value=cursor_mock)
        
        repo = InvestigationRepository(mock_db)
        results = repo.list_investigations()
        
        assert len(results) == 1
        assert results[0].investigation_id == "inv_test123456"
    
    def test_list_with_status_filter(self, mock_db):
        """Test listing with status filter"""
        cursor_mock = MagicMock()
        cursor_mock.sort.return_value = cursor_mock
        cursor_mock.skip.return_value = cursor_mock
        cursor_mock.limit.return_value = []
        
        mock_db["investigations"].find = MagicMock(return_value=cursor_mock)
        
        repo = InvestigationRepository(mock_db)
        repo.list_investigations(status=InvestigationStatus.ACTIVE)
        
        call_args = mock_db["investigations"].find.call_args
        assert call_args[0][0]["status"] == "active"
    
    def test_find_by_exit_node(self, mock_db, sample_investigation):
        """Test finding by exit node fingerprint"""
        mock_db["investigations"].find = MagicMock(
            return_value=[sample_investigation.to_dict()]
        )
        
        repo = InvestigationRepository(mock_db)
        results = repo.find_by_exit_node("ABCD1234" * 5)
        
        assert len(results) == 1
        call_args = mock_db["investigations"].find.call_args
        assert "exit_node_observations.fingerprint" in call_args[0][0]


# ============================================================================
# SERVICE LAYER TESTS
# ============================================================================

class TestInvestigationService:
    """Tests for InvestigationService"""
    
    @pytest.fixture
    def mock_repository(self):
        """Mock repository"""
        repo = MagicMock(spec=InvestigationRepository)
        return repo
    
    def test_create_investigation(self, mock_repository):
        """Test creating new investigation"""
        mock_repository.create = MagicMock(return_value="inv_123")
        
        service = InvestigationService(mock_repository)
        result = service.create_investigation(
            case_reference="CASE-001",
            created_by="officer_1",
            target_description="Test investigation",
        )
        
        assert result.case_reference == "CASE-001"
        assert result.created_by == "officer_1"
        assert result.investigation_id.startswith("inv_")
        mock_repository.create.assert_called_once()
    
    def test_add_exit_observation(self, mock_repository, sample_investigation):
        """Test adding exit observation"""
        mock_repository.get_by_id = MagicMock(return_value=sample_investigation)
        mock_repository.update = MagicMock(return_value=True)
        
        service = InvestigationService(mock_repository)
        result = service.add_exit_observation(
            investigation_id="inv_test123456",
            fingerprint="NEWEXIT" * 5,
            nickname="NewExitNode",
            ip_address="9.9.9.9",
            country_code="FR",
            source="pcap",
        )
        
        assert len(result.exit_node_observations) == 2
        mock_repository.update.assert_called_once()
    
    def test_add_exit_observation_not_found(self, mock_repository):
        """Test adding to non-existent investigation"""
        mock_repository.get_by_id = MagicMock(return_value=None)
        
        service = InvestigationService(mock_repository)
        
        with pytest.raises(ValueError, match="not found"):
            service.add_exit_observation(
                investigation_id="nonexistent",
                fingerprint="FP",
                nickname="Nick",
                ip_address="1.2.3.4",
                country_code="US",
                source="manual",
            )
    
    def test_incremental_probability_update_new_entry(self, mock_repository):
        """Test incremental update creates new entry"""
        inv = Investigation(investigation_id="inv_test")
        mock_repository.get_by_id = MagicMock(return_value=inv)
        mock_repository.update = MagicMock(return_value=True)
        
        service = InvestigationService(mock_repository)
        result = service.update_entry_probability_incremental(
            investigation_id="inv_test",
            fingerprint="FP123",
            nickname="Guard1",
            new_prior=0.001,
            new_posterior=0.015,
            new_likelihood=0.7,
            evidence_summary={
                "time_overlap": 0.8,
                "traffic_similarity": 0.7,
            },
            exit_nodes_involved=["exit1"],
        )
        
        assert "FP123" in result.entry_node_probabilities
        entry = result.entry_node_probabilities["FP123"]
        assert entry.current_posterior == 0.015
        assert len(entry.history) == 1
    
    def test_incremental_probability_update_existing_entry(self, mock_repository):
        """Test incremental update refines existing entry"""
        # Create investigation with existing entry
        existing_history = ProbabilityHistoryEntry(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
            prior_probability=0.001,
            posterior_probability=0.01,
            likelihood=0.5,
            update_reason="initial",
            evidence_summary={"time_overlap": 0.6},
            observation_count=1,
        )
        
        existing_entry = EntryNodeProbability(
            fingerprint="FP123",
            nickname="Guard1",
            current_prior=0.001,
            current_posterior=0.01,
            last_updated=datetime.now(timezone.utc) - timedelta(hours=1),
            update_count=1,
            history=[existing_history],
            avg_time_overlap=0.6,
        )
        
        inv = Investigation(
            investigation_id="inv_test",
            entry_node_probabilities={"FP123": existing_entry},
        )
        
        mock_repository.get_by_id = MagicMock(return_value=inv)
        mock_repository.update = MagicMock(return_value=True)
        
        service = InvestigationService(mock_repository)
        result = service.update_entry_probability_incremental(
            investigation_id="inv_test",
            fingerprint="FP123",
            nickname="Guard1",
            new_prior=0.001,
            new_posterior=0.02,  # Higher than before
            new_likelihood=0.75,
            evidence_summary={"time_overlap": 0.85},
            exit_nodes_involved=["exit1", "exit2"],
        )
        
        entry = result.entry_node_probabilities["FP123"]
        
        # Should have updated values
        assert entry.current_posterior == 0.02
        assert entry.update_count == 2
        
        # Should have 2 history entries
        assert len(entry.history) == 2
        
        # Running average should be updated
        # (0.6 * 1 + 0.85) / 2 = 0.725
        assert 0.72 <= entry.avg_time_overlap <= 0.73
    
    def test_add_confidence_snapshot(self, mock_repository, sample_investigation):
        """Test adding confidence snapshot"""
        mock_repository.get_by_id = MagicMock(return_value=sample_investigation)
        mock_repository.update = MagicMock(return_value=True)
        
        service = InvestigationService(mock_repository)
        result = service.add_confidence_snapshot(
            investigation_id="inv_test123456",
            confidence_value=0.85,
            components={"quality": 0.9, "consistency": 0.8},
            trigger="analysis_run",
            note="High confidence after PCAP analysis",
        )
        
        assert result.current_confidence == 0.85
        assert result.current_confidence_level == ConfidenceLevel.VERY_HIGH
        assert len(result.confidence_timeline) == 2  # Original + new
    
    def test_save_and_load_bayesian_state(self, mock_repository):
        """Test saving and loading Bayesian state"""
        inv = Investigation(investigation_id="inv_test")
        mock_repository.get_by_id = MagicMock(return_value=inv)
        mock_repository.update = MagicMock(return_value=True)
        
        service = InvestigationService(mock_repository)
        
        # Save state
        priors = {"entry1": 0.001, "entry2": 0.002}
        observations = {"entry1": [{"ts": "2024-01-01"}]}
        stats = {"entry1": {"count": 1}}
        
        service.save_bayesian_state(
            investigation_id="inv_test",
            priors=priors,
            observations=observations,
            stats=stats,
        )
        
        # Verify state was saved
        assert inv.bayesian_state is not None
        assert inv.bayesian_state["priors"] == priors
        
        # Load state
        mock_repository.get_by_id = MagicMock(return_value=inv)
        loaded = service.load_bayesian_state("inv_test")
        
        assert loaded["priors"] == priors
    
    def test_get_probability_evolution(self, mock_repository):
        """Test getting probability evolution"""
        history1 = ProbabilityHistoryEntry(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=2),
            prior_probability=0.001,
            posterior_probability=0.01,
            likelihood=0.5,
            update_reason="initial",
            evidence_summary={"time_overlap": 0.6},
            observation_count=1,
        )
        
        history2 = ProbabilityHistoryEntry(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
            prior_probability=0.001,
            posterior_probability=0.02,
            likelihood=0.7,
            update_reason="update",
            evidence_summary={"time_overlap": 0.8},
            observation_count=2,
        )
        
        entry = EntryNodeProbability(
            fingerprint="FP123",
            nickname="Guard1",
            current_prior=0.001,
            current_posterior=0.02,
            last_updated=datetime.now(timezone.utc),
            update_count=2,
            history=[history1, history2],
        )
        
        inv = Investigation(
            investigation_id="inv_test",
            entry_node_probabilities={"FP123": entry},
        )
        
        mock_repository.get_by_id = MagicMock(return_value=inv)
        
        service = InvestigationService(mock_repository)
        evolution = service.get_probability_evolution("inv_test", "FP123")
        
        assert len(evolution) == 2
        assert evolution[0]["posterior"] == 0.01
        assert evolution[1]["posterior"] == 0.02
    
    def test_confidence_level_assessment(self, mock_repository):
        """Test confidence level assessment logic"""
        service = InvestigationService(mock_repository)
        
        # Very low: no observations
        level = service._assess_confidence_level(0, 0.5, 0.001)
        assert level == ConfidenceLevel.VERY_LOW
        
        # Higher confidence with more observations and certainty
        level = service._assess_confidence_level(15, 0.95, 0.001)
        assert level in [ConfidenceLevel.VERY_HIGH, ConfidenceLevel.HIGH]
        
        # Medium confidence
        level = service._assess_confidence_level(5, 0.6, 0.001)
        assert level in [ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH]


# ============================================================================
# ENUM TESTS
# ============================================================================

class TestEnums:
    """Tests for enum values"""
    
    def test_investigation_status_values(self):
        """Test all status values"""
        assert InvestigationStatus.ACTIVE.value == "active"
        assert InvestigationStatus.PAUSED.value == "paused"
        assert InvestigationStatus.COMPLETED.value == "completed"
        assert InvestigationStatus.ARCHIVED.value == "archived"
    
    def test_evidence_type_values(self):
        """Test evidence type values"""
        types = [e.value for e in EvidenceType]
        assert "temporal" in types
        assert "traffic" in types
        assert "pcap_flow" in types
        assert "forensic" in types
    
    def test_confidence_level_values(self):
        """Test confidence level values"""
        levels = [c.value for c in ConfidenceLevel]
        assert "very_high" in levels
        assert "high" in levels
        assert "medium" in levels
        assert "low" in levels
        assert "very_low" in levels


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""
    
    def test_empty_investigation_serialization(self):
        """Test empty investigation can be serialized"""
        inv = Investigation(investigation_id="empty_test")
        d = inv.to_dict()
        
        assert d["exit_node_observations"] == []
        assert d["entry_node_probabilities"] == {}
        assert d["confidence_timeline"] == []
    
    def test_large_history_handling(self):
        """Test handling of large history lists"""
        history_entries = []
        for i in range(100):
            entry = ProbabilityHistoryEntry(
                timestamp=datetime.now(timezone.utc) - timedelta(hours=i),
                prior_probability=0.001,
                posterior_probability=0.001 + (i * 0.0001),
                likelihood=0.5 + (i * 0.005),
                update_reason=f"update_{i}",
                evidence_summary={"time": 0.5 + i * 0.005},
                observation_count=i + 1,
            )
            history_entries.append(entry)
        
        entry_prob = EntryNodeProbability(
            fingerprint="FP123",
            nickname="Guard",
            current_prior=0.001,
            current_posterior=0.011,
            last_updated=datetime.now(timezone.utc),
            update_count=100,
            history=history_entries,
        )
        
        # Should serialize without issues
        d = entry_prob.to_dict()
        assert len(d["history"]) == 100
        
        # Should deserialize without issues
        restored = EntryNodeProbability.from_dict(d)
        assert len(restored.history) == 100
    
    def test_special_characters_in_description(self):
        """Test handling of special characters"""
        inv = Investigation(
            investigation_id="inv_special",
            target_description="Test with 'quotes', \"double\", and unicode: café → résumé",
            notes=[{"text": "Note with <html> & entities"}],
        )
        
        d = inv.to_dict()
        restored = Investigation.from_dict(d)
        
        assert "café" in restored.target_description
        assert "<html>" in restored.notes[0]["text"]
    
    def test_zero_probability_handling(self):
        """Test handling of zero probabilities"""
        entry = EntryNodeProbability(
            fingerprint="FP123",
            nickname="Guard",
            current_prior=0.0,
            current_posterior=0.0,
            last_updated=datetime.now(timezone.utc),
            update_count=0,
        )
        
        d = entry.to_dict()
        assert d["current_prior"] == 0.0
        assert d["current_posterior"] == 0.0
    
    def test_very_small_probability_handling(self):
        """Test handling of very small probabilities"""
        entry = EntryNodeProbability(
            fingerprint="FP123",
            nickname="Guard",
            current_prior=1e-10,
            current_posterior=1e-12,
            last_updated=datetime.now(timezone.utc),
            update_count=1,
        )
        
        d = entry.to_dict()
        restored = EntryNodeProbability.from_dict(d)
        
        # Should preserve precision
        assert restored.current_prior == 1e-10
        assert restored.current_posterior == 1e-12


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
