"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    crop_service.py
Module:  Crop Management Service Layer
Version: 2.0  (Increment 2 — Core Data Engine & Demand Side)
Author:  Hasnain Hamza (Core Backend Engineer)
Date:    2026-11-14
Source:  AG-PLAN-INC2-001 §4.2 & Phase 1 Build Package (Part B)

Purpose
-------
Pure business logic and persistence service for farmer crop listings.
Decouples raw SQL queries, pagination math, transactions, and entity mapping
from HTTP routing and Flask controllers.

Extraction Boundary (Package §B1):
- Domain constants and payload validation remain in crops.py to preserve
  test_frontend_contract.py AST-based lock.
- All SQL statements, transaction boundaries, and row serialization functions
  are encapsulated in this service.
- Standard library only — NO Flask dependencies (request, g, jsonify, current_app).
- All DB connections are passed in explicitly by callers.
"""

import sqlite3
from datetime import datetime, timezone

CROP_CODE_MAP = {
    "Wheat":     "WHT",
    "Rice":      "RIC",
    "Tomato":    "TOM",
    "Potato":    "POT",
    "Cotton":    "COT",
    "Maize":     "MAI",
    "Sugarcane": "SUG",
}


def _get_crop_code(crop_name: str) -> str:
    """Return 3-letter uppercase crop taxonomy code, defaulting to 'OTH'."""
    return CROP_CODE_MAP.get(crop_name, "OTH")


def row_to_summary(row: sqlite3.Row) -> dict:
    """List-view fields (AG-API-INC1-003 §4.2 & AG-API-INC2-003 §8.1 shape)."""
    keys = row.keys() if hasattr(row, "keys") else ()
    return {
        "listing_id":             row["id"],
        "crop_name":              row["crop_name"],
        "batch_id":               row["batch_id"] if "batch_id" in keys else None,
        "planting_date":          row["planting_date"],
        "estimated_harvest_date": row["estimated_harvest_date"],
        "gps_latitude":           row["gps_latitude"],
        "gps_longitude":          row["gps_longitude"],
        "acreage":                row["acreage"],
        "quantity_kg":            row["quantity_kg"],
        "asking_price_per_kg":    row["asking_price_per_kg"] if "asking_price_per_kg" in keys else None,
        "status":                 row["status"],
        "created_at":             row["created_at"],
    }


def row_to_full(row: sqlite3.Row) -> dict:
    """Full detail fields (AG-API-INC1-003 §4.1/§4.3/§4.4 & AG-API-INC2-003 §8.1 shape)."""
    keys = row.keys() if hasattr(row, "keys") else ()
    return {
        "listing_id":             row["id"],
        "farmer_id":              row["farmer_id"],
        "crop_name":              row["crop_name"],
        "batch_id":               row["batch_id"] if "batch_id" in keys else None,
        "acreage":                row["acreage"],
        "quantity_kg":            row["quantity_kg"],
        "asking_price_per_kg":    row["asking_price_per_kg"] if "asking_price_per_kg" in keys else None,
        "planting_date":          row["planting_date"],
        "estimated_harvest_date": row["estimated_harvest_date"],
        "gps_latitude":           row["gps_latitude"],
        "gps_longitude":          row["gps_longitude"],
        "status":                 row["status"],
        "is_deleted":             bool(row["is_deleted"]),
        "created_at":             row["created_at"],
        "updated_at":             row["updated_at"],
    }


def create_listing(conn: sqlite3.Connection, farmer_id: int, cleaned: dict) -> dict:
    """
    Create a new active crop listing for the authenticated farmer.
    Commits on success, rolls back on error.
    """
    try:
        cursor = conn.execute(
            """
            INSERT INTO listings
                (farmer_id, crop_name, planting_date, estimated_harvest_date,
                 acreage, gps_latitude, gps_longitude, quantity_kg,
                 status, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active', 0)
            """,
            (
                farmer_id,
                cleaned["crop_name"],
                cleaned["planting_date"],
                cleaned["estimated_harvest_date"],
                cleaned["acreage"],
                cleaned["gps_latitude"],
                cleaned["gps_longitude"],
                cleaned["quantity_kg"],
            ),
        )
        conn.commit()
        listing_id = cursor.lastrowid
    except sqlite3.Error:
        conn.rollback()
        raise

    row = conn.execute(
        "SELECT * FROM listings WHERE id = ?", (listing_id,)
    ).fetchone()
    return row_to_full(row)


def list_listings(
    conn: sqlite3.Connection,
    farmer_id: int,
    status: str | None,
    page: int,
    limit: int,
) -> tuple[list[dict], int]:
    """
    Return paginated listing summaries and total count for a farmer.
    Enforces soft-delete filter (is_deleted = 0) and tenant filter (farmer_id = ?).
    """
    offset = (page - 1) * limit

    if status:
        count_row = conn.execute(
            "SELECT COUNT(*) FROM listings WHERE farmer_id=? AND is_deleted=0 AND status=?",
            (farmer_id, status),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT * FROM listings
            WHERE farmer_id=? AND is_deleted=0 AND status=?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (farmer_id, status, limit, offset),
        ).fetchall()
    else:
        count_row = conn.execute(
            "SELECT COUNT(*) FROM listings WHERE farmer_id=? AND is_deleted=0",
            (farmer_id,),
        ).fetchone()
        rows = conn.execute(
            """
            SELECT * FROM listings
            WHERE farmer_id=? AND is_deleted=0
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (farmer_id, limit, offset),
        ).fetchall()

    total = count_row[0] if count_row else 0
    return [row_to_summary(r) for r in rows], total


def get_listing(conn: sqlite3.Connection, farmer_id: int, listing_id: int) -> dict | None:
    """
    Retrieve full details of a listing.
    Returns None if not found, deleted, or owned by another tenant.
    """
    row = conn.execute(
        """
        SELECT * FROM listings
        WHERE id = ? AND farmer_id = ? AND is_deleted = 0
        """,
        (listing_id, farmer_id),
    ).fetchone()

    if row is None:
        return None
    return row_to_full(row)


def update_listing(
    conn: sqlite3.Connection,
    farmer_id: int,
    listing_id: int,
    cleaned: dict,
) -> dict | None:
    """
    Update mutable listing fields.
    Persists commercial asking price and generates unique batch_id if currently null.
    Returns None if 0 rows affected (not found or cross-tenant).
    """
    # 1. Fetch existing listing to verify ownership, active status, and current batch_id
    existing = conn.execute(
        "SELECT id, crop_name, batch_id, asking_price_per_kg FROM listings WHERE id = ? AND farmer_id = ? AND is_deleted = 0",
        (listing_id, farmer_id),
    ).fetchone()
    if not existing:
        return None

    try:
        if "asking_price_per_kg" in cleaned:
            # Set price and assign batch_id if currently NULL
            current_batch = existing["batch_id"]
            if current_batch:
                batch_id_to_persist = current_batch
            else:
                crop = cleaned.get("crop_name") or existing["crop_name"]
                code3 = _get_crop_code(crop)
                year = datetime.now(timezone.utc).year
                batch_id_to_persist = f"BATCH-{year}-{code3}-{listing_id:04d}"

            cursor = conn.execute(
                """
                UPDATE listings
                   SET crop_name              = ?,
                       planting_date          = ?,
                       estimated_harvest_date = ?,
                       acreage                = ?,
                       gps_latitude           = ?,
                       gps_longitude          = ?,
                       quantity_kg            = ?,
                       asking_price_per_kg    = ?,
                       batch_id               = ?
                 WHERE id = ? AND farmer_id = ? AND is_deleted = 0
                """,
                (
                    cleaned["crop_name"],
                    cleaned["planting_date"],
                    cleaned["estimated_harvest_date"],
                    cleaned["acreage"],
                    cleaned["gps_latitude"],
                    cleaned["gps_longitude"],
                    cleaned["quantity_kg"],
                    cleaned["asking_price_per_kg"],
                    batch_id_to_persist,
                    listing_id,
                    farmer_id,
                ),
            )
        else:
            cursor = conn.execute(
                """
                UPDATE listings
                   SET crop_name              = ?,
                       planting_date          = ?,
                       estimated_harvest_date = ?,
                       acreage                = ?,
                       gps_latitude           = ?,
                       gps_longitude          = ?,
                       quantity_kg            = ?
                 WHERE id = ? AND farmer_id = ? AND is_deleted = 0
                """,
                (
                    cleaned["crop_name"],
                    cleaned["planting_date"],
                    cleaned["estimated_harvest_date"],
                    cleaned["acreage"],
                    cleaned["gps_latitude"],
                    cleaned["gps_longitude"],
                    cleaned["quantity_kg"],
                    listing_id,
                    farmer_id,
                ),
            )
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise

    if cursor.rowcount == 0:
        return None

    row = conn.execute(
        "SELECT * FROM listings WHERE id = ?", (listing_id,)
    ).fetchone()
    return row_to_full(row)


def withdraw_listing(conn: sqlite3.Connection, farmer_id: int, listing_id: int) -> bool:
    """
    Soft-delete / withdraw an active listing.
    Never physically deletes the row.
    Returns False if 0 rows affected (not found or cross-tenant).
    """
    try:
        cursor = conn.execute(
            """
            UPDATE listings
               SET is_deleted = 1,
                   status     = 'Withdrawn'
             WHERE id = ? AND farmer_id = ? AND is_deleted = 0
            """,
            (listing_id, farmer_id),
        )
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise

    return cursor.rowcount > 0


def get_stats(conn: sqlite3.Connection, farmer_id: int | None = None) -> dict:
    """
    Compute summary telemetry metrics for active crops.
    Optionally scoped to a specific farmer_id.
    """
    if farmer_id is not None:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS active_fields,
                COALESCE(SUM(acreage), 0.0) AS total_acreage,
                COALESCE(SUM(quantity_kg), 0.0) AS total_yield
            FROM listings
            WHERE farmer_id = ? AND is_deleted = 0 AND status = 'Active'
            """,
            (farmer_id,),
        ).fetchone()
    else:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS active_fields,
                COALESCE(SUM(acreage), 0.0) AS total_acreage,
                COALESCE(SUM(quantity_kg), 0.0) AS total_yield
            FROM listings
            WHERE is_deleted = 0 AND status = 'Active'
            """,
        ).fetchone()

    return {
        "active_fields": row["active_fields"] if row else 0,
        "total_acreage": round(row["total_acreage"], 1) if row else 0.0,
        "projected_yield_kg": round(row["total_yield"]) if row else 0,
    }
