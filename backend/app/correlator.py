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

def normalized_bandwidth_score(bw: Optional[int], max_bw: float = 50_000_000.0) -> float:
    if not bw:
        return 0.05
    s = float(bw) / float(max_bw)
    return min(1.0, s)

def role_score(flags: List[str]) -> float:
    score = 0.0
    if "Running" in flags: score += 0.4
    if "Stable" in flags: score += 0.2
    if "Valid" in flags: score += 0.2
    if "Fast" in flags: score += 0.2
    return min(1.0, score)

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

    # simple uptime score: average normalized pairwise overlap
    # Normalize by max typical active window (30 days) to avoid tiny numbers
    norm = 30.0
    uptime_score = min(1.0, ((overlap_em + overlap_mx) / 2.0) / norm)

    # bandwidth score
    bw_e = entry.get("advertised_bandwidth") or 0
    bw_m = middle.get("advertised_bandwidth") or 0
    bw_x = exit.get("advertised_bandwidth") or 0
    bw_score = (normalized_bandwidth_score(bw_e) + normalized_bandwidth_score(bw_m) + normalized_bandwidth_score(bw_x)) / 3.0

    # role flags
    role_s = (role_score(entry.get("flags", [])) + role_score(middle.get("flags", [])) + role_score(exit.get("flags", []))) / 3.0

    # AS diversity penalty (if entry and exit in same AS, small penalty)
    as_e = (entry.get("as") or "").lower()
    as_x = (exit.get("as") or "").lower()
    as_penalty = 0.85 if (as_e and as_x and as_e == as_x) else 1.0

    # country proximity (optional small boost when different countries)
    c_e = (entry.get("country") or "").upper()
    c_x = (exit.get("country") or "").upper()
    country_diversity_boost = 1.05 if (c_e and c_x and c_e != c_x) else 1.0

    # Weighted sum to final plausibility (explainable)
    final = (0.45 * uptime_score) + (0.30 * bw_score) + (0.25 * role_s)
    final = final * as_penalty * country_diversity_boost
    final = max(0.0, min(1.0, final))

    return {
        "score": round(final, 4),
        "components": {
            "uptime_score": round(uptime_score, 4),
            "bandwidth_score": round(bw_score, 4),
            "role_score": round(role_s, 4),
            "as_penalty": round(as_penalty, 3),
            "country_diversity_boost": round(country_diversity_boost, 3)
        }
    }

# -------------------------
# Candidate generation
# -------------------------
def generate_candidate_paths(limit_guards:int=50, limit_middles:int=150, limit_exits:int=50, top_k:int=1000) -> List[Dict]:
    """
    Generate candidate paths (entry->middle->exit), compute plausibility,
    sort by score and return top_k. Results are also stored in db.path_candidates.
    """
    guards = list(db.relays.find({"is_guard": True, "running": True}).sort("advertised_bandwidth", -1).limit(limit_guards))
    exits = list(db.relays.find({"is_exit": True, "running": True}).sort("advertised_bandwidth", -1).limit(limit_exits))
    middles = list(db.relays.find({"is_guard": False, "is_exit": False, "running": True}).sort("advertised_bandwidth", -1).limit(limit_middles))

    candidates = []
    for g in guards:
        for m in middles:
            # quick heuristic: avoid same fingerprint or same IP overlap
            if g.get("fingerprint") == m.get("fingerprint"): continue
            for x in exits:
                if m.get("fingerprint") == x.get("fingerprint"): continue
                if g.get("fingerprint") == x.get("fingerprint"): continue
                result = path_plausibility(g, m, x)
                candidate = {
                    "id": str(uuid.uuid4()),
                    "entry": {"fingerprint": g.get("fingerprint"), "nickname": g.get("nickname"), "ip": g.get("ip"), "country": g.get("country"), "as": g.get("as")},
                    "middle": {"fingerprint": m.get("fingerprint"), "nickname": m.get("nickname"), "ip": m.get("ip"), "country": m.get("country"), "as": m.get("as")},
                    "exit": {"fingerprint": x.get("fingerprint"), "nickname": x.get("nickname"), "ip": x.get("ip"), "country": x.get("country"), "as": x.get("as")},
                    "score": result["score"],
                    "components": result["components"],
                    "generated_at": datetime.utcnow()
                }
                candidates.append(candidate)

    candidates.sort(key=lambda it: it["score"], reverse=True)
    top = candidates[:top_k]

    # store in DB collection (overwrite), but keep only summary fields
    db.path_candidates.delete_many({})
    if top:
        # store sanitized docs
        db.path_candidates.insert_many(top)
    return top

def top_candidate_paths(limit:int=100) -> List[Dict]:
    docs = list(db.path_candidates.find({}, {"_id":0}).sort("score", -1).limit(limit))
    return docs
