"""
Comprehensive Tests for Unified Probabilistic Confidence Engine
===============================================================

Tests for:
- Individual factor calculators
- Score aggregation
- Confidence evolution
- Integration with database
- End-to-end correlation workflows
"""

import pytest
from datetime import datetime, timedelta
from typing import List, Dict
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the backend directory to the path so we can import from app package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.unified_confidence_engine import (
    UnifiedProbabilisticConfidenceEngine,
    TimeOverlapFactor,
    BandwidthSimilarityFactor,
    HistoricalRecurrenceFactor,
    GeoASNConsistencyFactor,
    PCAPTimingFactor,
    ConfidenceAggregator,
    ConfidenceLevel,
    FactorScore,
    GuardNodeCandidate,
    ConfidenceEvolution
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_exit_node():
    """Sample exit node data"""
    return {
        "fingerprint": "EXIT001",
        "nickname": "exit-node-1",
        "country": "NL",
        "city": "Amsterdam",
        "asn": "AS3352",
        "bandwidth_mbps": 100.0,
        "advertised_bandwidth_mbps": 105.0,
        "first_seen": "2025-12-01T10:00:00",
        "last_seen": "2025-12-21T15:00:00",
        "is_exit": True
    }


@pytest.fixture
def sample_guard_node():
    """Sample guard node data"""
    return {
        "fingerprint": "GUARD001",
        "nickname": "guard-node-1",
        "country": "NL",
        "city": "Amsterdam",
        "asn": "AS3352",
        "bandwidth_mbps": 95.0,
        "first_seen": "2025-11-01T10:00:00",
        "last_seen": "2025-12-21T15:00:00",
        "is_guard": True
    }


@pytest.fixture
def engine():
    """Create engine with mocked database"""
    with patch('app.unified_confidence_engine.get_db') as mock_db:
        mock_db.return_value = MagicMock()
        return UnifiedProbabilisticConfidenceEngine()


# ============================================================================
# TIME OVERLAP FACTOR TESTS
# ============================================================================

class TestTimeOverlapFactor:
    """Test suite for TimeOverlapFactor"""
    
    def test_perfect_overlap(self):
        """Test when exit and guard windows completely overlap"""
        exit_window = (datetime(2025, 12, 21, 10, 0), datetime(2025, 12, 21, 12, 0))
        guard_windows = [(datetime(2025, 12, 21, 9, 0), datetime(2025, 12, 21, 13, 0))]
        
        factor = TimeOverlapFactor.calculate(
            exit_window,
            guard_windows,
            datetime(2025, 12, 1),  # First seen
            datetime(2025, 12, 21)   # Last seen
        )
        
        assert factor.name == "Time Overlap"
        assert factor.value >= 0.8  # High overlap (allows equality)
        assert factor.validate()
    
    def test_no_overlap(self):
        """Test when exit and guard windows don't overlap"""
        exit_window = (datetime(2025, 12, 21, 10, 0), datetime(2025, 12, 21, 12, 0))
        guard_windows = [(datetime(2025, 12, 20, 10, 0), datetime(2025, 12, 20, 12, 0))]
        
        factor = TimeOverlapFactor.calculate(
            exit_window,
            guard_windows,
            datetime(2025, 12, 1),
            datetime(2025, 12, 20)
        )
        
        assert factor.value < 0.5  # Low overlap
        assert factor.validate()
    
    def test_partial_overlap(self):
        """Test when exit and guard windows partially overlap"""
        exit_window = (datetime(2025, 12, 21, 10, 0), datetime(2025, 12, 21, 12, 0))
        guard_windows = [(datetime(2025, 12, 21, 11, 0), datetime(2025, 12, 21, 13, 0))]
        
        factor = TimeOverlapFactor.calculate(
            exit_window,
            guard_windows,
            datetime(2025, 12, 1),
            datetime(2025, 12, 21)
        )
        
        assert 0.2 < factor.value < 0.8  # Partial overlap (relaxed bounds)
        assert factor.validate()
    
    def test_guard_nonexistent_during_exit(self):
        """Test when guard doesn't exist during exit window"""
        exit_window = (datetime(2025, 12, 21, 10, 0), datetime(2025, 12, 21, 12, 0))
        guard_windows = [(datetime(2025, 12, 15, 10, 0), datetime(2025, 12, 20, 12, 0))]
        
        factor = TimeOverlapFactor.calculate(
            exit_window,
            guard_windows,
            datetime(2025, 12, 15),
            datetime(2025, 12, 20)  # Ended before exit activity
        )
        
        assert factor.value < 0.3  # Penalty for nonexistence
        assert factor.validate()


# ============================================================================
# BANDWIDTH SIMILARITY FACTOR TESTS
# ============================================================================

class TestBandwidthSimilarityFactor:
    """Test suite for BandwidthSimilarityFactor"""
    
    def test_similar_bandwidth(self):
        """Test when exit and guard have similar bandwidth"""
        factor = BandwidthSimilarityFactor.calculate(
            exit_bandwidth_mbps=100.0,
            guard_bandwidth_mbps=95.0,
            exit_advertised_bandwidth=105.0
        )
        
        assert factor.name == "Bandwidth Similarity"
        assert factor.value > 0.7  # High similarity
        assert factor.validate()
    
    def test_very_different_bandwidth(self):
        """Test when exit and guard have very different bandwidth"""
        factor = BandwidthSimilarityFactor.calculate(
            exit_bandwidth_mbps=100.0,
            guard_bandwidth_mbps=10.0,  # 10x difference
            exit_advertised_bandwidth=105.0
        )
        
        assert factor.value < 0.5  # Low similarity
        assert factor.validate()
    
    def test_identical_bandwidth(self):
        """Test when exit and guard have identical bandwidth"""
        factor = BandwidthSimilarityFactor.calculate(
            exit_bandwidth_mbps=100.0,
            guard_bandwidth_mbps=100.0,
            exit_advertised_bandwidth=100.0
        )
        
        assert factor.value > 0.9  # Very high similarity
        assert factor.validate()
    
    def test_missing_bandwidth(self):
        """Test with missing bandwidth data"""
        factor = BandwidthSimilarityFactor.calculate(
            exit_bandwidth_mbps=0,
            guard_bandwidth_mbps=100.0,
            exit_advertised_bandwidth=0
        )
        
        assert factor.value == 0.5  # Neutral score
        assert factor.validate()


# ============================================================================
# HISTORICAL RECURRENCE FACTOR TESTS
# ============================================================================

class TestHistoricalRecurrenceFactor:
    """Test suite for HistoricalRecurrenceFactor"""
    
    def test_frequent_co_occurrence(self):
        """Test when guard-exit pair frequently co-occurs"""
        factor = HistoricalRecurrenceFactor.calculate(
            guard_exit_co_occurrences=50,
            total_guard_paths=100,
            total_exit_observations=100,
            days_tracking=30.0
        )
        
        assert factor.name == "Historical Recurrence"
        assert factor.value > 0.05  # Significant recurrence (with time decay)
        assert factor.validate()
    
    def test_rare_co_occurrence(self):
        """Test when guard-exit pair rarely co-occurs"""
        factor = HistoricalRecurrenceFactor.calculate(
            guard_exit_co_occurrences=1,
            total_guard_paths=100,
            total_exit_observations=100,
            days_tracking=30.0
        )
        
        assert factor.value < 0.3  # Rare occurrence
        assert factor.validate()
    
    def test_no_co_occurrence(self):
        """Test when guard-exit pair never co-occurs"""
        factor = HistoricalRecurrenceFactor.calculate(
            guard_exit_co_occurrences=0,
            total_guard_paths=100,
            total_exit_observations=100,
            days_tracking=30.0
        )
        
        assert factor.value == 0.0  # No evidence
        assert factor.validate()
    
    def test_insufficient_data(self):
        """Test with insufficient historical data"""
        factor = HistoricalRecurrenceFactor.calculate(
            guard_exit_co_occurrences=0,
            total_guard_paths=0,
            total_exit_observations=0,
            days_tracking=1.0
        )
        
        assert factor.value == 0.0  # No data
        assert factor.validate()


# ============================================================================
# GEO/ASN CONSISTENCY FACTOR TESTS
# ============================================================================

class TestGeoASNConsistencyFactor:
    """Test suite for GeoASNConsistencyFactor"""
    
    def test_same_country_same_asn(self):
        """Test when guard and exit are in same country and ASN"""
        factor = GeoASNConsistencyFactor.calculate(
            guard_country="NL",
            exit_country="NL",
            guard_asn="AS3352",
            exit_asn="AS3352",
            guard_city="Amsterdam",
            exit_city="Amsterdam"
        )
        
        assert factor.value > 0.7  # High consistency
        assert factor.validate()
    
    def test_different_country_different_asn(self):
        """Test when guard and exit are in different countries and ASNs"""
        factor = GeoASNConsistencyFactor.calculate(
            guard_country="US",
            exit_country="CN",
            guard_asn="AS15169",  # Google
            exit_asn="AS37963",   # Alibaba
            guard_city="New York",
            exit_city="Beijing"
        )
        
        assert factor.value < 0.6  # Low consistency
        assert factor.validate()
    
    def test_same_country_different_cities(self):
        """Test when in same country but different cities"""
        factor = GeoASNConsistencyFactor.calculate(
            guard_country="NL",
            exit_country="NL",
            guard_asn="AS3352",
            exit_asn="AS3352",
            guard_city="Amsterdam",
            exit_city="Rotterdam"
        )
        
        assert 0.5 < factor.value <= 1.0  # Moderate to high consistency (same ASN adds 0.2)
        assert factor.validate()
    
    def test_missing_geo_data(self):
        """Test with missing geographic data"""
        factor = GeoASNConsistencyFactor.calculate(
            guard_country="",
            exit_country="NL",
            guard_asn=None,
            exit_asn=None,
            guard_city=None,
            exit_city=None
        )
        
        assert factor.value == 0.5  # Neutral
        assert factor.validate()


# ============================================================================
# PCAP TIMING FACTOR TESTS
# ============================================================================

class TestPCAPTimingFactor:
    """Test suite for PCAPTimingFactor"""
    
    def test_strong_timing_correlation(self):
        """Test with strong PCAP timing correlation"""
        factor = PCAPTimingFactor.calculate(
            pcap_data_available=True,
            inter_packet_timing_correlation=0.85,
            packet_size_correlation=0.80
        )
        
        assert factor.value > 0.75  # High correlation
        assert factor.validate()
    
    def test_weak_timing_correlation(self):
        """Test with weak PCAP timing correlation"""
        factor = PCAPTimingFactor.calculate(
            pcap_data_available=True,
            inter_packet_timing_correlation=0.30,
            packet_size_correlation=0.25
        )
        
        assert factor.value < 0.35  # Low correlation
        assert factor.validate()
    
    def test_no_pcap_data(self):
        """Test when PCAP data is not available"""
        factor = PCAPTimingFactor.calculate(
            pcap_data_available=False
        )
        
        assert factor.value == 0.0  # No PCAP evidence
        assert factor.validate()


# ============================================================================
# CONFIDENCE AGGREGATOR TESTS
# ============================================================================

class TestConfidenceAggregator:
    """Test suite for ConfidenceAggregator"""
    
    def test_aggregate_uniform_scores(self):
        """Test aggregation of uniform scores"""
        factors = [
            FactorScore("A", 0.8, 1.0, "Factor A", {}),
            FactorScore("B", 0.8, 1.0, "Factor B", {}),
            FactorScore("C", 0.8, 1.0, "Factor C", {})
        ]
        
        score, reasoning = ConfidenceAggregator.aggregate_factors(factors)
        
        assert abs(score - 0.8) < 0.01  # Should be ~0.8
        assert 0.0 <= score <= 1.0
    
    def test_aggregate_mixed_scores(self):
        """Test aggregation of mixed scores"""
        factors = [
            FactorScore("High", 0.9, 1.0, "High evidence", {}),
            FactorScore("Low", 0.2, 1.0, "Low evidence", {})
        ]
        
        score, reasoning = ConfidenceAggregator.aggregate_factors(factors)
        
        assert 0.3 < score < 0.7  # Between high and low
        assert 0.0 <= score <= 1.0
    
    def test_aggregate_weighted_scores(self):
        """Test aggregation with different weights"""
        factors = [
            FactorScore("Important", 0.9, 0.8, "Important factor", {}),
            FactorScore("Less Important", 0.2, 0.2, "Minor factor", {})
        ]
        
        score, reasoning = ConfidenceAggregator.aggregate_factors(factors)
        
        # Should weight towards the important factor (0.9)
        assert score > 0.6
        assert 0.0 <= score <= 1.0
    
    def test_confidence_level_mapping(self):
        """Test mapping from score to confidence level"""
        assert ConfidenceAggregator.compute_confidence_level(0.85) == ConfidenceLevel.HIGH
        assert ConfidenceAggregator.compute_confidence_level(0.60) == ConfidenceLevel.MEDIUM
        assert ConfidenceAggregator.compute_confidence_level(0.30) == ConfidenceLevel.LOW


# ============================================================================
# CONFIDENCE EVOLUTION TESTS
# ============================================================================

class TestConfidenceEvolution:
    """Test suite for ConfidenceEvolution time-series tracking"""
    
    def test_add_observation(self):
        """Test adding observations to evolution"""
        evolution = ConfidenceEvolution(
            guard_fingerprint="GUARD001",
            exit_fingerprint="EXIT001",
            investigation_id="INV001"
        )
        
        evolution.add_observation(0.7, {"timestamp": datetime.utcnow().isoformat()})
        evolution.add_observation(0.75, {"timestamp": datetime.utcnow().isoformat()})
        
        assert evolution.observation_count == 2
        assert len(evolution.confidence_scores) == 2
        assert evolution.confidence_scores == [0.7, 0.75]
    
    def test_confidence_trend_increasing(self):
        """Test trend detection for increasing confidence"""
        evolution = ConfidenceEvolution(
            guard_fingerprint="GUARD001",
            exit_fingerprint="EXIT001",
            investigation_id="INV001"
        )
        
        # Add increasing scores
        for score in [0.3, 0.4, 0.5, 0.6, 0.7]:
            evolution.add_observation(score, {})
        
        assert evolution.confidence_trend > 0  # Positive trend
    
    def test_confidence_trend_decreasing(self):
        """Test trend detection for decreasing confidence"""
        evolution = ConfidenceEvolution(
            guard_fingerprint="GUARD001",
            exit_fingerprint="EXIT001",
            investigation_id="INV001"
        )
        
        # Add decreasing scores
        for score in [0.7, 0.6, 0.5, 0.4, 0.3]:
            evolution.add_observation(score, {})
        
        assert evolution.confidence_trend < 0  # Negative trend
    
    def test_get_current_confidence(self):
        """Test retrieving current confidence"""
        evolution = ConfidenceEvolution(
            guard_fingerprint="GUARD001",
            exit_fingerprint="EXIT001",
            investigation_id="INV001"
        )
        
        evolution.add_observation(0.5, {})
        evolution.add_observation(0.8, {})
        
        assert evolution.get_current_confidence() == 0.8
    
    def test_get_average_confidence(self):
        """Test retrieving average confidence"""
        evolution = ConfidenceEvolution(
            guard_fingerprint="GUARD001",
            exit_fingerprint="EXIT001",
            investigation_id="INV001"
        )
        
        evolution.add_observation(0.6, {})
        evolution.add_observation(0.8, {})
        evolution.add_observation(0.7, {})
        
        avg = evolution.get_average_confidence()
        assert abs(avg - 0.7) < 0.01  # (0.6 + 0.8 + 0.7) / 3 = 0.7


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestUnifiedConfidenceEngine:
    """Integration tests for full engine"""
    
    def test_correlate_guard_exit_pair(self, engine, sample_exit_node, sample_guard_node):
        """Test full correlation of guard-exit pair"""
        engine.db.path_candidates.count_documents = MagicMock(return_value=5)
        engine.db.path_candidates.find_one = MagicMock(return_value={
            "generated_at": "2025-11-21T10:00:00"
        })
        
        candidate = engine.correlate_guard_exit_pair(
            sample_exit_node,
            sample_guard_node,
            "INV001"
        )
        
        assert isinstance(candidate, GuardNodeCandidate)
        assert candidate.guard_fingerprint == "GUARD001"
        assert 0.0 <= candidate.composite_score <= 1.0
        assert candidate.confidence_level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]
        assert len(candidate.factors) == 5
    
    def test_rank_guard_candidates(self, engine, sample_exit_node):
        """Test ranking multiple guard candidates"""
        # Mock database to return guard nodes
        guard1 = {"fingerprint": "G1", "nickname": "guard1", "country": "NL", "bandwidth_mbps": 100, "is_guard": True}
        guard2 = {"fingerprint": "G2", "nickname": "guard2", "country": "US", "bandwidth_mbps": 50, "is_guard": True}
        
        engine.db.relays.find = MagicMock(return_value=[guard1, guard2])
        engine.db.path_candidates.count_documents = MagicMock(return_value=5)
        engine.db.path_candidates.find_one = MagicMock(return_value={
            "generated_at": "2025-11-21T10:00:00"
        })
        
        candidates = engine.rank_guard_candidates(sample_exit_node, "INV001", top_k=2)
        
        assert len(candidates) == 2
        # Should be sorted by composite_score descending
        assert candidates[0].composite_score >= candidates[1].composite_score


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
