"""
Independent Evidence Metrics for TOR Relay Correlation

This module computes normalized evidence metrics (0.0-1.0) for analyzing
TOR relay paths. Each metric is independent and can be evaluated separately.

Each function returns a dictionary with:
- value: float (0.0-1.0) - normalized evidence strength
- details: dict - supporting data and calculations
- confidence: float (0.0-1.0) - derived confidence based on evidence strength and consistency
"""

from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from .confidence_calculator import ConfidenceCalculator, EvidenceMetrics

# Import forensic PCAP types for evidence integration
try:
    from ..forensic_pcap import FlowEvidence, flow_evidence_to_scoring_metrics
    _PCAP_AVAILABLE = True
except ImportError:
    _PCAP_AVAILABLE = False
    FlowEvidence = None

logger = logging.getLogger(__name__)

# Global confidence calculator instance
_confidence_calculator = ConfidenceCalculator()


# ============================================================================
# 1. TIME OVERLAP SCORE
# ============================================================================

def time_overlap_score(
    entry_uptime: Tuple[datetime, datetime],
    middle_uptime: Tuple[datetime, datetime],
    exit_uptime: Tuple[datetime, datetime],
) -> Dict:
    """
    Compute temporal overlap evidence metric.
    
    Measures the intersection of relay operational windows to assess
    whether the three relays could have been online simultaneously.
    
    Args:
        entry_uptime: (first_seen, last_seen) datetime tuple for entry relay
        middle_uptime: (first_seen, last_seen) datetime tuple for middle relay
        exit_uptime: (first_seen, last_seen) datetime tuple for exit relay
    
    Returns:
        {
            "value": 0.0-1.0,  # normalized overlap metric
            "details": {
                "overlap_start": datetime,
                "overlap_end": datetime,
                "overlap_days": float,
                "overlap_percentage": float,
                "entry_window_days": float,
                "middle_window_days": float,
                "exit_window_days": float,
                "all_concurrent": bool,
            },
            "confidence": "high|medium|low"
        }
    """
    try:
        e_start, e_end = entry_uptime
        m_start, m_end = middle_uptime
        x_start, x_end = exit_uptime
        
        # Validate inputs
        if not all([e_start, e_end, m_start, m_end, x_start, x_end]):
            return {
                "value": 0.0,
                "details": {
                    "error": "Missing uptime data",
                    "overlap_days": 0.0,
                    "all_concurrent": False,
                },
                "confidence": 0.0
            }
        
        # Find intersection of three windows
        overlap_start = max(e_start, m_start, x_start)
        overlap_end = min(e_end, m_end, x_end)
        
        # Calculate overlap duration
        if overlap_start >= overlap_end:
            overlap_days = 0.0
            all_concurrent = False
        else:
            overlap_days = (overlap_end - overlap_start).total_seconds() / 86400.0
            all_concurrent = True
        
        # Calculate individual window sizes
        e_window_days = (e_end - e_start).total_seconds() / 86400.0
        m_window_days = (m_end - m_start).total_seconds() / 86400.0
        x_window_days = (x_end - x_start).total_seconds() / 86400.0
        
        # Compute overlap percentage relative to smallest window
        min_window = min(e_window_days, m_window_days, x_window_days)
        overlap_percentage = (overlap_days / min_window * 100) if min_window > 0 else 0.0
        
        # Normalize to 0-1 score
        # Longer overlap = higher score
        # 30+ days of overlap = 1.0
        # 0-2 days = lower score
        if overlap_days < 0.1:
            score = 0.0
        elif overlap_days < 1:
            score = 0.1
        elif overlap_days < 3:
            score = 0.3
        elif overlap_days < 7:
            score = 0.5
        elif overlap_days < 14:
            score = 0.7
        elif overlap_days < 30:
            score = 0.85
        else:
            score = 0.95  # Cap at 0.95 (high confidence but not absolute)
        
        # Derive confidence from evidence strength
        # Use the overlap percentage as the primary evidence metric
        evidence_metrics = EvidenceMetrics(time_overlap=score)
        confidence_result = _confidence_calculator.compute_derived_confidence(
            evidence_metrics=evidence_metrics,
            observation_count=1,
        )
        confidence_value = confidence_result["confidence"]
        
        return {
            "value": round(score, 4),
            "details": {
                "overlap_start": overlap_start.isoformat() if overlap_start else None,
                "overlap_end": overlap_end.isoformat() if overlap_end else None,
                "overlap_days": round(overlap_days, 2),
                "overlap_percentage": round(overlap_percentage, 1),
                "entry_window_days": round(e_window_days, 2),
                "middle_window_days": round(m_window_days, 2),
                "exit_window_days": round(x_window_days, 2),
                "all_concurrent": all_concurrent,
            },
            "confidence": round(confidence_value, 4)
        }
    
    except Exception as e:
        logger.error(f"Error computing time_overlap_score: {e}")
        return {
            "value": 0.0,
            "details": {"error": str(e)},
            "confidence": 0.0
        }


# ============================================================================
# 2. TRAFFIC SIMILARITY SCORE
# ============================================================================

def traffic_similarity_score(
    entry_observed_bandwidth: float,
    middle_observed_bandwidth: float,
    exit_observed_bandwidth: float,
    entry_advertised_bandwidth: Optional[float] = None,
    middle_advertised_bandwidth: Optional[float] = None,
    exit_advertised_bandwidth: Optional[float] = None,
) -> Dict:
    """
    Compute traffic pattern similarity evidence metric.
    
    Measures whether relay bandwidth patterns suggest they could have
    processed the same traffic stream. Compares observed vs advertised
    bandwidth to identify consistency.
    
    Args:
        entry_observed_bandwidth: Observed outbound bandwidth (bytes/sec)
        middle_observed_bandwidth: Observed throughput (bytes/sec)
        exit_observed_bandwidth: Observed outbound bandwidth (bytes/sec)
        entry_advertised_bandwidth: Advertised capacity (bytes/sec)
        middle_advertised_bandwidth: Advertised capacity (bytes/sec)
        exit_advertised_bandwidth: Advertised capacity (bytes/sec)
    
    Returns:
        {
            "value": 0.0-1.0,  # normalized similarity metric
            "details": {
                "entry_util_ratio": float,
                "middle_util_ratio": float,
                "exit_util_ratio": float,
                "avg_util_ratio": float,
                "bandwidth_balance": str,
                "suspicious_spike": bool,
            },
            "confidence": "high|medium|low"
        }
    """
    try:
        # Normalize to Mbps for comparison
        e_obs_mbps = max(0.0, entry_observed_bandwidth / 1e6)
        m_obs_mbps = max(0.0, middle_observed_bandwidth / 1e6)
        x_obs_mbps = max(0.0, exit_observed_bandwidth / 1e6)
        
        e_adv_mbps = max(0.1, (entry_advertised_bandwidth or 1) / 1e6)
        m_adv_mbps = max(0.1, (middle_advertised_bandwidth or 1) / 1e6)
        x_adv_mbps = max(0.1, (exit_advertised_bandwidth or 1) / 1e6)
        
        # Calculate utilization ratios
        e_util = min(1.0, e_obs_mbps / e_adv_mbps)
        m_util = min(1.0, m_obs_mbps / m_adv_mbps)
        x_util = min(1.0, x_obs_mbps / x_adv_mbps)
        
        avg_util = (e_util + m_util + x_util) / 3
        
        # Check bandwidth balance (similar rates suggest same traffic)
        bw_values = [e_obs_mbps, m_obs_mbps, x_obs_mbps]
        bw_max = max(bw_values)
        bw_min = min(bw_values)
        
        if bw_max == 0:
            balance_ratio = 1.0
            bandwidth_balance = "balanced"
        else:
            balance_ratio = bw_min / bw_max
            if balance_ratio > 0.8:
                bandwidth_balance = "well-balanced"
            elif balance_ratio > 0.5:
                bandwidth_balance = "balanced"
            else:
                bandwidth_balance = "unbalanced"
        
        # Detect suspicious spikes (one relay using much more than others)
        suspicious_spike = (bw_max > bw_min * 10) and bw_max > 50  # 50 Mbps threshold
        
        # Score: higher if balanced and utilized
        if bw_max == 0:
            score = 0.1  # No traffic at all
        elif balance_ratio < 0.3:
            score = 0.2  # Very unbalanced
        elif balance_ratio < 0.5:
            score = 0.4  # Somewhat unbalanced
        elif balance_ratio < 0.8:
            score = 0.6  # Reasonably balanced
        else:
            score = 0.8  # Well balanced
        
        # Boost if utilization is consistent
        if 0.3 < avg_util < 0.9:
            score = min(1.0, score + 0.1)
        
        # Penalize extreme spikes
        if suspicious_spike:
            score = max(0.2, score - 0.3)
        
        # Derive confidence from evidence strength and data availability
        # More complete data = higher confidence
        data_completeness = sum([
            1 if entry_advertised_bandwidth else 0,
            1 if middle_advertised_bandwidth else 0,
            1 if exit_advertised_bandwidth else 0,
        ]) / 3.0
        
        evidence_metrics = EvidenceMetrics(traffic_similarity=score)
        confidence_result = _confidence_calculator.compute_derived_confidence(
            evidence_metrics=evidence_metrics,
            observation_count=1,
        )
        confidence_value = confidence_result["confidence"] * (0.5 + 0.5 * data_completeness)
        
        return {
            "value": round(score, 4),
            "details": {
                "entry_util_ratio": round(e_util, 3),
                "middle_util_ratio": round(m_util, 3),
                "exit_util_ratio": round(x_util, 3),
                "avg_util_ratio": round(avg_util, 3),
                "bandwidth_balance": bandwidth_balance,
                "balance_ratio": round(balance_ratio, 3),
                "suspicious_spike": suspicious_spike,
                "entry_mbps": round(e_obs_mbps, 2),
                "middle_mbps": round(m_obs_mbps, 2),
                "exit_mbps": round(x_obs_mbps, 2),
            },
            "confidence": round(confidence_value, 4)
        }
    
    except Exception as e:
        logger.error(f"Error computing traffic_similarity_score: {e}")
        return {
            "value": 0.0,
            "details": {"error": str(e)},
            "confidence": 0.0
        }


# ============================================================================
# 3. RELAY STABILITY SCORE
# ============================================================================

def relay_stability_score(
    entry_uptime_days: float,
    middle_uptime_days: float,
    exit_uptime_days: float,
    entry_tor_flags: Optional[list] = None,
    middle_tor_flags: Optional[list] = None,
    exit_tor_flags: Optional[list] = None,
) -> Dict:
    """
    Compute relay infrastructure stability evidence metric.
    
    Measures how established and reliable the relays are based on
    historical uptime and Tor directory consensus flags.
    
    Args:
        entry_uptime_days: Days the entry relay has been online
        middle_uptime_days: Days the middle relay has been online
        exit_uptime_days: Days the exit relay has been online
        entry_tor_flags: List of flags (e.g., ["Running", "Valid", "Stable"])
        middle_tor_flags: List of flags
        exit_tor_flags: List of flags
    
    Returns:
        {
            "value": 0.0-1.0,  # normalized stability metric
            "details": {
                "entry_stability": float,
                "middle_stability": float,
                "exit_stability": float,
                "avg_stability": float,
                "min_stability": float,
                "entry_flags": list,
                "middle_flags": list,
                "exit_flags": list,
                "all_have_stable_flag": bool,
            },
            "confidence": "high|medium|low"
        }
    """
    try:
        # Flag weightings
        flag_scores = {
            "Running": 0.1,
            "Valid": 0.2,
            "Stable": 0.3,
            "Fast": 0.2,
            "Guard": 0.1,
            "Exit": 0.1,
            "HSDir": 0.05,
            "Authority": 0.05,
        }
        
        def compute_relay_stability(uptime_days: float, flags: Optional[list]) -> float:
            """Compute stability score for single relay"""
            if uptime_days < 0.1:
                base_stability = 0.0
            elif uptime_days < 1:
                base_stability = 0.1
            elif uptime_days < 3:
                base_stability = 0.2
            elif uptime_days < 7:
                base_stability = 0.35
            elif uptime_days < 14:
                base_stability = 0.5
            elif uptime_days < 30:
                base_stability = 0.65
            elif uptime_days < 90:
                base_stability = 0.8
            elif uptime_days < 180:
                base_stability = 0.88
            elif uptime_days < 365:
                base_stability = 0.93
            else:
                base_stability = 0.97  # Multi-year uptime
            
            # Apply flag bonuses
            if flags:
                flag_bonus = sum(flag_scores.get(f, 0) for f in flags)
                flag_bonus = min(0.25, flag_bonus)  # Cap bonus
                stability = min(1.0, base_stability + flag_bonus)
            else:
                stability = base_stability
            
            return stability
        
        e_stability = compute_relay_stability(entry_uptime_days, entry_tor_flags)
        m_stability = compute_relay_stability(middle_uptime_days, middle_tor_flags)
        x_stability = compute_relay_stability(exit_uptime_days, exit_tor_flags)
        
        avg_stability = (e_stability + m_stability + x_stability) / 3
        min_stability = min(e_stability, m_stability, x_stability)
        
        # Check if all have "Stable" flag
        all_have_stable = (
            ("Stable" in (entry_tor_flags or []))
            and ("Stable" in (middle_tor_flags or []))
            and ("Stable" in (exit_tor_flags or []))
        )
        
        # Final score is weighted towards the weakest link
        score = 0.7 * min_stability + 0.3 * avg_stability
        
        # Derive confidence from stability evidence and flag availability
        flag_count = sum([
            1 if entry_tor_flags else 0,
            1 if middle_tor_flags else 0,
            1 if exit_tor_flags else 0,
        ])
        
        evidence_metrics = EvidenceMetrics(stability=score)
        confidence_result = _confidence_calculator.compute_derived_confidence(
            evidence_metrics=evidence_metrics,
            observation_count=1,
        )
        # Scale confidence by flag availability
        confidence_value = confidence_result["confidence"] * (0.6 + 0.4 * (flag_count / 3.0))
        
        return {
            "value": round(score, 4),
            "details": {
                "entry_stability": round(e_stability, 3),
                "middle_stability": round(m_stability, 3),
                "exit_stability": round(x_stability, 3),
                "avg_stability": round(avg_stability, 3),
                "min_stability": round(min_stability, 3),
                "entry_uptime_days": round(entry_uptime_days, 1),
                "middle_uptime_days": round(middle_uptime_days, 1),
                "exit_uptime_days": round(exit_uptime_days, 1),
                "entry_flags": entry_tor_flags or [],
                "middle_flags": middle_tor_flags or [],
                "exit_flags": exit_tor_flags or [],
                "all_have_stable_flag": all_have_stable,
            },
            "confidence": round(confidence_value, 4)
        }
    
    except Exception as e:
        logger.error(f"Error computing relay_stability_score: {e}")
        return {
            "value": 0.0,
            "details": {"error": str(e)},
            "confidence": 0.0
        }


# ============================================================================
# 4. PATH CONSISTENCY SCORE
# ============================================================================

def path_consistency_score(
    entry_exit_as_different: bool,
    entry_middle_as_different: bool,
    middle_exit_as_different: bool,
    entry_exit_country_different: bool,
    entry_middle_country_different: bool,
    middle_exit_country_different: bool,
    family_independent: bool,
    entry_exit_same_provider_risk: bool = False,
) -> Dict:
    """
    Compute path infrastructure consistency evidence metric.
    
    Measures whether the path follows expected TOR architecture patterns
    (diverse ASes, countries, operators) to assess plausibility.
    
    Args:
        entry_exit_as_different: Entry and exit use different AS?
        entry_middle_as_different: Entry and middle use different AS?
        middle_exit_as_different: Middle and exit use different AS?
        entry_exit_country_different: Entry and exit in different countries?
        entry_middle_country_different: Entry and middle in different countries?
        middle_exit_country_different: Middle and exit in different countries?
        family_independent: All three relays independent operators?
        entry_exit_same_provider_risk: Known provider that operates both?
    
    Returns:
        {
            "value": 0.0-1.0,  # normalized consistency metric
            "details": {
                "as_diversity_score": float,
                "geographic_diversity_score": float,
                "operator_independence_score": float,
                "diversity_flags": dict,
            },
            "confidence": "high|medium|low"
        }
    """
    try:
        # AS-level diversity scoring
        as_diversity_count = sum([
            entry_exit_as_different,
            entry_middle_as_different,
            middle_exit_as_different
        ])
        as_diversity_score = as_diversity_count / 3.0
        
        # Geographic diversity scoring
        geo_diversity_count = sum([
            entry_exit_country_different,
            entry_middle_country_different,
            middle_exit_country_different
        ])
        geo_diversity_score = geo_diversity_count / 3.0
        
        # Operator independence
        operator_score = 0.9 if family_independent else 0.3
        
        # Penalize if entry-exit same provider (common attack pattern)
        if entry_exit_same_provider_risk:
            operator_score = max(0.1, operator_score - 0.3)
        
        # Weighted combination
        # AS diversity most important (prevents correlation at ISP level)
        # Geography important (prevents centralized control)
        # Operator independence (prevents single entity owning path)
        score = (
            0.5 * as_diversity_score +
            0.3 * geo_diversity_score +
            0.2 * operator_score
        )
        
        # Confidence assessment
        diversity_flags = {
            "entry_exit_as_different": entry_exit_as_different,
            "entry_middle_as_different": entry_middle_as_different,
            "middle_exit_as_different": middle_exit_as_different,
            "entry_exit_country_different": entry_exit_country_different,
            "entry_middle_country_different": entry_middle_country_different,
            "middle_exit_country_different": middle_exit_country_different,
            "family_independent": family_independent,
            "entry_exit_same_provider_risk": entry_exit_same_provider_risk,
        }
        
        # Derive confidence from path consistency evidence
        all_checks_present = all([
            entry_exit_as_different is not None,
            entry_exit_country_different is not None,
            family_independent is not None,
        ])
        
        # Scale evidence by check completeness
        check_completeness = sum([
            1 if entry_exit_as_different is not None else 0,
            1 if entry_exit_country_different is not None else 0,
            1 if family_independent is not None else 0,
        ]) / 3.0
        
        evidence_metrics = EvidenceMetrics(path_consistency=score)
        confidence_result = _confidence_calculator.compute_derived_confidence(
            evidence_metrics=evidence_metrics,
            observation_count=1,
        )
        confidence_value = confidence_result["confidence"] * (0.6 + 0.4 * check_completeness)
        
        # Penalize if suspicious patterns detected
        risk_penalty = 0.0
        if entry_exit_as_different is False and entry_exit_country_different is False:
            risk_penalty = 0.15  # Increase confidence in risk detection
            confidence_value = min(1.0, confidence_value + risk_penalty)
        
        return {
            "value": round(score, 4),
            "details": {
                "as_diversity_score": round(as_diversity_score, 3),
                "geographic_diversity_score": round(geo_diversity_score, 3),
                "operator_independence_score": round(operator_score, 3),
                "diversity_flags": diversity_flags,
                "risk_level": "high" if score < 0.3 else "medium" if score < 0.6 else "low",
            },
            "confidence": round(confidence_value, 4)
        }
    
    except Exception as e:
        logger.error(f"Error computing path_consistency_score: {e}")
        return {
            "value": 0.0,
            "details": {"error": str(e)},
            "confidence": 0.0
        }


# ============================================================================
# 5. GEO PLAUSIBILITY SCORE
# ============================================================================

def geo_plausibility_score(
    entry_country: str,
    middle_country: str,
    exit_country: str,
    entry_latitude: Optional[float] = None,
    entry_longitude: Optional[float] = None,
    middle_latitude: Optional[float] = None,
    middle_longitude: Optional[float] = None,
    exit_latitude: Optional[float] = None,
    exit_longitude: Optional[float] = None,
    network_latency_ms: Optional[float] = None,
) -> Dict:
    """
    Compute geographic plausibility evidence metric.
    
    Measures whether the geographic distribution of relays is plausible
    for a single TOR circuit based on realistic network latency patterns.
    
    Args:
        entry_country: ISO country code (e.g., "US")
        middle_country: ISO country code
        exit_country: ISO country code
        entry_latitude: Latitude of entry relay (-90 to 90)
        entry_longitude: Longitude of entry relay (-180 to 180)
        middle_latitude: Latitude of middle relay
        middle_longitude: Longitude of middle relay
        exit_latitude: Latitude of exit relay
        exit_longitude: Longitude of exit relay
        network_latency_ms: Expected network latency in milliseconds
    
    Returns:
        {
            "value": 0.0-1.0,  # normalized plausibility metric
            "details": {
                "country_pattern": str,
                "geo_distance_km": float,
                "estimated_latency_ms": float,
                "latency_plausible": bool,
                "jurisdictional_concerns": list,
            },
            "confidence": "high|medium|low"
        }
    """
    try:
        # High-risk country patterns
        high_risk_countries = {"CN", "RU", "IR", "KP"}  # Censoring regimes
        
        # Jurisdictional concerns
        jurisdictional_concerns = []
        
        # Check for all three in same country (high anonymity risk)
        if entry_country == middle_country == exit_country:
            jurisdictional_concerns.append("all_same_country")
            geo_score = 0.1
        # Check for entry-exit in same country (observation risk)
        elif entry_country == exit_country:
            jurisdictional_concerns.append("entry_exit_same_country")
            geo_score = 0.3
        # Check for all in high-risk countries
        elif all(c in high_risk_countries for c in [entry_country, middle_country, exit_country]):
            jurisdictional_concerns.append("all_high_risk_countries")
            geo_score = 0.4
        else:
            geo_score = 0.7
        
        # Check for entry in high-risk country (potential surveillance)
        if entry_country in high_risk_countries:
            jurisdictional_concerns.append("entry_high_risk_country")
            geo_score = max(0.2, geo_score - 0.2)
        
        # Estimate geographic distance if coordinates available
        geo_distance_km = None
        estimated_latency_ms = None
        latency_plausible = True
        
        if all([entry_latitude is not None, entry_longitude is not None,
                middle_latitude is not None, middle_longitude is not None,
                exit_latitude is not None, exit_longitude is not None]):
            
            # Haversine distance estimation (simplified)
            def haversine_distance(lat1, lon1, lat2, lon2):
                """Calculate approximate distance in km"""
                import math
                R = 6371  # Earth radius in km
                
                lat1_rad = math.radians(lat1)
                lat2_rad = math.radians(lat2)
                delta_lat = math.radians(lat2 - lat1)
                delta_lon = math.radians(lon2 - lon1)
                
                a = (math.sin(delta_lat/2)**2 +
                     math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2)
                c = 2 * math.asin(math.sqrt(a))
                
                return R * c
            
            # Calculate distances
            e_m_dist = haversine_distance(entry_latitude, entry_longitude,
                                         middle_latitude, middle_longitude)
            m_x_dist = haversine_distance(middle_latitude, middle_longitude,
                                        exit_latitude, exit_longitude)
            total_dist = e_m_dist + m_x_dist
            geo_distance_km = total_dist
            
            # Estimate latency (rough: ~1ms per 150km)
            estimated_latency_ms = total_dist / 150.0
            
            # Check plausibility against network latency
            if network_latency_ms:
                # Allow some variance (network latency could be 50-200% of geo estimate)
                plausible_min = estimated_latency_ms * 0.5
                plausible_max = estimated_latency_ms * 3.0
                
                if plausible_min <= network_latency_ms <= plausible_max:
                    latency_plausible = True
                    geo_score = min(1.0, geo_score + 0.2)
                else:
                    latency_plausible = False
                    jurisdictional_concerns.append("latency_implausible")
                    geo_score = max(0.1, geo_score - 0.3)
        
        # Derive confidence from geographic evidence and data availability
        geo_data_completeness = sum([
            1 if entry_latitude is not None else 0,
            1 if middle_latitude is not None else 0,
            1 if exit_latitude is not None else 0,
        ]) / 3.0
        
        country_data_completeness = sum([
            1 if entry_country else 0,
            1 if middle_country else 0,
            1 if exit_country else 0,
        ]) / 3.0
        
        evidence_metrics = EvidenceMetrics(geo_plausibility=geo_score)
        confidence_result = _confidence_calculator.compute_derived_confidence(
            evidence_metrics=evidence_metrics,
            observation_count=1,
        )
        
        # Scale confidence by data completeness (coordinates > countries)
        data_confidence = 0.6 * geo_data_completeness + 0.4 * country_data_completeness
        confidence_value = confidence_result["confidence"] * (0.5 + 0.5 * data_confidence)
        
        return {
            "value": round(max(0.0, min(1.0, geo_score)), 4),
            "details": {
                "entry_country": entry_country,
                "middle_country": middle_country,
                "exit_country": exit_country,
                "country_pattern": f"{entry_country}→{middle_country}→{exit_country}",
                "geo_distance_km": round(geo_distance_km, 1) if geo_distance_km else None,
                "estimated_latency_ms": round(estimated_latency_ms, 1) if estimated_latency_ms else None,
                "network_latency_ms": network_latency_ms,
                "latency_plausible": latency_plausible,
                "jurisdictional_concerns": jurisdictional_concerns,
            },
            "confidence": round(confidence_value, 4)
        }
    
    except Exception as e:
        logger.error(f"Error computing geo_plausibility_score: {e}")
        return {
            "value": 0.0,
            "details": {"error": str(e)},
            "confidence": 0.0
        }


# ============================================================================
# 6. PCAP EVIDENCE SCORE
# ============================================================================

def pcap_evidence_score(
    pcap_evidence: Optional[Any] = None,
    pcap_metrics: Optional[Dict[str, float]] = None,
) -> Dict:
    """
    Compute PCAP-derived evidence metric for TOR path correlation.
    
    This function integrates forensic PCAP analysis results into the
    evidence scoring pipeline. It evaluates:
    - TOR traffic likelihood (cell sizes, ports, patterns)
    - Data quality and capture completeness
    - Traffic directionality patterns
    - Burst activity patterns
    - Timing coverage
    
    Args:
        pcap_evidence: FlowEvidence object from forensic PCAP analysis
        pcap_metrics: Pre-computed metrics dict (alternative to pcap_evidence)
    
    Returns:
        {
            "value": 0.0-1.0,  # normalized PCAP evidence strength
            "details": {
                "tor_likelihood": float,
                "data_quality": float,
                "directionality_balance": float,
                "burst_intensity": float,
                "timing_coverage": float,
                "total_packets": int,
                "total_flows": int,
                "has_pcap_data": bool,
            },
            "confidence": float (0.0-1.0)
        }
    """
    try:
        # Handle no PCAP data case
        if pcap_evidence is None and pcap_metrics is None:
            return {
                "value": 0.0,
                "details": {
                    "error": "No PCAP data provided",
                    "has_pcap_data": False,
                },
                "confidence": 0.0
            }
        
        # Convert FlowEvidence to metrics if needed
        if pcap_metrics is None and pcap_evidence is not None:
            if _PCAP_AVAILABLE:
                pcap_metrics = flow_evidence_to_scoring_metrics(pcap_evidence)
            else:
                # Fallback: try to extract from dict-like object
                pcap_metrics = {
                    "pcap_tor_likelihood": getattr(pcap_evidence, 'tor_cell_ratio', 0.0),
                    "pcap_data_quality": getattr(pcap_evidence, 'data_quality', 0.5),
                    "pcap_directionality_balance": 0.5,
                    "pcap_burst_intensity": 0.5,
                    "pcap_timing_coverage": 0.5,
                }
        
        # Extract metrics
        tor_likelihood = pcap_metrics.get("pcap_tor_likelihood", 0.0)
        data_quality = pcap_metrics.get("pcap_data_quality", 0.5)
        directionality_balance = pcap_metrics.get("pcap_directionality_balance", 0.5)
        burst_intensity = pcap_metrics.get("pcap_burst_intensity", 0.0)
        timing_coverage = pcap_metrics.get("pcap_timing_coverage", 0.0)
        
        # Compute overall PCAP evidence score
        # Weighted combination emphasizing TOR likelihood and data quality
        score = (
            0.35 * tor_likelihood +
            0.25 * data_quality +
            0.15 * directionality_balance +
            0.15 * burst_intensity +
            0.10 * timing_coverage
        )
        
        # Adjust score based on data quality (low quality = lower confidence in score)
        adjusted_score = score * (0.5 + 0.5 * data_quality)
        
        # Extract additional details from pcap_evidence if available
        total_packets = 0
        total_flows = 0
        total_bytes = 0
        capture_duration = 0.0
        
        if pcap_evidence is not None:
            total_packets = getattr(pcap_evidence, 'total_packets', 0)
            total_flows = getattr(pcap_evidence, 'total_flows', 0)
            total_bytes = getattr(pcap_evidence, 'total_bytes', 0)
            capture_duration = getattr(pcap_evidence, 'capture_duration_seconds', 0.0)
        
        # Derive confidence from evidence strength and data quality
        evidence_metrics = EvidenceMetrics(
            time_overlap=timing_coverage,
            traffic_similarity=directionality_balance,
            stability=data_quality,
        )
        
        confidence_result = _confidence_calculator.compute_derived_confidence(
            evidence_metrics=evidence_metrics,
            observation_count=1,
            has_pcap_support=True,
            pcap_packet_count=total_packets,
        )
        confidence_value = confidence_result["confidence"]
        
        return {
            "value": round(max(0.0, min(1.0, adjusted_score)), 4),
            "details": {
                "tor_likelihood": round(tor_likelihood, 4),
                "data_quality": round(data_quality, 4),
                "directionality_balance": round(directionality_balance, 4),
                "burst_intensity": round(burst_intensity, 4),
                "timing_coverage": round(timing_coverage, 4),
                "total_packets": total_packets,
                "total_flows": total_flows,
                "total_bytes": total_bytes,
                "capture_duration_seconds": round(capture_duration, 2),
                "has_pcap_data": True,
                "raw_score": round(score, 4),
                "quality_adjusted_score": round(adjusted_score, 4),
            },
            "confidence": round(confidence_value, 4)
        }
    
    except Exception as e:
        logger.error(f"Error computing pcap_evidence_score: {e}")
        return {
            "value": 0.0,
            "details": {"error": str(e), "has_pcap_data": False},
            "confidence": 0.0
        }


# ============================================================================
# AGGREGATION FUNCTION
# ============================================================================

def compute_evidence_summary(
    time_overlap: Dict,
    traffic_similarity: Dict,
    relay_stability: Dict,
    path_consistency: Dict,
    geo_plausibility: Dict,
    pcap_evidence: Optional[Dict] = None,
    observation_count: int = 1,
    session_consistency: Optional[float] = None,
    path_convergence: Optional[float] = None,
    has_pcap_support: bool = False,
    pcap_packet_count: int = 0,
) -> Dict:
    """
    Aggregate independent evidence metrics into a summary.
    
    Returns a comprehensive evidence report without aggregating into
    a single score (intentional to preserve component independence).
    
    Args:
        time_overlap: Result from time_overlap_score()
        traffic_similarity: Result from traffic_similarity_score()
        relay_stability: Result from relay_stability_score()
        path_consistency: Result from path_consistency_score()
        geo_plausibility: Result from geo_plausibility_score()
        pcap_evidence: Optional result from pcap_evidence_score()
        observation_count: Number of corroborating observations
        session_consistency: Pre-computed session consistency (0.0-1.0)
        path_convergence: Pre-computed path convergence (0.0-1.0)
        has_pcap_support: Whether PCAP data is available
        pcap_packet_count: Number of packets in PCAP capture
    
    Returns:
        {
            "metrics": {...},  # All metric scores
            "evidence_quality": "very_high|high|medium|low|very_low",
            "overall_confidence": float (0.0-1.0),
            "high_confidence_indicators": list,
            "risk_indicators": list,
            "recommendation": str,
        }
    """
    try:
        metrics = {
            "time_overlap": time_overlap.get("value", 0.0),
            "traffic_similarity": traffic_similarity.get("value", 0.0),
            "relay_stability": relay_stability.get("value", 0.0),
            "path_consistency": path_consistency.get("value", 0.0),
            "geo_plausibility": geo_plausibility.get("value", 0.0),
        }
        
        # Include PCAP evidence if provided
        if pcap_evidence is not None and pcap_evidence.get("value", 0.0) > 0:
            metrics["pcap_evidence"] = pcap_evidence.get("value", 0.0)
            has_pcap_support = True
            pcap_packet_count = pcap_evidence.get("details", {}).get("total_packets", pcap_packet_count)
        
        # Compute derived overall confidence using the calculator
        evidence_scores = list(metrics.values())
        derived_confidence = _confidence_calculator.compute_derived_confidence(
            evidence_scores=evidence_scores,
            observation_count=max(1, observation_count),
            session_consistency=session_consistency,
            path_convergence=path_convergence or path_consistency.get("value", 0.0),
            has_pcap_support=has_pcap_support,
            pcap_packet_count=pcap_packet_count,
            return_breakdown=True,
        )
        overall_confidence = derived_confidence.get("confidence", 0.0)
        confidence_components = derived_confidence.get("components", {})
        evidence_quality = _confidence_calculator.confidence_to_category(overall_confidence)
        
        # Identify positive indicators
        high_confidence_indicators = []
        if time_overlap.get("value", 0) > 0.7:
            high_confidence_indicators.append("Strong temporal overlap")
        if traffic_similarity.get("value", 0) > 0.7:
            high_confidence_indicators.append("Similar traffic patterns")
        if relay_stability.get("value", 0) > 0.7:
            high_confidence_indicators.append("Stable relay infrastructure")
        if path_consistency.get("value", 0) > 0.7:
            high_confidence_indicators.append("Consistent path architecture")
        if geo_plausibility.get("value", 0) > 0.7:
            high_confidence_indicators.append("Plausible geographic distribution")
        if pcap_evidence and pcap_evidence.get("value", 0) > 0.5:
            high_confidence_indicators.append("PCAP forensic evidence supports correlation")
        if pcap_evidence and pcap_evidence.get("details", {}).get("tor_likelihood", 0) > 0.5:
            high_confidence_indicators.append("PCAP shows TOR traffic patterns")
        
        # Identify risk indicators
        risk_indicators = []
        if path_consistency.get("details", {}).get("diversity_flags", {}).get("entry_exit_same_provider_risk"):
            risk_indicators.append("Entry-exit same provider (centralization risk)")
        if geo_plausibility.get("details", {}).get("jurisdictional_concerns"):
            concerns = geo_plausibility.get("details", {}).get("jurisdictional_concerns", [])
            for concern in concerns:
                risk_indicators.append(f"Geographic concern: {concern}")
        if time_overlap.get("value", 0) < 0.3:
            risk_indicators.append("Limited temporal overlap")
        if traffic_similarity.get("details", {}).get("suspicious_spike"):
            risk_indicators.append("Suspicious bandwidth spike detected")
        if pcap_evidence and pcap_evidence.get("details", {}).get("data_quality", 1.0) < 0.5:
            risk_indicators.append("Low quality PCAP data")
        
        # Recommendation
        avg_score = sum(metrics.values()) / len(metrics)
        if overall_confidence > 0.8 and len(high_confidence_indicators) >= 3:
            recommendation = "High confidence in path correlation. Evidence supports technical plausibility."
        elif overall_confidence > 0.6 and len(risk_indicators) == 0:
            recommendation = "Moderate confidence. Path is plausible but consider additional evidence."
        elif overall_confidence < 0.3 or len(risk_indicators) >= 3:
            recommendation = "Low confidence or significant risks identified. Recommend further investigation."
        else:
            recommendation = "Mixed evidence. Evaluate components individually based on case requirements."
        
        # Build component details
        component_details = {
            "time_overlap": time_overlap,
            "traffic_similarity": traffic_similarity,
            "relay_stability": relay_stability,
            "path_consistency": path_consistency,
            "geo_plausibility": geo_plausibility,
        }
        if pcap_evidence:
            component_details["pcap_evidence"] = pcap_evidence
        
        return {
            "metrics": metrics,
            "metric_averages": {
                "mean": round(avg_score, 3),
                "median": round(sorted(metrics.values())[len(metrics)//2], 3),
                "min": round(min(metrics.values()), 3),
                "max": round(max(metrics.values()), 3),
            },
            "evidence_quality": evidence_quality,
            "overall_confidence": round(overall_confidence, 4),
            "confidence_components": confidence_components,
            "confidence_details": derived_confidence.get("details", {}),
            "high_confidence_indicators": high_confidence_indicators,
            "risk_indicators": risk_indicators,
            "recommendation": recommendation,
            "component_details": component_details,
            "pcap_integrated": pcap_evidence is not None,
        }
    
    except Exception as e:
        logger.error(f"Error computing evidence_summary: {e}")
        return {
            "metrics": {},
            "evidence_quality": "low",
            "error": str(e)
        }
