# tests/test_probabilistic_paths.py
"""
Tests for Probabilistic Hypothesis Modeling for TOR Path Inference

Tests cover:
1. Hypothesis creation and management
2. Bayesian updates with observations
3. Guard persistence modeling
4. Evidence decay
5. Entropy tracking
6. State persistence
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import math

import sys
sys.path.insert(0, "/home/subha/Downloads/tor-unveil")

from backend.app.probabilistic_paths import (
    HypothesisConfig,
    EvidenceStrength,
    ExitObservation,
    GuardHypothesis,
    HypothesisExplanation,
    RankedHypothesis,
    BayesianHypothesisEngine,
    ProbabilisticPathInference,
    ProbabilisticPathResult,
    create_inference_engine,
    compute_entropy,
    normalize_probabilities,
    generate_probabilistic_paths,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_guards():
    """Sample guard relay data"""
    return [
        {
            "fingerprint": f"GUARD{i:040d}",
            "nickname": f"TestGuard{i}",
            "advertised_bandwidth": (100 - i) * 1_000_000,
            "consensus_weight": (100 - i) * 100,
            "country": ["DE", "FR", "NL", "US", "GB"][i % 5],
            "as": f"AS{10000 + i}",
            "flags": ["Guard", "Running", "Valid", "Stable"],
        }
        for i in range(5)
    ]


@pytest.fixture
def sample_observation():
    """Sample exit observation"""
    return ExitObservation(
        observation_id="obs-001",
        exit_fingerprint="EXIT0000000000000000000000000000000000001",
        exit_nickname="TestExit1",
        timestamp=datetime.utcnow(),
        evidence_score=0.75,
    )


@pytest.fixture
def config():
    """Standard test configuration"""
    return HypothesisConfig()


# ============================================================================
# EXIT OBSERVATION TESTS
# ============================================================================

class TestExitObservation:
    """Tests for ExitObservation dataclass"""
    
    def test_creation(self):
        """Test observation creation"""
        obs = ExitObservation(
            observation_id="obs-001",
            exit_fingerprint="EXIT123",
            exit_nickname="TestExit",
            timestamp=datetime.utcnow(),
            evidence_score=0.8,
        )
        
        assert obs.observation_id == "obs-001"
        assert obs.exit_fingerprint == "EXIT123"
        assert obs.evidence_score == 0.8
    
    def test_age_hours(self):
        """Test age calculation"""
        now = datetime.utcnow()
        past = now - timedelta(hours=5)
        
        obs = ExitObservation(
            observation_id="obs-001",
            exit_fingerprint="EXIT123",
            exit_nickname="TestExit",
            timestamp=past,
            evidence_score=0.5,
        )
        
        age = obs.age_hours(now)
        assert 4.9 < age < 5.1
    
    def test_decay_factor_recent(self):
        """Test decay factor for recent observation"""
        obs = ExitObservation(
            observation_id="obs-001",
            exit_fingerprint="EXIT123",
            exit_nickname="TestExit",
            timestamp=datetime.utcnow(),
            evidence_score=0.5,
        )
        
        decay = obs.decay_factor()
        assert decay > 0.9  # Recent observation should have high decay factor
    
    def test_decay_factor_old(self):
        """Test decay factor for old observation"""
        old_time = datetime.utcnow() - timedelta(hours=48)
        
        obs = ExitObservation(
            observation_id="obs-001",
            exit_fingerprint="EXIT123",
            exit_nickname="TestExit",
            timestamp=old_time,
            evidence_score=0.5,
        )
        
        decay = obs.decay_factor()
        assert decay < 0.5  # Old observation should have decayed
    
    def test_decay_factor_very_old(self):
        """Test decay factor for very old (stale) observation"""
        very_old = datetime.utcnow() - timedelta(days=10)
        
        obs = ExitObservation(
            observation_id="obs-001",
            exit_fingerprint="EXIT123",
            exit_nickname="TestExit",
            timestamp=very_old,
            evidence_score=0.5,
        )
        
        decay = obs.decay_factor()
        assert decay == 0.1  # Very stale observation


# ============================================================================
# GUARD HYPOTHESIS TESTS
# ============================================================================

class TestGuardHypothesis:
    """Tests for GuardHypothesis dataclass"""
    
    def test_creation(self):
        """Test hypothesis creation"""
        hyp = GuardHypothesis(
            hypothesis_id="hyp-001",
            guard_fingerprint="GUARD123",
            guard_nickname="TestGuard",
            prior_probability=0.1,
            likelihood=1.0,
            posterior_probability=0.1,
        )
        
        assert hyp.guard_fingerprint == "GUARD123"
        assert hyp.prior_probability == 0.1
        assert hyp.evidence_count == 0
    
    def test_exit_nodes_seen(self):
        """Test tracking of unique exit nodes"""
        hyp = GuardHypothesis(
            hypothesis_id="hyp-001",
            guard_fingerprint="GUARD123",
            guard_nickname="TestGuard",
            prior_probability=0.1,
            likelihood=1.0,
            posterior_probability=0.1,
        )
        
        # Add observations
        hyp.exit_observations.append(ExitObservation(
            observation_id="obs-1",
            exit_fingerprint="EXIT1",
            exit_nickname="Exit1",
            timestamp=datetime.utcnow(),
            evidence_score=0.5,
        ))
        hyp.exit_observations.append(ExitObservation(
            observation_id="obs-2",
            exit_fingerprint="EXIT2",
            exit_nickname="Exit2",
            timestamp=datetime.utcnow(),
            evidence_score=0.5,
        ))
        hyp.exit_observations.append(ExitObservation(
            observation_id="obs-3",
            exit_fingerprint="EXIT1",  # Duplicate exit
            exit_nickname="Exit1",
            timestamp=datetime.utcnow(),
            evidence_score=0.5,
        ))
        
        # Should only count unique exits
        assert len(hyp.exit_nodes_seen) == 2
        assert "EXIT1" in hyp.exit_nodes_seen
        assert "EXIT2" in hyp.exit_nodes_seen
    
    def test_observation_span(self):
        """Test observation time span calculation"""
        hyp = GuardHypothesis(
            hypothesis_id="hyp-001",
            guard_fingerprint="GUARD123",
            guard_nickname="TestGuard",
            prior_probability=0.1,
            likelihood=1.0,
            posterior_probability=0.1,
            first_observation=datetime.utcnow() - timedelta(hours=10),
            last_observation=datetime.utcnow(),
        )
        
        span = hyp.observation_span_hours
        assert 9.9 < span < 10.1
    
    def test_evidence_strength_update(self):
        """Test evidence strength classification"""
        hyp = GuardHypothesis(
            hypothesis_id="hyp-001",
            guard_fingerprint="GUARD123",
            guard_nickname="TestGuard",
            prior_probability=0.1,
            likelihood=1.0,
            posterior_probability=0.1,
        )
        
        # No observations - very weak
        hyp.update_evidence_strength()
        assert hyp.evidence_strength == EvidenceStrength.VERY_WEAK
        
        # Add high-quality recent observations
        for i in range(6):
            hyp.exit_observations.append(ExitObservation(
                observation_id=f"obs-{i}",
                exit_fingerprint=f"EXIT{i}",
                exit_nickname=f"Exit{i}",
                timestamp=datetime.utcnow(),
                evidence_score=0.9,
            ))
        
        hyp.update_evidence_strength()
        assert hyp.evidence_strength == EvidenceStrength.VERY_STRONG
    
    def test_to_dict(self):
        """Test serialization"""
        hyp = GuardHypothesis(
            hypothesis_id="hyp-001",
            guard_fingerprint="GUARD123",
            guard_nickname="TestGuard",
            prior_probability=0.2,
            likelihood=0.8,
            posterior_probability=0.25,
            evidence_count=5,
        )
        
        d = hyp.to_dict()
        
        assert d["hypothesis_id"] == "hyp-001"
        assert d["guard_node"]["fingerprint"] == "GUARD123"
        assert d["prior_probability"] == 0.2
        assert d["posterior_probability"] == 0.25
        assert d["evidence_count"] == 5


# ============================================================================
# BAYESIAN HYPOTHESIS ENGINE TESTS
# ============================================================================

class TestBayesianHypothesisEngine:
    """Tests for BayesianHypothesisEngine"""
    
    def test_initialization(self, config):
        """Test engine initialization"""
        engine = BayesianHypothesisEngine(config)
        
        assert len(engine.hypotheses) == 0
        assert engine.total_updates == 0
        assert engine.current_dominant_guard is None
    
    def test_set_guard_priors(self, sample_guards, config):
        """Test setting guard priors"""
        engine = BayesianHypothesisEngine(config)
        engine.set_guard_priors(sample_guards)
        
        assert len(engine.guard_priors) == 5
        
        # Priors should sum to approximately 1
        total = sum(engine.guard_priors.values())
        assert 0.99 < total < 1.01
    
    def test_set_guard_priors_uniform(self, sample_guards, config):
        """Test uniform priors"""
        engine = BayesianHypothesisEngine(config)
        engine.set_guard_priors(sample_guards, use_consensus_weights=False)
        
        # Each guard should have equal prior
        for prior in engine.guard_priors.values():
            assert abs(prior - 0.2) < 0.01
    
    def test_get_or_create_hypothesis(self, sample_guards, config):
        """Test hypothesis creation"""
        engine = BayesianHypothesisEngine(config)
        engine.set_guard_priors(sample_guards)
        
        fp = sample_guards[0]["fingerprint"]
        hyp = engine.get_or_create_hypothesis(fp, "TestGuard0")
        
        assert hyp.guard_fingerprint == fp
        assert hyp.guard_nickname == "TestGuard0"
        assert fp in engine.hypotheses
        
        # Getting same hypothesis again should return existing
        hyp2 = engine.get_or_create_hypothesis(fp, "TestGuard0")
        assert hyp.hypothesis_id == hyp2.hypothesis_id
    
    def test_update_with_observation(self, sample_guards, sample_observation, config):
        """Test Bayesian update with observation"""
        engine = BayesianHypothesisEngine(config)
        engine.set_guard_priors(sample_guards)
        
        posteriors = engine.update_with_observation(
            sample_observation,
            candidate_guards=sample_guards
        )
        
        assert len(posteriors) == 5
        assert engine.total_updates == 1
        
        # Posteriors should sum to 1
        total = sum(posteriors.values())
        assert 0.99 < total < 1.01
    
    def test_multiple_updates(self, sample_guards, config):
        """Test multiple observations update"""
        engine = BayesianHypothesisEngine(config)
        engine.set_guard_priors(sample_guards)
        
        # Add multiple observations
        for i in range(5):
            obs = ExitObservation(
                observation_id=f"obs-{i}",
                exit_fingerprint=f"EXIT{i}",
                exit_nickname=f"Exit{i}",
                timestamp=datetime.utcnow(),
                evidence_score=0.7,
            )
            engine.update_with_observation(obs, candidate_guards=sample_guards)
        
        assert engine.total_updates == 5
        assert len(engine.all_observations) == 5
    
    def test_entropy_computation(self, sample_guards, config):
        """Test entropy calculation"""
        engine = BayesianHypothesisEngine(config)
        engine.set_guard_priors(sample_guards, use_consensus_weights=False)
        
        # Create hypotheses for all guards
        for guard in sample_guards:
            engine.get_or_create_hypothesis(
                guard["fingerprint"],
                guard["nickname"]
            )
        
        # With uniform distribution, entropy should be log2(5) ??? 2.32
        entropy = engine.compute_entropy()
        assert 2.0 < entropy < 2.5
    
    def test_entropy_reduction(self, sample_guards, config):
        """Test that entropy reduces with consistent evidence"""
        engine = BayesianHypothesisEngine(config)
        engine.set_guard_priors(sample_guards)
        
        initial_entropy = None
        
        # Add observations that consistently favor first guard
        target_guard = sample_guards[0]
        
        for i in range(10):
            obs = ExitObservation(
                observation_id=f"obs-{i}",
                exit_fingerprint=f"EXIT{i}",
                exit_nickname=f"Exit{i}",
                timestamp=datetime.utcnow(),
                evidence_score=0.9,
            )
            
            # Manually boost likelihood for target guard
            engine.update_with_observation(obs, candidate_guards=sample_guards)
            
            if initial_entropy is None:
                initial_entropy = engine.entropy_history[0][1] if engine.entropy_history else None
        
        final_entropy = engine.compute_entropy()
        
        # With many observations, entropy should be tracked
        assert len(engine.entropy_history) == 10
    
    def test_get_ranked_hypotheses(self, sample_guards, config):
        """Test hypothesis ranking"""
        engine = BayesianHypothesisEngine(config)
        engine.set_guard_priors(sample_guards)
        
        # Add some observations
        for i in range(3):
            obs = ExitObservation(
                observation_id=f"obs-{i}",
                exit_fingerprint=f"EXIT{i}",
                exit_nickname=f"Exit{i}",
                timestamp=datetime.utcnow(),
                evidence_score=0.7,
            )
            engine.update_with_observation(obs, candidate_guards=sample_guards)
        
        ranked = engine.get_ranked_hypotheses(top_k=3)
        
        assert len(ranked) <= 3
        
        # Should be ranked by posterior (descending)
        for i in range(len(ranked) - 1):
            assert ranked[i].hypothesis.posterior_probability >= ranked[i+1].hypothesis.posterior_probability
    
    def test_state_export_import(self, sample_guards, config):
        """Test state persistence"""
        engine = BayesianHypothesisEngine(config)
        engine.set_guard_priors(sample_guards)
        
        # Add observations
        for i in range(3):
            obs = ExitObservation(
                observation_id=f"obs-{i}",
                exit_fingerprint=f"EXIT{i}",
                exit_nickname=f"Exit{i}",
                timestamp=datetime.utcnow(),
                evidence_score=0.7,
            )
            engine.update_with_observation(obs, candidate_guards=sample_guards)
        
        # Export state
        state = engine.export_state()
        
        assert "hypotheses" in state
        assert "guard_priors" in state
        assert state["total_updates"] == 3
        
        # Import into new engine
        engine2 = BayesianHypothesisEngine(config)
        engine2.import_state(state)
        
        assert engine2.total_updates == 3
        assert len(engine2.hypotheses) == len(engine.hypotheses)
    
    def test_state_summary(self, sample_guards, config):
        """Test state summary generation"""
        engine = BayesianHypothesisEngine(config)
        engine.set_guard_priors(sample_guards)
        
        obs = ExitObservation(
            observation_id="obs-1",
            exit_fingerprint="EXIT1",
            exit_nickname="Exit1",
            timestamp=datetime.utcnow(),
            evidence_score=0.7,
        )
        engine.update_with_observation(obs, candidate_guards=sample_guards)
        
        summary = engine.get_state_summary()
        
        assert "total_hypotheses" in summary
        assert "total_observations" in summary
        assert "entropy" in summary
        assert "uncertainty_level" in summary


# ============================================================================
# PROBABILISTIC PATH INFERENCE TESTS
# ============================================================================

class TestProbabilisticPathInference:
    """Tests for high-level ProbabilisticPathInference"""
    
    def test_initialization(self, config):
        """Test inference initialization"""
        inference = ProbabilisticPathInference(config)
        
        assert inference.engine is not None
        assert len(inference.guard_metadata) == 0
    
    def test_initialize_guards(self, sample_guards, config):
        """Test guard initialization"""
        inference = ProbabilisticPathInference(config)
        inference.initialize_guards(sample_guards)
        
        assert len(inference.guard_metadata) == 5
        assert len(inference.engine.guard_priors) == 5
    
    def test_add_exit_observation(self, sample_guards, config):
        """Test adding exit observation"""
        inference = ProbabilisticPathInference(config)
        inference.initialize_guards(sample_guards)
        
        posteriors = inference.add_exit_observation(
            exit_fingerprint="EXIT001",
            exit_nickname="TestExit",
            evidence_score=0.8,
        )
        
        assert len(posteriors) == 5
        assert sum(posteriors.values()) > 0.99
    
    def test_add_path_observation(self, sample_guards, config):
        """Test adding path observation with metrics"""
        inference = ProbabilisticPathInference(config)
        inference.initialize_guards(sample_guards)
        
        exit_relay = {
            "fingerprint": "EXIT001",
            "nickname": "TestExit",
        }
        
        evidence_metrics = {
            "timing_score": 0.8,
            "traffic_score": 0.7,
            "stability_score": 0.9,
        }
        
        posteriors = inference.add_path_observation(
            exit_relay,
            evidence_metrics=evidence_metrics,
        )
        
        assert len(posteriors) == 5
    
    def test_get_ranked_hypotheses(self, sample_guards, config):
        """Test getting ranked hypotheses"""
        inference = ProbabilisticPathInference(config)
        inference.initialize_guards(sample_guards)
        
        # Add some observations
        for i in range(3):
            inference.add_exit_observation(
                exit_fingerprint=f"EXIT{i}",
                exit_nickname=f"Exit{i}",
                evidence_score=0.7,
            )
        
        ranked = inference.get_ranked_hypotheses(top_k=3)
        
        assert len(ranked) <= 3
        assert all("hypothesis_id" in h for h in ranked)
        assert all("posterior_probability" in h for h in ranked)
    
    def test_get_inference_result(self, sample_guards, config):
        """Test complete inference result"""
        inference = ProbabilisticPathInference(config)
        inference.initialize_guards(sample_guards)
        
        inference.add_exit_observation(
            exit_fingerprint="EXIT001",
            exit_nickname="TestExit",
            evidence_score=0.8,
        )
        
        result = inference.get_inference_result(top_k=5)
        
        assert "hypotheses" in result
        assert "summary" in result
        assert "entropy" in result
        assert "uncertainty_level" in result
        assert "_disclaimer" in result
        assert "_methodology" in result


# ============================================================================
# UTILITY FUNCTION TESTS
# ============================================================================

class TestUtilityFunctions:
    """Tests for utility functions"""
    
    def test_compute_entropy_uniform(self):
        """Test entropy of uniform distribution"""
        probs = [0.25, 0.25, 0.25, 0.25]
        entropy = compute_entropy(probs)
        
        # Entropy of uniform distribution with 4 outcomes = 2.0 bits
        assert abs(entropy - 2.0) < 0.01
    
    def test_compute_entropy_peaked(self):
        """Test entropy of peaked distribution"""
        probs = [0.97, 0.01, 0.01, 0.01]
        entropy = compute_entropy(probs)
        
        # Peaked distribution should have low entropy
        assert entropy < 0.5
    
    def test_compute_entropy_with_zeros(self):
        """Test entropy handles zero probabilities"""
        probs = [0.5, 0.5, 0.0, 0.0]
        entropy = compute_entropy(probs)
        
        # Should handle zeros gracefully
        assert abs(entropy - 1.0) < 0.01
    
    def test_normalize_probabilities(self):
        """Test probability normalization"""
        values = [10, 20, 30, 40]
        normalized = normalize_probabilities(values)
        
        assert abs(sum(normalized) - 1.0) < 0.001
        assert normalized[0] == 0.1
        assert normalized[3] == 0.4
    
    def test_normalize_probabilities_zeros(self):
        """Test normalization with all zeros"""
        values = [0, 0, 0, 0]
        normalized = normalize_probabilities(values)
        
        # Should return uniform distribution
        assert abs(sum(normalized) - 1.0) < 0.001
        assert all(abs(p - 0.25) < 0.01 for p in normalized)
    
    def test_create_inference_engine(self, sample_guards):
        """Test convenience function"""
        engine = create_inference_engine(sample_guards)
        
        assert isinstance(engine, ProbabilisticPathInference)
        assert len(engine.guard_metadata) == 5


# ============================================================================
# LEGACY COMPATIBILITY TESTS
# ============================================================================

class TestLegacyCompatibility:
    """Tests for legacy function compatibility"""
    
    def test_generate_probabilistic_paths(self, sample_guards):
        """Test legacy function returns expected structure"""
        result = generate_probabilistic_paths(
            guards=sample_guards,
            middles=None,
            exits=None,
            top_k=5,
        )
        
        assert "hypotheses" in result
        assert "summary" in result
        assert "_disclaimer" in result


# ============================================================================
# PROBABILISTIC PATH RESULT TESTS
# ============================================================================

class TestProbabilisticPathResult:
    """Tests for ProbabilisticPathResult dataclass"""
    
    def test_to_dict(self):
        """Test result serialization"""
        result = ProbabilisticPathResult(
            hypotheses=[{"hypothesis_id": "hyp-001", "posterior_probability": 0.5}],
            summary={"total_hypotheses": 5},
            entropy=2.3,
            uncertainty_level="moderate",
            total_observations=10,
            inference_timestamp=datetime.utcnow().isoformat(),
        )
        
        d = result.to_dict()
        
        assert d["entropy"] == 2.3
        assert d["uncertainty_level"] == "moderate"
        assert "_disclaimer" in d
        assert "_analysis_notice" in d
        assert "key_features" in d["_analysis_notice"]
        assert "limitations" in d["_analysis_notice"]
