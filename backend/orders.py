"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    orders.py
Module:  Escrow Orders & Settlement Blueprint
Version: 2.0  (Increment 2 — Escrow Orders & Settlement)
Author:  Hasnain Hamza (Core Backend Engineer)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §5, Phase 3 Build Package, AG-API-INC2-003 §6 (Endpoints 5–10)

Purpose
-------
HTTP controller for digital escrow checkout, order lifecycle transitions
(confirm delivery, cancel, dispute), and multi-tenant order history retrieval.
Enforces RBAC and input validation. All persistence and transaction logic is
delegated to backend/services/order_service.py and backend/services/escrow_service.py.
"""

import sqlite3
from flask import Blueprint, current_app, g, jsonify, request

from auth import token_required
import services.order_service as order_service
from services.order_service import (
    OrderError,
    VALID_ORDER_STATUSES,
)

orders_bp = Blueprint("orders", __name__, url_prefix="/api/orders")

ALLOWED_QUERY_PARAMS = {"status", "page", "limit"}


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
# ROUTE 1 — POST /api/orders  (Checkout)
# AG-API-INC2-003 §6.1 (Endpoint 5 / Diagram 3)
# ===========================================================================
@orders_bp.route("", methods=["POST"])
@token_required
def checkout_order():
    """
    Atomic B2B procurement checkout, locking funds in escrow.
    Role: buyer only.
    """
    if g.role != "buyer":
        return jsonify({"success": False, "error": "Access denied."}), 403

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"success": False, "error": "All checkout fields are required."}), 400

    # 1. Required fields presence and type validation
    listing_id = payload.get("listing_id")
    ordered_quantity_kg = payload.get("ordered_quantity_kg")
    destination_warehouse = payload.get("destination_warehouse")
    max_temperature_celsius = payload.get("max_temperature_celsius")

    if (
        listing_id is None
        or ordered_quantity_kg is None
        or destination_warehouse is None
        or max_temperature_celsius is None
    ):
        return jsonify({"success": False, "error": "All checkout fields are required."}), 400

    if not isinstance(listing_id, int) or isinstance(listing_id, bool):
        return jsonify({"success": False, "error": "All checkout fields are required."}), 400

    if (
        not isinstance(ordered_quantity_kg, (int, float))
        or isinstance(ordered_quantity_kg, bool)
        or ordered_quantity_kg <= 0
    ):
        return jsonify({"success": False, "error": "All checkout fields are required."}), 400

    if not isinstance(destination_warehouse, str) or len(destination_warehouse.strip()) < 5:
        return jsonify({"success": False, "error": "All checkout fields are required."}), 400

    if not isinstance(max_temperature_celsius, (int, float)) or isinstance(max_temperature_celsius, bool):
        return jsonify({"success": False, "error": "All checkout fields are required."}), 400

    db = _get_db()
    try:
        result = order_service.create_order(
            conn=db,
            buyer_id=g.buyer_id,
            listing_id=listing_id,
            ordered_quantity_kg=float(ordered_quantity_kg),
            destination_warehouse=destination_warehouse.strip(),
            max_temperature_celsius=float(max_temperature_celsius),
        )
        return jsonify({
            "success": True,
            "message": "Order created successfully. Escrow funds locked.",
            "data": result,
        }), 201
    except OrderError as err:
        return jsonify({"success": False, "error": err.message}), err.status_code


# ===========================================================================
# ROUTE 2 — POST /api/orders/<id>/confirm-delivery
# AG-API-INC2-003 §6.2 (Endpoint 6 / Diagram 4)
# ===========================================================================
@orders_bp.route("/<int:order_id>/confirm-delivery", methods=["POST"])
@token_required
def confirm_delivery(order_id: int):
    """
    Buyer quality acceptance and escrow release endpoint.
    Role: buyer only.
    """
    if g.role != "buyer":
        return jsonify({"success": False, "error": "Access denied."}), 403

    db = _get_db()
    try:
        result = order_service.confirm_delivery(
            conn=db,
            order_id=order_id,
            caller_buyer_id=g.buyer_id,
        )
        return jsonify({
            "success": True,
            "message": "Delivery confirmed and escrow funds released to farmer.",
            "data": result,
        }), 200
    except OrderError as err:
        return jsonify({"success": False, "error": err.message}), err.status_code


# ===========================================================================
# ROUTE 3 — POST /api/orders/<id>/cancel
# AG-API-INC2-003 §6.3 (Endpoint 7 / Diagram 5)
# ===========================================================================
@orders_bp.route("/<int:order_id>/cancel", methods=["POST"])
@token_required
def cancel_order(order_id: int):
    """
    Cancel an Escrow_Funded order, refunding buyer and returning crop to catalog.
    Role: buyer or farmer (must be party to order).
    """
    if g.role not in ("buyer", "farmer"):
        return jsonify({"success": False, "error": "Access denied."}), 403

    caller_tenant_id = g.buyer_id if g.role == "buyer" else g.farmer_id

    db = _get_db()
    try:
        result = order_service.cancel_order(
            conn=db,
            order_id=order_id,
            caller_role=g.role,
            caller_tenant_id=caller_tenant_id,
        )
        return jsonify({
            "success": True,
            "message": "Order cancelled successfully. Funds refunded and crop restored to catalog.",
            "data": result,
        }), 200
    except OrderError as err:
        return jsonify({"success": False, "error": err.message}), err.status_code


# ===========================================================================
# ROUTE 4 — POST /api/orders/<id>/dispute
# AG-API-INC2-003 §6.4 (Endpoint 8 / Diagram 6)
# ===========================================================================
@orders_bp.route("/<int:order_id>/dispute", methods=["POST"])
@token_required
def dispute_order(order_id: int):
    """
    Flag dispute on an Escrow_Funded order, freezing escrow funds.
    Role: buyer or farmer (must be party to order).
    """
    if g.role not in ("buyer", "farmer"):
        return jsonify({"success": False, "error": "Access denied."}), 403

    caller_tenant_id = g.buyer_id if g.role == "buyer" else g.farmer_id

    db = _get_db()
    try:
        result = order_service.dispute_order(
            conn=db,
            order_id=order_id,
            caller_role=g.role,
            caller_tenant_id=caller_tenant_id,
        )
        return jsonify({
            "success": True,
            "message": "Dispute registered. Escrow funds have been frozen.",
            "data": result,
        }), 200
    except OrderError as err:
        return jsonify({"success": False, "error": err.message}), err.status_code


# ===========================================================================
# ROUTE 5 — GET /api/orders/buyer  (Buyer Procurement History)
# AG-API-INC2-003 §6.5 (Endpoint 9 / Diagram 11)
# ===========================================================================
@orders_bp.route("/buyer", methods=["GET"])
@token_required
def get_buyer_orders():
    """
    Retrieve paginated order history for calling buyer.
    Role: buyer only.
    """
    if g.role != "buyer":
        return jsonify({"success": False, "error": "Access denied."}), 403

    # Query params validation
    if any(k not in ALLOWED_QUERY_PARAMS for k in request.args.keys()):
        return jsonify({"success": False, "error": "Invalid filter parameters."}), 400

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

    # 3. Parse & validate status
    status_filter = request.args.get("status")
    if status_filter is not None and status_filter.strip() != "":
        status_filter = status_filter.strip()
        if status_filter not in VALID_ORDER_STATUSES:
            return jsonify({"success": False, "error": "Invalid filter parameters."}), 400
    else:
        status_filter = None

    db = _get_db()
    data, total = order_service.get_buyer_orders(
        conn=db,
        buyer_id=g.buyer_id,
        status_filter=status_filter,
        page=page,
        limit=limit,
    )

    return jsonify({
        "success": True,
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
    }), 200


# ===========================================================================
# ROUTE 6 — GET /api/orders/farmer  (Farmer Sales Orders)
# AG-API-INC2-003 §6.6 (Endpoint 10 / Diagram 11)
# ===========================================================================
@orders_bp.route("/farmer", methods=["GET"])
@token_required
def get_farmer_orders():
    """
    Retrieve paginated inbound sales orders for calling farmer.
    Role: farmer only.
    """
    if g.role != "farmer":
        return jsonify({"success": False, "error": "Access denied."}), 403

    # Query params validation
    if any(k not in ALLOWED_QUERY_PARAMS for k in request.args.keys()):
        return jsonify({"success": False, "error": "Invalid filter parameters."}), 400

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

    # 3. Parse & validate status
    status_filter = request.args.get("status")
    if status_filter is not None and status_filter.strip() != "":
        status_filter = status_filter.strip()
        if status_filter not in VALID_ORDER_STATUSES:
            return jsonify({"success": False, "error": "Invalid filter parameters."}), 400
    else:
        status_filter = None

    db = _get_db()
    data, total = order_service.get_farmer_orders(
        conn=db,
        farmer_id=g.farmer_id,
        status_filter=status_filter,
        page=page,
        limit=limit,
    )

    return jsonify({
        "success": True,
        "data": data,
        "page": page,
        "limit": limit,
        "total": total,
    }), 200
