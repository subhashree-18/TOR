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
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Header
    p.setFont("Helvetica-Bold", 14)
    p.drawString(40, height - 40, "TOR Unveil — Path Plausibility Report")

    p.setFont("Helvetica", 10)
    p.drawString(40, height - 60, f"Generated: {datetime.datetime.utcnow().isoformat()} UTC")
    p.drawString(40, height - 80, f"Path ID: {path_candidate.get('id')}")
    p.drawString(40, height - 100, f"Score: {path_candidate.get('score')}")

    # Components
    p.drawString(40, height - 130, "Components:")
    y = height - 150
    for k, v in path_candidate.get("components", {}).items():
        p.drawString(60, y, f"{k}: {v}")
        y -= 14

    # Entry / Middle / Exit details
    def block(title, obj):
        nonlocal y
        y -= 10
        p.setFont("Helvetica-Bold", 12)
        p.drawString(40, y, title)
        p.setFont("Helvetica", 10)
        y -= 14
        for k, v in obj.items():
            p.drawString(60, y, f"{k}: {v}")
            y -= 12

    block("Entry Relay", path_candidate.get("entry", {}))
    block("Middle Relay", path_candidate.get("middle", {}))
    block("Exit Relay", path_candidate.get("exit", {}))

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
