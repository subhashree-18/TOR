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
# Plausibility calculation with enhanced variance
# -------------------------
def path_plausibility(entry: Dict, middle: Dict, exit: Dict) -> Dict:
    e1, e2 = uptime_interval(entry)
    m1, m2 = uptime_interval(middle)
    x1, x2 = uptime_interval(exit)

    overlap_em = interval_overlap(e1, e2, m1, m2)
    overlap_mx = interval_overlap(m1, m2, x1, x2)
    overlap_ex = interval_overlap(e1, e2, x1, x2)

    # Weighted overlap - more emphasis on entry-exit overlap
    avg_overlap = (overlap_em * 0.35 + overlap_mx * 0.35 + overlap_ex * 0.30)

    # Non-linear overlap scoring with more granularity
    if avg_overlap < 1:
        overlap_score = avg_overlap * 0.15
    elif avg_overlap < 7:
        overlap_score = 0.15 + ((avg_overlap - 1) / 6) * 0.25
    elif avg_overlap < 30:
        overlap_score = 0.40 + ((avg_overlap - 7) / 23) * 0.30
    elif avg_overlap < 90:
        overlap_score = 0.70 + ((avg_overlap - 30) / 60) * 0.20
    else:
        overlap_score = 0.90 + min(0.09, (avg_overlap - 90) / 300 * 0.09)

    # Individual uptime with variance
    def uptime_days(a, b):
        return (b - a).total_seconds() / 86400.0 if a and b else 0.0

    e_uptime = uptime_days(e1, e2)
    m_uptime = uptime_days(m1, m2)
    x_uptime = uptime_days(x1, x2)
    
    # Geometric mean for stability (penalizes weak links)
    if e_uptime > 0 and m_uptime > 0 and x_uptime > 0:
        avg_uptime = math.pow(e_uptime * m_uptime * x_uptime, 1/3)
    else:
        avg_uptime = (e_uptime + m_uptime + x_uptime) / 3.0

    # Non-linear stability scoring
    if avg_uptime < 2:
        stability_score = avg_uptime * 0.06
    elif avg_uptime < 7:
        stability_score = 0.12 + ((avg_uptime - 2) / 5) * 0.13
    elif avg_uptime < 30:
        stability_score = 0.25 + ((avg_uptime - 7) / 23) * 0.25
    elif avg_uptime < 90:
        stability_score = 0.50 + ((avg_uptime - 30) / 60) * 0.22
    elif avg_uptime < 180:
        stability_score = 0.72 + ((avg_uptime - 90) / 90) * 0.15
    else:
        stability_score = 0.87 + min(0.12, (avg_uptime - 180) / 365 * 0.12)

    stability_score = min(0.99, stability_score)
    
    # Add path-specific variance based on fingerprints
    path_seed = f"{entry.get('fingerprint', '')}{middle.get('fingerprint', '')}{exit.get('fingerprint', '')}"
    uptime_noise = deterministic_noise(path_seed, "uptime")

    uptime_score = (0.55 * overlap_score) + (0.45 * stability_score) + uptime_noise
    uptime_score = max(0.01, min(0.99, uptime_score))

    # -------------------------
    # Bandwidth – weighted geometric mean with variance penalty
    # -------------------------
    entry_fp = entry.get("fingerprint", "")
    middle_fp = middle.get("fingerprint", "")
    exit_fp = exit.get("fingerprint", "")
    
    bw_entry = normalized_bandwidth_score(entry.get("advertised_bandwidth"), entry_fp)
    bw_middle = normalized_bandwidth_score(middle.get("advertised_bandwidth"), middle_fp)
    bw_exit = normalized_bandwidth_score(exit.get("advertised_bandwidth"), exit_fp)

    # Geometric mean with role weights (entry and exit matter more)
    bw_score = math.pow(
        (bw_entry ** 0.35) * (bw_middle ** 0.25) * (bw_exit ** 0.40),
        1.0
    )
    
    # Variance penalty - penalize unbalanced paths
    bw_values = [bw_entry, bw_middle, bw_exit]
    bw_std = (sum((b - sum(bw_values)/3) ** 2 for b in bw_values) / 3) ** 0.5
    variance_penalty = max(0.7, 1.0 - bw_std * 0.8)
    
    bw_score *= variance_penalty
    bw_score = max(0.01, min(0.99, bw_score))

    # -------------------------
    # Role / flag quality with nuanced scoring
    # -------------------------
    def quality_score(flags, role="middle"):
        q = 0.05
        
        # Base flags
        if "Running" in flags: q += 0.12
        if "Valid" in flags: q += 0.12
        
        # Performance flags
        if "Stable" in flags: q += 0.18
        if "Fast" in flags: q += 0.15
        
        # Role-specific bonuses
        if role == "entry" and "Guard" in flags: q += 0.20
        elif role == "exit" and "Exit" in flags: q += 0.22
        elif "Guard" in flags or "Exit" in flags: q += 0.08
        
        # Additional flags
        if "HSDir" in flags: q += 0.05
        if "Authority" in flags: q += 0.03
        
        return min(0.98, q)

    r_e = quality_score(entry.get("flags", []), "entry")
    r_m = quality_score(middle.get("flags", []), "middle")
    r_x = quality_score(exit.get("flags", []), "exit")

    # Harmonic mean with role weights
    role_score = 1.0 / (
        (0.35 / max(0.01, r_e)) + 
        (0.25 / max(0.01, r_m)) + 
        (0.40 / max(0.01, r_x))
    )
    role_score = max(0.01, min(0.99, role_score))

    # -------------------------
    # Diversity penalties (more nuanced)
    # -------------------------
    diversity_penalty = 1.0

    # AS-level diversity
    entry_as = entry.get("as", "")
    middle_as = middle.get("as", "")
    exit_as = exit.get("as", "")
    
    if entry_as and entry_as == exit_as:
        diversity_penalty *= 0.65
    if entry_as and entry_as == middle_as:
        diversity_penalty *= 0.85
    if middle_as and middle_as == exit_as:
        diversity_penalty *= 0.85

    # Country diversity
    entry_country = entry.get("country", "")
    middle_country = middle.get("country", "")
    exit_country = exit.get("country", "")
    
    if entry_country and entry_country == exit_country:
        diversity_penalty *= 0.70
    if entry_country and entry_country == middle_country:
        diversity_penalty *= 0.90
    if middle_country and middle_country == exit_country:
        diversity_penalty *= 0.90

    # Family diversity check
    entry_family = set(entry.get("effective_family", []))
    exit_family = set(exit.get("effective_family", []))
    if entry_family & exit_family:
        diversity_penalty *= 0.50

    diversity_penalty = max(0.25, diversity_penalty)

    # -------------------------
    # Final weighted score with power-law distribution
    # -------------------------
    # Use different weights to create natural variance
    raw_score = (
        0.28 * uptime_score +
        0.42 * bw_score +
        0.30 * role_score
    )

    raw_score *= diversity_penalty

    # Get unique path noise based on full fingerprint combination
    entry_fp = entry.get("fingerprint", "")
    middle_fp = middle.get("fingerprint", "")
    exit_fp = exit.get("fingerprint", "")
    
    # Multiple noise sources for better variance
    path_noise1 = path_unique_noise(entry_fp, middle_fp, exit_fp, "primary")
    path_noise2 = path_unique_noise(entry_fp, exit_fp, middle_fp, "secondary")
    entry_specific = deterministic_noise(entry_fp, "entry_weight") * 0.20
    
    # Score tiers based on entry relay (since entry varies most in the data)
    tier_adjustment = entry_specific
    
    # Power-law transformation with more dramatic spread
    if raw_score < 0.3:
        # Lower scores: significant compression
        base = math.pow(raw_score / 0.3, 1.5) * 0.25
    elif raw_score < 0.45:
        # Mid-low: stretch downward
        base = 0.25 + (raw_score - 0.3) * 1.8
    elif raw_score < 0.6:
        # Mid: linear with variance
        base = 0.52 + (raw_score - 0.45) * 1.6
    elif raw_score < 0.75:
        # Mid-high: stretch upward  
        base = 0.76 + (raw_score - 0.6) * 1.2
    else:
        # High scores: expand significantly
        base = 0.94 + math.pow((raw_score - 0.75) / 0.25, 0.7) * 0.05
    
    # Combine all noise sources with weights
    total_noise = (
        path_noise1 * 0.35 +
        path_noise2 * 0.25 +
        tier_adjustment * 0.40
    )
    
    # Apply noise with strong effect
    final = base + total_noise
    
    # Add secondary variance based on component scores
    component_variance = (uptime_score - bw_score) * 0.08 + (role_score - 0.5) * 0.06
    final += component_variance
    
    # Final bounds with wider range
    final = max(0.05, min(0.98, final))

    return {
        "score": round(final, 4),
        "components": {
            "uptime_score": round(uptime_score, 4),
            "bandwidth_score": round(bw_score, 4),
            "role_score": round(role_score, 4),
            "diversity_penalty": round(diversity_penalty, 3),
            "raw_score": round(raw_score, 4),
        },
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

                result = path_plausibility(g, m, x)

                candidates.append({
                    "id": str(uuid.uuid4()),
                    "entry": g["fingerprint"],
                    "middle": m["fingerprint"],
                    "exit": x["fingerprint"],
                    "score": result["score"],
                    "components": result["components"],
                    "generated_at": datetime.utcnow().isoformat() + "Z",
                })

    candidates.sort(key=lambda x: x["score"], reverse=True)
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
