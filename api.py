"""
api.py
──────
Handles all external data fetching (WAQI API) and
persistent lag buffer storage (JSON on disk).

Functions:
  fetch_waqi()     → hits WAQI geo-lookup endpoint, returns live reading
  load_lag_store() → loads lag_history.json from disk
  save_lag_store() → writes lag_history.json to disk
  push_reading()   → prepends a new reading and keeps only last 6
"""

import json
import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")  # UTC+5:30

def now_ist():
    """Current time in Indian Standard Time (IST = UTC+5:30)."""
    return datetime.datetime.now(IST).replace(tzinfo=None)
import requests

from config import LAG_FILE

# LAG_FILE is resolved in config.py via Path(__file__).resolve().parent


# ── WAQI API ───────────────────────────────────────────────────────────────
def fetch_waqi(lat: float, lon: float, api_key: str):
    """
    Fetch live AQI + pollutant + weather data from WAQI.

    Uses geo:lat;lon endpoint (NOT hardcoded station tokens) so we always
    hit the nearest real CPCB-verified monitoring station for given coordinates.

    Returns:
        (reading_dict, None)  on success
        (None, error_string)  on failure

    reading_dict keys:
        aqi, pm25, pm10, no2, so2, co, o3,
        temperature, humidity, wind_speed,
        timestamp, _api_station (debug only)
    """
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/?token={api_key}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()

        if data.get("status") != "ok":
            return None, str(data.get("data", "Unknown WAQI error"))

        d    = data["data"]
        iaqi = d.get("iaqi", {})

        def g(k):
            """Safely extract a value from iaqi dict."""
            v = iaqi.get(k, {}).get("v")
            return float(v) if v is not None else float("nan")

        # data["aqi"] is the Indian AQI value for CPCB-sourced stations
        try:
            aqi_val = float(d.get("aqi"))
        except (TypeError, ValueError):
            aqi_val = float("nan")

        return {
            "aqi":          aqi_val,
            "pm25":         g("pm25"),
            "pm10":         g("pm10"),
            "no2":          g("no2"),
            "so2":          g("so2"),
            "co":           g("co"),
            "o3":           g("o3"),
            "temperature":  g("t"),
            "humidity":     g("h"),
            "wind_speed":   g("w"),
            "timestamp":    now_ist().isoformat(),
            "_api_station": d.get("city", {}).get("name", "unknown"),
        }, None

    except Exception as e:
        return None, str(e)


def station_names_match(app_name: str, api_name: str) -> bool:
    """
    Smart keyword-overlap check between the app's station name and
    the name WAQI returns. Ignores word order and common filler words.

    Example:
        app_name = 'Ghaziabad Vasundhara'
        api_name = 'Vasundhara, Ghaziabad, India'
        → True  (both share 'vasundhara' and 'ghaziabad')
    """
    ignore = {"delhi", "india", "sec", "phase", "new", "old", "town", "sector"}
    app_kw = {w for w in app_name.lower().replace(",", "").split()
              if w not in ignore and len(w) > 2}
    api_kw = {w for w in api_name.lower().replace(",", "").split()
              if w not in ignore and len(w) > 2}
    return bool(app_kw & api_kw)


# ── Persistent Lag Store ───────────────────────────────────────────────────
def load_lag_store() -> dict:
    """
    Load lag_history.json from disk.
    Returns empty dict if file doesn't exist yet.

    Structure: { "station_name": [ reading_dict, ... ] }
               newest reading at index 0 (= lag1)
    """
    if LAG_FILE.exists():
        with open(LAG_FILE) as f:
            return json.load(f)
    return {}


def save_lag_store(store: dict):
    """Write the full lag store back to lag_history.json."""
    with open(LAG_FILE, "w") as f:
        json.dump(store, f, indent=2, default=str)


def push_reading(store: dict, station_key: str, reading: dict) -> dict:
    """
    Prepend a new reading for a station and trim to max 6.
    Index 0 = lag1 (most recent), index 5 = lag6 (oldest).
    Automatically saves to disk.
    """
    history = store.get(station_key, [])
    history.insert(0, reading)
    store[station_key] = history[:6]
    save_lag_store(store)
    return store
