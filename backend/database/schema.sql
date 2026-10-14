-- =============================================================================
-- Agri-Grid: Smart Agriculture & Food Security Ecosystem
-- File:       schema.sql
-- Version:    1.0  (Increment 1 — Foundation & Farmer Dashboard)
-- Source:     AG-SRS-INC1-001 v1.1  |  AG-API-INC1-003 v1.0
-- Author:     Database & Backend Agent (DBA)
-- Date:       2026-10-12
--
-- Target DBMS : SQLite 3 (zero-config local prototype)
--               Compatible with standard SQL; migration path to
--               PostgreSQL / MySQL deferred to deployment phase.
--
-- Normalization: 3rd Normal Form (3NF)
-- Transactions:  ACID-compliant (SQLite WAL journal mode recommended)
-- Zero-Trust:    farmer_id is the row-level tenant anchor — never
--                supplied by the client; always derived from JWT on
--                the backend.
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 0. RUNTIME PRAGMAS
-- ---------------------------------------------------------------------------
-- Enforce referential integrity for every connection that opens this DB.
-- SQLite disables FK checks by default; this MUST be the first statement
-- in every session (init_db.py also issues it programmatically).
PRAGMA foreign_keys = ON;

-- Write-Ahead Logging: better concurrency for concurrent readers + 1 writer.
PRAGMA journal_mode = WAL;

-- ---------------------------------------------------------------------------
-- 1. TABLE: users
--    Master authentication and RBAC identity store.
--    All six system actors share this table; role drives routing.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    -- Surrogate PK ─ auto-increment integer (SQLite ROWID alias)
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,

    -- Login credential — must be globally unique across all roles
    username            TEXT        NOT NULL UNIQUE
                                    CHECK(LENGTH(username) >= 3 AND LENGTH(username) <= 50),

    -- Bcrypt / Argon2 digest — plaintext NEVER stored (NFR-SEC-001)
    password_hash       TEXT        NOT NULL,

    -- RBAC role — drives dashboard routing and middleware enforcement
    -- Extensible via CHECK; new roles require only a schema ALTER in
    -- future increments (NFR-MNT-001).
    role                TEXT        NOT NULL
                                    CHECK(role IN (
                                        'farmer',
                                        'buyer',
                                        'transporter',
                                        'agronomist',
                                        'compliance_officer'
                                    )),

    -- Optional contact (UNIQUE allows NULL duplicates in SQLite)
    email               TEXT        UNIQUE
                                    CHECK(email IS NULL OR LENGTH(email) <= 100),

    -- Soft-deactivation flag — preserves audit trail without hard deletes
    is_active           INTEGER     NOT NULL DEFAULT 1
                                    CHECK(is_active IN (0, 1)),

    -- Immutable creation timestamp (UTC ISO-8601)
    created_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ---------------------------------------------------------------------------
-- 2. TABLE: farmers
--    Extended profile for users whose role = 'farmer'.
--    1-to-1 with users (enforced by UNIQUE constraint on user_id).
--    Carries the default GPS anchor for the farm.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS farmers (
    -- Surrogate PK
    id                  INTEGER     PRIMARY KEY AUTOINCREMENT,

    -- FK to users.id  — 1:1 relationship; UNIQUE prevents duplicate profiles
    -- ON DELETE CASCADE: removing a user record purges the farmer profile
    -- and all downstream listings (via the cascade on listings.farmer_id).
    user_id             INTEGER     NOT NULL UNIQUE
                                    REFERENCES users(id) ON DELETE CASCADE,

    -- Human-readable farm identity (required at registration for farmers)
    farm_name           TEXT        NOT NULL
                                    CHECK(LENGTH(farm_name) >= 1 AND LENGTH(farm_name) <= 100),

    -- Optional free-text address / region
    farm_location       TEXT,

    -- Default GPS anchor for the farm; individual listings may override.
    -- DECIMAL(9,6) precision: ±0.000001° ≈ ±0.11 m — sufficient for field-level accuracy.
    default_gps_latitude    REAL    CHECK(default_gps_latitude  IS NULL OR
                                         (default_gps_latitude  >= -90.0  AND
                                          default_gps_latitude  <= 90.0)),

    default_gps_longitude   REAL    CHECK(default_gps_longitude IS NULL OR
                                         (default_gps_longitude >= -180.0 AND
                                          default_gps_longitude <= 180.0)),

    -- Immutable creation timestamp
    created_at          TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ---------------------------------------------------------------------------
-- 3. TABLE: listings
--    Active crop ledger — the primary data-generation point of the system.
--    Each row = one crop cultivated by one farmer.
--    Zero-Trust anchor: farmer_id links every row to its owning tenant.
--
--    Soft-delete design (AG-API-INC1-003 §4.5 / CTO Blocker 3 Fix):
--      Physical DELETE queries are PROHIBITED on this table.
--      Retirement = UPDATE SET is_deleted = 1, status = 'Withdrawn'.
--      Reason: preserves provenance chain for future Increment 5 consumer QR.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS listings (
    -- Surrogate PK
    id                      INTEGER     PRIMARY KEY AUTOINCREMENT,

    -- Tenant anchor — FK to farmers.id
    -- ON DELETE CASCADE: if a farmer profile is removed, all their listings
    -- are also purged (data hygiene; aligns with NFR-REL-003).
    farmer_id               INTEGER     NOT NULL
                                        REFERENCES farmers(id) ON DELETE CASCADE,

    -- Crop taxonomy (enum, validated again at the API layer per AG-API-INC1-003 §4.1)
    crop_name               TEXT        NOT NULL
                                        CHECK(crop_name IN (
                                            'Wheat', 'Rice', 'Tomato', 'Potato',
                                            'Cotton', 'Maize', 'Sugarcane', 'Other'
                                        )),

    -- Agricultural date fields
    planting_date           TEXT        NOT NULL,   -- stored as 'YYYY-MM-DD'
    estimated_harvest_date  TEXT        NOT NULL,   -- stored as 'YYYY-MM-DD'

    -- Quantitative fields — CHECK constraints mirror API validation (§8.3 SRS)
    acreage                 REAL        NOT NULL CHECK(acreage > 0),
    gps_latitude            REAL        NOT NULL CHECK(gps_latitude  >= -90.0  AND gps_latitude  <= 90.0),
    gps_longitude           REAL        NOT NULL CHECK(gps_longitude >= -180.0 AND gps_longitude <= 180.0),
    quantity_kg             REAL        NOT NULL CHECK(quantity_kg > 0),

    -- Lifecycle status — backend sets 'Active' on creation; farmer cannot override
    status                  TEXT        NOT NULL DEFAULT 'Active'
                                        CHECK(status IN (
                                            'Active',
                                            'Sold',
                                            'In Transit',
                                            'Delivered',
                                            'Withdrawn'
                                        )),

    -- Soft-delete flag (0 = live, 1 = withdrawn/archived)
    -- All GET queries MUST include WHERE is_deleted = 0 (enforced at API layer)
    is_deleted              INTEGER     NOT NULL DEFAULT 0
                                        CHECK(is_deleted IN (0, 1)),

    -- Audit timestamps
    created_at              TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    updated_at              TEXT        NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

-- ---------------------------------------------------------------------------
-- 4. TRIGGER: listings_updated_at
--    SQLite has no native ON UPDATE DEFAULT; this trigger maintains
--    updated_at integrity automatically on every UPDATE statement.
-- ---------------------------------------------------------------------------
CREATE TRIGGER IF NOT EXISTS trg_listings_updated_at
    AFTER UPDATE ON listings
    FOR EACH ROW
BEGIN
    UPDATE listings
       SET updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
     WHERE id = OLD.id;
END;

-- ---------------------------------------------------------------------------
-- 5. PERFORMANCE INDEXES
--    Justified by the query patterns defined in AG-API-INC1-003:
--
--    idx_users_username      : Login lookup — O(log n) vs O(n) full scan
--    idx_listings_farmer_id  : GET /api/crops tenant filter (hot path)
--    idx_listings_status     : Future marketplace filtering by status
--    idx_listings_is_deleted : Every active listing query filters on this
--    idx_listings_farmer_active : Composite — covers the exact WHERE clause
--                                 used by GET /api/crops (farmer + not deleted)
-- ---------------------------------------------------------------------------

-- Single-column indexes
CREATE INDEX IF NOT EXISTS idx_users_username
    ON users(username);

CREATE INDEX IF NOT EXISTS idx_listings_farmer_id
    ON listings(farmer_id);

CREATE INDEX IF NOT EXISTS idx_listings_status
    ON listings(status);

CREATE INDEX IF NOT EXISTS idx_listings_is_deleted
    ON listings(is_deleted);

-- Composite index: covers the most frequent query pattern
--   SELECT * FROM listings WHERE farmer_id = ? AND is_deleted = 0
CREATE INDEX IF NOT EXISTS idx_listings_farmer_active
    ON listings(farmer_id, is_deleted);

-- =============================================================================
-- End of schema.sql
-- All DDL is idempotent (CREATE ... IF NOT EXISTS) — safe to re-run.
-- =============================================================================
