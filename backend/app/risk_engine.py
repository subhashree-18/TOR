# backend/app/risk_engine.py

from typing import Dict, Any, Iterable

# Some commonly abused AS names for Tor / shady hosting (example list)
HIGH_RISK_ASN_KEYWORDS = [
    "M247",
    "OVH",
    "Hetzner",
    "Online S.A.S",
    "DataCamp",
    "Choopa",
    "DigitalOcean",
    "Tor Exit",
]

def _score_bandwidth(bw: int | float | None) -> float:
    """
    Map advertised_bandwidth to 0–35.
    Treat ~50 Mbps as 'high' for scoring purposes.
    """
    if not bw or bw <= 0:
        return 0.0

    BW_MAX = 50_000_000  # 50 Mbps
    ratio = min(bw / BW_MAX, 1.0)
    return ratio * 35.0


def _score_flags(flags: Iterable[str]) -> float:
    """
    Flags contribution: Exit > Guard > Stable/Running.
    Max ~45 points.
    """
    if not flags:
        return 0.0

    flags = set(flags)
    score = 0.0

    if "Exit" in flags:
        score += 25.0
    if "Guard" in flags:
        score += 15.0
    if "Stable" in flags and "Running" in flags:
        score += 5.0

    # Slight extra if both entry & exit capabilities
    if "Exit" in flags and "Guard" in flags:
        score += 5.0

    return score


def _score_asn(as_name: str | None) -> float:
    """
    Basic heuristic: some ASNs / hosting providers are
    frequently used for Tor and abuse.
    """
    if not as_name:
        return 0.0

    upper_name = as_name.upper()
    for kw in HIGH_RISK_ASN_KEYWORDS:
        if kw.upper() in upper_name:
            return 15.0
    return 0.0


def compute_risk(relay: Dict[str, Any]) -> int:
    """
    Compute a composite risk score (0–100) for a relay.

    Inputs (from normalized relay):
      - advertised_bandwidth
      - flags
      - as
    """
    bw = relay.get("advertised_bandwidth") or 0
    flags = relay.get("flags") or []
    as_name = relay.get("as") or relay.get("as_name")

    score = 0.0
    score += _score_bandwidth(bw)
    score += _score_flags(flags)
    score += _score_asn(as_name)

    # Clamp to [0, 100] and return as int
    score = max(0.0, min(100.0, score))
    return int(round(score))


def explain_risk(relay: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return the numeric risk score (same as compute_risk) plus a short,
    human-readable explanation suitable for non-technical users and law
    enforcement. The function does NOT change the numeric scoring logic.

    Explanation covers:
      - bandwidth influence
      - relay role (Exit/Guard)
      - hosting provider / ASN influence
    """
    score = compute_risk(relay)

    parts = []
    bw = relay.get("advertised_bandwidth") or 0
    flags = set(relay.get("flags") or [])
    as_name = relay.get("as") or relay.get("as_name") or "unknown provider"

    # Bandwidth explanation
    try:
        if bw <= 0:
            parts.append("low advertised bandwidth suggests reduced ability to observe high-volume traffic")
        elif bw < 10_000_000:
            parts.append("moderate advertised bandwidth")
        else:
            parts.append("high advertised bandwidth increases potential to observe traffic")
    except Exception:
        parts.append("bandwidth information unavailable")

    # Role explanation
    if "Exit" in flags:
        parts.append("exit capability (can see traffic leaving Tor) increases risk")
    elif "Guard" in flags:
        parts.append("guard/entry capability (can observe client-side connections)")
    else:
        parts.append("no strong exit/entry role detected")

    # ASN / hosting explanation
    if as_name and any(k.upper() in (as_name or "").upper() for k in HIGH_RISK_ASN_KEYWORDS):
        parts.append(f"hosted by {as_name}, a provider sometimes associated with abusive services")
    else:
        if as_name and as_name != "unknown provider":
            parts.append(f"hosted by {as_name}")
        else:
            parts.append("hosting provider unknown")

    # Build final simple sentence(s) suitable for display
    explanation = ", ".join(parts)
    # Short friendly summary
    summary = []
    if score >= 70:
        summary.append("High risk")
    elif score >= 40:
        summary.append("Medium risk")
    else:
        summary.append("Low risk")

    summary_text = f"{summary[0]} due to {explanation}."

    return {
        "score": score,
        "explanation": summary_text
    }
