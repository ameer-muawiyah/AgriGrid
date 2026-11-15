"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    buyer_service.py
Module:  Buyer Management Service Layer
Version: 2.0  (Increment 2 — Core Data Engine & Demand Side)
Author:  Hasnain Hamza (Core Backend Engineer) & Bareera Noor (Database Administrator)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §5 & Phase 2 Build Package (Part A) & AG-API-INC2-003 §4

Purpose
-------
Pure business logic and persistence service for B2B buyer onboarding, virtual
ledger wallet initialization (500,000.00 PKR), and profile retrieval.
Guarantees zero-orphan ACID atomic creation within explicit BEGIN IMMEDIATE transactions.
Stdlib only — no Flask dependencies.
"""

import sqlite3
from typing import Any

SIMULATED_BUYER_STARTING_BALANCE_PKR = 500000.00


def create_buyer(
    conn: sqlite3.Connection,
    username: str,
    password_hash: str,
    email: str | None,
    company_name: str,
    contact_phone: str,
    warehouse_address: str,
    warehouse_gps_latitude: float | None = None,
    warehouse_gps_longitude: float | None = None,
) -> dict[str, Any]:
    """
    Atomically create a user record (role='buyer'), linked buyer profile,
    and initialize the buyer's virtual ledger wallet with 500,000.00 PKR.

    Executes under an explicit BEGIN IMMEDIATE transaction to prevent races.
    Rolls back fully on any exception.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    try:
        conn.execute("BEGIN IMMEDIATE;")

        # 1. Insert users record
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, role, email)
            VALUES (?, ?, 'buyer', ?)
            """,
            (username, password_hash, email),
        )
        user_id = cursor.lastrowid

        # 2. Insert buyers profile
        cursor.execute(
            """
            INSERT INTO buyers (
                user_id,
                company_name,
                contact_phone,
                warehouse_address,
                warehouse_gps_latitude,
                warehouse_gps_longitude
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                company_name,
                contact_phone,
                warehouse_address,
                warehouse_gps_latitude,
                warehouse_gps_longitude,
            ),
        )
        buyer_id = cursor.lastrowid

        # 3. Insert buyer_wallets ledger entry
        cursor.execute(
            """
            INSERT INTO buyer_wallets (buyer_id, balance_pkr)
            VALUES (?, ?)
            """,
            (buyer_id, SIMULATED_BUYER_STARTING_BALANCE_PKR),
        )

        conn.execute("COMMIT;")

        return {
            "user_id": user_id,
            "username": username,
            "role": "buyer",
            "buyer_id": buyer_id,
            "company_name": company_name,
            "wallet_balance_pkr": SIMULATED_BUYER_STARTING_BALANCE_PKR,
        }

    except Exception:
        try:
            conn.execute("ROLLBACK;")
        except Exception:
            pass
        raise


def get_buyer_by_user_id(conn: sqlite3.Connection, user_id: int) -> dict[str, Any] | None:
    """
    Retrieve buyer profile and current wallet balance for a given user_id.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT  b.id AS buyer_id,
                b.company_name,
                b.contact_phone,
                b.warehouse_address,
                b.warehouse_gps_latitude,
                b.warehouse_gps_longitude,
                COALESCE(bw.balance_pkr, 0.0) AS wallet_balance_pkr
        FROM buyers b
        LEFT JOIN buyer_wallets bw ON bw.buyer_id = b.id
        WHERE b.user_id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    if isinstance(row, sqlite3.Row):
        return dict(row)

    return {
        "buyer_id": row[0],
        "company_name": row[1],
        "contact_phone": row[2],
        "warehouse_address": row[3],
        "warehouse_gps_latitude": row[4],
        "warehouse_gps_longitude": row[5],
        "wallet_balance_pkr": float(row[6]),
    }
