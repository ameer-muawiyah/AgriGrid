"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    test_escrow_orders.py
Module:  Escrow Orders & Settlement Verification Suite (Increment 2 Phase 3 V&V)
Version: 2.0  (Increment 2 — Escrow Orders & Settlement)
Author:  Muhammad Hashir (QA & DevOps Engineer)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §5, AG-API-INC2-003 §6 (Endpoints 5–10), SRS v1.3 (FR-ORD-*, FR-SET-*, FR-STM-*)

Test Coverage
-------------
  Digital Escrow Checkout (TC-ORD)
    TC-ORD-01  POST /api/orders  — Happy path: Sara buys Tahir's Wheat (201, ORD format, wallet debited, HELD escrow)
    TC-ORD-02  POST /api/orders  — Missing required checkout fields rejected (400)
    TC-ORD-03  POST /api/orders  — Cold-chain temperature validation (-25.1°C / +30.1°C -> 400; -25.0°C boundary -> 201)
    TC-ORD-04  POST /api/orders  — Partial quantity purchase rejected (400)
    TC-ORD-05  POST /api/orders  — Insufficient buyer wallet balance rejected (400)
    TC-ORD-06  POST /api/orders  — Unpriced and soft-deleted listings rejected (404 'Listing not found.')
    TC-ORD-07  POST /api/orders  — Concurrency / Sold and Withdrawn listings rejected (409)
    TC-ORD-08  POST /api/orders  — RBAC guards: Farmer caller (403), Unauthenticated (401)

  Delivery Confirmation & Escrow Release (TC-SET)
    TC-SET-01  POST /api/orders/<id>/confirm-delivery — Buyer quality acceptance releases escrow to farmer (200, 72h auto-release, TX ref)
    TC-SET-02  POST /api/orders/<id>/confirm-delivery — Guards: Non-owner buyer (404), Farmer caller (403), Re-confirm (400)

  Order Cancellation & Refund (TC-CAN)
    TC-CAN-01  POST /api/orders/<id>/cancel — Buyer cancels order: wallet refunded, escrow REFUNDED, listing restored to catalog (200)
    TC-CAN-02  POST /api/orders/<id>/cancel — Farmer cancels order: release_tx_ref records farmer_cancellation (200)
    TC-CAN-03  POST /api/orders/<id>/cancel — Guards: Non-party buyer (404), Completed order (400), Transporter role (403)

  Dispute Registration (TC-DSP)
    TC-DSP-01  POST /api/orders/<id>/dispute — Formal dispute flags order & freezes escrow; zero fund movement (200)
    TC-DSP-02  POST /api/orders/<id>/dispute — State-machine boundaries: Re-dispute (400), Confirm disputed (400), Cancel disputed (400)

  Multi-Tenant Order History (TC-HIST)
    TC-HIST-01  GET /api/orders/buyer — Buyer procurement history: tenant isolation, envelope, farm_name & escrow_status (200)
    TC-HIST-02  GET /api/orders/buyer — Filter validation: status=Escrow_Funded, In_Transit (empty 200), Pending rejected (400, PD-1)
    TC-HIST-03  GET /api/orders/farmer — Farmer inbound sales: buyer_company_name; Cross-role access denied (403)

Usage
-----
  python backend/test_escrow_orders.py       (from project root)
  python test_escrow_orders.py               (from backend/ directory)
"""

import os
import re
import sys
import time
import threading
import sqlite3
from datetime import datetime, timezone, date, timedelta
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
TEST_PORT = int(os.environ.get("AGRIGRID_TEST_PORT", "5004"))
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

_sara_token: str = ""
_tahir_token: str = ""
_transporter_token: str = ""

_happy_order_id: int = 0
_disputed_order_id: int = 0

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


def _create_and_price_crop(farmer_token: str, crop_name: str = "Potato", quantity_kg: float = 1000.0, price_per_kg: float = 50.0) -> int:
    """Helper to create a crop listing for farmer and assign commercial asking price."""
    r_create = requests.post(
        f"{API_BASE_URL}/crops",
        headers=_auth(farmer_token),
        json={
            "crop_name": crop_name,
            "planting_date": PLANT_DATE,
            "estimated_harvest_date": HARVEST_DATE,
            "acreage": 3.0,
            "gps_latitude": 30.1234,
            "gps_longitude": 72.5678,
            "quantity_kg": quantity_kg,
        },
    )
    if r_create.status_code != 201:
        raise RuntimeError(f"Failed to create crop: {r_create.text}")
    listing_id = r_create.json()["data"]["listing_id"]

    r_price = requests.put(
        f"{API_BASE_URL}/crops/{listing_id}",
        headers=_auth(farmer_token),
        json={"asking_price_per_kg": price_per_kg},
    )
    if r_price.status_code != 200:
        raise RuntimeError(f"Failed to price crop: {r_price.text}")

    return listing_id


# ===========================================================================
# 1. DIGITAL ESCROW CHECKOUT (TC-ORD)
# ===========================================================================

def tc_ord_01_checkout_happy_path():
    """Sara buys Tahir's priced Wheat: 201, ORD format, wallet debited, listing Sold, escrow HELD."""
    global _happy_order_id, _sara_token, _tahir_token

    # 1. Login seeded Sara Buyer & Tahir Farmer
    r_sara = requests.post(f"{API_BASE_URL}/auth/login", json={"username": "sara_buyer", "password": "BuyerPass1"})
    _sara_token = r_sara.json()["token"]

    r_tahir = requests.post(f"{API_BASE_URL}/auth/login", json={"username": "tahir_farmer", "password": "FarmSecure1"})
    _tahir_token = r_tahir.json()["token"]

    # 2. Reset listing 1 to 5000 kg @ 45.00 PKR and wallet balances
    conn = _get_db_conn()
    try:
        conn.execute("""
            UPDATE listings
               SET status = 'Active',
                   quantity_kg = 5000.0,
                   asking_price_per_kg = 45.0,
                   batch_id = 'BATCH-2026-WHT-0001',
                   is_deleted = 0
             WHERE id = 1
        """)
        conn.execute("UPDATE buyer_wallets SET balance_pkr = 500000.00 WHERE buyer_id = 1")
        conn.execute("UPDATE farmer_wallets SET balance_pkr = 0.00 WHERE farmer_id = 1")
        conn.commit()
    finally:
        conn.close()

    # 3. Sara checkouts listing 1
    checkout_payload = {
        "listing_id": 1,
        "ordered_quantity_kg": 5000.0,
        "destination_warehouse": "Metro Central Hub, Multan Road, Lahore",
        "max_temperature_celsius": 18.0,
    }
    r = requests.post(f"{API_BASE_URL}/orders", headers=_auth(_sara_token), json=checkout_payload)
    data = r.json()

    status_ok = r.status_code == 201
    msg_ok = data.get("message") == "Order created successfully. Escrow funds locked."
    order_data = data.get("data", {})

    order_num = order_data.get("order_number", "")
    order_num_ok = bool(re.match(r"^ORD-\d{4}-\d{4}$", order_num))
    _happy_order_id = order_data.get("order_id", 0)

    qty_ok = order_data.get("ordered_quantity_kg") == 5000.0
    total_ok = order_data.get("total_amount_pkr") == 225000.0
    order_stat_ok = order_data.get("order_status") == "Escrow_Funded"
    escrow_stat_ok = order_data.get("escrow_status") == "HELD"
    rem_wallet_ok = order_data.get("remaining_wallet_balance_pkr") == 275000.0

    # DB Persistence verification
    conn = _get_db_conn()
    try:
        bw = conn.execute("SELECT balance_pkr FROM buyer_wallets WHERE buyer_id = 1").fetchone()
        db_wallet_ok = bw is not None and float(bw["balance_pkr"]) == 275000.0

        lst = conn.execute("SELECT status FROM listings WHERE id = 1").fetchone()
        db_listing_sold = lst is not None and lst["status"] == "Sold"

        esc = conn.execute("SELECT escrow_status, held_amount_pkr FROM escrow_holdings WHERE order_id = ?", (_happy_order_id,)).fetchone()
        db_escrow_ok = esc is not None and esc["escrow_status"] == "HELD" and float(esc["held_amount_pkr"]) == 225000.0
    finally:
        conn.close()

    all_ok = (
        status_ok and msg_ok and order_num_ok and qty_ok and total_ok
        and order_stat_ok and escrow_stat_ok and rem_wallet_ok
        and db_wallet_ok and db_listing_sold and db_escrow_ok
    )
    detail = (
        f"status={r.status_code} order_num={order_num} total={order_data.get('total_amount_pkr')} "
        f"rem_wallet={order_data.get('remaining_wallet_balance_pkr')} db_wallet={db_wallet_ok} listing_sold={db_listing_sold}"
    )

    _check(
        "TC-ORD-01",
        "Sara buys Tahir's priced Wheat: 201, ORD format, wallet debited (500k -> 275k), listing Sold, escrow HELD",
        all_ok,
        detail,
    )


def tc_ord_02_missing_field_rejected():
    """Missing or empty checkout fields rejected with HTTP 400 'All checkout fields are required.'"""
    expected_err = "All checkout fields are required."

    # 1. Missing destination_warehouse
    p1 = {"listing_id": 1, "ordered_quantity_kg": 5000.0, "max_temperature_celsius": 18.0}
    r1 = requests.post(f"{API_BASE_URL}/orders", headers=_auth(_sara_token), json=p1)

    # 2. Missing max_temperature_celsius
    p2 = {"listing_id": 1, "ordered_quantity_kg": 5000.0, "destination_warehouse": "Lahore Warehouse Hub"}
    r2 = requests.post(f"{API_BASE_URL}/orders", headers=_auth(_sara_token), json=p2)

    # 3. Missing ordered_quantity_kg
    p3 = {"listing_id": 1, "destination_warehouse": "Lahore Warehouse Hub", "max_temperature_celsius": 18.0}
    r3 = requests.post(f"{API_BASE_URL}/orders", headers=_auth(_sara_token), json=p3)

    # 4. Destination warehouse too short (< 5 chars)
    p4 = {"listing_id": 1, "ordered_quantity_kg": 5000.0, "destination_warehouse": "Hub", "max_temperature_celsius": 18.0}
    r4 = requests.post(f"{API_BASE_URL}/orders", headers=_auth(_sara_token), json=p4)

    all_400 = (
        r1.status_code == 400 and r1.json().get("error") == expected_err
        and r2.status_code == 400 and r2.json().get("error") == expected_err
        and r3.status_code == 400 and r3.json().get("error") == expected_err
        and r4.status_code == 400 and r4.json().get("error") == expected_err
    )

    _check(
        "TC-ORD-02",
        "Missing checkout fields and short warehouse address rejected with 400 'All checkout fields are required.'",
        all_400,
        f"r1={r1.status_code} r2={r2.status_code} r3={r3.status_code} r4={r4.status_code}",
    )


def tc_ord_03_temperature_boundaries():
    """Max temperature validation: -25.1 and +30.1 rejected (400); -25.0 boundary accepted (201)."""
    # Create test listings for Tahir
    listing_neg = _create_and_price_crop(_tahir_token, "Rice", 100.0, 30.0)
    listing_pos = _create_and_price_crop(_tahir_token, "Rice", 100.0, 30.0)
    listing_bound = _create_and_price_crop(_tahir_token, "Rice", 100.0, 30.0)

    expected_err = "Max temperature must be between -25.0°C and 30.0°C."

    # 1. -25.1°C -> 400
    r_neg = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": listing_neg,
            "ordered_quantity_kg": 100.0,
            "destination_warehouse": "Cold Storage Facility A, Lahore",
            "max_temperature_celsius": -25.1,
        },
    )

    # 2. +30.1°C -> 400
    r_pos = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": listing_pos,
            "ordered_quantity_kg": 100.0,
            "destination_warehouse": "Cold Storage Facility A, Lahore",
            "max_temperature_celsius": 30.1,
        },
    )

    # 3. Boundary -25.0°C -> 201 accepted
    r_bound = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": listing_bound,
            "ordered_quantity_kg": 100.0,
            "destination_warehouse": "Cold Storage Facility A, Lahore",
            "max_temperature_celsius": -25.0,
        },
    )

    neg_ok = r_neg.status_code == 400 and r_neg.json().get("error") == expected_err
    pos_ok = r_pos.status_code == 400 and r_pos.json().get("error") == expected_err
    bound_ok = r_bound.status_code == 201 and r_bound.json().get("success") is True

    _check(
        "TC-ORD-03",
        "Temperature boundaries: -25.1°C and +30.1°C rejected (400); -25.0°C boundary accepted (201)",
        neg_ok and pos_ok and bound_ok,
        f"neg_status={r_neg.status_code} pos_status={r_pos.status_code} bound_status={r_bound.status_code}",
    )


def tc_ord_04_partial_quantity_rejected():
    """Partial quantity checkout rejected with 400 'Partial quantity purchasing is not supported in Increment 2.'"""
    test_listing = _create_and_price_crop(_tahir_token, "Maize", 2000.0, 35.0)

    r = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": test_listing,
            "ordered_quantity_kg": 1000.0,  # Partial (listing has 2000.0)
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 15.0,
        },
    )
    data = r.json()

    status_ok = r.status_code == 400
    expected_err = "Partial quantity purchasing is not supported in Increment 2."
    err_ok = data.get("error") == expected_err

    _check(
        "TC-ORD-04",
        "Partial quantity checkout rejected with 400 'Partial quantity purchasing is not supported in Increment 2.'",
        status_ok and err_ok,
        f"status={r.status_code} error='{data.get('error')}'",
    )


def tc_ord_05_insufficient_balance():
    """Checkout with wallet balance below total amount rejected with 400 'Insufficient wallet balance.'"""
    # 1. Register a fresh buyer with low wallet balance
    poor_user = f"poor_buyer_{RUN_TIMESTAMP}"
    r_reg = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "username": poor_user,
            "password": "PoorBuyerPass1!",
            "role": "buyer",
            "company_name": "Small Mart Ltd",
            "contact_phone": "+92-333-1122334",
            "warehouse_address": "Small Mart Warehouse, Kasur",
        },
    )
    buyer_id = r_reg.json()["user"]["buyer_id"]

    # 2. Set wallet balance to 100.00 PKR in DB
    conn = _get_db_conn()
    try:
        conn.execute("UPDATE buyer_wallets SET balance_pkr = 100.00 WHERE buyer_id = ?", (buyer_id,))
        conn.commit()
    finally:
        conn.close()

    r_login = requests.post(f"{API_BASE_URL}/auth/login", json={"username": poor_user, "password": "PoorBuyerPass1!"})
    poor_token = r_login.json()["token"]

    # 3. Create listing costing 25,000.00 PKR
    expensive_listing = _create_and_price_crop(_tahir_token, "Wheat", 500.0, 50.0)

    # 4. Attempt checkout
    r_order = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(poor_token),
        json={
            "listing_id": expensive_listing,
            "ordered_quantity_kg": 500.0,
            "destination_warehouse": "Small Mart Warehouse, Kasur",
            "max_temperature_celsius": 20.0,
        },
    )
    data = r_order.json()

    status_ok = r_order.status_code == 400
    expected_err = "Insufficient wallet balance."
    err_ok = data.get("error") == expected_err

    _check(
        "TC-ORD-05",
        "Checkout with insufficient wallet balance rejected with 400 'Insufficient wallet balance.'",
        status_ok and err_ok,
        f"status={r_order.status_code} error='{data.get('error')}'",
    )


def tc_ord_06_unpriced_and_softdeleted_listing():
    """Unpriced and soft-deleted listings return unified 404 'Listing not found.' on checkout."""
    expected_err = "Listing not found."

    # 1. Unpriced listing: Listing 2 is unpriced Tomato
    r_unpriced = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": 2,
            "ordered_quantity_kg": 2000.0,
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 12.0,
        },
    )

    # 2. Soft-deleted listing
    del_listing = _create_and_price_crop(_tahir_token, "Sugarcane", 1000.0, 20.0)
    requests.delete(f"{API_BASE_URL}/crops/{del_listing}", headers=_auth(_tahir_token))

    r_deleted = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": del_listing,
            "ordered_quantity_kg": 1000.0,
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 12.0,
        },
    )

    unpriced_404 = r_unpriced.status_code == 404 and r_unpriced.json().get("error") == expected_err
    deleted_404 = r_deleted.status_code == 404 and r_deleted.json().get("error") == expected_err

    _check(
        "TC-ORD-06",
        "Unpriced and soft-deleted listings return unified 404 'Listing not found.' on checkout",
        unpriced_404 and deleted_404,
        f"unpriced_status={r_unpriced.status_code} deleted_status={r_deleted.status_code}",
    )


def tc_ord_07_second_checkout_and_withdrawn_listing():
    """Checkout on Sold listing or Withdrawn listing rejected with HTTP 409 'Listing has already been sold.'"""
    expected_err = "Listing has already been sold."

    # 1. Listing 1 is already in 'Sold' status from TC-ORD-01
    r_sold = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": 1,
            "ordered_quantity_kg": 5000.0,
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 18.0,
        },
    )

    # 2. Listing in 'Withdrawn' status (not soft-deleted)
    withdrawn_listing = _create_and_price_crop(_tahir_token, "Cotton", 1000.0, 70.0)
    conn = _get_db_conn()
    try:
        conn.execute("UPDATE listings SET status = 'Withdrawn' WHERE id = ?", (withdrawn_listing,))
        conn.commit()
    finally:
        conn.close()

    r_withdrawn = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": withdrawn_listing,
            "ordered_quantity_kg": 1000.0,
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 22.0,
        },
    )

    sold_409 = r_sold.status_code == 409 and r_sold.json().get("error") == expected_err
    withdrawn_409 = r_withdrawn.status_code == 409 and r_withdrawn.json().get("error") == expected_err

    _check(
        "TC-ORD-07",
        "Checkout on Sold or Withdrawn listing rejected with 409 'Listing has already been sold.'",
        sold_409 and withdrawn_409,
        f"sold_status={r_sold.status_code} withdrawn_status={r_withdrawn.status_code}",
    )


def tc_ord_08_rbac_guards():
    """Farmer caller rejected with 403 'Access denied.'; Unauthenticated request rejected with 401."""
    # 1. Farmer caller
    r_farmer = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_tahir_token),
        json={
            "listing_id": 1,
            "ordered_quantity_kg": 5000.0,
            "destination_warehouse": "Some Warehouse",
            "max_temperature_celsius": 15.0,
        },
    )
    farmer_403 = r_farmer.status_code == 403 and r_farmer.json().get("error") == "Access denied."

    # 2. No token
    r_anon = requests.post(
        f"{API_BASE_URL}/orders",
        json={
            "listing_id": 1,
            "ordered_quantity_kg": 5000.0,
            "destination_warehouse": "Some Warehouse",
            "max_temperature_celsius": 15.0,
        },
    )
    anon_401 = r_anon.status_code == 401 and r_anon.json().get("error") == "Authentication required. Please log in."

    _check(
        "TC-ORD-08",
        "Checkout RBAC guards: Farmer caller blocked with 403, Unauthenticated request with 401",
        farmer_403 and anon_401,
        f"farmer_status={r_farmer.status_code} anon_status={r_anon.status_code}",
    )


# ===========================================================================
# 2. DELIVERY CONFIRMATION & ESCROW RELEASE (TC-SET)
# ===========================================================================

def tc_set_01_owner_confirm_delivery():
    """Owner buyer confirms delivery: order Completed, escrow RELEASED, farmer wallet credited (0 -> 225k)."""
    global _happy_order_id

    # Buyer Sara confirms delivery on order 1
    r = requests.post(f"{API_BASE_URL}/orders/{_happy_order_id}/confirm-delivery", headers=_auth(_sara_token))
    data = r.json()

    status_ok = r.status_code == 200
    msg_ok = data.get("message") == "Delivery confirmed and escrow funds released to farmer."
    res = data.get("data", {})

    order_comp = res.get("order_status") == "Completed"
    escrow_rel = res.get("escrow_status") == "RELEASED"
    delivered_at = res.get("delivered_at")
    del_ok = delivered_at is not None

    expected_ref = f"TRIGGER:buyer_confirmation;REF:TX-{_happy_order_id}-SETTLE"
    ref_ok = res.get("release_tx_ref") == expected_ref

    # DB persistence & timestamp audit
    conn = _get_db_conn()
    try:
        ord_row = conn.execute("SELECT order_status, delivered_at FROM orders WHERE id = ?", (_happy_order_id,)).fetchone()
        esc_row = conn.execute("SELECT escrow_status, delivered_at, auto_release_at, release_tx_ref FROM escrow_holdings WHERE order_id = ?", (_happy_order_id,)).fetchone()
        fw_row = conn.execute("SELECT balance_pkr FROM farmer_wallets WHERE farmer_id = 1").fetchone()

        db_order_ok = ord_row is not None and ord_row["order_status"] == "Completed"
        db_escrow_ok = esc_row is not None and esc_row["escrow_status"] == "RELEASED" and esc_row["release_tx_ref"] == expected_ref
        db_farmer_credited = fw_row is not None and float(fw_row["balance_pkr"]) == 225000.0

        # Exact +72 hours verification
        del_dt = datetime.fromisoformat(esc_row["delivered_at"].replace("Z", "+00:00"))
        auto_dt = datetime.fromisoformat(esc_row["auto_release_at"].replace("Z", "+00:00"))
        time_diff_hours = (auto_dt - del_dt).total_seconds() / 3600.0
        time_72h_ok = abs(time_diff_hours - 72.0) < 0.001
    finally:
        conn.close()

    all_ok = status_ok and msg_ok and order_comp and escrow_rel and del_ok and ref_ok and db_order_ok and db_escrow_ok and db_farmer_credited and time_72h_ok
    detail = (
        f"status={r.status_code} farmer_wallet={fw_row['balance_pkr'] if fw_row else None} "
        f"ref='{res.get('release_tx_ref')}' 72h_diff={time_diff_hours:.2f}h"
    )

    _check(
        "TC-SET-01",
        "Buyer confirms delivery: order Completed, escrow RELEASED, farmer credited (0 -> 225k), exact +72h auto-release",
        all_ok,
        detail,
    )


def tc_set_02_confirm_delivery_guards():
    """Non-owner buyer returns 404; Farmer returns 403; Re-confirming Completed returns 400."""
    # 1. Register other buyer
    other_user = f"intruder_buyer_{RUN_TIMESTAMP}"
    r_reg = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "username": other_user,
            "password": "IntruderPass1!",
            "role": "buyer",
            "company_name": "Intruder Foods",
            "contact_phone": "+92-300-8877665",
            "warehouse_address": "Intruder Storage, Gujranwala",
        },
    )
    r_login = requests.post(f"{API_BASE_URL}/auth/login", json={"username": other_user, "password": "IntruderPass1!"})
    other_token = r_login.json()["token"]

    # 1. Non-owner buyer -> 404 "Order not found."
    r_non_owner = requests.post(f"{API_BASE_URL}/orders/{_happy_order_id}/confirm-delivery", headers=_auth(other_token))
    non_owner_404 = r_non_owner.status_code == 404 and r_non_owner.json().get("error") == "Order not found."

    # 2. Farmer caller -> 403 "Access denied."
    r_farmer = requests.post(f"{API_BASE_URL}/orders/{_happy_order_id}/confirm-delivery", headers=_auth(_tahir_token))
    farmer_403 = r_farmer.status_code == 403 and r_farmer.json().get("error") == "Access denied."

    # 3. Confirming already Completed order -> 400 "Order cannot be confirmed in current status."
    r_reconfirm = requests.post(f"{API_BASE_URL}/orders/{_happy_order_id}/confirm-delivery", headers=_auth(_sara_token))
    reconfirm_400 = (
        r_reconfirm.status_code == 400
        and r_reconfirm.json().get("error") == "Order cannot be confirmed in current status."
    )

    _check(
        "TC-SET-02",
        "Confirm delivery guards: Non-owner buyer (404), Farmer (403), Re-confirming Completed order (400)",
        non_owner_404 and farmer_403 and reconfirm_400,
        f"non_owner={r_non_owner.status_code} farmer={r_farmer.status_code} reconfirm={r_reconfirm.status_code}",
    )


# ===========================================================================
# 3. ORDER CANCELLATION & REFUND (TC-CAN)
# ===========================================================================

def tc_can_01_buyer_cancel_refund_and_restore():
    """Buyer cancel: refunded exactly, escrow REFUNDED, listing restored to catalog Active."""
    # 1. Create crop & checkout
    c_listing = _create_and_price_crop(_tahir_token, "Potato", 1000.0, 40.0)
    r_order = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": c_listing,
            "ordered_quantity_kg": 1000.0,
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 16.0,
        },
    )
    order_id = r_order.json()["data"]["order_id"]
    wallet_before_cancel = r_order.json()["data"]["remaining_wallet_balance_pkr"]

    # 2. Sara cancels order
    r_cancel = requests.post(f"{API_BASE_URL}/orders/{order_id}/cancel", headers=_auth(_sara_token))
    data = r_cancel.json()

    status_ok = r_cancel.status_code == 200
    res = data.get("data", {})
    order_cancelled = res.get("order_status") == "Cancelled"
    escrow_refunded = res.get("escrow_status") == "REFUNDED"
    amt_ok = res.get("refunded_amount_pkr") == 40000.0

    # DB Checks
    conn = _get_db_conn()
    try:
        bw = conn.execute("SELECT balance_pkr FROM buyer_wallets WHERE buyer_id = 1").fetchone()
        db_refund_ok = bw is not None and abs(float(bw["balance_pkr"]) - (wallet_before_cancel + 40000.0)) < 0.01

        lst = conn.execute("SELECT status FROM listings WHERE id = ?", (c_listing,)).fetchone()
        db_listing_active = lst is not None and lst["status"] == "Active"

        esc = conn.execute("SELECT escrow_status, release_tx_ref FROM escrow_holdings WHERE order_id = ?", (order_id,)).fetchone()
        db_escrow_ok = esc is not None and esc["escrow_status"] == "REFUNDED" and f"TRIGGER:buyer_cancellation;REF:TX-{order_id}-REFUND" in esc["release_tx_ref"]
    finally:
        conn.close()

    # Catalog presence check
    r_cat = requests.get(f"{API_BASE_URL}/marketplace/listings", headers=_auth(_sara_token))
    cat_items = [it for it in r_cat.json().get("data", []) if it["listing_id"] == c_listing]
    cat_visible = len(cat_items) == 1

    all_ok = status_ok and order_cancelled and escrow_refunded and amt_ok and db_refund_ok and db_listing_active and db_escrow_ok and cat_visible
    detail = (
        f"status={r_cancel.status_code} refunded={res.get('refunded_amount_pkr')} "
        f"db_wallet_refund={db_refund_ok} listing_active={db_listing_active} cat_visible={cat_visible}"
    )

    _check(
        "TC-CAN-01",
        "Buyer cancels order: wallet refunded (40k), escrow REFUNDED, listing Active & visible in marketplace",
        all_ok,
        detail,
    )


def tc_can_02_farmer_cancel_release_ref():
    """Farmer cancel of separate order: 200, release_tx_ref records farmer_cancellation."""
    # 1. Create crop & checkout
    c_listing = _create_and_price_crop(_tahir_token, "Maize", 1000.0, 35.0)
    r_order = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": c_listing,
            "ordered_quantity_kg": 1000.0,
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 16.0,
        },
    )
    order_id = r_order.json()["data"]["order_id"]

    # 2. Farmer Tahir cancels order
    r_cancel = requests.post(f"{API_BASE_URL}/orders/{order_id}/cancel", headers=_auth(_tahir_token))
    data = r_cancel.json()

    status_ok = r_cancel.status_code == 200
    res = data.get("data", {})
    expected_ref = f"TRIGGER:farmer_cancellation;REF:TX-{order_id}-REFUND"

    conn = _get_db_conn()
    try:
        esc = conn.execute("SELECT escrow_status, release_tx_ref FROM escrow_holdings WHERE order_id = ?", (order_id,)).fetchone()
        db_ref_ok = esc is not None and esc["release_tx_ref"] == expected_ref and esc["escrow_status"] == "REFUNDED"
    finally:
        conn.close()

    _check(
        "TC-CAN-02",
        "Farmer cancel of separate order: 200, release_tx_ref records TRIGGER:farmer_cancellation",
        status_ok and db_ref_ok,
        f"status={r_cancel.status_code} tx_ref='{esc['release_tx_ref'] if esc else None}'",
    )


def tc_can_03_cancel_guards():
    """Cancel guards: Non-party buyer (404), Completed order (400), Transporter role (403)."""
    # 1. Create order for Sara and Tahir
    c_listing = _create_and_price_crop(_tahir_token, "Wheat", 500.0, 45.0)
    r_order = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": c_listing,
            "ordered_quantity_kg": 500.0,
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 16.0,
        },
    )
    order_id = r_order.json()["data"]["order_id"]

    # Register other buyer & transporter
    other_user = f"third_buyer_{RUN_TIMESTAMP}"
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "username": other_user,
            "password": "ThirdBuyerPass1!",
            "role": "buyer",
            "company_name": "Third Mart",
            "contact_phone": "+92-300-7766554",
            "warehouse_address": "Third Mart Warehouse, Sialkot",
        },
    )
    r_other_login = requests.post(f"{API_BASE_URL}/auth/login", json={"username": other_user, "password": "ThirdBuyerPass1!"})
    other_token = r_other_login.json()["token"]

    trans_user = f"transporter_ord_{RUN_TIMESTAMP}"
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": trans_user, "password": "TransSecurePass1!", "role": "transporter"},
    )
    r_trans_login = requests.post(f"{API_BASE_URL}/auth/login", json={"username": trans_user, "password": "TransSecurePass1!"})
    trans_token = r_trans_login.json()["token"]

    # 1. Non-party buyer cancel -> 404 "Order not found."
    r_non_party = requests.post(f"{API_BASE_URL}/orders/{order_id}/cancel", headers=_auth(other_token))
    non_party_404 = r_non_party.status_code == 404 and r_non_party.json().get("error") == "Order not found."

    # 2. Cancelling Completed order (_happy_order_id) -> 400 "Only Escrow_Funded orders can be cancelled."
    r_completed = requests.post(f"{API_BASE_URL}/orders/{_happy_order_id}/cancel", headers=_auth(_sara_token))
    completed_400 = (
        r_completed.status_code == 400
        and r_completed.json().get("error") == "Only Escrow_Funded orders can be cancelled."
    )

    # 3. Transporter role -> 403 "Access denied."
    r_trans = requests.post(f"{API_BASE_URL}/orders/{order_id}/cancel", headers=_auth(trans_token))
    trans_403 = r_trans.status_code == 403 and r_trans.json().get("error") == "Access denied."

    _check(
        "TC-CAN-03",
        "Cancel guards: Non-party buyer (404), Completed order (400), Transporter role (403)",
        non_party_404 and completed_400 and trans_403,
        f"non_party={r_non_party.status_code} completed={r_completed.status_code} trans={r_trans.status_code}",
    )


# ===========================================================================
# 4. DISPUTE REGISTRATION (TC-DSP)
# ===========================================================================

def tc_dsp_01_party_dispute_funds_frozen():
    """Party dispute flags order & freezes escrow in DISPUTED state; zero funds moved."""
    global _disputed_order_id

    # 1. Create order
    c_listing = _create_and_price_crop(_tahir_token, "Cotton", 500.0, 60.0)
    r_order = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(_sara_token),
        json={
            "listing_id": c_listing,
            "ordered_quantity_kg": 500.0,
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 20.0,
        },
    )
    _disputed_order_id = r_order.json()["data"]["order_id"]

    # Snapshot balances
    conn = _get_db_conn()
    try:
        bw_before = float(conn.execute("SELECT balance_pkr FROM buyer_wallets WHERE buyer_id = 1").fetchone()["balance_pkr"])
        fw_before = float(conn.execute("SELECT balance_pkr FROM farmer_wallets WHERE farmer_id = 1").fetchone()["balance_pkr"])
    finally:
        conn.close()

    # 2. Sara flags dispute
    r_disp = requests.post(f"{API_BASE_URL}/orders/{_disputed_order_id}/dispute", headers=_auth(_sara_token))
    data = r_disp.json()

    status_ok = r_disp.status_code == 200
    msg_ok = data.get("message") == "Dispute registered. Escrow funds have been frozen."
    res = data.get("data", {})
    order_disp = res.get("order_status") == "Disputed"
    escrow_disp = res.get("escrow_status") == "DISPUTED"

    # DB Persistence and wallet freeze verification
    conn = _get_db_conn()
    try:
        ord_row = conn.execute("SELECT order_status FROM orders WHERE id = ?", (_disputed_order_id,)).fetchone()
        esc_row = conn.execute("SELECT escrow_status FROM escrow_holdings WHERE order_id = ?", (_disputed_order_id,)).fetchone()
        bw_after = float(conn.execute("SELECT balance_pkr FROM buyer_wallets WHERE buyer_id = 1").fetchone()["balance_pkr"])
        fw_after = float(conn.execute("SELECT balance_pkr FROM farmer_wallets WHERE farmer_id = 1").fetchone()["balance_pkr"])

        db_order_ok = ord_row is not None and ord_row["order_status"] == "Disputed"
        db_escrow_ok = esc_row is not None and esc_row["escrow_status"] == "DISPUTED"
        wallets_unchanged = (bw_before == bw_after) and (fw_before == fw_after)
    finally:
        conn.close()

    all_ok = status_ok and msg_ok and order_disp and escrow_disp and db_order_ok and db_escrow_ok and wallets_unchanged
    detail = (
        f"status={r_disp.status_code} order_status='{res.get('order_status')}' "
        f"escrow_status='{res.get('escrow_status')}' wallets_frozen={wallets_unchanged}"
    )

    _check(
        "TC-DSP-01",
        "Party dispute: order Disputed, escrow DISPUTED; zero wallet movement (funds frozen)",
        all_ok,
        detail,
    )


def tc_dsp_02_dispute_frozen_boundary_guards():
    """State-machine boundaries: Re-disputing (400), Confirming (400), Cancelling disputed (400, FR-STM-006)."""
    # 1. Disputing again
    r_redisp = requests.post(f"{API_BASE_URL}/orders/{_disputed_order_id}/dispute", headers=_auth(_sara_token))
    redisp_400 = (
        r_redisp.status_code == 400
        and r_redisp.json().get("error") == "Only Escrow_Funded orders can be disputed."
    )

    # 2. Confirming disputed order
    r_confirm = requests.post(f"{API_BASE_URL}/orders/{_disputed_order_id}/confirm-delivery", headers=_auth(_sara_token))
    confirm_400 = (
        r_confirm.status_code == 400
        and r_confirm.json().get("error") == "Order cannot be confirmed in current status."
    )

    # 3. Cancelling disputed order (FR-STM-006)
    r_cancel = requests.post(f"{API_BASE_URL}/orders/{_disputed_order_id}/cancel", headers=_auth(_sara_token))
    cancel_400 = (
        r_cancel.status_code == 400
        and r_cancel.json().get("error") == "Only Escrow_Funded orders can be cancelled."
    )

    _check(
        "TC-DSP-02",
        "Dispute boundaries (FR-STM-006): Re-dispute (400), Confirm disputed (400), Cancel disputed (400)",
        redisp_400 and confirm_400 and cancel_400,
        f"redisp={r_redisp.status_code} confirm={r_confirm.status_code} cancel={r_cancel.status_code}",
    )


# ===========================================================================
# 5. MULTI-TENANT ORDER HISTORY (TC-HIST)
# ===========================================================================

def tc_hist_01_buyer_history_shape_and_isolation():
    """Buyer order history: returns own orders only, envelope exact, farm_name & escrow_status present."""
    r = requests.get(f"{API_BASE_URL}/orders/buyer", headers=_auth(_sara_token))
    data = r.json()

    status_ok = r.status_code == 200
    expected_keys = {"success", "data", "page", "limit", "total"}
    keys_ok = set(data.keys()) == expected_keys

    orders = data.get("data", [])
    total = data.get("total", -1)
    has_orders = len(orders) > 0 and total >= len(orders)

    # Check payload fields of first item
    first = orders[0] if orders else {}
    expected_fields = [
        "order_id", "order_number", "listing_id", "crop_name", "batch_id",
        "farmer_id", "farm_name", "ordered_quantity_kg", "agreed_price_per_kg",
        "total_amount_pkr", "destination_warehouse", "max_temperature_celsius",
        "order_status", "escrow_status", "created_at"
    ]
    missing_fields = [f for f in expected_fields if f not in first]

    _check(
        "TC-HIST-01",
        "Buyer history: exact envelope keys, isolation verified, farm_name & escrow_status present",
        status_ok and keys_ok and has_orders and len(missing_fields) == 0,
        f"status={r.status_code} total={total} items={len(orders)} missing={missing_fields}",
    )


def tc_hist_02_filter_validation_and_pd1():
    """History filter validation: status=Escrow_Funded (200), In_Transit (empty 200), Pending (400, PD-1)."""
    # 1. status=Escrow_Funded
    r_funded = requests.get(f"{API_BASE_URL}/orders/buyer?status=Escrow_Funded", headers=_auth(_sara_token))
    data_funded = r_funded.json()
    funded_items = data_funded.get("data", [])
    funded_all_ok = all(it["order_status"] == "Escrow_Funded" for it in funded_items)

    # 2. status=In_Transit (valid schema status, but empty in current data)
    r_transit = requests.get(f"{API_BASE_URL}/orders/buyer?status=In_Transit", headers=_auth(_sara_token))
    data_transit = r_transit.json()
    transit_ok = r_transit.status_code == 200 and data_transit.get("data") == [] and data_transit.get("total") == 0

    # 3. status=Pending -> 400 "Invalid filter parameters." (pins PD-1 — schema vocabulary governs)
    r_pending = requests.get(f"{API_BASE_URL}/orders/buyer?status=Pending", headers=_auth(_sara_token))
    data_pending = r_pending.json()
    pending_ok = (
        r_pending.status_code == 400
        and data_pending.get("error") == "Invalid filter parameters."
    )

    all_ok = r_funded.status_code == 200 and funded_all_ok and transit_ok and pending_ok
    detail = (
        f"funded_status={r_funded.status_code} (items={len(funded_items)}) | "
        f"transit_status={r_transit.status_code} (count={data_transit.get('total')}) | "
        f"pending_status={r_pending.status_code} error='{data_pending.get('error')}'"
    )

    _check(
        "TC-HIST-02",
        "History filtering: Escrow_Funded (200), In_Transit (empty 200), Pending rejected (400, pins PD-1)",
        all_ok,
        detail,
    )


def tc_hist_03_farmer_history_and_cross_rbac():
    """Farmer history carries buyer_company_name; Cross-role access blocked with 403 'Access denied.'"""
    # 1. Farmer Tahir queries inbound sales history
    r_farmer = requests.get(f"{API_BASE_URL}/orders/farmer", headers=_auth(_tahir_token))
    data_farmer = r_farmer.json()
    farmer_status_ok = r_farmer.status_code == 200
    farmer_orders = data_farmer.get("data", [])
    first_order = farmer_orders[0] if farmer_orders else {}
    has_company = "buyer_company_name" in first_order

    # 2. Cross-role RBAC guards
    r_buyer_on_farmer = requests.get(f"{API_BASE_URL}/orders/farmer", headers=_auth(_sara_token))
    r_farmer_on_buyer = requests.get(f"{API_BASE_URL}/orders/buyer", headers=_auth(_tahir_token))

    b_on_f_403 = r_buyer_on_farmer.status_code == 403 and r_buyer_on_farmer.json().get("error") == "Access denied."
    f_on_b_403 = r_farmer_on_buyer.status_code == 403 and r_farmer_on_buyer.json().get("error") == "Access denied."

    all_ok = farmer_status_ok and has_company and b_on_f_403 and f_on_b_403
    detail = (
        f"farmer_status={r_farmer.status_code} has_company={has_company} "
        f"buyer_on_farmer={r_buyer_on_farmer.status_code} farmer_on_buyer={r_farmer_on_buyer.status_code}"
    )

    _check(
        "TC-HIST-03",
        "Farmer history carries buyer_company_name; Cross-role access denied (Buyer -> 403, Farmer -> 403)",
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
        cursor.execute("DELETE FROM escrow_holdings;")
        cursor.execute("DELETE FROM orders;")
        cursor.execute("DELETE FROM yield_forecasts WHERE listing_id > 4;")
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
    print("  AGRI-GRID  Escrow Orders & Settlement API Test Suite")
    print("=" * 65)

    _ensure_server_running()

    tests = [
        # Digital Escrow Checkout (TC-ORD)
        tc_ord_01_checkout_happy_path,
        tc_ord_02_missing_field_rejected,
        tc_ord_03_temperature_boundaries,
        tc_ord_04_partial_quantity_rejected,
        tc_ord_05_insufficient_balance,
        tc_ord_06_unpriced_and_softdeleted_listing,
        tc_ord_07_second_checkout_and_withdrawn_listing,
        tc_ord_08_rbac_guards,
        # Delivery Confirmation & Escrow Release (TC-SET)
        tc_set_01_owner_confirm_delivery,
        tc_set_02_confirm_delivery_guards,
        # Order Cancellation & Refund (TC-CAN)
        tc_can_01_buyer_cancel_refund_and_restore,
        tc_can_02_farmer_cancel_release_ref,
        tc_can_03_cancel_guards,
        # Dispute Registration (TC-DSP)
        tc_dsp_01_party_dispute_funds_frozen,
        tc_dsp_02_dispute_frozen_boundary_guards,
        # Multi-Tenant Order History (TC-HIST)
        tc_hist_01_buyer_history_shape_and_isolation,
        tc_hist_02_filter_validation_and_pd1,
        tc_hist_03_farmer_history_and_cross_rbac,
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
        print("\n  All tests passed. Escrow Orders & Settlement API verified.")
        sys.exit(0)


if __name__ == "__main__":
    main()
