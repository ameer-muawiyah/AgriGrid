"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    test_auth.py
Module:  Authentication Pipeline Self-Verification
Version: 1.0  (Increment 1 - Foundation & Farmer Dashboard)
Source:  AG-API-INC1-003 v1.0

Purpose
-------
Standalone end-to-end test script that verifies the entire authentication
pipeline before Run 3 begins. Launches the Flask dev server in a background
thread, then exercises all auth endpoints and the RBAC guard decorator.

Test Cases
----------
  TC-01  Register a new farmer account (expect 201)
  TC-02  Attempt to register with the same username (expect 409 conflict)
  TC-03  Register a buyer account (expect 201, farmer_id must be null)
  TC-04  Login with valid credentials — new farmer (expect 200 + JWT)
  TC-05  Login with wrong password (expect 401, generic message)
  TC-06  Login with non-existent username (expect 401, generic message)
  TC-07  Login as seed farmer 'tahir_farmer' (tests pbkdf2$ backward-compat)
  TC-08  Access protected /api/auth/me with valid token (expect 200)
  TC-09  Access protected /api/auth/me with no token (expect 401)
  TC-10  Access protected /api/auth/me with a tampered token (expect 401)
  TC-11  Access farmer-only /dashboard/farmer as farmer (expect 200)
  TC-12  Access farmer-only /dashboard/farmer as buyer (expect 403)
  TC-13  Logout with valid token (expect 200)
  TC-14  Register farmer without farm_name (expect 400)
  TC-15  Register with weak password (expect 400)
  TC-16  Access protected /api/auth/me with expired token (expect 401)

Usage
-----
  python backend/test_auth.py        (from project root)
  python test_auth.py                (from backend/ directory)
"""

import sys
import os
import time
import threading
from datetime import datetime, timezone, timedelta
import requests
import jwt

# ---------------------------------------------------------------------------
# Path setup — allow imports from backend/ regardless of CWD
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from app import create_app  # noqa: E402

# ---------------------------------------------------------------------------
# Server Configuration
# ---------------------------------------------------------------------------
TEST_HOST = "127.0.0.1"
TEST_PORT = 5001          # Use 5001 to avoid conflict with a running dev server
BASE_URL  = f"http://{TEST_HOST}:{TEST_PORT}"

# ---------------------------------------------------------------------------
# Test State
# ---------------------------------------------------------------------------
RESULTS: list[dict] = []
_farmer_token: str = ""
_buyer_token:  str = ""
RUN_ID = str(int(time.time()))
FARMER_USERNAME = f"test_farmer_tc01_{RUN_ID}"
BUYER_USERNAME = f"test_buyer_tc03_{RUN_ID}"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pass(tc: str, desc: str, detail: str = "") -> None:
    status = f"[PASS] {tc}: {desc}"
    if detail:
        status += f"\n       {detail}"
    print(status)
    RESULTS.append({"tc": tc, "status": "PASS", "desc": desc})


def _fail(tc: str, desc: str, detail: str = "") -> None:
    status = f"[FAIL] {tc}: {desc}"
    if detail:
        status += f"\n       {detail}"
    print(status)
    RESULTS.append({"tc": tc, "status": "FAIL", "desc": desc})


def _check(tc: str, desc: str, condition: bool, detail: str = "") -> None:
    if condition:
        _pass(tc, desc, detail)
    else:
        _fail(tc, desc, detail)


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Flask server thread
# ---------------------------------------------------------------------------

def _start_server(app):
    """Run Flask in a daemon thread — exits when the main thread exits."""
    app.run(host=TEST_HOST, port=TEST_PORT, debug=False, use_reloader=False)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def tc01_register_new_farmer():
    global _farmer_token
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username":  FARMER_USERNAME,
        "password":  "TestPass1A",
        "role":      "farmer",
        "farm_name": "TC01 Test Farm",
    })
    body = r.json()
    ok = (
        r.status_code == 201
        and body.get("success") is True
        and body.get("user", {}).get("farmer_id") is not None
        and body.get("user", {}).get("role") == "farmer"
    )
    _check("TC-01", "Register new farmer", ok,
           f"status={r.status_code} farmer_id={body.get('user', {}).get('farmer_id')}")


def tc02_duplicate_username():
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username":  FARMER_USERNAME,   # same as TC-01
        "password":  "TestPass1A",
        "role":      "farmer",
        "farm_name": "Duplicate Farm",
    })
    body = r.json()
    _check("TC-02", "Duplicate username rejected (409)",
           r.status_code == 409 and "already exists" in body.get("error", ""),
           f"status={r.status_code} error='{body.get('error')}'")


def tc03_register_buyer():
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": BUYER_USERNAME,
        "password": "BuyerPass1B",
        "role":     "buyer",
    })
    body = r.json()
    _check("TC-03", "Register buyer (farmer_id must be null)",
           r.status_code == 201
           and body.get("user", {}).get("farmer_id") is None
           and body.get("user", {}).get("role") == "buyer",
           f"status={r.status_code} farmer_id={body.get('user', {}).get('farmer_id')}")


def tc04_login_valid():
    global _farmer_token
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": FARMER_USERNAME,
        "password": "TestPass1A",
    })
    body = r.json()
    token = body.get("token", "")
    _farmer_token = token
    _check("TC-04", "Login with valid farmer credentials (200 + JWT)",
           r.status_code == 200
           and body.get("success") is True
           and len(token) > 20
           and body.get("role") == "farmer",
           f"status={r.status_code} token_len={len(token)} role='{body.get('role')}'")


def tc05_login_wrong_password():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": FARMER_USERNAME,
        "password": "WrongPassword9",
    })
    body = r.json()
    _check("TC-05", "Wrong password returns generic 401",
           r.status_code == 401
           and body.get("error") == "Invalid credentials.",
           f"status={r.status_code} error='{body.get('error')}'")


def tc06_login_nonexistent_user():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "ghost_user_xyz",
        "password": "SomePass1A",
    })
    body = r.json()
    _check("TC-06", "Non-existent username returns generic 401 (anti-enumeration)",
           r.status_code == 401
           and body.get("error") == "Invalid credentials.",
           f"status={r.status_code} error='{body.get('error')}'")


def tc07_login_seed_farmer_pbkdf2():
    """
    Tests backward-compatible pbkdf2$ hash verification.
    tahir_farmer was seeded by init_db.py using stdlib PBKDF2-HMAC-SHA256.
    """
    r = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "tahir_farmer",
        "password": "FarmSecure1",
    })
    body = r.json()
    _check("TC-07", "Seed farmer login (pbkdf2$ backward-compat)",
           r.status_code == 200
           and body.get("success") is True
           and body.get("role") == "farmer",
           f"status={r.status_code} farmer_id={body.get('user', {}).get('farmer_id')}")


def tc08_protected_route_valid_token():
    global _farmer_token
    if not _farmer_token:
        _fail("TC-08", "Protected /api/auth/me — skipped (no token from TC-04)")
        return
    r = requests.get(f"{BASE_URL}/api/auth/me",
                     headers=auth_header(_farmer_token))
    body = r.json()
    _check("TC-08", "Authenticated GET /api/auth/me with valid token (200)",
           r.status_code == 200
           and body.get("success") is True
           and body.get("role") == "farmer",
           f"status={r.status_code} user_id={body.get('user_id')} role='{body.get('role')}'")


def tc09_protected_route_no_token():
    r = requests.get(f"{BASE_URL}/api/auth/me")
    body = r.json()
    _check("TC-09", "Missing token returns 401",
           r.status_code == 401 and body.get("success") is False,
           f"status={r.status_code} error='{body.get('error')}'")


def tc10_protected_route_tampered_token():
    r = requests.get(f"{BASE_URL}/api/auth/me",
                     headers=auth_header("eyJhbGciOiJIUzI1NiJ9.TAMPERED.signature"))
    body = r.json()
    _check("TC-10", "Tampered/invalid token returns 401",
           r.status_code == 401 and body.get("success") is False,
           f"status={r.status_code} error='{body.get('error')}'")


def tc11_farmer_dashboard_as_farmer():
    global _farmer_token
    if not _farmer_token:
        _fail("TC-11", "/dashboard/farmer RBAC — skipped (no token)")
        return
    r = requests.get(f"{BASE_URL}/dashboard/farmer",
                     headers=auth_header(_farmer_token))
    _check("TC-11", "Farmer token accesses /dashboard/farmer (200)",
           r.status_code == 200,
           f"status={r.status_code}")


def tc12_farmer_dashboard_as_buyer():
    global _buyer_token
    # Login as buyer first
    r_login = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": BUYER_USERNAME,
        "password": "BuyerPass1B",
    })
    if r_login.status_code != 200:
        _fail("TC-12", "/dashboard/farmer RBAC — buyer login failed, skipped")
        return
    _buyer_token = r_login.json().get("token", "")
    r = requests.get(f"{BASE_URL}/dashboard/farmer",
                     headers=auth_header(_buyer_token))
    body = r.json()
    _check("TC-12", "Buyer token blocked from /dashboard/farmer (403)",
           r.status_code == 403 and "Access denied" in body.get("error", ""),
           f"status={r.status_code} error='{body.get('error')}'")


def tc13_logout():
    global _farmer_token
    if not _farmer_token:
        _fail("TC-13", "Logout — skipped (no token)")
        return
    r = requests.post(f"{BASE_URL}/api/auth/logout",
                      headers=auth_header(_farmer_token))
    body = r.json()
    _check("TC-13", "Logout with valid token (200)",
           r.status_code == 200
           and body.get("success") is True
           and "Logged out" in body.get("message", ""),
           f"status={r.status_code} message='{body.get('message')}'")


def tc14_register_farmer_without_farm_name():
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "no_farm_farmer",
        "password": "TestPass1A",
        "role":     "farmer",
        # farm_name intentionally omitted
    })
    body = r.json()
    _check("TC-14", "Farmer registration without farm_name rejected (400)",
           r.status_code == 400
           and "farm name" in body.get("error", "").lower(),
           f"status={r.status_code} error='{body.get('error')}'")


def tc15_weak_password():
    r = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "weak_pass_user",
        "password": "weak",       # too short, no uppercase, no digit
        "role":     "buyer",
    })
    body = r.json()
    _check("TC-15", "Weak password rejected (400)",
           r.status_code == 400 and body.get("success") is False,
           f"status={r.status_code} error='{body.get('error')}'")


def tc16_expired_token():
    now = datetime.now(timezone.utc)
    expired_payload = {
        "user_id":   1,
        "farmer_id": 1,
        "role":      "farmer",
        "iat":       now - timedelta(minutes=60),
        "exp":       now - timedelta(seconds=10),
    }
    secret = os.environ.get(
        "AGRIGRID_JWT_SECRET",
        "agrigrid-dev-secret-CHANGE-IN-PRODUCTION-2026",
    )
    expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")
    r = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_header(expired_token))
    body = r.json()
    _check("TC-16", "Expired token returns 401 Unauthorized",
           r.status_code == 401
           and body.get("success") is False
           and "expired" in body.get("error", "").lower(),
           f"status={r.status_code} error='{body.get('error')}'")


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  AGRI-GRID  Authentication Pipeline  —  Run 2 V&V")
    print("=" * 60)

    # -- Start Flask server in a background thread ----------------------
    app = create_app()
    server_thread = threading.Thread(
        target=_start_server, args=(app,), daemon=True
    )
    server_thread.start()

    # Wait for the server to be ready (poll with timeout)
    print(f"\n[BOOT] Starting test server on {BASE_URL} …")
    for attempt in range(20):
        time.sleep(0.5)
        try:
            requests.get(f"{BASE_URL}/api/auth/me", timeout=1)
            break
        except requests.exceptions.ConnectionError:
            pass
    else:
        print("[FATAL] Server did not start within 10 seconds.")
        sys.exit(1)
    print(f"[BOOT] Server ready.\n")

    # -- Execute all test cases -----------------------------------------
    tests = [
        tc01_register_new_farmer,
        tc02_duplicate_username,
        tc03_register_buyer,
        tc04_login_valid,
        tc05_login_wrong_password,
        tc06_login_nonexistent_user,
        tc07_login_seed_farmer_pbkdf2,
        tc08_protected_route_valid_token,
        tc09_protected_route_no_token,
        tc10_protected_route_tampered_token,
        tc11_farmer_dashboard_as_farmer,
        tc12_farmer_dashboard_as_buyer,
        tc13_logout,
        tc14_register_farmer_without_farm_name,
        tc15_weak_password,
        tc16_expired_token,
    ]

    for test_fn in tests:
        try:
            test_fn()
        except Exception as exc:
            tc_name = test_fn.__name__.replace("tc", "TC-").replace("_", " ", 1)
            _fail(tc_name, f"Unexpected exception: {exc}")

    # -- Summary --------------------------------------------------------
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    total  = len(RESULTS)

    print()
    print("=" * 60)
    print(f"  RESULTS: {passed}/{total} passed  |  {failed} failed")
    print("=" * 60)

    if failed:
        print("\n  Failed tests:")
        for r in RESULTS:
            if r["status"] == "FAIL":
                print(f"    - {r['tc']}: {r['desc']}")
        print()
        sys.exit(1)
    else:
        print("\n  All tests passed. Authentication pipeline verified.")
        print("  agrigrid.db is ready for Run 3 (Crop CRUD endpoints).")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
