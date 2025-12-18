"""
Unit Tests for Independent Evidence Metrics

Tests each scoring function independently with various scenarios
to ensure they return valid normalized values (0.0-1.0).

Run with: python -m pytest tests/test_evidence.py -v
"""

import pytest
from datetime import datetime, timedelta
from backend.app.scoring.evidence import (
    time_overlap_score,
    traffic_similarity_score,
    relay_stability_score,
    path_consistency_score,
    geo_plausibility_score,
    compute_evidence_summary,
)


class TestTimeOverlapScore:
    """Test temporal alignment metrics"""
    
    def test_perfect_overlap(self):
        """Relays with perfect temporal overlap"""
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)
        
        result = time_overlap_score(
            entry_uptime=(start, end),
            middle_uptime=(start, end),
            exit_uptime=(start, end),
        )
        
        assert result["value"] >= 0.7
        assert result["details"]["overlap_days"] == 9.0
        assert result["details"]["all_concurrent"] is True
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["confidence"] > 0.5
    
    def test_partial_overlap(self):
        """Relays with partial temporal overlap"""
        result = time_overlap_score(
            entry_uptime=(datetime(2024, 1, 1), datetime(2024, 1, 15)),
            middle_uptime=(datetime(2024, 1, 5), datetime(2024, 1, 20)),
            exit_uptime=(datetime(2024, 1, 10), datetime(2024, 1, 25)),
        )
        
        # Only days 10-15 overlap
        assert 0 < result["value"] <= 1.0
        assert result["details"]["overlap_days"] == 5.0
        assert result["details"]["all_concurrent"] is True
    
    def test_no_overlap(self):
        """Relays with no temporal overlap"""
        result = time_overlap_score(
            entry_uptime=(datetime(2024, 1, 1), datetime(2024, 1, 5)),
            middle_uptime=(datetime(2024, 1, 10), datetime(2024, 1, 15)),
            exit_uptime=(datetime(2024, 1, 20), datetime(2024, 1, 25)),
        )
        
        assert result["value"] == 0.0
        assert result["details"]["overlap_days"] == 0.0
        assert result["details"]["all_concurrent"] is False
    
    def test_missing_data(self):
        """Handle missing uptime data gracefully"""
        result = time_overlap_score(
            entry_uptime=(None, None),
            middle_uptime=(datetime(2024, 1, 1), datetime(2024, 1, 10)),
            exit_uptime=(datetime(2024, 1, 1), datetime(2024, 1, 10)),
        )
        
        assert result["value"] == 0.0
        assert result["confidence"] == 0.0
        assert "error" in result["details"]
    
    def test_value_range(self):
        """Result is always in valid normalized range"""
        for i in range(10):
            start_offset = i
            result = time_overlap_score(
                entry_uptime=(datetime(2024, 1, 1), datetime(2024, 1, 20)),
                middle_uptime=(datetime(2024, 1, 1 + start_offset), datetime(2024, 1, 15)),
                exit_uptime=(datetime(2024, 1, 5), datetime(2024, 1, 25)),
            )
            
            assert 0.0 <= result["value"] <= 1.0
            assert 0.0 <= result["confidence"] <= 1.0


class TestTrafficSimilarityScore:
    """Test traffic pattern analysis"""
    
    def test_balanced_traffic(self):
        """Similar bandwidth across path"""
        result = traffic_similarity_score(
            entry_observed_bandwidth=3e6,  # 3 Mbps
            middle_observed_bandwidth=3e6,
            exit_observed_bandwidth=3e6,
            entry_advertised_bandwidth=5e6,
            middle_advertised_bandwidth=5e6,
            exit_advertised_bandwidth=5e6,
        )
        
        assert result["value"] > 0.7
        assert result["details"]["bandwidth_balance"] == "well-balanced"
        assert result["details"]["suspicious_spike"] is False
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_unbalanced_traffic(self):
        """Disparate bandwidth across path"""
        result = traffic_similarity_score(
            entry_observed_bandwidth=1e6,  # 1 Mbps
            middle_observed_bandwidth=10e6,  # 10 Mbps
            exit_observed_bandwidth=0.5e6,  # 0.5 Mbps
            entry_advertised_bandwidth=5e6,
            middle_advertised_bandwidth=20e6,
            exit_advertised_bandwidth=5e6,
        )
        
        assert result["value"] < 0.5
        assert result["details"]["bandwidth_balance"] == "unbalanced"
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_suspicious_spike(self):
        """Detect abnormal bandwidth spike"""
        result = traffic_similarity_score(
            entry_observed_bandwidth=1e6,
            middle_observed_bandwidth=100e6,  # Huge spike
            exit_observed_bandwidth=1e6,
            entry_advertised_bandwidth=5e6,
            middle_advertised_bandwidth=20e6,
            exit_advertised_bandwidth=5e6,
        )
        
        assert result["details"]["suspicious_spike"] is True
        assert result["value"] < 0.6
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_zero_traffic(self):
        """Handle zero bandwidth gracefully"""
        result = traffic_similarity_score(
            entry_observed_bandwidth=0,
            middle_observed_bandwidth=0,
            exit_observed_bandwidth=0,
        )
        
        assert result["value"] == 0.1
        assert 0.0 <= result["value"] <= 1.0
    
    def test_value_range(self):
        """Result is always normalized"""
        for obs_bw in [0, 1e6, 10e6, 100e6, 1e9]:
            result = traffic_similarity_score(
                entry_observed_bandwidth=obs_bw,
                middle_observed_bandwidth=obs_bw,
                exit_observed_bandwidth=obs_bw,
            )
            
            assert 0.0 <= result["value"] <= 1.0


class TestRelayStabilityScore:
    """Test relay infrastructure stability"""
    
    def test_stable_relays(self):
        """Established relays with long uptime"""
        result = relay_stability_score(
            entry_uptime_days=90.0,
            middle_uptime_days=120.0,
            exit_uptime_days=60.0,
            entry_tor_flags=["Running", "Valid", "Stable", "Guard"],
            middle_tor_flags=["Running", "Valid", "Stable"],
            exit_tor_flags=["Running", "Valid", "Stable", "Exit"],
        )
        
        assert result["value"] > 0.7
        assert result["details"]["all_have_stable_flag"] is True
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["confidence"] > 0.5
    
    def test_new_relays(self):
        """Recently deployed relays"""
        result = relay_stability_score(
            entry_uptime_days=1.0,
            middle_uptime_days=2.0,
            exit_uptime_days=0.5,
        )
        
        assert result["value"] < 0.3
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_mixed_stability(self):
        """Mix of established and new relays"""
        result = relay_stability_score(
            entry_uptime_days=30.0,
            middle_uptime_days=1.0,
            exit_uptime_days=60.0,
            entry_tor_flags=["Running", "Valid", "Stable"],
            exit_tor_flags=["Running", "Valid", "Stable"],
        )
        
        assert 0.3 < result["value"] < 0.9
        assert result["details"]["all_have_stable_flag"] is False
    
    def test_no_flags_available(self):
        """Handle case with no flag data"""
        result = relay_stability_score(
            entry_uptime_days=30.0,
            middle_uptime_days=30.0,
            exit_uptime_days=30.0,
        )
        
        assert 0.0 <= result["value"] <= 1.0
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_value_range(self):
        """Result is always normalized"""
        for uptime in [0.1, 1, 7, 30, 90, 180, 365]:
            result = relay_stability_score(
                entry_uptime_days=uptime,
                middle_uptime_days=uptime,
                exit_uptime_days=uptime,
            )
            
            assert 0.0 <= result["value"] <= 1.0


class TestPathConsistencyScore:
    """Test path architecture plausibility"""
    
    def test_diverse_path(self):
        """Path with good diversity (different AS, countries, operators)"""
        result = path_consistency_score(
            entry_exit_as_different=True,
            entry_middle_as_different=True,
            middle_exit_as_different=True,
            entry_exit_country_different=True,
            entry_middle_country_different=True,
            middle_exit_country_different=True,
            family_independent=True,
            entry_exit_same_provider_risk=False,
        )
        
        assert result["value"] > 0.7
        assert result["details"]["as_diversity_score"] == 1.0
        assert result["details"]["geographic_diversity_score"] == 1.0
        assert result["details"]["operator_independence_score"] > 0.8
    
    def test_concentrated_path(self):
        """Path with poor diversity (same AS, country, operator)"""
        result = path_consistency_score(
            entry_exit_as_different=False,
            entry_middle_as_different=False,
            middle_exit_as_different=False,
            entry_exit_country_different=False,
            entry_middle_country_different=False,
            middle_exit_country_different=False,
            family_independent=False,
            entry_exit_same_provider_risk=True,
        )
        
        assert result["value"] < 0.3
        assert result["details"]["risk_level"] == "high"
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_partial_diversity(self):
        """Path with mixed diversity"""
        result = path_consistency_score(
            entry_exit_as_different=True,
            entry_middle_as_different=False,
            middle_exit_as_different=True,
            entry_exit_country_different=True,
            entry_middle_country_different=False,
            middle_exit_country_different=True,
            family_independent=True,
        )
        
        assert 0.3 < result["value"] < 0.9
    
    def test_value_range(self):
        """Result is always normalized"""
        for as_diverse in [True, False]:
            for country_diverse in [True, False]:
                for family_indep in [True, False]:
                    result = path_consistency_score(
                        entry_exit_as_different=as_diverse,
                        entry_middle_as_different=as_diverse,
                        middle_exit_as_different=as_diverse,
                        entry_exit_country_different=country_diverse,
                        entry_middle_country_different=country_diverse,
                        middle_exit_country_different=country_diverse,
                        family_independent=family_indep,
                    )
                    
                    assert 0.0 <= result["value"] <= 1.0


class TestGeoPlausibilityScore:
    """Test geographic distribution analysis"""
    
    def test_diverse_countries(self):
        """Relays in different countries (good)"""
        result = geo_plausibility_score(
            entry_country="US",
            middle_country="NL",
            exit_country="JP",
        )
        
        assert result["value"] > 0.6
        assert len(result["details"]["jurisdictional_concerns"]) == 0
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_same_country_all(self):
        """All relays in same country (risky)"""
        result = geo_plausibility_score(
            entry_country="US",
            middle_country="US",
            exit_country="US",
        )
        
        assert result["value"] < 0.2
        assert "all_same_country" in result["details"]["jurisdictional_concerns"]
    
    def test_entry_exit_same_country(self):
        """Entry and exit in same country (observation risk)"""
        result = geo_plausibility_score(
            entry_country="US",
            middle_country="NL",
            exit_country="US",
        )
        
        assert result["value"] < 0.5
        assert "entry_exit_same_country" in result["details"]["jurisdictional_concerns"]
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_high_risk_countries(self):
        """Relays in high-risk countries (censorship)"""
        result = geo_plausibility_score(
            entry_country="CN",
            middle_country="RU",
            exit_country="IR",
        )
        
        assert result["value"] < 0.5
        assert "entry_high_risk_country" in result["details"]["jurisdictional_concerns"]
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_with_coordinates(self):
        """Geographic calculation with coordinates"""
        result = geo_plausibility_score(
            entry_country="US",
            middle_country="NL",
            exit_country="JP",
            entry_latitude=40.7128,  # New York
            entry_longitude=-74.0060,
            middle_latitude=52.3676,  # Amsterdam
            middle_longitude=4.9041,
            exit_latitude=35.6762,  # Tokyo
            exit_longitude=139.6503,
        )
        
        assert result["value"] > 0.6
        assert result["details"]["geo_distance_km"] is not None
        assert result["details"]["estimated_latency_ms"] is not None
        assert 0.0 <= result["confidence"] <= 1.0
        assert result["confidence"] > 0.4
    
    def test_latency_implausibility(self):
        """Detect implausible latency"""
        result = geo_plausibility_score(
            entry_country="US",
            middle_country="NL",
            exit_country="JP",
            entry_latitude=40.7128,
            entry_longitude=-74.0060,
            middle_latitude=52.3676,
            middle_longitude=4.9041,
            exit_latitude=35.6762,
            exit_longitude=139.6503,
            network_latency_ms=1.0,  # Unrealistically low
        )
        
        assert result["value"] < 0.6
        assert "latency_implausible" in result["details"]["jurisdictional_concerns"]
        assert result["details"]["latency_plausible"] is False
    
    def test_value_range(self):
        """Result is always normalized"""
        for entry_c in ["US", "CN", "RU"]:
            for middle_c in ["US", "NL", "RU"]:
                for exit_c in ["JP", "IR", "US"]:
                    result = geo_plausibility_score(
                        entry_country=entry_c,
                        middle_country=middle_c,
                        exit_country=exit_c,
                    )
                    
                    assert 0.0 <= result["value"] <= 1.0


class TestEvidenceSummary:
    """Test aggregation of evidence metrics"""
    
    def test_high_confidence_case(self):
        """All metrics indicate high confidence"""
        summary = compute_evidence_summary(
            time_overlap={"value": 0.8, "confidence": 0.9, "details": {}},
            traffic_similarity={"value": 0.75, "confidence": 0.9, "details": {}},
            relay_stability={"value": 0.85, "confidence": 0.9, "details": {}},
            path_consistency={"value": 0.8, "confidence": 0.9, "details": {}},
            geo_plausibility={"value": 0.75, "confidence": 0.9, "details": {}},
        )
        
        assert summary["evidence_quality"] in ["high", "very_high"]
        assert summary["overall_confidence"] > 0.6
        assert len(summary["high_confidence_indicators"]) > 2
        assert summary["recommendation"].startswith(("High confidence", "Moderate confidence"))
    
    def test_low_confidence_case(self):
        """All metrics indicate low confidence"""
        summary = compute_evidence_summary(
            time_overlap={"value": 0.2, "confidence": 0.1, "details": {}},
            traffic_similarity={"value": 0.1, "confidence": 0.1, "details": {}},
            relay_stability={"value": 0.15, "confidence": 0.1, "details": {}},
            path_consistency={"value": 0.2, "confidence": 0.1, "details": {}},
            geo_plausibility={"value": 0.1, "confidence": 0.1, "details": {}},
        )
        
        assert summary["evidence_quality"] in ["low", "very_low"]
        assert any(text in summary["recommendation"] for text in ["Low confidence", "Mixed evidence", "further investigation"])
    
    def test_mixed_confidence_case(self):
        """Mixed confidence levels"""
        summary = compute_evidence_summary(
            time_overlap={"value": 0.7, "confidence": 0.75, "details": {}},
            traffic_similarity={"value": 0.5, "confidence": 0.5, "details": {}},
            relay_stability={"value": 0.6, "confidence": 0.65, "details": {}},
            path_consistency={"value": 0.4, "confidence": 0.35, "details": {}},
            geo_plausibility={"value": 0.65, "confidence": 0.55, "details": {}},
        )
        
        assert summary["evidence_quality"] in ["very_high", "high", "medium", "low", "very_low"]
        assert "overall_confidence" in summary
        assert "component_details" in summary
        assert all(k in summary["metrics"] for k in [
            "time_overlap", "traffic_similarity", "relay_stability",
            "path_consistency", "geo_plausibility"
        ])
    
    def test_has_risk_indicators(self):
        """Summary includes risk indicators"""
        summary = compute_evidence_summary(
            time_overlap={"value": 0.2, "confidence": 0.2, "details": {}},
            traffic_similarity={
                "value": 0.5,
                "confidence": 0.6,
                "details": {"suspicious_spike": True}
            },
            relay_stability={"value": 0.6, "confidence": 0.7, "details": {}},
            path_consistency={
                "value": 0.3,
                "confidence": 0.7,
                "details": {
                    "diversity_flags": {
                        "entry_exit_same_provider_risk": True
                    }
                }
            },
            geo_plausibility={
                "value": 0.2,
                "confidence": 0.7,
                "details": {
                    "jurisdictional_concerns": ["entry_high_risk_country"]
                }
            },
        )
        
        assert len(summary["risk_indicators"]) > 0
    
    def test_summary_structure(self):
        """Summary has expected structure"""
        summary = compute_evidence_summary(
            time_overlap={"value": 0.5, "confidence": 0.5, "details": {}},
            traffic_similarity={"value": 0.5, "confidence": 0.5, "details": {}},
            relay_stability={"value": 0.5, "confidence": 0.5, "details": {}},
            path_consistency={"value": 0.5, "confidence": 0.5, "details": {}},
            geo_plausibility={"value": 0.5, "confidence": 0.5, "details": {}},
        )
        
        assert "metrics" in summary
        assert "metric_averages" in summary
        assert "evidence_quality" in summary
        assert "high_confidence_indicators" in summary
        assert "risk_indicators" in summary
        assert "recommendation" in summary
        assert "component_details" in summary
        assert "overall_confidence" in summary
        assert "confidence_components" in summary
        
        # Check averages
        assert all(k in summary["metric_averages"] for k in ["mean", "median", "min", "max"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
