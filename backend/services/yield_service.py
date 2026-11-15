"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    yield_service.py
Module:  Predictive Yield Engine Service Layer
Version: 2.0  (Increment 2 — Intelligence Layer)
Author:  Hasnain Hamza (Core Backend Engineer) & Bareera Noor (Database Administrator)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §4.2, §13 (Decision 5), Sequence Diagram 9,
         API Contracts Delta v1.2 §7.2, SRS (FR-YLD-*)

Purpose
-------
Deterministic, explainable agronomic yield estimation combining crop parameters,
growth stages, and environmental telemetry (weather + soil edaphic factors).
"""

from datetime import date, datetime, timedelta
import os
from pathlib import Path
import sqlite3
from typing import Any

from flask import current_app, g, has_app_context

from services.telemetry_service import (
    fetch_weather,
    fetch_soil,
    _load_weather_fixture,
    _load_soil_fixture,
)

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = str(BASE_DIR / "database" / "agrigrid.db")

CROP_CONSTANTS = {
    "Wheat":     {"y_base": 1400,  "t_base": 5,  "season_days": 150},
    "Rice":      {"y_base": 2600,  "t_base": 10, "season_days": 140},
    "Tomato":    {"y_base": 8000,  "t_base": 10, "season_days": 120},
    "Potato":    {"y_base": 9000,  "t_base": 7,  "season_days": 110},
    "Cotton":    {"y_base": 1100,  "t_base": 12, "season_days": 180},
    "Maize":     {"y_base": 2800,  "t_base": 10, "season_days": 120},
    "Sugarcane": {"y_base": 32000, "t_base": 12, "season_days": 330},
    "Other":     {"y_base": 1500,  "t_base": 8,  "season_days": 120},
}


class YieldError(Exception):
    """Base exception for yield service errors."""
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ListingNotFound(YieldError):
    """Unified 404 for missing or non-owned listings (anti-enumeration doctrine)."""
    def __init__(self):
        super().__init__("Listing not found.", 404)


def _get_connection(caller_conn: sqlite3.Connection | None = None) -> tuple[sqlite3.Connection, bool]:
    """Obtain a database connection. Returns (conn, should_close)."""
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


def _clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamp numeric value between min_val and max_val."""
    return max(min_val, min(max_val, val))


def generate_yield_forecast(
    listing_id: int,
    caller_farmer_id: int,
    conn: sqlite3.Connection | None = None,
) -> dict[str, Any]:
    """
    Generate and persist predictive yield forecast for a farmer's crop listing (FR-YLD-001..006).
    """
    db, should_close = _get_connection(conn)
    try:
        cursor = db.cursor()

        # Step 1: Listing lookup & ownership verification
        cursor.execute(
            """
            SELECT id, farmer_id, crop_name, acreage, planting_date, gps_latitude, gps_longitude
              FROM listings
             WHERE id = ? AND is_deleted = 0
            """,
            (listing_id,),
        )
        listing = cursor.fetchone()

        # Anti-enumeration doctrine: Missing OR non-owner -> uniform 404 (PD-8: no status check)
        if not listing or listing["farmer_id"] != caller_farmer_id:
            raise ListingNotFound()

        crop_name = listing["crop_name"]
        acreage = float(listing["acreage"])
        planting_date_raw = listing["planting_date"]
        if isinstance(planting_date_raw, str):
            p_date = datetime.strptime(planting_date_raw[:10], "%Y-%m-%d").date()
        else:
            p_date = planting_date_raw

        # Step 2: Telemetry resolution
        has_gps = (listing["gps_latitude"] is not None and listing["gps_longitude"] is not None)
        if has_gps:
            weather_data, weather_source = fetch_weather(
                float(listing["gps_latitude"]),
                float(listing["gps_longitude"]),
                conn=db,
            )
            soil_data, soil_source = fetch_soil(
                float(listing["gps_latitude"]),
                float(listing["gps_longitude"]),
                conn=db,
            )
        else:
            # If either GPS value is NULL: load fixtures directly, no cache interaction (PD-10)
            weather_data = _load_weather_fixture()
            weather_source = "offline_fixture"
            soil_data = _load_soil_fixture()
            soil_source = "offline_fixture"

        # Step 3: Agronomic formula core computation (PD-5, PD-6, PD-7)
        constants = CROP_CONSTANTS.get(crop_name, CROP_CONSTANTS["Other"])
        y_base = constants["y_base"]
        t_base = constants["t_base"]
        season_days = constants["season_days"]

        # 3a. GDD accumulation factor
        today = date.today()
        days_elapsed = (today - p_date).days
        progress = _clamp(days_elapsed, 0, season_days) / float(season_days)

        temp_c = float(weather_data.get("temperature_c", 25.0))
        if temp_c <= t_base:
            f_gdd = 0.90
        else:
            f_gdd = 0.90 + 0.20 * progress

        # 3b. Rainfall deviation factor (14-day cumulative precipitation)
        rain_mm = float(weather_data.get("cumulative_precipitation_14d_mm", 0.0))
        if rain_mm < 5.0:
            f_rain = 0.90
        elif 5.0 <= rain_mm < 10.0:
            f_rain = 0.97
        elif 10.0 <= rain_mm <= 20.0:
            f_rain = 1.05
        elif 20.0 < rain_mm <= 35.0:
            f_rain = 1.00
        else:
            f_rain = 0.93

        # 3c. Soil factor (moisture band * pH band)
        moisture = float(soil_data.get("topsoil_moisture_vol_pct", 25.0))
        if 20.0 <= moisture <= 30.0:
            m_factor = 1.00
        elif (15.0 <= moisture < 20.0) or (30.0 < moisture <= 35.0):
            m_factor = 0.97
        else:
            m_factor = 0.92

        ph = float(soil_data.get("soil_ph", 7.0))
        if 6.0 <= ph <= 7.0:
            ph_factor = 1.00
        elif 7.0 < ph <= 7.5:
            ph_factor = 0.98
        elif (5.5 <= ph < 6.0) or (7.5 < ph <= 8.0):
            ph_factor = 0.95
        else:
            ph_factor = 0.90

        f_soil = m_factor * ph_factor

        # 3d. Predicted yield
        predicted_yield_kg = round(acreage * y_base * f_gdd * f_rain * f_soil, 2)

        # 3e. Confidence score
        sources = [weather_source, soil_source]
        num_offline = sources.count("offline_fixture")
        num_cache = sources.count("cache")
        confidence_score_pct = max(0, 100 - 6 * num_offline - 3 * num_cache)

        # 3f. Environmental index
        temp_score = _clamp(1.0 - abs(temp_c - 25.0) / 25.0, 0.0, 1.0)
        hum_pct = float(weather_data.get("relative_humidity_pct", 60.0))
        hum_score = _clamp(1.0 - abs(hum_pct - 60.0) / 60.0, 0.0, 1.0)
        solar_index = float(weather_data.get("solar_radiation_index", 0.85))
        moist_score = _clamp(1.0 - abs(moisture - 25.0) / 25.0, 0.0, 1.0)
        environmental_index = round((temp_score + hum_score + solar_index + moist_score) / 4.0, 2)

        # 3g. Predicted harvest date
        predicted_harvest_date = (p_date + timedelta(days=season_days)).strftime("%Y-%m-%d")

        # 3h. Irrigation advice
        if moisture < 15.0:
            irrigation_advice = "Low soil moisture. Increase irrigation frequency immediately."
        elif 15.0 <= moisture < 20.0:
            irrigation_advice = "Soil moisture below optimal. Consider supplemental irrigation."
        elif 20.0 <= moisture <= 30.0:
            irrigation_advice = "Optimal soil moisture. Maintain standard irrigation schedule."
        else:
            irrigation_advice = "High soil moisture. Reduce irrigation to avoid waterlogging."

        # Step 4: Persist to yield_forecasts table (FR-YLD-006)
        cursor.execute(
            """
            INSERT INTO yield_forecasts (
                listing_id, crop_name, predicted_harvest_date,
                predicted_yield_kg, confidence_score_pct,
                environmental_index, irrigation_advice
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                listing_id,
                crop_name,
                predicted_harvest_date,
                predicted_yield_kg,
                confidence_score_pct,
                environmental_index,
                irrigation_advice,
            ),
        )
        forecast_id = cursor.lastrowid
        db.commit()

        # Read back the inserted row
        cursor.execute("SELECT * FROM yield_forecasts WHERE id = ?", (forecast_id,))
        row = cursor.fetchone()

        return {
            "forecast_id": row["id"],
            "listing_id": row["listing_id"],
            "crop_name": row["crop_name"],
            "acreage": acreage,
            "predicted_harvest_date": row["predicted_harvest_date"],
            "predicted_yield_kg": float(row["predicted_yield_kg"]),
            "confidence_score_pct": int(row["confidence_score_pct"]),
            "environmental_index": float(row["environmental_index"]) if row["environmental_index"] is not None else None,
            "irrigation_advice": row["irrigation_advice"],
            "generated_at": row["generated_at"],
        }
    finally:
        if should_close:
            db.close()
