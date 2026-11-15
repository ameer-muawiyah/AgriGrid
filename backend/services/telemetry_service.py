"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    telemetry_service.py
Module:  Environmental Telemetry & Cache Service
Version: 2.0  (Increment 2 — Intelligence Layer)
Author:  Hasnain Hamza (Core Backend Engineer) & Bareera Noor (Database Administrator)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §2.1, §4.4, §13 (Decision 4), Sequence Diagram 8,
         API Contracts Delta v1.2 §7.1, SRS (FR-TEL-*, FR-CCH-*)

Purpose
-------
External environmental telemetry fetching (OpenWeatherMap & SoilGrids) with a
mandatory 6-hour SQLite caching layer (telemetry_cache table) and deterministic
offline fallback fixtures. Never raises unhandled exceptions and never produces 500s.
"""

from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import sqlite3
from typing import Any, Tuple

from flask import current_app, g, has_app_context
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = str(BASE_DIR / "database" / "agrigrid.db")
FIXTURES_DIR = str(BASE_DIR / "tests" / "fixtures")


def _get_connection(caller_conn: sqlite3.Connection | None = None) -> Tuple[sqlite3.Connection, bool]:
    """
    Obtain a database connection. Returns (conn, should_close).
    Reuses caller_conn or Flask g.db when available, otherwise connects to DB_PATH.
    """
    if caller_conn is not None:
        return caller_conn, False

    if has_app_context():
        if "db" in g:
            return g.db, False
        db_path = current_app.config.get("DB_PATH", os.environ.get("AGRIGRID_DB_PATH", DEFAULT_DB_PATH))
    else:
        db_path = os.environ.get("AGRIGRID_DB_PATH", DEFAULT_DB_PATH)

    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn, True


def cache_key(telemetry_type: str, lat: float, lon: float) -> str:
    """
    Format deterministic cache key: <telemetry_type>:<lat:.4f>:<lon:.4f>.
    Per FR-CCH-002.
    """
    return f"{telemetry_type}:{float(lat):.4f}:{float(lon):.4f}"


def purge_expired_cache(conn: sqlite3.Connection | None = None) -> int:
    """
    Purge expired records from telemetry_cache.
    DELETE FROM telemetry_cache WHERE expires_at <= CURRENT_TIMESTAMP.
    Exception-safe for callers (e.g., app startup).
    """
    try:
        db, should_close = _get_connection(conn)
        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM telemetry_cache WHERE expires_at <= CURRENT_TIMESTAMP")
            purged = cursor.rowcount
            db.commit()
            return purged
        finally:
            if should_close:
                db.close()
    except Exception:
        return 0


def _load_weather_fixture() -> dict[str, Any]:
    """Load weather fixture and stamp current UTC ISO-8601 timestamp."""
    fpath = os.path.join(FIXTURES_DIR, "weather_punjab.json")
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return data


def _load_soil_fixture() -> dict[str, Any]:
    """Load soil fixture and stamp current UTC ISO-8601 timestamp."""
    fpath = os.path.join(FIXTURES_DIR, "soil_punjab.json")
    with open(fpath, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["timestamp"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return data


def _resolve_fresh_weather(lat: float, lon: float) -> Tuple[dict[str, Any], str]:
    """
    Resolve fresh weather data via live OpenWeatherMap API or deterministic offline fixture.
    Normalizes response per package PD-4.
    Never raises an exception.
    """
    is_offline = (os.environ.get("AGRIGRID_OFFLINE_MODE") == "1")
    api_key = os.environ.get("OPENWEATHER_API_KEY", "").strip()

    if is_offline or not api_key:
        return _load_weather_fixture(), "offline_fixture"

    try:
        url = "https://api.openweathermap.org/data/2.5/forecast"
        resp = requests.get(
            url,
            params={"lat": lat, "lon": lon, "appid": api_key, "units": "metric"},
            timeout=5,
        )
        if resp.status_code != 200:
            return _load_weather_fixture(), "offline_fixture"

        raw = resp.json()
        items = raw.get("list", [])
        if not items:
            return _load_weather_fixture(), "offline_fixture"

        temps = [item["main"]["temp"] for item in items if "main" in item and "temp" in item["main"]]
        humidities = [item["main"]["humidity"] for item in items if "main" in item and "humidity" in item["main"]]
        if not temps or not humidities:
            return _load_weather_fixture(), "offline_fixture"

        temp_c = round(sum(temps) / len(temps), 1)
        humidity_pct = round(sum(humidities) / len(humidities), 1)

        rain_sum = 0.0
        for item in items:
            rain_obj = item.get("rain")
            if isinstance(rain_obj, dict):
                rain_sum += rain_obj.get("3h", 0.0)
        cumulative_precip = round(rain_sum, 1)

        clouds = [item.get("clouds", {}).get("all", 0) for item in items if "clouds" in item]
        avg_clouds = sum(clouds) / len(clouds) if clouds else 0.0
        solar_index = round(max(0.0, min(1.0, 1.0 - (avg_clouds / 100.0) * 0.6)), 2)

        descriptions = []
        for item in items:
            for w in item.get("weather", []):
                desc = w.get("description")
                if desc:
                    descriptions.append(desc.capitalize())

        modal_desc = Counter(descriptions).most_common(1)[0][0] if descriptions else "Clear sky"

        data = {
            "temperature_c": temp_c,
            "relative_humidity_pct": humidity_pct,
            "cumulative_precipitation_14d_mm": cumulative_precip,
            "solar_radiation_index": solar_index,
            "description": modal_desc,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        return data, "live_api"
    except Exception:
        return _load_weather_fixture(), "offline_fixture"


def _resolve_fresh_soil(lat: float, lon: float) -> Tuple[dict[str, Any], str]:
    """
    Resolve fresh soil data via live SoilGrids REST API or deterministic offline fixture.
    Converts and normalizes response per package PD-4.
    Never raises an exception.
    """
    is_offline = (os.environ.get("AGRIGRID_OFFLINE_MODE") == "1")
    if is_offline:
        return _load_soil_fixture(), "offline_fixture"

    try:
        url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
        params = {
            "lat": lat,
            "lon": lon,
            "property": ["phh2o", "soc", "wv0033", "clay", "sand", "silt"],
            "depth": "0-5cm",
            "value": "mean",
        }
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code != 200:
            return _load_soil_fixture(), "offline_fixture"

        raw = resp.json()
        layers = raw.get("properties", {}).get("layers", [])
        if not layers:
            return _load_soil_fixture(), "offline_fixture"

        prop_values: dict[str, Any] = {}
        for layer in layers:
            name = layer.get("name")
            for d in layer.get("depths", []):
                if d.get("label") == "0-5cm":
                    vals = d.get("values", {})
                    prop_values[name] = vals.get("mean")

        ph_raw = prop_values.get("phh2o")
        soil_ph = round(ph_raw / 10.0, 1) if ph_raw is not None else 7.4

        soc_raw = prop_values.get("soc")
        soc = round(soc_raw / 10.0, 1) if soc_raw is not None else 11.2

        wv_raw = prop_values.get("wv0033")
        topsoil_moisture = round(wv_raw / 10.0, 1) if wv_raw is not None else 24.5

        clay_raw = prop_values.get("clay")
        sand_raw = prop_values.get("sand")
        silt_raw = prop_values.get("silt")

        clay = clay_raw / 10.0 if clay_raw is not None else 30.0
        sand = sand_raw / 10.0 if sand_raw is not None else 35.0
        silt = silt_raw / 10.0 if silt_raw is not None else 35.0

        if clay >= 40.0:
            texture = "Clay"
        elif clay >= 27.0 and sand <= 45.0:
            texture = "Clay Loam"
        elif sand >= 70.0:
            texture = "Sandy Loam"
        elif silt >= 80.0:
            texture = "Silt Loam"
        else:
            texture = "Loam"

        data = {
            "topsoil_moisture_vol_pct": topsoil_moisture,
            "soil_organic_carbon_g_per_kg": soc,
            "soil_ph": soil_ph,
            "soil_texture_class": texture,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        return data, "live_api"
    except Exception:
        return _load_soil_fixture(), "offline_fixture"


def fetch_weather(lat: float, lon: float, conn: sqlite3.Connection | None = None) -> Tuple[dict[str, Any], str]:
    """
    Fetch weather telemetry for (lat, lon) with 6-hour SQLite cache and fallback.
    Returns (data_dict, source) where source is 'live_api', 'cache', or 'offline_fixture'.
    """
    lat_f = float(lat)
    lon_f = float(lon)
    ckey = cache_key("weather", lat_f, lon_f)

    db, should_close = _get_connection(conn)
    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT payload_json FROM telemetry_cache WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP",
            (ckey,),
        )
        row = cursor.fetchone()
        if row:
            payload = json.loads(row["payload_json"] if isinstance(row, sqlite3.Row) else row[0])
            return payload, "cache"

        # Cache miss / expired: resolve fresh
        data, source = _resolve_fresh_weather(lat_f, lon_f)

        cursor.execute(
            """
            INSERT OR REPLACE INTO telemetry_cache
                (cache_key, provider, latitude, longitude, payload_json, expires_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', '+6 hours'))
            """,
            (ckey, "OpenWeatherMap", lat_f, lon_f, json.dumps(data)),
        )
        db.commit()
        return data, source
    finally:
        if should_close:
            db.close()


def fetch_soil(lat: float, lon: float, conn: sqlite3.Connection | None = None) -> Tuple[dict[str, Any], str]:
    """
    Fetch soil telemetry for (lat, lon) with 6-hour SQLite cache and fallback.
    Returns (data_dict, source) where source is 'live_api', 'cache', or 'offline_fixture'.
    """
    lat_f = float(lat)
    lon_f = float(lon)
    ckey = cache_key("soil", lat_f, lon_f)

    db, should_close = _get_connection(conn)
    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT payload_json FROM telemetry_cache WHERE cache_key = ? AND expires_at > CURRENT_TIMESTAMP",
            (ckey,),
        )
        row = cursor.fetchone()
        if row:
            payload = json.loads(row["payload_json"] if isinstance(row, sqlite3.Row) else row[0])
            return payload, "cache"

        # Cache miss / expired: resolve fresh
        data, source = _resolve_fresh_soil(lat_f, lon_f)

        cursor.execute(
            """
            INSERT OR REPLACE INTO telemetry_cache
                (cache_key, provider, latitude, longitude, payload_json, expires_at)
            VALUES (?, ?, ?, ?, ?, datetime('now', '+6 hours'))
            """,
            (ckey, "SoilGrids", lat_f, lon_f, json.dumps(data)),
        )
        db.commit()
        return data, source
    finally:
        if should_close:
            db.close()
