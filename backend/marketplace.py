"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    marketplace.py
Module:  B2B Produce Marketplace Blueprint & Routing
Version: 2.0  (Increment 2 — Core Data Engine & Demand Side)
Author:  Hasnain Hamza (Core Backend Engineer)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §5, Phase 2 Build Package (Part B) & AG-API-INC2-003 §5

Purpose
-------
Thin HTTP routing controller for the B2B wholesale marketplace catalog and
single produce listing inspection.
Enforces RBAC (buyer + farmer permitted; others receive 403 "Access denied.")
and input validation against domain whitelists.
All database access is delegated to backend/services/marketplace_service.py.
"""

import sqlite3
from flask import Blueprint, current_app, g, jsonify, request

from auth import token_required
from crops import VALID_CROP_NAMES
import services.marketplace_service as marketplace_service

marketplace_bp = Blueprint("marketplace", __name__, url_prefix="/api/marketplace")

VALID_SORT_OPTIONS = {"price_asc", "price_desc", "date_desc"}


def _get_db() -> sqlite3.Connection:
    """Return the per-request database connection from Flask's g context."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DB_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db


# ===========================================================================
# ROUTE 1 — GET /api/marketplace/listings  (Catalog Browse)
# AG-API-INC2-003 §5.1 (Endpoint 3)
# ===========================================================================
@marketplace_bp.route("/listings", methods=["GET"])
@token_required
def browse_catalog():
    """
    Browse wholesale produce catalog with pagination and filtering.
    Permitted roles: buyer, farmer (for market transparency).
    """
    if g.role not in ("buyer", "farmer"):
        return jsonify({"success": False, "error": "Access denied."}), 403

    db = _get_db()

    # 1. Parse & validate page
    page_param = request.args.get("page", "1")
    try:
        page = int(page_param)
        if page < 1:
            return jsonify({"success": False, "error": "Invalid filter parameters."}), 400
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid filter parameters."}), 400

    # 2. Parse & validate limit
    limit_param = request.args.get("limit", "20")
    try:
        limit = int(limit_param)
        if limit < 1:
            return jsonify({"success": False, "error": "Invalid filter parameters."}), 400
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "Invalid filter parameters."}), 400

    # 3. Parse & validate crop_name
    crop_name = request.args.get("crop_name")
    if crop_name is not None and crop_name.strip() != "":
        crop_name = crop_name.strip()
        if crop_name not in VALID_CROP_NAMES:
            return jsonify({"success": False, "error": "Invalid filter parameters."}), 400
    else:
        crop_name = None

    # 4. Parse & validate max_price
    max_price_param = request.args.get("max_price")
    max_price = None
    if max_price_param is not None and max_price_param.strip() != "":
        try:
            max_price = float(max_price_param)
            if max_price <= 0:
                return jsonify({"success": False, "error": "Invalid filter parameters."}), 400
        except (TypeError, ValueError):
            return jsonify({"success": False, "error": "Invalid filter parameters."}), 400

    # 5. Parse & validate sort
    sort = request.args.get("sort", "date_desc").strip()
    if sort not in VALID_SORT_OPTIONS:
        return jsonify({"success": False, "error": "Invalid filter parameters."}), 400

    # Execute query via service
    try:
        items, total = marketplace_service.list_marketplace_listings(
            db,
            page=page,
            limit=limit,
            crop_name=crop_name,
            max_price=max_price,
            sort=sort,
        )
    except Exception:
        return jsonify({"success": False, "error": "Failed to retrieve marketplace catalog."}), 500

    return jsonify({
        "success": True,
        "data":    items,
        "page":    page,
        "limit":   limit,
        "total":   total,
    }), 200


# ===========================================================================
# ROUTE 2 — GET /api/marketplace/listings/<id>  (Listing Detail)
# AG-API-INC2-003 §5.2 (Endpoint 4)
# ===========================================================================
@marketplace_bp.route("/listings/<int:listing_id>", methods=["GET"])
@token_required
def get_listing_detail(listing_id: int):
    """
    Retrieve single produce listing detail for checkout inspection.
    Permitted roles: buyer, farmer.
    Returns 404 "Listing not found." for non-existent, unpriced, or withdrawn listings.
    """
    if g.role not in ("buyer", "farmer"):
        return jsonify({"success": False, "error": "Access denied."}), 403

    db = _get_db()

    try:
        listing = marketplace_service.get_marketplace_listing(db, listing_id)
    except Exception:
        return jsonify({"success": False, "error": "Failed to retrieve listing detail."}), 500

    if listing is None:
        return jsonify({"success": False, "error": "Listing not found."}), 404

    return jsonify({
        "success": True,
        "data":    listing,
    }), 200
