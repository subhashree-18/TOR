# backend/app/fetcher.py
# FEATURE 10 & 11: RELAY FETCH LIMIT INCREASE + TOR DATA COLLECTION ENHANCEMENT

import os
import requests
from pymongo import ReplaceOne
import re
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
import time

from .database import get_db
from .risk_engine import compute_risk
from .geoip_resolver import get_geo

# Onionoo API endpoint
ONIONOO_SUMMARY = "https://onionoo.torproject.org/details"
ONIONOO_TIMEOUT = 120  # seconds

# MongoDB connection
db = get_db()
relays_col = db["relays"]

# Regex to extract IPv4 even with port
IPV4_RE = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")

# Enhanced bad-IP intel (expanded threat list)
BAD_IPS = {
    "45.83.64.1",
    "185.220.101.1",
    "185.220.102.4",
    "199.249.230.70",
    "45.33.32.156",
    "31.185.104.19",
    "87.118.96.89",
}

# Configure logging
logger = logging.getLogger("torunveil.fetcher")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# -----------------------------------------
# Utility helpers
# -----------------------------------------
def extract_ipv4(or_addresses):
    """Extract first IPv4 address from OR addresses."""
    if not or_addresses:
        return None
    if isinstance(or_addresses, str):
        or_addresses = [or_addresses]
    for addr in or_addresses:
        match = IPV4_RE.search(addr)
        if match:
            return match.group(1)
    return None


def threat_intel(ip: Optional[str]) -> bool:
    """Return True if IP matches a known bad set."""
    if not ip:
        return False
    return ip in BAD_IPS


# -----------------------------------------
# Normalization (Enhanced for Feature 11)
# -----------------------------------------
def normalize_relay(raw: dict) -> dict:
    """Normalize a single Onionoo relay record + enrich with risk + geo.
    
    FEATURE 11: ENHANCED METADATA ENRICHMENT
    ========================================
    - Better error handling for missing fields
    - Improved geo resolution
    - Enhanced risk scoring
    - Metadata stability
    """
    try:
        # Handle compact Onionoo key mappings
        fp = raw.get("fingerprint") or raw.get("f")
        nickname = raw.get("nickname") or raw.get("n") or "unnamed"
        or_addresses = raw.get("or_addresses") or raw.get("a") or []
        ip = extract_ipv4(or_addresses)

        # Country (either full or compact)
        country = raw.get("country") or raw.get("c")
        if isinstance(country, str):
            country = country.upper()
        else:
            country = None

        # GeoIP (lat/lon + possible country from GeoIP) - with fallback
        geo = {}
        if ip:
            try:
                geo = get_geo(ip) or {}
            except Exception as e:
                logger.debug(f"GeoIP lookup failed for {ip}: {e}")
                geo = {}
        
        if not country and geo.get("country"):
            country = geo.get("country")
        
        if not country:
            country = "UNKNOWN"

        # Flags or booleans - robust parsing
        flags = raw.get("flags") or []
        if not flags:
            # Infer from boolean compact flags
            flags = []
            if raw.get("e"):
                flags.append("Exit")
            if raw.get("g"):
                flags.append("Guard")
            if raw.get("r"):
                flags.append("Running")
            if raw.get("s"):
                flags.append("Stable")
            if raw.get("v"):
                flags.append("Valid")

        # Advertised bandwidth with safety checks
        try:
            bw = int(raw.get("advertised_bandwidth") or raw.get("b") or 0)
            advertised_bandwidth = max(0, bw)
        except (ValueError, TypeError):
            advertised_bandwidth = 0

        # AS name with safety
        as_name = raw.get("as_name") or raw.get("as") or ""
        if not isinstance(as_name, str):
            as_name = str(as_name)

        # Base normalized structure
        normalized = {
            "fingerprint": fp or "unknown",
            "nickname": str(nickname) if nickname else "unnamed",
            "or_addresses": or_addresses if isinstance(or_addresses, list) else [],
            "ip": ip,
            "country": country,
            "flags": flags,
            "is_exit": "Exit" in flags,
            "is_guard": "Guard" in flags,
            "running": "Running" in flags,
            "advertised_bandwidth": advertised_bandwidth,
            "first_seen": raw.get("first_seen"),
            "last_seen": raw.get("last_seen"),
            "hostnames": raw.get("hostnames") or [],
            "as": as_name,
        }

        # Risk engine expects these fields
        try:
            risk_score = compute_risk(normalized)
            normalized["risk_score"] = risk_score
        except Exception as e:
            logger.warning(f"Risk scoring failed for {fp}: {e}")
            normalized["risk_score"] = 0

        # Geo fields with fallback
        normalized["lat"] = geo.get("lat")
        normalized["lon"] = geo.get("lon")

        # Threat intel flag
        normalized["is_malicious"] = threat_intel(ip)
        
        # Data quality indicator
        normalized["data_quality"] = "good" if (ip and country != "UNKNOWN") else "partial"

        return normalized
        
    except Exception as e:
        logger.error(f"Failed to normalize relay: {e}")
        raise


# -----------------------------------------
# Feature 10: Fetch + Store with Batching
# -----------------------------------------
def fetch_and_store_relays(batch_size: int = 100) -> int:
    """Fetch Onionoo data and save normalized entries in MongoDB.

    FEATURE 10: RELAY FETCH LIMIT INCREASE (5000+)
    ==============================================
    
    Improvements:
    - Fetch all available relays (now supports 5000+)
    - Batch upsert operations (performance optimization)
    - Add fetch timestamp to each relay
    - Use upserts (no data loss on partial failures)
    - Comprehensive error handling
    - Logging for monitoring
    - Deterministic risk scoring
    
    Parameters:
    - batch_size: Number of relays to batch upsert (default 100)
    
    Returns:
    - Number of relays successfully stored
    """
    start_time = time.time()
    logger.info("=" * 70)
    logger.info("[+] FEATURE 10: Starting TOR relay fetch from Onionoo...")
    logger.info(f"[+] Onionoo endpoint: {ONIONOO_SUMMARY}")
    logger.info(f"[+] Batch size: {batch_size}")
    logger.info("=" * 70)
    
    try:
        # Fetch relay data from Onionoo
        logger.info("[*] Requesting relay details from Onionoo...")
        r = requests.get(ONIONOO_SUMMARY, timeout=ONIONOO_TIMEOUT)
        r.raise_for_status()
        payload = r.json()
        relays = payload.get("relays") or payload.get("r") or []
        
        logger.info(f"[+] Received {len(relays)} relays from Onionoo")
        
        if not relays:
            logger.warning("[-] No relays returned from Onionoo")
            return 0

        # Normalize all relays with error resilience
        normalized = []
        normalization_errors = 0
        
        logger.info("[*] Normalizing relay metadata...")
        for idx, item in enumerate(relays):
            try:
                nr = normalize_relay(item)
                # Attach fetch timestamp for forensic reproducibility
                nr["fetched_at"] = datetime.utcnow().isoformat() + "Z"
                normalized.append(nr)
                
                # Progress indicator every 500 relays
                if (idx + 1) % 500 == 0:
                    logger.info(f"[*] Normalized {idx + 1}/{len(relays)} relays...")
                    
            except Exception as e_item:
                normalization_errors += 1
                logger.debug(f"[-] Failed to normalize relay #{idx}: {e_item}")
                continue
        
        logger.info(f"[+] Normalized {len(normalized)} relays ({normalization_errors} errors)")

        # Batch upsert operations for efficiency
        # This prevents data loss on partial failures
        logger.info(f"[*] Upserting to MongoDB in batches of {batch_size}...")
        updated = 0
        upsert_errors = 0
        
        for batch_idx in range(0, len(normalized), batch_size):
            batch = normalized[batch_idx:batch_idx + batch_size]
            batch_start = batch_idx + 1
            batch_end = min(batch_idx + batch_size, len(normalized))
            
            try:
                # Use bulk operations for better performance
                operations = []
                valid_count = 0
                
                for doc in batch:
                    fp = doc.get("fingerprint")
                    if not fp or fp == "unknown":
                        logger.warning(f"[-] Skipping relay without valid fingerprint")
                        continue
                    
                    # Replace if exists, insert if not
                    operations.append(ReplaceOne(
                        {"fingerprint": fp},
                        doc,
                        upsert=True
                    ))
                    valid_count += 1
                
                if operations:
                    result = relays_col.bulk_write(operations, ordered=False)
                    batch_upserted = len(result.upserted_ids) + result.modified_count
                    updated += batch_upserted
                    
                    logger.info(f"[+] Batch {batch_start}-{batch_end}: {batch_upserted} upserted")
                    
            except Exception as e_batch:
                upsert_errors += 1
                logger.error(f"[-] Batch {batch_start}-{batch_end} failed: {e_batch}")
                continue

        # Final statistics
        elapsed = time.time() - start_time
        logger.info("=" * 70)
        logger.info(f"[+] FETCH COMPLETE")
        logger.info(f"[+] Total relays processed: {len(relays)}")
        logger.info(f"[+] Successfully normalized: {len(normalized)}")
        logger.info(f"[+] Successfully upserted: {updated}")
        logger.info(f"[+] Normalization errors: {normalization_errors}")
        logger.info(f"[+] Upsert errors: {upsert_errors}")
        logger.info(f"[+] Total time: {elapsed:.2f} seconds")
        if elapsed > 0:
            logger.info(f"[+] Average: {len(relays) / elapsed:.0f} relays/second")
        logger.info("=" * 70)
        
        return updated
        
    except requests.exceptions.Timeout:
        logger.error(f"[-] Timeout connecting to Onionoo (>{ONIONOO_TIMEOUT}s)")
        return 0
    except requests.exceptions.ConnectionError as e:
        logger.error(f"[-] Connection error: {e}")
        return 0
    except requests.exceptions.HTTPError as e:
        logger.error(f"[-] HTTP error: {e.response.status_code}")
        return 0
    except Exception as e:
        # On full-fetch failure, do NOT delete existing DB contents
        logger.exception(f"[-] Unexpected error fetching/storing relays: {e}")
        return 0
