"""
Unit Tests for Forensic PCAP-TOR Integration

Tests the complete flow:
1. PCAP metadata extraction
2. Traffic characteristics analysis
3. TOR exit node correlation
4. PCAP support scoring
5. Confidence integration

Run with: python -m pytest tests/test_forensic_pcap_integration.py -v
"""

import pytest
from datetime import datetime, timedelta
from backend.app.forensic_pcap_integration import (
    ForensicTrafficMetadata,
    TrafficCharacteristics,
    TrafficPattern,
    ExitNodeActivityWindow,
    PCAPTORCorrelationEvidence,
    PCAPTORCorrelator,
    PCAPSupportScorer,
    PCAPSupportScore,
    EvidenceQuality,
    CorrelationConfidence,
    ForensicTrafficExtractor,
    generate_forensic_report,
)
from backend.app.forensic_confidence_integration import (
    PCAPEvidenceFactor,
    integrate_pcap_evidence,
    create_pcap_evidence_linkage,
    generate_pcap_evidence_summary,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_traffic_metadata():
    """Sample extracted PCAP metadata"""
    now = datetime.utcnow()
    return ForensicTrafficMetadata(
        case_id="CASE-2025-001",
        evidence_id="PCAP-20250101-001",
        source_file="evidence.pcap",
        capture_start=now - timedelta(hours=1),
        capture_end=now,
        total_packets=5000,
        total_bytes=2500000,
        unique_source_ips=3,
        unique_dest_ips=10,
        unique_flows=15,
        session_start=now - timedelta(minutes=55),
        session_end=now - timedelta(minutes=5),
    )


@pytest.fixture
def sample_traffic_characteristics():
    """Sample traffic characteristics"""
    return TrafficCharacteristics(
        dominant_pattern=TrafficPattern.BURSTY,
        patterns={
            TrafficPattern.BURSTY: 0.7,
            TrafficPattern.DOWNLOAD_HEAVY: 0.3,
        },
        inter_packet_times_ms=[5.2, 3.1, 8.5, 2.1, 6.3],
        mean_ipt_ms=5.04,
        std_ipt_ms=2.43,
        median_ipt_ms=5.2,
        burst_count=12,
        bursts=[],
        avg_burst_size=415.0,
        burst_frequency=0.04,  # 12 bursts over 50 minutes
        upload_bytes=800000,
        download_bytes=1700000,
        upload_packets=2000,
        download_packets=3000,
    )


@pytest.fixture
def sample_exit_node():
    """Sample TOR exit node with activity window"""
    now = datetime.utcnow()
    return ExitNodeActivityWindow(
        exit_fingerprint="A1B2C3D4E5F6G7H8I9J0K1L2M3N4O5P6",
        exit_ip="198.51.100.1",
        exit_country="US",
        consensus_valid_after=now - timedelta(hours=2),
        consensus_valid_until=now + timedelta(hours=1),
        bandwidth_capacity_bps=10000000,  # 10 Mbps
        is_exit_permitted=True,
        exit_ports=[80, 443, 8080],
    )


# ============================================================================
# METADATA EXTRACTION TESTS
# ============================================================================

class TestTrafficMetadata:
    """Test PCAP metadata extraction"""
    
    def test_metadata_creation(self, sample_traffic_metadata):
        """Create traffic metadata"""
        assert sample_traffic_metadata.case_id == "CASE-2025-001"
        assert sample_traffic_metadata.total_packets == 5000
        assert sample_traffic_metadata.total_bytes == 2500000
    
    def test_capture_duration(self, sample_traffic_metadata):
        """Calculate capture duration"""
        duration = sample_traffic_metadata.capture_duration_seconds
        assert duration == 3600.0  # 1 hour
    
    def test_session_duration(self, sample_traffic_metadata):
        """Calculate session duration"""
        duration = sample_traffic_metadata.session_duration_seconds
        assert 2900 < duration < 3300  # Approximately 50 minutes
    
    def test_metadata_serialization(self, sample_traffic_metadata):
        """Convert metadata to dictionary"""
        data = sample_traffic_metadata.to_dict()
        assert data["case_id"] == "CASE-2025-001"
        assert data["total_packets"] == 5000
        assert "capture_duration_seconds" in data
        assert "session_duration_seconds" in data


class TestTrafficCharacteristics:
    """Test traffic characteristics analysis"""
    
    def test_characteristics_creation(self, sample_traffic_characteristics):
        """Create traffic characteristics"""
        assert sample_traffic_characteristics.dominant_pattern == TrafficPattern.BURSTY
        assert sample_traffic_characteristics.burst_count == 12
        assert sample_traffic_characteristics.mean_ipt_ms > 0
    
    def test_directionality_ratio(self, sample_traffic_characteristics):
        """Calculate upload-to-total ratio"""
        ratio = sample_traffic_characteristics.directionality_ratio
        assert ratio == 0.32  # 800000 / 2500000
    
    def test_total_bytes(self, sample_traffic_characteristics):
        """Calculate total bytes"""
        total = sample_traffic_characteristics.total_bytes
        assert total == 2500000
    
    def test_characteristics_serialization(self, sample_traffic_characteristics):
        """Convert characteristics to dictionary"""
        data = sample_traffic_characteristics.to_dict()
        assert "dominant_pattern" in data
        assert "mean_ipt_ms" in data
        assert "burst_frequency" in data


# ============================================================================
# CORRELATION TESTS
# ============================================================================

class TestPCAPTORCorrelator:
    """Test PCAP-TOR correlation engine"""
    
    def test_correlator_creation(self):
        """Create correlator instance"""
        correlator = PCAPTORCorrelator()
        assert correlator is not None
    
    def test_correlation_with_overlap(
        self,
        sample_traffic_metadata,
        sample_traffic_characteristics,
        sample_exit_node,
    ):
        """Correlate traffic with overlapping exit node"""
        correlator = PCAPTORCorrelator()
        
        correlations = correlator.correlate(
            traffic_metadata=sample_traffic_metadata,
            traffic_characteristics=sample_traffic_characteristics,
            exit_nodes=[sample_exit_node],
            confidence_threshold=0.3,
        )
        
        assert len(correlations) > 0
        correlation = correlations[0]
        assert correlation.exit_node_fingerprint == sample_exit_node.exit_fingerprint
        assert correlation.overlap_ratio > 0
    
    def test_correlation_no_overlap(
        self,
        sample_traffic_metadata,
        sample_traffic_characteristics,
    ):
        """No correlation with non-overlapping exit node"""
        correlator = PCAPTORCorrelator()
        
        # Exit node that doesn't overlap with traffic
        non_overlapping_node = ExitNodeActivityWindow(
            exit_fingerprint="X1Y2Z3",
            exit_ip="192.0.2.1",
            exit_country="RU",
            consensus_valid_after=datetime.utcnow() + timedelta(days=1),
            consensus_valid_until=datetime.utcnow() + timedelta(days=2),
            bandwidth_capacity_bps=5000000,
            is_exit_permitted=True,
            exit_ports=[80, 443],
        )
        
        correlations = correlator.correlate(
            traffic_metadata=sample_traffic_metadata,
            traffic_characteristics=sample_traffic_characteristics,
            exit_nodes=[non_overlapping_node],
        )
        
        assert len(correlations) == 0
    
    def test_timing_alignment_scoring(self, sample_exit_node):
        """Test timing alignment score calculation"""
        correlator = PCAPTORCorrelator()
        
        # Full overlap
        score = correlator._score_timing_alignment(
            traffic_duration=3600,
            overlap_seconds=3600,
            overlap_ratio=1.0,
        )
        assert score == 1.0
        
        # 50% overlap
        score = correlator._score_timing_alignment(
            traffic_duration=3600,
            overlap_seconds=1800,
            overlap_ratio=0.5,
        )
        assert score == 0.6
        
        # 20% overlap
        score = correlator._score_timing_alignment(
            traffic_duration=3600,
            overlap_seconds=720,
            overlap_ratio=0.2,
        )
        assert score == 0.2
    
    def test_pattern_match_scoring(self):
        """Test traffic pattern match scoring"""
        correlator = PCAPTORCorrelator()
        exit_node = ExitNodeActivityWindow(
            exit_fingerprint="ABC123",
            exit_ip="10.0.0.1",
            exit_country="US",
            consensus_valid_after=datetime.utcnow(),
            consensus_valid_until=datetime.utcnow() + timedelta(hours=1),
            bandwidth_capacity_bps=10000000,
            is_exit_permitted=True,
            exit_ports=[80, 443],
        )
        
        bursty_characteristics = TrafficCharacteristics(
            dominant_pattern=TrafficPattern.BURSTY,
            patterns={TrafficPattern.BURSTY: 1.0},
            inter_packet_times_ms=[1, 2, 3],
            mean_ipt_ms=50,
            std_ipt_ms=10,
            median_ipt_ms=50,
            burst_count=5,
            bursts=[],
            avg_burst_size=100,
            burst_frequency=0.01,
            upload_bytes=100000,
            download_bytes=500000,
            upload_packets=100,
            download_packets=500,
        )
        
        # Bursty traffic should score better
        score = correlator._score_pattern_match(bursty_characteristics, exit_node)
        assert score > 0.6


# ============================================================================
# SCORING TESTS
# ============================================================================

class TestPCAPSupportScorer:
    """Test PCAP support scoring"""
    
    def test_scorer_creation(self):
        """Create scorer instance"""
        scorer = PCAPSupportScorer()
        assert scorer is not None
    
    def test_scoring_with_correlations(
        self,
        sample_traffic_metadata,
        sample_traffic_characteristics,
        sample_exit_node,
    ):
        """Score PCAP evidence with correlations"""
        # Create correlations
        correlator = PCAPTORCorrelator()
        correlations = correlator.correlate(
            traffic_metadata=sample_traffic_metadata,
            traffic_characteristics=sample_traffic_characteristics,
            exit_nodes=[sample_exit_node],
        )
        
        # Score them
        scorer = PCAPSupportScorer()
        score = scorer.compute_pcap_support_score(correlations)
        
        assert score.total_correlations > 0
        assert 0 <= score.pcap_support_factor <= 1.0
        assert len(score.recommendations) > 0
    
    def test_scoring_empty_correlations(self):
        """Score with no correlations"""
        scorer = PCAPSupportScorer()
        score = scorer.compute_pcap_support_score([])
        
        assert score.total_correlations == 0
        assert score.pcap_support_factor == 0.0
        assert len(score.recommendations) > 0


# ============================================================================
# CONFIDENCE INTEGRATION TESTS
# ============================================================================

class TestPCAPEvidenceFactor:
    """Test PCAP evidence factor creation"""
    
    def test_factor_from_support_score(self):
        """Create factor from support score"""
        support_score = PCAPSupportScore(
            case_id="CASE-001",
            pcap_evidence_id="PCAP-001",
            top_correlations=[],
            total_correlations=3,
            strongest_correlation_score=0.75,
            mean_correlation_score=0.65,
            std_correlation_score=0.08,
            evidence_completeness=0.8,
            evidence_consistency=0.85,
            evidence_reliability=0.75,
            pcap_support_factor=0.70,
            singular_strong_match=True,
            multiple_consistent_matches=False,
            ambiguous_matches=False,
            recommendations=[],
            data_quality_notes=[],
        )
        
        factor = PCAPEvidenceFactor.from_pcap_score(support_score)
        
        assert factor.pcap_evidence_id == "PCAP-001"
        assert factor.base_strength == 0.75
        assert factor.confidence_boost > 0
    
    def test_factor_serialization(self):
        """Convert factor to dictionary"""
        from backend.app.forensic_confidence_integration import PCAPEvidenceType
        
        factor = PCAPEvidenceFactor(
            pcap_evidence_id="PCAP-001",
            evidence_type=PCAPEvidenceType.SINGULAR_STRONG,
            base_strength=0.75,
            confidence_boost=0.15,
            number_of_correlations=3,
            strongest_correlation_score=0.75,
            evidence_completeness=0.8,
            is_singular_strong_match=True,
            is_multiple_consistent=False,
            is_ambiguous=False,
        )
        
        data = factor.to_dict()
        assert data["pcap_evidence_id"] == "PCAP-001"
        assert "confidence_boost" in data


class TestConfidenceIntegration:
    """Test confidence integration"""
    
    def test_pcap_evidence_integration(self):
        """Integrate PCAP evidence into confidence"""
        support_score = PCAPSupportScore(
            case_id="CASE-001",
            pcap_evidence_id="PCAP-001",
            top_correlations=[],
            total_correlations=2,
            strongest_correlation_score=0.80,
            mean_correlation_score=0.70,
            std_correlation_score=0.10,
            evidence_completeness=0.85,
            evidence_consistency=0.90,
            evidence_reliability=0.80,
            pcap_support_factor=0.75,
            singular_strong_match=True,
            multiple_consistent_matches=False,
            ambiguous_matches=False,
            recommendations=["Test recommendation"],
            data_quality_notes=[],
        )
        
        pcap_factor = PCAPEvidenceFactor.from_pcap_score(support_score)
        
        result = integrate_pcap_evidence(
            base_confidence=0.60,
            pcap_factor=pcap_factor,
            existing_evidence_count=2,
        )
        
        assert result.base_confidence == 0.60
        assert result.enhanced_confidence > result.base_confidence
        assert result.pcap_confidence_boost > 0
    
    def test_diminishing_returns(self):
        """High confidence limits PCAP boost"""
        support_score = PCAPSupportScore(
            case_id="CASE-001",
            pcap_evidence_id="PCAP-001",
            top_correlations=[],
            total_correlations=3,
            strongest_correlation_score=0.90,
            mean_correlation_score=0.85,
            std_correlation_score=0.05,
            evidence_completeness=0.95,
            evidence_consistency=0.95,
            evidence_reliability=0.90,
            pcap_support_factor=0.85,
            singular_strong_match=True,
            multiple_consistent_matches=False,
            ambiguous_matches=False,
            recommendations=[],
            data_quality_notes=[],
        )
        
        pcap_factor = PCAPEvidenceFactor.from_pcap_score(support_score)
        
        # Low base confidence → large boost
        low_result = integrate_pcap_evidence(
            base_confidence=0.30,
            pcap_factor=pcap_factor,
            existing_evidence_count=1,
        )
        
        # High base confidence → small boost
        high_result = integrate_pcap_evidence(
            base_confidence=0.80,
            pcap_factor=pcap_factor,
            existing_evidence_count=5,
        )
        
        # Higher base should have smaller boost
        assert low_result.pcap_confidence_boost > high_result.pcap_confidence_boost


# ============================================================================
# EVIDENCE LINKAGE TESTS
# ============================================================================

class TestEvidenceLinkage:
    """Test chain-of-custody tracking"""
    
    def test_linkage_creation(
        self,
        sample_traffic_metadata,
        sample_traffic_characteristics,
        sample_exit_node,
    ):
        """Create evidence linkage"""
        # Create a correlation
        correlator = PCAPTORCorrelator()
        correlations = correlator.correlate(
            traffic_metadata=sample_traffic_metadata,
            traffic_characteristics=sample_traffic_characteristics,
            exit_nodes=[sample_exit_node],
        )
        
        # Create support score
        scorer = PCAPSupportScorer()
        support_score = scorer.compute_pcap_support_score(correlations)
        
        # Create linkage
        linkage = create_pcap_evidence_linkage(
            case_id="CASE-001",
            pcap_evidence_id="PCAP-001",
            traffic_metadata=sample_traffic_metadata,
            correlations=correlations,
            pcap_support_score=support_score,
        )
        
        assert linkage.case_id == "CASE-001"
        assert linkage.pcap_evidence_id == "PCAP-001"
        assert len(linkage.correlated_exit_nodes) > 0
    
    def test_forensic_chain_generation(
        self,
        sample_traffic_metadata,
        sample_traffic_characteristics,
        sample_exit_node,
    ):
        """Generate chain-of-custody document"""
        correlator = PCAPTORCorrelator()
        correlations = correlator.correlate(
            traffic_metadata=sample_traffic_metadata,
            traffic_characteristics=sample_traffic_characteristics,
            exit_nodes=[sample_exit_node],
        )
        
        scorer = PCAPSupportScorer()
        support_score = scorer.compute_pcap_support_score(correlations)
        
        linkage = create_pcap_evidence_linkage(
            case_id="CASE-001",
            pcap_evidence_id="PCAP-001",
            traffic_metadata=sample_traffic_metadata,
            correlations=correlations,
            pcap_support_score=support_score,
        )
        
        chain = linkage.to_forensic_chain()
        
        assert "case_id" in chain
        assert "pcap_evidence" in chain
        assert "tor_correlations" in chain
        assert "chain_of_custody" in chain


# ============================================================================
# FORENSIC REPORT TESTS
# ============================================================================

class TestForensicReporting:
    """Test forensic report generation"""
    
    def test_report_generation(
        self,
        sample_traffic_metadata,
        sample_traffic_characteristics,
        sample_exit_node,
    ):
        """Generate complete forensic report"""
        correlator = PCAPTORCorrelator()
        correlations = correlator.correlate(
            traffic_metadata=sample_traffic_metadata,
            traffic_characteristics=sample_traffic_characteristics,
            exit_nodes=[sample_exit_node],
        )
        
        scorer = PCAPSupportScorer()
        support_score = scorer.compute_pcap_support_score(correlations)
        
        report = generate_forensic_report(
            traffic_metadata=sample_traffic_metadata,
            pcap_correlations=correlations,
            pcap_support_score=support_score,
            investigator_name="Detective Smith",
            investigator_agency="Cyber Crimes Unit",
            evidence_custodian="Evidence Tech Johnson",
        )
        
        assert report.case_id == sample_traffic_metadata.case_id
        assert report.investigator_name == "Detective Smith"
        assert len(report.analysis_limitations) > 0
        assert report.uncertainty_statement is not None
    
    def test_report_serialization(
        self,
        sample_traffic_metadata,
        sample_traffic_characteristics,
        sample_exit_node,
    ):
        """Serialize report to dictionary"""
        correlator = PCAPTORCorrelator()
        correlations = correlator.correlate(
            traffic_metadata=sample_traffic_metadata,
            traffic_characteristics=sample_traffic_characteristics,
            exit_nodes=[sample_exit_node],
        )
        
        scorer = PCAPSupportScorer()
        support_score = scorer.compute_pcap_support_score(correlations)
        
        report = generate_forensic_report(
            traffic_metadata=sample_traffic_metadata,
            pcap_correlations=correlations,
            pcap_support_score=support_score,
            investigator_name="Detective Smith",
            investigator_agency="Cyber Crimes Unit",
            evidence_custodian="Evidence Tech Johnson",
        )
        
        data = report.to_dict()
        assert "case_id" in data
        assert "traffic_evidence" in data
        assert "pcap_correlations" in data
        assert "investigator" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
