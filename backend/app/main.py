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

# Internal imports
from .fetcher import fetch_and_store_relays
from .correlator import generate_candidate_paths, top_candidate_paths

app = FastAPI(title="TOR Unveil API", version="2.0")

# ---------------------------------------------------------
# CORS CONFIG (MANDATORY FOR FRONTEND)
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
# RELAYS – FIXED (NOW RETURNS ONLY NECESSARY FIELDS)
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
    }

    relays = list(db.relays.find({}, projection).limit(limit))
    return {"count": len(relays), "data": relays}


# ---------------------------------------------------------
# CORRELATOR ENDPOINTS
# ---------------------------------------------------------
@app.get("/paths/generate")
def api_generate_paths(
    guards: int = 30,
    middles: int = 80,
    exits: int = 30,
    top_k: int = 500
):
    top = generate_candidate_paths(
        limit_guards=guards,
        limit_middles=middles,
        limit_exits=exits,
        top_k=top_k
    )
    return {"count": len(top), "paths": top}


@app.get("/paths/top")
def api_top_paths(limit: int = 100):
    top = top_candidate_paths(limit=limit)
    return {"count": len(top), "paths": top}


# ---------------------------------------------------------
# TIMELINE ENDPOINT
# ---------------------------------------------------------
@app.get("/relay/{fp}/timeline")
def relay_timeline(fp: str):
    r = db.relays.find_one({"fingerprint": fp}, {"_id": 0})
    if not r:
        raise HTTPException(status_code=404, detail="Relay not found")
    return {"relay": r}


# ---------------------------------------------------------
# PDF REPORT GENERATOR
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
        }
    )
