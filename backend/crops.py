"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    crops.py
Module:  Active Crop Management — Flask Blueprint
Version: 1.0  (Increment 1 - Foundation & Farmer Dashboard)
Source:  AG-API-INC1-003 v1.0  Section 4 & 5 | AG-SRS-INC1-001 v1.1

Endpoints
---------
  POST   /api/crops                   — Create crop listing
  GET    /api/crops                   — List all farmer's crops (paginated)
  GET    /api/crops/<int:listing_id>  — Retrieve single crop
  PUT    /api/crops/<int:listing_id>  — Update crop fields
  DELETE /api/crops/<int:listing_id>  — Soft-delete (Withdraw) crop

Zero-Trust Rules (AG-API-INC1-003 §1, §4)
------------------------------------------
  - farmer_id is ALWAYS extracted from g.farmer_id (JWT claim).
  - farmer_id is NEVER accepted from the request body.
  - Cross-tenant access returns HTTP 404 (not 403) to prevent
    resource enumeration (CTO Gap 3 Fix, §1 Architectural Principles).
  - Physical DELETE on the listings table is PROHIBITED.
    Retirement = UPDATE SET is_deleted=1, status='Withdrawn'.
"""

import sqlite3
from datetime import date, datetime, timezone, timedelta

from flask import Blueprint, g, jsonify, request, current_app

from auth import token_required, role_required

# ---------------------------------------------------------------------------
# Blueprint registration
# ---------------------------------------------------------------------------
crops_bp = Blueprint("crops", __name__, url_prefix="/api/crops")

# ---------------------------------------------------------------------------
# Domain constants (mirror schema CHECK constraints + API taxonomy)
# ---------------------------------------------------------------------------
VALID_CROP_NAMES = frozenset([
    "Wheat", "Rice", "Tomato", "Potato",
    "Cotton", "Maize", "Sugarcane", "Other",
])

VALID_STATUSES = frozenset([
    "Active", "Sold", "In Transit", "Delivered", "Withdrawn",
])

# Max planting date age for an active listing (AG-API-INC1-003 §4.1)
MAX_PLANTING_AGE_DAYS = 365


# ---------------------------------------------------------------------------
# Helper: db access via Blueprint
# ---------------------------------------------------------------------------
def _get_db() -> sqlite3.Connection:
    """
    Retrieve the per-request DB connection from Flask's g context
    via the application factory's get_db() helper.
    """
    return current_app.get_db()


# ---------------------------------------------------------------------------
# Helper: shared field validation for POST and PUT
# ---------------------------------------------------------------------------
def _validate_crop_payload(data: dict) -> tuple[dict | None, str | None, int | None]:
    """
    Validate and coerce a crop payload dict.

    Returns:
        (clean_fields, None, None)       on success
        (None, error_message, http_code) on validation failure

    Validates all fields defined in AG-API-INC1-003 §4.1 and §4.4.
    """
    # --- Required field presence ---
    required = [
        "crop_name", "planting_date", "estimated_harvest_date",
        "acreage", "gps_latitude", "gps_longitude", "quantity_kg",
    ]
    for field in required:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            return None, f"Missing required field: {field}.", 400

    crop_name = str(data["crop_name"]).strip()
    planting_date_str = str(data["planting_date"]).strip()
    harvest_date_str  = str(data["estimated_harvest_date"]).strip()

    # --- Crop taxonomy (AG-API-INC1-003 §4.1) ---
    if crop_name not in VALID_CROP_NAMES:
        return None, (
            "Invalid crop name. Must be one of: "
            "Wheat, Rice, Tomato, Potato, Cotton, Maize, Sugarcane, Other."
        ), 400

    # --- Date format validation (YYYY-MM-DD) ---
    try:
        planting_date = date.fromisoformat(planting_date_str)
    except ValueError:
        return None, "Invalid date format. Use YYYY-MM-DD.", 400

    try:
        harvest_date = date.fromisoformat(harvest_date_str)
    except ValueError:
        return None, "Invalid date format. Use YYYY-MM-DD.", 400

    today = date.today()

    # Planting date: cannot be in the future
    if planting_date > today:
        return None, "Planting date cannot be in the future.", 400

    # Planting date: cannot be older than 365 days (active listing rule)
    if (today - planting_date).days > MAX_PLANTING_AGE_DAYS:
        return None, "Planting date cannot be older than 365 days for an active listing.", 400

    # Harvest date must be strictly after planting date
    if harvest_date <= planting_date:
        return None, "Estimated harvest date must be after planting date.", 400

    # --- Numeric field validation ---
    try:
        acreage = float(data["acreage"])
    except (TypeError, ValueError):
        return None, "Acreage must be a positive number.", 400
    if acreage <= 0:
        return None, "Acreage must be a positive number.", 400

    try:
        gps_lat = float(data["gps_latitude"])
    except (TypeError, ValueError):
        return None, "GPS latitude must be a number between -90 and 90.", 400
    if not (-90.0 <= gps_lat <= 90.0):
        return None, "Latitude must be between -90 and 90.", 400

    try:
        gps_lon = float(data["gps_longitude"])
    except (TypeError, ValueError):
        return None, "GPS longitude must be a number between -180 and 180.", 400
    if not (-180.0 <= gps_lon <= 180.0):
        return None, "Longitude must be between -180 and 180.", 400

    try:
        quantity_kg = float(data["quantity_kg"])
    except (TypeError, ValueError):
        return None, "Quantity must be a positive number.", 400
    if quantity_kg <= 0:
        return None, "Quantity must be a positive number.", 400

    return {
        "crop_name":              crop_name,
        "planting_date":          planting_date_str,
        "estimated_harvest_date": harvest_date_str,
        "acreage":                acreage,
        "gps_latitude":           gps_lat,
        "gps_longitude":          gps_lon,
        "quantity_kg":            quantity_kg,
    }, None, None


# ---------------------------------------------------------------------------
# Helper: serialise a sqlite3.Row listing into a clean dict
# ---------------------------------------------------------------------------
def _row_to_dict_summary(row) -> dict:
    """List-view fields (AG-API-INC1-003 §4.2 response shape)."""
    return {
        "listing_id":             row["id"],
        "crop_name":              row["crop_name"],
        "planting_date":          row["planting_date"],
        "estimated_harvest_date": row["estimated_harvest_date"],
        "acreage":                row["acreage"],
        "quantity_kg":            row["quantity_kg"],
        "status":                 row["status"],
        "created_at":             row["created_at"],
    }


def _row_to_dict_full(row) -> dict:
    """Full detail fields (AG-API-INC1-003 §4.1 / §4.3 / §4.4 response shape)."""
    return {
        "listing_id":             row["id"],
        "farmer_id":              row["farmer_id"],
        "crop_name":              row["crop_name"],
        "planting_date":          row["planting_date"],
        "estimated_harvest_date": row["estimated_harvest_date"],
        "acreage":                row["acreage"],
        "gps_latitude":           row["gps_latitude"],
        "gps_longitude":          row["gps_longitude"],
        "quantity_kg":            row["quantity_kg"],
        "status":                 row["status"],
        "is_deleted":             bool(row["is_deleted"]),
        "created_at":             row["created_at"],
        "updated_at":             row["updated_at"],
    }


# ===========================================================================
# ROUTE 1 — POST /api/crops  (Create)
# AG-API-INC1-003 §4.1
# ===========================================================================
@crops_bp.route("", methods=["POST"])
@token_required
@role_required("farmer")
def create_crop():
    """
    Create a new active crop listing for the authenticated farmer.

    Zero-Trust: farmer_id is read exclusively from g.farmer_id (JWT).
    The request body MUST NOT contain farmer_id; any such key is silently ignored.
    """
    db = _get_db()

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request format."}), 400

    # Validate and coerce all fields
    fields, err, code = _validate_crop_payload(data)
    if err:
        return jsonify({"success": False, "error": err}), code

    # Tenant identity — ONLY from JWT, never from body
    farmer_id = g.farmer_id
    if farmer_id is None:
        # Farmer profile was not linked during login (data integrity issue)
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again later.",
        }), 500

    try:
        cursor = db.execute(
            """
            INSERT INTO listings
                (farmer_id, crop_name, planting_date, estimated_harvest_date,
                 acreage, gps_latitude, gps_longitude, quantity_kg,
                 status, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Active', 0)
            """,
            (
                farmer_id,
                fields["crop_name"],
                fields["planting_date"],
                fields["estimated_harvest_date"],
                fields["acreage"],
                fields["gps_latitude"],
                fields["gps_longitude"],
                fields["quantity_kg"],
            ),
        )
        db.commit()
        listing_id = cursor.lastrowid
    except sqlite3.Error:
        db.rollback()
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again later.",
        }), 500

    # Fetch the newly created row to return exact, DB-confirmed values
    row = db.execute(
        "SELECT * FROM listings WHERE id = ?", (listing_id,)
    ).fetchone()

    return jsonify({
        "success": True,
        "message": "Crop listing created successfully.",
        "data":    _row_to_dict_full(row),
    }), 201


# ===========================================================================
# ROUTE 2 — GET /api/crops  (List — Paginated)
# AG-API-INC1-003 §4.2
# ===========================================================================
@crops_bp.route("", methods=["GET"])
@token_required
@role_required("farmer")
def list_crops():
    """
    Return a paginated list of the authenticated farmer's non-deleted listings.

    Query params:
        page  (int, default=1,  min=1)
        limit (int, default=20, min=1, max=100)
        status (str, optional) — filter by lifecycle status
    """
    db = _get_db()
    farmer_id = g.farmer_id

    # -- Pagination parameters --
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(100, max(1, int(request.args.get("limit", 20))))
    except (TypeError, ValueError):
        limit = 20

    offset = (page - 1) * limit

    # -- Optional status filter --
    status_filter = request.args.get("status", "").strip() or None
    if status_filter and status_filter not in VALID_STATUSES:
        return jsonify({
            "success": False,
            "error": f"Invalid status filter. Must be one of: {', '.join(sorted(VALID_STATUSES))}.",
        }), 400

    # -- Build query (Zero-Trust: always AND farmer_id = ? AND is_deleted = 0) --
    if status_filter:
        count_row = db.execute(
            "SELECT COUNT(*) FROM listings WHERE farmer_id=? AND is_deleted=0 AND status=?",
            (farmer_id, status_filter),
        ).fetchone()
        rows = db.execute(
            """
            SELECT * FROM listings
            WHERE farmer_id=? AND is_deleted=0 AND status=?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (farmer_id, status_filter, limit, offset),
        ).fetchall()
    else:
        count_row = db.execute(
            "SELECT COUNT(*) FROM listings WHERE farmer_id=? AND is_deleted=0",
            (farmer_id,),
        ).fetchone()
        rows = db.execute(
            """
            SELECT * FROM listings
            WHERE farmer_id=? AND is_deleted=0
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            (farmer_id, limit, offset),
        ).fetchall()

    total = count_row[0]

    return jsonify({
        "success": True,
        "data":    [_row_to_dict_summary(r) for r in rows],
        "page":    page,
        "limit":   limit,
        "total":   total,
    }), 200


# ===========================================================================
# ROUTE 3 — GET /api/crops/<listing_id>  (Retrieve Single)
# AG-API-INC1-003 §4.3
# ===========================================================================
@crops_bp.route("/<int:listing_id>", methods=["GET"])
@token_required
@role_required("farmer")
def get_crop(listing_id: int):
    """
    Retrieve full details for a single listing.

    Enumeration defence (CTO Gap 3 Fix):
      If the record does not exist OR belongs to another farmer,
      return HTTP 404 — identical to non-existent ID.
      HTTP 403 is deliberately NOT used here.
    """
    db = _get_db()

    # Single query with farmer_id filter — prevents cross-tenant data leak
    row = db.execute(
        """
        SELECT * FROM listings
        WHERE id = ? AND farmer_id = ? AND is_deleted = 0
        """,
        (listing_id, g.farmer_id),
    ).fetchone()

    if row is None:
        return jsonify({"success": False, "error": "Listing not found."}), 404

    return jsonify({"success": True, "data": _row_to_dict_full(row)}), 200


# ===========================================================================
# ROUTE 4 — PUT /api/crops/<listing_id>  (Update)
# AG-API-INC1-003 §4.4
# ===========================================================================
@crops_bp.route("/<int:listing_id>", methods=["PUT"])
@token_required
@role_required("farmer")
def update_crop(listing_id: int):
    """
    Update mutable fields of an active listing.

    Ownership verification is performed inside the UPDATE WHERE clause
    (farmer_id = ? AND is_deleted = 0).  If 0 rows are affected, the
    listing either doesn't exist or belongs to another tenant — unified 404.
    """
    db = _get_db()

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request format."}), 400

    fields, err, code = _validate_crop_payload(data)
    if err:
        return jsonify({"success": False, "error": err}), code

    # Update with ownership guard — no separate SELECT needed
    try:
        cursor = db.execute(
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
                fields["crop_name"],
                fields["planting_date"],
                fields["estimated_harvest_date"],
                fields["acreage"],
                fields["gps_latitude"],
                fields["gps_longitude"],
                fields["quantity_kg"],
                listing_id,
                g.farmer_id,
            ),
        )
        db.commit()
    except sqlite3.Error:
        db.rollback()
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again later.",
        }), 500

    # If no rows were updated, the listing was not found or is cross-tenant
    if cursor.rowcount == 0:
        return jsonify({"success": False, "error": "Listing not found."}), 404

    # Return the updated record (trigger will have refreshed updated_at)
    row = db.execute(
        "SELECT * FROM listings WHERE id = ?", (listing_id,)
    ).fetchone()

    return jsonify({
        "success": True,
        "message": "Crop listing updated successfully.",
        "data":    _row_to_dict_full(row),
    }), 200


# ===========================================================================
# ROUTE 5 — DELETE /api/crops/<listing_id>  (Soft-Delete / Withdraw)
# AG-API-INC1-003 §4.5
# ===========================================================================
@crops_bp.route("/<int:listing_id>", methods=["DELETE"])
@token_required
@role_required("farmer")
def withdraw_crop(listing_id: int):
    """
    Withdraw a crop listing via soft-delete.

    CRITICAL: This endpoint NEVER issues a physical DELETE SQL statement.
    The row is archived in-place:
        is_deleted = 1
        status     = 'Withdrawn'
        updated_at = <current UTC timestamp>  (handled by schema trigger)

    This preserves the provenance chain for the future Increment 5
    Consumer QR storyboard (AG-API-INC1-003 §1 / CTO Blocker 3 Fix).
    """
    db = _get_db()

    try:
        cursor = db.execute(
            """
            UPDATE listings
               SET is_deleted = 1,
                   status     = 'Withdrawn'
             WHERE id = ? AND farmer_id = ? AND is_deleted = 0
            """,
            (listing_id, g.farmer_id),
        )
        db.commit()
    except sqlite3.Error:
        db.rollback()
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again later.",
        }), 500

    # 0 rows affected → listing not found, already withdrawn, or cross-tenant
    if cursor.rowcount == 0:
        return jsonify({"success": False, "error": "Listing not found."}), 404

    return jsonify({
        "success": True,
        "message": "Listing withdrawn successfully.",
    }), 200
