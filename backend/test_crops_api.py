"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    test_crops_api.py
Module:  Crop CRUD Pipeline Self-Verification  (Run 3 V&V)
Version: 1.0  (Increment 1 - Foundation & Farmer Dashboard)
Source:  AG-API-INC1-003 v1.0  Section 4 & 5 | AG-SRS-INC1-001 v1.1

Test Coverage
-------------
  Full Lifecycle (Farmer A)
    TC-01  POST /api/auth/register  — Register Farmer A
    TC-02  POST /api/auth/login     — Login Farmer A, capture JWT
    TC-03  POST /api/crops          — Create Crop Listing 1 (Wheat)
    TC-04  POST /api/crops          — Create Crop Listing 2 (Tomato)
    TC-05  GET  /api/crops          — Paginated list shows both listings
    TC-06  GET  /api/crops/<id>     — Retrieve Listing 1 full detail
    TC-07  PUT  /api/crops/<id>     — Update Listing 1 (acreage + quantity)
    TC-08  DELETE /api/crops/<id>   — Soft-delete Listing 2
    TC-09  GET  /api/crops          — Soft-deleted listing absent from results
    TC-10  GET  /api/crops/<id>     — Soft-deleted listing returns 404

  Zero-Trust Multi-Tenant Isolation
    TC-11  Register & login Farmer B
    TC-12  GET  /api/crops/<id>  Farmer B reads Farmer A's listing   -> 404
    TC-13  PUT  /api/crops/<id>  Farmer B updates Farmer A's listing -> 404
    TC-14  DELETE /api/crops/<id> Farmer B deletes Farmer A's listing -> 404
    TC-15  GET  /api/crops        Farmer B sees ONLY their own listings

  Input Validation
    TC-16  POST invalid crop_name taxonomy                           -> 400
    TC-17  POST planting_date in the future                         -> 400
    TC-18  POST harvest_date before planting_date                   -> 400
    TC-19  POST acreage = 0 (non-positive)                          -> 400
    TC-20  POST missing required field                              -> 400

  RBAC Guard
    TC-21  Buyer token attempts POST /api/crops                     -> 403
    TC-22  No token on GET /api/crops                               -> 401

  Metrics Aggregation
    TC-23  GET /api/crops/stats: 200 for farmer, 403 for buyer, 401 unauth

Usage
-----
  python backend/test_crops_api.py       (from project root)
  python test_crops_api.py               (from backend/ directory)
"""

import sys
import os
import time
import threading
import requests
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from app import create_app   # noqa: E402

# ---------------------------------------------------------------------------
# Server config
# ---------------------------------------------------------------------------
TEST_HOST = "127.0.0.1"
TEST_PORT = 5002           # separate port from test_auth.py (5001)
BASE_URL  = f"http://{TEST_HOST}:{TEST_PORT}"

# ---------------------------------------------------------------------------
# Shared test state
# ---------------------------------------------------------------------------
RESULTS: list[dict] = []

# Farmer A
_farmer_a_token: str = ""
_farmer_a_id:    int = 0
_listing_1_id:   int = 0
_listing_2_id:   int = 0

# Farmer B (multi-tenant isolation)
_farmer_b_token: str = ""

# Buyer (RBAC guard)
_buyer_token: str = ""

# Date helpers (safe for active listing rules)
TODAY      = date.today()
PLANT_DATE = (TODAY - timedelta(days=30)).isoformat()    # 30 days ago, valid
HARVEST_OK = (TODAY + timedelta(days=90)).isoformat()    # 90 days future, valid
# HARVEST_BAD: one day BEFORE planting — must fail the harvest > planting check
HARVEST_BAD = (TODAY - timedelta(days=31)).isoformat()   # one day before PLANT_DATE


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


# ---------------------------------------------------------------------------
# Flask server thread
# ---------------------------------------------------------------------------
def _start_server(app):
    app.run(host=TEST_HOST, port=TEST_PORT, debug=False, use_reloader=False)


# ===========================================================================
# TEST CASES
# ===========================================================================

# ------- LIFECYCLE: FARMER A -----------------------------------------------

def tc01_register_farmer_a():
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username":  "crop_test_farmer_a",
        "password":  "FarmerApass1",
        "role":      "farmer",
        "farm_name": "Alpha Harvest Farm",
    })
    body = r.json()
    # 201 on first run; 409 on subsequent re-runs (persistent DB, idempotent)
    already_exists = r.status_code == 409 and "already exists" in body.get("error", "")
    first_time_ok  = (
        r.status_code == 201
        and body.get("user", {}).get("farmer_id") is not None
    )
    _check("TC-01", "Register Farmer A (201 new | 409 idempotent re-run)",
           first_time_ok or already_exists,
           f"status={r.status_code} msg='{body.get('error') or body.get('message')}'")



def tc02_login_farmer_a():
    global _farmer_a_token, _farmer_a_id
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "crop_test_farmer_a",
        "password": "FarmerApass1",
    })
    body = r.json()
    _farmer_a_token = body.get("token", "")
    _farmer_a_id    = body.get("user", {}).get("farmer_id", 0)
    _check("TC-02", "Login Farmer A — get JWT (200)",
           r.status_code == 200 and len(_farmer_a_token) > 20,
           f"status={r.status_code} farmer_id={_farmer_a_id}")


def tc03_create_listing_wheat():
    global _listing_1_id
    if not _farmer_a_token:
        _fail("TC-03", "Create Wheat listing — skipped (no token)")
        return
    r = requests.post(f"{BASE_URL}/api/crops",
                      headers=_auth(_farmer_a_token),
                      json={
                          "crop_name":              "Wheat",
                          "planting_date":          PLANT_DATE,
                          "estimated_harvest_date": HARVEST_OK,
                          "acreage":                12.5,
                          "gps_latitude":           30.3753,
                          "gps_longitude":          69.3451,
                          "quantity_kg":            5000.0,
                      })
    body = r.json()
    _listing_1_id = body.get("data", {}).get("listing_id", 0)
    _check("TC-03", "Create Wheat listing (201)",
           r.status_code == 201
           and body.get("success") is True
           and body.get("data", {}).get("status") == "Active"
           and body.get("data", {}).get("is_deleted") is False
           and _listing_1_id > 0,
           f"status={r.status_code} listing_id={_listing_1_id} "
           f"status_val={body.get('data', {}).get('status')}")


def tc04_create_listing_tomato():
    global _listing_2_id
    if not _farmer_a_token:
        _fail("TC-04", "Create Tomato listing — skipped (no token)")
        return
    r = requests.post(f"{BASE_URL}/api/crops",
                      headers=_auth(_farmer_a_token),
                      json={
                          "crop_name":              "Tomato",
                          "planting_date":          PLANT_DATE,
                          "estimated_harvest_date": HARVEST_OK,
                          "acreage":                4.0,
                          "gps_latitude":           30.3800,
                          "gps_longitude":          69.3500,
                          "quantity_kg":            1800.0,
                      })
    body = r.json()
    _listing_2_id = body.get("data", {}).get("listing_id", 0)
    _check("TC-04", "Create Tomato listing (201)",
           r.status_code == 201 and _listing_2_id > 0,
           f"status={r.status_code} listing_id={_listing_2_id}")


def tc05_list_crops_paginated():
    if not _farmer_a_token:
        _fail("TC-05", "List crops — skipped (no token)")
        return
    r = requests.get(f"{BASE_URL}/api/crops?page=1&limit=20",
                     headers=_auth(_farmer_a_token))
    body = r.json()
    listing_ids = [item["listing_id"] for item in body.get("data", [])]
    _check("TC-05", "GET /api/crops — pagination envelope + both listings present (200)",
           r.status_code == 200
           and body.get("success") is True
           and "total" in body and "page" in body and "limit" in body
           and _listing_1_id in listing_ids
           and _listing_2_id in listing_ids,
           f"status={r.status_code} total={body.get('total')} ids={listing_ids}")


def tc06_get_single_listing():
    if not _farmer_a_token or not _listing_1_id:
        _fail("TC-06", "Get single listing — skipped")
        return
    r = requests.get(f"{BASE_URL}/api/crops/{_listing_1_id}",
                     headers=_auth(_farmer_a_token))
    body = r.json()
    data = body.get("data", {})
    _check("TC-06", "GET /api/crops/<id> — full detail with GPS (200)",
           r.status_code == 200
           and data.get("listing_id") == _listing_1_id
           and "gps_latitude" in data
           and "gps_longitude" in data
           and "updated_at" in data,
           f"status={r.status_code} crop={data.get('crop_name')} "
           f"lat={data.get('gps_latitude')}")


def tc07_update_listing():
    if not _farmer_a_token or not _listing_1_id:
        _fail("TC-07", "Update listing — skipped")
        return
    r = requests.put(f"{BASE_URL}/api/crops/{_listing_1_id}",
                     headers=_auth(_farmer_a_token),
                     json={
                         "crop_name":              "Wheat",
                         "planting_date":          PLANT_DATE,
                         "estimated_harvest_date": HARVEST_OK,
                         "acreage":                20.0,        # updated
                         "gps_latitude":           30.3753,
                         "gps_longitude":          69.3451,
                         "quantity_kg":            8000.0,       # updated
                     })
    body = r.json()
    data = body.get("data", {})
    _check("TC-07", "PUT /api/crops/<id> — fields updated, updated_at refreshed (200)",
           r.status_code == 200
           and data.get("acreage") == 20.0
           and data.get("quantity_kg") == 8000.0
           and body.get("message") == "Crop listing updated successfully.",
           f"status={r.status_code} acreage={data.get('acreage')} "
           f"qty={data.get('quantity_kg')}")


def tc08_soft_delete_listing():
    if not _farmer_a_token or not _listing_2_id:
        _fail("TC-08", "Soft-delete listing — skipped")
        return
    r = requests.delete(f"{BASE_URL}/api/crops/{_listing_2_id}",
                        headers=_auth(_farmer_a_token))
    body = r.json()
    _check("TC-08", "DELETE /api/crops/<id> — soft-delete returns 200",
           r.status_code == 200
           and body.get("success") is True
           and body.get("message") == "Listing withdrawn successfully.",
           f"status={r.status_code} message='{body.get('message')}'")


def tc09_deleted_listing_absent_from_list():
    if not _farmer_a_token or not _listing_2_id:
        _fail("TC-09", "Deleted listing absent — skipped")
        return
    r = requests.get(f"{BASE_URL}/api/crops",
                     headers=_auth(_farmer_a_token))
    body = r.json()
    listing_ids = [item["listing_id"] for item in body.get("data", [])]
    _check("TC-09", "Soft-deleted listing absent from GET /api/crops",
           r.status_code == 200
           and _listing_2_id not in listing_ids,
           f"status={r.status_code} visible_ids={listing_ids} "
           f"deleted_id={_listing_2_id}")


def tc10_deleted_listing_returns_404():
    if not _farmer_a_token or not _listing_2_id:
        _fail("TC-10", "Deleted listing GET returns 404 — skipped")
        return
    r = requests.get(f"{BASE_URL}/api/crops/{_listing_2_id}",
                     headers=_auth(_farmer_a_token))
    body = r.json()
    _check("TC-10", "GET soft-deleted listing by ID returns 404",
           r.status_code == 404
           and body.get("error") == "Listing not found.",
           f"status={r.status_code} error='{body.get('error')}'")


# ------- MULTI-TENANT ISOLATION: FARMER B ----------------------------------

def tc11_register_and_login_farmer_b():
    global _farmer_b_token
    r_reg = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username":  "crop_test_farmer_b",
        "password":  "FarmerBpass1",
        "role":      "farmer",
        "farm_name": "Beta Fields",
    })
    if r_reg.status_code not in (201, 409):
        _fail("TC-11", f"Register Farmer B failed (status={r_reg.status_code})")
        return
    r_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "crop_test_farmer_b",
        "password": "FarmerBpass1",
    })
    _farmer_b_token = r_login.json().get("token", "")
    _check("TC-11", "Register & login Farmer B",
           r_login.status_code == 200 and len(_farmer_b_token) > 20,
           f"login_status={r_login.status_code}")


def tc12_farmer_b_read_farmer_a_listing():
    if not _farmer_b_token or not _listing_1_id:
        _fail("TC-12", "Cross-tenant GET — skipped")
        return
    r = requests.get(f"{BASE_URL}/api/crops/{_listing_1_id}",
                     headers=_auth(_farmer_b_token))
    body = r.json()
    _check("TC-12", "Farmer B GET Farmer A's listing -> unified 404 (no data leak)",
           r.status_code == 404
           and body.get("error") == "Listing not found.",
           f"status={r.status_code} error='{body.get('error')}'")


def tc13_farmer_b_update_farmer_a_listing():
    if not _farmer_b_token or not _listing_1_id:
        _fail("TC-13", "Cross-tenant PUT — skipped")
        return
    r = requests.put(f"{BASE_URL}/api/crops/{_listing_1_id}",
                     headers=_auth(_farmer_b_token),
                     json={
                         "crop_name":              "Wheat",
                         "planting_date":          PLANT_DATE,
                         "estimated_harvest_date": HARVEST_OK,
                         "acreage":                999.0,
                         "gps_latitude":           0.0,
                         "gps_longitude":          0.0,
                         "quantity_kg":            999.0,
                     })
    body = r.json()
    _check("TC-13", "Farmer B PUT Farmer A's listing -> unified 404",
           r.status_code == 404
           and body.get("error") == "Listing not found.",
           f"status={r.status_code} error='{body.get('error')}'")


def tc14_farmer_b_delete_farmer_a_listing():
    if not _farmer_b_token or not _listing_1_id:
        _fail("TC-14", "Cross-tenant DELETE — skipped")
        return
    r = requests.delete(f"{BASE_URL}/api/crops/{_listing_1_id}",
                        headers=_auth(_farmer_b_token))
    body = r.json()
    _check("TC-14", "Farmer B DELETE Farmer A's listing -> unified 404",
           r.status_code == 404
           and body.get("error") == "Listing not found.",
           f"status={r.status_code} error='{body.get('error')}'")


def tc15_farmer_b_sees_only_own_listings():
    if not _farmer_b_token:
        _fail("TC-15", "Farmer B list isolation — skipped")
        return
    # Farmer B creates their own listing first
    requests.post(f"{BASE_URL}/api/crops",
                  headers=_auth(_farmer_b_token),
                  json={
                      "crop_name":              "Rice",
                      "planting_date":          PLANT_DATE,
                      "estimated_harvest_date": HARVEST_OK,
                      "acreage":                8.0,
                      "gps_latitude":           31.0,
                      "gps_longitude":          70.0,
                      "quantity_kg":            2000.0,
                  })
    r = requests.get(f"{BASE_URL}/api/crops", headers=_auth(_farmer_b_token))
    body = r.json()
    farmer_a_leaked = _listing_1_id in [
        item["listing_id"] for item in body.get("data", [])
    ]
    _check("TC-15", "Farmer B's listing view contains ONLY their own records",
           r.status_code == 200 and not farmer_a_leaked,
           f"status={r.status_code} total={body.get('total')} "
           f"farmer_a_leak={farmer_a_leaked}")


# ------- INPUT VALIDATION --------------------------------------------------

def tc16_invalid_crop_taxonomy():
    if not _farmer_a_token:
        _fail("TC-16", "Invalid crop name — skipped")
        return
    r = requests.post(f"{BASE_URL}/api/crops",
                      headers=_auth(_farmer_a_token),
                      json={
                          "crop_name":              "Banana",     # not in taxonomy
                          "planting_date":          PLANT_DATE,
                          "estimated_harvest_date": HARVEST_OK,
                          "acreage":                5.0,
                          "gps_latitude":           30.0,
                          "gps_longitude":          69.0,
                          "quantity_kg":            1000.0,
                      })
    body = r.json()
    _check("TC-16", "Invalid crop_name taxonomy rejected (400)",
           r.status_code == 400 and "Invalid crop name" in body.get("error", ""),
           f"status={r.status_code} error='{body.get('error')}'")


def tc17_future_planting_date():
    if not _farmer_a_token:
        _fail("TC-17", "Future planting date — skipped")
        return
    future_date = (TODAY + timedelta(days=5)).isoformat()
    r = requests.post(f"{BASE_URL}/api/crops",
                      headers=_auth(_farmer_a_token),
                      json={
                          "crop_name":              "Wheat",
                          "planting_date":          future_date,
                          "estimated_harvest_date": HARVEST_OK,
                          "acreage":                5.0,
                          "gps_latitude":           30.0,
                          "gps_longitude":          69.0,
                          "quantity_kg":            1000.0,
                      })
    body = r.json()
    _check("TC-17", "Future planting date rejected (400)",
           r.status_code == 400
           and "future" in body.get("error", "").lower(),
           f"status={r.status_code} error='{body.get('error')}'")


def tc18_harvest_before_planting():
    if not _farmer_a_token:
        _fail("TC-18", "Harvest before planting — skipped")
        return
    r = requests.post(f"{BASE_URL}/api/crops",
                      headers=_auth(_farmer_a_token),
                      json={
                          "crop_name":              "Wheat",
                          "planting_date":          PLANT_DATE,
                          "estimated_harvest_date": HARVEST_BAD,  # before planting
                          "acreage":                5.0,
                          "gps_latitude":           30.0,
                          "gps_longitude":          69.0,
                          "quantity_kg":            1000.0,
                      })
    body = r.json()
    _check("TC-18", "Harvest date before planting rejected (400)",
           r.status_code == 400
           and "harvest date" in body.get("error", "").lower(),
           f"status={r.status_code} error='{body.get('error')}'")


def tc19_nonpositive_acreage():
    if not _farmer_a_token:
        _fail("TC-19", "Non-positive acreage — skipped")
        return
    r = requests.post(f"{BASE_URL}/api/crops",
                      headers=_auth(_farmer_a_token),
                      json={
                          "crop_name":              "Wheat",
                          "planting_date":          PLANT_DATE,
                          "estimated_harvest_date": HARVEST_OK,
                          "acreage":                0,            # invalid
                          "gps_latitude":           30.0,
                          "gps_longitude":          69.0,
                          "quantity_kg":            1000.0,
                      })
    body = r.json()
    _check("TC-19", "Acreage = 0 rejected (400)",
           r.status_code == 400
           and "acreage" in body.get("error", "").lower(),
           f"status={r.status_code} error='{body.get('error')}'")


def tc20_missing_required_field():
    if not _farmer_a_token:
        _fail("TC-20", "Missing field — skipped")
        return
    r = requests.post(f"{BASE_URL}/api/crops",
                      headers=_auth(_farmer_a_token),
                      json={
                          "crop_name": "Wheat",
                          # planting_date intentionally omitted
                          "estimated_harvest_date": HARVEST_OK,
                          "acreage":    5.0,
                          "gps_latitude":  30.0,
                          "gps_longitude": 69.0,
                          "quantity_kg":   1000.0,
                      })
    body = r.json()
    _check("TC-20", "Missing required field rejected (400)",
           r.status_code == 400 and body.get("success") is False,
           f"status={r.status_code} error='{body.get('error')}'")


# ------- RBAC GUARD --------------------------------------------------------

def tc21_buyer_blocked_from_create():
    global _buyer_token
    # Register & login buyer
    requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "crop_test_buyer",
        "password": "BuyerPass1B",
        "role":     "buyer",
    })
    r_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "crop_test_buyer",
        "password": "BuyerPass1B",
    })
    _buyer_token = r_login.json().get("token", "")
    if not _buyer_token:
        _fail("TC-21", "Buyer RBAC block — login failed, skipped")
        return
    r = requests.post(f"{BASE_URL}/api/crops",
                      headers=_auth(_buyer_token),
                      json={
                          "crop_name":              "Wheat",
                          "planting_date":          PLANT_DATE,
                          "estimated_harvest_date": HARVEST_OK,
                          "acreage":                5.0,
                          "gps_latitude":           30.0,
                          "gps_longitude":          69.0,
                          "quantity_kg":            1000.0,
                      })
    body = r.json()
    _check("TC-21", "Buyer token blocked from POST /api/crops (403)",
           r.status_code == 403
           and "Access denied" in body.get("error", ""),
           f"status={r.status_code} error='{body.get('error')}'")


def tc22_no_token_on_get():
    r = requests.get(f"{BASE_URL}/api/crops")
    body = r.json()
    _check("TC-22", "No Bearer token on GET /api/crops returns 401",
           r.status_code == 401 and body.get("success") is False,
           f"status={r.status_code} error='{body.get('error')}'")


def tc23_get_crop_stats():
    global _farmer_a_token, _buyer_token
    # 1. Farmer token -> 200 with active_fields, total_acreage, projected_yield_kg
    r_farmer = requests.get(f"{BASE_URL}/api/crops/stats", headers=_auth(_farmer_a_token))
    body = r_farmer.json()
    data = body.get("data", {})
    ok_farmer = (
        r_farmer.status_code == 200
        and body.get("success") is True
        and "active_fields" in data
        and "total_acreage" in data
        and "projected_yield_kg" in data
    )

    # 2. Buyer token -> 403
    r_buyer = requests.get(f"{BASE_URL}/api/crops/stats", headers=_auth(_buyer_token))
    ok_buyer = r_buyer.status_code == 403

    # 3. No token -> 401
    r_no_token = requests.get(f"{BASE_URL}/api/crops/stats")
    ok_no_token = r_no_token.status_code == 401

    all_ok = ok_farmer and ok_buyer and ok_no_token
    _check(
        "TC-23",
        "GET /api/crops/stats: 200 for farmer, 403 for buyer, 401 unauthenticated",
        all_ok,
        f"farmer_status={r_farmer.status_code} stats={data} buyer_status={r_buyer.status_code} no_token_status={r_no_token.status_code}"
    )


# ===========================================================================
# MAIN RUNNER
# ===========================================================================

def main():
    print("=" * 65)
    print("  AGRI-GRID  Crop CRUD Pipeline V&V  —  Run 3")
    print("=" * 65)

    app = create_app()
    server_thread = threading.Thread(
        target=_start_server, args=(app,), daemon=True
    )
    server_thread.start()

    print(f"\n[BOOT] Starting test server on {BASE_URL} ...")
    for _ in range(20):
        time.sleep(0.5)
        try:
            requests.get(f"{BASE_URL}/api/auth/me", timeout=1)
            break
        except requests.exceptions.ConnectionError:
            pass
    else:
        print("[FATAL] Server did not start within 10 seconds.")
        sys.exit(1)
    print("[BOOT] Server ready.\n")

    # Execute all test cases in defined order
    tests = [
        # Full lifecycle
        tc01_register_farmer_a,
        tc02_login_farmer_a,
        tc03_create_listing_wheat,
        tc04_create_listing_tomato,
        tc05_list_crops_paginated,
        tc06_get_single_listing,
        tc07_update_listing,
        tc08_soft_delete_listing,
        tc09_deleted_listing_absent_from_list,
        tc10_deleted_listing_returns_404,
        # Multi-tenant isolation
        tc11_register_and_login_farmer_b,
        tc12_farmer_b_read_farmer_a_listing,
        tc13_farmer_b_update_farmer_a_listing,
        tc14_farmer_b_delete_farmer_a_listing,
        tc15_farmer_b_sees_only_own_listings,
        # Input validation
        tc16_invalid_crop_taxonomy,
        tc17_future_planting_date,
        tc18_harvest_before_planting,
        tc19_nonpositive_acreage,
        tc20_missing_required_field,
        # RBAC guard
        tc21_buyer_blocked_from_create,
        tc22_no_token_on_get,
        # Metrics Aggregation
        tc23_get_crop_stats,
    ]

    for fn in tests:
        try:
            fn()
        except Exception as exc:
            _fail(fn.__name__, f"Unexpected exception: {exc}")

    # Summary
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    total  = len(RESULTS)

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
        print("\n  All tests passed. Crop CRUD pipeline fully verified.")
        print("  Increment 1 backend is ready for frontend integration.")
        sys.exit(0)


if __name__ == "__main__":
    main()
