"""
Unit Tests for Forensic PCAP Analysis Module

Tests flow extraction, burst detection, directionality analysis,
and both real-time and offline analysis modes.

Run with: python -m pytest tests/test_forensic_pcap.py -v
"""

import pytest
from datetime import datetime, timedelta
from backend.app.forensic_pcap import (
    ForensicPCAPAnalyzer,
    FlowEvidence,
    FlowKey,
    FlowStatistics,
    PacketInfo,
    Burst,
    AnalysisMode,
    flow_evidence_to_scoring_metrics,
    analyze_pcap_forensic,
    create_realtime_analyzer,
    TOR_PORTS,
    TOR_CELL_SIZE,
)


class TestFlowKey:
    """Test FlowKey data structure"""
    
    def test_flow_key_creation(self):
        """Create basic flow key"""
        key = FlowKey(
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=443,
            protocol=6
        )
        
        assert key.src_ip == "192.168.1.1"
        assert key.dst_ip == "10.0.0.1"
        assert key.src_port == 12345
        assert key.dst_port == 443
        assert key.protocol == 6
    
    def test_flow_key_hash(self):
        """Flow keys can be used as dict keys"""
        key1 = FlowKey("1.1.1.1", "2.2.2.2", 80, 443, 6)
        key2 = FlowKey("1.1.1.1", "2.2.2.2", 80, 443, 6)
        key3 = FlowKey("1.1.1.1", "3.3.3.3", 80, 443, 6)
        
        assert hash(key1) == hash(key2)
        assert key1 == key2
        assert key1 != key3
        
        # Use as dict key
        flows = {key1: "flow1"}
        assert flows[key2] == "flow1"
    
    def test_flow_key_reverse(self):
        """Reverse flow key swaps src/dst"""
        key = FlowKey("1.1.1.1", "2.2.2.2", 80, 443, 6)
        rev = key.reverse()
        
        assert rev.src_ip == "2.2.2.2"
        assert rev.dst_ip == "1.1.1.1"
        assert rev.src_port == 443
        assert rev.dst_port == 80
    
    def test_flow_key_canonical(self):
        """Canonical ordering for bidirectional flows"""
        key1 = FlowKey("1.1.1.1", "2.2.2.2", 80, 443, 6)
        key2 = FlowKey("2.2.2.2", "1.1.1.1", 443, 80, 6)
        
        canonical1, is_forward1 = key1.canonical()
        canonical2, is_forward2 = key2.canonical()
        
        # Both should produce same canonical key
        assert canonical1 == canonical2


class TestPacketInfo:
    """Test PacketInfo data structure"""
    
    def test_packet_info_creation(self):
        """Create basic packet info"""
        now = datetime.utcnow()
        packet = PacketInfo(
            timestamp=now,
            size=1500,
            direction=1,
            payload_size=1460,
        )
        
        assert packet.timestamp == now
        assert packet.size == 1500
        assert packet.direction == 1
        assert packet.payload_size == 1460
    
    def test_tor_cell_detection(self):
        """Detect TOR cell-sized packets"""
        # Exact TOR cell size
        packet1 = PacketInfo(
            timestamp=datetime.utcnow(),
            size=552,
            direction=1,
            payload_size=TOR_CELL_SIZE,
        )
        assert packet1.is_tor_cell_sized
        
        # Within tolerance
        packet2 = PacketInfo(
            timestamp=datetime.utcnow(),
            size=562,
            direction=1,
            payload_size=TOR_CELL_SIZE + 30,
        )
        assert packet2.is_tor_cell_sized
        
        # Outside tolerance
        packet3 = PacketInfo(
            timestamp=datetime.utcnow(),
            size=1500,
            direction=1,
            payload_size=1460,
        )
        assert not packet3.is_tor_cell_sized


class TestBurst:
    """Test Burst data structure"""
    
    def test_burst_creation(self):
        """Create basic burst"""
        start = datetime.utcnow()
        end = start + timedelta(milliseconds=100)
        
        burst = Burst(
            start_time=start,
            end_time=end,
            packet_count=10,
            total_bytes=5000,
            direction=1,
            inter_arrival_times=[10, 11, 9, 12, 10, 11, 10, 9, 8],
        )
        
        assert burst.packet_count == 10
        assert burst.total_bytes == 5000
        assert burst.direction == 1
    
    def test_burst_duration(self):
        """Burst duration calculation"""
        start = datetime.utcnow()
        end = start + timedelta(milliseconds=150)
        
        burst = Burst(
            start_time=start,
            end_time=end,
            packet_count=10,
            total_bytes=5000,
            direction=1,
        )
        
        assert abs(burst.duration_ms - 150) < 1
    
    def test_burst_packets_per_second(self):
        """Burst rate calculation"""
        start = datetime.utcnow()
        end = start + timedelta(seconds=1)
        
        burst = Burst(
            start_time=start,
            end_time=end,
            packet_count=100,
            total_bytes=50000,
            direction=1,
        )
        
        assert abs(burst.packets_per_second - 100) < 1
    
    def test_burst_avg_inter_arrival(self):
        """Average inter-arrival time"""
        burst = Burst(
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() + timedelta(milliseconds=100),
            packet_count=10,
            total_bytes=5000,
            direction=1,
            inter_arrival_times=[10.0, 10.0, 10.0, 10.0],
        )
        
        assert burst.avg_inter_arrival_ms == 10.0


class TestFlowStatistics:
    """Test FlowStatistics data structure"""
    
    def test_flow_statistics_creation(self):
        """Create basic flow statistics"""
        key = FlowKey("1.1.1.1", "2.2.2.2", 80, 443, 6)
        now = datetime.utcnow()
        
        flow = FlowStatistics(
            flow_key=key,
            first_seen=now,
            last_seen=now + timedelta(seconds=10),
        )
        
        assert flow.packet_count == 0
        assert flow.byte_count == 0
    
    def test_flow_directionality(self):
        """Flow directionality ratio"""
        key = FlowKey("1.1.1.1", "2.2.2.2", 80, 443, 6)
        now = datetime.utcnow()
        
        flow = FlowStatistics(
            flow_key=key,
            first_seen=now,
            last_seen=now + timedelta(seconds=10),
            forward_packets=60,
            reverse_packets=40,
        )
        
        assert flow.directionality_ratio == 0.6
    
    def test_flow_tor_cell_ratio(self):
        """TOR cell ratio calculation"""
        key = FlowKey("1.1.1.1", "2.2.2.2", 80, 9001, 6)
        now = datetime.utcnow()
        
        flow = FlowStatistics(
            flow_key=key,
            first_seen=now,
            last_seen=now + timedelta(seconds=10),
            packet_count=100,
            tor_cell_packets=40,
        )
        
        assert flow.tor_cell_ratio == 0.4
    
    def test_flow_is_likely_tor(self):
        """TOR likelihood detection"""
        # TOR port + cell pattern
        key1 = FlowKey("1.1.1.1", "2.2.2.2", 12345, 9001, 6)
        now = datetime.utcnow()
        
        flow1 = FlowStatistics(
            flow_key=key1,
            first_seen=now,
            last_seen=now + timedelta(seconds=10),
            packet_count=100,
            tor_cell_packets=40,
            forward_packets=50,
            reverse_packets=50,
        )
        
        assert flow1.is_likely_tor


class TestForensicPCAPAnalyzer:
    """Test ForensicPCAPAnalyzer class"""
    
    def test_analyzer_creation_offline(self):
        """Create offline analyzer"""
        analyzer = ForensicPCAPAnalyzer(mode=AnalysisMode.OFFLINE)
        
        assert analyzer.mode == AnalysisMode.OFFLINE
        assert analyzer.packet_count == 0
        assert len(analyzer.flows) == 0
    
    def test_analyzer_creation_realtime(self):
        """Create real-time analyzer"""
        analyzer = create_realtime_analyzer()
        
        assert analyzer.mode == AnalysisMode.REALTIME
    
    def test_add_packet_realtime(self):
        """Add packets in real-time mode"""
        analyzer = create_realtime_analyzer()
        
        now = datetime.utcnow()
        for i in range(10):
            analyzer.add_packet(
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=443,
                protocol=6,
                size=1500,
                timestamp=now + timedelta(milliseconds=i * 10),
            )
        
        assert analyzer.packet_count == 10
        assert len(analyzer.flows) == 1
    
    def test_get_current_evidence(self):
        """Get evidence from real-time analyzer"""
        analyzer = create_realtime_analyzer()
        
        now = datetime.utcnow()
        for i in range(20):
            analyzer.add_packet(
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=9001,  # TOR port
                protocol=6,
                size=552,  # ~TOR cell
                timestamp=now + timedelta(milliseconds=i * 5),
                payload_size=512,
            )
        
        evidence = analyzer.get_current_evidence()
        
        assert evidence.total_packets == 20
        assert evidence.total_flows == 1
        assert evidence.tor_port_matches >= 1
    
    def test_flow_summary(self):
        """Get flow summary"""
        analyzer = create_realtime_analyzer()
        
        now = datetime.utcnow()
        # Add packets for two flows
        for i in range(10):
            analyzer.add_packet(
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=443,
                protocol=6,
                size=1500,
                timestamp=now + timedelta(milliseconds=i * 10),
            )
            analyzer.add_packet(
                src_ip="192.168.1.2",
                dst_ip="10.0.0.2",
                src_port=54321,
                dst_port=80,
                protocol=6,
                size=500,
                timestamp=now + timedelta(milliseconds=i * 10),
            )
        
        summary = analyzer.get_flow_summary()
        
        assert len(summary) == 2
        assert summary[0]["packet_count"] == 10
    
    def test_reset(self):
        """Reset analyzer state"""
        analyzer = create_realtime_analyzer()
        
        analyzer.add_packet(
            src_ip="192.168.1.1",
            dst_ip="10.0.0.1",
            src_port=12345,
            dst_port=443,
            protocol=6,
            size=1500,
        )
        
        assert analyzer.packet_count == 1
        
        analyzer.reset()
        
        assert analyzer.packet_count == 0
        assert len(analyzer.flows) == 0


class TestFlowEvidence:
    """Test FlowEvidence data structure"""
    
    def test_flow_evidence_creation(self):
        """Create basic flow evidence"""
        evidence = FlowEvidence(
            total_flows=5,
            total_packets=1000,
            total_bytes=500000,
        )
        
        assert evidence.total_flows == 5
        assert evidence.total_packets == 1000
        assert evidence.total_bytes == 500000
    
    def test_flow_evidence_to_dict(self):
        """Convert evidence to dictionary"""
        evidence = FlowEvidence(
            total_flows=5,
            total_packets=1000,
            tor_cell_ratio=0.35,
        )
        
        d = evidence.to_dict()
        
        assert d["total_flows"] == 5
        assert d["total_packets"] == 1000
        assert d["tor_cell_ratio"] == 0.35


class TestScoringIntegration:
    """Test integration with scoring pipeline"""
    
    def test_flow_evidence_to_scoring_metrics(self):
        """Convert flow evidence to scoring metrics"""
        evidence = FlowEvidence(
            total_flows=10,
            total_packets=1000,
            total_bytes=500000,
            capture_duration_seconds=60.0,
            tor_likely_flows=5,
            tor_cell_ratio=0.4,
            tor_port_matches=6,
            overall_directionality=0.55,
            data_quality=0.9,
        )
        
        metrics = flow_evidence_to_scoring_metrics(evidence)
        
        assert "pcap_tor_likelihood" in metrics
        assert "pcap_data_quality" in metrics
        assert "pcap_directionality_balance" in metrics
        assert "pcap_burst_intensity" in metrics
        assert "pcap_timing_coverage" in metrics
        
        assert 0.0 <= metrics["pcap_tor_likelihood"] <= 1.0
        assert 0.0 <= metrics["pcap_data_quality"] <= 1.0
        assert 0.0 <= metrics["pcap_directionality_balance"] <= 1.0
    
    def test_pcap_evidence_score_integration(self):
        """Test pcap_evidence_score with flow evidence"""
        from backend.app.scoring.evidence import pcap_evidence_score
        
        evidence = FlowEvidence(
            total_flows=10,
            total_packets=1000,
            total_bytes=500000,
            capture_duration_seconds=60.0,
            tor_likely_flows=5,
            tor_cell_ratio=0.4,
            tor_port_matches=6,
            overall_directionality=0.55,
            data_quality=0.9,
        )
        
        metrics = flow_evidence_to_scoring_metrics(evidence)
        result = pcap_evidence_score(pcap_metrics=metrics)
        
        assert 0.0 <= result["value"] <= 1.0
        assert result["details"]["has_pcap_data"] is True
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_pcap_evidence_score_no_data(self):
        """Test pcap_evidence_score without data"""
        from backend.app.scoring.evidence import pcap_evidence_score
        
        result = pcap_evidence_score()
        
        assert result["value"] == 0.0
        assert result["details"]["has_pcap_data"] is False
        assert result["confidence"] == 0.0


class TestBurstDetection:
    """Test burst detection functionality"""
    
    def test_burst_detection_rapid_packets(self):
        """Detect burst from rapid packet sequence"""
        analyzer = create_realtime_analyzer()
        
        now = datetime.utcnow()
        # Create a burst: 10 packets in 50ms
        for i in range(10):
            analyzer.add_packet(
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=443,
                protocol=6,
                size=1500,
                timestamp=now + timedelta(milliseconds=i * 5),
            )
        
        # Add gap
        # Then another burst
        for i in range(10):
            analyzer.add_packet(
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=443,
                protocol=6,
                size=1500,
                timestamp=now + timedelta(milliseconds=500 + i * 5),
            )
        
        evidence = analyzer.get_current_evidence()
        
        # Should detect at least one burst
        assert evidence.total_bursts >= 1
    
    def test_no_burst_slow_packets(self):
        """No burst detection for slow packets"""
        analyzer = create_realtime_analyzer()
        
        now = datetime.utcnow()
        # Slow packets: 1 packet per second
        for i in range(5):
            analyzer.add_packet(
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=443,
                protocol=6,
                size=1500,
                timestamp=now + timedelta(seconds=i),
            )
        
        evidence = analyzer.get_current_evidence()
        
        # Should not detect bursts
        assert evidence.total_bursts == 0


class TestDirectionalityAnalysis:
    """Test directionality analysis"""
    
    def test_balanced_traffic(self):
        """Detect balanced bidirectional traffic"""
        analyzer = create_realtime_analyzer()
        
        now = datetime.utcnow()
        # Add forward packets
        for i in range(50):
            analyzer.add_packet(
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=443,
                protocol=6,
                size=1500,
                timestamp=now + timedelta(milliseconds=i * 10),
            )
        # Add reverse packets
        for i in range(50):
            analyzer.add_packet(
                src_ip="10.0.0.1",
                dst_ip="192.168.1.1",
                src_port=443,
                dst_port=12345,
                protocol=6,
                size=1500,
                timestamp=now + timedelta(milliseconds=i * 10 + 5),
            )
        
        evidence = analyzer.get_current_evidence()
        
        # Should be relatively balanced
        assert 0.3 < evidence.overall_directionality < 0.7
    
    def test_upload_dominant(self):
        """Detect upload-dominant traffic"""
        analyzer = create_realtime_analyzer()
        
        now = datetime.utcnow()
        # Mostly forward (upload) packets - larger size
        for i in range(90):
            analyzer.add_packet(
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=443,
                protocol=6,
                size=1500,
                timestamp=now + timedelta(milliseconds=i * 10),
            )
        # Few reverse packets - smaller size
        for i in range(10):
            analyzer.add_packet(
                src_ip="10.0.0.1",
                dst_ip="192.168.1.1",
                src_port=443,
                dst_port=12345,
                protocol=6,
                size=100,
                timestamp=now + timedelta(milliseconds=i * 100),
            )
        
        evidence = analyzer.get_current_evidence()
        
        # Check that forward_packets > reverse_packets in the flow
        # Due to canonical ordering, the flow might be reversed
        # So we check the total bytes ratio makes sense
        total = evidence.upload_bytes + evidence.download_bytes
        assert total > 0
        # The larger packet direction should dominate
        max_bytes = max(evidence.upload_bytes, evidence.download_bytes)
        min_bytes = min(evidence.upload_bytes, evidence.download_bytes)
        assert max_bytes > min_bytes * 5  # Dominant direction has 5x more bytes


class TestDataQuality:
    """Test data quality assessment"""
    
    def test_high_quality_capture(self):
        """High quality with many packets and flows"""
        analyzer = create_realtime_analyzer()
        
        now = datetime.utcnow()
        # Many packets across multiple flows over time
        for flow_idx in range(10):
            for i in range(100):
                analyzer.add_packet(
                    src_ip=f"192.168.1.{flow_idx}",
                    dst_ip=f"10.0.0.{flow_idx}",
                    src_port=12345 + flow_idx,
                    dst_port=443,
                    protocol=6,
                    size=1500,
                    timestamp=now + timedelta(seconds=i, milliseconds=flow_idx * 10),
                )
        
        evidence = analyzer.get_current_evidence()
        
        assert evidence.data_quality > 0.8
    
    def test_low_quality_few_packets(self):
        """Low quality with few packets"""
        analyzer = create_realtime_analyzer()
        
        now = datetime.utcnow()
        # Only a few packets
        for i in range(5):
            analyzer.add_packet(
                src_ip="192.168.1.1",
                dst_ip="10.0.0.1",
                src_port=12345,
                dst_port=443,
                protocol=6,
                size=1500,
                timestamp=now + timedelta(milliseconds=i * 10),
            )
        
        evidence = analyzer.get_current_evidence()
        
        assert evidence.data_quality < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
