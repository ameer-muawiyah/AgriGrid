-- =============================================================================
-- Agri-Grid: Smart Agriculture & Food Security Ecosystem
-- Migration:  002_increment_2_marketplace_escrow_telemetry.sql
-- Module:     Increment 2 Core Data Engine & Demand Side Schema Extensions
-- Author:     Bareera Noor (Database Administrator)
-- Date:       2026-11-14
-- Source:     AG-PLAN-INC2-001 §5 & Phase 1 Build Package (Parts A1 & A2)
--
-- Target DBMS : SQLite 3 (zero-config local prototype)
-- Normalization: 3rd Normal Form (3NF)
-- Transactions:  ACID-compliant
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. ALTERATIONS TO EXISTING TABLES
--    Extend listings table with commercial pricing and batch tracking.
--    Note: In SQLite, UNIQUE column constraint on ALTER TABLE is applied via
--    a separate UNIQUE INDEX (idx_listings_batch_id) to adhere to engine rules.
-- ---------------------------------------------------------------------------
ALTER TABLE listings ADD COLUMN asking_price_per_kg REAL CHECK(asking_price_per_kg IS NULL OR asking_price_per_kg > 0);
ALTER TABLE listings ADD COLUMN batch_id TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS idx_listings_batch_id ON listings(batch_id);

-- Performance index for marketplace search
CREATE INDEX IF NOT EXISTS idx_listings_marketplace 
    ON listings(status, is_deleted, crop_name, asking_price_per_kg);

-- ---------------------------------------------------------------------------
-- 1. TABLE: buyers
--    Extended profile for users whose role = 'buyer'.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS buyers (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                 INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE RESTRICT,
    company_name            TEXT NOT NULL CHECK(LENGTH(company_name) >= 2 AND LENGTH(company_name) <= 100),
    contact_phone           TEXT NOT NULL CHECK(LENGTH(contact_phone) >= 7 AND LENGTH(contact_phone) <= 20),
    warehouse_address       TEXT NOT NULL CHECK(LENGTH(warehouse_address) >= 5),
    warehouse_gps_latitude  REAL CHECK(warehouse_gps_latitude IS NULL OR (warehouse_gps_latitude >= -90.0 AND warehouse_gps_latitude <= 90.0)),
    warehouse_gps_longitude REAL CHECK(warehouse_gps_longitude IS NULL OR (warehouse_gps_longitude >= -180.0 AND warehouse_gps_longitude <= 180.0)),
    created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ---------------------------------------------------------------------------
-- 2. TABLE: buyer_wallets & farmer_wallets
--    Virtual ledgers for simulated multi-party transactions.
--    Constant: SIMULATED_BUYER_STARTING_BALANCE_PKR = 500000.00
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS buyer_wallets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id    INTEGER NOT NULL UNIQUE REFERENCES buyers(id) ON DELETE RESTRICT,
    balance_pkr REAL NOT NULL DEFAULT 500000.00 CHECK(balance_pkr >= 0),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE TABLE IF NOT EXISTS farmer_wallets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id   INTEGER NOT NULL UNIQUE REFERENCES farmers(id) ON DELETE RESTRICT,
    balance_pkr REAL NOT NULL DEFAULT 0.00 CHECK(balance_pkr >= 0),
    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ---------------------------------------------------------------------------
-- 3. TABLE: orders
--    Commercial purchase agreements linking Buyers to Farmer Listings.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number                TEXT NOT NULL UNIQUE,
    listing_id                  INTEGER NOT NULL REFERENCES listings(id) ON DELETE RESTRICT,
    buyer_id                    INTEGER NOT NULL REFERENCES buyers(id) ON DELETE RESTRICT,
    farmer_id                   INTEGER NOT NULL REFERENCES farmers(id) ON DELETE RESTRICT,
    ordered_quantity_kg         REAL NOT NULL CHECK(ordered_quantity_kg > 0),
    agreed_price_per_kg         REAL NOT NULL CHECK(agreed_price_per_kg > 0),
    total_amount_pkr            REAL NOT NULL CHECK(total_amount_pkr > 0),
    destination_warehouse       TEXT NOT NULL,
    max_temperature_celsius     REAL NOT NULL DEFAULT 8.0,
    order_status                TEXT NOT NULL DEFAULT 'Escrow_Funded'
                                CHECK(order_status IN ('Escrow_Funded', 'In_Transit', 'Delivered', 'Completed', 'Cancelled', 'Disputed')),
    delivered_at                TEXT, -- Timestamp set upon physical delivery confirmation
    created_at                  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at                  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ---------------------------------------------------------------------------
-- 4. TABLE: escrow_holdings
--    Stateful escrow holding ledger for active transactions.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS escrow_holdings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id            INTEGER NOT NULL UNIQUE REFERENCES orders(id) ON DELETE RESTRICT,
    held_amount_pkr     REAL NOT NULL CHECK(held_amount_pkr > 0),
    escrow_status       TEXT NOT NULL DEFAULT 'HELD'
                        CHECK(escrow_status IN ('HELD', 'RELEASED', 'REFUNDED', 'DISPUTED')),
    held_at             TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    delivered_at        TEXT, -- Mirrors orders.delivered_at
    auto_release_at     TEXT, -- Future seam: set to delivered_at + 72 hours
    released_at         TEXT,
    release_tx_ref      TEXT  -- Format: "TRIGGER:<trigger_type>;REF:<tx_identifier>"
);

-- ---------------------------------------------------------------------------
-- 5. TABLE: telemetry_cache
--    API Database Caching (Doc 3 §5.1) — Rate-limit protection for external APIs.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS telemetry_cache (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key           TEXT NOT NULL UNIQUE, -- e.g. "weather:30.3753:69.3451"
    provider            TEXT NOT NULL CHECK(provider IN ('OpenWeatherMap', 'SoilGrids')),
    latitude            REAL NOT NULL,
    longitude           REAL NOT NULL,
    payload_json        TEXT NOT NULL,
    fetched_at          TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    expires_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_telemetry_cache_lookup 
    ON telemetry_cache(cache_key, expires_at);

-- ---------------------------------------------------------------------------
-- 6. TABLE: yield_forecasts
--    Persisted mathematical model outputs from Predictive Yield Engine.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS yield_forecasts (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id              INTEGER NOT NULL REFERENCES listings(id) ON DELETE RESTRICT,
    crop_name               TEXT NOT NULL,
    predicted_harvest_date  TEXT NOT NULL,
    predicted_yield_kg      REAL NOT NULL CHECK(predicted_yield_kg > 0),
    confidence_score_pct    INTEGER NOT NULL CHECK(confidence_score_pct >= 0 AND confidence_score_pct <= 100),
    environmental_index     REAL,
    irrigation_advice       TEXT,
    generated_at            TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ---------------------------------------------------------------------------
-- 7. IDEMPOTENT SEED DATA (Package A2)
--    Seeds buyer profile and initial wallet for sara_buyer, and wallet for
--    tahir_farmer.
-- ---------------------------------------------------------------------------

-- Seed Sara Buyer profile if user exists and buyer record does not (per SRS FR-BYR-006)
INSERT OR IGNORE INTO buyers (user_id, company_name, contact_phone, warehouse_address, warehouse_gps_latitude, warehouse_gps_longitude)
SELECT id, 'Metro Wholesale Foods', '+92-300-1234567', 'Metro Central Hub, Lahore', 31.5204, 74.3587
  FROM users
 WHERE username = 'sara_buyer' AND role = 'buyer';

-- SIMULATED_BUYER_STARTING_BALANCE_PKR = 500000.00
-- Seed Sara Buyer wallet with simulated starting balance of 500000.00 PKR
INSERT OR IGNORE INTO buyer_wallets (buyer_id, balance_pkr)
SELECT b.id, 500000.00
  FROM buyers b
  JOIN users u ON b.user_id = u.id
 WHERE u.username = 'sara_buyer';

-- Seed Tahir Farmer wallet with 0.00 balance
INSERT OR IGNORE INTO farmer_wallets (farmer_id, balance_pkr)
SELECT f.id, 0.00
  FROM farmers f
  JOIN users u ON f.user_id = u.id
 WHERE u.username = 'tahir_farmer';
