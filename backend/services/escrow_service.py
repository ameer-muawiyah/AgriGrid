"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    escrow_service.py
Module:  Escrow Release & Refund Settlement Service
Version: 2.0  (Increment 2 — Escrow Orders & Settlement)
Author:  Hasnain Hamza (Core Backend Engineer) & Bareera Noor (Database Administrator)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §5, Pinned Decisions (PD-4, PD-5), SRS (FR-SET-004, FR-SET-006)

Purpose
-------
Stdlib-only domain service for atomic digital escrow release and refund operations.
Both functions execute strictly within the caller's active database transaction
(no BEGIN/COMMIT/ROLLBACK within this service).
"""

from datetime import datetime, timezone
import sqlite3
from typing import Any


def _utcnow_iso() -> str:
    """Return current UTC timestamp in DB ISO-8601 format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def release_escrow(conn: sqlite3.Connection, order_id: int, trigger: str) -> dict[str, Any]:
    """
    Release escrow funds to the selling farmer (FR-SET-004).
    Credits the farmer's wallet via UPSERT (PD-5) and updates escrow_holdings to RELEASED.
    Must be called inside an active transaction.
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT o.farmer_id, e.held_amount_pkr, e.escrow_status
          FROM orders o
          JOIN escrow_holdings e ON o.id = e.order_id
         WHERE o.id = ?
    """, (order_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Order or escrow holding not found for order_id: {order_id}")

    farmer_id = row[0]
    held_amount_pkr = float(row[1])
    now_ts = _utcnow_iso()
    release_tx_ref = f"TRIGGER:{trigger};REF:TX-{order_id}-SETTLE"

    # Credit farmer's wallet using upsert (handles missing wallet row per PD-5)
    cursor.execute("""
        INSERT INTO farmer_wallets (farmer_id, balance_pkr, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(farmer_id) DO UPDATE SET
            balance_pkr = balance_pkr + excluded.balance_pkr,
            updated_at = excluded.updated_at
    """, (farmer_id, held_amount_pkr, now_ts))

    # Update holding status to RELEASED with released_at and release_tx_ref
    cursor.execute("""
        UPDATE escrow_holdings
           SET escrow_status = 'RELEASED',
               released_at = ?,
               release_tx_ref = ?
         WHERE order_id = ?
    """, (now_ts, release_tx_ref, order_id))

    # Query new balance
    cursor.execute("SELECT balance_pkr FROM farmer_wallets WHERE farmer_id = ?", (farmer_id,))
    bal_row = cursor.fetchone()
    farmer_new_balance_pkr = round(float(bal_row[0]), 2) if bal_row else round(held_amount_pkr, 2)

    return {
        "released_amount_pkr": round(held_amount_pkr, 2),
        "release_tx_ref": release_tx_ref,
        "farmer_new_balance_pkr": farmer_new_balance_pkr,
    }


def refund_escrow(conn: sqlite3.Connection, order_id: int, trigger: str) -> dict[str, Any]:
    """
    Refund held escrow funds back to the purchasing buyer (FR-SET-006).
    Credits the buyer's wallet, updates escrow_holdings to REFUNDED, and leaves
    released_at as NULL (PD-4).
    Must be called inside an active transaction.
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT o.buyer_id, e.held_amount_pkr, e.escrow_status
          FROM orders o
          JOIN escrow_holdings e ON o.id = e.order_id
         WHERE o.id = ?
    """, (order_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError(f"Order or escrow holding not found for order_id: {order_id}")

    buyer_id = row[0]
    held_amount_pkr = float(row[1])
    now_ts = _utcnow_iso()
    release_tx_ref = f"TRIGGER:{trigger};REF:TX-{order_id}-REFUND"

    # Credit buyer's wallet (buyer wallet rows always exist)
    cursor.execute("""
        UPDATE buyer_wallets
           SET balance_pkr = balance_pkr + ?,
               updated_at = ?
         WHERE buyer_id = ?
    """, (held_amount_pkr, now_ts, buyer_id))

    # Set escrow_status to REFUNDED, leave released_at as NULL (PD-4)
    cursor.execute("""
        UPDATE escrow_holdings
           SET escrow_status = 'REFUNDED',
               release_tx_ref = ?
         WHERE order_id = ?
    """, (release_tx_ref, order_id))

    # Query new buyer balance
    cursor.execute("SELECT balance_pkr FROM buyer_wallets WHERE buyer_id = ?", (buyer_id,))
    bal_row = cursor.fetchone()
    buyer_new_balance_pkr = round(float(bal_row[0]), 2) if bal_row else 0.0

    return {
        "refunded_amount_pkr": round(held_amount_pkr, 2),
        "release_tx_ref": release_tx_ref,
        "buyer_new_balance_pkr": buyer_new_balance_pkr,
    }


def get_farmer_wallet_balance(farmer_id: int, conn: sqlite3.Connection | None = None) -> float:
    """Return the farmer's current wallet balance in PKR.
    A farmer with no farmer_wallets row (no completed sale yet) has 0.0 —
    the row is created by settlement, never by this read."""
    should_close = False
    db = conn
    if db is None:
        try:
            from flask import current_app, g, has_app_context
            if has_app_context():
                if "db" in g:
                    db = g.db
                else:
                    import os
                    from pathlib import Path
                    _base = Path(__file__).resolve().parent.parent
                    db_path = current_app.config.get(
                        "DB_PATH",
                        os.environ.get("AGRIGRID_DB_PATH", str(_base / "database" / "agrigrid.db")),
                    )
                    db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
                    db.row_factory = sqlite3.Row
                    db.execute("PRAGMA foreign_keys = ON;")
                    should_close = True
        except ImportError:
            pass
        if db is None:
            import os
            from pathlib import Path
            _base = Path(__file__).resolve().parent.parent
            db_path = os.environ.get(
                "AGRIGRID_DB_PATH", str(_base / "database" / "agrigrid.db")
            )
            db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys = ON;")
            should_close = True
    try:
        cursor = db.cursor()
        cursor.execute(
            "SELECT balance_pkr FROM farmer_wallets WHERE farmer_id = ?", (farmer_id,)
        )
        row = cursor.fetchone()
        if not row:
            return 0.0
        val = row[0] if not isinstance(row, sqlite3.Row) else row["balance_pkr"]
        return float(val) if val is not None else 0.0
    finally:
        if should_close:
            db.close()
