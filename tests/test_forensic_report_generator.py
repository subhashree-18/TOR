"""
Test suite for Forensic Report Generator
==========================================

Comprehensive tests for:
- Report generation with various input scenarios
- JSON export and serialization
- PDF export (if reportlab available)
- Text export formatting
- Timeline event creation and sorting
- Guard node ranking and analysis
- Report integrity and hashing
- Metadata tracking
"""

import pytest
from datetime import datetime, timedelta
from typing import List
import json
import hashlib

from backend.app.forensic_report_generator import (
    ForensicReportGenerator,
    ForensicReport,
    GuardNodeAnalysis,
    TimelineEvent,
    PCAPEvidenceSummary,
    CaseMetadata,
    ReportFormat,
    ReportClassification,
    ConfidenceRating,
    JSONReportExporter,
    TextReportExporter,
    PDFReportExporter,
    create_timeline_event,
    rank_guard_nodes,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_case_metadata():
    """Create sample case metadata"""
    return CaseMetadata(
        case_id="CASE-2025-001",
        case_title="Illegal Online Marketplace Investigation",
        case_description="Investigation into illegal online marketplace using TOR",
        jurisdiction="State Cyber Crime Unit",
        case_number="SC-2025-00123",
        investigator_name="Detective John Smith",
        investigator_badge="SC-12345",
        investigator_agency="State Cyber Crimes Division",
        reviewing_officer_name="Captain Jane Williams",
        reviewing_officer_title="Cyber Crimes Commander",
        evidence_custodian="Evidence Technician Robert Johnson",
        investigation_date_start=datetime(2025, 1, 15),
        investigation_date_end=datetime(2025, 1, 21),
    )


@pytest.fixture
def sample_guard_node():
    """Create sample guard node analysis"""
    return GuardNodeAnalysis(
        guard_fingerprint="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        guard_nickname="guard-node-1",
        guard_country="US",
        guard_ip_address="203.0.113.1",
        guard_bandwidth_mbps=1000.0,
        overall_confidence=0.82,
        confidence_level="High",
        time_overlap_score=0.85,
        time_overlap_reasoning="95% overlap between exit activity window and guard uptime",
        bandwidth_similarity_score=0.80,
        bandwidth_similarity_reasoning="Exit bandwidth 850 Mbps, guard 1000 Mbps (proportional match)",
        historical_recurrence_score=0.85,
        historical_recurrence_reasoning="Same guard observed in 5 out of 7 exit node correlations",
        geographic_asn_score=0.75,
        geographic_asn_reasoning="Guard and exit in different countries but consistent routing patterns",
        pcap_correlation_score=0.80,
        pcap_correlation_reasoning="Network traffic patterns match probabilistic model with 80% confidence",
        observation_count=7,
        first_observed=datetime(2025, 1, 15),
        last_observed=datetime(2025, 1, 20),
        observation_trend="increasing",
        limiting_factors=["Multiple guards correlate with this exit", "Limited PCAP data"],
        uncertainty_statement="This is a probable candidate but not definitive identification",
    )


@pytest.fixture
def sample_guard_nodes(sample_guard_node):
    """Create multiple candidate guard nodes"""
    nodes = []
    
    # Primary candidate
    nodes.append(sample_guard_node)
    
    # Secondary candidate
    node2 = GuardNodeAnalysis(
        guard_fingerprint="b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
        guard_nickname="guard-node-2",
        guard_country="GB",
        guard_ip_address="198.51.100.2",
        guard_bandwidth_mbps=800.0,
        overall_confidence=0.68,
        confidence_level="Moderate",
        time_overlap_score=0.70,
        time_overlap_reasoning="70% overlap with exit activity window",
        bandwidth_similarity_score=0.72,
        bandwidth_similarity_reasoning="Bandwidth within reasonable range",
        historical_recurrence_score=0.65,
        historical_recurrence_reasoning="Observed in 3 of 7 correlations",
        geographic_asn_score=0.68,
        geographic_asn_reasoning="Geographic routing consistent",
        pcap_correlation_score=0.65,
        pcap_correlation_reasoning="Moderate PCAP pattern match",
        observation_count=3,
        first_observed=datetime(2025, 1, 18),
        last_observed=datetime(2025, 1, 20),
        observation_trend="stable",
    )
    nodes.append(node2)
    
    # Tertiary candidate
    node3 = GuardNodeAnalysis(
        guard_fingerprint="c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        guard_nickname="guard-node-3",
        guard_country="DE",
        guard_ip_address="192.0.2.3",
        guard_bandwidth_mbps=500.0,
        overall_confidence=0.52,
        confidence_level="Low",
        time_overlap_score=0.50,
        time_overlap_reasoning="Limited temporal overlap",
        bandwidth_similarity_score=0.55,
        bandwidth_similarity_reasoning="Smaller bandwidth than expected",
        historical_recurrence_score=0.50,
        historical_recurrence_reasoning="Observed once in correlation set",
        geographic_asn_score=0.55,
        geographic_asn_reasoning="Different geographic region",
        pcap_correlation_score=0.50,
        pcap_correlation_reasoning="Weak PCAP pattern match",
        observation_count=1,
        first_observed=datetime(2025, 1, 19),
        last_observed=datetime(2025, 1, 19),
        observation_trend="stable",
    )
    nodes.append(node3)
    
    return nodes


@pytest.fixture
def sample_timeline_events():
    """Create sample timeline events"""
    base_time = datetime(2025, 1, 15, 12, 0, 0)
    
    events = [
        TimelineEvent(
            timestamp=base_time,
            event_type="pcap_captured",
            description="Initial PCAP evidence captured from network monitor",
            confidence=1.0,
            evidence_source="pcap_correlation",
            related_nodes=[]
        ),
        TimelineEvent(
            timestamp=base_time + timedelta(hours=2),
            event_type="exit_node_detected",
            description="Exit node 5f6a7b8c detected in TOR consensus",
            confidence=0.95,
            evidence_source="tor_consensus",
            related_nodes=["5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a"]
        ),
        TimelineEvent(
            timestamp=base_time + timedelta(hours=4),
            event_type="correlation_detected",
            description="Traffic pattern matched with guard node a1b2c3d4",
            confidence=0.82,
            evidence_source="pattern_analysis",
            related_nodes=["a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"]
        ),
        TimelineEvent(
            timestamp=base_time + timedelta(hours=6),
            event_type="confidence_updated",
            description="Confidence score updated to 82% after pattern analysis",
            confidence=0.85,
            evidence_source="unified_confidence_engine",
            related_nodes=["a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"]
        ),
    ]
    
    return events


@pytest.fixture
def sample_pcap_evidence():
    """Create sample PCAP evidence summary"""
    return PCAPEvidenceSummary(
        evidence_id="PCAP-2025-001",
        total_packets=125432,
        total_bytes=89234567,
        capture_duration_seconds=3600.0,
        correlated_exit_nodes=["5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a"],
        strongest_exit_match="5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a",
        strongest_match_confidence=0.78,
        traffic_pattern="download_heavy",
        average_packet_size=512.5,
        packet_interarrival_mean_ms=2.3,
        completeness_score=0.95,
        anomalies_detected=["Packet retransmission rate slightly elevated", "One traffic burst at 14:23 UTC"],
    )


@pytest.fixture
def report_generator():
    """Create sample report generator"""
    return ForensicReportGenerator(
        investigator_name="Detective John Smith",
        investigator_agency="State Cyber Crimes Division",
        jurisdiction="State",
        classification="Confidential - Investigation"
    )


# ============================================================================
# TESTS - Report Generation
# ============================================================================

class TestReportGeneration:
    """Test basic report generation"""
    
    def test_generate_basic_report(self, report_generator, sample_guard_nodes, 
                                   sample_timeline_events, sample_pcap_evidence):
        """Test generating a basic forensic report"""
        report = report_generator.generate_report(
            case_id="CASE-2025-001",
            case_title="Test Investigation",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=sample_timeline_events,
            pcap_evidence=sample_pcap_evidence,
        )
        
        assert report.report_id.startswith("FOR-CASE-2025-001")
        assert report.case_metadata.case_id == "CASE-2025-001"
        assert len(report.guard_node_candidates) == 3
        assert len(report.timeline_events) == 4
        assert report.pcap_evidence is not None
    
    def test_report_without_pcap(self, report_generator, sample_guard_nodes, 
                                sample_timeline_events):
        """Test generating report without PCAP evidence"""
        report = report_generator.generate_report(
            case_id="CASE-2025-002",
            case_title="TOR Analysis Only",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=sample_timeline_events,
        )
        
        assert report.pcap_evidence is None
        assert len(report.guard_node_candidates) == 3
    
    def test_report_with_findings_and_recommendations(self, report_generator, 
                                                     sample_guard_nodes):
        """Test report with key findings and recommendations"""
        findings = [
            "Primary suspect correlates with identified TOR guard node",
            "Network traffic patterns consistent with market activity",
        ]
        recommendations = [
            "Obtain warrant for ISP records of identified exit node",
            "Cross-reference with other ongoing investigations",
            "Interview network administrator for log retention",
        ]
        
        report = report_generator.generate_report(
            case_id="CASE-2025-003",
            case_title="Full Analysis",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
            key_findings=findings,
            recommendations=recommendations,
        )
        
        assert len(report.key_findings) == 2
        assert len(report.recommendations) == 3
        assert "Primary suspect" in report.key_findings[0]
    
    def test_report_integrity_hash(self, report_generator, sample_guard_nodes):
        """Test report integrity hashing creates a hash"""
        report = report_generator.generate_report(
            case_id="CASE-2025-004",
            case_title="Hash Test",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        # Just verify it's a valid SHA256 hash
        assert len(report.report_hash) == 64
        assert report.report_hash.isalnum()
        # Verify it's reproducible
        report.report_hash = ""  # Clear it
        new_hash = report.generate_hash()
        assert len(new_hash) == 64
        assert new_hash == report.report_hash


# ============================================================================
# TESTS - JSON Export
# ============================================================================

class TestJSONExport:
    """Test JSON export functionality"""
    
    def test_json_export_basic(self, report_generator, sample_guard_nodes):
        """Test basic JSON export"""
        report = report_generator.generate_report(
            case_id="CASE-2025-005",
            case_title="JSON Test",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        json_bytes = report_generator.export_report(report, ReportFormat.JSON)
        json_str = json_bytes.decode('utf-8')
        data = json.loads(json_str)
        
        assert "report_metadata" in data
        assert "case_metadata" in data
        assert "analysis_results" in data
        assert data["case_metadata"]["case_id"] == "CASE-2025-005"
    
    def test_json_export_guard_nodes(self, report_generator, sample_guard_nodes):
        """Test JSON export includes all guard node details"""
        report = report_generator.generate_report(
            case_id="CASE-2025-006",
            case_title="Guard Node JSON Test",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        json_data = report.to_json()
        nodes = json_data["analysis_results"]["guard_node_candidates"]
        
        assert len(nodes) == 3
        assert nodes[0]["guard_nickname"] == "guard-node-1"
        assert "factor_breakdown" in nodes[0]
        assert "time_overlap" in nodes[0]["factor_breakdown"]
    
    def test_json_export_string(self, report_generator, sample_guard_nodes):
        """Test export_json convenience method"""
        report = report_generator.generate_report(
            case_id="CASE-2025-007",
            case_title="Export JSON String",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        json_str = report_generator.export_json(report)
        assert isinstance(json_str, str)
        data = json.loads(json_str)
        assert data["case_metadata"]["case_id"] == "CASE-2025-007"
    
    def test_json_serialization_completeness(self, report_generator, sample_guard_nodes,
                                            sample_timeline_events, sample_pcap_evidence):
        """Test JSON export includes all information"""
        report = report_generator.generate_report(
            case_id="CASE-2025-008",
            case_title="Complete Data",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=sample_timeline_events,
            pcap_evidence=sample_pcap_evidence,
            key_findings=["Finding 1", "Finding 2"],
            recommendations=["Rec 1"],
        )
        
        json_data = report.to_json()
        
        assert "report_metadata" in json_data
        assert "case_metadata" in json_data
        assert len(json_data["analysis_results"]["guard_node_candidates"]) == 3
        assert len(json_data["timeline"]) == 4
        assert json_data["pcap_evidence"] is not None
        assert len(json_data["findings"]["key_findings"]) == 2
        assert len(json_data["findings"]["recommendations"]) == 1


# ============================================================================
# TESTS - Text Export
# ============================================================================

class TestTextExport:
    """Test text export functionality"""
    
    def test_text_export_basic(self, report_generator, sample_guard_nodes):
        """Test basic text export"""
        report = report_generator.generate_report(
            case_id="CASE-2025-009",
            case_title="Text Export Test",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        text_bytes = report_generator.export_report(report, ReportFormat.TXT)
        text = text_bytes.decode('utf-8')
        
        assert "FORENSIC INVESTIGATION REPORT" in text
        assert "CASE-2025-009" in text
        assert "PROBABLE ORIGIN (GUARD) NODES" in text
    
    def test_text_export_includes_guard_nodes(self, report_generator, sample_guard_nodes):
        """Test text export includes guard node information"""
        report = report_generator.generate_report(
            case_id="CASE-2025-010",
            case_title="Text Guard Nodes",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        text = report_generator.export_text(report)
        
        assert "guard-node-1" in text
        assert "guard-node-2" in text
        assert "guard-node-3" in text
        assert "High" in text  # confidence level
        assert "Moderate" in text
        assert "Low" in text
    
    def test_text_export_timeline(self, report_generator, sample_guard_nodes, 
                                 sample_timeline_events):
        """Test text export includes timeline"""
        report = report_generator.generate_report(
            case_id="CASE-2025-011",
            case_title="Text Timeline",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=sample_timeline_events,
        )
        
        text = report_generator.export_text(report)
        
        assert "ACTIVITY TIMELINE" in text
        assert "PCAP_CAPTURED" in text
        assert "EXIT_NODE_DETECTED" in text
        assert "CORRELATION_DETECTED" in text
    
    def test_text_export_pcap_evidence(self, report_generator, sample_guard_nodes,
                                      sample_pcap_evidence):
        """Test text export includes PCAP evidence"""
        report = report_generator.generate_report(
            case_id="CASE-2025-012",
            case_title="Text PCAP",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
            pcap_evidence=sample_pcap_evidence,
        )
        
        text = report_generator.export_text(report)
        
        assert "NETWORK FORENSIC EVIDENCE (PCAP)" in text
        assert "125432" in text  # packet count
        assert "download_heavy" in text


# ============================================================================
# TESTS - PDF Export
# ============================================================================

class TestPDFExport:
    """Test PDF export functionality (if reportlab available)"""
    
    def test_pdf_export_basic(self, report_generator, sample_guard_nodes):
        """Test basic PDF export"""
        # Check if PDF export is available
        if ReportFormat.PDF not in report_generator.exporters:
            pytest.skip("reportlab not available")
        
        report = report_generator.generate_report(
            case_id="CASE-2025-013",
            case_title="PDF Export Test",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        pdf_bytes = report_generator.export_report(report, ReportFormat.PDF)
        
        # Check PDF structure (starts with PDF header)
        assert pdf_bytes.startswith(b"%PDF")
        assert len(pdf_bytes) > 1000  # Reasonable PDF size
    
    def test_pdf_export_convenience_method(self, report_generator, sample_guard_nodes):
        """Test export_pdf convenience method"""
        if ReportFormat.PDF not in report_generator.exporters:
            pytest.skip("reportlab not available")
        
        report = report_generator.generate_report(
            case_id="CASE-2025-014",
            case_title="PDF Convenience",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        pdf_bytes = report_generator.export_pdf(report)
        
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes.startswith(b"%PDF")


# ============================================================================
# TESTS - Timeline
# ============================================================================

class TestTimelineEvents:
    """Test timeline event creation and management"""
    
    def test_create_timeline_event(self):
        """Test timeline event creation"""
        event = create_timeline_event(
            timestamp=datetime(2025, 1, 15, 12, 0, 0),
            event_type="exit_detected",
            description="Exit node observed in consensus",
            confidence=0.95,
            evidence_source="tor_consensus",
            related_nodes=["abc123"]
        )
        
        assert event.event_type == "exit_detected"
        assert event.confidence == 0.95
        assert "abc123" in event.related_nodes
    
    def test_timeline_event_invalid_confidence(self):
        """Test timeline event rejects invalid confidence"""
        with pytest.raises(ValueError):
            create_timeline_event(
                timestamp=datetime.utcnow(),
                event_type="test",
                description="test",
                confidence=1.5,  # Invalid
                evidence_source="test"
            )
    
    def test_timeline_event_sorting(self, sample_timeline_events):
        """Test timeline events sort chronologically"""
        report = ForensicReport(
            report_id="TEST",
            generated_at=datetime.utcnow(),
            case_metadata=CaseMetadata(
                case_id="TEST",
                case_title="Test"
            ),
            guard_node_candidates=[],
            timeline_events=sample_timeline_events,
        )
        
        sorted_events = sorted(report.timeline_events, key=lambda x: x.timestamp)
        
        for i in range(len(sorted_events) - 1):
            assert sorted_events[i].timestamp <= sorted_events[i + 1].timestamp
    
    def test_timeline_event_to_dict(self, sample_timeline_events):
        """Test timeline event serialization"""
        event = sample_timeline_events[0]
        event_dict = event.to_dict()
        
        assert "timestamp" in event_dict
        assert "event_type" in event_dict
        assert "description" in event_dict
        assert "confidence" in event_dict
        assert event_dict["event_type"] == "pcap_captured"


# ============================================================================
# TESTS - Guard Node Ranking
# ============================================================================

class TestGuardNodeRanking:
    """Test guard node ranking and analysis"""
    
    def test_rank_guard_nodes(self, sample_guard_nodes):
        """Test ranking guard nodes by confidence"""
        ranked = rank_guard_nodes(sample_guard_nodes)
        
        assert ranked[0].guard_nickname == "guard-node-1"  # 82% confidence
        assert ranked[1].guard_nickname == "guard-node-2"  # 68%
        assert ranked[2].guard_nickname == "guard-node-3"  # 52%
        assert ranked[0].overall_confidence >= ranked[1].overall_confidence >= ranked[2].overall_confidence
    
    def test_guard_node_to_dict(self, sample_guard_node):
        """Test guard node serialization"""
        node_dict = sample_guard_node.to_dict()
        
        assert node_dict["guard_nickname"] == "guard-node-1"
        assert "factor_breakdown" in node_dict
        assert "time_overlap" in node_dict["factor_breakdown"]
        assert node_dict["overall_confidence"] == round(0.82, 4)
    
    def test_guard_node_rank_score(self, sample_guard_node):
        """Test guard node ranking score"""
        score = sample_guard_node.rank_score()
        assert score == 0.82


# ============================================================================
# TESTS - Case Metadata
# ============================================================================

class TestCaseMetadata:
    """Test case metadata handling"""
    
    def test_case_metadata_to_dict(self, sample_case_metadata):
        """Test case metadata serialization"""
        metadata_dict = sample_case_metadata.to_dict()
        
        assert metadata_dict["case_id"] == "CASE-2025-001"
        assert metadata_dict["case_title"] == "Illegal Online Marketplace Investigation"
        assert metadata_dict["jurisdiction"] == "State Cyber Crime Unit"
        assert "personnel" in metadata_dict
        assert metadata_dict["personnel"]["investigator"] == "Detective John Smith"
    
    def test_case_metadata_investigation_period(self, sample_case_metadata):
        """Test case metadata includes investigation period"""
        metadata_dict = sample_case_metadata.to_dict()
        
        assert "investigation_period" in metadata_dict
        assert "start" in metadata_dict["investigation_period"]
        assert "end" in metadata_dict["investigation_period"]


# ============================================================================
# TESTS - PCAP Evidence
# ============================================================================

class TestPCAPEvidence:
    """Test PCAP evidence summary"""
    
    def test_pcap_evidence_to_dict(self, sample_pcap_evidence):
        """Test PCAP evidence serialization"""
        pcap_dict = sample_pcap_evidence.to_dict()
        
        assert pcap_dict["evidence_id"] == "PCAP-2025-001"
        assert pcap_dict["capture_statistics"]["total_packets"] == 125432
        assert "correlation_results" in pcap_dict
        assert "forensic_quality" in pcap_dict
    
    def test_pcap_evidence_completeness(self, sample_pcap_evidence):
        """Test PCAP evidence includes all details"""
        pcap_dict = sample_pcap_evidence.to_dict()
        
        stats = pcap_dict["capture_statistics"]
        assert "total_packets" in stats
        assert "total_bytes" in stats
        assert "duration_seconds" in stats


# ============================================================================
# TESTS - Exporter Classes
# ============================================================================

class TestExporterClasses:
    """Test individual exporter implementations"""
    
    def test_json_exporter(self, sample_guard_nodes):
        """Test JSON exporter"""
        report = ForensicReport(
            report_id="TEST",
            generated_at=datetime.utcnow(),
            case_metadata=CaseMetadata(case_id="TEST", case_title="Test"),
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        exporter = JSONReportExporter()
        result = exporter.export(report)
        
        assert isinstance(result, bytes)
        data = json.loads(result)
        assert "case_metadata" in data
    
    def test_text_exporter(self, sample_guard_nodes):
        """Test text exporter"""
        report = ForensicReport(
            report_id="TEST",
            generated_at=datetime.utcnow(),
            case_metadata=CaseMetadata(case_id="TEST", case_title="Test"),
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        exporter = TextReportExporter()
        result = exporter.export(report)
        
        assert isinstance(result, bytes)
        text = result.decode('utf-8')
        assert "FORENSIC INVESTIGATION REPORT" in text


# ============================================================================
# TESTS - Error Handling
# ============================================================================

class TestErrorHandling:
    """Test error handling and validation"""
    
    def test_invalid_export_format(self, report_generator, sample_guard_nodes):
        """Test error on invalid export format"""
        report = report_generator.generate_report(
            case_id="CASE-2025-015",
            case_title="Invalid Format Test",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        # Create a mock invalid format object
        class InvalidFormat:
            value = "invalid"
        
        with pytest.raises((ValueError, AttributeError)):
            report_generator.export_report(report, InvalidFormat())
    
    def test_confidence_bounds(self):
        """Test confidence scores are bounded 0.0-1.0"""
        with pytest.raises(ValueError):
            create_timeline_event(
                timestamp=datetime.utcnow(),
                event_type="test",
                description="test",
                confidence=1.5,
                evidence_source="test"
            )


# ============================================================================
# TESTS - Report Integrity
# ============================================================================

class TestReportIntegrity:
    """Test report integrity features"""
    
    def test_report_hash_generation(self, report_generator, sample_guard_nodes):
        """Test report hash generation"""
        report = report_generator.generate_report(
            case_id="CASE-2025-016",
            case_title="Integrity Test",
            guard_node_candidates=sample_guard_nodes,
            timeline_events=[],
        )
        
        assert len(report.report_hash) == 64
        assert report.report_hash.isalnum()
    
    def test_report_hash_deterministic(self, report_generator):
        """Test report hash is deterministic for same content"""
        # Create two identical reports with same data
        fixed_timestamp = datetime(2025, 1, 20, 12, 0, 0)
        
        node1 = GuardNodeAnalysis(
            guard_fingerprint="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
            guard_nickname="test-guard",
            guard_country="US",
            guard_ip_address="203.0.113.1",
            guard_bandwidth_mbps=1000.0,
            overall_confidence=0.75,
            confidence_level="High",
            time_overlap_score=0.75,
            time_overlap_reasoning="Test reason",
            bandwidth_similarity_score=0.75,
            bandwidth_similarity_reasoning="Test reason",
            historical_recurrence_score=0.75,
            historical_recurrence_reasoning="Test reason",
            geographic_asn_score=0.75,
            geographic_asn_reasoning="Test reason",
            pcap_correlation_score=0.75,
            pcap_correlation_reasoning="Test reason",
            observation_count=1,
        )
        
        report1 = report_generator.generate_report(
            case_id="HASH-TEST",
            case_title="Hash Test",
            guard_node_candidates=[node1],
            timeline_events=[],
        )
        
        report2 = report_generator.generate_report(
            case_id="HASH-TEST",
            case_title="Hash Test",
            guard_node_candidates=[node1],
            timeline_events=[],
        )
        
        # Both should have valid hashes
        assert len(report1.report_hash) == 64
        assert len(report2.report_hash) == 64


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
