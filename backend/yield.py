"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    yield.py
Module:  Predictive Yield Engine Controller
Version: 2.0  (Increment 2 — Intelligence Layer)
Author:  Hasnain Hamza (Core Backend Engineer)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §6.3, API Contracts Delta v1.2 §7.2, Sequence Diagram 9

Purpose
-------
REST API controller for predictive yield forecasts (Endpoint 12).
Computes deterministic agronomic projections and persists outputs to yield_forecasts.
"""

from flask import Blueprint, g, jsonify, request
from auth import token_required
from services.yield_service import generate_yield_forecast, YieldError

yield_bp = Blueprint("yield", __name__, url_prefix="/api/yield")


@yield_bp.route("/predict", methods=["POST"])
@token_required
def predict_yield():
    """
    Calculate and persist predictive yield forecast for a crop listing.
    Role: farmer only (must own the listing).
    """
    if g.role != "farmer":
        return jsonify({"success": False, "error": "Access denied."}), 403

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"success": False, "error": "Listing ID is required."}), 400

    listing_id = payload.get("listing_id")
    if listing_id is None or isinstance(listing_id, bool) or not isinstance(listing_id, int):
        return jsonify({"success": False, "error": "Listing ID is required."}), 400

    try:
        result = generate_yield_forecast(
            listing_id=listing_id,
            caller_farmer_id=g.farmer_id,
        )
        return jsonify({
            "success": True,
            "message": "Yield forecast generated successfully.",
            "data": result,
        }), 200
    except YieldError as err:
        return jsonify({"success": False, "error": err.message}), err.status_code
