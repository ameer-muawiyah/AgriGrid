"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    init_db.py
Version: 1.0  (Increment 1 â€” Foundation & Farmer Dashboard)
Source:  AG-SRS-INC1-001 v1.1  |  AG-API-INC1-003 v1.0
Author:  Database & Backend Agent (DBA)
Date:    2026-10-12

Purpose
-------
Bootstrap the agrigrid.db SQLite database from schema.sql, then seed it
with two test accounts and two sample crop listings so the backend and
frontend teams can immediately exercise RBAC and CRUD flows.

Seed Accounts
-------------
  1. tahir_farmer   | role: farmer          | password: FarmSecure1  (hashed)
     â””â”€ Farmer profile: "Green Acres Organic Field"
     â””â”€ 2 active crop listings (Wheat, Tomato)

  2. sara_buyer     | role: buyer           | password: BuyerPass1   (hashed)
     â””â”€ No farmer profile â€” used to verify RBAC 403 rejection in Run 3.

Execution Boundary
------------------
  This script is STRICTLY a DBA initializer.
  It does NOT define Flask routes, JWT logic, or API handlers.
  Those belong to Run 2 (Flask app factory) and Run 3 (RBAC middleware).

Usage
-----
  python backend/database/init_db.py          # from project root
  python init_db.py                           # from backend/database/
"""

import sqlite3
import os
import sys
import hashlib
import hmac
import base64

# ---------------------------------------------------------------------------
# Path resolution â€” script is runnable from both project root AND its own dir
# ---------------------------------------------------------------------------
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH  = os.path.join(SCRIPT_DIR, "schema.sql")
DB_PATH      = os.path.join(SCRIPT_DIR, "agrigrid.db")


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
# NOTE: Run 2 will integrate bcrypt (pip install bcrypt) for production-grade
#       hashing.  For this seed-only script â€” which runs before the full
#       Python environment is guaranteed â€” we use PBKDF2-HMAC-SHA256 from
#       the standard library so there are ZERO external dependencies.
#       The stored format is:  pbkdf2$<iterations>$<salt_hex>$<hash_hex>
#       The Flask auth layer in Run 2 will transition to bcrypt for new
#       passwords; the seed hashes here are for DBA/test use only.

PBKDF2_ITERATIONS = 260_000  # OWASP 2024 minimum recommendation

def hash_password(plaintext: str) -> str:
    """Return a PBKDF2-HMAC-SHA256 password hash string (no external deps)."""
    salt = os.urandom(32)
    dk = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=plaintext.encode("utf-8"),
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------
SEED_USERS = [
    # (username, plaintext_password, role, email)
    ("tahir_farmer", "FarmSecure1",  "farmer", "tahir@greenacres.pk"),
    ("sara_buyer",   "BuyerPass1",   "buyer",  "sara@agrobuyer.pk"),
]

SEED_FARMER_PROFILE = {
    # keyed by username
    "tahir_farmer": {
        "farm_name":              "Green Acres Organic Field",
        "farm_location":          "Punjab, Pakistan",
        "default_gps_latitude":   30.3753,
        "default_gps_longitude":  69.3451,
    }
}

# Two active crop listings for tahir_farmer (farmer_id will be resolved at
# runtime after the farmers row is inserted).
SEED_LISTINGS = [
    {
        "crop_name":               "Wheat",
        "planting_date":           "2026-09-01",
        "estimated_harvest_date":  "2027-01-15",
        "acreage":                 12.5,
        "gps_latitude":            30.3753,
        "gps_longitude":           69.3451,
        "quantity_kg":             5000.00,
        "status":                  "Active",
    },
    {
        "crop_name":               "Tomato",
        "planting_date":           "2026-09-20",
        "estimated_harvest_date":  "2026-12-10",
        "acreage":                 4.0,
        "gps_latitude":            30.3800,
        "gps_longitude":           69.3500,
        "quantity_kg":             1800.00,
        "status":                  "Active",
    },
]


# ---------------------------------------------------------------------------
# Core initializer
# ---------------------------------------------------------------------------

def load_schema(conn: sqlite3.Connection) -> None:
    """Read and execute schema.sql against the open connection."""
    if not os.path.exists(SCHEMA_PATH):
        print(f"[FATAL] schema.sql not found at: {SCHEMA_PATH}")
        sys.exit(1)

    with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
        schema_sql = fh.read()

    # executescript() handles multi-statement DDL and commits automatically.
    conn.executescript(schema_sql)
    print(f"[OK]    Schema executed from: {SCHEMA_PATH}")


def seed_data(conn: sqlite3.Connection) -> None:
    """
    Insert seed records inside a single ACID transaction.
    If any INSERT fails the entire transaction is rolled back, leaving the
    DB in a clean state (ACID â€“ Atomicity guarantee).
    """
    cursor = conn.cursor()

    # -- PRAGMA inside transaction (must be set per-connection) ----------
    cursor.execute("PRAGMA foreign_keys = ON;")

    # -- 1. Users --------------------------------------------------------
    print("\n[SEED]  Inserting users â€¦")
    user_ids: dict[str, int] = {}

    for username, plaintext, role, email in SEED_USERS:
        # Idempotent: skip if already present (re-run safety)
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        existing = cursor.fetchone()
        if existing:
            user_ids[username] = existing[0]
            print(f"        SKIP  users â†’ '{username}' (already exists, id={existing[0]})")
            continue

        pw_hash = hash_password(plaintext)
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, role, email)
            VALUES (?, ?, ?, ?)
            """,
            (username, pw_hash, role, email),
        )
        user_ids[username] = cursor.lastrowid
        print(f"        INSERT users â†’ '{username}' (role={role}, id={cursor.lastrowid})")

    # -- 2. Farmer profiles ----------------------------------------------
    print("\n[SEED]  Inserting farmer profiles â€¦")
    farmer_ids: dict[str, int] = {}

    for username, profile in SEED_FARMER_PROFILE.items():
        uid = user_ids.get(username)
        if uid is None:
            print(f"        WARN  farmers â†’ no user_id for '{username}', skipping.")
            continue

        cursor.execute("SELECT id FROM farmers WHERE user_id = ?", (uid,))
        existing = cursor.fetchone()
        if existing:
            farmer_ids[username] = existing[0]
            print(f"        SKIP  farmers â†’ '{username}' profile (already exists, id={existing[0]})")
            continue

        cursor.execute(
            """
            INSERT INTO farmers
                (user_id, farm_name, farm_location,
                 default_gps_latitude, default_gps_longitude)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                uid,
                profile["farm_name"],
                profile["farm_location"],
                profile["default_gps_latitude"],
                profile["default_gps_longitude"],
            ),
        )
        farmer_ids[username] = cursor.lastrowid
        print(f"        INSERT farmers â†’ '{profile['farm_name']}' (id={cursor.lastrowid}, user_id={uid})")

    # -- 3. Crop listings ------------------------------------------------
    print("\n[SEED]  Inserting crop listings â€¦")
    fid = farmer_ids.get("tahir_farmer")
    if fid is None:
        print("        WARN  listings â†’ farmer_id for 'tahir_farmer' not found. Skipping listings.")
    else:
        # Only seed if the farmer has no listings yet (idempotency)
        cursor.execute(
            "SELECT COUNT(*) FROM listings WHERE farmer_id = ? AND is_deleted = 0",
            (fid,),
        )
        existing_count = cursor.fetchone()[0]

        if existing_count >= len(SEED_LISTINGS):
            print(f"        SKIP  listings â†’ {existing_count} active listing(s) already exist for farmer_id={fid}.")
        else:
            for listing in SEED_LISTINGS:
                cursor.execute(
                    """
                    INSERT INTO listings
                        (farmer_id, crop_name, planting_date, estimated_harvest_date,
                         acreage, gps_latitude, gps_longitude, quantity_kg, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fid,
                        listing["crop_name"],
                        listing["planting_date"],
                        listing["estimated_harvest_date"],
                        listing["acreage"],
                        listing["gps_latitude"],
                        listing["gps_longitude"],
                        listing["quantity_kg"],
                        listing["status"],
                    ),
                )
                print(
                    f"        INSERT listings â†’ crop='{listing['crop_name']}' "
                    f"| {listing['acreage']} acres | {listing['quantity_kg']} kg "
                    f"(id={cursor.lastrowid}, farmer_id={fid})"
                )

    conn.commit()
    print("\n[OK]    Seed transaction committed successfully.")


# ---------------------------------------------------------------------------
# Verification block
# ---------------------------------------------------------------------------

def verify(conn: sqlite3.Connection) -> None:
    """
    Post-seed sanity checks â€” prints table names and record counts.
    Verifies that foreign keys are active by attempting a controlled
    FK-violating INSERT and confirming it is rejected.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys;")
    fk_status = cursor.fetchone()[0]

    print("\n" + "=" * 60)
    print("  AGRI-GRID DATABASE VERIFICATION REPORT")
    print("=" * 60)
    print(f"  DB Path          : {DB_PATH}")
    print(f"  Foreign Keys ON  : {'YES âœ“' if fk_status else 'NO âœ— â€” CRITICAL ERROR'}")
    print()

    # Table existence + row counts
    tables = ["users", "farmers", "listings"]
    for tbl in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
        count = cursor.fetchone()[0]
        print(f"  Table '{tbl}':  {count} row(s)")

    # Spot-check: farmers.user_id FK integrity
    print()
    cursor.execute(
        """
        SELECT u.username, u.role, f.farm_name
          FROM farmers f
          JOIN users u ON f.user_id = u.id
        """
    )
    rows = cursor.fetchall()
    print("  Farmer â†” User JOIN check:")
    for row in rows:
        print(f"    username='{row[0]}' | role='{row[1]}' | farm='{row[2]}'")

    # Spot-check: listing ownership chain
    print()
    cursor.execute(
        """
        SELECT l.id, l.crop_name, l.status, l.is_deleted,
               f.farm_name, u.username
          FROM listings l
          JOIN farmers f ON l.farmer_id = f.id
          JOIN users   u ON f.user_id   = u.id
        """
    )
    rows = cursor.fetchall()
    print("  Listings â†” Farmer â†” User chain check:")
    for row in rows:
        deleted_flag = "DELETED" if row[3] else "live"
        print(
            f"    listing_id={row[0]} | crop='{row[1]}' | status='{row[2]}' "
            f"| {deleted_flag} | farm='{row[4]}' | user='{row[5]}'"
        )

    # FK enforcement test: insert a listing with a non-existent farmer_id
    print()
    print("  FK enforcement test (expect IntegrityError) â€¦")
    try:
        cursor.execute(
            """
            INSERT INTO listings
                (farmer_id, crop_name, planting_date, estimated_harvest_date,
                 acreage, gps_latitude, gps_longitude, quantity_kg)
            VALUES (99999, 'Wheat', '2026-01-01', '2026-06-01',
                    1.0, 30.0, 70.0, 100.0)
            """
        )
        conn.commit()
        print("  [FAIL] FK constraint was NOT enforced â€” schema problem!")
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        print(f"  [PASS] FK constraint correctly rejected orphan insert: {exc}")

    print()
    print("  RBAC test accounts summary:")
    cursor.execute("SELECT username, role, is_active FROM users ORDER BY id")
    for row in cursor.fetchall():
        active_flag = "active" if row[2] else "inactive"
        print(f"    {row[0]:20s} | role={row[1]:20s} | {active_flag}")

    print()
    print("=" * 60)
    print("  Verification complete. agrigrid.db is ready for Run 2.")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  AGRI-GRID DB INITIALIZER  â€”  Increment 1")
    print("=" * 60)
    print(f"  Target DB : {DB_PATH}")
    print(f"  Schema    : {SCHEMA_PATH}")
    print()

    # Open (or create) the database file
    conn = sqlite3.connect(DB_PATH)

    # Enable FK enforcement for this connection (schema.sql also sets it,
    # but executescript() doesn't retain PRAGMA state across connections).
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        load_schema(conn)
        seed_data(conn)
        verify(conn)
    except Exception as exc:
        conn.rollback()
        print(f"\n[FATAL] Unhandled exception during initialization: {exc}")
        raise
    finally:
        conn.close()
        print("\n[OK]    Database connection closed cleanly.")


if __name__ == "__main__":
    main()

