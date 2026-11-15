-- =============================================================================
-- Agri-Grid: Smart Agriculture & Food Security Ecosystem
-- Migration:  003_buyers_legacy_profile.sql
-- Module:     Increment 2 Core Data Engine & Buyer Profile Relaxation (D-INC2-11)
-- Author:     Bareera Noor (Database Administrator)
-- Date:       2026-11-15
-- Source:     D-INC2-11 & Fix-Round Prompt 2b
--
-- Target DBMS : SQLite 3 (zero-config local prototype)
-- Normalization: 3rd Normal Form (3NF)
-- Transactions:  ACID-compliant
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1. TABLE REBUILD: buyers
--    Relax CHECK constraints on company_name, contact_phone, and
--    warehouse_address to permit length = 0 (empty string) for legacy
--    profile registrations under determination D-INC2-11, while preserving
--    the full format range checks for non-empty profiles.
-- ---------------------------------------------------------------------------
CREATE TABLE buyers_new (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                 INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE RESTRICT,
    company_name            TEXT NOT NULL CHECK(LENGTH(company_name) = 0 OR (LENGTH(company_name) >= 2 AND LENGTH(company_name) <= 100)),
    contact_phone           TEXT NOT NULL CHECK(LENGTH(contact_phone) = 0 OR (LENGTH(contact_phone) >= 7 AND LENGTH(contact_phone) <= 20)),
    warehouse_address       TEXT NOT NULL CHECK(LENGTH(warehouse_address) = 0 OR LENGTH(warehouse_address) >= 5),
    warehouse_gps_latitude  REAL CHECK(warehouse_gps_latitude IS NULL OR (warehouse_gps_latitude >= -90.0 AND warehouse_gps_latitude <= 90.0)),
    warehouse_gps_longitude REAL CHECK(warehouse_gps_longitude IS NULL OR (warehouse_gps_longitude >= -180.0 AND warehouse_gps_longitude <= 180.0)),
    created_at              TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

INSERT INTO buyers_new (id, user_id, company_name, contact_phone, warehouse_address, warehouse_gps_latitude, warehouse_gps_longitude, created_at)
SELECT id, user_id, company_name, contact_phone, warehouse_address, warehouse_gps_latitude, warehouse_gps_longitude, created_at
  FROM buyers;

DROP TABLE buyers;

ALTER TABLE buyers_new RENAME TO buyers;
