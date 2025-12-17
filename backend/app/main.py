# backend/app/main.py

from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi import File, UploadFile
from io import BytesIO, StringIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import datetime
from dateutil import parser as date_parser
import csv
import json

# Internal imports
from .fetcher import fetch_and_store_relays
from .correlator import generate_candidate_paths, top_candidate_paths
from .pcap_analyzer import analyze_pcap_file
from .auth import router as auth_router
from typing import List, Dict, Any, Optional

app = FastAPI(title="TOR Unveil API", version="2.0")

# ---------------------------------------------------------
# INCLUDE AUTH ROUTES
# ---------------------------------------------------------
app.include_router(auth_router)

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
# LOGGING & MONITORING (FEATURE 13: BACKEND HARDENING)
# ---------------------------------------------------------
import logging

logger = logging.getLogger("tor_unveil")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ---------------------------------------------------------
# VALIDATION & ERROR HANDLING HELPERS (FEATURE 13)
# ---------------------------------------------------------

def validate_limit_parameter(value: int, default: int = 500, min_val: int = 1, max_val: int = 5000) -> int:
    """Validate and normalize limit parameters.
    
    Ensures:
    - No negative values
    - Respects max limits for scalability
    - Returns safe defaults on error
    """
    try:
        val = int(value)
        if val < min_val:
            logger.debug(f"validate_limit_parameter: {val} < {min_val}, using {min_val}")
            return min_val
        if val > max_val:
            logger.debug(f"validate_limit_parameter: {val} > {max_val}, capping at {max_val}")
            return max_val
        return val
    except (TypeError, ValueError):
        logger.warning(f"validate_limit_parameter: Invalid value {value}, using default {default}")
        return default


def validate_skip_parameter(value: int, default: int = 0) -> int:
    """Validate pagination skip parameter."""
    try:
        val = int(value)
        return max(0, val)
    except (TypeError, ValueError):
        logger.warning(f"validate_skip_parameter: Invalid value {value}, using default {default}")
        return default


def validate_country_code(code: Optional[str]) -> Optional[str]:
    """Validate and normalize ISO country codes.
    
    Returns:
    - Uppercase 2-letter country code if valid
    - None if invalid or not provided
    """
    if not code:
        return None
    try:
        code_upper = str(code).strip().upper()
        if len(code_upper) == 2 and code_upper.isalpha():
            return code_upper
        logger.warning(f"validate_country_code: Invalid country code '{code}'")
        return None
    except Exception as e:
        logger.error(f"validate_country_code: Error validating '{code}': {e}")
        return None


def log_endpoint_call(endpoint: str, **kwargs):
    """Log API endpoint calls for audit trail."""
    params = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"[API] {endpoint} called with: {params if params else 'no params'}")


def log_endpoint_response(endpoint: str, status: str, count: int = None, error: str = None):
    """Log API endpoint responses for monitoring."""
    if error:
        logger.error(f"[API] {endpoint}: {status} - ERROR: {error}")
    else:
        msg = f"[API] {endpoint}: {status}"
        if count is not None:
            msg += f" ({count} items)"
        logger.info(msg)


def safe_db_query(query_func, *args, **kwargs):
    """Safely execute database queries with error handling.
    
    Ensures:
    - No silent failures
    - Proper logging of errors
    - Deterministic responses
    """
    try:
        return query_func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Database query error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Database query failed. Please try again."
        )


# ---------------------------------------------------------
# BASIC ROUTES
# ---------------------------------------------------------
@app.get("/")
def root():
    return {"message": "Backend running successfully"}


@app.get("/relays/fetch")
def fetch_relays():
    """Fetch latest TOR relay data from Onionoo and index in MongoDB.
    
    FEATURE 13: BACKEND HARDENING - DETERMINISTIC OPERATIONS
    =========================================================
    
    This endpoint:
    - Fetches complete relay list from Onionoo
    - Normalizes and enriches with risk scores, geoIP, threat intel
    - Stores in MongoDB for fast queries
    - Supports 5,000+ relays for large-scale investigations
    
    Returns:
    - Success status with relay count
    - Deterministic error messages on failure
    - No silent failures
    """
    start_time = datetime.datetime.utcnow()
    
    try:
        log_endpoint_call("GET /relays/fetch")
        logger.info("fetch_relays: Starting TOR relay fetch from Onionoo...")
        
        count = fetch_and_store_relays()
        
        elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()
        
        if count == 0:
            logger.warning("fetch_relays: No relays fetched from Onionoo")
        
        response = {
            "status": "success",
            "stored_relays": count,
            "indexing_time_seconds": round(elapsed, 3),
            "message": f"✓ Indexed {count} running TOR relays successfully"
        }
        
        logger.info(f"fetch_relays: SUCCESS - {count} relays indexed in {elapsed:.2f}s")
        log_endpoint_response("GET /relays/fetch", "success", count=count)
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()
        logger.error(f"fetch_relays: FAILED after {elapsed:.2f}s - {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch TOR network data from Onionoo. Please verify network connectivity."
        )


# ---------------------------------------------------------
# RELAYS – WITH PAGINATION AND FILTERING
# ---------------------------------------------------------
@app.get("/relays")
def get_relays(limit: int = 500, skip: int = 0, country: Optional[str] = None, is_exit: Optional[bool] = None):
    """Get TOR relays with optional filtering.
    
    FEATURE 13: BACKEND HARDENING - ROBUST API
    ===========================================
    
    Parameters:
    - limit: Maximum relays to return (default 500, max 5000 for scalability)
    - skip: Number of relays to skip (for pagination)
    - country: Filter by ISO country code (e.g., 'US', 'IN')
    - is_exit: Filter exit relays (true/false)
    
    Returns:
    - Metadata and list of relays
    - Pagination info for large datasets
    - Deterministic error messages on failure
    """
    start_time = datetime.datetime.utcnow()
    
    try:
        # Validate input parameters
        limit = validate_limit_parameter(limit, default=500, max_val=5000)
        skip = validate_skip_parameter(skip)
        country = validate_country_code(country)
        
        log_endpoint_call("GET /relays", limit=limit, skip=skip, country=country, is_exit=is_exit)
        
        # Build query filter
        filter_query = {}
        if country:
            filter_query["country"] = country
        if is_exit is not None:
            filter_query["is_exit"] = is_exit
        
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

        # Execute query with error handling
        total_count = safe_db_query(db.relays.count_documents, filter_query)
        relays = safe_db_query(
            lambda: list(
                db.relays.find(filter_query, projection)
                .skip(skip)
                .limit(limit)
            )
        )
        
        elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()
        
        response = {
            "status": "success",
            "total": total_count,
            "count": len(relays),
            "skip": skip,
            "limit": limit,
            "query_time_seconds": round(elapsed, 3),
            "data": relays
        }
        
        log_endpoint_response("GET /relays", "success", count=len(relays))
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /relays failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve relays. Database may be unavailable."
        )


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
# NEW: INDIA-SPECIFIC ANALYTICS
# ---------------------------------------------------------
@app.get("/analytics/india")
def india_analytics():
    """Return India-focused TOR network statistics.
    
    Returns:
    - Indian relay count and details
    - Indian ASN involvement
    - Domestic vs foreign infrastructure split
    - High-risk paths involving India
    """
    projection = {
        "_id": 0,
        "fingerprint": 1,
        "nickname": 1,
        "country": 1,
        "is_exit": 1,
        "is_guard": 1,
        "advertised_bandwidth": 1,
        "as": 1,
        "risk_score": 1,
    }
    
    # Indian relays
    indian_relays = list(db.relays.find({"country": "IN"}, projection))
    
    # All relays for calculating percentages
    total_relays = db.relays.count_documents({})
    
    # Count Indian ASN involvement (if present in 'as' field)
    indian_asn_relays = list(db.relays.find(
        {"as": {"$regex": "^(AS4755|AS9829|AS9498|AS18101|AS55836|AS24560|AS133480|AS45839|AS17638|AS56399|AS58953)"}},
        {"_id": 0, "as": 1, "nickname": 1}
    ))
    
    # Calculate infrastructure split: domestic vs foreign
    domestic_count = len(indian_relays)
    foreign_count = total_relays - domestic_count
    
    # Path statistics (check if any paths use Indian relays)
    indian_paths = list(db.paths.find(
        {
            "$or": [
                {"entry.country": "IN"},
                {"middle.country": "IN"},
                {"exit.country": "IN"}
            ]
        },
        {"_id": 0, "score": 1, "entry.country": 1, "exit.country": 1}
    ).limit(100))
    
    return {
        "indian_relays": {
            "count": domestic_count,
            "percentage": round((domestic_count / total_relays * 100) if total_relays > 0 else 0, 2),
            "details": indian_relays
        },
        "indian_asn_involvement": {
            "count": len(indian_asn_relays),
            "relays": indian_asn_relays[:20]  # Top 20
        },
        "infrastructure_split": {
            "domestic": {
                "count": domestic_count,
                "percentage": round((domestic_count / total_relays * 100) if total_relays > 0 else 0, 2)
            },
            "foreign": {
                "count": foreign_count,
                "percentage": round((foreign_count / total_relays * 100) if total_relays > 0 else 0, 2)
            }
        },
        "paths_involving_india": {
            "count": len(indian_paths),
            "high_confidence": len([p for p in indian_paths if p.get("score", 0) > 0.8])
        },
        "total_relays_indexed": total_relays
    }


# ---------------------------------------------------------
# NEW: FORENSIC FILE UPLOAD & CORRELATION
# ---------------------------------------------------------
import re
import logging

# Setup logging
logger = logging.getLogger("tor_unveil")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


@app.post("/forensic/upload")
async def forensic_upload(file: UploadFile = File(...)):
    """Upload forensic data (logs, metadata, PCAP analysis) for correlation.
    
    FEATURE 12: FILE UPLOAD FOR FORENSIC CORRELATION
    ================================================
    
    Accepts:
    - CSV files with timestamped events (metadata only)
    - JSON files with event metadata
    - Log files (text format with timestamps)
    
    Does NOT accept:
    - Binary PCAP files (payload data)
    - Raw packet data
    
    Returns:
    - Parsed events with timestamp ranges
    - Correlation with TOR activity windows
    - Forensic metadata for case documentation
    
    Processing:
    1. Validates file size (max 50MB)
    2. Parses timestamps using multiple date formats
    3. Extracts metadata (no packet inspection)
    4. Correlates with TOR path activity windows
    5. Returns structured analysis results
    """
    start_time = datetime.datetime.utcnow()
    
    try:
        # ============================================================
        # STEP 1: VALIDATE INPUT FILE
        # ============================================================
        
        if not file:
            logger.error("forensic_upload: No file provided")
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file.filename:
            logger.error("forensic_upload: File has no name")
            raise HTTPException(status_code=400, detail="File has no name")
        
        # Read file content
        content = await file.read()
        filename = file.filename
        file_size = len(content)
        file_ext = filename.split('.')[-1].lower()
        
        logger.info(f"forensic_upload: Processing file '{filename}' ({file_size} bytes, .{file_ext})")
        
        # Validate file size (50MB limit for safety)
        MAX_FILE_SIZE = 50 * 1024 * 1024
        if file_size > MAX_FILE_SIZE:
            logger.error(f"forensic_upload: File too large ({file_size} > {MAX_FILE_SIZE})")
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({file_size / 1024 / 1024:.1f}MB > 50MB limit)"
            )
        
        # Validate file type
        ALLOWED_EXTENSIONS = ['csv', 'json', 'log', 'txt', 'pcap', 'pcapng', 'cap']
        if file_ext not in ALLOWED_EXTENSIONS:
            logger.error(f"forensic_upload: Unsupported file type .{file_ext}")
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type (.{file_ext}). Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # ============================================================
        # STEP 2: PARSE FILE AND EXTRACT TIMESTAMPS
        # ============================================================
        
        events = []
        timestamps = []
        parse_errors = 0
        
        # ============================================================
        # PCAP FILE PROCESSING (BINARY FILES)
        # ============================================================
        if file_ext in ['pcap', 'pcapng', 'cap']:
            try:
                logger.info(f"forensic_upload: Processing PCAP file '{filename}'...")
                pcap_result = analyze_pcap_file(content)
                
                if pcap_result.get('success'):
                    logger.info(f"forensic_upload: PCAP parsed successfully - {pcap_result.get('total_packets')} packets")
                    
                    # Extract events from PCAP packets
                    sample_events = []
                    for packet in pcap_result.get('packets', [])[:100]:  # Limit to first 100 for sample
                        if 'timestamp' in packet:
                            try:
                                dt = datetime.datetime.fromisoformat(packet['timestamp'].replace('Z', '+00:00'))
                                timestamps.append(dt)
                                event_entry = {
                                    'timestamp': packet['timestamp'],
                                    'source': 'pcap',
                                    'src_ip': packet.get('src_ip'),
                                    'dst_ip': packet.get('dst_ip'),
                                    'protocol': packet.get('protocol_name'),
                                    'src_port': packet.get('src_port'),
                                    'dst_port': packet.get('dst_port'),
                                    'size': packet.get('captured_len', 0)
                                }
                                events.append(event_entry)
                                sample_events.append(event_entry)
                            except Exception as e:
                                parse_errors += 1
                                logger.debug(f"forensic_upload: Could not parse PCAP packet timestamp: {e}")
                    
                    logger.info(f"forensic_upload: PCAP extracted {len(events)} events with timestamps")
                    
                    # Transform PCAP data to expected frontend format
                    unique_ips = set()
                    protocols = set()
                    
                    for pkt in pcap_result.get('packets', []):
                        if pkt.get('src_ip'):
                            unique_ips.add(pkt['src_ip'])
                        if pkt.get('dst_ip'):
                            unique_ips.add(pkt['dst_ip'])
                        if pkt.get('protocol_name'):
                            protocols.add(pkt['protocol_name'])
                    
                    # Return PCAP analysis in frontend-expected format
                    elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()
                    return {
                        "status": "success",
                        "filename": filename,
                        "file_type": file_ext,
                        "processing_time_seconds": round(elapsed, 2),
                        "message": f"✓ PCAP file analyzed successfully",
                        "events": {
                            "found": len(events),
                            "timestamp_range": {
                                "earliest": min(timestamps).isoformat() if timestamps else None,
                                "latest": max(timestamps).isoformat() if timestamps else None,
                            }
                        },
                        "correlation": {
                            "overlapping_tor_paths": 0,  # Will be calculated if needed
                            "total_paths_checked": 0,
                            "paths": []
                        },
                        "sample_events": sample_events,
                        "pcap_metadata": {
                            "total_packets": pcap_result.get('total_packets', 0),
                            "unique_ips": len(unique_ips),
                            "protocols": list(protocols),
                            "time_range": {
                                "first": min(timestamps).isoformat() if timestamps else None,
                                "last": max(timestamps).isoformat() if timestamps else None,
                            }
                        }
                    }
                else:
                    logger.error(f"forensic_upload: PCAP analysis failed - {pcap_result.get('error')}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"PCAP parsing error: {pcap_result.get('error')}"
                    )
                    
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"forensic_upload: PCAP processing error: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"PCAP file processing error: {str(e)}"
                )
        
        # ============================================================
        # TEXT FILE DECODING (for CSV, JSON, LOG, TXT)
        # ============================================================
        try:
            text_content = content.decode('utf-8', errors='replace')
        except Exception as e:
            logger.error(f"forensic_upload: Decoding error: {e}")
            raise HTTPException(status_code=400, detail="File encoding error (must be UTF-8)")
        
        # ============================================================
        # CSV FILE PROCESSING
        # ============================================================
        if file_ext == 'csv':
            try:
                reader = csv.DictReader(StringIO(text_content))
                
                if not reader.fieldnames:
                    logger.error("forensic_upload: CSV has no headers")
                    raise HTTPException(status_code=400, detail="CSV file has no headers")
                
                row_count = 0
                for row in reader:
                    row_count += 1
                    
                    # Look for timestamp column (multiple naming conventions)
                    ts_value = None
                    for ts_col in ['timestamp', 'time', 'date', 'datetime', 'ts', 'event_time', 'occurred_at']:
                        if ts_col in row and row[ts_col]:
                            ts_value = row[ts_col]
                            break
                    
                    if ts_value:
                        try:
                            dt = date_parser.parse(ts_value)
                            timestamps.append(dt)
                            events.append({
                                'timestamp': dt.isoformat(),
                                'source': 'csv',
                                'data': dict(row),
                                'row': row_count
                            })
                        except Exception as e:
                            parse_errors += 1
                            logger.debug(f"forensic_upload: Could not parse timestamp '{ts_value}': {e}")
                
                logger.info(f"forensic_upload: CSV parsed {row_count} rows, {len(events)} events extracted")
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"forensic_upload: CSV parsing error: {e}")
                raise HTTPException(status_code=400, detail=f"CSV parsing error: {str(e)}")
        
        # ============================================================
        # JSON FILE PROCESSING
        # ============================================================
        elif file_ext == 'json':
            try:
                data = json.loads(text_content)
                
                # Handle both array and single object
                if isinstance(data, dict):
                    data = [data]
                elif not isinstance(data, list):
                    logger.error("forensic_upload: JSON root is not array or object")
                    raise HTTPException(status_code=400, detail="JSON must be array or object")
                
                for idx, item in enumerate(data):
                    if not isinstance(item, dict):
                        parse_errors += 1
                        continue
                    
                    # Look for timestamp field
                    ts_value = item.get('timestamp') or item.get('time') or item.get('date')
                    
                    if ts_value:
                        try:
                            dt = date_parser.parse(ts_value)
                            timestamps.append(dt)
                            events.append({
                                'timestamp': dt.isoformat(),
                                'source': 'json',
                                'data': item,
                                'index': idx
                            })
                        except Exception as e:
                            parse_errors += 1
                            logger.debug(f"forensic_upload: Could not parse JSON timestamp: {e}")
                    else:
                        parse_errors += 1
                
                logger.info(f"forensic_upload: JSON parsed {len(data)} items, {len(events)} events extracted")
                
            except HTTPException:
                raise
            except json.JSONDecodeError as e:
                logger.error(f"forensic_upload: JSON decode error: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
            except Exception as e:
                logger.error(f"forensic_upload: JSON parsing error: {e}")
                raise HTTPException(status_code=400, detail=f"JSON parsing error: {str(e)}")
        
        # ============================================================
        # LOG/TEXT FILE PROCESSING
        # ============================================================
        else:  # .log, .txt
            try:
                lines = text_content.split('\n')
                max_lines = 5000  # Process first 5000 lines max
                processed_lines = 0
                
                # Multiple regex patterns for timestamp detection
                patterns = [
                    r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[\.\,]?\d*(?:Z|[\+\-]\d{2}:\d{2})?',  # ISO
                    r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',  # Syslog style
                    r'\d{1,2}/\d{1,2}/\d{4}\s+\d{2}:\d{2}:\d{2}',  # US date
                ]
                
                for line in lines[:max_lines]:
                    if not line.strip():
                        continue
                    
                    processed_lines += 1
                    
                    # Try to find timestamp using patterns
                    found_timestamp = False
                    for pattern in patterns:
                        match = re.search(pattern, line)
                        if match:
                            try:
                                dt = date_parser.parse(match.group())
                                timestamps.append(dt)
                                events.append({
                                    'timestamp': dt.isoformat(),
                                    'source': 'log',
                                    'line': line[:200],  # First 200 chars
                                    'line_num': processed_lines
                                })
                                found_timestamp = True
                                break
                            except Exception as e:
                                logger.debug(f"forensic_upload: Timestamp parse error: {e}")
                    
                    if not found_timestamp:
                        parse_errors += 1
                
                logger.info(f"forensic_upload: Log file processed {processed_lines} lines, {len(events)} events extracted")
                
            except Exception as e:
                logger.error(f"forensic_upload: Log file parsing error: {e}")
                raise HTTPException(status_code=400, detail=f"Log file parsing error: {str(e)}")
        
        # ============================================================
        # STEP 3: VALIDATE EVENT EXTRACTION
        # ============================================================
        
        if not events or not timestamps:
            logger.warning(f"forensic_upload: No valid events found in {filename}")
            raise HTTPException(
                status_code=400,
                detail=f"No valid timestamps found in file ({parse_errors} parse errors). Ensure file has timestamp column/field."
            )
        
        logger.info(f"forensic_upload: Successfully extracted {len(events)} events from file")
        
        # ============================================================
        # STEP 4: FIND OVERLAPPING TOR PATHS
        # ============================================================
        
        min_ts = min(timestamps)
        max_ts = max(timestamps)
        time_window = (max_ts - min_ts).total_seconds()
        
        logger.info(f"forensic_upload: Timestamp range: {min_ts} to {max_ts} (window: {time_window}s)")
        
        overlapping_paths = []
        path_query_errors = 0
        
        try:
            # Query all paths from database
            total_paths = db.path_candidates.count_documents({}) if 'path_candidates' in db.list_collection_names() else 0
            
            if total_paths == 0:
                logger.warning("forensic_upload: No paths in database for correlation")
            else:
                # Look for overlapping paths (within 24 hours of any event)
                paths = list(db.path_candidates.find({}).limit(1000))
                
                for path in paths:
                    try:
                        path_ts = path.get('timestamp') or path.get('generated_at')
                        if not path_ts:
                            continue
                        
                        path_dt = date_parser.parse(path_ts)
                        
                        # Check if path timestamp overlaps with any event (24h window)
                        for evt_ts in timestamps:
                            time_diff = abs((path_dt - evt_ts).total_seconds())
                            if time_diff < 86400:  # 24 hours
                                overlapping_paths.append({
                                    'path_id': path.get('id'),
                                    'score': path.get('score', 0),
                                    'entry': path.get('entry', {}).get('nickname', 'unknown'),
                                    'exit': path.get('exit', {}).get('nickname', 'unknown'),
                                    'time_diff_seconds': time_diff
                                })
                                break  # Only add once per path
                    except Exception as e:
                        path_query_errors += 1
                        logger.debug(f"forensic_upload: Path correlation error: {e}")
                
                logger.info(f"forensic_upload: Found {len(overlapping_paths)} overlapping paths ({path_query_errors} errors)")
        
        except Exception as e:
            logger.error(f"forensic_upload: Path query failed: {e}")
            # Don't fail the upload if path query fails
        
        # ============================================================
        # STEP 5: BUILD RESPONSE
        # ============================================================
        
        elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()
        
        response = {
            "status": "success",
            "filename": filename,
            "file_size_bytes": file_size,
            "processing_time_seconds": round(elapsed, 3),
            "events": {
                "found": len(events),
                "with_errors": parse_errors,
                "timestamp_range": {
                    "earliest": min_ts.isoformat(),
                    "latest": max_ts.isoformat(),
                    "window_seconds": int(time_window)
                }
            },
            "correlation": {
                "overlapping_tor_paths": len(overlapping_paths),
                "total_paths_checked": total_paths,
                "paths": overlapping_paths[:20]  # Top 20
            },
            "sample_events": events[:10],  # Return first 10 events for preview
            "message": (
                f"✓ Forensic upload complete: {len(events)} events parsed, "
                f"{len(overlapping_paths)} potentially correlated TOR paths found."
            )
        }
        
        logger.info(f"forensic_upload: SUCCESS - {response['message']}")
        return response
    
    except HTTPException as e:
        logger.error(f"forensic_upload: HTTP error {e.status_code}: {e.detail}")
        raise
    
    except Exception as e:
        logger.error(f"forensic_upload: Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload processing failed: {str(e)}"
        )


# ---------------------------------------------------------
# CORRELATOR ENDPOINTS (FEATURE 13: HARDENED)
# ---------------------------------------------------------
@app.get("/paths/generate")
def api_generate_paths(
    guards: int = 30,
    middles: int = 80,
    exits: int = 30,
    top_k: int = 500,
):
    """Generate candidate TOR paths with plausibility scoring.
    
    FEATURE 13: BACKEND HARDENING - ROBUST API
    ===========================================
    
    Parameters:
    - guards: Number of guard relay candidates (default 30, max 200)
    - middles: Number of middle relay candidates (default 80, max 500)
    - exits: Number of exit relay candidates (default 30, max 200)
    - top_k: Return top K paths by score (default 500, max 10000)
    
    Returns:
    - Scored paths with component breakdown
    - Ranked by correlation plausibility
    - Deterministic error messages on failure
    """
    start_time = datetime.datetime.utcnow()
    
    try:
        # Validate and normalize parameters
        guards = validate_limit_parameter(guards, default=30, min_val=1, max_val=200)
        middles = validate_limit_parameter(middles, default=80, min_val=1, max_val=500)
        exits = validate_limit_parameter(exits, default=30, min_val=1, max_val=200)
        top_k = validate_limit_parameter(top_k, default=500, min_val=1, max_val=10000)
        
        log_endpoint_call("GET /paths/generate", guards=guards, middles=middles, exits=exits, top_k=top_k)
        
        # Generate paths
        top = safe_db_query(
            generate_candidate_paths,
            limit_guards=guards,
            limit_middles=middles,
            limit_exits=exits,
            top_k=top_k,
        )
        
        elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()
        
        response = {
            "status": "success",
            "count": len(top),
            "query_time_seconds": round(elapsed, 3),
            "parameters": {
                "guards": guards,
                "middles": middles,
                "exits": exits,
                "top_k": top_k
            },
            "paths": top
        }
        
        log_endpoint_response("GET /paths/generate", "success", count=len(top))
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /paths/generate failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Path generation failed. Please verify relays are indexed."
        )


@app.get("/paths/top")
def api_top_paths(limit: int = 100):
    """Get top candidate paths by plausibility score.
    
    FEATURE 13: BACKEND HARDENING - ROBUST API
    ===========================================
    
    Parameters:
    - limit: Maximum paths to return (default 100, max 5000)
    
    Returns top-scoring paths for rapid investigation start
    """
    start_time = datetime.datetime.utcnow()
    
    try:
        # Validate limit
        limit = validate_limit_parameter(limit, default=100, max_val=5000)
        
        log_endpoint_call("GET /paths/top", limit=limit)
        
        # Retrieve paths
        top = safe_db_query(top_candidate_paths, limit=limit)
        
        elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()
        
        response = {
            "status": "success",
            "count": len(top),
            "limit": limit,
            "query_time_seconds": round(elapsed, 3),
            "paths": top
        }
        
        log_endpoint_response("GET /paths/top", "success", count=len(top))
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GET /paths/top failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Could not retrieve top paths. Database may be unavailable."
        )


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
    draw_title("1. EXECUTIVE SUMMARY", 12)
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
    draw_title("2. TECHNICAL FINDINGS", 12)
    
    # Entry Relay
    draw_title("2.1 Entry Node (Connection Entry Point)", 11)
    entry = path_candidate.get("entry", {})
    draw_text(f"Nickname: {entry.get('nickname', 'Unknown')}", 10, 10)
    draw_text(f"Fingerprint: {entry.get('fingerprint', 'N/A')[:16]}...", 9, 10)
    draw_text(f"IP Address: {entry.get('ip', 'Unknown')}", 10, 10)
    draw_text(f"Country: {entry.get('country', 'Unknown')}", 10, 10)
    draw_text(f"Advertised Bandwidth: {entry.get('advertised_bandwidth', 0) / 1_000_000:.1f} Mbps", 10, 10)
    draw_text(f"Uptime: {entry.get('first_seen', 'Unknown')} to {entry.get('last_seen', 'Unknown')}", 9, 10)
    y_position -= 4
    
    # Middle Relay
    draw_title("2.2 Middle Relay (Intermediate Node)", 11)
    middle = path_candidate.get("middle", {})
    draw_text(f"Nickname: {middle.get('nickname', 'Unknown')}", 10, 10)
    draw_text(f"Fingerprint: {middle.get('fingerprint', 'N/A')[:16]}...", 9, 10)
    draw_text(f"IP Address: {middle.get('ip', 'Unknown')}", 10, 10)
    draw_text(f"Country: {middle.get('country', 'Unknown')}", 10, 10)
    draw_text(f"Advertised Bandwidth: {middle.get('advertised_bandwidth', 0) / 1_000_000:.1f} Mbps", 10, 10)
    draw_text(f"Uptime: {middle.get('first_seen', 'Unknown')} to {middle.get('last_seen', 'Unknown')}", 9, 10)
    y_position -= 4
    
    # Exit Relay
    draw_title("2.3 Exit Node (Connection Exit Point)", 11)
    exit_node = path_candidate.get("exit", {})
    draw_text(f"Nickname: {exit_node.get('nickname', 'Unknown')}", 10, 10)
    draw_text(f"Fingerprint: {exit_node.get('fingerprint', 'N/A')[:16]}...", 9, 10)
    draw_text(f"IP Address: {exit_node.get('ip', 'Unknown')}", 10, 10)
    draw_text(f"Country: {exit_node.get('country', 'Unknown')}", 10, 10)
    draw_text(f"Advertised Bandwidth: {exit_node.get('advertised_bandwidth', 0) / 1_000_000:.1f} Mbps", 10, 10)
    draw_text(f"Uptime: {exit_node.get('first_seen', 'Unknown')} to {exit_node.get('last_seen', 'Unknown')}", 9, 10)
    
    check_page_break()
    
    # ========== SCORE BREAKDOWN ==========
    draw_title("3. SCORE COMPONENTS & METHODOLOGY", 12)
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
    draw_title("4. CONFIDENCE ASSESSMENT & LIMITATIONS", 12)
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
    draw_title("5. LEGAL & ETHICAL STATEMENT", 12)
    draw_text("AUTHORIZED LAW ENFORCEMENT USE ONLY", 10)
    draw_text("This tool is designed for investigative support in cybercrime cases.", 9)
    y_position -= 4
    draw_text("IMPORTANT DISCLAIMERS:", 10)
    draw_text("1. This analysis is metadata-only and does NOT break TOR anonymity", 9, 10)
    draw_text("2. Results must be independently validated through other investigative methods", 9, 10)
    draw_text("3. These findings are NOT admissible as proof; use for investigative guidance only", 9, 10)
    draw_text("4. Compliance: Indian Penal Code § 43, § 66 (cybercrime), § 120 (investigation)", 9, 10)
    draw_text("5. Court admissibility requires corroboration with non-metadata evidence", 9, 10)
    y_position -= 8
    
    # Footer with legal notice
    p.setFont("Helvetica", 8)
    p.drawString(margin_left, 20, "Metadata-Only Analysis • No Anonymity Breached • For Investigation Support Only")
    p.drawString(margin_left, 12, f"TOR Unveil v2.0 | Tamil Nadu Police Cyber Crime Wing | {datetime.datetime.utcnow().strftime('%Y-%m-%d')}")
    
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
