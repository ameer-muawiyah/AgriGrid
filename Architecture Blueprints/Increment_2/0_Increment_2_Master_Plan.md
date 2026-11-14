# Master Document: Increment 2 Master Architecture & Execution Plan
## Core Data Engine & Demand Side (B2B Marketplace, Escrow & Predictive Yield)

| Field | Value |
|---|---|
| **Project Name** | Agri-Grid: Smart Agriculture & Food Security Ecosystem |
| **Document ID** | `AG-PLAN-INC2-001` |
| **Version** | 1.1 (Master Execution Plan) |
| **Prepared By** | Ameer Muawiyah (Scrum Master + Lead Data Architect) |
| **Reviewed By** | Ameer Muawiyah (Scrum Master + Lead Data Architect) |
| **Date** | 2026-11-13 |
| **Target Stage** | Increment 2 (Core Data Engine & Demand Side) |
| **Methodology** | Agile-Incremental Hybrid with V-Model Continuous Verification & Validation |
| **Source Documents** | Docs 1–7 (`./Documentation/`), `AG-SRS-INC1-001`, `AG-API-INC1-003`, `FRONTEND_CHANGE_CHECKLIST.md` |

> **v1.1 — Amendment round per Scrum Master audit, 2026-11-13**

---

## Table of Contents
1. [Baseline Confirmation & Discrepancy Audit](#1-baseline-confirmation--discrepancy-audit)
2. [Scope Statement & Document Traces](#2-scope-statement--document-traces)
3. [System Integration Map](#3-system-integration-map)
4. [Architectural Gap-Closure Designs](#4-architectural-gap-closure-designs)
   - 4.1 Automated Database Migration Engine
   - 4.2 Behavior-Preserving Service Layer Extraction
   - 4.3 End-to-End Status Lifecycle & Transition State Machine
   - 4.4 Backlog Cleanups (Currency, Taxonomies, Contract Test Extensions)
5. [Data Model Delta & Persistence Schema](#5-data-model-delta--persistence-schema)
6. [API Contract Delta & JSON Envelopes](#6-api-contract-delta--json-envelopes)
7. [Frontend Plan & Human-Computer Interface](#7-frontend-plan--human-computer-interface)
8. [Role & Permission Matrix](#8-role--permission-matrix)
9. [Work Breakdown Structure & Sprint Phases](#9-work-breakdown-structure--sprint-phases)
10. [Verification & Validation Strategy (V-Model Gate)](#10-verification--validation-strategy-v-model-gate)
11. [Risk Analysis & Mitigation Engineering](#11-risk-analysis--mitigation-engineering)
12. [Future-Increment Readiness & Architectural Seams](#12-future-increment-readiness--architectural-seams)
13. [Scrum Master Decision List](#13-scrum-master-decision-list)

---

## 1. Baseline Confirmation & Discrepancy Audit

### 1.1 Baseline Status Confirmation
On 2026-11-13, an exhaustive local audit of the Agri-Grid repository (`D:\3rd Semester\Software Engineering\AgriGrid`) confirmed that **Increment 1 is officially closed and certified**.

- **Backend Application Factory:** `backend/app.py` correctly implements `create_app()`, registers `crops_bp`, wires error handlers, supports CORS for local dev origins (`http://127.0.0.1:5500`), and serves RBAC-protected endpoints.
- **Security & Cryptography:** `backend/auth.py` enforces stateless HS256 JWT tokens, OWASP-compliant password complexity, `bcrypt` hashing with backward-compatible `PBKDF2-HMAC-SHA256` digest verification, and route decorators (`@token_required`, `@role_required`).
- **Data Persistence:** `backend/database/schema.sql` establishes 3NF tables (`users`, `farmers`, `listings`) with `PRAGMA foreign_keys = ON;`, WAL mode, and update triggers. `backend/database/init_db.py` bootstraps and seeds test credentials (`tahir_farmer`, `sara_buyer`).
- **Presentation Layer:** Reskinned under the **Terra × Terracotta** design-token aesthetic (`frontend/css/auth.css`, `frontend/css/dashboard.css`). Pure vanilla ES6 (`frontend/js/auth.js`, `frontend/js/dashboard.js`), zero framework dependencies, with anti-FOUC auth guarding, XSS entity escaping, and mobile-responsive viewport containment.
- **Single-Click Operations:** Operational launcher scripts (`start-agri-grid.bat`, `start-agri-grid.sh`, and `launch_agrigrid.py`) execute backend and frontend servers with automated port-readiness polling and browser startup.
- **Automated V-Model Test Gate:** All 3 test suites were executed on 2026-11-13 and passed with a 100% success rate:
  - `backend/test_auth.py`: **17 / 17 Passed**
  - `backend/test_crops_api.py`: **23 / 23 Passed**
  - `backend/test_frontend_contract.py`: **5 / 5 Passed**
  - **Total Increment 1 Regression Suite:** **45 / 45 Passed (100%)**.

### 1.2 Discrepancy & Finding Report
The baseline scan identified three discrepancies between project documentation notes and physical repository state that must be explicitly acknowledged:

1. **`asking_price` Persistence Scaffolding Discrepancy (Critical):**
   - *Briefing Note:* States that "`asking_price` already exists on listings as nullable Increment-2 scaffolding."
   - *Physical Reality:* In the presentation layer (`frontend/dashboard.html` lines 121, 232 and `frontend/js/dashboard.js` lines 280, 449), asking price is scaffolded in form inputs and UI headers with `<span class="inc2-badge">Inc 2</span>`. However, in the physical SQLite database (`backend/database/schema.sql`) and backend validation (`backend/crops.py`), the column **does not exist** in the `listings` table and is ignored in payload processing.
   - *Plan Impact:* Increment 2 cannot assume the column exists. It must be added via an explicit migration step (`002_increment_2_marketplace_escrow_telemetry.sql`).
2. **Duplicate SQLite Database Artifact:**
   - *Physical Reality:* Two database files exist: `backend/database/agrigrid.db` (the active database path referenced by `app.py`) and a stray `backend/agrigrid.db` (created by direct script execution from `backend/`).
   - *Plan Impact:* All migrations and service layers must strictly anchor to `DB_PATH = os.path.join(BASE_DIR, "database", "agrigrid.db")` to avoid database bifurcation.
3. **Currency Symbol Inconsistency:**
   - *Physical Reality:* The Increment 1 UI displays `$` symbols (`Asking Price ($/kg)` and `$${price} / kg`), whereas the system domain context is Pakistani agriculture (e.g., `Punjab, Pakistan` in seed data).
   - *Plan Impact:* Increment 2 will standardize currency formatting to **Rs / PKR** across frontend and backend contracts.

---

## 2. Scope Statement & Document Traces

Increment 2 establishes the **Demand Side** (B2B wholesale marketplace) and the **Analytical Core** (environmental data integration and algorithmic yield forecasting).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        INCREMENT 2 CORE PILLARS                        │
├────────────────────────┬───────────────────────────────────────────────┤
│ B2B Marketplace        │ Public wholesale catalog, filtering, and      │
│ (Demand Side)          │ buyer procurement exchange.                   │
├────────────────────────┼───────────────────────────────────────────────┤
│ Digital Escrow Engine  │ Contractual purchase agreements, funds locking│
│ (Financial Integrity)  │ (simulated), cold-chain parameter mandates.   │
├────────────────────────┼───────────────────────────────────────────────┤
│ External Telemetry     │ OpenWeatherMap & SoilGrids integration with   │
│ (Environmental Context)│ database rate-limit caching (6-hour TTL).     │
├────────────────────────┼───────────────────────────────────────────────┤
│ Predictive Yield Engine│ Algorithmic yield & harvest readiness engine  │
│ (Intelligence Layer)   │ combining telemetry and farmer crop inputs.   │
└────────────────────────┴───────────────────────────────────────────────┘
```

### 2.1 In-Scope Features & Document Traceability Matrix

| Feature ID | Feature Name | Detailed Description | Document Trace | Primary Actor |
|---|---|---|---|---|
| **FEAT-INC2-01** | B2B Procurement Catalog | Searchable, paginated produce catalog allowing wholesale buyers to filter available listings by crop variety, maximum price, available quantity, and geographic region. | Doc 4 §2.2; Doc 5 §2 Step 2; Doc 6 §2 | B2B Buyer |
| **FEAT-INC2-02** | Buyer Profile Onboarding | Profile registration and storage for wholesale buyers (`company_name`, `warehouse_address`, `warehouse_gps_lat`, `warehouse_gps_lon`, `contact_phone`). | Doc 4 §2.2; Doc 5 §2 Step 2 | B2B Buyer |
| **FEAT-INC2-03** | Digital Escrow Ordering | Purchase contract checkout. Buyer locks purchase value into digital escrow (`escrow_holdings`), defines delivery warehouse, and mandates cold-chain constraints (e.g., maximum temperature `< 6°C`). | Doc 4 §2.2; Doc 5 §2 Step 2; Doc 7 §2 | B2B Buyer |
| **FEAT-INC2-04** | Buyer Quality Acceptance & Settlement | Delivery sign-off terminal. Buyer reviews produce delivery, enters inspection score, and executes release of escrow funds to farmer wallet (`farmer_wallets`). | Doc 4 §2.2; Doc 5 §2 Step 5 | B2B Buyer |
| **FEAT-INC2-05** | Farmer Listing Publishing & Commercial Pricing | Interface for farmers to convert active crop records into commercial offerings with a real `asking_price_per_kg` and generated `batch_id`. | Doc 4 §2.1; Doc 5 §2 Step 1 | Farmer |
| **FEAT-INC2-06** | Simulated Multi-Party Wallets | Virtual ledger tracking buyer deposit balances, locked escrow commitments, and farmer receivable accounts. | Doc 4 §2.2; Doc 5 §2 Step 2, 5; Doc 7 §2 | Farmer / Buyer |
| **FEAT-INC2-07** | External Weather & Soil Telemetry Client | Python integration pulling hyper-local 14-day rainfall, temperature, humidity (OpenWeatherMap) and soil moisture/pH (SoilGrids) via GPS coordinates. | Doc 3 §3; Doc 3 §4 | System / Data Engine |
| **FEAT-INC2-08** | Telemetry Database Caching Engine | Rate-limit protection caching raw API payloads in SQLite with a 6-hour TTL timestamp, preventing external API quota exhaustion. | Doc 3 §5.1; Doc 5 §2 Step 1 | Backend / DBA |
| **FEAT-INC2-09** | Algorithmic Predictive Yield Engine | Pure Python calculation service combining crop growth metrics, planting date, and soil/weather telemetry to output estimated harvest dates and yield quantities. | Doc 2 §3 (Role 2); Doc 3 §4; Doc 5 §2 Step 1 | System / Data Architect |
| **FEAT-INC2-10** | Database Migration Infrastructure | Automated, versioned migration runner ensuring continuous schema evolution without wiping existing data. | System Gap 1 Closure | DBA / DevOps |
| **FEAT-INC2-11** | Backend Service Layer Extraction | Refactoring monolithic route handlers into pure business logic services while keeping the 45 Increment 1 tests 100% green. | System Gap 2 Closure | Core Backend |
| **FEAT-INC2-12** | Global Status State Machine | Formalization and enforcement of valid lifecycle state transitions across all entities (`listings`, `orders`, `escrow`). | System Gap 3 Closure | Architect / Backend |

### 2.2 Explicitly Out-of-Scope (Deferred to Later Increments)
The following modules must not be built in Increment 2; placeholders remain in place:
1. **Transporter Logistics & In-Transit Telemetry (Increment 3):** QR code camera handshake, driver dispatch manifests, truck temperature hardware telemetry logging, and offline mobile flash caching.
2. **Agronomist Telemedicine & Prescriptions (Increment 4):** Diagnostic photo ticketing queues, split-screen expert workbenches, digital prescription forms, and regional outbreak heatmaps.
3. **Compliance & Grant Auditing (Increment 4):** Government subsidy applications, automated satellite cross-checking confidence scoring, and grant disbursement ledgers.
4. **Consumer QR Provenance Storyboard (Increment 5):** Unauthenticated public QR landing page, farm-to-table vertical visual timeline, and consumer verification scans.
5. **Real-Money Payment Gateways:** Real credit card/banking rails (Stripe, JazzCash, EasyPaisa) are out-of-scope; escrow operations are strictly simulated via internal ACID-compliant ledger tables.
6. **Dispute Resolution Workflow:** While dispute flagging (`POST /api/orders/<id>/dispute`) is available to record dissatisfaction and freeze escrow funds, **no dispute-resolution endpoint or administrative arbitration workflow exists in Increment 2**. Adjudication and escrow unfreezing are formal Increment 4 (Compliance Officer) capabilities.

### 2.3 Disposition of Self-Service Password Recovery ("Forgot Password")
- **Context:** The Increment 1 auth UI (`frontend/index.html` line 124) displays: `Self-service recovery scheduled for Increment 2`.
- **Engineering Assessment:** Building production-grade self-service recovery requires SMTP server configuration, outbound email delivery, secure cryptographic single-use reset tokens with expiry tables, and rate-limiting. Introducing SMTP infrastructure in Increment 2 would distract from the core deliverables (Demand Side & Predictive Yield).
- **Formal Disposition:** **Formally Defer to Increment 4 (Administration & Governance).**
- **Immediate Action in Increment 2:** Update the copy in `frontend/index.html` to state: *"Self-service recovery scheduled for Increment 4 — Contact admin for access."* This closes the UI debt transparently without breaking any backend contracts.

---

## 3. System Integration Map

Increment 2 does not operate in isolation. It anchors directly into the components built in Increment 1:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        INCREMENT 2 INTEGRATION MAP                     │
├───────────────────────┬──────────────────────┬─────────────────────────┤
│ Increment 1 Component │ Mode of Attachment   │ Increment 2 Impact      │
├───────────────────────┼──────────────────────┼─────────────────────────┤
│ users Table           │ 1-to-1 Foreign Key   │ Provisions new buyers   │
│                       │                      │ profile table.          │
├───────────────────────┼──────────────────────┼─────────────────────────┤
│ listings Table        │ Extension & FK Root  │ Adds asking_price_per_kg│
│                       │                      │ and batch_id; orders FK │
│                       │                      │ anchors to listings.id. │
├───────────────────────┼──────────────────────┼─────────────────────────┤
│ crops.py Blueprint    │ Service Layer Handoff│ Reads/updates listings  │
│                       │                      │ status via shared crop  │
│                       │                      │ service.                │
├───────────────────────┼──────────────────────┼─────────────────────────┤
│ auth.py Security Core │ Reused Intact        │ @token_required &       │
│                       │                      │ @role_required('buyer') │
│                       │                      │ protect buyer routes.   │
├───────────────────────┼──────────────────────┼─────────────────────────┤
│ dashboard.html        │ Enhanced In-Place    │ Adds commercial pricing │
│ (Farmer Console)      │                      │ and Yield Forecast CTA. │
├───────────────────────┼──────────────────────┼─────────────────────────┤
│ Role Placeholders     │ Substituted          │ /dashboard/buyer serves │
│                       │                      │ real marketplace UI.    │
└───────────────────────┴──────────────────────┴─────────────────────────┘
```

1. **Authentication Gateway (`backend/auth.py`):**
   - Reused with zero breaking changes.
   - The `@token_required` and `@role_required` decorators will guard all new marketplace, order, and telemetry routes.
   - The pre-seeded buyer account (`sara_buyer` / `BuyerPass1`) and newly registered buyers will now route to an active buyer dashboard rather than a placeholder.
2. **Crop Persistence (`backend/database/schema.sql` & `backend/crops.py`):**
   - The `listings` table remains the immutable provenance root.
   - When a B2B Buyer purchases a crop in Increment 2, the listing's lifecycle status transitions from `'Active'` to `'Sold'`.
   - The soft-delete invariant (`is_deleted = 1`, `status = 'Withdrawn'`) remains strictly enforced: buyers can never view or purchase withdrawn listings.
3. **Error Handling & JSON Envelopes (`AG-API-INC1-003`):**
   - All new endpoints under `/api/marketplace/*`, `/api/orders/*`, `/api/telemetry/*`, and `/api/yield/*` adhere strictly to the established standard response envelopes (`{"success": true, "data": ...}` and `{"success": false, "error": "..."}`).

---

## 4. Architectural Gap-Closure Designs

### 4.1 Automated Database Migration Engine (Gap 1 Closure)

To eliminate the dangerous practice of destroying `agrigrid.db` on schema changes, Increment 2 introduces a lightweight, zero-dependency migration framework.

#### Migration Directory Structure
```text
backend/database/
├── agrigrid.db                      # SQLite WAL database file
├── schema.sql                       # Master baseline (v1)
├── init_db.py                       # Bootstrap & seed script
├── migrate.py                       # Automated migration runner
└── migrations/
    ├── 001_increment_1_baseline.sql # Recorded snapshot of Inc 1
    └── 002_increment_2_marketplace_escrow_telemetry.sql # Inc 2 DDL
```

#### Migration Mechanism Design
1. **Version Tracking Table with Checksum Security:**
   ```sql
   CREATE TABLE IF NOT EXISTS schema_versions (
       id          INTEGER PRIMARY KEY AUTOINCREMENT,
       version     INTEGER NOT NULL UNIQUE,
       script_name TEXT NOT NULL,
       checksum    TEXT NOT NULL, -- SHA-256 hex digest of file contents
       applied_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
   );
   ```
2. **Explicit Transaction & Statement Execution Rules:**
   - The runner splits each migration file into individual SQL statements and executes them under explicit transaction control using a connection with `isolation_level=None`.
   - The runner opens with `BEGIN IMMEDIATE` and closes with `COMMIT` (or `ROLLBACK` on any error).
   - **Critical Rule:** The runner **must NOT use** `sqlite3.executescript()`, because `executescript()` executes an implicit `COMMIT` before running, which silently destroys the all-or-nothing transactional guarantee.
3. **Immutable Checksum Verification:**
   - On every run, the runner computes the SHA-256 checksum of every already-applied migration file in `backend/database/migrations/` and compares it to the recorded `checksum` in `schema_versions`.
   - If an applied migration file was edited after application, the runner **fails loudly and halts startup**, preventing silent database divergence across team members.
4. **Single Deterministic Trigger Point:**
   - Migrations are triggered automatically by `launch_agrigrid.py`, which invokes `backend/database/migrate.py` before launching the Flask backend (a fast no-op if current).
   - In addition, `backend/app.py` startup performs a lightweight read-only check against `schema_versions`; if the database version is behind the codebase requirement, it refuses to boot and logs an explicit remediation command: `python backend/database/migrate.py`.

### 4.2 Behavior-Preserving Service Layer Extraction (Gap 2 Closure)

In Increment 1, controller functions in `backend/crops.py` directly executed raw SQL and validation. In Increment 2, multiple blueprints (`crops_bp`, `marketplace_bp`, `orders_bp`) need access to listing status transitions, tenant validation, and inventory calculations.

#### Architecture of the Service Layer
```text
backend/
├── app.py                     # Presentation & Blueprint routing
├── crops.py                   # HTTP Controller (Farmer endpoints)
├── marketplace.py             # HTTP Controller (Buyer catalog endpoints)
├── orders.py                  # HTTP Controller (Escrow & checkout endpoints)
├── telemetry.py               # HTTP Controller (Weather & soil endpoints)
└── services/                  # Pure Business Logic Layer
    ├── __init__.py
    ├── crop_service.py        # Listing CRUD, validation, status guards
    ├── marketplace_service.py # Catalog querying, public filtering
    ├── escrow_service.py      # Order creation, funds locking, settlement
    ├── yield_service.py       # Algorithmic predictive yield calculations
    └── telemetry_service.py   # External API fetchers & SQLite caching
```

*(Note: Auth internals in `backend/auth.py` are deliberately excluded from service extraction in Phase 1; they represent the highest-blast-radius code in the system and require zero changes for Increment 2).*

#### Refactoring & Gating Procedure
1. Extract `_validate_crop_payload()` and database queries from `crops.py` into `services/crop_service.py`.
2. Controller `crops.py` delegates directly to `crop_service.py` and maps service results to Flask `jsonify()` responses.
3. **Escrow Service Release Operation Contract:**
   The escrow service implements a strictly typed release operation:
   ```python
   def release_escrow(order_id: int, trigger: str) -> dict:
       """
       Release held escrow funds to the farmer wallet.
       trigger MUST be one of: 'buyer_confirmation', 'auto_timeout', 'admin'
       """
   ```
   In Increment 2, this function is invoked **strictly with `trigger='buyer_confirmation'`**. The trigger identifier and timestamp are recorded in `escrow_holdings.release_tx_ref` (`"TRIGGER:buyer_confirmation;REF:<tx_id>"`), guaranteeing full auditability.
4. **Regression Gate:** The refactoring is executed **prior to adding any Increment 2 features**. Before merging the service extraction, all 45 existing tests (`test_auth.py`, `test_crops_api.py`, `test_frontend_contract.py`) must run and pass with zero modifications.

### 4.3 End-to-End Status Lifecycle & Transition State Machine (Gap 3 Closure)

To prevent invalid business states (e.g., buying a withdrawn crop, or withdrawing a crop that has already been delivered), the system enforces a strict finite state machine across `listings` and `orders`.

#### Master State Transition Matrix

| Entity | Current Status | Allowed Target Status | Permitted Role | Triggering Action & Endpoint | Invariant / Validation Pre-Condition |
|---|---|---|---|---|---|
| **Listing** | `Active` | `Withdrawn` | `farmer` | Farmer soft-deletes (`DELETE /api/crops/<id>`) | Must be owned by farmer; listing has zero pending or held orders. |
| **Listing** | `Active` | `Sold` | `system` / `buyer` | Buyer submits escrow order (`POST /api/orders`) | Ordered quantity equals the listing's full `quantity_kg`; buyer wallet has sufficient balance. |
| **Listing** | `Sold` | `Active` | `system` | Order cancelled (`POST /api/orders/<id>/cancel`) | Escrow refunded to buyer wallet; crop returned to public catalog. |
| **Listing** | `Sold` | `In Transit` | `transporter` *(Inc 3)* | Transporter scans QR code (`POST /api/logistics/handshake`) | Custody transfer verified. |
| **Listing** | `In Transit` | `Delivered` | `transporter` *(Inc 3)* | Transporter logs PoD (`POST /api/logistics/pod`) | Delivery signature captured. |
| **Order** | `Escrow_Funded` | `Completed` | `buyer` | Buyer accepts quality (`POST /api/orders/<id>/confirm-delivery`) | Order is `Escrow_Funded`; sets `orders.delivered_at`; releases escrow funds via `release_escrow(order_id, 'buyer_confirmation')`. |
| **Order** | `Escrow_Funded` | `Cancelled` | `buyer` / `farmer` | Cancellation request (`POST /api/orders/<id>/cancel`) | Order not yet completed; escrow refunded to buyer wallet; listing returns to `Active`. |
| **Order** | `Escrow_Funded` | `Disputed` | `buyer` / `farmer` | Dispute flagged (`POST /api/orders/<id>/dispute`) | Order is `Escrow_Funded`; freezes escrow funds (`escrow_status → DISPUTED`). |
| **Order** | `Escrow_Funded` | `In_Transit` | `transporter` *(Inc 3)* | Handshake completed at farm | Manifest marked active. |
| **Order** | `In_Transit` | `Delivered` | `transporter` *(Inc 3)* | PoD uploaded | Cargo arrived at buyer warehouse. |

> **Increment 2 Operational Reality Note:** In Increment 2, with no transporter role active, the buyer's quality acceptance action (`POST /api/orders/<id>/confirm-delivery`) doubles as delivery confirmation and transitions the order directly from `Escrow_Funded` to `Completed`. In Increment 3, the transporter's physical actions will insert `In_Transit` and `Delivered` between these states without altering the buyer confirmation contract.
>
> **Scope Boundary Note:** Dispute flagging is strictly record-only in Increment 2. No dispute-resolution endpoint or workflow exists in Increment 2; formal dispute adjudication and escrow arbitration are deferred to Increment 4 (Compliance).

### 4.4 Backlog Cleanups

1. **Taxonomy & Vocabularies Architecture:**
   - The **farmer dashboard's** crop `<select>` remains statically rendered in HTML (preserving the Increment 1 pattern); `TC-F1` continues to verify it against the backend constant.
   - The **buyer UI's** crop filter is dynamically populated from `GET /api/meta/taxonomies`.
   - `TC-F1` gains an automated runtime assertion: the array returned by `GET /api/meta/taxonomies` must match `crops.py:VALID_CROP_NAMES` byte-for-byte.
   - `TC-F2` likewise validates the endpoint's status list against `crops.py:VALID_STATUSES`.
2. **Currency Standardization:**
   - Migrate UI and contracts from `$` to **`Rs. / PKR`** (e.g., `Rs. 45.00 / kg`).
3. **Contract Test Extension:**
   - Extend `test_frontend_contract.py` (`TC-F3`) to scan `document.querySelector` and `document.querySelectorAll` string literals in addition to class attributes, guaranteeing 100% CSS selector integrity.

---

## 5. Data Model Delta & Persistence Schema

Increment 2 applies migration `002_increment_2_marketplace_escrow_telemetry.sql` to expand the schema from 3 tables to 9 tables.

```
┌────────────────────────────────────────────────────────────────────────┐
│                     INCREMENT 2 EXTENDED ER DIAGRAM                    │
└────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐         1:1          ┌──────────────┐
    │    users     ├──────────────────────┤   farmers    │
    │ (Auth Core)  │                      │ (Farm Data)  │
    └──────┬───────┘                      └──────┬───┬───┘
           │ 1:1                                 │   │ 1:1
           ▼                                     │   ▼
    ┌──────────────┐                      1:N    │ ┌──────────────┐
    │    buyers    │                             │ │farmer_wallets│
    └──────┬───┬───┘                             │ └──────────────┘
       1:1 │   │ 1:N                             ▼
           │   │                          ┌──────────────┐
           │   │                          │   listings   │
           │   │                          │ (Crop Root)  │
           │   │                          └──┬───┬───────┘
           │   │                             │   │
           │   │         ┌───────────────────┘   │ 1:N
           │   │         ▼                       ▼
           │   │  ┌──────────────┐        ┌──────────────┐
           │   └──►    orders    │        │yield_forecast│
           │      │(Escrow Loop) │        │ (AI Output)  │
           ▼      └──────┬───────┘        └──────────────┘
    ┌──────────────┐     │ 1:1
    │buyer_wallets │     ▼
    └──────────────┘┌──────────────┐
                    │escrow_holding│
                    │(Sim. Ledger) │
                    └──────────────┘
```

### 5.1 Alterations to Existing Tables

```sql
-- 1. Extend listings table with commercial pricing and batch tracking
ALTER TABLE listings ADD COLUMN asking_price_per_kg REAL CHECK(asking_price_per_kg IS NULL OR asking_price_per_kg > 0);
ALTER TABLE listings ADD COLUMN batch_id TEXT UNIQUE;

-- Performance index for marketplace search
CREATE INDEX IF NOT EXISTS idx_listings_marketplace 
    ON listings(status, is_deleted, crop_name, asking_price_per_kg);
```

### 5.2 New Tables DDL Specification

```sql
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
--    Virtual ledgers for simulated transactions.
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
```

---

## 6. API Contract Delta & JSON Envelopes

### Universal List Response Rule
All Increment 2 list endpoints (`/api/marketplace/listings`, `/api/orders/*`) use the established **Increment 1 list envelope** (`AG-API-INC1-003`) unchanged:
```json
{
  "success": true,
  "data": [ ... ],
  "page": 1,
  "limit": 20,
  "total": 1
}
```
Extending the contract is allowed; forking it is strictly prohibited.

### 6.1 B2B Marketplace Endpoints (`backend/marketplace.py`)

#### `GET /api/marketplace/listings`
- **Method / Auth:** `GET` | Authenticated (`buyer`, `farmer` only)
- **Query Parameters:** `page` (default 1), `limit` (default 20), `crop_name` (optional), `max_price` (optional), `sort` (e.g. `price_asc`, `date_desc`).
- **Description:** Returns paginated, active, purchasable crops with price information and farm regional origin. Excludes soft-deleted (`is_deleted=1`) and non-active listings.
- **Response (200 OK):**
  ```json
  {
    "success": true,
    "data": [
      {
        "listing_id": 1,
        "batch_id": "BATCH-2026-WHT-001",
        "crop_name": "Wheat",
        "quantity_kg": 5000.0,
        "asking_price_per_kg": 45.0,
        "total_price_pkr": 225000.0,
        "estimated_harvest_date": "2027-01-15",
        "farm_name": "Green Acres Organic Field",
        "farm_location": "Punjab, Pakistan",
        "gps_latitude": 30.3753,
        "gps_longitude": 69.3451
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 1
  }
  ```

#### `GET /api/marketplace/listings/{id}`
- **Method / Auth:** `GET` | Authenticated (`buyer`, `farmer` only)
- **Description:** Full public detail for an active produce listing. If listing is withdrawn, returns unified `404 Not Found`.

### 6.2 Escrow & Order Endpoints (`backend/orders.py`)

#### `POST /api/orders`
- **Method / Auth:** `POST` | Authenticated (`buyer` only)
- **Description:** Atomic purchase transaction. Validates buyer wallet balance, creates `orders` record, locks funds in `escrow_holdings`, deducts from `buyer_wallets.balance_pkr`, and transitions listing status to `'Sold'`.
- **Request Payload:**
  ```json
  {
    "listing_id": 1,
    "ordered_quantity_kg": 5000.0,
    "destination_warehouse": "Metro Central Hub, Lahore",
    "max_temperature_celsius": 6.0
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "success": true,
    "message": "Order created successfully. Escrow funds locked.",
    "data": {
      "order_number": "ORD-2026-8941",
      "listing_id": 1,
      "total_amount_pkr": 225000.0,
      "order_status": "Escrow_Funded",
      "escrow_status": "HELD",
      "remaining_wallet_balance_pkr": 275000.0
    }
  }
  ```

#### `GET /api/orders/buyer` & `GET /api/orders/farmer`
- **Method / Auth:** `GET` | Authenticated (`buyer` or `farmer`)
- **Description:** Retrieves role-specific orders list using the Increment 1 list envelope (`data`, `page`, `limit`, `total`).

#### `POST /api/orders/{id}/confirm-delivery`
- **Method / Auth:** `POST` | Authenticated (`buyer` only)
- **Description:** Digital settlement terminal. Buyer accepts delivery, triggering atomic release of escrow funds to `farmer_wallets.balance_pkr` via `release_escrow(order_id, 'buyer_confirmation')`, populating `orders.delivered_at`, and setting order status to `'Completed'`.

#### `POST /api/orders/{id}/cancel`
- **Method / Auth:** `POST` | Authenticated (`buyer` or `farmer`)
- **Description:** Order cancellation. Only permitted when order is `Escrow_Funded`. In a single transaction, refunds held escrow back to `buyer_wallets.balance_pkr`, sets `escrow_status = 'REFUNDED'`, marks `order_status = 'Cancelled'`, and restores `listings.status = 'Active'`.

#### `POST /api/orders/{id}/dispute`
- **Method / Auth:** `POST` | Authenticated (`buyer` or `farmer`)
- **Description:** Dispute notification. Only permitted when order is `Escrow_Funded`. Transitions `order_status = 'Disputed'` and `escrow_status = 'DISPUTED'`. Funds remain frozen in escrow. Adjudication workflow is deferred to Increment 4.

### 6.3 Predictive Yield & Telemetry Endpoints (`backend/yield.py`, `backend/telemetry.py`)

#### `POST /api/yield/predict`
- **Method / Auth:** `POST` | Authenticated (`farmer` only)
- **Description:** Algorithmic computation combining crop attributes with cached weather and soil telemetry.

#### `GET /api/telemetry/weather` & `GET /api/telemetry/soil`
- **Method / Auth:** `GET` | Authenticated (`farmer`, `buyer` only)
- **Description:** Returns cached or freshly fetched telemetry for provided coordinates.

### 6.4 Registration & Backward-Compatibility Matrix

#### Atomic Buyer Onboarding Specification (`POST /api/auth/register` with `role = 'buyer'`)
- **Strictly Required Payload Fields:** `username`, `password`, `role = 'buyer'`, `company_name`, `contact_phone`, `warehouse_address`. (`warehouse_gps_latitude` and `warehouse_gps_longitude` are optional).
- **Atomic Transaction Rule:** In a single transaction, creates the `users` row, creates the `buyers` profile row, and initializes a `buyer_wallets` row with the starting balance:
  `SIMULATED_BUYER_STARTING_BALANCE_PKR = 500000.00`.
- **Validation Failure:** If any required buyer field is missing or invalid, returns `400 Bad Request` with an explicit error message and creates **no** partial user row.

| Existing Endpoint | Increment 2 Mutation | Compatibility Status | Notes |
|---|---|---|---|
| `POST /api/auth/register` | Implements atomic buyer onboarding with mandatory company fields & wallet | **Backward-Compatible** | Existing farmer registration behavior untouched. |
| `POST /api/auth/login` | Returns buyer profile and wallet ID when `role == 'buyer'` | **Backward-Compatible** | Token claims structure (`user_id`, `farmer_id`, `role`, `exp`) identical. |
| `GET /api/crops` | Now serializes `asking_price_per_kg` and `batch_id` | **Backward-Compatible** | Frontend already anticipates price field. |
| `POST /api/crops` | Accepts optional `asking_price_per_kg` on crop creation | **Backward-Compatible** | Validation allows null price for unlisted crops. |
| `PUT /api/crops/<id>` | Allows farmer to update `asking_price_per_kg` | **Backward-Compatible** | Re-validates price > 0. |

---

## 7. Frontend Plan & Human-Computer Interface

The frontend implementation strictly adheres to `FRONTEND_CHANGE_CHECKLIST.md` and preserves the approved **Terra × Terracotta** design tokens.

### 7.1 New Interface: Buyer Marketplace Console (`frontend/buyer_dashboard.html`)
- **Page Layout:** Full dashboard experience replacing the Increment 1 buyer under-construction placeholder.
- **Navigation Shell:** Reuses the verified header architecture (User Avatar, Company Name, Role Badge: `"B2B Buyer"`, Logout button).
- **Top Metric Cards:**
  - `Available Produce Listings` (Count of active items)
  - `Active Escrow Commitments` (Total Rs locked in escrow)
  - `Wallet Balance` (Simulated available liquidity in Rs)
- **Marketplace Procurement Table / Grid:**
  - Interactive search bar and filter controls (Crop Type, Max Price/kg in Rs).
  - Produce rows rendering: Batch ID, Crop Variety, Quantity Available (kg), Asking Price (Rs/kg), Farm Location, and a `"Purchase via Escrow"` action button.
- **Escrow Checkout Modal:**
  - Order summary (Crop, Total kg, Agreed Price, Total Amount in Rs).
  - Input field for Destination Warehouse.
  - Temperature constraint selector (Default `< 6°C`).
  - Action button: `"Confirm & Lock Escrow Funds"`.

### 7.2 Farmer Dashboard Extensions (`frontend/dashboard.html`)
- **Commercial Pricing Control:** In the Add/Edit Crop modal, enable the `Asking Price (Rs/kg)` field (removing the "Inc 2" disabled flag).
- **Yield Forecast Trigger:** Add a `"⚡ Forecast Yield"` button on each crop row. Clicking triggers the prediction engine modal showing predicted harvest window, estimated tonnage, and soil/weather context.
- **Orders & Sales Tab:** Add a secondary tab/view on the Farmer Dashboard displaying inbound B2B purchase orders, showing funds currently locked in escrow awaiting delivery.

### 7.3 Frontend Quality & Invariant Gates
- **Zero Undefined Classes:** All new styles must be defined in `frontend/css/dashboard.css` or `frontend/css/buyer.css`.
- **Taxonomy Lock:** The buyer UI dynamically populates crop filters from `GET /api/meta/taxonomies`.
- **Currency Consistency:** Replace all literal `$` characters with `Rs.`.
- **Anti-FOUC & Zero-Trust:** The buyer console features the inline synchronous auth check and never submits `buyer_id` in request payloads.

---

## 8. Role & Permission Matrix

| Endpoint / Operation | Farmer | B2B Buyer | Transporter *(Inc 3)* | Agronomist *(Inc 4)* | Compliance *(Inc 4)* | Public / Anon |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `POST /api/auth/register` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `POST /api/auth/login` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `GET /api/crops` (Own crops) | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |
| `POST /api/crops` (Create crop) | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |
| `GET /api/marketplace/listings` | ✅ | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |
| `POST /api/orders` (Escrow Checkout)| ❌ (403) | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |
| `GET /api/orders/buyer` | ❌ (403) | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |
| `GET /api/orders/farmer` | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |
| `POST /api/orders/<id>/confirm-delivery` | ❌ (403) | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |
| `POST /api/orders/<id>/cancel` | ✅ | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |
| `POST /api/orders/<id>/dispute` | ✅ | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |
| `POST /api/yield/predict` | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |
| `GET /api/telemetry/*` | ✅ | ✅ | ❌ (403) | ❌ (403) | ❌ (403) | ❌ (401) |

> **Standing Security Policy:** Roles scheduled for later increments (`transporter`, `agronomist`, `compliance_officer`) receive `HTTP 401 Unauthorized` / `HTTP 403 Forbidden` or their verified under-construction placeholder experience on every Increment 2 endpoint, without exception, until their dedicated increment activates them.

---

## 9. Work Breakdown Structure & Sprint Phases

The 7 team members execute Increment 2 across four sequential phases adhering to strict dependency ordering:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        INCREMENT 2 SPRINT PHASES                       │
├─────────────┬──────────────────────────────────────────┬───────────────┤
│ Phase 1     │ Foundation, Migration Engine & Services  │ Days 1–3      │
├─────────────┼──────────────────────────────────────────┼───────────────┤
│ Phase 2     │ Marketplace Catalog (Read Path)          │ Days 4–6      │
├─────────────┼──────────────────────────────────────────┼───────────────┤
│ Phase 3     │ Orders, Digital Escrow & Wallet Ledger   │ Days 7–10     │
├─────────────┼──────────────────────────────────────────┼───────────────┤
│ Phase 4     │ Telemetry, Yield Engine & Final V&V Gate │ Days 11–14    │
└─────────────┴──────────────────────────────────────────┴───────────────┘
```

### Phase 1: Foundation, Migration Engine & Service Layer (Days 1–3)
- **Task 1.1: Automated Migration Runner (`migrate.py`)**
  - *Owner:* Bareera Noor (Database Administrator)
  - *Deliverable:* Script reading `schema_versions` with SHA-256 checksums, executing split statements inside `BEGIN IMMEDIATE` / `COMMIT`.
  - *Definition of Done:* `python backend/database/migrate.py` applies `001` baseline and `002` DDL on a clean database without error and stamps `schema_versions` with valid checksums.
- **Task 1.2: DDL Migration Script & Seed Update (`002_increment_2_marketplace_escrow_telemetry.sql`)**
  - *Owner:* Bareera Noor (DBA)
  - *Deliverable:* DDL altering `listings` and creating `buyers`, `orders`, `escrow_holdings`, `buyer_wallets`, `farmer_wallets`, `telemetry_cache`, `yield_forecasts`. Update `init_db.py` to seed `sara_buyer` with profile + wallet (`SIMULATED_BUYER_STARTING_BALANCE_PKR = 500000.00`) and `tahir_farmer` with wallet.
  - *Definition of Done:* `init_db.py` bootstraps cleanly; SQL queries confirm all 9 tables exist and seed accounts have linked profiles and wallets.
- **Task 1.3: Crop Service Layer Extraction (`backend/services/crop_service.py`)**
  - *Owner:* Hasnain Hamza (Core Backend Engineer)
  - *Deliverable:* Extract pure business logic and queries from `crops.py` into `crop_service.py` (`auth.py` internals untouched).
  - *Definition of Done:* `backend/services/crop_service.py` operational; controller delegates to it; all 45 Increment 1 regression tests remain 100% green.
- **Task 1.4: Phase 1 Regression Certification**
  - *Owner:* Muhammad Hashir (QA & DevOps Engineer)
  - *Definition of Done:* Automated execution confirms `test_auth.py` (17/17), `test_crops_api.py` (23/23), and `test_frontend_contract.py` (5/5) pass with zero failures.

### Phase 2: Marketplace Catalog — Read Path (Days 4–6)
- **Task 2.1: Marketplace API Blueprint (`marketplace.py`, `marketplace_service.py`)**
  - *Owner:* Hasnain Hamza (Core Backend) & Iqra Fayaz (API Designer)
  - *Deliverable:* Implement `GET /api/marketplace/listings` with filtering, pagination, and anti-enumeration using the Increment 1 list envelope.
  - *Definition of Done:* Endpoint returns HTTP 200 with envelope `{ success: true, data: [...], page, limit, total }` and excludes unpriced or withdrawn listings.
- **Task 2.2: Buyer Dashboard Presentation Layer (`buyer_dashboard.html`, `buyer.js`, `buyer.css`)**
  - *Owner:* Manahil Zardad (UI/UX Designer)
  - *Deliverable:* Responsive procurement exchange interface in Terra × Terracotta design tokens.
  - *Definition of Done:* Conforms to `FRONTEND_CHANGE_CHECKLIST.md` with zero console errors, zero undefined CSS classes, and anti-FOUC guard.
- **Task 2.3: Marketplace Automated Test Harness (`test_marketplace_api.py`)**
  - *Owner:* Muhammad Hashir (QA & DevOps)
  - *Deliverable:* Test suite exercising public catalog filters, pagination, and RBAC visibility.
  - *Definition of Done:* `python backend/test_marketplace_api.py` passes 12/12 test cases.

### Phase 3: Orders, Digital Escrow & Wallet Simulation (Days 7–10)
- **Task 3.1: Digital Escrow Service & Controller (`orders.py`, `escrow_service.py`)**
  - *Owner:* Hasnain Hamza (Core Backend) & Bareera Noor (DBA)
  - *Deliverable:* Atomic checkout transaction: deduct buyer wallet, create order, lock escrow, mark listing `Sold`. Implement cancellation and dispute endpoints.
  - *Definition of Done:* Tested via unit calls; insufficient balance rejects with 400; double-spending blocked via `BEGIN IMMEDIATE`.
- **Task 3.2: Buyer Settlement & Quality Sign-Off**
  - *Owner:* Hasnain Hamza (Core Backend)
  - *Deliverable:* `POST /api/orders/<id>/confirm-delivery` invoking `release_escrow(order_id, 'buyer_confirmation')` and recording `orders.delivered_at`.
  - *Definition of Done:* Escrow funds transition to `RELEASED`; farmer wallet credited; order marked `Completed`.
- **Task 3.3: Escrow Checkout UI & Farmer Sales Tab**
  - *Owner:* Manahil Zardad (UI/UX)
  - *Deliverable:* Modal checkout in buyer console; inbound orders table in farmer dashboard with Rs currency formatting.
  - *Definition of Done:* End-to-end checkout, confirmation, and wallet updates verifiable in browser interface.
- **Task 3.4: Escrow & Orders Test Harness (`test_escrow_orders.py`)**
  - *Owner:* Muhammad Hashir (QA & DevOps)
  - *Deliverable:* Automated suite testing atomic checkout, insufficient funds rejection, double-spend prevention, cancellation, and settlement.
  - *Definition of Done:* `python backend/test_escrow_orders.py` passes 16/16 test cases.

### Phase 4: Telemetry Integration, Yield Engine & Final V&V Gate (Days 11–14)
- **Task 4.1: External Telemetry Client & SQLite Caching (`telemetry_service.py`, `telemetry.py`)**
  - *Owner:* Ameer Muawiyah (Lead Data Architect) & Hasnain Hamza (Backend)
  - *Deliverable:* OpenWeatherMap and SoilGrids fetchers with 6-hour SQLite caching and deterministic offline fallback fixtures.
  - *Definition of Done:* Cache hit verified on duplicate coordinate query; offline mode delivers valid data without internet.
- **Task 4.2: Algorithmic Predictive Yield Engine (`yield_service.py`, `yield.py`)**
  - *Owner:* Ameer Muawiyah (Lead Data Architect)
  - *Deliverable:* Pure Python mathematical model taking crop parameters and telemetry to output harvest date, tonnage, and confidence score.
  - *Definition of Done:* Deterministic formula output validated against agronomic test benchmarks across all 8 supported crops.
- **Task 4.3: Farmer Yield Prediction UI & Telemetry Badges**
  - *Owner:* Manahil Zardad (UI/UX)
  - *Deliverable:* Yield prediction modal and live environmental indicator displays.
  - *Definition of Done:* Farmer can click "Forecast Yield" and view calculated metrics and advice rendered within modal.
- **Task 4.4: Master V-Model Integration Sign-Off**
  - *Owner:* Ameer Muawiyah (Scrum Master) & Muhammad Hashir (QA Lead)
  - *Definition of Done:* Increment 1 regression suite (45/45) + Increment 2 suites (38+ tests) + extended contract suite (7/7) pass 100%. Sign off `INCREMENT_2_INTEGRATION_REPORT.md`.

---

## 10. Verification & Validation Strategy (V-Model Gate)

```
       REQUIREMENTS                           ACCEPTANCE TESTING
       (SRS / Inc 2 Plan)                     (Full System E2E)
             \                                      /
              \                                    /
               DESIGN                      INTEGRATION TESTING
         (Schema & API DDL)              (Escrow & Yield Suites)
                   \                            /
                    \                          /
                     IMPLEMENTATION     UNIT TESTING
                     (Flask / SQL) ──── (Service Tests)
```

### 10.1 Standing Invariant Rule
The 45 automated checks established in Increment 1 (`test_auth.py`, `test_crops_api.py`, `test_frontend_contract.py`) are **sacrosanct**. They must remain 100% green at every sprint boundary and commit milestone.

### 10.2 Automated Test Suites for Increment 2

1. **`backend/test_marketplace_api.py` (Target: 12 tests):**
   - Verifies catalog browsing, crop taxonomy filtering, price range bounds, and pagination.
   - Asserts that withdrawn (`is_deleted=1`) and non-active (`status != 'Active'`) crops are excluded from catalog.
   - Confirms anti-enumeration 404 behavior on single listing queries.
2. **`backend/test_escrow_orders.py` (Target: 16 tests):**
   - Verifies atomic checkout transaction across `orders`, `escrow_holdings`, `buyer_wallets`, and `listings`.
   - Tests insufficient funds rejection (HTTP 400).
   - Verifies double-ordering rejection (cannot buy an already sold listing).
   - Verifies order cancellation: refund to buyer wallet, listing status restored to `Active`.
   - Verifies dispute recording: funds frozen, no leak.
   - Verifies quality acceptance: escrow release via `release_escrow()`, farmer wallet credit, timestamping of `delivered_at`, and order state transition to `'Completed'`.
3. **`backend/test_yield_telemetry.py` (Target: 10 tests):**
   - Pure offline verification of `yield_service.py` using recorded environmental fixtures.
   - Tests telemetry database caching: verifies second call within 6-hour TTL reads from SQLite without triggering HTTP requests.
   - Verifies graceful fallback when API credentials are dummy or network is unreachable.
4. **`backend/test_frontend_contract.py` (Extended to 7 tests):**
   - `TC-F1`: Extended with runtime assertion that `GET /api/meta/taxonomies` crops array equals `VALID_CROP_NAMES`.
   - `TC-F2`: Extended with runtime assertion that `GET /api/meta/taxonomies` statuses array equals `VALID_STATUSES`.
   - `TC-F3`: Class cross-check for all defined CSS rules.
   - `TC-F4`: ID cross-check for all JS `getElementById` calls.
   - `TC-F5`: Pinned SRS copy validation.
   - `TC-F6 (New)`: Buyer dashboard DOM element ID and CSS class cross-check.
   - `TC-F7 (New)`: Scans all `document.querySelector` and `document.querySelectorAll` string literals across JS files to verify targets exist in HTML/CSS.

### 10.3 Offline External API Testing Doctrine
- **Zero Live Network Calls in CI/CD:** No automated test suite may ping real external API endpoints.
- **Fixture Mocks:** Telemetry clients inspect `os.environ.get("AGRIGRID_OFFLINE_MODE")`. When set (or when API keys are default placeholders), clients return standardized JSON fixtures stored in `backend/tests/fixtures/`.

---

## 11. Risk Analysis & Mitigation Engineering

| Risk ID | Risk Description | Severity | Probability | Technical Mitigation Strategy |
|---|---|:---:|:---:|---|
| **RSK-01** | **Escrow State Corruption & Double-Spending:** Concurrent buyers attempt to purchase the same listing simultaneously. | High | Medium | Execute checkout inside an explicit SQLite `BEGIN IMMEDIATE` transaction. Validate listing status equals `'Active'` within the locked transaction; update status to `'Sold'` atomically before releasing lock. |
| **RSK-02** | **External API Quota Exhaustion & Cost:** Free tier limits (e.g. 1,000 calls/day on weather APIs) exceeded during testing. | High | High | Implement mandatory SQLite caching table (`telemetry_cache`) with a strict 6-hour TTL. Require automated test suites to run in offline mock mode. |
| **RSK-03** | **Database Migration Failure on Existing Installs:** Migration script fails on existing team SQLite databases, locking schema. | Medium | Low | All DDL statements executed statement-by-statement inside `BEGIN IMMEDIATE` / `COMMIT` blocks (no `executescript`). Checksum column in `schema_versions` enforces script immutability. |
| **RSK-04** | **Scope Creep into Logistics & Telemedicine:** Team members attempt to implement real GPS tracking or agronomist tickets in Increment 2. | High | Medium | Scrum Master strictly enforces Increment 2 boundary. Transporter, Agronomist, and Compliance routes remain locked behind HTTP 403 / under-construction placeholders. |
| **RSK-05** | **Frontend Token & Design Drift:** New buyer pages introduce framework classes (Bootstrap/Tailwind) or deviate from design tokens. | Medium | Low | Mandatory execution of `FRONTEND_CHANGE_CHECKLIST.md` and automated CSS cross-check (`test_frontend_contract.py`) blocking pull requests. |

---

## 12. Future-Increment Readiness & Architectural Seams

Increment 2 intentionally designs foundational hooks for future increments without building them:

1. **Seam for Increment 3 (Logistics & Transporter):**
   - The `orders` table explicitly includes `destination_warehouse`, `max_temperature_celsius`, `delivered_at`, and status `'Escrow_Funded'`.
   - In Increment 3, when a transporter scans the QR code at the farm, the system will bind `orders.id` directly to a new `deliveries` manifest row and transition `order_status` to `'In_Transit'`.
2. **Seam for Increment 4 (Agronomist & Compliance):**
   - The `telemetry_cache` table stores structured soil and weather metrics that the Agronomist Diagnostic Workbench will query in Increment 4 to provide environmental context alongside crop photos.
   - The `escrow_holdings` ledger provides an immutable audit trail for the Compliance Officer's financial verification engine.
   - The `order_status = 'Disputed'` state provides the entry point for Compliance Officer dispute resolution.
3. **Seam for Increment 5 (Consumer QR Storyboard):**
   - The `batch_id` generated on listing publication becomes the physical identifier encoded in the retail QR code.
   - The relationship `listings` $\rightarrow$ `orders` $\rightarrow$ `escrow_holdings` ensures that when a consumer scans a batch in Increment 5, the system can traverse backwards to display origin farm coordinates and harvest timestamps.

---

## 13. Scrum Master Decision List

### Status: DECIDED — Approved by the Scrum Master on 2026-11-13

All six decisions have been formally approved as recommended, with one clarification on Decision 3 regarding the future auto-release architectural seam:

---

### Decision 1: Whole-Listing vs. Partial-Quantity Purchasing
- **Status:** **APPROVED — Option A (Whole-Listing Only).**
- **Decision:** A buyer must purchase the entire listing in a single transaction. The listing transitions from `Active` $\rightarrow$ `Sold` atomically. Zero state fragmentation or inventory race conditions.
- **Architectural Seam:** Farmers wishing to sell smaller batches can register multiple separate plot listings in the farmer console.

---

### Decision 2: Pricing Requirement & Unpriced Legacy Listings
- **Status:** **APPROVED — Option A (Strict Commercial Gating).**
- **Decision:** Only listings with `asking_price_per_kg IS NOT NULL` and `asking_price_per_kg > 0` are displayed in the B2B marketplace. Farmers must use `"Edit Crop"` to set a price before a crop becomes purchasable.
- **Seed Action:** `init_db.py` is updated to assign default prices (Rs. 45.00/kg for Wheat, Rs. 80.00/kg for Tomato).

---

### Decision 3: Escrow Settlement Release Triggers & Auto-Release Seam
- **Status:** **APPROVED — Option A with Architectural Seam (Scrum Master Clarification).**
- **Decision:** Buyer manual confirmation (`POST /api/orders/<id>/confirm-delivery`) is the active Increment 2 settlement mechanism.
- **Architectural Seam (Zero-Rewrite Guarantee):** To guarantee that auto-release can be activated in the future with **no schema migration and no escrow-service rewrite**, Increment 2 builds the following hooks now:
  1. `orders` table gains nullable `delivered_at TEXT` (set upon delivery confirmation).
  2. `escrow_holdings` gains nullable `auto_release_at TEXT` (populated as `delivered_at + 72h` upon delivery confirmation; unused by Increment 2 code paths).
  3. `escrow_service.py` implements `release_escrow(order_id, trigger)` where `trigger ∈ {'buyer_confirmation', 'auto_timeout', 'admin'}`. Increment 2 calls it exclusively with `'buyer_confirmation'`. The trigger value is recorded in `escrow_holdings.release_tx_ref`.

---

### Decision 4: External Telemetry API Keys & Offline Fallback Strategy
- **Status:** **APPROVED — Option B (Graceful Degradation with Deterministic Mock Fallbacks).**
- **Decision:** If API keys are present in environment variables, the system pings external APIs and caches payloads in SQLite with a 6-hour TTL. If keys are missing or network calls fail, the service seamlessly serves high-fidelity deterministic fixtures from `backend/tests/fixtures/`.
- **Testing Doctrine:** Automated test suites run strictly offline using mock fixtures.

---

### Decision 5: Predictive Yield Engine Mathematical Model & Presentation
- **Status:** **APPROVED — Option B (Agronomic Algorithmic Formula Core).**
- **Decision:** A pure Python deterministic formula combining baseline crop yields, growing degree days elapsed, rainfall deviation factors, and soil moisture stress coefficients. Fast, explainable, lightweight, and offline-testable.

---

### Decision 6: Self-Service Password Recovery Disposition
- **Status:** **APPROVED — Option B (Formally Defer to Increment 4).**
- **Decision:** Building full SMTP infrastructure is deferred to Increment 4 (Administration & Governance).
- **UI Update:** The copy in `frontend/index.html` is updated to state: *"Self-service recovery scheduled for Increment 4 — Contact admin for access."*

---
*End of Master Architecture & Execution Plan for Increment 2.*  
**Status:** Approved by the Scrum Master on 2026-11-13, subject to the v1.1 amendments (A1–A10).
