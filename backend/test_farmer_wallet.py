"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    test_farmer_wallet.py
Module:  Farmer Wallet API Verification Suite (Increment 2 Post-Release V&V)
Version: 2.0  (Increment 2 — Settlement & Ledgers)
Author:  Muhammad Hashir (QA & DevOps Engineer)
Date:    2026-11-16
Source:  agrigrid-farmer-wallet-patch-package.md (PD-W1..PD-W4)

Test Coverage (4 Tests)
-----------------------
  Farmer Wallet Visibility (TC-WLT)
    TC-WLT-01  GET /api/farmer/wallet — New farmer without wallet row returns 200 with balance_pkr == 0.0
    TC-WLT-02  GET /api/farmer/wallet — Balance after delivery confirmation matches order total; second sale accumulates
    TC-WLT-03  GET /api/farmer/wallet — RBAC: Buyer receives 403 "Access denied."; Transporter receives 403
    TC-WLT-04  GET /api/farmer/wallet — Unauthenticated request receives 401 "Authentication required. Please log in."

Usage
-----
  python backend/test_farmer_wallet.py       (from project root)
  python test_farmer_wallet.py               (from backend/ directory)
"""

import os
import sys
import time
import threading
import sqlite3
from datetime import date, timedelta
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
TEST_PORT = int(os.environ.get("AGRIGRID_TEST_PORT", "5006"))
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
    if _probe_server(f"http://{TEST_HOST}:{TEST_PORT}/api", timeout=1.0):
        API_BASE_URL = f"http://{TEST_HOST}:{TEST_PORT}/api"
        print(f"[BOOT] Target server already active on {API_BASE_URL}")
        return

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
# 1. FARMER WALLET TESTS (TC-WLT)
# ===========================================================================

def tc_wlt_01_new_farmer_no_wallet():
    """Register fresh farmer (never sold anything) -> GET /api/farmer/wallet returns 200 with balance_pkr == 0.0."""
    farmer_user = f"farmer_fresh_{RUN_TIMESTAMP}"
    r_reg = requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "username": farmer_user,
            "password": "FarmSecurePass1!",
            "role": "farmer",
            "farm_name": "Fresh Sprout Fields",
        },
    )
    if r_reg.status_code != 201:
        _fail("TC-WLT-01", f"Failed to register fresh farmer: {r_reg.text}")
        return

    r_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": farmer_user, "password": "FarmSecurePass1!"},
    )
    farmer_token = r_login.json().get("token", "")

    # Query wallet
    r_wallet = requests.get(f"{API_BASE_URL}/farmer/wallet", headers=_auth(farmer_token))
    data = r_wallet.json()

    status_ok = r_wallet.status_code == 200
    success_ok = data.get("success") is True
    balance_ok = data.get("data", {}).get("balance_pkr") == 0.0

    all_ok = status_ok and success_ok and balance_ok
    detail = f"status={r_wallet.status_code} data={data.get('data')}"

    _check(
        "TC-WLT-01",
        "New farmer with no wallet row receives 200 with balance_pkr == 0.0",
        all_ok,
        detail,
    )


def tc_wlt_02_balance_after_settlement():
    """Balance after settlement: fresh farmer lists crop, buyer orders & confirms delivery -> balance equals order total; second sale accumulates."""
    # 1. Register fresh farmer
    f_user = f"farmer_sales_{RUN_TIMESTAMP}"
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={
            "username": f_user,
            "password": "FarmSecurePass1!",
            "role": "farmer",
            "farm_name": "Prosperous Acres",
        },
    )
    r_f_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": f_user, "password": "FarmSecurePass1!"},
    )
    f_token = r_f_login.json().get("token", "")

    # 2. Login Sara Buyer & ensure wallet balance
    r_b_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": "sara_buyer", "password": "BuyerPass1"},
    )
    b_token = r_b_login.json().get("token", "")

    conn = _get_db_conn()
    conn.execute("UPDATE buyer_wallets SET balance_pkr = 500000.00 WHERE buyer_id = 1")
    conn.commit()
    conn.close()

    # 3. First Sale: 1000 kg Wheat @ 45.00 PKR = 45,000.00 PKR
    r_crop1 = requests.post(
        f"{API_BASE_URL}/crops",
        headers=_auth(f_token),
        json={
            "crop_name": "Wheat",
            "planting_date": PLANT_DATE,
            "estimated_harvest_date": HARVEST_DATE,
            "acreage": 2.5,
            "gps_latitude": 30.1234,
            "gps_longitude": 72.5678,
            "quantity_kg": 1000.0,
        },
    )
    crop1_id = r_crop1.json()["data"]["listing_id"]
    requests.put(f"{API_BASE_URL}/crops/{crop1_id}", headers=_auth(f_token), json={"asking_price_per_kg": 45.0})

    # Buyer orders crop 1
    r_ord1 = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(b_token),
        json={
            "listing_id": crop1_id,
            "ordered_quantity_kg": 1000.0,
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 15.0,
        },
    )
    ord1_id = r_ord1.json()["data"]["order_id"]
    order1_total = r_ord1.json()["data"]["total_amount_pkr"]  # 45,000.00

    # Buyer confirms delivery -> settlement releases escrow to farmer
    r_conf1 = requests.post(f"{API_BASE_URL}/orders/{ord1_id}/confirm-delivery", headers=_auth(b_token))
    conf1_ok = r_conf1.status_code == 200

    # Check farmer wallet after sale 1
    r_wlt1 = requests.get(f"{API_BASE_URL}/farmer/wallet", headers=_auth(f_token))
    bal1 = r_wlt1.json().get("data", {}).get("balance_pkr")
    bal1_ok = bal1 == order1_total  # 45000.0

    # 4. Second Sale: 500 kg Rice @ 60.00 PKR = 30,000.00 PKR
    r_crop2 = requests.post(
        f"{API_BASE_URL}/crops",
        headers=_auth(f_token),
        json={
            "crop_name": "Rice",
            "planting_date": PLANT_DATE,
            "estimated_harvest_date": HARVEST_DATE,
            "acreage": 1.5,
            "gps_latitude": 30.5678,
            "gps_longitude": 72.8901,
            "quantity_kg": 500.0,
        },
    )
    crop2_id = r_crop2.json()["data"]["listing_id"]
    requests.put(f"{API_BASE_URL}/crops/{crop2_id}", headers=_auth(f_token), json={"asking_price_per_kg": 60.0})

    # Buyer orders crop 2
    r_ord2 = requests.post(
        f"{API_BASE_URL}/orders",
        headers=_auth(b_token),
        json={
            "listing_id": crop2_id,
            "ordered_quantity_kg": 500.0,
            "destination_warehouse": "Metro Central Hub, Lahore",
            "max_temperature_celsius": 18.0,
        },
    )
    ord2_id = r_ord2.json()["data"]["order_id"]
    order2_total = r_ord2.json()["data"]["total_amount_pkr"]  # 30,000.00

    # Buyer confirms delivery
    r_conf2 = requests.post(f"{API_BASE_URL}/orders/{ord2_id}/confirm-delivery", headers=_auth(b_token))
    conf2_ok = r_conf2.status_code == 200

    # Check farmer wallet after sale 2 -> accumulated balance
    r_wlt2 = requests.get(f"{API_BASE_URL}/farmer/wallet", headers=_auth(f_token))
    bal2 = r_wlt2.json().get("data", {}).get("balance_pkr")
    expected_accumulated = order1_total + order2_total  # 75,000.0
    bal2_ok = bal2 == expected_accumulated

    all_ok = conf1_ok and bal1_ok and conf2_ok and bal2_ok
    detail = (
        f"sale1_total={order1_total} bal_after_sale1={bal1} (ok={bal1_ok}) | "
        f"sale2_total={order2_total} bal_after_sale2={bal2} (expected={expected_accumulated}, ok={bal2_ok})"
    )

    _check(
        "TC-WLT-02",
        "Balance after delivery confirmation matches order total; second completed sale accumulates correctly",
        all_ok,
        detail,
    )


def tc_wlt_03_rbac_guards():
    """RBAC guards: Buyer receives 403 'Access denied.'; Transporter receives 403."""
    # 1. Buyer token -> 403
    r_sara = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": "sara_buyer", "password": "BuyerPass1"},
    )
    buyer_token = r_sara.json().get("token", "")

    r_buyer = requests.get(f"{API_BASE_URL}/farmer/wallet", headers=_auth(buyer_token))
    buyer_status_ok = r_buyer.status_code == 403
    buyer_err_ok = r_buyer.json().get("error") == "Access denied."

    # 2. Transporter token -> 403
    tr_user = f"trans_wlt_{RUN_TIMESTAMP}"
    requests.post(
        f"{API_BASE_URL}/auth/register",
        json={"username": tr_user, "password": "TransporterPass1!", "role": "transporter"},
    )
    r_tr_login = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": tr_user, "password": "TransporterPass1!"},
    )
    tr_token = r_tr_login.json().get("token", "")

    r_trans = requests.get(f"{API_BASE_URL}/farmer/wallet", headers=_auth(tr_token))
    trans_status_ok = r_trans.status_code == 403
    trans_err_ok = r_trans.json().get("error") == "Access denied."

    all_ok = buyer_status_ok and buyer_err_ok and trans_status_ok and trans_err_ok
    detail = (
        f"buyer_status={r_buyer.status_code} buyer_err='{r_buyer.json().get('error')}' | "
        f"trans_status={r_trans.status_code} trans_err='{r_trans.json().get('error')}'"
    )

    _check(
        "TC-WLT-03",
        "RBAC guards: Buyer and Transporter roles rejected with 403 'Access denied.'",
        all_ok,
        detail,
    )


def tc_wlt_04_unauthenticated():
    """Unauthenticated request receives 401 'Authentication required. Please log in.'."""
    r_anon = requests.get(f"{API_BASE_URL}/farmer/wallet")
    status_ok = r_anon.status_code == 401
    err_ok = r_anon.json().get("error") == "Authentication required. Please log in."

    all_ok = status_ok and err_ok
    detail = f"status={r_anon.status_code} error='{r_anon.json().get('error')}'"

    _check(
        "TC-WLT-04",
        "Unauthenticated request returns 401 'Authentication required. Please log in.'",
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
    print("  AGRI-GRID  Farmer Wallet API Test Suite")
    print("=" * 65)

    _ensure_server_running()

    tests = [
        tc_wlt_01_new_farmer_no_wallet,
        tc_wlt_02_balance_after_settlement,
        tc_wlt_03_rbac_guards,
        tc_wlt_04_unauthenticated,
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
        print("\n  All tests passed. Farmer Wallet API verified.")
        sys.exit(0)


if __name__ == "__main__":
    main()
