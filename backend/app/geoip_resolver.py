# backend/app/geoip_resolver.py

from typing import Dict, Any
import requests

def get_geo(ip: str | None) -> Dict[str, Any]:
    """
    Resolve IP to geolocation using ip-api.com.
    Returns dict with {lat, lon, country}.
    On error, values are None.
    """
    if not ip:
        return {"lat": None, "lon": None, "country": None}

    try:
        r = requests.get(
            f"http://ip-api.com/json/{ip}?fields=status,lat,lon,countryCode",
            timeout=5,
        )
        if r.status_code == 200:
            js = r.json()
            if js.get("status") == "success":
                return {
                    "lat": js.get("lat"),
                    "lon": js.get("lon"),
                    "country": js.get("countryCode"),
                }
    except Exception:
        pass

    return {"lat": None, "lon": None, "country": None}
