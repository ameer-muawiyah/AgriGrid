"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    telemetry.py
Module:  Environmental Telemetry Controller
Version: 2.0  (Increment 2 — Intelligence Layer)
Author:  Hasnain Hamza (Core Backend Engineer)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §6.3, API Contracts Delta v1.2 §7.1, Sequence Diagram 8

Purpose
-------
REST API controller for meteorological and edaphic telemetry queries (Endpoint 11).
Backed by 6-hour SQLite cache and deterministic fallback fixtures.
"""

import math
from flask import Blueprint, g, jsonify, request
from auth import token_required
from services.telemetry_service import fetch_weather, fetch_soil

telemetry_bp = Blueprint("telemetry", __name__, url_prefix="/api/telemetry")


def _parse_coordinates() -> tuple[float, float] | None:
    """Parse and validate lat and lon query parameters."""
    lat_str = request.args.get("lat")
    lon_str = request.args.get("lon")
    if lat_str is None or lon_str is None:
        return None
    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except (ValueError, TypeError):
        return None
    if math.isnan(lat) or math.isnan(lon) or lat < -90.0 or lat > 90.0 or lon < -180.0 or lon > 180.0:
        return None
    return lat, lon


@telemetry_bp.route("/weather", methods=["GET"])
@token_required
def get_weather():
    """
    Fetch normalized meteorological telemetry.
    Roles: farmer or buyer.
    """
    if g.role not in ("farmer", "buyer"):
        return jsonify({"success": False, "error": "Access denied."}), 403

    coords = _parse_coordinates()
    if coords is None:
        return jsonify({
            "success": False,
            "error": "Valid latitude (-90 to 90) and longitude (-180 to 180) are required.",
        }), 400

    lat, lon = coords
    data, source = fetch_weather(lat, lon)
    return jsonify({"success": True, "source": source, "data": data}), 200


@telemetry_bp.route("/soil", methods=["GET"])
@token_required
def get_soil():
    """
    Fetch normalized edaphic (soil) telemetry.
    Roles: farmer or buyer.
    """
    if g.role not in ("farmer", "buyer"):
        return jsonify({"success": False, "error": "Access denied."}), 403

    coords = _parse_coordinates()
    if coords is None:
        return jsonify({
            "success": False,
            "error": "Valid latitude (-90 to 90) and longitude (-180 to 180) are required.",
        }), 400

    lat, lon = coords
    data, source = fetch_soil(lat, lon)
    return jsonify({"success": True, "source": source, "data": data}), 200
