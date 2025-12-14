# backend/app/main.py

from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import datetime
from dateutil import parser as date_parser

# Internal imports
from .fetcher import fetch_and_store_relays
from .correlator import generate_candidate_paths, top_candidate_paths
from typing import List, Dict, Any, Optional

app = FastAPI(title="TOR Unveil API", version="2.0")

# ---------------------------------------------------------
# CORS CONFIG (MANDATORY FOR FRONTEND)
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # relax for now; can tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------
MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017/torunveil")
client = MongoClient(MONGO_URL)
db = client["torunveil"]


# ---------------------------------------------------------
# BASIC ROUTES
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Backend running successfully"}


@app.get("/relays/fetch")
def fetch_relays():
    count = fetch_and_store_relays()
    return {"status": "success", "stored_relays": count}


# ---------------------------------------------------------
# RELAYS – WITH NEW FIELDS
# ---------------------------------------------------------
@app.get("/relays")
def get_relays(limit: int = 500):
    projection = {
        "_id": 0,
        "fingerprint": 1,
        "nickname": 1,
        "or_addresses": 1,
        "ip": 1,
        "country": 1,
        "flags": 1,
        "is_exit": 1,
        "is_guard": 1,
        "running": 1,
        "advertised_bandwidth": 1,
        "first_seen": 1,
        "last_seen": 1,
        "hostnames": 1,
        "as": 1,
        "lat": 1,
        "lon": 1,
        "risk_score": 1,
        "is_malicious": 1,
    }

    relays = list(db.relays.find({}, projection).limit(limit))
    return {"count": len(relays), "data": relays}


# ---------------------------------------------------------
# NEW: MAP ENDPOINT
# ---------------------------------------------------------
@app.get("/relays/map")
def relays_map(limit: int = 2000):
    """
    Return relays with coordinates so frontend can plot them on a map.
    """
    projection = {
        "_id": 0,
        "fingerprint": 1,
        "nickname": 1,
        "ip": 1,
        "country": 1,
        "lat": 1,
        "lon": 1,
        "risk_score": 1,
        "is_exit": 1,
        "is_guard": 1,
        "is_malicious": 1,
    }

    relays = list(
        db.relays.find(
            {"lat": {"$ne": None}, "lon": {"$ne": None}},
            projection,
        ).limit(limit)
    )
    return {"count": len(relays), "data": relays}


# ---------------------------------------------------------
# NEW: RISK TOP-K ENDPOINT
# ---------------------------------------------------------
@app.get("/risk/top")
def api_risk_top(limit: int = 50):
    """
    Return top N highest-risk relays.
    """
    projection = {
        "_id": 0,
        "fingerprint": 1,
        "nickname": 1,
        "ip": 1,
        "country": 1,
        "flags": 1,
        "risk_score": 1,
        "is_malicious": 1,
        "advertised_bandwidth": 1,
        "as": 1,
    }

    cursor = (
        db.relays.find(
            {"risk_score": {"$exists": True}},
            projection,
        )
        .sort("risk_score", -1)
        .limit(limit)
    )
    relays = list(cursor)
    return {"count": len(relays), "data": relays}


# ---------------------------------------------------------
# NEW: THREAT INTEL / MALICIOUS RELAYS
# ---------------------------------------------------------
@app.get("/intel/malicious")
def api_malicious(limit: int = 100):
    """
    Return relays flagged as malicious by simple intel rules.
    """
    projection = {
        "_id": 0,
        "fingerprint": 1,
        "nickname": 1,
        "ip": 1,
        "country": 1,
        "flags": 1,
        "risk_score": 1,
        "is_malicious": 1,
        "advertised_bandwidth": 1,
        "as": 1,
    }

    relays = list(
        db.relays.find(
            {"is_malicious": True},
            projection,
        ).limit(limit)
    )
    return {"count": len(relays), "data": relays}


# ---------------------------------------------------------
# CORRELATOR ENDPOINTS (existing)
# ---------------------------------------------------------
@app.get("/paths/generate")
def api_generate_paths(
    guards: int = 30,
    middles: int = 80,
    exits: int = 30,
    top_k: int = 500,
):
    top = generate_candidate_paths(
        limit_guards=guards,
        limit_middles=middles,
        limit_exits=exits,
        top_k=top_k,
    )
    return {"count": len(top), "paths": top}


@app.get("/paths/top")
def api_top_paths(limit: int = 100):
    top = top_candidate_paths(limit=limit)
    return {"count": len(top), "paths": top}


# ---------------------------------------------------------
# TIMELINE ENDPOINT (existing)
# ---------------------------------------------------------
@app.get("/relay/{fp}/timeline")
def relay_timeline(fp: str):
    r = db.relays.find_one({"fingerprint": fp}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Relay not found")
    return {"relay": r}


# ---------------------------------------------------------
# AGGREGATED TIMELINE (new)
# ---------------------------------------------------------
def _to_dt(v) -> Optional[datetime.datetime]:
    if not v:
        return None
    if isinstance(v, datetime.datetime):
        return v
    try:
        return date_parser.parse(v)
    except Exception:
        return None


def _short_fp(fp: str) -> str:
    if not fp:
        return "unknown"
    return fp[:6]


@app.get("/api/timeline")
def api_timeline(limit: int = 500, start: Optional[str] = None, end: Optional[str] = None):
    """
    Return an event-based timeline for relays and generated paths.

    Events include:
      - Relay Active: when a relay was first observed
      - Exit Observed: when an exit-capable relay was first observed
      - Relay Last Seen: when a relay was last observed
      - Path Correlated: when a candidate path was generated

    The response is a list of simple events ordered by timestamp (newest first).
    Fields are non-technical and suitable for explanation to non-technical users.
    """
    start_dt = _to_dt(start)
    end_dt = _to_dt(end)

    events: List[Dict[str, Any]] = []

    # --- Relay events ---
    # Fetch relays with minimal projection to build events.
    projection = {"_id": 0, "fingerprint": 1, "nickname": 1, "first_seen": 1, "last_seen": 1, "is_exit": 1, "country": 1}
    cursor = db.relays.find({}, projection)
    for r in cursor:
        fp = r.get("fingerprint")
        nick = r.get("nickname") or _short_fp(fp)
        country = r.get("country")

        # first_seen -> Relay Active
        fs = _to_dt(r.get("first_seen"))
        if fs and (not start_dt or fs >= start_dt) and (not end_dt or fs <= end_dt):
            events.append({
                "timestamp": fs.isoformat(),
                "label": "Relay Active",
                "description": f"Relay {nick} ({_short_fp(fp)}) was first observed in {country or 'unknown country'}.",
                "fingerprint": _short_fp(fp),
                "type": "relay"
            })

        # if relay is exit, create an Exit Observed event at first_seen
        if r.get("is_exit") and fs and (not start_dt or fs >= start_dt) and (not end_dt or fs <= end_dt):
            events.append({
                "timestamp": fs.isoformat(),
                "label": "Exit Observed",
                "description": f"Relay {nick} ({_short_fp(fp)}) was observed providing exit capability.",
                "fingerprint": _short_fp(fp),
                "type": "relay"
            })

        # last_seen -> Relay Last Seen
        ls = _to_dt(r.get("last_seen"))
        if ls and (not start_dt or ls >= start_dt) and (not end_dt or ls <= end_dt):
            events.append({
                "timestamp": ls.isoformat(),
                "label": "Relay Last Seen",
                "description": f"Relay {nick} ({_short_fp(fp)}) was last observed on this date.",
                "fingerprint": _short_fp(fp),
                "type": "relay"
            })

    # --- Path events ---
    # Paths stored in db.path_candidates include 'generated_at'
    path_cursor = db.path_candidates.find({}, {"_id": 0, "id": 1, "entry": 1, "exit": 1, "score": 1, "generated_at": 1}).limit(limit)
    for p in path_cursor:
        ga = _to_dt(p.get("generated_at"))
        if not ga:
            continue
        if start_dt and ga < start_dt:
            continue
        if end_dt and ga > end_dt:
            continue

        entry_fp = (p.get("entry") or {}).get("fingerprint")
        exit_fp = (p.get("exit") or {}).get("fingerprint")
        ef = _short_fp(entry_fp)
        xf = _short_fp(exit_fp)

        events.append({
            "timestamp": ga.isoformat(),
            "label": "Path Correlated",
            "description": f"A plausible path was generated linking entry {ef} to exit {xf} (score: {p.get('score')}).",
            "path_id": p.get("id"),
            "entry": ef,
            "exit": xf,
            "type": "path"
        })

    # Order events by timestamp (newest first)
    def _parse_ts(e):
        try:
            ts_str = e["timestamp"]
            dt = date_parser.parse(ts_str)
            # Remove timezone info for comparison (make naive)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except Exception:
            return datetime.datetime.min

    events.sort(key=_parse_ts, reverse=True)

    # apply global limit
    events = events[:limit]

    return {"count": len(events), "events": events}


# ---------------------------------------------------------
# PDF REPORT GENERATOR (existing)
# ---------------------------------------------------------
def build_report_pdf(path_candidate: dict) -> bytes:
    """
    Generate professional forensic report PDF with structured sections:
    - Executive Summary (non-technical)
    - Technical Findings (detailed)
    - Timeline (metadata events)
    - Confidence & Limitations
    - Legal & Ethical Disclaimers
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    margin_left = 40
    margin_right = 40
    margin_top = 40
    y_position = height - margin_top
    line_height = 14
    
    def draw_title(text, size=14):
        nonlocal y_position
        p.setFont("Helvetica-Bold", size)
        p.drawString(margin_left, y_position, text)
        y_position -= (line_height + 4)
    
    def draw_text(text, size=10, indent=0):
        nonlocal y_position
        p.setFont("Helvetica", size)
        p.drawString(margin_left + indent, y_position, text)
        y_position -= line_height
    
    def draw_separator():
        nonlocal y_position
        p.setLineWidth(0.5)
        p.line(margin_left, y_position, width - margin_right, y_position)
        y_position -= 10
    
    def check_page_break():
        nonlocal y_position
        if y_position < 100:
            p.showPage()
            y_position = height - margin_top
    
    # ========== PAGE 1: HEADER & EXECUTIVE SUMMARY ==========
    draw_title("TOR UNVEIL – FORENSIC INVESTIGATION REPORT", 16)
    draw_text(f"Tamil Nadu Police Cyber Crime Wing", 10)
    draw_text(f"Generated: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}", 9)
    draw_separator()
    
    # Report Metadata
    draw_text(f"Path ID: {path_candidate.get('id', 'N/A')}", 10)
    draw_text(f"Plausibility Score: {path_candidate.get('score', 0.0):.1%}", 10)
    confidence_level = "HIGH" if path_candidate.get('score', 0) >= 0.8 else ("MEDIUM" if path_candidate.get('score', 0) >= 0.5 else "LOW")
    draw_text(f"Confidence Level: {confidence_level}", 10)
    y_position -= 6
    
    # Executive Summary
    draw_title("EXECUTIVE SUMMARY", 12)
    draw_text("This report presents a statistical analysis of TOR network metadata correlation,", 10)
    draw_text("identifying a probable path configuration based on timing and topological indicators.", 10)
    draw_text("", 10)
    draw_text("PURPOSE: Investigative support for cybercrime cases. This analysis is metadata-only", 10)
    draw_text("and does NOT break TOR anonymity or identify actual users.", 10)
    draw_text("", 10)
    draw_text("KEY FINDINGS:", 10, 10)
    draw_text("The entry → middle → exit relay configuration identified herein exhibits", 10, 20)
    draw_text(f"a correlation score of {path_candidate.get('score', 0.0):.1%}, indicating {confidence_level.lower()} confidence", 10, 20)
    draw_text("that these relays were temporally and topologically compatible for routing a", 10, 20)
    draw_text("single TOR connection.", 10, 20)
    y_position -= 6
    
    check_page_break()
    
    # ========== TECHNICAL FINDINGS ==========
    draw_title("TECHNICAL FINDINGS", 12)
    
    # Entry Relay
    draw_title("Entry Node (Connection Entry Point)", 11)
    entry = path_candidate.get("entry", {})
    draw_text(f"Nickname: {entry.get('nickname', 'Unknown')}", 10, 10)
    draw_text(f"Fingerprint: {entry.get('fingerprint', 'N/A')[:16]}...", 9, 10)
    draw_text(f"IP Address: {entry.get('ip', 'Unknown')}", 10, 10)
    draw_text(f"Country: {entry.get('country', 'Unknown')}", 10, 10)
    draw_text(f"Advertised Bandwidth: {entry.get('advertised_bandwidth', 0) / 1_000_000:.1f} Mbps", 10, 10)
    draw_text(f"Uptime: {entry.get('first_seen', 'Unknown')} to {entry.get('last_seen', 'Unknown')}", 9, 10)
    y_position -= 4
    
    # Middle Relay
    draw_title("Middle Relay (Intermediate Node)", 11)
    middle = path_candidate.get("middle", {})
    draw_text(f"Nickname: {middle.get('nickname', 'Unknown')}", 10, 10)
    draw_text(f"Fingerprint: {middle.get('fingerprint', 'N/A')[:16]}...", 9, 10)
    draw_text(f"IP Address: {middle.get('ip', 'Unknown')}", 10, 10)
    draw_text(f"Country: {middle.get('country', 'Unknown')}", 10, 10)
    draw_text(f"Advertised Bandwidth: {middle.get('advertised_bandwidth', 0) / 1_000_000:.1f} Mbps", 10, 10)
    draw_text(f"Uptime: {middle.get('first_seen', 'Unknown')} to {middle.get('last_seen', 'Unknown')}", 9, 10)
    y_position -= 4
    
    # Exit Relay
    draw_title("Exit Node (Connection Exit Point)", 11)
    exit_node = path_candidate.get("exit", {})
    draw_text(f"Nickname: {exit_node.get('nickname', 'Unknown')}", 10, 10)
    draw_text(f"Fingerprint: {exit_node.get('fingerprint', 'N/A')[:16]}...", 9, 10)
    draw_text(f"IP Address: {exit_node.get('ip', 'Unknown')}", 10, 10)
    draw_text(f"Country: {exit_node.get('country', 'Unknown')}", 10, 10)
    draw_text(f"Advertised Bandwidth: {exit_node.get('advertised_bandwidth', 0) / 1_000_000:.1f} Mbps", 10, 10)
    draw_text(f"Uptime: {exit_node.get('first_seen', 'Unknown')} to {exit_node.get('last_seen', 'Unknown')}", 9, 10)
    
    check_page_break()
    
    # ========== SCORE BREAKDOWN ==========
    draw_title("SCORE COMPONENTS & METHODOLOGY", 12)
    components = path_candidate.get("components", {})
    draw_text("Uptime Score: Temporal overlap + stability", 10, 10)
    draw_text(f"  Value: {components.get('uptime_score', 0):.3f} (Weight: 30%)", 9, 20)
    draw_text("Bandwidth Score: Relay capacity distribution", 10, 10)
    draw_text(f"  Value: {components.get('bandwidth_score', 0):.3f} (Weight: 45%)", 9, 20)
    draw_text("Role Score: TOR directory flags (Running, Valid, Stable, etc.)", 10, 10)
    draw_text(f"  Value: {components.get('role_score', 0):.3f} (Weight: 25%)", 9, 20)
    y_position -= 6
    
    draw_text("Applied Penalties:", 10)
    draw_text(f"Autonomous System Penalty: {components.get('as_penalty', 1.0):.2f}x", 10, 10)
    draw_text("  (Applied if entry & exit share same AS)", 9, 20)
    draw_text(f"Country Penalty: {components.get('country_penalty', 1.0):.2f}x", 10, 10)
    draw_text("  (Applied if entry & exit in same country)", 9, 20)
    y_position -= 6
    
    draw_text(f"Final Score: {path_candidate.get('score', 0.0):.1%}", 10)
    draw_text("(Capped at 95% to prevent unrealistic confidence claims)", 9)
    
    check_page_break()
    
    # ========== CONFIDENCE & LIMITATIONS ==========
    draw_title("CONFIDENCE ASSESSMENT & LIMITATIONS", 12)
    draw_text("This analysis provides PLAUSIBILITY estimates based on metadata correlation only:", 10)
    y_position -= 2
    draw_text("• NO packet inspection or traffic analysis performed", 10, 10)
    draw_text("• NO TOR anonymity broken or attempted", 10, 10)
    draw_text("• NO user identification or endpoint deanonymization", 10, 10)
    draw_text("• Metadata: uptime, bandwidth, flags from public TOR directory", 10, 10)
    draw_text("• Score does NOT prove actual usage — indicates plausibility only", 10, 10)
    y_position -= 6
    
    draw_text("Limitations:", 10)
    draw_text("• False Positives: High-scoring paths may not represent actual traffic", 10, 10)
    draw_text("• False Negatives: Low-scoring paths could still be valid routes", 10, 10)
    draw_text("• Temporal Variability: Relay uptime windows change; scores reflect snapshots", 10, 10)
    draw_text("• No Causation: Correlation ≠ Causation in network analysis", 10, 10)
    y_position -= 6
    
    # ========== LEGAL & ETHICAL DISCLAIMER ==========
    draw_title("LEGAL & ETHICAL STATEMENT", 12)
    draw_text("AUTHORIZED LAW ENFORCEMENT USE ONLY", 10)
    draw_text("This tool is designed for investigative support in cybercrime cases.", 9)
    y_position -= 4
    draw_text("IMPORTANT DISCLAIMERS:", 10)
    draw_text("1. This analysis is metadata-only and does NOT break TOR anonymity", 9, 10)
    draw_text("2. Results must be independently validated through other investigative methods", 9, 10)
    draw_text("3. These findings are NOT admissible as proof; use for investigative guidance only", 9, 10)
    draw_text("4. Compliance: Indian Penal Code § 43, § 66 (cybercrime), § 120 (investigation)", 9, 10)
    draw_text("5. Court admissibility requires corroboration with non-metadata evidence", 9, 10)
    y_position -= 6
    
    draw_text("Prepared by: TOR Unveil v2.0 — Tamil Nadu Police Cyber Crime Wing", 10)
    draw_text(f"Date: {datetime.datetime.utcnow().strftime('%Y-%m-%d')}", 10)
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.read()


@app.get("/export/report")
def export_report(path_id: str):
    path_candidate = db.path_candidates.find_one({"id": path_id}, {"_id": 0})
    if not path_candidate:
        raise HTTPException(status_code=404, detail="Path candidate not found")

    pdf_bytes = build_report_pdf(path_candidate)

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="tor_unveil_report_{path_id}.pdf"'
        },
    )


# ---------------------------------------------------------
# NEW: METADATA & PROVENANCE ENDPOINTS
# ---------------------------------------------------------
@app.get("/api/metadata")
def get_metadata():
    """
    Returns metadata about data sources and provenance for transparency.
    All data is metadata-only (no packet inspection, no deanonymization).
    """
    return {
        "platform": "TOR Unveil - Police Cybercrime Investigation Assistant",
        "version": "2.0",
        "legal_status": "Investigative Support Tool - Metadata Analysis Only",
        "data_sources": {
            "onionoo": {
                "name": "Onionoo - TOR Directory Services",
                "url": "https://onionoo.torproject.org",
                "description": "Live TOR network relay metadata, consensus documents, bandwidth statistics",
                "refresh_frequency": "Hourly",
                "data_types": ["relay_status", "bandwidth", "flags", "uptime", "geographic_location"]
            },
            "collector": {
                "name": "CollecTor - Historical TOR Relay Data",
                "url": "https://collector.torproject.org",
                "description": "Archived TOR directory documents, consensus history, relay descriptors",
                "refresh_frequency": "Daily",
                "data_types": ["historical_consensus", "relay_descriptors", "network_archive"]
            },
            "geoip": {
                "name": "GeoIP Databases",
                "description": "IP geolocation data for relay locations (non-identifying)",
                "data_types": ["country_code", "coordinates", "ASN"]
            }
        },
        "data_limitations": [
            "No packet capture or inspection",
            "No deanonymization attempts",
            "Correlation scores are plausibility estimates only, not proof",
            "Geographic data is low-resolution (country-level)",
            "Relay metadata is public TOR directory data only",
            "No identification of actual users or traffic"
        ],
        "legal_notice": "TOR Unveil is a metadata analysis tool for law enforcement investigative support. Results must be validated through independent investigative methods. No claims of attribution or TOR deanonymization.",
        "ethical_guidelines": {
            "purpose": "Support legitimate cybercrime investigations",
            "scope": "Metadata correlation only",
            "transparency": "All scoring explained and auditable",
            "compliance": "Indian Penal Code § 43, § 66 (cybercrime), § 120 (investigation authorization)"
        }
    }


@app.get("/api/scoring-methodology")
def scoring_methodology():
    """
    Explains the scoring methodology used in path plausibility calculation.
    Ensures transparency and explainability for police review.
    """
    return {
        "title": "TOR Path Plausibility Scoring Methodology",
        "version": "2.0",
        "purpose": "Estimate correlation plausibility between network metadata (uptime, bandwidth, flags)",
        "important_disclaimer": "Scores are statistical estimates, NOT proof of actual network usage",
        "score_range": {
            "minimum": 0.30,
            "maximum": 0.95,
            "reason": "Prevents unrealistic claims while allowing natural variation based on relay characteristics"
        },
        "confidence_levels": {
            "HIGH": {"range": [0.80, 0.95], "interpretation": "Strong correlation patterns observed"},
            "MEDIUM": {"range": [0.50, 0.79], "interpretation": "Moderate correlation indicators present"},
            "LOW": {"range": [0.30, 0.49], "interpretation": "Weak or limited correlation evidence"}
        },
        "score_components": {
            "uptime_score": {
                "weight": 0.30,
                "factors": [
                    "Temporal overlap between entry/middle/exit relay uptime windows",
                    "Individual relay stability (days online)",
                    "Reliability indicators from uptime patterns"
                ],
                "range": [0.0, 1.0]
            },
            "bandwidth_score": {
                "weight": 0.45,
                "factors": [
                    "Advertised bandwidth of each relay",
                    "Normalized percentile-based scoring",
                    "Network capacity contribution"
                ],
                "range": [0.0, 1.0],
                "note": "Highest variation component - differentiates between relay tiers"
            },
            "role_score": {
                "weight": 0.25,
                "factors": [
                    "TOR directory flags: Running, Valid, Stable, Fast, Guard",
                    "Relay role reliability and quality indicators",
                    "Consensus participation"
                ],
                "range": [0.0, 1.0]
            },
            "as_penalty": {
                "value": 0.70,
                "applied_when": "Entry and Exit nodes share same Autonomous System",
                "reason": "Network topology suggests suspicious configuration"
            },
            "country_penalty": {
                "value": 0.60,
                "applied_when": "Entry and Exit nodes in same country",
                "reason": "Same-country entry/exit is uncommon in TOR network design"
            }
        },
        "calculation": {
            "formula": "final_score = (0.30 × uptime_score + 0.45 × bandwidth_score + 0.25 × role_score) × as_penalty × country_penalty",
            "post_processing": "Capped at 95% maximum to ensure empirical humility",
            "unit": "Dimensionless confidence score (0–1 scale)"
        },
        "explainability": {
            "transparency": "Every component is independently calculable and auditable",
            "auditability": "Component breakdown provided with each path score",
            "reproducibility": "Same relay data + same algorithm = same score"
        },
        "limitations": {
            "metadata_only": "Based on public TOR directory metadata, not packet analysis",
            "timing_variation": "Relay uptime windows vary; scores reflect overlap probability",
            "no_certainty": "Correlation does not imply causation or actual usage",
            "false_positives": "High-scoring paths may not represent actual user traffic",
            "false_negatives": "Low-scoring paths could still be valid network routes"
        }
    }
