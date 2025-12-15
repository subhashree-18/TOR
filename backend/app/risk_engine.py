# backend/app/risk_engine.py
# FEATURE 11: TOR DATA COLLECTION ENHANCEMENT - RISK SCORING IMPROVEMENTS

from typing import Dict, Any, Iterable
import logging

logger = logging.getLogger("torunveil.risk_engine")

# FEATURE 11: ENHANCED - More comprehensive ASN keyword detection
HIGH_RISK_ASN_KEYWORDS = [
    # VPS/Cloud Hosting (commonly used for Tor exits)
    "M247", "OVH", "Hetzner", "Online S.A.S", "DataCamp", "Choopa",
    "DigitalOcean", "Linode", "Vultr", "Contabo", "BuyVM", "HostBrr",
    "ExoScale", "LeaseWeb", "Scaleway", "AWS", "Azure", "Google Cloud",
    
    # Bullet-proof hosting
    "Bulletproof", "Colocrossing", "Server Mania", "Puremagic",
    
    # Known Tor-friendly ASNs
    "Tor Exit", "Tor Guard", "Onionoo",
    
    # Shared hosting indicators
    "Shared Hosting", "Virtual Private Server",
]

# FEATURE 11: Enhanced thresholds for better differentiation
BW_THRESHOLD_HIGH = 50_000_000    # 50 Mbps = "high"
BW_THRESHOLD_MEDIUM = 10_000_000   # 10 Mbps = "medium"
BW_THRESHOLD_LOW = 1_000_000       # 1 Mbps = "low"


def _score_bandwidth(bw: int | float | None) -> float:
    """
    FEATURE 11: ENHANCED BANDWIDTH SCORING
    
    Map advertised_bandwidth to 0–40 points (increased from 35).
    Uses threshold-based scoring for better differentiation:
    - 0 Mbps: 0 points
    - 1-10 Mbps: 10-20 points
    - 10-50 Mbps: 20-35 points
    - 50+ Mbps: 35-40 points (increasing risk)
    """
    if not bw or bw <= 0:
        return 0.0

    # Threshold-based scoring for better granularity
    if bw < BW_THRESHOLD_LOW:
        # Very low: 1-1000k
        return (bw / BW_THRESHOLD_LOW) * 15.0
    elif bw < BW_THRESHOLD_MEDIUM:
        # Low-medium: 1-10 Mbps
        ratio = (bw - BW_THRESHOLD_LOW) / (BW_THRESHOLD_MEDIUM - BW_THRESHOLD_LOW)
        return 15.0 + (ratio * 10.0)
    elif bw < BW_THRESHOLD_HIGH:
        # Medium-high: 10-50 Mbps
        ratio = (bw - BW_THRESHOLD_MEDIUM) / (BW_THRESHOLD_HIGH - BW_THRESHOLD_MEDIUM)
        return 25.0 + (ratio * 10.0)
    else:
        # High: 50+ Mbps
        capped_ratio = min((bw - BW_THRESHOLD_HIGH) / BW_THRESHOLD_HIGH, 1.0)
        return 35.0 + (capped_ratio * 5.0)


def _score_flags(flags: Iterable[str]) -> float:
    """
    FEATURE 11: ENHANCED FLAG SCORING
    
    Refined contribution based on relay capabilities:
    - Exit relays: highest risk (can see outgoing traffic)
    - Guard relays: high risk (can see incoming connections)
    - Stable: increases reliability and observation duration
    - Running: basic requirement
    
    Max ~50 points (increased from 45 for better granularity).
    """
    if not flags:
        return 0.0

    flags = set(flags)
    score = 0.0

    # Exit is most dangerous (can intercept traffic leaving Tor)
    if "Exit" in flags:
        score += 28.0
    
    # Guard is next most dangerous (can see entry connections)
    if "Guard" in flags:
        score += 18.0
    
    # Stability increases observation window
    if "Stable" in flags:
        score += 3.0
    
    # Running + Valid indicates active participation
    if "Running" in flags and "Valid" in flags:
        score += 2.0
    
    # Combination penalty: both exit and guard (rare but dangerous)
    if "Exit" in flags and "Guard" in flags:
        score += 3.0  # Increased from 5.0 to avoid double-counting

    return min(score, 50.0)  # Cap at 50


def _score_asn(as_name: str | None) -> float:
    """
    FEATURE 11: ENHANCED ASN SCORING
    
    Improved heuristic: some ASNs/hosting providers are frequently
    used for Tor relay operations and abuse. Check expanded keyword list.
    
    Returns 0-20 points based on match confidence:
    - Exact keyword: 15 points
    - Partial match: 10 points
    - No match: 0 points
    """
    if not as_name:
        return 0.0

    upper_name = str(as_name).upper()
    
    # Exact keyword matches (highest confidence)
    for kw in HIGH_RISK_ASN_KEYWORDS:
        if kw.upper() == upper_name or upper_name == kw.upper():
            return 15.0
        # Partial match (e.g., "M247 Ltd" contains "M247")
        if kw.upper() in upper_name:
            return 10.0
    
    return 0.0


def compute_risk(relay: Dict[str, Any]) -> int:
    """
    FEATURE 11: ENHANCED RISK SCORING
    
    Compute a composite risk score (0–100) for a relay using:
      - Bandwidth capacity (0-40 points)
      - Relay flags/role (0-50 points)
      - ASN/hosting provider (0-20 points)
    
    Total: 0-110, clamped to 0-100 for interpretation.
    
    Inputs (from normalized relay):
      - advertised_bandwidth
      - flags
      - as (or as_name)
    
    Returns: int in range [0, 100]
    """
    try:
        bw = relay.get("advertised_bandwidth") or 0
        flags = relay.get("flags") or []
        as_name = relay.get("as") or relay.get("as_name")

        score = 0.0
        score += _score_bandwidth(bw)     # 0-40
        score += _score_flags(flags)      # 0-50
        score += _score_asn(as_name)      # 0-20
        
        # Total possible: 110, but we clamp to 100
        score = max(0.0, min(100.0, score))
        return int(round(score))
        
    except Exception as e:
        logger.warning(f"Risk computation failed: {e}, returning 0")
        return 0


def explain_risk(relay: Dict[str, Any]) -> Dict[str, Any]:
    """
    FEATURE 11: ENHANCED RISK EXPLANATION
    
    Return the numeric risk score plus a human-readable explanation
    suitable for law enforcement investigations.
    
    Explanation covers:
      - Bandwidth contribution to observation risk
      - Relay capabilities (Exit/Guard/Stable)
      - Hosting provider reputation
      - Overall risk summary
    """
    score = compute_risk(relay)

    parts = []
    bw = relay.get("advertised_bandwidth") or 0
    flags = set(relay.get("flags") or [])
    as_name = relay.get("as") or relay.get("as_name") or "unknown provider"

    # FEATURE 11: Enhanced bandwidth explanation with thresholds
    try:
        if bw <= 0:
            parts.append("minimal bandwidth (no significant traffic capacity)")
        elif bw < BW_THRESHOLD_LOW:
            parts.append("very low bandwidth (<1 Mbps)")
        elif bw < BW_THRESHOLD_MEDIUM:
            parts.append("low to moderate bandwidth (1-10 Mbps)")
        elif bw < BW_THRESHOLD_HIGH:
            parts.append("moderate to high bandwidth (10-50 Mbps)")
        else:
            parts.append("very high bandwidth (>50 Mbps) increases traffic observation potential")
    except Exception:
        parts.append("bandwidth information unavailable")

    # FEATURE 11: Enhanced role explanation
    if "Exit" in flags and "Guard" in flags:
        parts.append("rare dual role: both entry and exit capability (highest risk)")
    elif "Exit" in flags:
        parts.append("exit relay: can see traffic leaving Tor network")
    elif "Guard" in flags:
        parts.append("entry relay: can see connections entering Tor network")
    else:
        parts.append("middle relay: limited direct observation capability")
    
    # Stability indicator
    if "Stable" in flags:
        parts.append("marked as stable (long uptime, reliable for observation)")
    if "Valid" in flags:
        parts.append("valid directory consensus entry")

    # FEATURE 11: Enhanced ASN/hosting explanation
    upper_as = str(as_name).upper() if as_name else ""
    
    # Check for match
    matched_keyword = None
    for kw in HIGH_RISK_ASN_KEYWORDS:
        if kw.upper() in upper_as:
            matched_keyword = kw
            break
    
    if matched_keyword:
        parts.append(f"hosted by {as_name}: provider with Tor/abuse history")
    else:
        if as_name and as_name != "unknown provider":
            parts.append(f"hosted by {as_name}")
        else:
            parts.append("hosting provider: unknown (unresolved)")

    # Build final explanation
    explanation = ", ".join(parts)
    
    # Risk level categorization (FEATURE 11: Enhanced thresholds)
    if score >= 75:
        risk_level = "Very High Risk"
        confidence = "Strong evidence of observation capability"
    elif score >= 55:
        risk_level = "High Risk"
        confidence = "Significant observation potential"
    elif score >= 35:
        risk_level = "Medium Risk"
        confidence = "Moderate observation capability"
    elif score >= 15:
        risk_level = "Low Risk"
        confidence = "Limited observation capability"
    else:
        risk_level = "Very Low Risk"
        confidence = "Minimal observation capability"

    summary_text = f"{risk_level}: {confidence}. {explanation}."

    return {
        "score": score,
        "risk_level": risk_level,
        "explanation": summary_text
    }

