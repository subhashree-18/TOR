# backend/app/correlator.py
from datetime import datetime
from pymongo import MongoClient
import os
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
import uuid
import math
import random
import hashlib

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017/torunveil")
client = MongoClient(MONGO_URL)
db = client["torunveil"]

# -------------------------
# Utility functions
# -------------------------
def parse_date(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        return date_parser.parse(s)
    except Exception:
        return None

def uptime_interval(relay: Dict[str, Any]):
    return parse_date(relay.get("first_seen")), parse_date(relay.get("last_seen"))

def interval_overlap(a1, b1, a2, b2) -> float:
    if not (a1 and b1 and a2 and b2):
        return 0.0
    start = max(a1, a2)
    end = min(b1, b2)
    if end <= start:
        return 0.0
    return (end - start).total_seconds() / 86400.0

def deterministic_noise(fingerprint: str, seed: str = "variance") -> float:
    """Generate deterministic pseudo-random noise based on fingerprint"""
    h = hashlib.md5(f"{fingerprint}{seed}".encode()).hexdigest()
    # Increase range for more variance: -0.12 to +0.12
    return (int(h[:8], 16) / 0xFFFFFFFF) * 0.24 - 0.12

def path_unique_noise(entry_fp: str, middle_fp: str, exit_fp: str, seed: str = "path") -> float:
    """Generate unique noise based on the full path combination"""
    # Use different hash combinations for more uniqueness
    combined = f"{entry_fp[:8]}_{middle_fp[:8]}_{exit_fp[:8]}_{seed}"
    h = hashlib.sha256(combined.encode()).hexdigest()
    return (int(h[:8], 16) / 0xFFFFFFFF) * 0.30 - 0.15  # Range: -0.15 to +0.15

def normalized_bandwidth_score(bw: Optional[int], fingerprint: str = "") -> float:
    if not bw or bw <= 0:
        base = 0.02 + random.uniform(0, 0.03)
    else:
        bw_mbps = bw / 1_000_000.0
        
        if bw_mbps < 1:
            base = 0.05 + (bw_mbps * 0.03)
        elif bw_mbps < 5:
            base = 0.08 + ((bw_mbps - 1) / 4) * 0.12
        elif bw_mbps < 20:
            base = 0.20 + ((bw_mbps - 5) / 15) * 0.20
        elif bw_mbps < 50:
            base = 0.40 + ((bw_mbps - 20) / 30) * 0.18
        elif bw_mbps < 100:
            base = 0.58 + ((bw_mbps - 50) / 50) * 0.17
        elif bw_mbps < 250:
            base = 0.75 + ((bw_mbps - 100) / 150) * 0.13
        else:
            base = 0.88 + min(0.10, (bw_mbps - 250) / 500 * 0.10)
    
    # Add deterministic variance
    noise = deterministic_noise(fingerprint, "bw") if fingerprint else random.uniform(-0.05, 0.05)
    return max(0.01, min(0.98, base + noise))

# -------------------------
# Component Analysis (No Aggregated Score)
# -------------------------
def analyze_temporal_alignment(entry: Dict, middle: Dict, exit: Dict) -> Dict:
    """Analyze temporal alignment without scoring"""
    e1, e2 = uptime_interval(entry)
    m1, m2 = uptime_interval(middle)
    x1, x2 = uptime_interval(exit)

    overlap_em = interval_overlap(e1, e2, m1, m2)
    overlap_mx = interval_overlap(m1, m2, x1, x2)
    overlap_ex = interval_overlap(e1, e2, x1, x2)

    # Raw temporal metrics without scoring
    return {
        "overlap_entry_middle_days": round(overlap_em, 2),
        "overlap_middle_exit_days": round(overlap_mx, 2),
        "overlap_entry_exit_days": round(overlap_ex, 2),
        "min_overlap": round(min(overlap_em, overlap_mx, overlap_ex), 2),
        "max_overlap": round(max(overlap_em, overlap_mx, overlap_ex), 2),
        "avg_overlap": round((overlap_em + overlap_mx + overlap_ex) / 3, 2),
    }

def analyze_stability(entry: Dict, middle: Dict, exit: Dict) -> Dict:
    """Analyze relay stability without scoring"""
    e1, e2 = uptime_interval(entry)
    m1, m2 = uptime_interval(middle)
    x1, x2 = uptime_interval(exit)
    
    def uptime_days(a, b):
        return (b - a).total_seconds() / 86400.0 if a and b else 0.0

    e_uptime = uptime_days(e1, e2)
    m_uptime = uptime_days(m1, m2)
    x_uptime = uptime_days(x1, x2)
    
    return {
        "entry_uptime_days": round(e_uptime, 1),
        "middle_uptime_days": round(m_uptime, 1),
        "exit_uptime_days": round(x_uptime, 1),
        "min_uptime": round(min(e_uptime, m_uptime, x_uptime), 1),
        "max_uptime": round(max(e_uptime, m_uptime, x_uptime), 1),
        "avg_uptime": round((e_uptime + m_uptime + x_uptime) / 3, 1),
    }

def analyze_bandwidth(entry: Dict, middle: Dict, exit: Dict) -> Dict:
    """Analyze bandwidth characteristics without scoring"""
    e_bw = entry.get("advertised_bandwidth", 0) or 0
    m_bw = middle.get("advertised_bandwidth", 0) or 0
    x_bw = exit.get("advertised_bandwidth", 0) or 0
    
    # Convert to Mbps
    e_bw_mbps = e_bw / 1_000_000.0
    m_bw_mbps = m_bw / 1_000_000.0
    x_bw_mbps = x_bw / 1_000_000.0
    
    return {
        "entry_bandwidth_mbps": round(e_bw_mbps, 2),
        "middle_bandwidth_mbps": round(m_bw_mbps, 2),
        "exit_bandwidth_mbps": round(x_bw_mbps, 2),
        "min_bandwidth_mbps": round(min(e_bw_mbps, m_bw_mbps, x_bw_mbps), 2),
        "max_bandwidth_mbps": round(max(e_bw_mbps, m_bw_mbps, x_bw_mbps), 2),
        "avg_bandwidth_mbps": round((e_bw_mbps + m_bw_mbps + x_bw_mbps) / 3, 2),
        "bandwidth_balance": "unbalanced" if max(e_bw_mbps, m_bw_mbps, x_bw_mbps) > min(e_bw_mbps, m_bw_mbps, x_bw_mbps) * 3 else "balanced",
    }

def analyze_relay_quality(entry: Dict, middle: Dict, exit: Dict) -> Dict:
    """Analyze individual relay quality flags without scoring"""
    def get_flags_summary(relay, role="unknown"):
        flags = relay.get("flags", [])
        summary = {
            "has_running": "Running" in flags,
            "has_valid": "Valid" in flags,
            "has_stable": "Stable" in flags,
            "has_fast": "Fast" in flags,
            "flag_count": len(flags),
            "flags": flags,
        }
        
        if role == "entry":
            summary["is_guard"] = "Guard" in flags
        elif role == "exit":
            summary["is_exit"] = "Exit" in flags
        
        return summary
    
    return {
        "entry": {
            "nickname": entry.get("nickname", "unknown"),
            **get_flags_summary(entry, "entry"),
        },
        "middle": {
            "nickname": middle.get("nickname", "unknown"),
            **get_flags_summary(middle, "middle"),
        },
        "exit": {
            "nickname": exit.get("nickname", "unknown"),
            **get_flags_summary(exit, "exit"),
        },
    }

def analyze_diversity(entry: Dict, middle: Dict, exit: Dict) -> Dict:
    """Analyze geographic and network diversity without penalties"""
    entry_as = entry.get("as", "unknown")
    middle_as = middle.get("as", "unknown")
    exit_as = exit.get("as", "unknown")
    
    entry_country = entry.get("country", "unknown")
    middle_country = middle.get("country", "unknown")
    exit_country = exit.get("country", "unknown")
    
    entry_family = set(entry.get("effective_family", []))
    middle_family = set(middle.get("effective_family", []))
    exit_family = set(exit.get("effective_family", []))
    
    return {
        "as_diversity": {
            "entry_as": entry_as,
            "middle_as": middle_as,
            "exit_as": exit_as,
            "entry_exit_same_as": entry_as == exit_as,
            "entry_middle_same_as": entry_as == middle_as,
            "middle_exit_same_as": middle_as == exit_as,
        },
        "geographic_diversity": {
            "entry_country": entry_country,
            "middle_country": middle_country,
            "exit_country": exit_country,
            "entry_exit_same_country": entry_country == exit_country,
            "entry_middle_same_country": entry_country == middle_country,
            "middle_exit_same_country": middle_country == exit_country,
        },
        "family_diversity": {
            "entry_middle_related": bool(entry_family & middle_family),
            "entry_exit_related": bool(entry_family & exit_family),
            "middle_exit_related": bool(middle_family & exit_family),
            "all_independent": not (entry_family & (middle_family | exit_family)),
        },
    }

def path_components(entry: Dict, middle: Dict, exit: Dict) -> Dict:
    """Analyze path with detailed component breakdown (no aggregation)"""
    return {
        "temporal": analyze_temporal_alignment(entry, middle, exit),
        "stability": analyze_stability(entry, middle, exit),
        "bandwidth": analyze_bandwidth(entry, middle, exit),
        "relay_quality": analyze_relay_quality(entry, middle, exit),
        "diversity": analyze_diversity(entry, middle, exit),
    }

# -------------------------
# Candidate selection & scoring with improved diversity
# -------------------------
def select_candidate_relays(limit_guards=80, limit_middles=200, limit_exits=80):
    """Select diverse candidate relays with mixed bandwidth and geographic distribution"""
    
    # Get guards - mix of high and medium bandwidth
    guards_high = list(db.relays.find(
        {"is_guard": True, "running": True}
    ).sort("advertised_bandwidth", -1).limit(limit_guards // 2))
    
    guards_medium = list(db.relays.find(
        {"is_guard": True, "running": True}
    ).sort("advertised_bandwidth", -1).skip(limit_guards // 2).limit(limit_guards // 2))
    
    guards = guards_high + guards_medium
    
    # Get middles - diverse selection
    middles = list(db.relays.find(
        {"is_guard": False, "is_exit": False, "running": True}
    ).sort("advertised_bandwidth", -1).limit(limit_middles))
    
    # Get exits - mix of bandwidth levels
    exits_high = list(db.relays.find(
        {"is_exit": True, "running": True}
    ).sort("advertised_bandwidth", -1).limit(limit_exits // 2))
    
    exits_low = list(db.relays.find(
        {"is_exit": True, "running": True}
    ).sort("advertised_bandwidth", 1).limit(limit_exits // 2))
    
    exits = exits_high + exits_low
    
    return guards, middles, exits

def score_candidate_paths(guards, middles, exits, top_k=1500):
    """Generate and score candidate paths with improved variance"""
    candidates = []
    
    # Shuffle to get varied combinations
    import random
    random.shuffle(guards)
    random.shuffle(middles)
    random.shuffle(exits)

    for g in guards:
        for m in middles[:50]:  # Limit inner loops for performance
            if g["fingerprint"] == m["fingerprint"]:
                continue
            
            # Skip same-AS combinations early
            if g.get("as") and g.get("as") == m.get("as"):
                continue
                
            for x in exits[:40]:
                if x["fingerprint"] in {g["fingerprint"], m["fingerprint"]}:
                    continue
                
                # Skip same-AS entry-exit
                if g.get("as") and g.get("as") == x.get("as"):
                    # Still include some for penalty demonstration
                    if random.random() > 0.1:
                        continue

                components = path_components(g, m, x)

                candidates.append({
                    "id": str(uuid.uuid4()),
                    "entry": g["fingerprint"],
                    "middle": m["fingerprint"],
                    "exit": x["fingerprint"],
                    "components": components,
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                })

    # Return candidates without sorting by aggregated score
    top = candidates[:top_k]

    if top:
        db.path_candidates.delete_many({})
        db.path_candidates.insert_many(top)

    return top

def generate_candidate_paths():
    """Main entry point for path generation"""
    guards, middles, exits = select_candidate_relays()
    return score_candidate_paths(guards, middles, exits)

def top_candidate_paths(limit=100):
    """Retrieve top scored paths"""
    return list(db.path_candidates.find({}, {"_id": 0}).sort("score", -1).limit(limit))
