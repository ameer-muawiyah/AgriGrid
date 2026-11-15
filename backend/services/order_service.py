"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    order_service.py
Module:  Order Processing & Lifecycle Service Layer
Version: 2.0  (Increment 2 — Escrow Orders & Settlement)
Author:  Hasnain Hamza (Core Backend Engineer) & Bareera Noor (Database Administrator)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §5, Pinned Decisions (PD-1, PD-6, PD-7, PD-10),
         SRS (FR-ORD-*, FR-SET-*, FR-STM-*), API Contracts Delta v1.2 §6

Purpose
-------
Pure domain logic and SQL operations for digital escrow checkout, order lifecycle
transitions, and multi-tenant order history retrieval.
Stdlib only — zero Flask dependencies.
Opens BEGIN IMMEDIATE before all precondition SELECTs to prevent race conditions (PD-6).
Refreshes orders.updated_at on all transitions (PD-10).
"""

from datetime import datetime, timezone, timedelta
import sqlite3
from typing import Any

from services.escrow_service import release_escrow, refund_escrow

VALID_ORDER_STATUSES = {
    "Escrow_Funded",
    "In_Transit",
    "Delivered",
    "Completed",
    "Cancelled",
    "Disputed",
}


# ---------------------------------------------------------------------------
# Domain Exceptions (mapped to HTTP response envelopes in orders.py)
# ---------------------------------------------------------------------------

class OrderError(Exception):
    """Base exception for order-related domain errors."""
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ListingNotFound(OrderError):
    def __init__(self):
        super().__init__("Listing not found.", 404)


class ListingAlreadySold(OrderError):
    def __init__(self):
        super().__init__("Listing has already been sold.", 409)


class InvalidTemperature(OrderError):
    def __init__(self):
        super().__init__("Max temperature must be between -25.0°C and 30.0°C.", 400)


class PartialQuantityNotSupported(OrderError):
    def __init__(self):
        super().__init__("Partial quantity purchasing is not supported in Increment 2.", 400)


class InsufficientBalance(OrderError):
    def __init__(self):
        super().__init__("Insufficient wallet balance.", 400)


class OrderNotFound(OrderError):
    def __init__(self):
        super().__init__("Order not found.", 404)


class InvalidOrderStatus(OrderError):
    def __init__(self, message: str):
        super().__init__(message, 400)


def _utcnow_iso() -> str:
    """Return current UTC timestamp formatted as ISO-8601 string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Core Operations
# ---------------------------------------------------------------------------

def create_order(
    conn: sqlite3.Connection,
    buyer_id: int,
    listing_id: int,
    ordered_quantity_kg: float,
    destination_warehouse: str,
    max_temperature_celsius: float,
) -> dict[str, Any]:
    """
    Execute atomic digital escrow checkout (Endpoint 5 / Diagram 3).
    Precondition checks and mutations are executed inside BEGIN IMMEDIATE (PD-6, PD-7).
    """
    conn.isolation_level = None
    cursor = conn.cursor()

    conn.execute("BEGIN IMMEDIATE;")
    try:
        # Step 1: Listing SELECT by id
        cursor.execute("""
            SELECT id, farmer_id, quantity_kg, asking_price_per_kg, status, is_deleted
              FROM listings
             WHERE id = ?
        """, (listing_id,))
        listing = cursor.fetchone()

        if not listing or listing["is_deleted"] == 1 or listing["asking_price_per_kg"] is None:
            raise ListingNotFound()

        # Step 2: Concurrency / Already sold check
        if listing["status"] in ("Sold", "Withdrawn"):
            raise ListingAlreadySold()

        # Step 3: Temperature constraint validation (-25.0 to +30.0 °C)
        if max_temperature_celsius < -25.0 or max_temperature_celsius > 30.0:
            raise InvalidTemperature()

        # Step 4: Strict whole-listing quantity check
        if abs(float(ordered_quantity_kg) - float(listing["quantity_kg"])) > 1e-6:
            raise PartialQuantityNotSupported()

        # Step 5: Buyer wallet balance check
        total_amount = round(float(listing["quantity_kg"]) * float(listing["asking_price_per_kg"]), 2)
        cursor.execute("SELECT balance_pkr FROM buyer_wallets WHERE buyer_id = ?", (buyer_id,))
        wallet = cursor.fetchone()
        if not wallet or float(wallet["balance_pkr"]) < total_amount:
            raise InsufficientBalance()

        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Step 6: Mutations
        # 6a. Debit buyer wallet
        cursor.execute("""
            UPDATE buyer_wallets
               SET balance_pkr = round(balance_pkr - ?, 2),
                   updated_at = ?
             WHERE buyer_id = ?
        """, (total_amount, now_str, buyer_id))

        # 6b. Insert order record (status = 'Escrow_Funded')
        cursor.execute("""
            INSERT INTO orders (
                order_number, listing_id, buyer_id, farmer_id,
                ordered_quantity_kg, agreed_price_per_kg, total_amount_pkr,
                destination_warehouse, max_temperature_celsius, order_status,
                created_at, updated_at
            ) VALUES (
                'ORD-TEMP', ?, ?, ?,
                ?, ?, ?,
                ?, ?, 'Escrow_Funded',
                ?, ?
            )
        """, (
            listing_id, buyer_id, listing["farmer_id"],
            float(listing["quantity_kg"]), float(listing["asking_price_per_kg"]), total_amount,
            destination_warehouse, float(max_temperature_celsius),
            now_str, now_str
        ))
        order_id = cursor.lastrowid

        # 6c. Generate deterministic order_number
        year = now_dt.year
        order_number = f"ORD-{year}-{order_id:04d}"
        cursor.execute("UPDATE orders SET order_number = ? WHERE id = ?", (order_number, order_id))

        # 6d. Insert escrow holding (HELD)
        cursor.execute("""
            INSERT INTO escrow_holdings (
                order_id, held_amount_pkr, escrow_status, held_at
            ) VALUES (
                ?, ?, 'HELD', ?
            )
        """, (order_id, total_amount, now_str))

        # 6e. Transition listing status to 'Sold'
        cursor.execute("""
            UPDATE listings
               SET status = 'Sold',
                   updated_at = ?
             WHERE id = ?
        """, (now_str, listing_id))

        # Read remaining buyer wallet balance
        cursor.execute("SELECT balance_pkr FROM buyer_wallets WHERE buyer_id = ?", (buyer_id,))
        rem_wallet = cursor.fetchone()
        remaining_balance = round(float(rem_wallet["balance_pkr"]), 2) if rem_wallet else 0.0

        conn.execute("COMMIT;")

        return {
            "order_id": order_id,
            "order_number": order_number,
            "listing_id": listing_id,
            "ordered_quantity_kg": float(listing["quantity_kg"]),
            "total_amount_pkr": total_amount,
            "order_status": "Escrow_Funded",
            "escrow_status": "HELD",
            "destination_warehouse": destination_warehouse,
            "max_temperature_celsius": float(max_temperature_celsius),
            "remaining_wallet_balance_pkr": remaining_balance,
            "created_at": now_str,
        }
    except Exception:
        conn.execute("ROLLBACK;")
        raise


def confirm_delivery(conn: sqlite3.Connection, order_id: int, caller_buyer_id: int) -> dict[str, Any]:
    """
    Confirm produce delivery and release escrow funds to farmer (Endpoint 6 / Diagram 4).
    """
    conn.isolation_level = None
    cursor = conn.cursor()

    conn.execute("BEGIN IMMEDIATE;")
    try:
        cursor.execute("""
            SELECT o.id, o.order_number, o.buyer_id, o.farmer_id, o.order_status,
                   e.held_amount_pkr, e.escrow_status
              FROM orders o
              JOIN escrow_holdings e ON o.id = e.order_id
             WHERE o.id = ?
        """, (order_id,))
        order = cursor.fetchone()

        if not order or order["buyer_id"] != caller_buyer_id:
            raise OrderNotFound()

        if order["order_status"] != "Escrow_Funded":
            raise InvalidOrderStatus("Order cannot be confirmed in current status.")

        now_dt = datetime.now(timezone.utc)
        delivered_at = now_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        auto_release_at = (now_dt + timedelta(hours=72)).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Update order status to Completed, refresh updated_at (PD-10)
        cursor.execute("""
            UPDATE orders
               SET order_status = 'Completed',
                   delivered_at = ?,
                   updated_at = ?
             WHERE id = ?
        """, (delivered_at, delivered_at, order_id))

        # Update escrow_holdings delivery timestamps
        cursor.execute("""
            UPDATE escrow_holdings
               SET delivered_at = ?,
                   auto_release_at = ?
             WHERE order_id = ?
        """, (delivered_at, auto_release_at, order_id))

        # Release escrow funds to farmer (FR-SET-004)
        release_res = release_escrow(conn, order_id, "buyer_confirmation")

        conn.execute("COMMIT;")

        return {
            "order_id": order_id,
            "order_number": order["order_number"],
            "order_status": "Completed",
            "escrow_status": "RELEASED",
            "delivered_at": delivered_at,
            "release_tx_ref": release_res["release_tx_ref"],
        }
    except Exception:
        conn.execute("ROLLBACK;")
        raise


def cancel_order(
    conn: sqlite3.Connection,
    order_id: int,
    caller_role: str,
    caller_tenant_id: int,
) -> dict[str, Any]:
    """
    Cancel an Escrow_Funded order, refunding buyer and returning crop to catalog (Endpoint 7 / Diagram 5).
    """
    conn.isolation_level = None
    cursor = conn.cursor()

    conn.execute("BEGIN IMMEDIATE;")
    try:
        cursor.execute("""
            SELECT o.id, o.order_number, o.listing_id, o.buyer_id, o.farmer_id, o.order_status,
                   e.held_amount_pkr, e.escrow_status
              FROM orders o
              JOIN escrow_holdings e ON o.id = e.order_id
             WHERE o.id = ?
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            raise OrderNotFound()

        # Multi-tenant boundary check: caller must be party to order
        if caller_role == "buyer":
            if order["buyer_id"] != caller_tenant_id:
                raise OrderNotFound()
        elif caller_role == "farmer":
            if order["farmer_id"] != caller_tenant_id:
                raise OrderNotFound()
        else:
            raise OrderNotFound()

        if order["order_status"] != "Escrow_Funded":
            raise InvalidOrderStatus("Only Escrow_Funded orders can be cancelled.")

        trigger = "buyer_cancellation" if caller_role == "buyer" else "farmer_cancellation"
        refund_res = refund_escrow(conn, order_id, trigger)

        now_str = _utcnow_iso()

        # Transition order to Cancelled, refresh updated_at (PD-10)
        cursor.execute("""
            UPDATE orders
               SET order_status = 'Cancelled',
                   updated_at = ?
             WHERE id = ?
        """, (now_str, order_id))

        # Restore listing to Active in catalog
        cursor.execute("""
            UPDATE listings
               SET status = 'Active',
                   updated_at = ?
             WHERE id = ?
        """, (now_str, order["listing_id"]))

        conn.execute("COMMIT;")

        return {
            "order_id": order_id,
            "order_number": order["order_number"],
            "order_status": "Cancelled",
            "escrow_status": "REFUNDED",
            "refunded_amount_pkr": refund_res["refunded_amount_pkr"],
            "listing_id": order["listing_id"],
            "listing_status": "Active",
        }
    except Exception:
        conn.execute("ROLLBACK;")
        raise


def dispute_order(
    conn: sqlite3.Connection,
    order_id: int,
    caller_role: str,
    caller_tenant_id: int,
) -> dict[str, Any]:
    """
    Flag formal dispute on an Escrow_Funded order, freezing funds (Endpoint 8 / Diagram 6).
    """
    conn.isolation_level = None
    cursor = conn.cursor()

    conn.execute("BEGIN IMMEDIATE;")
    try:
        cursor.execute("""
            SELECT o.id, o.order_number, o.buyer_id, o.farmer_id, o.order_status,
                   e.escrow_status
              FROM orders o
              JOIN escrow_holdings e ON o.id = e.order_id
             WHERE o.id = ?
        """, (order_id,))
        order = cursor.fetchone()

        if not order:
            raise OrderNotFound()

        # Multi-tenant boundary check: caller must be party to order
        if caller_role == "buyer":
            if order["buyer_id"] != caller_tenant_id:
                raise OrderNotFound()
        elif caller_role == "farmer":
            if order["farmer_id"] != caller_tenant_id:
                raise OrderNotFound()
        else:
            raise OrderNotFound()

        if order["order_status"] != "Escrow_Funded":
            raise InvalidOrderStatus("Only Escrow_Funded orders can be disputed.")

        now_str = _utcnow_iso()

        # Transition order to Disputed, refresh updated_at (PD-10)
        cursor.execute("""
            UPDATE orders
               SET order_status = 'Disputed',
                   updated_at = ?
             WHERE id = ?
        """, (now_str, order_id))

        # Freeze escrow holdings in DISPUTED state (no money moves)
        cursor.execute("""
            UPDATE escrow_holdings
               SET escrow_status = 'DISPUTED'
             WHERE order_id = ?
        """, (order_id,))

        conn.execute("COMMIT;")

        return {
            "order_id": order_id,
            "order_number": order["order_number"],
            "order_status": "Disputed",
            "escrow_status": "DISPUTED",
        }
    except Exception:
        conn.execute("ROLLBACK;")
        raise


def get_buyer_orders(
    conn: sqlite3.Connection,
    buyer_id: int,
    status_filter: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """
    Retrieve paginated order history for calling buyer (Endpoint 9 / Diagram 11).
    """
    cursor = conn.cursor()
    base_where = ["o.buyer_id = ?"]
    params: list[Any] = [buyer_id]

    if status_filter:
        base_where.append("o.order_status = ?")
        params.append(status_filter)

    where_str = " AND ".join(base_where)

    # 1. Companion COUNT query sharing exact WHERE
    count_sql = f"SELECT COUNT(*) FROM orders o WHERE {where_str}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()[0]

    # 2. Paginated items query (newest first)
    offset = (page - 1) * limit
    data_sql = f"""
        SELECT o.id AS order_id,
               o.order_number,
               o.listing_id,
               l.crop_name,
               l.batch_id,
               o.farmer_id,
               f.farm_name,
               o.ordered_quantity_kg,
               o.agreed_price_per_kg,
               o.total_amount_pkr,
               o.destination_warehouse,
               o.max_temperature_celsius,
               o.order_status,
               e.escrow_status,
               o.created_at
          FROM orders o
          JOIN listings l ON o.listing_id = l.id
          JOIN farmers f ON o.farmer_id = f.id
          JOIN escrow_holdings e ON o.id = e.order_id
         WHERE {where_str}
         ORDER BY o.created_at DESC, o.id DESC
         LIMIT ? OFFSET ?
    """
    cursor.execute(data_sql, params + [limit, offset])
    rows = cursor.fetchall()
    data = [dict(r) for r in rows]

    return data, total


def get_farmer_orders(
    conn: sqlite3.Connection,
    farmer_id: int,
    status_filter: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict[str, Any]], int]:
    """
    Retrieve paginated inbound sales orders for calling farmer (Endpoint 10 / Diagram 11).
    """
    cursor = conn.cursor()
    base_where = ["o.farmer_id = ?"]
    params: list[Any] = [farmer_id]

    if status_filter:
        base_where.append("o.order_status = ?")
        params.append(status_filter)

    where_str = " AND ".join(base_where)

    # 1. Companion COUNT query sharing exact WHERE
    count_sql = f"SELECT COUNT(*) FROM orders o WHERE {where_str}"
    cursor.execute(count_sql, params)
    total = cursor.fetchone()[0]

    # 2. Paginated items query (newest first)
    offset = (page - 1) * limit
    data_sql = f"""
        SELECT o.id AS order_id,
               o.order_number,
               o.listing_id,
               l.crop_name,
               l.batch_id,
               o.buyer_id,
               b.company_name AS buyer_company_name,
               o.ordered_quantity_kg,
               o.agreed_price_per_kg,
               o.total_amount_pkr,
               o.destination_warehouse,
               o.max_temperature_celsius,
               o.order_status,
               e.escrow_status,
               o.created_at
          FROM orders o
          JOIN listings l ON o.listing_id = l.id
          JOIN buyers b ON o.buyer_id = b.id
          JOIN escrow_holdings e ON o.id = e.order_id
         WHERE {where_str}
         ORDER BY o.created_at DESC, o.id DESC
         LIMIT ? OFFSET ?
    """
    cursor.execute(data_sql, params + [limit, offset])
    rows = cursor.fetchall()
    data = [dict(r) for r in rows]

    return data, total
