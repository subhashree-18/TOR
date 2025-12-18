"""
Unit Tests for Bayesian Entry Node Inference

Tests the Bayesian inference engine for computing posterior probabilities
of TOR entry nodes given evidence from path analysis.

Run with: python -m pytest tests/test_bayes_inference.py -v
"""

import pytest
from datetime import datetime, timedelta
import math
from backend.app.scoring.bayes_inference import (
    BayesianEntryInference,
    RelayInfo,
    EvidenceObservation,
    create_relay_info,
    posterior_probability_given_evidence,
)


class TestRelayInfo:
    """Test RelayInfo data structure"""
    
    def test_relay_info_creation(self):
        """Test creating relay info object"""
        relay = RelayInfo(
            fingerprint="ABC123",
            consensus_weight=1000000.0,
            uptime_days=365,
            flags=["Guard", "Running", "Valid"],
        )
        
        assert relay.fingerprint == "ABC123"
        assert relay.consensus_weight == 1000000.0
        assert relay.uptime_days == 365
        assert relay.is_guard is True
    
    def test_relay_without_guard_flag(self):
        """Test relay without Guard flag"""
        relay = RelayInfo(
            fingerprint="DEF456",
            consensus_weight=500000.0,
            uptime_days=100,
            flags=["Running", "Valid"],
        )
        
        assert relay.is_guard is False
    
    def test_relay_info_via_convenience_function(self):
        """Test creating relay info via convenience function"""
        relay = create_relay_info(
            fingerprint="GHI789",
            consensus_weight=750000.0,
            uptime_days=200,
            flags=["Guard", "Stable"],
        )
        
        assert relay.fingerprint == "GHI789"
        assert relay.is_guard is True


class TestBayesianEntryInferenceInit:
    """Test initialization of Bayesian inference engine"""
    
    def test_initialization_with_defaults(self):
        """Test engine initialization with default parameters"""
        engine = BayesianEntryInference()
        
        assert engine.likelihood_weight_time == 0.35
        assert engine.likelihood_weight_traffic == 0.40
        assert engine.likelihood_weight_stability == 0.25
        assert engine.smoothing_factor == 0.01
        assert len(engine.priors) == 0
        assert len(engine.observations) == 0
    
    def test_initialization_with_custom_weights(self):
        """Test engine initialization with custom likelihood weights"""
        engine = BayesianEntryInference(
            likelihood_weight_time=0.30,
            likelihood_weight_traffic=0.50,
            likelihood_weight_stability=0.20,
            smoothing_factor=0.02,
        )
        
        assert engine.likelihood_weight_time == 0.30
        assert engine.likelihood_weight_traffic == 0.50
        assert engine.likelihood_weight_stability == 0.20
        assert engine.smoothing_factor == 0.02


class TestPriorSetting:
    """Test setting prior probabilities from relay consensus weights"""
    
    def test_set_priors_basic(self):
        """Test setting priors from relay list"""
        engine = BayesianEntryInference()
        
        relays = [
            RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=2000.0, uptime_days=100),
            RelayInfo("relay3", consensus_weight=1000.0, uptime_days=100),
        ]
        
        engine.set_priors(relays)
        
        assert len(engine.priors) == 3
        assert "relay1" in engine.priors
        assert "relay2" in engine.priors
        assert "relay3" in engine.priors
        
        # Prior should reflect weight proportions
        # relay2 should have higher prior than relay1 (before smoothing)
        assert engine.priors["relay2"] > engine.priors["relay1"]
    
    def test_set_priors_normalize(self):
        """Test that priors normalize to sum ~1.0"""
        engine = BayesianEntryInference()
        
        relays = [
            RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=2000.0, uptime_days=100),
            RelayInfo("relay3", consensus_weight=3000.0, uptime_days=100),
        ]
        
        engine.set_priors(relays)
        
        total = sum(engine.priors.values())
        assert 0.99 <= total <= 1.01  # Allow small rounding error
    
    def test_set_priors_empty_list_error(self):
        """Test that empty relay list raises error"""
        engine = BayesianEntryInference()
        
        with pytest.raises(ValueError):
            engine.set_priors([])
    
    def test_set_priors_zero_weights_error(self):
        """Test that all-zero weights raise error"""
        engine = BayesianEntryInference()
        
        relays = [
            RelayInfo("relay1", consensus_weight=0.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=0.0, uptime_days=100),
        ]
        
        with pytest.raises(ValueError):
            engine.set_priors(relays)


class TestEvidenceUpdate:
    """Test updating evidence for relays"""
    
    def test_update_evidence_basic(self):
        """Test basic evidence update"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100),
        ]
        engine.set_priors(relays)
        
        relay = relays[0]
        engine.update_evidence(
            entry_relay=relay,
            time_overlap=0.8,
            traffic_similarity=0.7,
            stability=0.9,
            exit_node_observed="exit1",
        )
        
        assert engine.stats["relay1"]["observation_count"] == 1
        assert "exit1" in engine.stats["relay1"]["exit_nodes_observed_with"]
    
    def test_update_evidence_invalid_likelihood_time(self):
        """Test that invalid time overlap likelihood raises error"""
        engine = BayesianEntryInference()
        relays = [RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100)]
        engine.set_priors(relays)
        
        with pytest.raises(ValueError):
            engine.update_evidence(
                entry_relay=relays[0],
                time_overlap=1.5,  # > 1.0
                traffic_similarity=0.7,
                stability=0.9,
                exit_node_observed="exit1",
            )
    
    def test_update_evidence_no_prior_error(self):
        """Test that updating evidence for relay without prior raises error"""
        engine = BayesianEntryInference()
        
        relay_no_prior = RelayInfo("relay999", consensus_weight=1000.0, uptime_days=100)
        
        with pytest.raises(ValueError):
            engine.update_evidence(
                entry_relay=relay_no_prior,
                time_overlap=0.8,
                traffic_similarity=0.7,
                stability=0.9,
                exit_node_observed="exit1",
            )
    
    def test_update_evidence_multiple_observations(self):
        """Test updating evidence multiple times"""
        engine = BayesianEntryInference()
        relays = [RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100)]
        engine.set_priors(relays)
        
        relay = relays[0]
        
        # Add multiple observations
        for i in range(5):
            engine.update_evidence(
                entry_relay=relay,
                time_overlap=0.7 + i * 0.02,
                traffic_similarity=0.6 + i * 0.03,
                stability=0.8 + i * 0.01,
                exit_node_observed=f"exit{i}",
            )
        
        assert engine.stats["relay1"]["observation_count"] == 5
        assert len(engine.stats["relay1"]["exit_nodes_observed_with"]) == 5


class TestPosteriorComputation:
    """Test posterior probability computation"""
    
    def test_posterior_no_observations(self):
        """Test posterior equals prior when no observations"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=2000.0, uptime_days=100),
        ]
        engine.set_priors(relays)
        
        # No observations yet
        post1 = engine.posterior_probability("relay1")
        prior1 = engine.priors["relay1"]
        
        # With no observations, likelihood is 0.5 (neutral)
        # So posterior should be proportional to prior
        assert post1 > 0.0
        assert post1 <= 1.0
    
    def test_posterior_with_strong_evidence(self):
        """Test posterior updates with strong evidence"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=1000.0, uptime_days=100),  # Equal prior
        ]
        engine.set_priors(relays)
        
        # Add strong evidence for relay1
        engine.update_evidence(
            entry_relay=relays[0],
            time_overlap=0.9,
            traffic_similarity=0.95,
            stability=0.85,
            exit_node_observed="exit1",
        )
        
        post1 = engine.posterior_probability("relay1")
        post2 = engine.posterior_probability("relay2")
        
        # relay1 should have higher posterior than relay2
        assert post1 > post2
    
    def test_posterior_caching(self):
        """Test that posteriors are cached"""
        engine = BayesianEntryInference()
        relays = [RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100)]
        engine.set_priors(relays)
        
        # First call computes
        post1 = engine.posterior_probability("relay1")
        assert engine._cache_valid is True
        
        # Second call should use cache
        post2 = engine.posterior_probability("relay1")
        assert post1 == post2
        
        # Adding evidence invalidates cache
        engine.update_evidence(
            entry_relay=relays[0],
            time_overlap=0.8,
            traffic_similarity=0.7,
            stability=0.9,
            exit_node_observed="exit1",
        )
        assert engine._cache_valid is False
    
    def test_posterior_normalized(self):
        """Test that posteriors sum to approximately 1.0"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo(f"relay{i}", consensus_weight=1000.0, uptime_days=100)
            for i in range(5)
        ]
        engine.set_priors(relays)
        
        # Add observations
        for i, relay in enumerate(relays):
            engine.update_evidence(
                entry_relay=relay,
                time_overlap=0.5 + i * 0.1,
                traffic_similarity=0.6 + i * 0.05,
                stability=0.7 + i * 0.02,
                exit_node_observed="exit1",
            )
        
        posteriors = engine.posterior_probabilities()
        total = sum(posteriors.values())
        
        assert 0.99 <= total <= 1.01


class TestRankedEntries:
    """Test ranking entries by posterior probability"""
    
    def test_ranked_entries_ordering(self):
        """Test entries are ranked by posterior descending"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=1000.0, uptime_days=100),
            RelayInfo("relay3", consensus_weight=1000.0, uptime_days=100),
        ]
        engine.set_priors(relays)
        
        # Add evidence: relay1 strongest, relay2 medium, relay3 weakest
        for relay, strength in zip(relays, [0.9, 0.6, 0.3]):
            engine.update_evidence(
                entry_relay=relay,
                time_overlap=strength,
                traffic_similarity=strength,
                stability=strength,
                exit_node_observed="exit1",
            )
        
        ranked = engine.ranked_entries()
        
        # Check ordering
        assert ranked[0][0] == "relay1"
        assert ranked[1][0] == "relay2"
        assert ranked[2][0] == "relay3"
        
        # Check probabilities descending
        assert ranked[0][1] >= ranked[1][1] >= ranked[2][1]
    
    def test_ranked_entries_top_k(self):
        """Test top_k parameter"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo(f"relay{i}", consensus_weight=1000.0, uptime_days=100)
            for i in range(10)
        ]
        engine.set_priors(relays)
        
        ranked = engine.ranked_entries(top_k=3)
        
        assert len(ranked) == 3
        assert all(isinstance(x, tuple) and len(x) == 2 for x in ranked)


class TestEntrySummary:
    """Test entry relay summary generation"""
    
    def test_entry_summary_basic(self):
        """Test basic entry summary"""
        engine = BayesianEntryInference()
        relays = [RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100)]
        engine.set_priors(relays)
        
        engine.update_evidence(
            entry_relay=relays[0],
            time_overlap=0.8,
            traffic_similarity=0.7,
            stability=0.9,
            exit_node_observed="exit1",
        )
        
        summary = engine.entry_summary("relay1")
        
        assert summary["fingerprint"] == "relay1"
        assert "prior_probability" in summary
        assert "posterior_probability" in summary
        assert "likelihood_ratio" in summary
        assert "observation_count" in summary
        assert "average_evidence" in summary
        assert "confidence_level" in summary
    
    def test_entry_summary_invalid_fingerprint(self):
        """Test summary for non-existent relay raises error"""
        engine = BayesianEntryInference()
        
        with pytest.raises(ValueError):
            engine.entry_summary("nonexistent")


class TestConfidenceAssessment:
    """Test confidence level assessment"""
    
    def test_confidence_very_low_no_observations(self):
        """Test very_low confidence with no observations"""
        engine = BayesianEntryInference()
        relays = [RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100)]
        engine.set_priors(relays)
        
        confidence = engine._assess_confidence(
            observation_count=0,
            posterior=0.5,
            prior=0.5,
        )
        
        assert confidence == "very_low"
    
    def test_confidence_high_with_many_observations(self):
        """Test higher confidence with many observations"""
        engine = BayesianEntryInference()
        
        confidence = engine._assess_confidence(
            observation_count=10,
            posterior=0.95,
            prior=0.1,
        )
        
        assert confidence in ["high", "very_high"]


class TestDynamicUpdateOnExit:
    """Test dynamic update when new exit node observed"""
    
    def test_dynamic_update_on_exit_basic(self):
        """Test basic dynamic update on exit observation"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=1000.0, uptime_days=100),
        ]
        engine.set_priors(relays)
        
        candidates = [
            (relays[0], 0.8, 0.7, 0.9),
            (relays[1], 0.4, 0.3, 0.5),
        ]
        
        posteriors = engine.dynamic_update_on_exit("exit1", candidates)
        
        assert len(posteriors) == 2
        assert "relay1" in posteriors
        assert "relay2" in posteriors
        
        # relay1 should have higher posterior
        assert posteriors["relay1"] > posteriors["relay2"]
    
    def test_dynamic_update_on_exit_empty_candidates(self):
        """Test dynamic update with no candidates"""
        engine = BayesianEntryInference()
        
        posteriors = engine.dynamic_update_on_exit("exit1", [])
        
        assert posteriors == {}


class TestHighestProbabilityEntry:
    """Test getting entry with highest probability"""
    
    def test_get_highest_probability_entry(self):
        """Test getting entry with max posterior"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=2000.0, uptime_days=100),
        ]
        engine.set_priors(relays)
        
        # Add evidence: relay2 stronger
        engine.update_evidence(
            entry_relay=relays[1],
            time_overlap=0.9,
            traffic_similarity=0.8,
            stability=0.85,
            exit_node_observed="exit1",
        )
        
        highest = engine.get_highest_probability_entry()
        
        assert highest is not None
        assert highest[0] == "relay2"
        assert highest[1] > 0.0


class TestEntropy:
    """Test Shannon entropy computation"""
    
    def test_entropy_uniform_distribution(self):
        """Test entropy for uniform distribution"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo(f"relay{i}", consensus_weight=1000.0, uptime_days=100)
            for i in range(4)
        ]
        engine.set_priors(relays)
        
        # No evidence added: posteriors should be uniform
        entropy = engine.entropy()
        
        # Uniform distribution over 4 items has entropy ln(4) ≈ 1.386
        expected_entropy = math.log(4)
        assert 1.0 < entropy < 1.5
    
    def test_entropy_peaked_distribution(self):
        """Test entropy for peaked distribution"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo("relay1", consensus_weight=10000.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=100.0, uptime_days=100),
        ]
        engine.set_priors(relays)
        
        entropy = engine.entropy()
        
        # Peaked distribution has lower entropy
        assert entropy < 0.5


class TestDiagnosticReport:
    """Test diagnostic report generation"""
    
    def test_diagnostic_report_basic(self):
        """Test diagnostic report structure"""
        engine = BayesianEntryInference()
        relays = [
            RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=2000.0, uptime_days=100),
        ]
        engine.set_priors(relays)
        
        engine.update_evidence(
            entry_relay=relays[0],
            time_overlap=0.8,
            traffic_similarity=0.7,
            stability=0.9,
            exit_node_observed="exit1",
        )
        
        report = engine.diagnostic_report()
        
        assert "engine_state" in report
        assert "likelihood_weights" in report
        assert "posterior_distribution" in report
        assert "top_5_entries" in report
        assert report["engine_state"]["total_relays"] == 2
        assert report["engine_state"]["relays_with_observations"] == 1


class TestConvenienceFunction:
    """Test convenience function for single computation"""
    
    def test_posterior_probability_given_evidence(self):
        """Test convenience function for posterior computation"""
        relays = [
            RelayInfo("relay1", consensus_weight=1000.0, uptime_days=100),
            RelayInfo("relay2", consensus_weight=2000.0, uptime_days=100),
        ]
        
        posterior = posterior_probability_given_evidence(
            entry_relay=relays[0],
            all_relays=relays,
            time_overlap=0.8,
            traffic_similarity=0.7,
            stability=0.9,
            exit_observed="exit1",
        )
        
        assert 0.0 <= posterior <= 1.0


class TestBayesianWithRealWorldScenario:
    """Integration tests with realistic scenarios"""
    
    def test_circuit_path_identification(self):
        """Test realistic circuit path identification scenario"""
        # Create pool of potential guard nodes
        guards = [
            RelayInfo("guard_a", consensus_weight=5000.0, uptime_days=365, flags=["Guard"]),
            RelayInfo("guard_b", consensus_weight=3000.0, uptime_days=200, flags=["Guard"]),
            RelayInfo("guard_c", consensus_weight=2000.0, uptime_days=100, flags=["Guard"]),
        ]
        
        engine = BayesianEntryInference()
        engine.set_priors(guards)
        
        # Simulate observing circuits with exit node X
        # Circuit 1: strong match with guard_a
        engine.update_evidence(
            entry_relay=guards[0],
            time_overlap=0.9,
            traffic_similarity=0.85,
            stability=0.9,
            exit_node_observed="exit_x",
        )
        
        # Circuit 2: weak match with guard_b
        engine.update_evidence(
            entry_relay=guards[1],
            time_overlap=0.4,
            traffic_similarity=0.3,
            stability=0.5,
            exit_node_observed="exit_x",
        )
        
        # Circuit 3: strong match with guard_a again
        engine.update_evidence(
            entry_relay=guards[0],
            time_overlap=0.88,
            traffic_similarity=0.82,
            stability=0.88,
            exit_node_observed="exit_x",
        )
        
        # Check results
        ranked = engine.ranked_entries()
        assert ranked[0][0] == "guard_a"  # Most evidence points to guard_a
        assert ranked[0][1] > ranked[1][1]  # guard_a has higher posterior
        
        # Diagnostic check
        report = engine.diagnostic_report()
        assert report["engine_state"]["total_observations"] == 3


# ============================================================================
# PERSISTENCE AND STATE MANAGEMENT TESTS
# ============================================================================

class TestBayesianStatePersistence:
    """Tests for export/import state functionality"""
    
    def test_export_state_basic(self):
        """Test exporting basic state"""
        guards = [
            RelayInfo("guard_a", consensus_weight=5000.0, uptime_days=365, flags=["Guard"]),
            RelayInfo("guard_b", consensus_weight=3000.0, uptime_days=200, flags=["Guard"]),
        ]
        
        engine = BayesianEntryInference()
        engine.set_priors(guards)
        
        # Add some evidence
        engine.update_evidence(
            entry_relay=guards[0],
            time_overlap=0.8,
            traffic_similarity=0.7,
            stability=0.85,
            exit_node_observed="exit_x",
        )
        
        # Export state
        state = engine.export_state()
        
        assert "priors" in state
        assert "observations" in state
        assert "stats" in state
        assert "config" in state
        
        # Check priors were saved
        assert "guard_a" in state["priors"]
        assert "guard_b" in state["priors"]
        
        # Check observations were saved
        assert "guard_a" in state["observations"]
        assert len(state["observations"]["guard_a"]) == 1
        
        # Check config
        assert state["config"]["likelihood_weight_time"] == 0.35
    
    def test_import_state_roundtrip(self):
        """Test that export/import preserves state"""
        guards = [
            RelayInfo("guard_a", consensus_weight=5000.0, uptime_days=365, flags=["Guard"]),
            RelayInfo("guard_b", consensus_weight=3000.0, uptime_days=200, flags=["Guard"]),
        ]
        
        # Create and populate engine
        engine1 = BayesianEntryInference()
        engine1.set_priors(guards)
        engine1.update_evidence(
            entry_relay=guards[0],
            time_overlap=0.8,
            traffic_similarity=0.7,
            stability=0.85,
            exit_node_observed="exit_x",
        )
        engine1.update_evidence(
            entry_relay=guards[1],
            time_overlap=0.5,
            traffic_similarity=0.6,
            stability=0.5,
            exit_node_observed="exit_y",
        )
        
        # Get posteriors before export
        post_a_before = engine1.posterior_probability("guard_a")
        post_b_before = engine1.posterior_probability("guard_b")
        
        # Export and import
        state = engine1.export_state()
        
        engine2 = BayesianEntryInference()
        engine2.import_state(state)
        
        # Check posteriors are the same
        post_a_after = engine2.posterior_probability("guard_a")
        post_b_after = engine2.posterior_probability("guard_b")
        
        assert abs(post_a_before - post_a_after) < 0.0001
        assert abs(post_b_before - post_b_after) < 0.0001
        
        # Check statistics
        assert engine2.stats["guard_a"]["observation_count"] == 1
        assert engine2.stats["guard_b"]["observation_count"] == 1
    
    def test_import_empty_state_raises(self):
        """Test that importing empty state raises error"""
        engine = BayesianEntryInference()
        
        with pytest.raises(ValueError, match="empty"):
            engine.import_state({})
        
        with pytest.raises(ValueError, match="empty"):
            engine.import_state(None)
    
    def test_import_state_preserves_config(self):
        """Test that import preserves configuration"""
        state = {
            "priors": {"guard_a": 0.5, "guard_b": 0.5},
            "observations": {},
            "stats": {},
            "config": {
                "likelihood_weight_time": 0.5,
                "likelihood_weight_traffic": 0.3,
                "likelihood_weight_stability": 0.2,
                "smoothing_factor": 0.02,
            },
        }
        
        engine = BayesianEntryInference()
        engine.import_state(state)
        
        assert engine.likelihood_weight_time == 0.5
        assert engine.likelihood_weight_traffic == 0.3
        assert engine.likelihood_weight_stability == 0.2
        assert engine.smoothing_factor == 0.02
    
    def test_incremental_update_after_import(self):
        """Test adding new evidence after importing state"""
        guards = [
            RelayInfo("guard_a", consensus_weight=5000.0, uptime_days=365, flags=["Guard"]),
            RelayInfo("guard_b", consensus_weight=3000.0, uptime_days=200, flags=["Guard"]),
        ]
        
        # Create initial engine with evidence
        engine1 = BayesianEntryInference()
        engine1.set_priors(guards)
        engine1.update_evidence(
            entry_relay=guards[0],
            time_overlap=0.6,
            traffic_similarity=0.6,
            stability=0.6,
            exit_node_observed="exit_x",
        )
        
        # Export and import to new engine
        state = engine1.export_state()
        engine2 = BayesianEntryInference()
        engine2.import_state(state)
        
        # Add new evidence to engine2
        engine2.update_evidence(
            entry_relay=guards[0],
            time_overlap=0.9,
            traffic_similarity=0.9,
            stability=0.9,
            exit_node_observed="exit_y",
        )
        
        # Should have 2 observations now
        assert engine2.stats["guard_a"]["observation_count"] == 2
        
        # Posterior should be higher due to strong new evidence
        assert engine2.posterior_probability("guard_a") > engine1.posterior_probability("guard_a")
    
    def test_get_observation_count(self):
        """Test observation count getter"""
        guards = [
            RelayInfo("guard_a", consensus_weight=5000.0, uptime_days=365, flags=["Guard"]),
            RelayInfo("guard_b", consensus_weight=3000.0, uptime_days=200, flags=["Guard"]),
        ]
        
        engine = BayesianEntryInference()
        engine.set_priors(guards)
        
        assert engine.get_observation_count() == 0
        assert engine.get_observation_count("guard_a") == 0
        
        engine.update_evidence(
            entry_relay=guards[0],
            time_overlap=0.8,
            traffic_similarity=0.7,
            stability=0.85,
            exit_node_observed="exit_x",
        )
        
        assert engine.get_observation_count() == 1
        assert engine.get_observation_count("guard_a") == 1
        assert engine.get_observation_count("guard_b") == 0
        
        engine.update_evidence(
            entry_relay=guards[0],
            time_overlap=0.7,
            traffic_similarity=0.8,
            stability=0.75,
            exit_node_observed="exit_y",
        )
        
        assert engine.get_observation_count() == 2
        assert engine.get_observation_count("guard_a") == 2
    
    def test_merge_with_investigation(self):
        """Test merging investigation data into engine"""
        guards = [
            RelayInfo("guard_a", consensus_weight=5000.0, uptime_days=365, flags=["Guard"]),
            RelayInfo("guard_b", consensus_weight=3000.0, uptime_days=200, flags=["Guard"]),
        ]
        
        engine = BayesianEntryInference()
        engine.set_priors(guards)
        
        # Simulate data from investigation
        investigation_data = {
            "guard_a": {
                "current_prior": 0.6,
                "update_count": 5,
                "avg_time_overlap": 0.75,
                "avg_traffic_similarity": 0.8,
                "avg_stability": 0.7,
                "associated_exit_nodes": ["exit_1", "exit_2"],
            },
            "guard_c": {  # New guard not in original priors
                "current_prior": 0.001,
                "update_count": 2,
                "avg_time_overlap": 0.5,
                "avg_traffic_similarity": 0.5,
                "avg_stability": 0.5,
                "associated_exit_nodes": ["exit_3"],
            },
        }
        
        engine.merge_with_investigation(investigation_data)
        
        # Check guard_a stats were merged
        assert engine.stats["guard_a"]["observation_count"] == 5
        assert engine.stats["guard_a"]["avg_time_likelihood"] == 0.75
        assert "exit_1" in engine.stats["guard_a"]["exit_nodes_observed_with"]
        
        # Check guard_c was added
        assert "guard_c" in engine.priors
        assert engine.stats["guard_c"]["observation_count"] == 2


class TestCreateInferenceFromInvestigation:
    """Tests for convenience function"""
    
    def test_create_from_empty_state(self):
        """Test creating engine from empty state"""
        from backend.app.scoring.bayes_inference import create_inference_from_investigation
        
        engine = create_inference_from_investigation(None)
        
        assert len(engine.priors) == 0
        assert len(engine.observations) == 0
    
    def test_create_from_saved_state(self):
        """Test creating engine from saved state"""
        from backend.app.scoring.bayes_inference import create_inference_from_investigation
        
        state = {
            "priors": {"guard_a": 0.6, "guard_b": 0.4},
            "observations": {
                "guard_a": [{
                    "timestamp": "2024-01-15T10:30:00",
                    "time_overlap_likelihood": 0.8,
                    "traffic_similarity_likelihood": 0.7,
                    "stability_likelihood": 0.75,
                    "exit_node_observed": "exit_x",
                }],
            },
            "stats": {
                "guard_a": {
                    "observation_count": 1,
                    "avg_time_likelihood": 0.8,
                    "avg_traffic_likelihood": 0.7,
                    "avg_stability_likelihood": 0.75,
                    "exit_nodes_observed_with": ["exit_x"],
                },
            },
            "config": {
                "likelihood_weight_time": 0.35,
                "likelihood_weight_traffic": 0.40,
                "likelihood_weight_stability": 0.25,
                "smoothing_factor": 0.01,
            },
        }
        
        engine = create_inference_from_investigation(state)
        
        assert "guard_a" in engine.priors
        assert engine.stats["guard_a"]["observation_count"] == 1
        assert len(engine.observations["guard_a"]) == 1
