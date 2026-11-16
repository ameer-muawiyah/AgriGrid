"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    wallet.py
Module:  Farmer Wallet Controller
Version: 2.0  (Increment 2 — Settlement & Ledgers)
Author:  Hasnain Hamza (Core Backend Engineer)
Date:    2026-11-16
Source:  AG-PLAN-INC2-001, agrigrid-farmer-wallet-patch-package.md (PD-W1)

Purpose
-------
REST API controller for farmer wallet operations.
Surfaces the farmer's current wallet balance (read-only).
"""

from flask import Blueprint, g, jsonify
from auth import token_required
from services.escrow_service import get_farmer_wallet_balance

wallet_bp = Blueprint("wallet", __name__, url_prefix="/api/farmer")


@wallet_bp.route("/wallet", methods=["GET"])
@token_required
def get_farmer_wallet():
    """
    Retrieve current wallet balance for the authenticated farmer.
    Role: farmer only.

    Responses:
      401 — no or invalid token (decorator handles this)
      403 — authenticated but role != farmer
      200 — {"success": true, "data": {"balance_pkr": <float>}}
    """
    if g.role != "farmer":
        return jsonify({"success": False, "error": "Access denied."}), 403

    balance = get_farmer_wallet_balance(g.farmer_id)
    return jsonify({
        "success": True,
        "data": {
            "balance_pkr": float(balance)
        }
    }), 200
