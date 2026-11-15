"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    test_marketplace_api.py
Module:  B2B Marketplace & Commercial Pricing API Self-Verification (Increment 2 Phase 2 V&V)
Version: 2.0  (Increment 2 — Core Data Engine & Demand Side)
Author:  Muhammad Hashir (QA & DevOps Engineer)
Date:    2026-11-15
Source:  AG-API-INC2-003 v1.1 Endpoints 1, 2, 3, 4, 13 | AG-SRS-INC2-001 v1.2 | Phase 2 Build Package Part E

Test Coverage
-------------
  Buyer Onboarding (TC-BYR)
    TC-BYR-01  POST /api/auth/register  — Register new buyer with full company profile (201 + Rs. 500k wallet)
    TC-BYR-02  POST /api/auth/login     — Login as new buyer; verify JWT claims (buyer_id set, farmer_id null) + user profile
    TC-BYR-03  POST /api/auth/login     — Login as seeded Sara Buyer; verify claims & profile
    TC-BYR-04  POST /api/auth/register  — Register missing warehouse_address rejected (400)
    TC-BYR-05  POST /api/auth/register  — Duplicate buyer username rejected (409)
    TC-BYR-06  POST /api/auth/register  — Farmer registration still functions per Increment 1 baseline (201)

  Marketplace Procurement Catalog (TC-MKT)
    TC-MKT-01  Setup & Visibility       — Tahir prices Wheat (1); leaves Tomato unpriced (2); Sara & Tahir see priced Wheat, Tomato absent
    TC-MKT-02  Filter: crop_name        — Filtering by crop_name narrows result set to matching crop only
    TC-MKT-03  Filter: max_price        — Filtering with max_price below listing price returns empty result set
    TC-MKT-04  Sorting & Envelope       — sort=price_asc and price_desc correctly order >= 3 listings; envelope matches {success, data, page, limit, total}
    TC-MKT-05  GET /api/marketplace/listings/<id> — Detail endpoint returns 200 with all Contracts Endpoint 4 fields
    TC-MKT-06  GET /api/marketplace/listings/<id> — Unpriced, Sold, soft-deleted, and non-existent listings return unified 404
    TC-MKT-07  RBAC Guard: Transporter — Transporter role receives 403 "Access denied." on marketplace catalog & detail
    TC-MKT-08  RBAC Guard: No Token    — Unauthenticated request receives 401 "Authentication required. Please log in."

  Commercial Pricing & Batch Assignment (TC-PRC)
    TC-PRC-01  PUT /api/crops/<id>      — Pricing unpriced listing generates valid batch_id matching format BATCH-{YYYY}-{CODE}-{ID:04d}
    TC-PRC-02  PUT /api/crops/<id>      — Re-pricing preserves existing batch_id (immutable)
    TC-PRC-03  PUT /api/crops/<id>      — Updating crop without asking_price_per_kg leaves existing price and batch_id unchanged
    TC-PRC-04  PUT /api/crops/<id>      — Invalid prices (0, -5, "abc") rejected with 400
    TC-PRC-05  PUT /api/crops/<id>      — Non-owner farmer updating price receives unified 404 "Listing not found."

Usage
-----
  python backend/test_marketplace_api.py       (from project root)
  python test_marketplace_api.py               (from backend/ directory)
"""

import os
import re
import sys
import time
import threading
import sqlite3
import jwt
import requests
from datetime import date, timedelta

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
TEST_PORT = int(os.environ.get("AGRIGRID_TEST_PORT", "5003"))
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

# Auth tokens
_new_buyer_token: str = ""
_new_buyer_id: int = 0
_sara_token: str = ""
_tahir_token: str = ""
_transporter_token: str = ""
_farmer_b_token: str = ""

# Listing references
_wheat_listing_id: int = 1
_tomato_listing_id: int = 2
_aux_listing_ids: list[int] = []

TODAY = date.today()
PLANT_DATE = (TODAY - timedelta(days=30)).isoformat()
HARVEST_DATE = (TODAY + timedelta(days=90)).isoformat()


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
    # Check if a server is already answering on API_BASE_URL
    if _probe_server(API_BASE_URL, timeout=1.0):
        print(f"[BOOT] Target server already active on {API_BASE_URL}")
        return

    # Check if port 5000 is active
    if _probe_server("http://127.0.0.1:5000/api", timeout=1.0):
        API_BASE_URL = "http://127.0.0.1:5000/api"
        print(f"[BOOT] Connected to active server on {API_BASE_URL}")
        return

    # Otherwise, launch dedicated background test server
    print(f"[BOOT] Starting dedicated test server on http://{TEST_HOST}:{TEST_PORT} ...")
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


# ===========================================================================
# 1. BUYER ONBOARDING (TC-BYR)
# ===========================================================================

def tc_byr_01_register_new_buyer():
    """Register new buyer -> 201, 500k wallet, verified in DB."""
    global _new_buyer_token
    username = f"buyer_qa_{RUN_TIMESTAMP}"
    payload = {
        "username": username,
        "password": "BuyerSecurePass1!",
        "role": "buyer",
        "company_name": "Indus Logistics & Food Hub",
        "contact_phone": "+92-300-9876543",
        "warehouse_address": "Plot 42, Multan Road Industrial Estate, Lahore",
        "warehouse_gps_latitude": 31.4501,
        "warehouse_gps_longitude": 74.2802,
    }

    r = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
    data = r.json()

    # Verify HTTP response
    status_ok = r.status_code == 201
    msg_ok = data.get("message") == "Buyer registration successful. Please log in."
    user_obj = data.get("user", {})
    wallet_ok = float(user_obj.get("wallet_balance_pkr", 0.0)) == 500000.00
    user_id = user_obj.get("user_id")

    # Verify physical database persistence
    conn = _get_db_conn()
    buyer_row = conn.execute(
        "SELECT b.id, b.company_name, bw.balance_pkr FROM buyers b "
        "JOIN buyer_wallets bw ON bw.buyer_id = b.id "
        "WHERE b.user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    db_ok = (
        buyer_row is not None
        and buyer_row["company_name"] == "Indus Logistics & Food Hub"
        and float(buyer_row["balance_pkr"]) == 500000.00
    )

    _check(
        "TC-BYR-01",
        "Register buyer returns 201, initial 500k balance, and persists to DB",
        status_ok and msg_ok and wallet_ok and db_ok,
        f"status={r.status_code} msg='{data.get('message')}' wallet={user_obj.get('wallet_balance_pkr')} db_ok={db_ok}",
    )


def tc_byr_02_login_new_buyer():
    """Login as new buyer -> JWT carries buyer_id (int) and farmer_id null; user carries company + wallet."""
    global _new_buyer_token, _new_buyer_id
    username = f"buyer_qa_{RUN_TIMESTAMP}"
    r = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": username, "password": "BuyerSecurePass1!"},
    )
    data = r.json()

    status_ok = r.status_code == 200
    token = data.get("token", "")
    _new_buyer_token = token

    # Decode JWT payload
    payload = jwt.decode(token, options={"verify_signature": False})
    claims_ok = (
        isinstance(payload.get("buyer_id"), int)
        and payload.get("farmer_id") is None
        and payload.get("role") == "buyer"
    )
    _new_buyer_id = payload.get("buyer_id", 0)

    user_obj = data.get("user", {})
    profile_ok = (
        user_obj.get("company_name") == "Indus Logistics & Food Hub"
        and float(user_obj.get("wallet_balance_pkr", 0.0)) == 500000.00
    )

    _check(
        "TC-BYR-02",
        "Buyer login JWT carries buyer_id & null farmer_id; user body carries company and wallet",
        status_ok and claims_ok and profile_ok,
        f"status={r.status_code} claims={payload} company='{user_obj.get('company_name')}'",
    )


def tc_byr_03_login_sara_seeded_buyer():
    """Sara seeded buyer login carries buyer_id, company name, and 500k wallet."""
    global _sara_token
    r = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": "sara_buyer", "password": "BuyerPass1"},
    )
    data = r.json()

    status_ok = r.status_code == 200
    _sara_token = data.get("token", "")
    payload = jwt.decode(_sara_token, options={"verify_signature": False})

    claims_ok = (
        isinstance(payload.get("buyer_id"), int)
        and payload.get("farmer_id") is None
        and payload.get("role") == "buyer"
    )

    user_obj = data.get("user", {})
    profile_ok = (
        user_obj.get("company_name") == "Metro Wholesale Foods"
        and float(user_obj.get("wallet_balance_pkr", 0.0)) == 500000.00
    )

    _check(
        "TC-BYR-03",
        "Seeded Sara login carries buyer_id claim, Metro Wholesale Foods, and 500k balance",
        status_ok and claims_ok and profile_ok,
        f"status={r.status_code} buyer_id={payload.get('buyer_id')} company='{user_obj.get('company_name')}'",
    )


def tc_byr_04_buyer_missing_required_fields():
    """Register buyer missing warehouse_address -> 400 with exact error message."""
    payload = {
        "username": f"bad_buyer_{RUN_TIMESTAMP}",
        "password": "BuyerSecurePass1!",
        "role": "buyer",
        "company_name": "Missing Address Wholesale",
        "contact_phone": "+92-300-1112233",
        # warehouse_address omitted
    }
    r = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
    data = r.json()

    status_ok = r.status_code == 400
    err_ok = data.get("error") == "Company name, phone, and warehouse address are required."

    _check(
        "TC-BYR-04",
        "Register buyer missing warehouse_address rejected (400)",
        status_ok and err_ok,
        f"status={r.status_code} error='{data.get('error')}'",
    )


def tc_byr_05_buyer_duplicate_username():
    """Register buyer with existing username -> 409 'Username already exists.'"""
    payload = {
        "username": "sara_buyer",  # already exists
        "password": "BuyerSecurePass1!",
        "role": "buyer",
        "company_name": "Imposter Co",
        "contact_phone": "+92-300-9999999",
        "warehouse_address": "Somewhere Else",
    }
    r = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
    data = r.json()

    status_ok = r.status_code == 409
    err_ok = data.get("error") == "Username already exists."

    _check(
        "TC-BYR-05",
        "Duplicate buyer username rejected with 409 'Username already exists.'",
        status_ok and err_ok,
        f"status={r.status_code} error='{data.get('error')}'",
    )


def tc_byr_06_farmer_registration_regression():
    """Farmer registration continues to work identically to Increment 1 baseline."""
    username = f"reg_farmer_{RUN_TIMESTAMP}"
    payload = {
        "username": username,
        "password": "FarmerSecurePass1!",
        "role": "farmer",
        "farm_name": "Sunrise Organic Orchards",
    }
    r = requests.post(f"{API_BASE_URL}/auth/register", json=payload)
    data = r.json()

    status_ok = r.status_code == 201
    msg_ok = "Registration successful" in data.get("message", "")
    farmer_id = data.get("user", {}).get("farmer_id")

    _check(
        "TC-BYR-06",
        "Farmer registration still works cleanly (201 + farmer_id assigned)",
        status_ok and msg_ok and (farmer_id is not None),
        f"status={r.status_code} farmer_id={farmer_id}",
    )


# ===========================================================================
# 2. MARKETPLACE CATALOG (TC-MKT)
# ===========================================================================

def tc_mkt_01_pricing_setup_and_visibility():
    """Tahir prices Wheat (1); leaves Tomato unpriced (2); Sara and Tahir see Wheat, Tomato absent."""
    global _tahir_token
    # 1. Login Tahir
    r_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": "tahir_farmer", "password": "FarmSecure1"},
    )
    _tahir_token = r_login.json().get("token", "")

    # Ensure Tomato (listing 2) is unpriced
    conn = _get_db_conn()
    conn.execute("UPDATE listings SET asking_price_per_kg = NULL, batch_id = NULL WHERE id = 2")
    conn.commit()
    conn.close()

    # 2. Tahir sets commercial price on Wheat listing 1 (Rs. 45.00/kg)
    r_put = requests.put(
        f"{API_BASE_URL}/crops/1",
        headers=_auth(_tahir_token),
        json={"asking_price_per_kg": 45.0},
    )
    put_data = r_put.json()
    batch_id = put_data.get("data", {}).get("batch_id")

    # 3. Query catalog as Sara Buyer
    r_sara = requests.get(
        f"{API_BASE_URL}/marketplace/listings",
        headers=_auth(_sara_token),
    )
    sara_data = r_sara.json()
    items = sara_data.get("data", [])
    wheat_items = [it for it in items if it.get("listing_id") == 1]
    tomato_items = [it for it in items if it.get("listing_id") == 2]

    wheat_visible = len(wheat_items) == 1
    tomato_absent = len(tomato_items) == 0

    wheat_record = wheat_items[0] if wheat_items else {}
    expected_total_price = float(wheat_record.get("quantity_kg", 0)) * 45.00
    math_ok = float(wheat_record.get("total_price_pkr", 0.0)) == expected_total_price

    # 4. Query catalog as Tahir Farmer (market transparency)
    r_tahir = requests.get(
        f"{API_BASE_URL}/marketplace/listings",
        headers=_auth(_tahir_token),
    )
    tahir_ok = r_tahir.status_code == 200 and r_tahir.json().get("success") is True

    _check(
        "TC-MKT-01",
        "Catalog setup: Tahir's priced Wheat present with batch & total_price; Tomato absent; visible to buyer & farmer",
        r_put.status_code == 200 and wheat_visible and tomato_absent and math_ok and tahir_ok,
        f"put_status={r_put.status_code} batch='{batch_id}' wheat_visible={wheat_visible} tomato_absent={tomato_absent} tahir_status={r_tahir.status_code}",
    )


def tc_mkt_02_crop_name_filter():
    """crop_name=Wheat filter narrows catalog to Wheat items only."""
    r = requests.get(
        f"{API_BASE_URL}/marketplace/listings?crop_name=Wheat",
        headers=_auth(_sara_token),
    )
    data = r.json()
    items = data.get("data", [])
    all_wheat = len(items) > 0 and all(it.get("crop_name") == "Wheat" for it in items)

    _check(
        "TC-MKT-02",
        "Catalog filter crop_name=Wheat returns strictly Wheat produce listings",
        r.status_code == 200 and all_wheat,
        f"status={r.status_code} count={len(items)} all_wheat={all_wheat}",
    )


def tc_mkt_03_max_price_filter():
    """max_price below Wheat price (e.g. 40.0 < 45.0) empties the result set."""
    r = requests.get(
        f"{API_BASE_URL}/marketplace/listings?crop_name=Wheat&max_price=40.0",
        headers=_auth(_sara_token),
    )
    data = r.json()
    items = data.get("data", [])
    total = data.get("total", -1)

    _check(
        "TC-MKT-03",
        "Catalog filter max_price=40.0 below asking price (45.0) yields empty result set",
        r.status_code == 200 and len(items) == 0 and total == 0,
        f"status={r.status_code} count={len(items)} total={total}",
    )


def tc_mkt_04_sorting_and_list_envelope():
    """sort=price_asc and sort=price_desc correctly order >= 3 listings; envelope matches standard."""
    global _aux_listing_ids
    # Create 3 distinct listings with varying prices for Tahir
    prices = [30.0, 85.0, 60.0]
    crops = ["Potato", "Rice", "Maize"]
    _aux_listing_ids = []

    for c_name, p_val in zip(crops, prices):
        r_create = requests.post(
            f"{API_BASE_URL}/crops",
            headers=_auth(_tahir_token),
            json={
                "crop_name": c_name,
                "planting_date": PLANT_DATE,
                "estimated_harvest_date": HARVEST_DATE,
                "acreage": 5.0,
                "gps_latitude": 30.1,
                "gps_longitude": 72.2,
                "quantity_kg": 1000.0,
            },
        )
        if r_create.status_code == 201:
            listing_id = r_create.json()["data"]["listing_id"]
            _aux_listing_ids.append(listing_id)
            # Apply commercial asking price via PUT
            requests.put(
                f"{API_BASE_URL}/crops/{listing_id}",
                headers=_auth(_tahir_token),
                json={"asking_price_per_kg": p_val},
            )

    # 1. Test price_asc
    r_asc = requests.get(
        f"{API_BASE_URL}/marketplace/listings?sort=price_asc",
        headers=_auth(_sara_token),
    )
    data_asc = r_asc.json()
    items_asc = data_asc.get("data", [])
    prices_asc = [it["asking_price_per_kg"] for it in items_asc]
    is_asc = prices_asc == sorted(prices_asc) and len(prices_asc) >= 3

    # 2. Test price_desc
    r_desc = requests.get(
        f"{API_BASE_URL}/marketplace/listings?sort=price_desc",
        headers=_auth(_sara_token),
    )
    data_desc = r_desc.json()
    items_desc = data_desc.get("data", [])
    prices_desc = [it["asking_price_per_kg"] for it in items_desc]
    is_desc = prices_desc == sorted(prices_desc, reverse=True) and len(prices_desc) >= 3

    # 3. Check exact envelope keys
    keys = set(data_asc.keys())
    expected_keys = {"success", "data", "page", "limit", "total"}
    keys_ok = keys == expected_keys
    total_ok = data_asc.get("total") == len(items_asc)

    _check(
        "TC-MKT-04",
        "Catalog sort=price_asc/desc orders >= 3 listings; envelope keys exact {success, data, page, limit, total}",
        r_asc.status_code == 200 and r_desc.status_code == 200 and is_asc and is_desc and keys_ok and total_ok,
        f"is_asc={is_asc} is_desc={is_desc} keys_match={keys_ok} total={data_asc.get('total')}",
    )


def tc_mkt_05_listing_detail_success():
    """GET /api/marketplace/listings/1 returns 200 with all Contracts Endpoint 4 fields."""
    r = requests.get(
        f"{API_BASE_URL}/marketplace/listings/1",
        headers=_auth(_sara_token),
    )
    data = r.json()
    status_ok = r.status_code == 200
    record = data.get("data", {})

    expected_fields = [
        "listing_id",
        "batch_id",
        "farmer_id",
        "crop_name",
        "acreage",
        "quantity_kg",
        "asking_price_per_kg",
        "total_price_pkr",
        "planting_date",
        "estimated_harvest_date",
        "status",
        "farm_name",
        "farm_location",
        "gps_latitude",
        "gps_longitude",
        "created_at",
    ]
    missing_fields = [f for f in expected_fields if f not in record]

    _check(
        "TC-MKT-05",
        "Single listing detail returns HTTP 200 with full Endpoint 4 contract payload",
        status_ok and len(missing_fields) == 0,
        f"status={r.status_code} missing_fields={missing_fields} batch_id='{record.get('batch_id')}'",
    )


def tc_mkt_06_listing_detail_unified_404():
    """Unpriced, Sold, soft-deleted, and non-existent IDs all return unified 404 'Listing not found.'"""
    conn = _get_db_conn()
    try:
        # 1. Unpriced listing: listing 2 is unpriced
        r_unpriced = requests.get(f"{API_BASE_URL}/marketplace/listings/2", headers=_auth(_sara_token))

        # 2. Sold listing: create one in 'Sold' status
        cursor = conn.execute(
            "INSERT INTO listings (farmer_id, crop_name, planting_date, estimated_harvest_date, acreage, "
            "gps_latitude, gps_longitude, quantity_kg, status, asking_price_per_kg, batch_id, is_deleted) "
            "VALUES (1, 'Wheat', '2026-09-01', '2027-01-15', 5.0, 30.0444, 72.3441, 2000.0, 'Sold', 45.0, 'BATCH-2026-WHT-9901', 0)"
        )
        sold_id = cursor.lastrowid

        # 3. Soft-deleted listing
        cursor = conn.execute(
            "INSERT INTO listings (farmer_id, crop_name, planting_date, estimated_harvest_date, acreage, "
            "gps_latitude, gps_longitude, quantity_kg, status, asking_price_per_kg, batch_id, is_deleted) "
            "VALUES (1, 'Tomato', '2026-09-01', '2027-01-15', 3.0, 30.0444, 72.3441, 1500.0, 'Active', 50.0, 'BATCH-2026-TOM-9902', 1)"
        )
        deleted_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()

    r_sold = requests.get(f"{API_BASE_URL}/marketplace/listings/{sold_id}", headers=_auth(_sara_token))
    r_deleted = requests.get(f"{API_BASE_URL}/marketplace/listings/{deleted_id}", headers=_auth(_sara_token))
    r_nonexistent = requests.get(f"{API_BASE_URL}/marketplace/listings/999999", headers=_auth(_sara_token))

    expected_err = "Listing not found."
    all_404 = (
        r_unpriced.status_code == 404 and r_unpriced.json().get("error") == expected_err
        and r_sold.status_code == 404 and r_sold.json().get("error") == expected_err
        and r_deleted.status_code == 404 and r_deleted.json().get("error") == expected_err
        and r_nonexistent.status_code == 404 and r_nonexistent.json().get("error") == expected_err
    )

    _check(
        "TC-MKT-06",
        "Unpriced, Sold, soft-deleted, and non-existent listings all return unified 404 'Listing not found.'",
        all_404,
        f"unpriced={r_unpriced.status_code} sold={r_sold.status_code} deleted={r_deleted.status_code} nonexistent={r_nonexistent.status_code}",
    )


def tc_mkt_07_transporter_role_forbidden():
    """Transporter token receives 403 'Access denied.' on both marketplace endpoints."""
    global _transporter_token
    # Register and login transporter
    t_user = f"transporter_qa_{RUN_TIMESTAMP}"
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": t_user, "password": "TransporterPass1!", "role": "transporter"},
    )
    r_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": t_user, "password": "TransporterPass1!"},
    )
    _transporter_token = r_login.json().get("token", "")

    r_browse = requests.get(f"{API_BASE_URL}/marketplace/listings", headers=_auth(_transporter_token))
    r_detail = requests.get(f"{API_BASE_URL}/marketplace/listings/1", headers=_auth(_transporter_token))

    browse_403 = r_browse.status_code == 403 and r_browse.json().get("error") == "Access denied."
    detail_403 = r_detail.status_code == 403 and r_detail.json().get("error") == "Access denied."

    _check(
        "TC-MKT-07",
        "Transporter role blocked with 403 'Access denied.' on catalog and detail endpoints",
        browse_403 and detail_403,
        f"browse_status={r_browse.status_code} detail_status={r_detail.status_code}",
    )


def tc_mkt_08_unauthenticated_requests():
    """No token on marketplace endpoints returns HTTP 401."""
    r_browse = requests.get(f"{API_BASE_URL}/marketplace/listings")
    r_detail = requests.get(f"{API_BASE_URL}/marketplace/listings/1")

    expected_err = "Authentication required. Please log in."
    browse_401 = r_browse.status_code == 401 and r_browse.json().get("error") == expected_err
    detail_401 = r_detail.status_code == 401 and r_detail.json().get("error") == expected_err

    _check(
        "TC-MKT-08",
        "Unauthenticated catalog & detail requests return 401 'Authentication required. Please log in.'",
        browse_401 and detail_401,
        f"browse={r_browse.status_code} detail={r_detail.status_code}",
    )


# ===========================================================================
# 3. COMMERCIAL PRICING & BATCH ASSIGNMENT (TC-PRC)
# ===========================================================================

def tc_prc_01_pricing_generates_batch_id():
    """PUT price on an unpriced listing -> 200; batch_id matches regex and zero-padded ID."""
    # Create fresh unpriced listing for Tahir
    r_create = requests.post(
        f"{API_BASE_URL}/crops",
        headers=_auth(_tahir_token),
        json={
            "crop_name": "Tomato",
            "planting_date": PLANT_DATE,
            "estimated_harvest_date": HARVEST_DATE,
            "acreage": 4.0,
            "gps_latitude": 30.2,
            "gps_longitude": 72.4,
            "quantity_kg": 2000.0,
        },
    )
    listing_id = r_create.json()["data"]["listing_id"]

    # PUT commercial price Rs. 80.00/kg
    r_put = requests.put(
        f"{API_BASE_URL}/crops/{listing_id}",
        headers=_auth(_tahir_token),
        json={"asking_price_per_kg": 80.0},
    )
    data = r_put.json()
    status_ok = r_put.status_code == 200
    batch_id = data.get("data", {}).get("batch_id", "")

    # Match format ^BATCH-\d{4}-(WHT|RIC|TOM|POT|COT|MAI|SUG|OTH)-\d{4}$
    pattern = r"^BATCH-\d{4}-(WHT|RIC|TOM|POT|COT|MAI|SUG|OTH)-\d{4}$"
    pattern_ok = bool(re.match(pattern, batch_id))
    expected_suffix = f"{listing_id:04d}"
    suffix_ok = batch_id.endswith(expected_suffix)

    _check(
        "TC-PRC-01",
        "Setting price on unpriced listing generates valid batch_id with zero-padded listing id",
        status_ok and pattern_ok and suffix_ok,
        f"status={r_put.status_code} batch_id='{batch_id}' expected_suffix='{expected_suffix}'",
    )


def tc_prc_02_batch_id_immutability():
    """A second PUT changing only the price leaves batch_id byte-identical."""
    # Price Wheat listing 1 to 48.0
    r1 = requests.get(f"{API_BASE_URL}/crops/1", headers=_auth(_tahir_token))
    original_batch = r1.json().get("data", {}).get("batch_id")

    r2 = requests.put(
        f"{API_BASE_URL}/crops/1",
        headers=_auth(_tahir_token),
        json={"asking_price_per_kg": 52.0},
    )
    new_batch = r2.json().get("data", {}).get("batch_id")
    batch_immutable = (original_batch == new_batch) and bool(new_batch)

    _check(
        "TC-PRC-02",
        "Updating price on an already-batched listing preserves batch_id byte-identical",
        r2.status_code == 200 and batch_immutable,
        f"original='{original_batch}' after_update='{new_batch}'",
    )


def tc_prc_03_put_without_price_preserves_values():
    """PUT with no price field leaves asking_price_per_kg and batch_id unchanged."""
    r_before = requests.get(f"{API_BASE_URL}/crops/1", headers=_auth(_tahir_token))
    before_data = r_before.json().get("data", {})
    p_before = before_data.get("asking_price_per_kg")
    b_before = before_data.get("batch_id")

    # Update only acreage
    r_update = requests.put(
        f"{API_BASE_URL}/crops/1",
        headers=_auth(_tahir_token),
        json={"acreage": 14.0},
    )
    after_data = r_update.json().get("data", {})
    p_after = after_data.get("asking_price_per_kg")
    b_after = after_data.get("batch_id")

    preserved = (p_before == p_after) and (b_before == b_after)

    _check(
        "TC-PRC-03",
        "PUT updating non-price fields leaves existing price and batch_id intact",
        r_update.status_code == 200 and preserved,
        f"price_before={p_before} price_after={p_after} batch_intact={b_before == b_after}",
    )


def tc_prc_04_invalid_prices_rejected():
    """Price 0, -5, and 'abc' rejected with 400 'Asking price per kg must be greater than 0.'"""
    expected_err = "Asking price per kg must be greater than 0."

    r_zero = requests.put(f"{API_BASE_URL}/crops/1", headers=_auth(_tahir_token), json={"asking_price_per_kg": 0})
    r_neg = requests.put(f"{API_BASE_URL}/crops/1", headers=_auth(_tahir_token), json={"asking_price_per_kg": -5})
    r_str = requests.put(f"{API_BASE_URL}/crops/1", headers=_auth(_tahir_token), json={"asking_price_per_kg": "abc"})
    r_bool = requests.put(f"{API_BASE_URL}/crops/1", headers=_auth(_tahir_token), json={"asking_price_per_kg": True})

    all_400 = (
        r_zero.status_code == 400 and r_zero.json().get("error") == expected_err
        and r_neg.status_code == 400 and r_neg.json().get("error") == expected_err
        and r_str.status_code == 400 and r_str.json().get("error") == expected_err
        and r_bool.status_code == 400 and r_bool.json().get("error") == expected_err
    )

    _check(
        "TC-PRC-04",
        "Invalid prices (0, -5, 'abc', boolean) rejected with 400 'Asking price per kg must be greater than 0.'",
        all_400,
        f"zero={r_zero.status_code} neg={r_neg.status_code} str={r_str.status_code} bool={r_bool.status_code}",
    )


def tc_prc_05_non_owner_pricing_rejected():
    """Non-owner farmer PUT with a price returns unified 404 'Listing not found.'"""
    global _farmer_b_token
    # Register Farmer B
    b_user = f"farmer_b_pricing_{RUN_TIMESTAMP}"
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": b_user, "password": "FarmerBPass1!", "role": "farmer", "farm_name": "Valley Farms"},
    )
    r_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": b_user, "password": "FarmerBPass1!"},
    )
    _farmer_b_token = r_login.json().get("token", "")

    # Farmer B attempts to price Tahir's Wheat (listing 1)
    r_put = requests.put(
        f"{API_BASE_URL}/crops/1",
        headers=_auth(_farmer_b_token),
        json={"asking_price_per_kg": 99.0},
    )
    data = r_put.json()
    status_ok = r_put.status_code == 404
    err_ok = data.get("error") == "Listing not found."

    _check(
        "TC-PRC-05",
        "Non-owner farmer attempting to price another farmer's crop returns unified 404 'Listing not found.'",
        status_ok and err_ok,
        f"status={r_put.status_code} error='{data.get('error')}'",
    )


# ===========================================================================
# SUITE MAIN RUNNER
# ===========================================================================

def main():
    print("=" * 65)
    print("  AGRI-GRID  Marketplace & Commercial Pricing API Test Suite")
    print("=" * 65)

    _ensure_server_running()

    tests = [
        # Buyer onboarding (TC-BYR)
        tc_byr_01_register_new_buyer,
        tc_byr_02_login_new_buyer,
        tc_byr_03_login_sara_seeded_buyer,
        tc_byr_04_buyer_missing_required_fields,
        tc_byr_05_buyer_duplicate_username,
        tc_byr_06_farmer_registration_regression,
        # Marketplace procurement catalog (TC-MKT)
        tc_mkt_01_pricing_setup_and_visibility,
        tc_mkt_02_crop_name_filter,
        tc_mkt_03_max_price_filter,
        tc_mkt_04_sorting_and_list_envelope,
        tc_mkt_05_listing_detail_success,
        tc_mkt_06_listing_detail_unified_404,
        tc_mkt_07_transporter_role_forbidden,
        tc_mkt_08_unauthenticated_requests,
        # Commercial pricing & batch assignment (TC-PRC)
        tc_prc_01_pricing_generates_batch_id,
        tc_prc_02_batch_id_immutability,
        tc_prc_03_put_without_price_preserves_values,
        tc_prc_04_invalid_prices_rejected,
        tc_prc_05_non_owner_pricing_rejected,
    ]

    for fn in tests:
        try:
            fn()
        except Exception as exc:
            _fail(fn.__name__, f"Unexpected exception: {exc}")

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
        print("\n  All tests passed. Marketplace & Commercial Pricing API verified.")
        sys.exit(0)


if __name__ == "__main__":
    main()
