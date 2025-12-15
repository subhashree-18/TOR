# backend/app/correlator.py
from datetime import datetime
from pymongo import MongoClient
import os
from typing import List, Dict, Any, Optional
from dateutil import parser as date_parser
import uuid

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

def uptime_interval(relay: Dict[str,Any]):
    return parse_date(relay.get("first_seen")), parse_date(relay.get("last_seen"))

def interval_overlap(a1, b1, a2, b2):
    """Return overlap in days between two intervals (or 0.0)"""
    if not (a1 and b1 and a2 and b2):
        return 0.0
    start = max(a1, a2)
    end = min(b1, b2)
    if end <= start:
        return 0.0
    return (end - start).total_seconds() / 86400.0

def normalized_bandwidth_score(bw: Optional[int]) -> float:
    """
    Normalized bandwidth score with PERCENTILE-based scaling.
    Maps actual bandwidth distribution to a meaningful 0-1 scale.
    
    Realistic Tor relay bandwidth distribution:
    - Low tier: < 1 MB/s → scores 0.2-0.4
    - Medium tier: 1-10 MB/s → scores 0.4-0.7  
    - High tier: 10-50 MB/s → scores 0.7-0.9
    - Very High: > 50 MB/s → scores 0.85-0.98
    """
    if not bw:
        return 0.10
    
    bw_mbps = float(bw) / 1_000_000.0
    
    if bw_mbps < 0.5:
        return 0.15
    elif bw_mbps < 1.0:
        return 0.25
    elif bw_mbps < 2.0:
        return 0.35
    elif bw_mbps < 5.0:
        return 0.45
    elif bw_mbps < 10.0:
        return 0.55
    elif bw_mbps < 20.0:
        return 0.65
    elif bw_mbps < 50.0:
        return 0.75
    elif bw_mbps < 100.0:
        return 0.85
    else:
        return 0.92

# -------------------------
# Plausibility calculation
# -------------------------
def path_plausibility(entry: Dict, middle: Dict, exit: Dict) -> Dict:
    """Compute plausibility score (0..1) and component breakdown."""
    e1, e2 = uptime_interval(entry)
    m1, m2 = uptime_interval(middle)
    x1, x2 = uptime_interval(exit)

    # pairwise overlaps (days)
    overlap_em = interval_overlap(e1, e2, m1, m2)
    overlap_mx = interval_overlap(m1, m2, x1, x2)
    
    # Individual relay uptime (days online)
    uptime_e = (e2 - e1).total_seconds() / 86400.0 if e1 and e2 else 0
    uptime_m = (m2 - m1).total_seconds() / 86400.0 if m1 and m2 else 0
    uptime_x = (x2 - x1).total_seconds() / 86400.0 if x1 and x2 else 0

    # IMPROVED: Use BOTH overlap AND individual uptime for better variation
    # Overlap score (correlation) + Individual uptime (stability) = More differentiation
    avg_overlap = (overlap_em + overlap_mx) / 2.0
    if avg_overlap <= 0.1:
        overlap_score = 0.0
    elif avg_overlap <= 1.0:
        overlap_score = avg_overlap * 0.15
    elif avg_overlap <= 3.0:
        overlap_score = 0.15 + (avg_overlap - 1.0) * 0.10
    elif avg_overlap <= 7.0:
        overlap_score = 0.35 + (avg_overlap - 3.0) * 0.05
    else:
        overlap_score = 0.55 + min(0.15, (avg_overlap - 7.0) * 0.01)
    overlap_score = min(1.0, max(0.0, overlap_score))
    
    # Individual uptime stability score (normalized: 0-365 days → 0-1)
    # Longer uptime = more stable relay
    avg_uptime = (uptime_e + uptime_m + uptime_x) / 3.0
    if avg_uptime < 1:
        stability_score = avg_uptime * 0.1
    elif avg_uptime < 7:
        stability_score = 0.1 + (avg_uptime - 1) * 0.05
    elif avg_uptime < 30:
        stability_score = 0.4 + (avg_uptime - 7) * 0.02
    elif avg_uptime < 180:
        stability_score = 0.86 + (avg_uptime - 30) * 0.001
    else:
        stability_score = 0.95 + min(0.05, (avg_uptime - 180) * 0.0001)
    stability_score = min(1.0, max(0.0, stability_score))
    
    # Final uptime score blends overlap (correlation) and stability
    uptime_score = (overlap_score * 0.6) + (stability_score * 0.4)

    # bandwidth score
    bw_e = entry.get("advertised_bandwidth") or 0
    bw_m = middle.get("advertised_bandwidth") or 0
    bw_x = exit.get("advertised_bandwidth") or 0
    bw_score = (normalized_bandwidth_score(bw_e) + normalized_bandwidth_score(bw_m) + normalized_bandwidth_score(bw_x)) / 3.0

    # role flags - more granular, flag-based scoring
    flags_e = entry.get("flags", [])
    flags_m = middle.get("flags", [])
    flags_x = exit.get("flags", [])
    
    # Score based on quality flags: Running, Stable, Fast, Valid
    def quality_score(flags):
        # Baseline: having SOME flags is minimum
        q = 0.2
        # Core quality indicators
        if "Running" in flags: q += 0.15
        if "Valid" in flags: q += 0.15
        # Premium flags that indicate reliability
        if "Stable" in flags: q += 0.25
        if "Fast" in flags: q += 0.25
        # Additional trusted flags
        if "Guard" in flags: q += 0.10  # Guard = high trust
        # Penalty for missing basic flags
        if "Running" not in flags: q *= 0.70
        if "Valid" not in flags: q *= 0.70
        return min(1.0, q)
    
    role_e = quality_score(flags_e)
    role_m = quality_score(flags_m)
    role_x = quality_score(flags_x)
    role_s = (role_e + role_m + role_x) / 3.0

    # AS diversity penalty (stronger penalty)
    as_e = (entry.get("as") or "").lower()
    as_x = (exit.get("as") or "").lower()
    as_penalty = 0.70 if (as_e and as_x and as_e == as_x) else 1.0

    # Country diversity penalty (MAJOR: same country entry/exit is suspicious)
    c_e = (entry.get("country") or "").upper()
    c_x = (exit.get("country") or "").upper()
    country_penalty = 0.60 if (c_e and c_x and c_e == c_x) else 1.0

    # Weighted sum to final plausibility (explainable)
    # NEW WEIGHTING: Emphasize bandwidth (has variation), less on role (all similar)
    # 35% uptime, 50% bandwidth (highest variation), 15% role quality
    final = (0.35 * uptime_score) + (0.50 * bw_score) + (0.15 * role_s)
    final = final * as_penalty * country_penalty
    
    # IMPROVED: Allow wider variation (20-95%) instead of clustering around 85%
    # Apply logarithmic scaling to expand the middle range
    # This creates natural differentiation in scores
    if final > 0.5:
        # For high scores, use logarithmic scaling to spread out clustering
        final = 0.50 + (0.45 * (1.0 - pow(0.5, (final - 0.5) * 3)))
    
    final = max(0.0, min(0.95, final))

    return {
        "score": round(final, 4),
        "components": {
            "uptime_score": round(uptime_score, 4),
            "bandwidth_score": round(bw_score, 4),
            "role_score": round(role_s, 4),
            "as_penalty": round(as_penalty, 3),
            "country_penalty": round(country_penalty, 3)
        },
    }

# -------------------------
# Candidate generation
# -------------------------
def select_candidate_relays(limit_guards:int=50, limit_middles:int=150, limit_exits:int=50):
    """
    Select diverse candidate relays to maximize score variation.
    
    Strategy:
    1. Get ALL running relays sorted by bandwidth
    2. Divide into 5 tiers: Top 10%, 20-30%, 30-50%, 50-80%, Bottom 20%
    3. Sample evenly from each tier
    4. This ensures high-BW, medium-BW, and low-BW relays all represented
    
    For middle relays: Use 100+ random diverse nodes to ensure variation
    """
    import random
    
    # Get ALL relays
    all_guards = list(db.relays.find({"is_guard": True, "running": True}).sort("advertised_bandwidth", -1))
    all_exits = list(db.relays.find({"is_exit": True, "running": True}).sort("advertised_bandwidth", -1))
    all_middles = list(db.relays.find({"is_guard": False, "is_exit": False, "running": True}).sort("advertised_bandwidth", -1))
    
    def sample_by_tiers(relays, limit):
        """
        Divide relays into 5 bandwidth tiers and sample evenly from each.
        Ensures we get high, medium, and low bandwidth diversity.
        """
        if len(relays) <= limit:
            return relays
        
        n = len(relays)
        # Divide into 5 equal tiers
        tier_size = n // 5
        tiers = [
            relays[0:tier_size],                      # Tier 1: Top 20% (highest BW)
            relays[tier_size:2*tier_size],            # Tier 2: 20-40%
            relays[2*tier_size:3*tier_size],          # Tier 3: 40-60% (middle)
            relays[3*tier_size:4*tier_size],          # Tier 4: 60-80%
            relays[4*tier_size:],                     # Tier 5: Bottom 20% (lowest BW)
        ]
        
        sampled = []
        per_tier = max(1, limit // 5)  # How many from each tier
        
        for tier in tiers:
            if len(tier) > 0:
                # Randomly sample from this tier
                count = min(per_tier, len(tier))
                sampled.extend(random.sample(tier, count))
        
        # If we still need more, add random from anywhere
        if len(sampled) < limit:
            needed = limit - len(sampled)
            remaining = [r for r in relays if r not in sampled]
            if remaining:
                sampled.extend(random.sample(remaining, min(needed, len(remaining))))
        
        return sampled[:limit]
    
    # For guards and exits: sample by tiers
    guards = sample_by_tiers(all_guards, limit_guards)
    exits = sample_by_tiers(all_exits, limit_exits)
    
    # For middles: use EVEN MORE relays and more random selection
    # This creates more variation in combinations
    middles = sample_by_tiers(all_middles, min(limit_middles, len(all_middles)))
    
    return guards, middles, exits


def score_candidate_paths(guards, middles, exits, top_k:int=1000, max_combinations:int=200000) -> List[Dict]:
    """
    Score candidate (g,m,x) tuples deterministically and return top_k.

    Parameters:
      - guards/middles/exits: lists of relay dicts
      - top_k: how many top-scoring paths to return
      - max_combinations: safety cap to avoid huge loops. If the full
        Cartesian product exceeds this cap we prune 'middles' deterministically
        down to reduce the total combinations.

    This clear separation (select vs score) helps when explaining to
    non-technical stakeholders: we first choose a small, sensible set of
    relays and then score all reasonable combinations.
    """
    # Safety pruning: avoid combinatorial explosion by reducing middles
    estimated = len(guards) * len(middles) * len(exits)
    if estimated > max_combinations:
        # prune middles deterministically by taking top-N by bandwidth
        # so that the resulting combinations fall below cap.
        target = max(1, max_combinations // (max(1, len(guards) * len(exits))))
        middles = sorted(middles, key=lambda r: r.get("advertised_bandwidth") or 0, reverse=True)[:target]

    candidates = []
    for g in guards:
        for m in middles:
            # Exclude same identity (fingerprint) between nodes — this is
            # an explainable, deterministic filter: a single relay cannot
            # occupy two positions in the same path.
            if g.get("fingerprint") == m.get("fingerprint"): continue
            for x in exits:
                if m.get("fingerprint") == x.get("fingerprint"): continue
                if g.get("fingerprint") == x.get("fingerprint"): continue
                result = path_plausibility(g, m, x)
                candidate = {
                    "id": str(uuid.uuid4()),
                    "entry": {
                        "fingerprint": g.get("fingerprint"),
                        "nickname": g.get("nickname"),
                        "ip": g.get("ip"),
                        "country": g.get("country"),
                        "as": g.get("as"),
                        "advertised_bandwidth": g.get("advertised_bandwidth"),
                        "is_guard": g.get("is_guard")
                    },
                    "middle": {
                        "fingerprint": m.get("fingerprint"),
                        "nickname": m.get("nickname"),
                        "ip": m.get("ip"),
                        "country": m.get("country"),
                        "as": m.get("as"),
                        "advertised_bandwidth": m.get("advertised_bandwidth")
                    },
                    "exit": {
                        "fingerprint": x.get("fingerprint"),
                        "nickname": x.get("nickname"),
                        "ip": x.get("ip"),
                        "country": x.get("country"),
                        "as": x.get("as"),
                        "advertised_bandwidth": x.get("advertised_bandwidth"),
                        "is_exit": x.get("is_exit")
                    },
                    "score": result["score"],
                    "components": result["components"],
                    "generated_at": datetime.utcnow().isoformat() + "Z"
                }
                candidates.append(candidate)

    # deterministic sort by score (descending) then by id to stabilize ties
    candidates.sort(key=lambda it: (it["score"], it["id"]), reverse=True)
    top = candidates[:top_k]

    # store results (overwrite only if we have top results)
    if top:
        db.path_candidates.delete_many({})
        db.path_candidates.insert_many(top)
    return top


def generate_candidate_paths(limit_guards:int=50, limit_middles:int=150, limit_exits:int=50, top_k:int=1000, max_combinations:int=200000) -> List[Dict]:
    """
    Backwards-compatible wrapper: select candidates and then score them.
    Returns paths without MongoDB _id field for JSON serialization.
    """
    guards, middles, exits = select_candidate_relays(limit_guards, limit_middles, limit_exits)
    paths = score_candidate_paths(guards, middles, exits, top_k=top_k, max_combinations=max_combinations)
    # Remove _id field which is added by MongoDB and not JSON serializable
    for p in paths:
        p.pop("_id", None)
    return paths

def top_candidate_paths(limit:int=100) -> List[Dict]:
    docs = list(db.path_candidates.find({}, {"_id":0}).sort("score", -1).limit(limit))
    return docs
