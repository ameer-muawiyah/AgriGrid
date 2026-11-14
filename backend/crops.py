"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    crops.py
Module:  Active Crop Management — Flask Blueprint Controller
Version: 2.0  (Increment 2 — Core Data Engine & Demand Side)
Author:  Hasnain Hamza (Core Backend Engineer)
Date:    2026-11-14
Source:  AG-API-INC1-003 v1.0 Section 4 & 5 | AG-PLAN-INC2-001 §4.2

Endpoints
---------
  POST   /api/crops                   — Create crop listing
  GET    /api/crops                   — List all farmer's crops (paginated)
  GET    /api/crops/stats             — Summary telemetry & metrics across active crops
  GET    /api/crops/<int:listing_id>  — Retrieve single crop
  PUT    /api/crops/<int:listing_id>  — Update crop fields
  DELETE /api/crops/<int:listing_id>  — Soft-delete (Withdraw) crop

Architectural Boundary (Package §B1):
------------------------------------
  - HTTP routing, JWT identity extraction, request parsing, response formatting,
    and payload validation stay in this controller.
  - VALID_CROP_NAMES and VALID_STATUSES stay in this file to satisfy AST-based
    contract verification in test_frontend_contract.py.
  - All database persistence, transaction management, and SQL execution are
    delegated to services.crop_service. Zero direct SQL in this module.
"""

import sqlite3
from datetime import date

from flask import Blueprint, g, jsonify, request, current_app

from auth import token_required, role_required
from services import crop_service

# ---------------------------------------------------------------------------
# Blueprint registration
# ---------------------------------------------------------------------------
crops_bp = Blueprint("crops", __name__, url_prefix="/api/crops")

# ---------------------------------------------------------------------------
# Domain constants (mirror schema CHECK constraints + API taxonomy)
# Pinned for AST inspection by backend/test_frontend_contract.py
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
    harvest_date_str = str(data["estimated_harvest_date"]).strip()

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
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again later.",
        }), 500

    try:
        listing = crop_service.create_listing(db, farmer_id, fields)
    except sqlite3.Error:
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again later.",
        }), 500

    return jsonify({
        "success": True,
        "message": "Crop listing created successfully.",
        "data":    listing,
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

    # -- Optional status filter --
    status_filter = request.args.get("status", "").strip() or None
    if status_filter and status_filter not in VALID_STATUSES:
        return jsonify({
            "success": False,
            "error": f"Invalid status filter. Must be one of: {', '.join(sorted(VALID_STATUSES))}.",
        }), 400

    listings, total = crop_service.list_listings(db, farmer_id, status_filter, page, limit)

    return jsonify({
        "success": True,
        "data":    listings,
        "page":    page,
        "limit":   limit,
        "total":   total,
    }), 200


# ===========================================================================
# ROUTE 2B — GET /api/crops/stats  (Summary Telemetry Metrics)
# ===========================================================================
@crops_bp.route("/stats", methods=["GET"])
@token_required
@role_required("farmer")
def get_crop_stats():
    """Return summary active acreage and projected yield for the farmer."""
    db = _get_db()
    stats = crop_service.get_stats(db, g.farmer_id)
    return jsonify({
        "success": True,
        "data":    stats,
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
    Enumeration defence: 404 returned if not found or cross-tenant.
    """
    db = _get_db()
    listing = crop_service.get_listing(db, g.farmer_id, listing_id)

    if listing is None:
        return jsonify({"success": False, "error": "Listing not found."}), 404

    return jsonify({"success": True, "data": listing}), 200


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
    Ownership verification is performed inside the service layer.
    """
    db = _get_db()

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "error": "Invalid request format."}), 400

    fields, err, code = _validate_crop_payload(data)
    if err:
        return jsonify({"success": False, "error": err}), code

    try:
        updated = crop_service.update_listing(db, g.farmer_id, listing_id, fields)
    except sqlite3.Error:
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again later.",
        }), 500

    if updated is None:
        return jsonify({"success": False, "error": "Listing not found."}), 404

    return jsonify({
        "success": True,
        "message": "Crop listing updated successfully.",
        "data":    updated,
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
    CRITICAL: Never issues a physical DELETE SQL statement.
    """
    db = _get_db()

    try:
        success = crop_service.withdraw_listing(db, g.farmer_id, listing_id)
    except sqlite3.Error:
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again later.",
        }), 500

    if not success:
        return jsonify({"success": False, "error": "Listing not found."}), 404

    return jsonify({
        "success": True,
        "message": "Listing withdrawn successfully.",
    }), 200
