# backend/app/fetcher.py

import os
import requests
from pymongo import MongoClient
import re
from typing import Optional
import logging
from datetime import datetime

from .risk_engine import compute_risk
from .geoip_resolver import get_geo

# Onionoo API endpoint
ONIONOO_SUMMARY = "https://onionoo.torproject.org/details"

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/torunveil")
client = MongoClient(MONGO_URL)
db = client["torunveil"]
relays_col = db["relays"]

# Regex to extract IPv4 even with port
IPV4_RE = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")

# Simple bad-IP intel (placeholder – you can expand/replace with file/db)
BAD_IPS = {
    "45.83.64.1",
    "185.220.101.1",
    "185.220.102.4",
    "199.249.230.70",
}


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
    """Return True if IP matches a known bad set (very small demo set)."""
    if not ip:
        return False
    return ip in BAD_IPS


# -----------------------------------------
# Normalization
# -----------------------------------------
def normalize_relay(raw: dict) -> dict:
    """Normalize a single Onionoo relay record + enrich with risk + geo."""
    # Handle compact Onionoo key mappings
    fp = raw.get("fingerprint") or raw.get("f")
    nickname = raw.get("nickname") or raw.get("n")
    or_addresses = raw.get("or_addresses") or raw.get("a") or []
    ip = extract_ipv4(or_addresses)

    # Country (either full or compact)
    country = raw.get("country") or raw.get("c")
    if isinstance(country, str):
        country = country.upper()

    # GeoIP (lat/lon + possible country from GeoIP)
    geo = get_geo(ip) if ip else {"lat": None, "lon": None, "country": None}
    if not country and geo.get("country"):
        country = geo["country"]

    # Flags or booleans
    flags = raw.get("flags") or []
    if not flags:
        # Infer from boolean compact flags
        if raw.get("e"):
            flags.append("Exit")
        if raw.get("g"):
            flags.append("Guard")
        if raw.get("r"):
            flags.append("Running")

    # Base normalized structure
    normalized = {
        "fingerprint": fp or "unknown",
        "nickname": nickname or "",
        "or_addresses": or_addresses,
        "ip": ip,
        "country": country or "UNKNOWN",
        "flags": flags,
        "is_exit": "Exit" in flags,
        "is_guard": "Guard" in flags,
        "running": "Running" in flags,
        "advertised_bandwidth": raw.get("advertised_bandwidth") or raw.get("b"),
        "first_seen": raw.get("first_seen"),
        "last_seen": raw.get("last_seen"),
        "hostnames": raw.get("hostnames") or [],
        "as": raw.get("as_name"),
    }

    # Risk engine expects these fields
    risk_score = compute_risk(normalized)
    normalized["risk_score"] = risk_score

    # Geo fields
    normalized["lat"] = geo.get("lat")
    normalized["lon"] = geo.get("lon")

    # Threat intel flag
    normalized["is_malicious"] = threat_intel(ip)

    return normalized


# -----------------------------------------
# Fetch + Store in MongoDB
# -----------------------------------------
logger = logging.getLogger("torunveil.fetcher")
logger.addHandler(logging.NullHandler())


# -----------------------------------------
# Fetch + Store in MongoDB (safer)
# -----------------------------------------
def fetch_and_store_relays():
    """Fetch Onionoo data and save normalized entries in MongoDB.

    Improvements made:
    - Add a fetch timestamp to each normalized relay ('fetched_at')
    - Use upserts (replace_one with upsert=True) so a failed fetch does not wipe DB
    - Log errors rather than raising, keep function safe for scheduled runs
    - Preserve deterministic risk scoring (compute_risk unchanged)
    """
    logger.info("[+] Fetching Tor relay data from Onionoo...")
    try:
        r = requests.get(ONIONOO_SUMMARY, timeout=120)
        r.raise_for_status()
        payload = r.json()
        relays = payload.get("relays") or payload.get("r") or []

        normalized = []
        for item in relays:
            try:
                nr = normalize_relay(item)
                # attach a fetch timestamp for forensic reproducibility
                nr["fetched_at"] = datetime.utcnow().isoformat() + "Z"
                normalized.append(nr)
            except Exception as e_item:
                # log and continue — bad item should not stop whole fetch
                logger.exception("Failed to normalize relay item: %s", e_item)

        # Upsert each normalized document by fingerprint. This avoids wiping the
        # entire collection if the fetch has a problem mid-flight.
        updated = 0
        for doc in normalized:
            try:
                fp = doc.get("fingerprint")
                if not fp:
                    # skip documents without fingerprint
                    logger.warning("Skipping doc without fingerprint: %s", doc)
                    continue
                relays_col.replace_one({"fingerprint": fp}, doc, upsert=True)
                updated += 1
            except Exception as e_up:
                logger.exception("Failed to upsert relay %s: %s", doc.get("fingerprint"), e_up)

        logger.info("[+] Upserted %d relays (normalized + risk + geo + intel).", updated)
        return updated
    except Exception as e:
        # On a full-fetch failure, do NOT delete existing DB contents. Log and return 0.
        logger.exception("[-] Error fetching/storing relays: %s", e)
        return 0
