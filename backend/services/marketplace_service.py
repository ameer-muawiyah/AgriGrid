"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    marketplace_service.py
Module:  B2B Wholesale Produce Marketplace Service Layer
Version: 2.0  (Increment 2 — Core Data Engine & Demand Side)
Author:  Hasnain Hamza (Core Backend Engineer) & Bareera Noor (Database Administrator)
Date:    2026-11-15
Source:  AG-PLAN-INC2-001 §5, Phase 2 Build Package (Part B) & AG-API-INC2-003 §5

Purpose
-------
Pure business logic and persistence service for B2B marketplace catalog browsing
and single produce listing inspection.
Enforces strict visibility gating:
  - status = 'Active'
  - is_deleted = 0
  - asking_price_per_kg IS NOT NULL
  - asking_price_per_kg > 0
Stdlib only — zero Flask dependencies.
"""

import sqlite3
from typing import Any

SORT_ORDER_MAP = {
    "price_asc":  "ORDER BY l.asking_price_per_kg ASC, l.id ASC",
    "price_desc": "ORDER BY l.asking_price_per_kg DESC, l.id ASC",
    "date_desc":  "ORDER BY l.created_at DESC, l.id DESC",
}


def list_marketplace_listings(
    conn: sqlite3.Connection,
    page: int = 1,
    limit: int = 20,
    crop_name: str | None = None,
    max_price: float | None = None,
    sort: str = "date_desc",
) -> tuple[list[dict[str, Any]], int]:
    """
    Query available commercial crop listings for wholesale marketplace browse.
    Returns (data_list, total_count).

    Visibility Gate:
      status == 'Active' AND is_deleted == 0 AND asking_price_per_kg > 0
    Enforced on BOTH total count and item fetch queries.
    """
    cursor = conn.cursor()

    base_where = [
        "l.status = 'Active'",
        "l.is_deleted = 0",
        "l.asking_price_per_kg IS NOT NULL",
        "l.asking_price_per_kg > 0",
    ]
    params: list[Any] = []

    if crop_name:
        base_where.append("l.crop_name = ?")
        params.append(crop_name)

    if max_price is not None:
        base_where.append("l.asking_price_per_kg <= ?")
        params.append(max_price)

    where_clause = " AND ".join(base_where)

    # 1. Total count query
    count_sql = f"""
        SELECT COUNT(*)
          FROM listings l
          JOIN farmers f ON l.farmer_id = f.id
         WHERE {where_clause}
    """
    cursor.execute(count_sql, params)
    total_count = cursor.fetchone()[0]

    # 2. Paginated items query
    order_clause = SORT_ORDER_MAP.get(sort, SORT_ORDER_MAP["date_desc"])
    offset = (page - 1) * limit

    data_sql = f"""
        SELECT  l.id AS listing_id,
                l.batch_id,
                l.crop_name,
                l.quantity_kg,
                l.asking_price_per_kg,
                l.estimated_harvest_date,
                f.farm_name,
                f.farm_location,
                l.gps_latitude,
                l.gps_longitude
          FROM listings l
          JOIN farmers f ON l.farmer_id = f.id
         WHERE {where_clause}
         {order_clause}
         LIMIT ? OFFSET ?
    """
    query_params = list(params) + [limit, offset]
    cursor.execute(data_sql, query_params)
    rows = cursor.fetchall()

    items: list[dict[str, Any]] = []
    for r in rows:
        qty = float(r["quantity_kg"])
        price = float(r["asking_price_per_kg"])
        total_pkr = round(qty * price, 2)
        items.append({
            "listing_id":             r["listing_id"],
            "batch_id":               r["batch_id"],
            "crop_name":              r["crop_name"],
            "quantity_kg":            qty,
            "asking_price_per_kg":    price,
            "total_price_pkr":        total_pkr,
            "estimated_harvest_date": r["estimated_harvest_date"],
            "farm_name":              r["farm_name"],
            "farm_location":          r["farm_location"],
            "gps_latitude":           float(r["gps_latitude"]),
            "gps_longitude":          float(r["gps_longitude"]),
        })

    return items, total_count


def get_marketplace_listing(
    conn: sqlite3.Connection,
    listing_id: int,
) -> dict[str, Any] | None:
    """
    Retrieve single commercial produce listing with detailed farm origin
    and computed total price.
    Returns None if listing does not exist, is withdrawn, or is unpriced.
    """
    cursor = conn.cursor()
    sql = """
        SELECT  l.id AS listing_id,
                l.batch_id,
                l.farmer_id,
                l.crop_name,
                l.acreage,
                l.quantity_kg,
                l.asking_price_per_kg,
                l.planting_date,
                l.estimated_harvest_date,
                l.status,
                l.created_at,
                f.farm_name,
                f.farm_location,
                l.gps_latitude,
                l.gps_longitude
          FROM listings l
          JOIN farmers f ON l.farmer_id = f.id
         WHERE l.id = ?
           AND l.status = 'Active'
           AND l.is_deleted = 0
           AND l.asking_price_per_kg IS NOT NULL
           AND l.asking_price_per_kg > 0
    """
    cursor.execute(sql, (listing_id,))
    row = cursor.fetchone()
    if not row:
        return None

    qty = float(row["quantity_kg"])
    price = float(row["asking_price_per_kg"])
    total_pkr = round(qty * price, 2)

    return {
        "listing_id":             row["listing_id"],
        "batch_id":               row["batch_id"],
        "farmer_id":              row["farmer_id"],
        "crop_name":              row["crop_name"],
        "acreage":                float(row["acreage"]),
        "quantity_kg":            qty,
        "asking_price_per_kg":    price,
        "total_price_pkr":        total_pkr,
        "planting_date":          row["planting_date"],
        "estimated_harvest_date": row["estimated_harvest_date"],
        "status":                 row["status"],
        "farm_name":              row["farm_name"],
        "farm_location":          row["farm_location"],
        "gps_latitude":           float(row["gps_latitude"]),
        "gps_longitude":          float(row["gps_longitude"]),
        "created_at":             row["created_at"],
    }
