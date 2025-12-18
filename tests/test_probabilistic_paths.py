# tests/test_probabilistic_paths.py
"""
Tests for Probabilistic Path Inference Module

Tests cover:
1. Evidence breakdown computation
2. Entry node inference
3. Probabilistic path generation
4. Aggregate statistics
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, "/home/subha/Downloads/tor-unveil")

from backend.app.probabilistic_paths import (
    EvidenceBreakdown,
    EntryNodeInference,
    PathInferenceResult,
    ProbabilisticPathResult,
    ProbabilisticPathInference,
    generate_probabilistic_paths,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_guard():
    """Sample guard relay data"""
    return {
        "fingerprint": "GUARD123456789ABCDEF" * 2,
        "nickname": "TestGuard1",
        "advertised_bandwidth": 50_000_000,
        "consensus_weight": 5000,
        "country": "DE",
        "as": "AS12345",
        "flags": ["Guard", "Running", "Valid", "Stable", "Fast"],
        "is_guard": True,
        "is_exit": False,
        "running": True,
        "first_seen": (datetime.now(timezone.utc) - timedelta(days=100)).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "or_addresses": ["192.168.1.1:9001"],
        "effective_family": [],
    }


@pytest.fixture
def sample_middle():
    """Sample middle relay data"""
    return {
        "fingerprint": "MIDDLE123456789ABCDEF" * 2,
        "nickname": "TestMiddle1",
        "advertised_bandwidth": 30_000_000,
        "consensus_weight": 3000,
        "country": "FR",
        "as": "AS67890",
        "flags": ["Running", "Valid", "Stable"],
        "is_guard": False,
        "is_exit": False,
        "running": True,
        "first_seen": (datetime.now(timezone.utc) - timedelta(days=50)).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "or_addresses": ["192.168.2.1:9001"],
        "effective_family": [],
    }


@pytest.fixture
def sample_exit():
    """Sample exit relay data"""
    return {
        "fingerprint": "EXIT123456789ABCDEF12" * 2,
        "nickname": "TestExit1",
        "advertised_bandwidth": 40_000_000,
        "consensus_weight": 4000,
        "country": "NL",
        "as": "AS11111",
        "flags": ["Exit", "Running", "Valid", "Stable", "Fast"],
        "is_guard": False,
        "is_exit": True,
        "running": True,
        "first_seen": (datetime.now(timezone.utc) - timedelta(days=80)).isoformat(),
        "last_seen": datetime.now(timezone.utc).isoformat(),
        "or_addresses": ["192.168.3.1:9001"],
        "effective_family": [],
    }


@pytest.fixture
def multiple_guards():
    """Multiple guard relays for testing"""
    return [
        {
            "fingerprint": f"GUARD{i:040d}",
            "nickname": f"Guard{i}",
            "advertised_bandwidth": (100 - i) * 1_000_000,
            "consensus_weight": (100 - i) * 100,
            "country": ["DE", "FR", "NL", "US", "GB"][i % 5],
            "as": f"AS{10000 + i}",
            "flags": ["Guard", "Running", "Valid", "Stable"],
            "is_guard": True,
            "is_exit": False,
            "running": True,
            "first_seen": (datetime.now(timezone.utc) - timedelta(days=100 + i)).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "or_addresses": [f"10.0.{i}.1:9001"],
            "effective_family": [],
        }
        for i in range(10)
    ]


@pytest.fixture
def multiple_middles():
    """Multiple middle relays for testing"""
    return [
        {
            "fingerprint": f"MIDDLE{i:039d}",
            "nickname": f"Middle{i}",
            "advertised_bandwidth": (50 - i) * 1_000_000,
            "consensus_weight": (50 - i) * 50,
            "country": ["DE", "FR", "NL", "US", "GB"][i % 5],
            "as": f"AS{20000 + i}",
            "flags": ["Running", "Valid"],
            "is_guard": False,
            "is_exit": False,
            "running": True,
            "first_seen": (datetime.now(timezone.utc) - timedelta(days=50 + i)).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "or_addresses": [f"10.1.{i}.1:9001"],
            "effective_family": [],
        }
        for i in range(20)
    ]


@pytest.fixture
def multiple_exits():
    """Multiple exit relays for testing"""
    return [
        {
            "fingerprint": f"EXIT{i:041d}",
            "nickname": f"Exit{i}",
            "advertised_bandwidth": (40 - i) * 1_000_000,
            "consensus_weight": (40 - i) * 40,
            "country": ["DE", "FR", "NL", "US", "GB"][i % 5],
            "as": f"AS{30000 + i}",
            "flags": ["Exit", "Running", "Valid"],
            "is_guard": False,
            "is_exit": True,
            "running": True,
            "first_seen": (datetime.now(timezone.utc) - timedelta(days=30 + i)).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "or_addresses": [f"10.2.{i}.1:9001"],
            "effective_family": [],
        }
        for i in range(10)
    ]


# ============================================================================
# EVIDENCE BREAKDOWN TESTS
# ============================================================================

class TestEvidenceBreakdown:
    """Tests for EvidenceBreakdown dataclass"""
    
    def test_to_dict(self):
        """Test serialization"""
        evidence = EvidenceBreakdown(
            time_overlap=0.85,
            time_overlap_label="strong",
            traffic_similarity=0.72,
            traffic_similarity_label="moderate",
            stability=0.9,
            stability_label="very_strong",
            path_consistency=0.65,
            path_consistency_label="moderate",
            geo_plausibility=0.8,
            geo_plausibility_label="strong",
            weighted_average=0.78,
            min_score=0.65,
            consistency_score=0.85,
        )
        
        d = evidence.to_dict()
        
        assert d["time_overlap"] == 0.85
        assert d["time_overlap_label"] == "strong"
        assert d["weighted_average"] == 0.78
    
    def test_score_to_label(self):
        """Test score to label conversion"""
        assert EvidenceBreakdown.score_to_label(0.95) == "very_strong"
        assert EvidenceBreakdown.score_to_label(0.8) == "strong"
        assert EvidenceBreakdown.score_to_label(0.65) == "moderate"
        assert EvidenceBreakdown.score_to_label(0.45) == "weak"
        assert EvidenceBreakdown.score_to_label(0.25) == "very_weak"
        assert EvidenceBreakdown.score_to_label(0.1) == "insufficient"


# ============================================================================
# ENTRY NODE INFERENCE TESTS
# ============================================================================

class TestEntryNodeInference:
    """Tests for EntryNodeInference dataclass"""
    
    def test_to_dict(self):
        """Test serialization"""
        evidence = EvidenceBreakdown(
            time_overlap=0.8, time_overlap_label="strong",
            traffic_similarity=0.7, traffic_similarity_label="moderate",
            stability=0.85, stability_label="strong",
            path_consistency=0.6, path_consistency_label="moderate",
            geo_plausibility=0.75, geo_plausibility_label="strong",
            weighted_average=0.74, min_score=0.6, consistency_score=0.8,
        )
        
        inference = EntryNodeInference(
            fingerprint="ABC123",
            nickname="TestGuard",
            prior_probability=0.001,
            posterior_probability=0.025,
            likelihood_ratio=25.0,
            confidence=0.72,
            confidence_level="high",
            evidence=evidence,
            country="DE",
            autonomous_system="AS12345",
            bandwidth_mbps=50.0,
            uptime_days=100,
            flags=["Guard", "Running"],
            is_guard=True,
            observation_count=5,
            exit_nodes_observed_with=["exit1", "exit2"],
            rank=1,
        )
        
        d = inference.to_dict()
        
        assert d["fingerprint"] == "ABC123"
        assert d["posterior_probability"] == 0.025
        assert d["confidence_level"] == "high"
        assert d["rank"] == 1
        assert "evidence" in d
        assert d["evidence"]["time_overlap"] == 0.8


# ============================================================================
# PROBABILISTIC PATH INFERENCE TESTS
# ============================================================================

class TestProbabilisticPathInference:
    """Tests for ProbabilisticPathInference engine"""
    
    def test_init_default_weights(self):
        """Test default weight initialization"""
        engine = ProbabilisticPathInference()
        
        assert abs(sum(engine.weights.values()) - 1.0) < 0.01
        assert "time_overlap" in engine.weights
        assert "traffic_similarity" in engine.weights
    
    def test_compute_evidence_for_path(self, sample_guard, sample_middle, sample_exit):
        """Test evidence computation for a path"""
        engine = ProbabilisticPathInference()
        
        evidence = engine.compute_evidence_for_path(
            sample_guard, sample_middle, sample_exit
        )
        
        assert 0.0 <= evidence.time_overlap <= 1.0
        assert 0.0 <= evidence.traffic_similarity <= 1.0
        assert 0.0 <= evidence.stability <= 1.0
        assert 0.0 <= evidence.weighted_average <= 1.0
        assert evidence.time_overlap_label in [
            "very_strong", "strong", "moderate", "weak", "very_weak", "insufficient"
        ]
    
    def test_set_entry_priors(self, multiple_guards):
        """Test setting entry priors"""
        engine = ProbabilisticPathInference()
        engine.set_entry_priors(multiple_guards)
        
        assert len(engine.bayesian_engine.priors) == len(multiple_guards)
        assert abs(sum(engine.bayesian_engine.priors.values()) - 1.0) < 0.01
    
    def test_add_path_observation(self, sample_guard, sample_middle, sample_exit):
        """Test adding path observation"""
        engine = ProbabilisticPathInference()
        engine.set_entry_priors([sample_guard])
        
        evidence = engine.add_path_observation(
            sample_guard, sample_middle, sample_exit
        )
        
        assert evidence is not None
        assert sample_guard["fingerprint"] in engine.entry_observations
        assert len(engine.entry_observations[sample_guard["fingerprint"]]) == 1
    
    def test_multiple_observations(self, sample_guard, multiple_middles, multiple_exits):
        """Test multiple observations for same entry"""
        engine = ProbabilisticPathInference()
        engine.set_entry_priors([sample_guard])
        
        # Add multiple observations
        for m, x in zip(multiple_middles[:5], multiple_exits[:5]):
            engine.add_path_observation(sample_guard, m, x)
        
        assert len(engine.entry_observations[sample_guard["fingerprint"]]) == 5
        assert len(engine.exit_nodes_by_entry[sample_guard["fingerprint"]]) == 5
    
    def test_compute_entry_inference(self, sample_guard, sample_middle, sample_exit):
        """Test computing full entry inference"""
        engine = ProbabilisticPathInference()
        engine.set_entry_priors([sample_guard])
        engine.add_path_observation(sample_guard, sample_middle, sample_exit)
        
        inference = engine.compute_entry_inference(sample_guard, rank=1)
        
        assert inference is not None
        assert inference.fingerprint == sample_guard["fingerprint"]
        assert inference.observation_count == 1
        assert inference.rank == 1
        assert 0.0 <= inference.confidence <= 1.0
    
    def test_get_ranked_entries(self, multiple_guards, multiple_middles, multiple_exits):
        """Test getting ranked entry candidates"""
        engine = ProbabilisticPathInference()
        engine.set_entry_priors(multiple_guards)
        
        # Add observations for some guards
        for g in multiple_guards[:5]:
            for m, x in zip(multiple_middles[:3], multiple_exits[:3]):
                engine.add_path_observation(g, m, x)
        
        ranked = engine.get_ranked_entries(multiple_guards, top_k=5)
        
        assert len(ranked) <= 5
        # Check ranking order
        for i in range(len(ranked) - 1):
            assert ranked[i].posterior_probability >= ranked[i + 1].posterior_probability
    
    def test_compute_aggregate_stats(self, multiple_guards, multiple_middles, multiple_exits):
        """Test aggregate statistics computation"""
        engine = ProbabilisticPathInference()
        engine.set_entry_priors(multiple_guards)
        
        # Add some observations
        for g in multiple_guards[:3]:
            engine.add_path_observation(g, multiple_middles[0], multiple_exits[0])
        
        stats = engine.compute_aggregate_stats()
        
        assert "total_entries_analyzed" in stats
        assert "total_observations" in stats
        assert "posterior_distribution" in stats
        assert stats["total_entries_analyzed"] == len(multiple_guards)


# ============================================================================
# GENERATE PROBABILISTIC PATHS TESTS
# ============================================================================

class TestGenerateProbabilisticPaths:
    """Tests for generate_probabilistic_paths function"""
    
    def test_basic_generation(self, multiple_guards, multiple_middles, multiple_exits):
        """Test basic path generation"""
        result = generate_probabilistic_paths(
            guards=multiple_guards,
            middles=multiple_middles,
            exits=multiple_exits,
            top_k=5,
            max_paths=50,
        )
        
        assert isinstance(result, ProbabilisticPathResult)
        assert len(result.entry_candidates) <= 5
        assert len(result.paths) > 0
        assert "total_entries_analyzed" in result.aggregate_stats
        assert "algorithm" in result.inference_metadata
    
    def test_to_dict(self, multiple_guards, multiple_middles, multiple_exits):
        """Test result serialization"""
        result = generate_probabilistic_paths(
            guards=multiple_guards,
            middles=multiple_middles,
            exits=multiple_exits,
            top_k=3,
            max_paths=20,
        )
        
        d = result.to_dict()
        
        assert "entry_candidates" in d
        assert "paths" in d
        assert "aggregate_stats" in d
        assert "inference_metadata" in d
        
        # Check entry candidates structure
        if d["entry_candidates"]:
            candidate = d["entry_candidates"][0]
            assert "fingerprint" in candidate
            assert "posterior_probability" in candidate
            assert "confidence" in candidate
            assert "evidence" in candidate
    
    def test_empty_guards(self, multiple_middles, multiple_exits):
        """Test with empty guards list"""
        result = generate_probabilistic_paths(
            guards=[],
            middles=multiple_middles,
            exits=multiple_exits,
            top_k=5,
            max_paths=50,
        )
        
        assert len(result.entry_candidates) == 0
    
    def test_inference_metadata(self, multiple_guards, multiple_middles, multiple_exits):
        """Test inference metadata content"""
        result = generate_probabilistic_paths(
            guards=multiple_guards,
            middles=multiple_middles,
            exits=multiple_exits,
            top_k=5,
            max_paths=50,
        )
        
        meta = result.inference_metadata
        
        assert meta["algorithm"] == "bayesian_entry_inference"
        assert "version" in meta
        assert "weights" in meta
        assert "paths_analyzed" in meta
        assert "generated_at" in meta


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_same_fingerprint_handling(self, sample_guard, sample_middle):
        """Test handling of same fingerprint in different roles"""
        engine = ProbabilisticPathInference()
        
        # Create an exit with same fingerprint as guard
        fake_exit = sample_guard.copy()
        fake_exit["is_exit"] = True
        
        engine.set_entry_priors([sample_guard])
        
        # Should not crash
        evidence = engine.compute_evidence_for_path(
            sample_guard, sample_middle, fake_exit
        )
        
        assert evidence is not None
    
    def test_missing_fields(self):
        """Test handling of relays with missing fields"""
        engine = ProbabilisticPathInference()
        
        minimal_guard = {"fingerprint": "ABC123"}
        minimal_middle = {"fingerprint": "DEF456"}
        minimal_exit = {"fingerprint": "GHI789"}
        
        engine.set_entry_priors([minimal_guard])
        
        # Should not crash
        evidence = engine.compute_evidence_for_path(
            minimal_guard, minimal_middle, minimal_exit
        )
        
        assert evidence is not None
        assert evidence.weighted_average >= 0.0
    
    def test_large_bandwidth_values(self):
        """Test handling of large bandwidth values"""
        engine = ProbabilisticPathInference()
        
        high_bw_guard = {
            "fingerprint": "ABC123",
            "advertised_bandwidth": 10_000_000_000,  # 10 Gbps
            "flags": ["Guard"],
        }
        
        evidence = engine.compute_evidence_for_path(
            high_bw_guard,
            {"fingerprint": "DEF456", "advertised_bandwidth": 1_000_000},
            {"fingerprint": "GHI789", "advertised_bandwidth": 1_000_000},
        )
        
        assert 0.0 <= evidence.traffic_similarity <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
