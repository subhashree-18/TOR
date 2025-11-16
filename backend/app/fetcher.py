import os
import requests
from pymongo import MongoClient
import re
from typing import Optional

# Onionoo API endpoint
ONIONOO_SUMMARY = "https://onionoo.torproject.org/details"

# MongoDB connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/torunveil")
client = MongoClient(MONGO_URL)
db = client["torunveil"]
relays_col = db["relays"]

# Regex to extract IPv4 even with port
IPV4_RE = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")

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

def geoip_country_fallback_http(ip: str) -> Optional[str]:
    """Use ip-api.com to enrich country (fallback)."""
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}?fields=countryCode", timeout=6)
        if r.status_code == 200:
            js = r.json()
            return js.get("countryCode")
    except Exception:
        pass
    return None

def normalize_relay(raw: dict) -> dict:
    """Normalize a single Onionoo relay record."""
    # Handle compact Onionoo key mappings
    fp = raw.get("fingerprint") or raw.get("f")
    nickname = raw.get("nickname") or raw.get("n")
    or_addresses = raw.get("or_addresses") or raw.get("a") or []
    ip = extract_ipv4(or_addresses)

    # Country (either full or compact)
    country = raw.get("country") or raw.get("c")
    if isinstance(country, str):
        country = country.upper()
    if not country and ip:
        country = geoip_country_fallback_http(ip)

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

    return {
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

def fetch_and_store_relays():
    """Fetch Onionoo data and save normalized entries in MongoDB."""
    print("[+] Fetching Tor relay data from Onionoo...")
    try:
        r = requests.get(ONIONOO_SUMMARY, timeout=20)
        r.raise_for_status()
        payload = r.json()
        relays = payload.get("relays") or payload.get("r") or []

        normalized = [normalize_relay(item) for item in relays]

        relays_col.delete_many({})
        if normalized:
            relays_col.insert_many(normalized)
        print(f"[+] Stored {len(normalized)} relays (normalized).")
        return len(normalized)
    except Exception as e:
        print("[-] Error fetching/storing relays:", e)
        return 0
