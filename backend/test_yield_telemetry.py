"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    test_yield_telemetry.py
Module:  Environmental Telemetry & Predictive Yield Verification Suite (Increment 2 Phase 4 V&V)
Version: 2.0  (Increment 2 — Intelligence Layer)
Author:  Muhammad Hashir (QA & DevOps Engineer)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §6.3, §10.3, API Contracts Delta v1.2 §7 (Endpoints 11 & 12),
         Phase 4 Build Package (PD-1..PD-12)

Test Coverage (11 Tests)
------------------------
  Environmental Telemetry Endpoints (TC-TEL)
    TC-TEL-01  GET /api/telemetry/weather — Offline weather fixture: exact values, keys & timestamp (200)
    TC-TEL-02  GET /api/telemetry/soil    — Offline soil fixture: exact values, keys & timestamp (200)
    TC-TEL-03  GET /api/telemetry/*       — Coordinate boundary & type validation (missing, >90, <-180, non-float -> 400)
    TC-TEL-04  GET /api/telemetry/*       — RBAC guards: Buyer (200), Transporter (403), Unauthenticated (401)

  Telemetry Cache Lifecycle (TC-CCH)
    TC-CCH-01  Cache hit + TTL            — Fresh coords: 1st call offline_fixture, 2nd call cache; 6h TTL (±5s)
    TC-CCH-02  Expired row refresh        — Pre-inserted expired sentinel row refreshed with live/fixture data
    TC-CCH-03  Key independence           — Weather & soil at same coords persist separate keys with distinct providers

  Predictive Yield Engine (TC-YLD)
    TC-YLD-01  The Benchmark (Wheat)      — 12.5 acres, 90d progress -> 18367.65 kg, 88% confidence, 0.90 env index, DB row
    TC-YLD-02  Yield Prediction Guards    — Buyer (403), missing listing_id (400), nonexistent (404), non-owner (404), soft-deleted (404)
    TC-YLD-03  All-Crop Determinism       — Formula verification across all 8 crops matching round(10 * Y_base * 1.02 * 1.05 * 0.98, 2)
    TC-YLD-04  Repeat Predict & Interplay — Second prediction serves from cache -> confidence rises to 94%; append-only history

Usage
-----
  python backend/test_yield_telemetry.py       (from project root)
  python test_yield_telemetry.py               (from backend/ directory)
"""

import os
import sys

# Force offline mode for the entire suite before importing any app/service logic
os.environ["AGRIGRID_OFFLINE_MODE"] = "1"

import json
import sqlite3
import threading
import time
from datetime import date, datetime, timedelta, timezone
import requests

# ---------------------------------------------------------------------------
# Path resolution — runnable from project root OR backend/ directory
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app  # noqa: E402

# ---------------------------------------------------------------------------
# Server configuration
# ---------------------------------------------------------------------------
TEST_HOST = os.environ.get("AGRIGRID_TEST_HOST", "127.0.0.1")
TEST_PORT = int(os.environ.get("AGRIGRID_TEST_PORT", "5005"))
API_BASE_URL = os.environ.get("API_BASE_URL", f"http://{TEST_HOST}:{TEST_PORT}/api")

DB_PATH = os.environ.get(
    "AGRIGRID_DB_PATH",
    os.path.join(SCRIPT_DIR, "database", "agrigrid.db"),
)

# ---------------------------------------------------------------------------
# Shared test state
# ---------------------------------------------------------------------------
RESULTS: list[dict] = []
RUN_TIMESTAMP = int(time.time())

_tahir_token: str = ""
_sara_token: str = ""
_transporter_token: str = ""
_farmer_b_token: str = ""

_benchmark_listing_id: int = 0

TODAY = date.today()


# ---------------------------------------------------------------------------
# Test result helpers
# ---------------------------------------------------------------------------
def _pass(tc: str, desc: str, detail: str = "") -> None:
    msg = f"[PASS] {tc}: {desc}"
    if detail:
        msg += f"\n       {detail}"
    print(msg)
    RESULTS.append({"tc": tc, "status": "PASS", "desc": desc})


def _fail(tc: str, desc: str, detail: str = "") -> None:
    msg = f"[FAIL] {tc}: {desc}"
    if detail:
        msg += f"\n       {detail}"
    print(msg)
    RESULTS.append({"tc": tc, "status": "FAIL", "desc": desc})


def _check(tc: str, desc: str, condition: bool, detail: str = "") -> None:
    (_pass if condition else _fail)(tc, desc, detail)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _get_db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ---------------------------------------------------------------------------
# Server startup & probe
# ---------------------------------------------------------------------------
def _probe_server(url: str, timeout: float = 12.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{url}/auth/me", timeout=1.0)
            if r.status_code == 401:
                return True
        except Exception:
            time.sleep(0.25)
    return False


def _ensure_server_running():
    global API_BASE_URL
    # Check if a dedicated test server is already running on TEST_PORT
    if _probe_server(f"http://{TEST_HOST}:{TEST_PORT}/api", timeout=1.0):
        API_BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}/api"
        print(f"[BOOT] Target server already active on {API_BASE_URL}")
        return

    # Start dedicated background test server with offline mode enforced
    print(f"[BOOT] Starting dedicated offline test server on http://{TEST_HOST}:{TEST_PORT} ...")
    app = create_app()
    server_thread = threading.Thread(
        target=lambda: app.run(host=TEST_HOST, port=TEST_PORT, debug=False, use_reloader=False),
        daemon=True,
    )
    server_thread.start()

    API_BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}/api"
    if not _probe_server(API_BASE_URL, timeout=15.0):
        print(f"[FATAL] Could not connect to test server on {API_BASE_URL}")
        sys.exit(1)
    print(f"[BOOT] Server ready at {API_BASE_URL}\n")


# ---------------------------------------------------------------------------
# Auth bootstrap helper
# ---------------------------------------------------------------------------
def _init_tokens():
    global _tahir_token, _sara_token, _transporter_token, _farmer_b_token

    # 1. Tahir Farmer
    r_tahir = requests.post(f"{API_BASE_URL}/auth/login", json={"username": "tahir_farmer", "password": "FarmSecure1"})
    if r_tahir.status_code == 200:
        _tahir_token = r_tahir.json().get("token", "")

    # 2. Sara Buyer
    r_sara = requests.post(f"{API_BASE_URL}/auth/login", json={"username": "sara_buyer", "password": "BuyerPass1"})
    if r_sara.status_code == 200:
        _sara_token = r_sara.json().get("token", "")

    # 3. Transporter
    trans_user = f"trans_qa_{RUN_TIMESTAMP}"
    r_reg_tr = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": trans_user, "password": "TransporterPass1!", "role": "transporter"},
    )
    if r_reg_tr.status_code in (201, 409):
        r_log_tr = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": trans_user, "password": "TransporterPass1!"},
        )
        if r_log_tr.status_code == 200:
            _transporter_token = r_log_tr.json().get("token", "")

    # 4. Farmer B
    farmer_b_user = f"farmer_b_qa_{RUN_TIMESTAMP}"
    r_reg_fb = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": farmer_b_user, "password": "FarmSecureB1!", "role": "farmer", "farm_name": "Sunrise Agro"},
    )
    if r_reg_fb.status_code in (201, 409):
        r_log_fb = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"username": farmer_b_user, "password": "FarmSecureB1!"},
        )
        if r_log_fb.status_code == 200:
            _farmer_b_token = r_log_fb.json().get("token", "")


# ===========================================================================
# 1. ENVIRONMENTAL TELEMETRY (TC-TEL)
# ===========================================================================

def tc_tel_01_weather_offline():
    """Tahir queries weather telemetry in offline mode -> 200, offline_fixture source, exact pinned values."""
    r = requests.get(
        f"{API_BASE_URL}/telemetry/weather?lat=30.3753&lon=69.3451",
        headers=_auth(_tahir_token),
    )
    data_json = r.json()

    status_ok = r.status_code == 200
    keys_ok = set(data_json.keys()) == {"success", "source", "data"}
    source_ok = data_json.get("source") == "offline_fixture"

    d = data_json.get("data", {})
    temp_ok = d.get("temperature_c") == 28.5
    humidity_ok = d.get("relative_humidity_pct") == 55.0
    precip_ok = d.get("cumulative_precipitation_14d_mm") == 12.4
    solar_ok = d.get("solar_radiation_index") == 0.85
    desc_ok = d.get("description") == "Clear sky"
    ts_ok = bool(d.get("timestamp"))

    all_ok = (status_ok and keys_ok and source_ok and temp_ok and
              humidity_ok and precip_ok and solar_ok and desc_ok and ts_ok)

    detail = (
        f"status={r.status_code} source='{data_json.get('source')}' "
        f"temp={d.get('temperature_c')} humidity={d.get('relative_humidity_pct')} "
        f"precip={d.get('cumulative_precipitation_14d_mm')} solar={d.get('solar_radiation_index')} "
        f"desc='{d.get('description')}' ts='{d.get('timestamp')}'"
    )

    _check(
        "TC-TEL-01",
        "Weather offline returns 200, envelope keys {success, source, data}, source 'offline_fixture', exact pinned values",
        all_ok,
        detail,
    )


def tc_tel_02_soil_offline():
    """Tahir queries soil telemetry in offline mode -> 200, offline_fixture source, exact pinned values."""
    r = requests.get(
        f"{API_BASE_URL}/telemetry/soil?lat=30.3753&lon=69.3451",
        headers=_auth(_tahir_token),
    )
    data_json = r.json()

    status_ok = r.status_code == 200
    keys_ok = set(data_json.keys()) == {"success", "source", "data"}
    source_ok = data_json.get("source") == "offline_fixture"

    d = data_json.get("data", {})
    moist_ok = d.get("topsoil_moisture_vol_pct") == 24.5
    soc_ok = d.get("soil_organic_carbon_g_per_kg") == 11.2
    ph_ok = d.get("soil_ph") == 7.4
    texture_ok = d.get("soil_texture_class") == "Clay Loam"
    ts_ok = bool(d.get("timestamp"))

    all_ok = status_ok and keys_ok and source_ok and moist_ok and soc_ok and ph_ok and texture_ok and ts_ok

    detail = (
        f"status={r.status_code} source='{data_json.get('source')}' "
        f"moisture={d.get('topsoil_moisture_vol_pct')} soc={d.get('soil_organic_carbon_g_per_kg')} "
        f"ph={d.get('soil_ph')} texture='{d.get('soil_texture_class')}' ts='{d.get('timestamp')}'"
    )

    _check(
        "TC-TEL-02",
        "Soil offline returns 200, envelope keys {success, source, data}, source 'offline_fixture', exact pinned values",
        all_ok,
        detail,
    )


def tc_tel_03_coordinate_validation():
    """Coordinate validation: missing lat, lat>90, lon<-180, non-numeric rejected with 400 and exact error."""
    expected_error = "Valid latitude (-90 to 90) and longitude (-180 to 180) are required."

    cases = [
        ("missing_lat", f"{API_BASE_URL}/telemetry/weather?lon=69.3451"),
        ("lat_gt_90", f"{API_BASE_URL}/telemetry/weather?lat=91&lon=69.3451"),
        ("lon_lt_minus_180", f"{API_BASE_URL}/telemetry/weather?lat=30.3753&lon=-181"),
        ("lat_non_numeric", f"{API_BASE_URL}/telemetry/weather?lat=abc&lon=69.3451"),
    ]

    all_ok = True
    details = []
    for label, url in cases:
        r = requests.get(url, headers=_auth(_tahir_token))
        err = r.json().get("error") if r.status_code == 400 else ""
        case_ok = (r.status_code == 400 and err == expected_error)
        all_ok = all_ok and case_ok
        details.append(f"{label}={'PASS' if case_ok else 'FAIL'}({r.status_code}, '{err}')")

    _check(
        "TC-TEL-03",
        "Coordinate validation: missing, lat>90, lon<-180, lat=abc return 400 with exact error message",
        all_ok,
        " | ".join(details),
    )


def tc_tel_04_rbac():
    """RBAC validation: buyer token -> 200; transporter token -> 403 'Access denied.'; no token -> 401."""
    # 1. Buyer token -> 200
    r_buyer = requests.get(
        f"{API_BASE_URL}/telemetry/weather?lat=30.3753&lon=69.3451",
        headers=_auth(_sara_token),
    )
    buyer_ok = r_buyer.status_code == 200 and r_buyer.json().get("success") is True

    # 2. Transporter token -> 403
    r_trans = requests.get(
        f"{API_BASE_URL}/telemetry/weather?lat=30.3753&lon=69.3451",
        headers=_auth(_transporter_token),
    )
    trans_ok = r_trans.status_code == 403 and r_trans.json().get("error") == "Access denied."

    # 3. Unauthenticated -> 401
    r_anon = requests.get(f"{API_BASE_URL}/telemetry/weather?lat=30.3753&lon=69.3451")
    anon_ok = r_anon.status_code == 401 and r_anon.json().get("error") == "Authentication required. Please log in."

    all_ok = buyer_ok and trans_ok and anon_ok
    detail = f"buyer={r_buyer.status_code} transporter={r_trans.status_code} anon={r_anon.status_code}"

    _check(
        "TC-TEL-04",
        "RBAC guards: buyer allowed (200), transporter denied (403), unauthenticated rejected (401)",
        all_ok,
        detail,
    )


# ===========================================================================
# 2. TELEMETRY CACHE LIFECYCLE (TC-CCH)
# ===========================================================================

def tc_cch_01_cache_hit_and_ttl():
    """Fresh coords: 1st call -> offline_fixture, 2nd call -> cache; DB row has 6h TTL (±5s) and OpenWeatherMap."""
    lat_val, lon_val = 32.1000, 71.5000
    url = f"{API_BASE_URL}/telemetry/weather?lat={lat_val}&lon={lon_val}"

    # Clean any prior cache record for these coordinates
    conn = _get_db_conn()
    conn.execute("DELETE FROM telemetry_cache WHERE latitude = ? AND longitude = ?", (lat_val, lon_val))
    conn.commit()

    # 1. First call -> offline_fixture
    r1 = requests.get(url, headers=_auth(_tahir_token))
    src1 = r1.json().get("source")
    r1_ok = r1.status_code == 200 and src1 == "offline_fixture"

    # 2. Second identical call -> cache
    r2 = requests.get(url, headers=_auth(_tahir_token))
    src2 = r2.json().get("source")
    r2_ok = r2.status_code == 200 and src2 == "cache"

    # 3. Verify exactly one DB row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM telemetry_cache WHERE cache_key = ?",
        (f"weather:{lat_val:.4f}:{lon_val:.4f}",),
    )
    rows = cursor.fetchall()
    row_count_ok = len(rows) == 1

    provider_ok = False
    ttl_ok = False
    diff_seconds = 0.0

    if row_count_ok:
        row = rows[0]
        provider_ok = row["provider"] == "OpenWeatherMap"

        fetched_at_str = row["fetched_at"]
        expires_at_str = row["expires_at"]

        # Parse fetched_at ('YYYY-MM-DDTHH:MM:SSZ' or 'YYYY-MM-DD HH:MM:SS')
        f_clean = fetched_at_str.replace("Z", "").replace("T", " ")
        e_clean = expires_at_str.replace("Z", "").replace("T", " ")
        f_dt = datetime.strptime(f_clean[:19], "%Y-%m-%d %H:%M:%S")
        e_dt = datetime.strptime(e_clean[:19], "%Y-%m-%d %H:%M:%S")

        diff_seconds = (e_dt - f_dt).total_seconds()
        ttl_ok = abs(diff_seconds - 6 * 3600) <= 5.0

    conn.close()

    all_ok = r1_ok and r2_ok and row_count_ok and provider_ok and ttl_ok
    detail = (
        f"1st_source='{src1}' 2nd_source='{src2}' rows={len(rows)} "
        f"provider='{rows[0]['provider'] if rows else ''}' ttl_diff={diff_seconds:.1f}s"
    )

    _check(
        "TC-CCH-01",
        "Cache hit + TTL: 1st call offline_fixture, 2nd call cache, exactly 1 row, provider OpenWeatherMap, TTL=6h (±5s)",
        all_ok,
        detail,
    )


def tc_cch_02_expired_row_refresh():
    """Expired row refresh: sentinel payload with past expires_at is refreshed with fixture and future expires_at."""
    ckey = "weather:33.0000:72.0000"
    lat_val, lon_val = 33.0, 72.0

    # 1. Pre-insert expired sentinel row
    conn = _get_db_conn()
    conn.execute(
        """
        INSERT OR REPLACE INTO telemetry_cache
            (cache_key, provider, latitude, longitude, payload_json, fetched_at, expires_at)
        VALUES (?, 'OpenWeatherMap', ?, ?, ?, '2020-01-01 00:00:00', '2020-01-01 06:00:00')
        """,
        (ckey, lat_val, lon_val, json.dumps({"temperature_c": -99.0})),
    )
    conn.commit()

    # 2. Call endpoint
    r = requests.get(
        f"{API_BASE_URL}/telemetry/weather?lat={lat_val}&lon={lon_val}",
        headers=_auth(_tahir_token),
    )
    res_data = r.json()
    status_ok = r.status_code == 200
    source_ok = res_data.get("source") == "offline_fixture"
    returned_temp = res_data.get("data", {}).get("temperature_c")
    data_fixture_ok = returned_temp == 28.5  # Not the sentinel -99.0

    # 3. Verify DB row replaced
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM telemetry_cache WHERE cache_key = ?", (ckey,))
    row = cursor.fetchone()

    db_temp_ok = False
    expires_future_ok = False
    if row:
        stored_payload = json.loads(row["payload_json"])
        db_temp_ok = stored_payload.get("temperature_c") == 28.5

        # Check expires_at is in the future (~ now + 6h)
        e_clean = row["expires_at"].replace("Z", "").replace("T", " ")
        e_dt = datetime.strptime(e_clean[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        expires_future_ok = e_dt > datetime.now(timezone.utc)

    conn.close()

    all_ok = status_ok and source_ok and data_fixture_ok and db_temp_ok and expires_future_ok
    detail = (
        f"status={r.status_code} source='{res_data.get('source')}' returned_temp={returned_temp} "
        f"db_temp_ok={db_temp_ok} expires_future={expires_future_ok}"
    )

    _check(
        "TC-CCH-02",
        "Expired row refresh: stale sentinel rejected, fresh offline_fixture returned, DB row refreshed with future expiry",
        all_ok,
        detail,
    )


def tc_cch_03_key_independence():
    """Key independence: weather and soil at same coords produce two distinct rows with respective providers."""
    lat_val, lon_val = 32.5000, 71.8000

    conn = _get_db_conn()
    conn.execute("DELETE FROM telemetry_cache WHERE latitude = ? AND longitude = ?", (lat_val, lon_val))
    conn.commit()

    # Call weather & soil
    r_w = requests.get(f"{API_BASE_URL}/telemetry/weather?lat={lat_val}&lon={lon_val}", headers=_auth(_tahir_token))
    r_s = requests.get(f"{API_BASE_URL}/telemetry/soil?lat={lat_val}&lon={lon_val}", headers=_auth(_tahir_token))

    calls_ok = r_w.status_code == 200 and r_s.status_code == 200

    cursor = conn.cursor()
    cursor.execute(
        "SELECT cache_key, provider FROM telemetry_cache WHERE latitude = ? AND longitude = ? ORDER BY cache_key",
        (lat_val, lon_val),
    )
    rows = cursor.fetchall()
    conn.close()

    two_rows_ok = len(rows) == 2
    row_map = {r["cache_key"]: r["provider"] for r in rows}

    w_key = f"weather:{lat_val:.4f}:{lon_val:.4f}"
    s_key = f"soil:{lat_val:.4f}:{lon_val:.4f}"

    weather_key_ok = row_map.get(w_key) == "OpenWeatherMap"
    soil_key_ok = row_map.get(s_key) == "SoilGrids"

    all_ok = calls_ok and two_rows_ok and weather_key_ok and soil_key_ok
    detail = f"calls_ok={calls_ok} rows={len(rows)} map={row_map}"

    _check(
        "TC-CCH-03",
        "Key independence: weather and soil at identical coordinates create separate keys (OpenWeatherMap vs SoilGrids)",
        all_ok,
        detail,
    )


# ===========================================================================
# 3. PREDICTIVE YIELD ENGINE (TC-YLD)
# ===========================================================================

def tc_yld_01_benchmark():
    """The Benchmark: Wheat 12.5 acres, 90d progress -> 18367.65 kg, 88% confidence, 0.90 env index, DB row verified."""
    global _benchmark_listing_id

    # 1. Create unique Wheat listing as Tahir
    p_date = (TODAY - timedelta(days=90)).isoformat()
    h_date = (TODAY + timedelta(days=60)).isoformat()
    lat_val, lon_val = 31.5204, 74.3587

    # Ensure clean cache state for these coordinates
    conn = _get_db_conn()
    conn.execute("DELETE FROM telemetry_cache WHERE latitude = ? AND longitude = ?", (lat_val, lon_val))
    conn.commit()

    r_create = requests.post(
        f"{API_BASE_URL}/crops",
        headers=_auth(_tahir_token),
        json={
            "crop_name": "Wheat",
            "acreage": 12.5,
            "planting_date": p_date,
            "estimated_harvest_date": h_date,
            "gps_latitude": lat_val,
            "gps_longitude": lon_val,
            "quantity_kg": 5000.0,
        },
    )
    if r_create.status_code != 201:
        _fail("TC-YLD-01", f"Failed to create benchmark Wheat listing: {r_create.text}")
        return

    _benchmark_listing_id = r_create.json()["data"]["listing_id"]

    # 2. Call POST /api/yield/predict
    r_predict = requests.post(
        f"{API_BASE_URL}/yield/predict",
        headers=_auth(_tahir_token),
        json={"listing_id": _benchmark_listing_id},
    )
    data = r_predict.json()
    status_ok = r_predict.status_code == 200 and data.get("success") is True
    forecast = data.get("data", {})

    yield_ok = forecast.get("predicted_yield_kg") == 18367.65
    conf_ok = forecast.get("confidence_score_pct") == 88
    advice_ok = forecast.get("irrigation_advice") == "Optimal soil moisture. Maintain standard irrigation schedule."
    expected_harvest_date = (TODAY - timedelta(days=90) + timedelta(days=150)).strftime("%Y-%m-%d")
    harvest_ok = forecast.get("predicted_harvest_date") == expected_harvest_date
    env_ok = forecast.get("environmental_index") == 0.90

    # 3. Check physical persistence in yield_forecasts table
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM yield_forecasts WHERE listing_id = ?",
        (_benchmark_listing_id,),
    )
    db_rows = cursor.fetchall()
    conn.close()

    db_ok = (
        len(db_rows) == 1
        and float(db_rows[0]["predicted_yield_kg"]) == 18367.65
        and int(db_rows[0]["confidence_score_pct"]) == 88
        and float(db_rows[0]["environmental_index"]) == 0.90
        and db_rows[0]["irrigation_advice"] == "Optimal soil moisture. Maintain standard irrigation schedule."
    )

    all_ok = status_ok and yield_ok and conf_ok and advice_ok and harvest_ok and env_ok and db_ok
    detail = (
        f"status={r_predict.status_code} yield={forecast.get('predicted_yield_kg')} "
        f"conf={forecast.get('confidence_score_pct')}% env_index={forecast.get('environmental_index')} "
        f"advice='{forecast.get('irrigation_advice')}' harvest_date={forecast.get('predicted_harvest_date')} db_ok={db_ok}"
    )

    _check(
        "TC-YLD-01",
        "The Benchmark: Wheat 12.5ac -> 18367.65 kg, 88% confidence, 0.90 env index, standard irrigation, persisted to DB",
        all_ok,
        detail,
    )


def tc_yld_02_guards():
    """Yield prediction guards: buyer (403), missing listing_id (400), nonexistent (404), non-owner (404), soft-deleted (404)."""
    # 1. Buyer token -> 403
    r_buyer = requests.post(
        f"{API_BASE_URL}/yield/predict",
        headers=_auth(_sara_token),
        json={"listing_id": _benchmark_listing_id},
    )
    buyer_ok = r_buyer.status_code == 403 and r_buyer.json().get("error") == "Access denied."

    # 2. Missing listing_id -> 400
    r_miss = requests.post(
        f"{API_BASE_URL}/yield/predict",
        headers=_auth(_tahir_token),
        json={},
    )
    miss_ok = r_miss.status_code == 400 and r_miss.json().get("error") == "Listing ID is required."

    # 3. Nonexistent listing_id -> 404
    r_nonexist = requests.post(
        f"{API_BASE_URL}/yield/predict",
        headers=_auth(_tahir_token),
        json={"listing_id": 999999},
    )
    nonexist_ok = r_nonexist.status_code == 404 and r_nonexist.json().get("error") == "Listing not found."

    # 4. Second farmer predicting Tahir's listing -> 404
    r_other_farmer = requests.post(
        f"{API_BASE_URL}/yield/predict",
        headers=_auth(_farmer_b_token),
        json={"listing_id": _benchmark_listing_id},
    )
    other_farmer_ok = r_other_farmer.status_code == 404 and r_other_farmer.json().get("error") == "Listing not found."

    # 5. Soft-deleted listing -> 404
    # Create listing and delete it
    r_tmp = requests.post(
        f"{API_BASE_URL}/crops",
        headers=_auth(_tahir_token),
        json={
            "crop_name": "Tomato",
            "acreage": 2.0,
            "planting_date": TODAY.isoformat(),
            "estimated_harvest_date": (TODAY + timedelta(days=120)).isoformat(),
            "gps_latitude": 30.1234,
            "gps_longitude": 72.5678,
            "quantity_kg": 1000.0,
        },
    )
    del_id = r_tmp.json()["data"]["listing_id"]
    requests.delete(f"{API_BASE_URL}/crops/{del_id}", headers=_auth(_tahir_token))

    r_deleted = requests.post(
        f"{API_BASE_URL}/yield/predict",
        headers=_auth(_tahir_token),
        json={"listing_id": del_id},
    )
    del_ok = r_deleted.status_code == 404 and r_deleted.json().get("error") == "Listing not found."

    all_ok = buyer_ok and miss_ok and nonexist_ok and other_farmer_ok and del_ok
    detail = (
        f"buyer={r_buyer.status_code} missing={r_miss.status_code} "
        f"nonexist={r_nonexist.status_code} non_owner={r_other_farmer.status_code} soft_deleted={r_deleted.status_code}"
    )

    _check(
        "TC-YLD-02",
        "Yield prediction guards: buyer (403), missing listing_id (400), nonexistent (404), non-owner (404), soft-deleted (404)",
        all_ok,
        detail,
    )


def tc_yld_03_all_crop_determinism():
    """All-crop determinism (FR-YLD-002): tests all 8 crops matching round(10 * Y_base * 1.02 * 1.05 * 0.98, 2) & 88% conf."""
    crops_spec = [
        ("Wheat", 1400, 150),
        ("Rice", 2600, 140),
        ("Tomato", 8000, 120),
        ("Potato", 9000, 110),
        ("Cotton", 1100, 180),
        ("Maize", 2800, 120),
        ("Sugarcane", 32000, 330),
        ("Other", 1500, 120),
    ]

    all_ok = True
    subresults = []

    conn = _get_db_conn()

    for i, (crop_name, y_base, season_days) in enumerate(crops_spec):
        # Progress = 0.6: planting_date = today - round(0.6 * season_days)
        days_ago = round(0.6 * season_days)
        p_date = (TODAY - timedelta(days=days_ago)).isoformat()
        h_date = (TODAY + timedelta(days=season_days - days_ago)).isoformat()

        # Unique coordinates per crop so every predict takes pure offline_fixture path
        lat_c = round(31.6204 + 0.01 * i, 4)
        lon_c = 74.3587

        # Clean cache for these coordinates just in case
        conn.execute("DELETE FROM telemetry_cache WHERE latitude = ? AND longitude = ?", (lat_c, lon_c))
        conn.commit()

        # Create listing
        r_create = requests.post(
            f"{API_BASE_URL}/crops",
            headers=_auth(_tahir_token),
            json={
                "crop_name": crop_name,
                "acreage": 10.0,
                "planting_date": p_date,
                "estimated_harvest_date": h_date,
                "gps_latitude": lat_c,
                "gps_longitude": lon_c,
                "quantity_kg": 1000.0,
            },
        )
        if r_create.status_code != 201:
            all_ok = False
            subresults.append(f"{crop_name}=CREATE_FAIL({r_create.status_code})")
            continue

        l_id = r_create.json()["data"]["listing_id"]

        # Predict yield
        r_pred = requests.post(
            f"{API_BASE_URL}/yield/predict",
            headers=_auth(_tahir_token),
            json={"listing_id": l_id},
        )
        if r_pred.status_code != 200:
            all_ok = False
            subresults.append(f"{crop_name}=PRED_FAIL({r_pred.status_code})")
            continue

        pred_data = r_pred.json().get("data", {})
        actual_yield = pred_data.get("predicted_yield_kg")
        actual_conf = pred_data.get("confidence_score_pct")

        # Expected: round(10 * Y_base * 1.02 * 1.05 * 0.98, 2)
        expected_yield = round(10.0 * y_base * 1.02 * 1.05 * 0.98, 2)
        expected_conf = 88

        crop_ok = (actual_yield == expected_yield and actual_conf == expected_conf)
        all_ok = all_ok and crop_ok
        subresults.append(f"{crop_name}={'OK' if crop_ok else 'FAIL'}({actual_yield}/{expected_yield}, {actual_conf}%)")

    conn.close()

    _check(
        "TC-YLD-03",
        "All-crop determinism (FR-YLD-002): all 8 crop formulas match exact expected mathematical yields and 88% confidence",
        all_ok,
        " | ".join(subresults),
    )


def tc_yld_04_repeat_predict_and_cache_interplay():
    """Repeat predict + cache interplay: second predict served from cache -> confidence rises to 94%; append-only history."""
    # Predict TC-YLD-01's benchmark listing a second time (telemetry coordinates are now cached)
    r_repeat = requests.post(
        f"{API_BASE_URL}/yield/predict",
        headers=_auth(_tahir_token),
        json={"listing_id": _benchmark_listing_id},
    )
    data = r_repeat.json()

    status_ok = r_repeat.status_code == 200 and data.get("success") is True
    forecast = data.get("data", {})

    conf_94_ok = forecast.get("confidence_score_pct") == 94
    yield_match = forecast.get("predicted_yield_kg") == 18367.65
    second_forecast_id = forecast.get("forecast_id")

    # Verify append-only history in yield_forecasts table
    conn = _get_db_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, confidence_score_pct FROM yield_forecasts WHERE listing_id = ? ORDER BY id ASC",
        (_benchmark_listing_id,),
    )
    rows = cursor.fetchall()
    conn.close()

    two_rows_ok = len(rows) == 2
    ids_differ = False
    conf_sequence_ok = False

    if two_rows_ok:
        ids_differ = rows[0]["id"] != rows[1]["id"] and rows[1]["id"] == second_forecast_id
        conf_sequence_ok = rows[0]["confidence_score_pct"] == 88 and rows[1]["confidence_score_pct"] == 94

    all_ok = status_ok and conf_94_ok and yield_match and two_rows_ok and ids_differ and conf_sequence_ok
    detail = (
        f"status={r_repeat.status_code} conf={forecast.get('confidence_score_pct')}% "
        f"forecast_ids=[{rows[0]['id'] if rows else ''}, {rows[1]['id'] if len(rows) > 1 else ''}] "
        f"confs=[{rows[0]['confidence_score_pct'] if rows else ''}, {rows[1]['confidence_score_pct'] if len(rows) > 1 else ''}]"
    )

    _check(
        "TC-YLD-04",
        "Repeat predict + cache interplay: 2nd prediction confidence=94% (cached telemetry), 2 distinct rows in yield_forecasts",
        all_ok,
        detail,
    )


# ===========================================================================
# TEARDOWN & BASELINE RESTORATION
# ===========================================================================

def _teardown_baseline():
    """Restore database state so subsequent suites run against clean baseline."""
    conn = _get_db_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys = OFF;")
        cursor.execute("DELETE FROM telemetry_cache;")
        cursor.execute("DELETE FROM yield_forecasts;")
        cursor.execute("DELETE FROM escrow_holdings;")
        cursor.execute("DELETE FROM orders;")
        cursor.execute("DELETE FROM listings WHERE id > 4;")
        cursor.execute("DELETE FROM buyer_wallets WHERE buyer_id IN (SELECT id FROM buyers WHERE user_id IN (SELECT id FROM users WHERE username NOT IN ('sara_buyer', 'tahir_farmer')));")
        cursor.execute("DELETE FROM buyers WHERE user_id IN (SELECT id FROM users WHERE username NOT IN ('sara_buyer', 'tahir_farmer'));")
        cursor.execute("DELETE FROM users WHERE username NOT IN ('tahir_farmer', 'sara_buyer');")
        cursor.execute("UPDATE listings SET status = 'Active', quantity_kg = 5000.0, asking_price_per_kg = 45.0, batch_id = 'BATCH-2026-WHT-0001', is_deleted = 0 WHERE id = 1;")
        cursor.execute("UPDATE listings SET status = 'Active', quantity_kg = 1800.0, asking_price_per_kg = NULL, batch_id = NULL, is_deleted = 0 WHERE id = 2;")
        cursor.execute("UPDATE listings SET status = 'Active', is_deleted = 0 WHERE id = 3;")
        cursor.execute("UPDATE listings SET status = 'Withdrawn', is_deleted = 1 WHERE id = 4;")
        cursor.execute("UPDATE buyer_wallets SET balance_pkr = 500000.00 WHERE buyer_id = 1;")
        cursor.execute("UPDATE farmer_wallets SET balance_pkr = 0.00 WHERE farmer_id = 1;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
    except Exception as exc:
        print(f"[WARN] Teardown baseline exception: {exc}")
    finally:
        conn.close()


# ===========================================================================
# SUITE MAIN RUNNER
# ===========================================================================

def main():
    print("=" * 65)
    print("  AGRI-GRID  Yield Telemetry & Forecasting API Test Suite")
    print("=" * 65)

    _ensure_server_running()
    _init_tokens()

    tests = [
        # Environmental Telemetry (TC-TEL)
        tc_tel_01_weather_offline,
        tc_tel_02_soil_offline,
        tc_tel_03_coordinate_validation,
        tc_tel_04_rbac,
        # Telemetry Cache Lifecycle (TC-CCH)
        tc_cch_01_cache_hit_and_ttl,
        tc_cch_02_expired_row_refresh,
        tc_cch_03_key_independence,
        # Predictive Yield Engine (TC-YLD)
        tc_yld_01_benchmark,
        tc_yld_02_guards,
        tc_yld_03_all_crop_determinism,
        tc_yld_04_repeat_predict_and_cache_interplay,
    ]

    try:
        for fn in tests:
            try:
                fn()
            except Exception as exc:
                _fail(fn.__name__, f"Unexpected exception: {exc}")
    finally:
        _teardown_baseline()

    # Summary
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    total = len(RESULTS)

    print()
    print("=" * 65)
    print(f"  RESULTS: {passed}/{total} passed  |  {failed} failed")
    print("=" * 65)

    if failed:
        print("\n  Failed tests:")
        for r in RESULTS:
            if r["status"] == "FAIL":
                print(f"    - {r['tc']}: {r['desc']}")
        sys.exit(1)
    else:
        print("\n  All tests passed. Environmental Telemetry & Yield Engine verified.")
        sys.exit(0)


if __name__ == "__main__":
    main()
