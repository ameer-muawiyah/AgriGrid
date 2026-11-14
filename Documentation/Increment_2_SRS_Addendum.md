# Software Requirements Specification (SRS) Addendum
## Increment 2: Core Data Engine & Demand Side (B2B Marketplace, Escrow & Predictive Yield)

| Field | Value |
|---|---|
| **Project Name** | Agri-Grid: Smart Agriculture & Food Security Ecosystem |
| **Document ID** | `AG-SRS-INC2-001` |
| **Version** | 1.2 (SRS Addendum — Pre-Sequence Diagram Baseline Pass) |
| **Prepared By** | Manahil Sohail (Requirements Engineer — RE Track Lead) |
| **Reviewed By** | Ameer Muawiyah (Scrum Master + Lead Data Architect) |
| **Date** | 2026-11-14 |
| **Governing Document** | Increment 2 Master Plan v1.1 (`AG-PLAN-INC2-001`, approved 2026-11-13) |
| **Baseline Reference** | Increment 1 SRS (`AG-SRS-INC1-001 v1.1`), API Contracts (`AG-API-INC1-003 v1.0`) |
| **Location** | `./Documentation/Increment_2_SRS_Addendum.md` |

---

## Table of Contents

1. [Introduction & Governing Context](#1-introduction--governing-context)
   - 1.1 Purpose & Scope Boundary
   - 1.2 Document Conventions & Requirement Prefixes
   - 1.3 Intended Audience
   - 1.4 References & Source Document Hierarchy
   - 1.5 Baseline Confirmation & Invariant Rules
2. [Overall System Evolution & Architectural Delta](#2-overall-system-evolution--architectural-delta)
   - 2.1 System Context Evolution
   - 2.2 System Actors Status in Increment 2
   - 2.3 Explicit Out-of-Scope Specifications
   - 2.4 Architectural Seams for Future Increments (Increments 3, 4, 5)
3. [Module 1: Infrastructure & Service Layer Requirements](#3-module-1-infrastructure--service-layer-requirements)
   - 3.1 Database Migration Engine (`FR-MIG-XXX`, FEAT-INC2-10)
   - 3.2 Service Layer Extraction Boundary (`FR-SRV-XXX`, FEAT-INC2-11)
4. [Module 2: B2B Marketplace & Commercial Listing Requirements](#4-module-2-b2b-marketplace--commercial-listing-requirements)
   - 4.1 Buyer Profile Onboarding & Authentication (`FR-BYR-XXX`, FEAT-INC2-02)
   - 4.2 Farmer Commercial Pricing & Batching (`FR-PRC-XXX`, FEAT-INC2-05)
   - 4.3 B2B Procurement Catalog & Filtering (`FR-MKT-XXX`, FEAT-INC2-01)
5. [Module 3: Digital Escrow & Financial Settlement Requirements](#5-module-3-digital-escrow--financial-settlement-requirements)
   - 5.1 Simulated Multi-Party Wallets (`FR-WLT-XXX`, FEAT-INC2-06)
   - 5.2 Escrow Checkout & Funds Locking (`FR-ORD-XXX`, FEAT-INC2-03)
   - 5.3 Quality Acceptance & Settlement (`FR-SET-XXX`, FEAT-INC2-04)
   - 5.4 Global Status State Machine & Transition Rules (`FR-STM-XXX`, FEAT-INC2-12)
6. [Module 4: Environmental Telemetry & Predictive Intelligence Requirements](#6-module-4-environmental-telemetry--predictive-intelligence-requirements)
   - 6.1 External Weather & Soil Telemetry Client (`FR-TEL-XXX`, FEAT-INC2-07)
   - 6.2 Telemetry Database Caching Engine (`FR-CCH-XXX`, FEAT-INC2-08)
   - 6.3 Algorithmic Predictive Yield Engine (`FR-YLD-XXX`, FEAT-INC2-09)
7. [Module 5: System Taxonomies & Contract Extensions](#7-module-5-system-taxonomies--contract-extensions)
   - 7.1 Taxonomy Vocabularies & Client Dropdown Bindings (`FR-TAX-XXX`)
8. [Non-Functional Requirements (NFRs)](#8-non-functional-requirements-nfrs)
   - 8.1 Performance & Scalability (`NFR-PERF-XXX`)
   - 8.2 Security, Multi-Tenancy & Integrity (`NFR-SEC-XXX`)
   - 8.3 Reliability, Offline Degradation & Availability (`NFR-REL-XXX`)
   - 8.4 Usability & Human-Computer Interface (`NFR-USE-XXX`)
9. [Complete Traceability Matrix](#9-complete-traceability-matrix)
10. [Scrum Master Decision List (Determinations Recorded)](#10-scrum-master-decision-list-determinations-recorded)
11. [Discrepancy & Finding Report (Plan vs. Docs vs. Code)](#11-discrepancy--finding-report-plan-vs-docs-vs-code)
12. [Revision History & V&V Approval Block](#12-revision-history--vv-approval-block)

---

## 1. Introduction & Governing Context

### 1.1 Purpose & Scope Boundary
This document is the formal **Software Requirements Specification (SRS) Addendum** for **Increment 2** of the Agri-Grid Smart Agriculture & Food Security Ecosystem. It strictly adheres to IEEE 830 / ISO/IEC/IEEE 29148 standards, extending the certified Increment 1 SRS (`AG-SRS-INC1-001 v1.1`) rather than restating it.

Increment 2 establishes the **Demand Side** (B2B wholesale marketplace), the **Financial Integrity Layer** (digital escrow ordering and simulated multi-party wallets), and the **Analytical Core** (environmental telemetry caching and the algorithmic Predictive Yield Engine).

### 1.2 Document Conventions & Requirement Prefixes
Requirements in this addendum utilize standard RFC 2119 keyword semantics:
- **SHALL**: Absolute, mandatory system requirement.
- **SHOULD**: Strongly recommended engineering standard / target; deviation requires written Scrum Master approval.
- **MAY**: Permissible architectural extension.

Requirement identifiers follow the Increment 1 modular taxonomy:
- `FR-MIG-XXX`: Database Migration Engine (FEAT-INC2-10)
- `FR-SRV-XXX`: Service Layer Extraction Architecture (FEAT-INC2-11)
- `FR-BYR-XXX`: Buyer Onboarding & Profile Management (FEAT-INC2-02)
- `FR-PRC-XXX`: Commercial Pricing & Batch Publication (FEAT-INC2-05)
- `FR-MKT-XXX`: B2B Procurement Catalog & Search (FEAT-INC2-01)
- `FR-ORD-XXX`: Digital Escrow Ordering & Checkout (FEAT-INC2-03)
- `FR-WLT-XXX`: Simulated Multi-Party Wallets (FEAT-INC2-06)
- `FR-SET-XXX`: Buyer Quality Acceptance & Settlement (FEAT-INC2-04)
- `FR-STM-XXX`: Global Status State Machine & Invariants (FEAT-INC2-12)
- `FR-TEL-XXX`: External Weather & Soil Telemetry Client (FEAT-INC2-07)
- `FR-CCH-XXX`: Telemetry Database Caching Engine (FEAT-INC2-08)
- `FR-YLD-XXX`: Algorithmic Predictive Yield Engine (FEAT-INC2-09)
- `FR-TAX-XXX`: Taxonomies & Contract Extensions (Backlog Cleanups)
- `NFR-XXX`: Non-Functional Requirements (Performance, Security, Reliability, Usability)

### 1.3 Intended Audience
- **Scrum Master & Lead Data Architect (Ameer Muawiyah)**: Review baseline alignment, verify state machine transitions, and decide open technical choices.
- **Core Backend Engineer (Hasnain Hamza)**: Implement service layer abstractions, REST controllers, and atomic transactions.
- **Database Administrator (Bareera Noor)**: Author SQL migrations (`001`, `002`), migration runner, and table indices.
- **UI/UX Designer (Manahil Zardad)**: Implement buyer dashboard (`buyer_dashboard.html`), checkout modals, and farmer pricing controls.
- **API Designer (Iqra Fayaz)**: Validate request/response JSON schemas against contracts.
- **QA & DevOps Engineer (Muhammad Hashir)**: Author unit, integration, and contract regression tests.

### 1.4 References & Source Document Hierarchy
In case of ambiguity, precedence is resolved strictly in the following order:
1. `0_Increment_2_Master_Plan.md` (`AG-PLAN-INC2-001 v1.1`) — Governing Execution Plan.
2. `This Document` (`AG-SRS-INC2-001 v1.1`) — Detailed Requirements Specification.
3. Master Documents 1–7 in `./Documentation/` — Immutable Foundation.
4. Increment 1 Artifacts (`AG-SRS-INC1-001 v1.1`, `AG-API-INC1-003 v1.0`, `2_Farmer_Sequence_Diagrams.md v1.1`).
5. `FRONTEND_CHANGE_CHECKLIST.md` — UI/UX Design Token and DOM Integrity Standard.

### 1.5 Baseline Confirmation & Invariant Rules
1. **Sacrosanct Regression Baseline**: Increment 1 closed with **45/45 tests passing** (17 auth, 23 crops, 5 frontend contract). All 45 tests SHALL remain 100% green without modification.
2. **Canonical Database Anchor**: Exactly one database file exists: `backend/database/agrigrid.db`. Direct creation of stray database files is prohibited.
3. **Currency Standard**: All currency representations SHALL use **Pakistani Rupee (`Rs.` / `PKR`)**. The Increment 1 presentation dollar (`$`) symbol is superseded.
4. **Zero-Trust Identity**: `farmer_id` and `buyer_id` SHALL be extracted exclusively from the cryptographically verified JWT (`Authorization: Bearer <token>`). Never accepted from request bodies or URL parameters.

---

## 2. Overall System Evolution & Architectural Delta

### 2.1 System Context Evolution
Increment 1 delivered a single active actor (**Farmer**) and internal ledger operations. Increment 2 activates the **Demand Side** of the commercial supply chain by onboarding wholesale **B2B Buyers**, providing public catalog discovery, locking purchase commitments in a simulated digital escrow, and executing settlement upon delivery sign-off. Simultaneously, it embeds predictive intelligence by querying hyper-local soil and meteorological telemetry.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   INCREMENT 2 EXTENDED SYSTEM BOUNDARY                 │
├────────────────────────┬───────────────────────────────────────────────┤
│ Active Actors          │ Farmer, B2B Buyer                             │
├────────────────────────┼───────────────────────────────────────────────┤
│ Provisioned Actors     │ Transporter (Inc 3), Agronomist (Inc 4),      │
│ (RBAC Placeholder)     │ Compliance Officer (Inc 4)                    │
├────────────────────────┼───────────────────────────────────────────────┤
│ Unauthenticated Public │ Public Consumer (Inc 5 QR scan only)          │
├────────────────────────┼───────────────────────────────────────────────┤
│ External Integrations  │ OpenWeatherMap API, SoilGrids REST API        │
│                        │ (Guarded by 6-hour SQLite cache + fixtures)   │
└────────────────────────┴───────────────────────────────────────────────┘
```

### 2.2 System Actors Status in Increment 2

| # | Actor | Increment 1 Status | Increment 2 Status | Permitted Operational Capabilities in Increment 2 |
|---|---|---|---|---|
| 1 | **Farmer** | ✅ Active | ✅ Active (Enhanced) | Full CRUD on own crops; commercial pricing & batching; view incoming escrow orders; trigger yield forecasts. |
| 2 | **B2B Buyer** | 🔒 Placeholder | ✅ **Active (Activated)** | Register profile; browse public marketplace; place escrow orders; cancel orders; confirm delivery & release escrow; flag disputes. |
| 3 | **Transporter** | 🔒 Placeholder | 🔒 Placeholder (Inc 3) | HTTP 403 Forbidden on all business routes. Receives verified under-construction screen. |
| 4 | **Agronomist** | 🔒 Placeholder | 🔒 Placeholder (Inc 4) | HTTP 403 Forbidden on all business routes. Receives verified under-construction screen. |
| 5 | **Compliance Officer** | 🔒 Placeholder | 🔒 Placeholder (Inc 4) | HTTP 403 Forbidden on all business routes. Receives verified under-construction screen. |
| 6 | **Public Consumer** | 🔒 Not Implemented | 🔒 Not Implemented (Inc 5) | Unauthenticated public catalog read not yet exposed to consumer QR storyboard. |

### 2.3 Explicit Out-of-Scope Specifications
The following capabilities are explicitly deferred and SHALL NOT be implemented in Increment 2:
1. **Transporter Logistics & In-Transit Tracking (Increment 3)**: QR camera scan handshakes, dispatch manifests, GPS breadcrumb streaming, truck temperature telemetry logging, mobile flash caching.
2. **Agronomist Diagnostics & Telemedicine (Increment 4)**: Image upload queues, diagnostic ticketing, split-screen expert workbenches, prescription authoring, regional pest outbreak heatmaps.
3. **Compliance & Grant Auditing (Increment 4)**: Government subsidy requests, automated satellite cross-checking confidence scoring, grant disbursements, carbon credit ledgers.
4. **Consumer QR Provenance Storyboard (Increment 5)**: Public consumer landing page, farm-to-table vertical timeline, dynamic QR code generation.
5. **Real-Money Payment Gateways**: Stripe, JazzCash, EasyPaisa, bank wire rails are excluded. Financial settlement is strictly simulated via internal ACID-compliant ledger tables (`buyer_wallets`, `farmer_wallets`, `escrow_holdings`).
6. **Dispute Resolution & Arbitration Workflow**: While buyers and farmers can flag an order as disputed (`POST /api/orders/<id>/dispute`), **no dispute-resolution endpoint or administrative arbitration workflow exists in Increment 2**. Adjudication and escrow unfreezing are formal Increment 4 (Compliance Officer) capabilities.
7. **Self-Service Password Recovery ("Forgot Password")**: Formally deferred to Increment 4 per Scrum Master Decision 6. The login UI copy in `frontend/index.html` SHALL be updated to state: *"Self-service recovery scheduled for Increment 4 — Contact admin for access."*

### 2.4 Architectural Seams for Future Increments
To prevent breaking changes and structural rewrites in future stages, Increment 2 establishes the following explicit architectural seams:
- **Increment 3 Seam (Logistics)**: `orders` table defines `destination_warehouse`, `max_temperature_celsius`, and status `'Escrow_Funded'`. When the Transporter module activates in Increment 3, the dispatch handshake will bind to `orders.id` and advance status to `'In_Transit'` without altering the buyer confirmation contract.
- **Increment 4 Seam (Escrow Auto-Release & Compliance)**:
  1. `orders.delivered_at` records physical delivery timestamp.
  2. `escrow_holdings.auto_release_at` records `delivered_at + 72 hours` upon delivery confirmation (populated, but untouched by Increment 2 code).
  3. `escrow_service.py` implements `release_escrow(order_id, trigger)` where `trigger ∈ {'buyer_confirmation', 'auto_timeout', 'admin'}`. Increment 2 calls it strictly with `'buyer_confirmation'`.
  4. `orders.order_status = 'Disputed'` provides the entry hook for Compliance Officer arbitration.
- **Increment 5 Seam (Consumer QR Storyboard)**: `listings.batch_id` serves as the unique identifier that will be encoded into consumer-facing QR codes in Increment 5.

---

## 3. Module 1: Infrastructure & Service Layer Requirements

### 3.1 Database Migration Engine (`FR-MIG-XXX`, FEAT-INC2-10)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-MIG-001** | The system SHALL implement an automated database migration runner (`backend/database/migrate.py`) that applies incremental SQL schema scripts without destroying existing data. | SHALL | Plan §4.1, §9 Task 1.1 | `python backend/database/migrate.py` applies pending migrations cleanly on clean or populated DB. |
| **FR-MIG-002** | The migration engine SHALL maintain a dedicated version tracking table named `schema_versions` recording: `id` (INTEGER PK AUTOINCREMENT), `version` (INTEGER UNIQUE), `script_name` (TEXT), `checksum` (TEXT SHA-256 hex digest), and `applied_at` (TEXT ISO-8601). | SHALL | Plan §4.1.1 | SQL Query: `SELECT * FROM schema_versions WHERE version = 2;` verifies schema structure. |
| **FR-MIG-003** | The migration runner SHALL baseline the existing Increment 1 schema into `001_increment_1_baseline.sql` and execute Increment 2 schema expansions via `002_increment_2_marketplace_escrow_telemetry.sql`. | SHALL | Plan §4.1.1, §5 | Migration directory scan verifies both files exist and are numbered sequentially. |
| **FR-MIG-004** | The migration runner SHALL split SQL migration scripts into individual statements and execute them statement-by-statement inside an explicit transaction (`BEGIN IMMEDIATE` ... `COMMIT`). The runner SHALL NOT use `sqlite3.executescript()`, guaranteeing that any failure triggers an immediate `ROLLBACK`. | SHALL | Plan §4.1.2 | Unit test: Inject invalid SQL syntax into mock migration; assert rollback and unchanged `schema_versions`. |
| **FR-MIG-005** | On every execution, the migration runner SHALL compute the SHA-256 checksum of every previously applied migration file and compare it against the recorded checksum in `schema_versions`. If any applied file was modified, the runner SHALL halt with an error and refuse to proceed. | SHALL | Plan §4.1.3 | Unit test: Mutate 1 byte of `001_increment_1_baseline.sql`; run `migrate.py`; assert loud failure and non-zero exit code. |
| **FR-MIG-006** | System startup scripts (`launch_agrigrid.py`) SHALL invoke `backend/database/migrate.py` automatically before starting backend or frontend servers. | SHALL | Plan §4.1.4 | E2E launcher test: Running `launch_agrigrid.py` on an unmigrated database migrates to v2 prior to port binding. |
| **FR-MIG-007** | During Flask application factory initialization (`backend/app.py`), the backend SHALL perform a lightweight read-only query against `schema_versions`. If the latest applied version is less than the codebase requirement (`version = 2`), the application SHALL refuse to start and log the exact command: `python backend/database/migrate.py`. | SHALL | Plan §4.1.4 | Execution check: start the app against a v1 database; assert non-zero exit and the remediation command in the output. |

### 3.2 Service Layer Extraction Boundary (`FR-SRV-XXX`, FEAT-INC2-11)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-SRV-001** | The backend architecture SHALL extract all raw SQL queries, transaction management, and database cursor manipulations from HTTP controllers (`crops.py`, `marketplace.py`, `orders.py`, `telemetry.py`, `yield.py`) into a dedicated service layer located in `backend/services/`. | SHALL | Plan §4.2, §9 Task 1.3 | Code review: grep confirms no SQL statements remain in `crops.py` route bodies; all queries reside in `crop_service.py`. |
| **FR-SRV-002** | The constants `VALID_CROP_NAMES`, `VALID_STATUSES` and the validation helper function `_validate_crop_payload()` SHALL strictly remain inside `backend/crops.py` to preserve AST contract compatibility with `test_frontend_contract.py`. | SHALL | Plan §4.2 Refinement | `python backend/test_frontend_contract.py` executes and passes `TC-F1` and `TC-F2` AST parsing. |
| **FR-SRV-003** | The extracted crop operations service (`backend/services/crop_service.py`) SHALL handle all listing database operations and return pure Python dictionaries or primitive values to the controller. | SHALL | Plan §4.2 | Controller `crops.py` delegates CRUD operations to `crop_service.py` functions and maps results to `jsonify()`. |
| **FR-SRV-004** | The service layer extraction refactoring SHALL preserve 100% backward compatibility: all 45 Increment 1 automated tests (`test_auth.py`, `test_crops_api.py`, `test_frontend_contract.py`) SHALL pass with zero test modifications. | SHALL | Plan §4.2.4, §10.1 | Automated test runner execution: `python backend/test_auth.py` (17/17), `python backend/test_crops_api.py` (23/23), `python backend/test_frontend_contract.py` (5/5) pass with zero failures. |

---

## 4. Module 2: B2B Marketplace & Commercial Listing Requirements

### 4.1 Buyer Profile Onboarding & Authentication (`FR-BYR-XXX`, FEAT-INC2-02)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-BYR-001** | The user registration endpoint (`POST /api/auth/register`) SHALL accept registration requests with `role = 'buyer'`. | SHALL | Plan §2.1, §6.4 | `test_marketplace_api.py::TC-BYR-01`: Register user with role buyer returns HTTP 201. |
| **FR-BYR-002** | When `role = 'buyer'`, the registration payload SHALL require the following additional fields: `company_name` (string, 2–100 characters), `contact_phone` (string, 7–20 characters), and `warehouse_address` (string, minimum 5 characters). Optional fields: `warehouse_gps_latitude` (-90.0 to 90.0) and `warehouse_gps_longitude` (-180.0 to 180.0). | SHALL | Plan §5.2, §6.4 | `test_marketplace_api.py::TC-BYR-02`: Submit buyer registration omitting `company_name`; assert HTTP 400 Bad Request. |
| **FR-BYR-003** | Upon valid buyer registration, the backend SHALL atomically execute the following actions within a single database transaction: (1) insert record into `users` table; (2) insert record into `buyers` table with user foreign key; (3) insert record into `buyer_wallets` table initialized with balance `500000.00` PKR (`SIMULATED_BUYER_STARTING_BALANCE_PKR`). | SHALL | Plan §5.2, §6.4 | Database inspection verifies linked rows in `users`, `buyers`, and `buyer_wallets` with 500,000.00 balance. |
| **FR-BYR-004** | If any constraint validation or SQL insert fails during buyer registration, the entire transaction SHALL roll back immediately, leaving no orphaned user or wallet records, and return HTTP 400 with a descriptive error message. | SHALL | Plan §6.4 | Unit test: Force duplicate company error or constraint fail; verify `users` table count is unchanged. |
| **FR-BYR-005** | Upon successful login (`POST /api/auth/login`) with buyer credentials, the backend SHALL return a signed JWT carrying claims: `user_id`, `role = 'buyer'`, `farmer_id = null`, and `exp`. The response body SHALL include user object and buyer profile metadata. | SHALL | Plan §3.1, §6.4 | `test_auth.py` extension: Login `sara_buyer`; decode JWT; assert `role == 'buyer'` and `farmer_id is None`. |
| **FR-BYR-006** | The database bootstrap path — `backend/database/init_db.py` plus migration 002's idempotent seed section — SHALL provision the default test buyer `sara_buyer` (`BuyerPass1`) with an associated `buyers` profile row (`company_name = 'Metro Wholesale Foods'`, `contact_phone = '+92-300-1234567'`, `warehouse_address = 'Metro Central Hub, Lahore'`) and a `buyer_wallets` row with `balance_pkr = 500000.00`. | SHALL | Plan §9 Task 1.2, Phase 1 Build Spec | Database query on bootstrap: `SELECT balance_pkr FROM buyer_wallets WHERE buyer_id = (SELECT id FROM buyers WHERE user_id = (SELECT id FROM users WHERE username = 'sara_buyer'))` returns 500000.00. |

### 4.2 Farmer Commercial Pricing & Batch Publication (`FR-PRC-XXX`, FEAT-INC2-05)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-PRC-001** | The database `listings` table SHALL be altered via migration 002 to add `asking_price_per_kg REAL CHECK(asking_price_per_kg IS NULL OR asking_price_per_kg > 0)` and `batch_id TEXT`. Uniqueness of `batch_id` SHALL be enforced via companion statement `CREATE UNIQUE INDEX IF NOT EXISTS idx_listings_batch_id ON listings(batch_id)` to satisfy SQLite 3 `ALTER TABLE` constraint restrictions. | SHALL | Plan §1.2, §5.1 | `sqlite3 agrigrid.db ".schema listings"` and index check verify column and unique index exist. |
| **FR-PRC-002** | The farmer crop creation (`POST /api/crops`) and update (`PUT /api/crops/<id>`) endpoints SHALL accept an optional `asking_price_per_kg` numeric field. If provided, the value SHALL be strictly greater than 0.00 PKR; otherwise, the endpoint SHALL return HTTP 400. | SHALL | Plan §6.4 | `test_crops_api.py::TC-PRC-01`: PUT with `asking_price_per_kg = -5.0` returns HTTP 400. |
| **FR-PRC-003** | When a farmer sets a valid `asking_price_per_kg` on a listing that does not yet possess a `batch_id`, the backend SHALL automatically generate and assign a unique `batch_id` formatted according to the template `BATCH-{YEAR}-{CROP_CODE3}-{LISTING_ID:04d}` (e.g., `BATCH-2026-WHT-0001`). The 3-letter uppercase crop code SHALL be mapped from `crop_name` via the authoritative taxonomy table: Wheat $\rightarrow$ `WHT`, Rice $\rightarrow$ `RIC`, Tomato $\rightarrow$ `TOM`, Potato $\rightarrow$ `POT`, Cotton $\rightarrow$ `COT`, Maize $\rightarrow$ `MAI`, Sugarcane $\rightarrow$ `SUG`, Other $\rightarrow$ `OTH`. | SHALL | Plan §5.1, §12.3, Scrum Master Determination D-INC2-08 | API test: Update crop with price; verify returned listing payload contains valid formatted `batch_id` matching `BATCH-{YEAR}-{CROP_CODE3}-{LISTING_ID:04d}`. |
| **FR-PRC-004** | The farmer dashboard presentation layer (`frontend/dashboard.html` and `dashboard.js`) SHALL enable the Asking Price input field (removing the disabled state and `<span class="inc2-badge">Inc 2</span>` badge) and display prices in `Rs. / kg`. | SHALL | Plan §7.2 | Manual UI verification: Modal input accepts price; table renders `Rs. 45.00 / kg` without console errors. |
| **FR-PRC-005** | The database bootstrap path — `backend/database/init_db.py` plus migration 002's idempotent seed section — SHALL provision default commercial prices for `tahir_farmer` listings: Rs. 45.00/kg for Wheat and Rs. 80.00/kg for Tomato, with valid generated `batch_id` values. | SHALL | Plan §13 Decision 2, Phase 1 Build Spec | `SELECT asking_price_per_kg, batch_id FROM listings;` returns valid prices and batch strings for seed rows. |

### 4.3 B2B Procurement Catalog & Filtering (`FR-MKT-XXX`, FEAT-INC2-01)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-MKT-001** | The system SHALL expose an authenticated public procurement catalog endpoint: `GET /api/marketplace/listings`, accessible by users holding roles `buyer` or `farmer`. | SHALL | Plan §6.1, §8 | `test_marketplace_api.py::TC-MKT-01`: Authorized buyer retrieves catalog returning HTTP 200. |
| **FR-MKT-002** | The catalog query SHALL strictly filter for listings meeting all three conditions: `status = 'Active'`, `is_deleted = 0`, and `asking_price_per_kg IS NOT NULL AND asking_price_per_kg > 0`. Soft-deleted, withdrawn, sold, or unpriced crops SHALL NEVER appear in catalog results. | SHALL | Plan §6.1, §13 Decision 2 | `test_marketplace_api.py::TC-MKT-02`: Verify unpriced and soft-deleted listings are absent from result set. |
| **FR-MKT-003** | The endpoint SHALL support the following optional query parameters for filtering and sorting: `crop_name` (string taxonomy match), `max_price` (numeric maximum asking price per kg), `page` (integer, default 1), `limit` (integer, default 20), and `sort` (`price_asc`, `price_desc`, `date_desc`). | SHALL | Plan §6.1 | `test_marketplace_api.py::TC-MKT-03`: Query with `?crop_name=Wheat&max_price=50` returns filtered subset. |
| **FR-MKT-004** | The catalog response SHALL adhere strictly to the established Increment 1 flat list envelope: `{ "success": true, "data": [ ... ], "page": 1, "limit": 20, "total": N }`. | SHALL | Plan §6 universal rule | Contract test assertion: Response JSON keys match exact set `{"success", "data", "page", "limit", "total"}`. |
| **FR-MKT-005** | Each catalog listing item in the response `data` array SHALL contain: `listing_id`, `batch_id`, `crop_name`, `quantity_kg`, `asking_price_per_kg`, `total_price_pkr` (`quantity_kg * asking_price_per_kg`), `estimated_harvest_date`, `farm_name`, `farm_location`, `gps_latitude`, and `gps_longitude`. | SHALL | Plan §6.1 | Unit test verifies serialized dictionary keys and calculation of `total_price_pkr`. |
| **FR-MKT-006** | The system SHALL expose a single listing detail endpoint: `GET /api/marketplace/listings/<id>`, accessible by authenticated buyers and farmers. | SHALL | Plan §6.1 | `test_marketplace_api.py::TC-MKT-04`: Query valid listing ID returns HTTP 200 with full details. |
| **FR-MKT-007** | If a requested listing ID in `GET /api/marketplace/listings/<id>` does not exist, has `is_deleted = 1`, or has `status != 'Active'`, the endpoint SHALL return a unified `HTTP 404 Not Found` with `{"success": false, "error": "Listing not found."}`, preventing status enumeration. Note: The error string `"Listing not found."` differs deliberately from Increment 1's crop endpoint string `"Crop listing not found."` because the marketplace is a new procurement surface; this exact string is to be formally confirmed in the API Contracts Delta (`AG-API-INC2-003`, RE Track Prompt 3). | SHALL | Plan §6.1 | `test_marketplace_api.py::TC-MKT-05`: Query ID of sold or withdrawn listing returns HTTP 404. |

---

## 5. Module 3: Digital Escrow & Financial Settlement Requirements

### 5.1 Simulated Multi-Party Wallets (`FR-WLT-XXX`, FEAT-INC2-06)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-WLT-001** | The database SHALL maintain two dedicated virtual ledger tables created via migration 002: `buyer_wallets` (`id`, `buyer_id UNIQUE`, `balance_pkr >= 0`, `updated_at`) and `farmer_wallets` (`id`, `farmer_id UNIQUE`, `balance_pkr >= 0`, `updated_at`). | SHALL | Plan §5.2 | Schema validation verifies table definitions and foreign key `ON DELETE RESTRICT` constraints. |
| **FR-WLT-002** | The database bootstrap path — `backend/database/init_db.py` plus migration 002's idempotent seed section — SHALL provision a `farmer_wallets` record for `tahir_farmer` with an initial balance of `0.00` PKR and a `buyer_wallets` record for `sara_buyer` with `500000.00` PKR. | SHALL | Plan §9 Task 1.2, Phase 1 Build Spec | Database query verifies balances on seeded bootstrap. |
| **FR-WLT-003** | When a buyer registers via `POST /api/auth/register`, their wallet SHALL automatically be credited with `SIMULATED_BUYER_STARTING_BALANCE_PKR = 500000.00` PKR. | SHALL | Plan §5.2, §6.4 | API test: Register new buyer; query wallet balance; assert exactly 500,000.00 PKR. |
| **FR-WLT-004** | When a farmer registers via `POST /api/auth/register`, their wallet SHALL automatically be created in `farmer_wallets` with `balance_pkr = 0.00` PKR. | SHALL | Plan §5.2 | API test: Register new farmer; query `farmer_wallets`; assert row exists with 0.00 balance. |
| **FR-WLT-005** | The system SHALL expose an authenticated wallet balance endpoint `GET /api/wallets/me` returning the current user's role, wallet ID, and available `balance_pkr`. | SHALL | Derived from Plan §7.1 (buyer dashboard wallet balance card); endpoint added by this addendum | `test_escrow_orders.py::TC-WLT-01`: Call `/api/wallets/me` with buyer token returns balance and HTTP 200. |

### 5.2 Escrow Checkout & Funds Locking (`FR-ORD-XXX`, FEAT-INC2-03)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-ORD-001** | The system SHALL provide an escrow checkout endpoint: `POST /api/orders`, accessible exclusively by authenticated users holding the `buyer` role. | SHALL | Plan §6.2, §8 | `test_escrow_orders.py::TC-ORD-01`: Farmer token on `POST /api/orders` returns HTTP 403 Forbidden. |
| **FR-ORD-002** | The request payload for `POST /api/orders` SHALL strictly contain: `listing_id` (integer, required), `ordered_quantity_kg` (numeric, required, > 0), `destination_warehouse` (string, required, length >= 5), and `max_temperature_celsius` (numeric, required, default 8.0, range -25.0 to 30.0 per Scrum Master Determination D-INC2-10). | SHALL | Plan §6.2, D-INC2-10 | `test_escrow_orders.py::TC-ORD-02`: Missing `destination_warehouse` returns HTTP 400 Bad Request. |
| **FR-ORD-003** | **Whole-Listing Purchasing Invariant**: In Increment 2, the `ordered_quantity_kg` SHALL equal the full available `quantity_kg` of the target listing. Any request for partial quantities SHALL be rejected with HTTP 400 Bad Request ("Partial quantity purchasing is not supported in Increment 2."). | SHALL | Plan §13 Decision 1 | `test_escrow_orders.py::TC-ORD-03`: Request 50% of listing quantity; assert HTTP 400 with exact error message. |
| **FR-ORD-004** | The total purchase price SHALL be calculated deterministically as `total_amount_pkr = ordered_quantity_kg * listing.asking_price_per_kg`. If the buyer's `balance_pkr` in `buyer_wallets` is less than `total_amount_pkr`, the transaction SHALL be rejected with HTTP 400 Bad Request ("Insufficient wallet balance."). | SHALL | Plan §6.2 | `test_escrow_orders.py::TC-ORD-04`: Attempt purchase with cost exceeding 500,000.00 PKR; assert HTTP 400 rejection. |
| **FR-ORD-005** | Upon passing validation, the backend SHALL execute the checkout inside an explicit SQLite `BEGIN IMMEDIATE` database transaction executing all of the following actions atomically: (1) deduct `total_amount_pkr` from `buyer_wallets.balance_pkr`; (2) insert record into `orders` table with generated `order_number = 'ORD-{YYYY}-{ORDER_ID:04d}'` (e.g., `ORD-2026-0001`), status `'Escrow_Funded'`; (3) insert record into `escrow_holdings` table with `held_amount_pkr = total_amount_pkr`, status `'HELD'`; (4) update `listings.status` to `'Sold'`. | SHALL | Plan §4.3, §5.2, §6.2 | `test_escrow_orders.py::TC-ORD-05`: End-to-end checkout creates linked records across all 4 tables in atomic commit. |
| **FR-ORD-006** | **Double-Spend Prevention Invariant**: If two concurrent checkout requests target the same listing, the database `BEGIN IMMEDIATE` lock SHALL ensure the second request detects `status = 'Sold'` and aborts with HTTP 409 Conflict ("Listing has already been sold."), guaranteeing zero double-selling. | SHALL | Plan §11 RSK-01 | Concurrent stress test script executing simultaneous checkout threads on a single listing; exactly 1 succeeds. |
| **FR-ORD-007** | The checkout response (`201 Created`) SHALL return order confirmation details: `order_number`, `listing_id`, `total_amount_pkr`, `order_status = 'Escrow_Funded'`, `escrow_status = 'HELD'`, and `remaining_wallet_balance_pkr`. | SHALL | Plan §6.2 | Response schema assertion matching Plan §6.2 specification. |
| **FR-ORD-008** | The system SHALL expose an authenticated buyer order history endpoint: `GET /api/orders/buyer`, accessible exclusively by users holding the `buyer` role (farmers receive HTTP 403 Forbidden). The endpoint SHALL accept optional query parameters: `status` (string filter on `order_status`), `page` (integer, default 1), and `limit` (integer, default 20), and SHALL return orders placed by the authenticated buyer (`orders.buyer_id = jwt.buyer_id`) formatted according to the Increment 1 list envelope: `{"success": true, "data": [ ... ], "page": 1, "limit": 20, "total": N}`. | SHALL | Plan §6.2, §7.1, §8 | `test_escrow_orders.py::TC-ORD-06`: Buyer token retrieves own orders returning HTTP 200; farmer token returns HTTP 403. |
| **FR-ORD-009** | The system SHALL expose an authenticated farmer incoming orders endpoint: `GET /api/orders/farmer`, accessible exclusively by users holding the `farmer` role (buyers receive HTTP 403 Forbidden). The endpoint SHALL accept optional query parameters: `status` (string filter on `order_status`), `page` (integer, default 1), and `limit` (integer, default 20), and SHALL return orders for crop listings owned by the authenticated farmer (`orders.farmer_id = jwt.farmer_id`) formatted according to the Increment 1 list envelope: `{"success": true, "data": [ ... ], "page": 1, "limit": 20, "total": N}`. | SHALL | Plan §6.2, §7.2, §8 | `test_escrow_orders.py::TC-ORD-07`: Farmer token retrieves incoming orders returning HTTP 200; buyer token returns HTTP 403. |

### 5.3 Quality Acceptance & Settlement (`FR-SET-XXX`, FEAT-INC2-04)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-SET-001** | The system SHALL expose an escrow settlement endpoint: `POST /api/orders/<id>/confirm-delivery`, accessible exclusively by the authenticated buyer who owns the order. Calling with the wrong role (e.g., a farmer) SHALL return HTTP 403 Forbidden. Calling with the buyer role on an order owned by another buyer SHALL return unified HTTP 404 Not Found per NFR-SEC-002. | SHALL | Plan §6.2, §8, NFR-SEC-002 | `test_escrow_orders.py::TC-SET-01`: Calling endpoint with wrong role (farmer token) returns HTTP 403 Forbidden; calling with right role but non-owner (Buyer B confirming Buyer A's order) returns unified HTTP 404 Not Found. |
| **FR-SET-002** | The endpoint SHALL verify that the target order currently holds `order_status = 'Escrow_Funded'`. If the order is in any other status, the request SHALL be rejected with HTTP 400 Bad Request. | SHALL | Plan §4.3, §6.2 | `test_escrow_orders.py::TC-SET-02`: Confirming an already completed order returns HTTP 400. |
| **FR-SET-003** | Upon valid delivery confirmation, the backend SHALL execute the settlement atomically inside a `BEGIN IMMEDIATE` transaction: (1) set `orders.order_status = 'Completed'`; (2) record `orders.delivered_at = CURRENT_TIMESTAMP`; (3) record `escrow_holdings.delivered_at = CURRENT_TIMESTAMP`; (4) populate `escrow_holdings.auto_release_at = datetime(delivered_at + 72 hours)` (Increment 4 seam); (5) invoke `release_escrow(order_id, trigger='buyer_confirmation')`. | SHALL | Plan §4.3, §13 Decision 3 | `test_escrow_orders.py::TC-SET-03`: Check order status, timestamps, and escrow release status after confirmation. |
| **FR-SET-004** | The function `release_escrow(order_id, trigger)` in `backend/services/escrow_service.py` SHALL credit `escrow_holdings.held_amount_pkr` to `farmer_wallets.balance_pkr`, update `escrow_holdings.escrow_status = 'RELEASED'`, set `escrow_holdings.released_at = CURRENT_TIMESTAMP`, and stamp `escrow_holdings.release_tx_ref = 'TRIGGER:buyer_confirmation;REF:<tx_id>'`. | SHALL | Plan §4.2.3, §13 Decision 3 | Database inspection: Assert `farmer_wallets.balance_pkr` increased by exact held amount and `release_tx_ref` format matches. |
| **FR-SET-005** | The system SHALL expose an order cancellation endpoint: `POST /api/orders/<id>/cancel`, accessible by either the buyer or the farmer associated with the order, strictly when `order_status = 'Escrow_Funded'`. Calling with an unauthorized role SHALL return HTTP 403 Forbidden; calling with an authenticated buyer/farmer not associated with the order SHALL return unified HTTP 404 Not Found per NFR-SEC-002. | SHALL | Plan §4.3, §6.2, NFR-SEC-002 | `test_escrow_orders.py::TC-SET-04`: Order cancellation by owner buyer or farmer returns HTTP 200 OK; call by wrong role returns HTTP 403; call by non-owner tenant returns unified HTTP 404 Not Found. |
| **FR-SET-006** | Upon valid order cancellation, the backend SHALL atomically: (1) refund `held_amount_pkr` to `buyer_wallets.balance_pkr`; (2) update `escrow_holdings.escrow_status = 'REFUNDED'`; (3) update `orders.order_status = 'Cancelled'`; (4) restore the underlying listing status from `'Sold'` back to `'Active'`. | SHALL | Plan §4.3, §6.2 | `test_escrow_orders.py::TC-SET-05`: Cancel order; assert buyer wallet refunded and listing reappears in marketplace catalog. |

### 5.4 Global Status State Machine & Transition Rules (`FR-STM-XXX`, FEAT-INC2-12)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-STM-001** | The system SHALL strictly enforce the Master State Transition Matrix across `listings`, `orders`, and `escrow_holdings`. Any transition attempt outside the permitted transitions SHALL be rejected with HTTP 400 Bad Request. | SHALL | Plan §4.3 | Matrix test suite exercising every invalid permutation; assert all invalid transitions are blocked. |
| **FR-STM-002** | A listing in status `'Active'` SHALL only transition to `'Withdrawn'` (via farmer `DELETE /api/crops/<id>`) or `'Sold'` (via buyer `POST /api/orders`). | SHALL | Plan §4.3 Master Matrix | State guard test in `crop_service.py` asserting valid listing targets. |
| **FR-STM-003** | A listing in status `'Sold'` SHALL only transition back to `'Active'` via an authorized order cancellation (`POST /api/orders/<id>/cancel`). In Increment 2, transitions to `'In Transit'` or `'Delivered'` are prohibited as the Transporter role is inactive. | SHALL | Plan §4.3 Master Matrix | State guard unit test verifying rejection of manual status edits on sold listings. |
| **FR-STM-004** | An order in status `'Escrow_Funded'` SHALL only transition to: `'Completed'` (via buyer confirmation), `'Cancelled'` (via buyer/farmer cancellation), or `'Disputed'` (via dispute notification). | SHALL | Plan §4.3 Master Matrix | `test_escrow_orders.py::TC-STM-01`: Assert order transition guards enforce valid targets. |
| **FR-STM-005** | The system SHALL expose an order dispute endpoint: `POST /api/orders/<id>/dispute`, accessible by the buyer or farmer when `order_status = 'Escrow_Funded'`. Calling with an unauthorized role SHALL return HTTP 403 Forbidden; calling on an order not owned by the tenant SHALL return unified HTTP 404 Not Found per NFR-SEC-002. The endpoint SHALL update `orders.order_status = 'Disputed'` and `escrow_holdings.escrow_status = 'DISPUTED'`, freezing funds in escrow. | SHALL | Plan §4.3, §6.2, NFR-SEC-002 | `test_escrow_orders.py::TC-STM-02`: Dispute by owner buyer/farmer freezes funds (HTTP 200); call by wrong role returns HTTP 403; call by non-owner tenant returns unified HTTP 404 Not Found. |
| **FR-STM-006** | **Dispute Record-Only Boundary Invariant**: In Increment 2, disputed orders and escrow holdings SHALL remain permanently frozen. No dispute-resolution endpoint, unfreezing logic, or exit transition SHALL exist in Increment 2. Formal dispute arbitration is deferred to Increment 4 (Compliance Officer). | SHALL | Plan §2.2.6, §4.3 Scope Note | Code inspection & API scan verifying zero dispute-resolution routes exist in `orders.py` or `escrow_service.py`. |

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 INCREMENT 2 LIFECYCLE STATE TRANSITION FLOW                 │
└─────────────────────────────────────────────────────────────────────────────┘

  [LISTING]
   Active ────────(Buyer POST /api/orders)─────────► Sold
     │                                                 │
     │ (Farmer DELETE /api/crops/<id>)                 │ (Buyer/Farmer POST /api/orders/<id>/cancel)
     ▼                                                 ▼
   Withdrawn                                         Active (Refunded & Restored)

  [ORDER]
   Escrow_Funded ───(Buyer POST /confirm-delivery)──► Completed (Funds to Farmer Wallet)
     │
     ├───(Buyer/Farmer POST /cancel)────────────────► Cancelled (Funds to Buyer Wallet)
     │
     └───(Buyer/Farmer POST /dispute)───────────────► Disputed (Frozen in Escrow — Inc 4 Seam)
```

---

## 6. Module 4: Environmental Telemetry & Predictive Intelligence Requirements

### 6.1 External Weather & Soil Telemetry Client (`FR-TEL-XXX`, FEAT-INC2-07)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-TEL-001** | The system SHALL implement an external telemetry service (`backend/services/telemetry_service.py`) capable of requesting meteorological data from OpenWeatherMap API and edaphic (soil) data from SoilGrids REST API using latitude and longitude coordinates. | SHALL | Plan §2.1, §9 Task 4.1 | Unit test exercising service methods `fetch_weather(lat, lon)` and `fetch_soil(lat, lon)`. |
| **FR-TEL-002** | Weather telemetry requests SHALL extract: ambient temperature (°C), relative humidity (%), 14-day cumulative precipitation forecast (mm), and solar radiation indices. | SHALL | Plan §2.1, Doc 3 §3 | Fixture payload validation: Check structure of parsed weather dictionary. |
| **FR-TEL-003** | Soil telemetry requests SHALL extract: topsoil moisture content (0–5cm, m³/m³), soil organic carbon content (g/kg), and soil pH. | SHALL | Plan §2.1, Doc 3 §4 | Fixture payload validation: Check structure of parsed soil dictionary. |
| **FR-TEL-004** | The system SHALL expose authenticated telemetry endpoints: `GET /api/telemetry/weather` and `GET /api/telemetry/soil`, accepting `lat` (latitude) and `lon` (longitude) query parameters, accessible by authenticated farmers and buyers. | SHALL | Plan §6.3, §8 | `test_yield_telemetry.py::TC-TEL-01`: Query `/api/telemetry/weather?lat=30.3753&lon=69.3451` returns HTTP 200. |
| **FR-TEL-005** | **Offline Test & Fallback Doctrine**: When external API calls fail (network timeout, rate limit exceeded, missing API key, or `AGRIGRID_OFFLINE_MODE = 1`), the telemetry service SHALL gracefully degrade and load high-fidelity deterministic fixtures from `backend/tests/fixtures/weather_punjab.json` and `backend/tests/fixtures/soil_punjab.json`, never raising an unhandled exception or returning HTTP 500. | SHALL | Plan §10.3, §13 Decision 4 | `test_yield_telemetry.py::TC-TEL-02`: Run with mock offline env var; assert valid telemetry returned without internet. |

### 6.2 Telemetry Database Caching Engine (`FR-CCH-XXX`, FEAT-INC2-08)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-CCH-001** | The database SHALL maintain a telemetry caching table named `telemetry_cache` created via migration 002: `id` (INTEGER PK AUTOINCREMENT), `cache_key` (TEXT UNIQUE), `provider` (TEXT CHECK IN ('OpenWeatherMap', 'SoilGrids')), `latitude` (REAL), `longitude` (REAL), `payload_json` (TEXT), `fetched_at` (TEXT ISO-8601), and `expires_at` (TEXT ISO-8601). | SHALL | Plan §5.2 | Schema verification confirms table structure and index `idx_telemetry_cache_lookup`. |
| **FR-CCH-002** | The cache key SHALL be formatted deterministically as `<telemetry_type>:<lat>:<lon>` where `telemetry_type` is `'weather'` (for provider OpenWeatherMap) or `'soil'` (for provider SoilGrids), and latitude and longitude are formatted to 4 decimal places (e.g., `weather:30.3753:69.3451` or `soil:30.3753:69.3451`). | SHALL | Plan §5.2 | Service unit test verifying exact key generation string format. |
| **FR-CCH-003** | All telemetry cache records SHALL enforce a uniform **6-Hour Time-To-Live (TTL)**. The `expires_at` column SHALL be calculated as `datetime(fetched_at + 6 hours)`. | SHALL | Plan §4.4, §13 Decision 4 | Unit test: Insert cache row; assert `expires_at` is exactly 6 hours ahead of `fetched_at`. |
| **FR-CCH-004** | Before making any external HTTP call, the telemetry service SHALL query `telemetry_cache` for a matching `cache_key` where `expires_at > CURRENT_TIMESTAMP`. If a valid unexpired record exists, the service SHALL deserialize and return `payload_json` immediately without invoking external APIs. | SHALL | Plan §4.4, §10.2 | `test_yield_telemetry.py::TC-CCH-01`: Query same coordinates twice; assert second call takes < 10ms and external mock count = 1. |
| **FR-CCH-005** | If a cache record is expired (`expires_at <= CURRENT_TIMESTAMP`) or absent, the service SHALL fetch fresh data, store/update the record in `telemetry_cache`, and update `expires_at` to `now() + 6 hours`. | SHALL | Plan §5.2 | Unit test: Query coordinates with artificially expired cache row; assert fresh fetch and updated timestamps. |

### 6.3 Algorithmic Predictive Yield Engine (`FR-YLD-XXX`, FEAT-INC2-09)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-YLD-001** | The system SHALL implement a deterministic, algorithmic Predictive Yield calculation service (`backend/services/yield_service.py`) combining crop parameters with environmental telemetry. | SHALL | Plan §4.2, §13 Decision 5 | `test_yield_telemetry.py::TC-YLD-01`: Execute yield service with standard input vectors; verify outputs. |
| **FR-YLD-002** | The yield engine SHALL utilize an explainable mathematical formula core based on: (1) baseline regional crop yield constants ($Y_{base}$ in kg/acre); (2) Growing Degree Days ($GDD$) accumulation relative to planting date; (3) rainfall deviation factor ($f_{rain}$); and (4) soil moisture/pH stress coefficients ($f_{soil}$). The engine SHALL NOT use non-deterministic black-box machine learning models in Increment 2. | SHALL | Plan §13 Decision 5 | Formula verification: Assert calculated values match manual arithmetic benchmarks across all 8 supported crops. |
| **FR-YLD-003** | The system SHALL expose an authenticated yield forecast endpoint: `POST /api/yield/predict`, accessible exclusively by the farmer who owns the target listing. | SHALL | Plan §6.3, §8 | `test_yield_telemetry.py::TC-YLD-02`: Call endpoint with non-owner farmer token; assert HTTP 404 Unified Not Found. |
| **FR-YLD-004** | The request payload for `POST /api/yield/predict` SHALL contain `listing_id` (integer, required). The service SHALL load crop variety, acreage, planting date, and GPS coordinates directly from the verified database listing. | SHALL | Plan §6.3 | API test: Pass valid `listing_id`; verify response extracts listing data and completes prediction. |
| **FR-YLD-005** | The calculation result SHALL output: `predicted_harvest_date` (ISO date), `predicted_yield_kg` (numeric, positive), `confidence_score_pct` (integer between 0 and 100), `environmental_index` (numeric 0.0–1.0), and `irrigation_advice` (actionable text advisory string). | SHALL | Plan §5.2, §6.3 | Payload contract assertion: Response matches required keys and data types. |
| **FR-YLD-006** | Every generated yield forecast SHALL be persisted in the `yield_forecasts` table created via migration 002: `listing_id`, `crop_name`, `predicted_harvest_date`, `predicted_yield_kg`, `confidence_score_pct`, `environmental_index`, `irrigation_advice`, and `generated_at`. | SHALL | Plan §5.2 | Database query: `SELECT * FROM yield_forecasts WHERE listing_id = ?` confirms persistence. |
| **FR-YLD-007** | The farmer dashboard (`frontend/dashboard.html` and `dashboard.js`) SHALL render a `"⚡ Forecast Yield"` button on each active crop row. Clicking it SHALL open a modal presenting the predicted harvest date, estimated tonnage, confidence score badge, and agronomic irrigation advice. | SHALL | Plan §7.2 | Manual UI verification: Click button; modal renders computed values and telemetry context without errors. |

---

## 7. Module 5: System Taxonomies & Contract Extensions

### 7.1 Taxonomy Vocabularies & Client Dropdown Bindings (`FR-TAX-XXX`)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **FR-TAX-001** | The backend SHALL expose an authenticated metadata endpoint: `GET /api/meta/taxonomies`, returning the authoritative system whitelists: `{"success": true, "data": {"crop_names": [...], "statuses": [...]}}`. | SHALL | Plan §4.4, §6.3 | `test_frontend_contract.py::TC-F1`: Runtime HTTP GET on `/api/meta/taxonomies` returns HTTP 200. |
| **FR-TAX-002** | The single source of truth for `crop_names` returned by `GET /api/meta/taxonomies` SHALL be `backend/crops.py:VALID_CROP_NAMES` (`["Wheat", "Rice", "Tomato", "Potato", "Cotton", "Maize", "Sugarcane", "Other"]`). | SHALL | Plan §4.4 | Contract assertion: `response.json()["data"]["crop_names"] == sorted(list(crops.VALID_CROP_NAMES))`. |
| **FR-TAX-003** | The single source of truth for `statuses` returned by `GET /api/meta/taxonomies` SHALL be `backend/crops.py:VALID_STATUSES` (`frozenset(["Active", "Sold", "In Transit", "Delivered", "Withdrawn"])`). | SHALL | Plan §4.4, Code Alignment | Contract assertion: `set(response.json()["data"]["statuses"]) == set(crops.VALID_STATUSES)`. |
| **FR-TAX-004** | **Client Dropdown Source-of-Truth Binding Rules**: (1) The **Farmer Dashboard** crop `<select id="modalCropName">` SHALL remain statically defined in `frontend/dashboard.html` to preserve Increment 1 AST compatibility (`TC-F1`); (2) The **Buyer Marketplace** catalog filter `<select id="filterCropName">` in `frontend/buyer_dashboard.html` SHALL be dynamically populated on page initialization by fetching `GET /api/meta/taxonomies`. | SHALL | Plan §4.4, §7.3 | Contract test `TC-F1` passes AST verification; E2E browser test verifies dynamic population of buyer filter. |

---

## 8. Non-Functional Requirements (NFRs)

### 8.1 Performance & Scalability (`NFR-PERF-XXX`)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **NFR-PERF-001** | The B2B Marketplace catalog endpoint (`GET /api/marketplace/listings`) SHOULD execute with a response latency under **1.0 second** on standard development environments. | SHOULD | Plan §9 Task 2.1 Target | Timing check in `test_marketplace_api.py`: catalog request completes < 1.0s on the dev machine. |
| **NFR-PERF-002** | Escrow checkout transactions (`POST /api/orders`) and delivery confirmations (`POST /api/orders/<id>/confirm-delivery`) SHOULD execute with a latency under **500 milliseconds** on standard development environments. | SHOULD | Plan §9 Task 3.1 Target | Timing check in `test_escrow_orders.py`: checkout and confirmation execute < 500ms on the dev machine. |
| **NFR-PERF-003** | Cached telemetry lookups from `telemetry_cache` SHALL return within **100 milliseconds**. | SHALL | Plan §10.2 | Benchmark test measuring database cache retrieval time; assert < 100ms. |
| **NFR-PERF-004** | The algorithmic Predictive Yield Engine (`yield_service.py`) SHOULD compute and return forecasts within **800 milliseconds** per listing on standard development environments. | SHOULD | Plan §9 Task 4.2 Target | Timing check in `test_yield_telemetry.py`: `POST /api/yield/predict` completes < 800ms on the dev machine. |

### 8.2 Security, Multi-Tenancy & Integrity (`NFR-SEC-XXX`)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **NFR-SEC-001** | **Strict Zero-Trust Multi-Tenancy**: The backend SHALL extract `farmer_id` and `buyer_id` exclusively from verified JWT claims. Request payloads containing explicit tenant ID fields (`buyer_id`, `farmer_id`, `user_id`) SHALL be ignored or rejected. | SHALL | Plan §8, Inc 1 SRS §6 | Security unit test: Submit POST `/api/orders` injecting foreign `buyer_id`; assert order binds to JWT identity. |
| **NFR-SEC-002** | **Unified 404 Anti-Enumeration Policy**: Any query or mutation targeting an order or listing that does not exist OR belongs to another tenant SHALL return `HTTP 404 Not Found` with a generic message, preventing resource enumeration. Calling an endpoint with an unauthorized role (e.g., a farmer calling a buyer-only endpoint) returns `HTTP 403 Forbidden`. | SHALL | Plan §6.1, Inc 1 SRS §6.3 | Multi-tenant test: Buyer A queries Buyer B's order ID; assert HTTP 404. Non-buyer role; assert HTTP 403. |
| **NFR-SEC-003** | **ACID Financial Integrity**: All escrow balance deductions, wallet credits, order status mutations, and listing state changes SHALL execute inside explicit `BEGIN IMMEDIATE` SQLite transactions to guarantee atomic consistency and prevent race conditions or double-spending. | SHALL | Plan §11 RSK-01 | Chaos test: Simulate sudden process termination during transaction; verify zero partial writes or balance leaks. |

### 8.3 Reliability, Offline Degradation & Availability (`NFR-REL-XXX`)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **NFR-REL-001** | **Graceful Telemetry Degradation**: External API network outages, HTTP 429 rate-limiting, or invalid API credentials SHALL NOT crash the application or prevent crop creation or yield estimation. The service SHALL seamlessly serve local deterministic fixtures. | SHALL | Plan §13 Decision 4 | Integration test: Disable network connectivity; execute yield forecast; assert successful response using fallback. |
| **NFR-REL-002** | **Immutable Migration Security**: Startup scripts SHALL immediately abort and refuse to run if any applied SQL migration file's SHA-256 hash differs from the hash recorded in `schema_versions`. | SHALL | Plan §4.1.3 | Automated CI check modifying past migration file; assert build failure. |
| **NFR-REL-003** | **100% Regression Suite Guarantee**: Every commit and merge milestone SHALL pass all 45 Increment 1 regression tests, all new Increment 2 test suites (marketplace, escrow, telemetry), and all extended contract tests. | SHALL | Plan §10.1, §10.2 | Test automation runner executing full suite: 100% pass rate required. |

### 8.4 Usability & Human-Computer Interface (`NFR-USE-XXX`)

| Req ID | Requirement Statement | Priority | Plan Trace | Executable Proof |
|---|---|:---:|:---:|---|
| **NFR-USE-001** | The Buyer Dashboard presentation layer (`frontend/buyer_dashboard.html`) SHALL adhere strictly to the established **Terra × Terracotta** design tokens (`frontend/css/dashboard.css` or `frontend/css/buyer.css`) and conform to `FRONTEND_CHANGE_CHECKLIST.md`. | SHALL | Plan §7.1, §7.3 | Visual audit and CSS validator confirming color tokens, typography, and viewport containment. |
| **NFR-USE-002** | The interface SHALL display all monetary values formatted in Pakistani Rupees with commas and two decimal places (e.g., `Rs. 225,000.00`). No `$` symbols SHALL be rendered. | SHALL | Plan §4.4, §7.3 | DOM inspection and contract test `TC-F5` confirming zero literal `$` characters in active UI. |
| **NFR-USE-003** | Presentation scripts (`frontend/js/buyer.js`, `frontend/js/dashboard.js`) SHALL contain inline anti-FOUC authentication guards redirecting unauthenticated sessions to `index.html` before rendering protected markup. | SHALL | Plan §7.3 | Browser simulation: Access `buyer_dashboard.html` without `sessionStorage` token; assert instantaneous redirect. |

---

## 9. Complete Traceability Matrix

| Requirement ID | Requirement Summary | Increment 2 Feature ID | Plan Section Trace | Source Doc Reference | Executable Proof Check |
|---|---|:---:|:---:|:---:|---|
| `FR-MIG-001` | Automated migration runner | FEAT-INC2-10 | Plan §4.1, §9 Task 1.1 | Gap 1 Closure | `backend/database/migrate.py` execution |
| `FR-MIG-002` | `schema_versions` tracking table | FEAT-INC2-10 | Plan §4.1.1 | Gap 1 Closure | SQL table definition & checksum column check |
| `FR-MIG-003` | Sequential scripts `001` & `002` | FEAT-INC2-10 | Plan §4.1.1, §5 | Gap 1 Closure | Migration file inventory & sequential ordering |
| `FR-MIG-004` | `BEGIN IMMEDIATE` / `COMMIT` loop | FEAT-INC2-10 | Plan §4.1.2 | Gap 1 Closure | Transaction rollback test on injected syntax error |
| `FR-MIG-005` | SHA-256 immutable checksum audit | FEAT-INC2-10 | Plan §4.1.3 | Gap 1 Closure | Tamper test: modify script byte; assert halt |
| `FR-MIG-006` | Launcher automatic migration run | FEAT-INC2-10 | Plan §4.1.4 | Gap 1 Closure | `launch_agrigrid.py` dry-run on fresh database |
| `FR-MIG-007` | `app.py` startup version guard | FEAT-INC2-10 | Plan §4.1.4 | Gap 1 Closure | Start app against v1 DB; assert non-zero exit & remediation message |
| `FR-SRV-001` | Service layer SQL extraction | FEAT-INC2-11 | Plan §4.2, §9 Task 1.3 | Gap 2 Closure | grep confirms no SQL in `crops.py` bodies; all queries in `crop_service.py` |
| `FR-SRV-002` | AST constants preserved in `crops.py` | FEAT-INC2-11 | Plan §4.2 Refinement | Gap 2 Closure | `test_frontend_contract.py::TC-F1, TC-F2` AST pass |
| `FR-SRV-003` | `crop_service.py` pure business ops | FEAT-INC2-11 | Plan §4.2 | Gap 2 Closure | Unit tests for `crop_service.py` CRUD methods |
| `FR-SRV-004` | 45/45 Inc 1 regression preserved | FEAT-INC2-11 | Plan §4.2.4, §10.1 | Gap 2 Closure | `python backend/test_auth.py`, `test_crops_api.py`, `test_frontend_contract.py` (45/45 pass) |
| `FR-BYR-001` | Buyer registration role support | FEAT-INC2-02 | Plan §2.1, §6.4 | Doc 4 §2.2; Doc 5 §2 | `test_marketplace_api.py::TC-BYR-01` |
| `FR-BYR-002` | Mandatory buyer company fields | FEAT-INC2-02 | Plan §5.2, §6.4 | Doc 4 §2.2 | `test_marketplace_api.py::TC-BYR-02` |
| `FR-BYR-003` | Atomic User + Buyer + Wallet insert | FEAT-INC2-02 | Plan §5.2, §6.4 | Doc 5 §2 Step 2 | Database inspection verifying 3 linked records |
| `FR-BYR-004` | Registration rollback on error | FEAT-INC2-02 | Plan §6.4 | System Integrity | Constraint failure test; verify zero orphaned rows |
| `FR-BYR-005` | Buyer JWT claims & login payload | FEAT-INC2-02 | Plan §3.1, §6.4 | Doc 7 §3.C | Token inspection; role `buyer`, `farmer_id` null |
| `FR-BYR-006` | Seed `sara_buyer` via migration 002 | FEAT-INC2-02 | Plan §9 Task 1.2, Phase 1 Spec | Doc 7 §3.C | Bootstrap execution; query Metro Wholesale Foods & 500k wallet |
| `FR-PRC-001` | Add `asking_price_per_kg` & `batch_id` (unique index) | FEAT-INC2-05 | Plan §1.2, §5.1 | Doc 4 §2.1; Doc 5 §2 | SQLite schema & index inspection |
| `FR-PRC-002` | Commercial price validation (> 0) | FEAT-INC2-05 | Plan §6.4 | Doc 4 §2.1 | `test_crops_api.py::TC-PRC-01` (negative price test) |
| `FR-PRC-003` | Automated `batch_id` template & codes | FEAT-INC2-05 | Plan §5.1, D-INC2-08 | Doc 5 §2 Step 1 | API test: verify `BATCH-{YEAR}-{CROP_CODE3}-{LISTING_ID:04d}` format |
| `FR-PRC-004` | UI commercial pricing inputs enabled | FEAT-INC2-05 | Plan §7.2 | Doc 4 §2.1 | UI verification; remove Inc 2 disabled tags |
| `FR-PRC-005` | Seed commercial prices in migration 002 | FEAT-INC2-05 | Plan §13 Dec 2, Phase 1 Spec | Doc 5 §2 Step 1 | Query seeded crop listings; verify prices & batches |
| `FR-MKT-001` | B2B catalog route `GET /api/marketplace` | FEAT-INC2-01 | Plan §6.1, §8 | Doc 4 §2.2; Doc 6 §2 | `test_marketplace_api.py::TC-MKT-01` |
| `FR-MKT-002` | Catalog filter: Active, unwithdrawn, priced | FEAT-INC2-01 | Plan §6.1, §13 Dec 2 | Doc 5 §2 Step 2 | `test_marketplace_api.py::TC-MKT-02` |
| `FR-MKT-003` | Filter parameters (crop, price, sort) | FEAT-INC2-01 | Plan §6.1 | Doc 4 §2.2 | `test_marketplace_api.py::TC-MKT-03` |
| `FR-MKT-004` | Flat list envelope `{data, page, limit, total}` | FEAT-INC2-01 | Plan §6 universal rule | AG-API-INC1-003 | Contract test asserting envelope keys match |
| `FR-MKT-005` | Serialized produce listing attributes | FEAT-INC2-01 | Plan §6.1 | Doc 4 §2.2 | Unit test asserting listing response payload schema |
| `FR-MKT-006` | Single listing detail endpoint | FEAT-INC2-01 | Plan §6.1 | Doc 4 §2.2 | `test_marketplace_api.py::TC-MKT-04` |
| `FR-MKT-007` | Unified 404 anti-enumeration & note | FEAT-INC2-01 | Plan §6.1 | Security Standard | `test_marketplace_api.py::TC-MKT-05` |
| `FR-WLT-001` | Ledger tables: `buyer_wallets`, `farmer_wallets`| FEAT-INC2-06 | Plan §5.2 | Doc 4 §2.2; Doc 7 §2 | Schema inspection of wallet tables & FK constraints |
| `FR-WLT-002` | Seed initial balances via migration 002 | FEAT-INC2-06 | Plan §9 Task 1.2, Phase 1 Spec | Doc 7 §2 | Query seed balances in `agrigrid.db` (500k Sara, 0 Tahir) |
| `FR-WLT-003` | Buyer onboarding initial credit (500k) | FEAT-INC2-06 | Plan §5.2, §6.4 | Doc 4 §2.2 | Register buyer test; verify 500,000.00 balance |
| `FR-WLT-004` | Farmer onboarding wallet creation (0.00) | FEAT-INC2-06 | Plan §5.2 | Doc 4 §2.1 | Register farmer test; verify 0.00 wallet created |
| `FR-WLT-005` | Current user wallet balance route | FEAT-INC2-06 | Derived from Plan §7.1 | UI Card Binding | `test_escrow_orders.py::TC-WLT-01` |
| `FR-ORD-001` | Escrow order route `POST /api/orders` | FEAT-INC2-03 | Plan §6.2, §8 | Doc 4 §2.2; Doc 5 §2 | `test_escrow_orders.py::TC-ORD-01` |
| `FR-ORD-002` | Order payload validation (warehouse, temp) | FEAT-INC2-03 | Plan §6.2, D-INC2-10 | Doc 5 §2 Step 2 | `test_escrow_orders.py::TC-ORD-02` |
| `FR-ORD-003` | Whole-listing purchasing invariant | FEAT-INC2-03 | Plan §13 Decision 1 | Architecture Rule | `test_escrow_orders.py::TC-ORD-03` |
| `FR-ORD-004` | Wallet balance sufficiency check | FEAT-INC2-03 | Plan §6.2 | Doc 5 §2 Step 2 | `test_escrow_orders.py::TC-ORD-04` |
| `FR-ORD-005` | Atomic checkout & deterministic order number | FEAT-INC2-03 | Plan §4.3, §5.2, §6.2 | Doc 5 §2 Step 2 | `test_escrow_orders.py::TC-ORD-05`: `ORD-{YYYY}-{ORDER_ID:04d}` created |
| `FR-ORD-006` | Double-spend prevention via `BEGIN IMMEDIATE` | FEAT-INC2-03 | Plan §11 RSK-01 | Financial Integrity | Concurrent checkout collision test |
| `FR-ORD-007` | Order checkout response schema | FEAT-INC2-03 | Plan §6.2 | AG-API-INC1-003 | Response JSON schema verification |
| `FR-ORD-008` | Buyer order history route `GET /api/orders/buyer` | FEAT-INC2-03 | Plan §6.2, §7.1, §8 | Doc 4 §2.2 | `test_escrow_orders.py::TC-ORD-06` |
| `FR-ORD-009` | Farmer incoming orders route `GET /api/orders/farmer` | FEAT-INC2-03 | Plan §6.2, §7.2, §8 | Doc 4 §2.1 | `test_escrow_orders.py::TC-ORD-07` |
| `FR-SET-001` | Buyer delivery confirmation (403/404 check) | FEAT-INC2-04 | Plan §6.2, §8, NFR-SEC-002 | Doc 4 §2.2; Doc 5 §5 | `test_escrow_orders.py::TC-SET-01`: wrong role -> 403; non-owner tenant -> 404 |
| `FR-SET-002` | Order status precondition (`Escrow_Funded`) | FEAT-INC2-04 | Plan §4.3, §6.2 | Doc 5 §2 Step 5 | `test_escrow_orders.py::TC-SET-02` |
| `FR-SET-003` | Atomic settlement & timestamping | FEAT-INC2-04 | Plan §4.3, §13 Dec 3 | Doc 5 §2 Step 5 | `test_escrow_orders.py::TC-SET-03` |
| `FR-SET-004` | `release_escrow()` farmer wallet credit | FEAT-INC2-04 | Plan §4.2.3, §13 Dec 3 | Doc 5 §2 Step 5 | Database query verifying farmer wallet balance |
| `FR-SET-005` | Order cancellation route (403/404 check) | FEAT-INC2-04 | Plan §4.3, §6.2, NFR-SEC-002 | State Machine Rule | `test_escrow_orders.py::TC-SET-04`: owner -> 200; wrong role -> 403; non-owner tenant -> 404 |
| `FR-SET-006` | Atomic cancellation refund & listing reset | FEAT-INC2-04 | Plan §4.3, §6.2 | State Machine Rule | `test_escrow_orders.py::TC-SET-05` |
| `FR-STM-001` | Master State Machine transition guards | FEAT-INC2-12 | Plan §4.3 | Gap 3 Closure | Transition matrix test suite |
| `FR-STM-002` | Listing transitions (Active to Withdrawn/Sold) | FEAT-INC2-12 | Plan §4.3 Master Matrix | Gap 3 Closure | Unit test verifying valid listing state changes |
| `FR-STM-003` | Sold listing restore via cancellation | FEAT-INC2-12 | Plan §4.3 Master Matrix | Gap 3 Closure | State guard test on sold listings |
| `FR-STM-004` | Order transitions (Funded to Comp/Canc/Disp) | FEAT-INC2-12 | Plan §4.3 Master Matrix | Gap 3 Closure | `test_escrow_orders.py::TC-STM-01` |
| `FR-STM-005` | Order dispute notification (403/404 check) | FEAT-INC2-12 | Plan §4.3, §6.2, NFR-SEC-002 | Doc 4 §2.2 | `test_escrow_orders.py::TC-STM-02`: owner -> 200; wrong role -> 403; non-owner tenant -> 404 |
| `FR-STM-006` | Dispute record-only boundary invariant | FEAT-INC2-12 | Plan §2.2.6, §4.3 Note | Scope Control | Code inspection confirming zero dispute exit routes |
| `FR-TEL-001` | Telemetry client service implementation | FEAT-INC2-07 | Plan §2.1, §9 Task 4.1 | Doc 3 §3, §4 | Unit tests for `telemetry_service.py` fetchers |
| `FR-TEL-002` | OpenWeatherMap data parsing | FEAT-INC2-07 | Plan §2.1, Doc 3 §3 | Doc 3 §3 | Fixture parsing assertion for temp, rain, humidity |
| `FR-TEL-003` | SoilGrids data parsing | FEAT-INC2-07 | Plan §2.1, Doc 3 §4 | Doc 3 §4 | Fixture parsing assertion for moisture, carbon, pH |
| `FR-TEL-004` | Telemetry API endpoints (weather/soil) | FEAT-INC2-07 | Plan §6.3, §8 | Doc 3 §3, §4 | `test_yield_telemetry.py::TC-TEL-01` |
| `FR-TEL-005` | Offline fixture fallback doctrine | FEAT-INC2-07 | Plan §10.3, §13 Dec 4 | Reliability Gate | `test_yield_telemetry.py::TC-TEL-02` (offline mode) |
| `FR-CCH-001` | `telemetry_cache` SQLite table & index | FEAT-INC2-08 | Plan §5.2 | Doc 3 §5.1 | SQLite schema inspection of cache table |
| `FR-CCH-002` | Cache key format (`telemetry_type:lat:lon`) | FEAT-INC2-08 | Plan §5.2 | Doc 3 §5.1 | Unit test verifying key generation string |
| `FR-CCH-003` | Uniform 6-hour TTL timestamping | FEAT-INC2-08 | Plan §4.4, §13 Dec 4 | Doc 3 §5.1 | Unit test: `expires_at == fetched_at + 6 hours` |
| `FR-CCH-004` | Cache hit on unexpired records (< 6h) | FEAT-INC2-08 | Plan §4.4, §10.2 | Performance Gate | `test_yield_telemetry.py::TC-CCH-01` |
| `FR-CCH-005` | Cache miss / expiry refresh | FEAT-INC2-08 | Plan §5.2 | Doc 3 §5.1 | Unit test verifying re-fetch on expired row |
| `FR-YLD-001` | Predictive yield calculation service | FEAT-INC2-09 | Plan §4.2, §13 Dec 5 | Doc 2 Role 2; Doc 3 §4 | `test_yield_telemetry.py::TC-YLD-01` |
| `FR-YLD-002` | Deterministic formula core (GDD, rain, soil) | FEAT-INC2-09 | Plan §13 Decision 5 | Doc 3 §4; Doc 5 §2 | Benchmark mathematical verification across 8 crops |
| `FR-YLD-003` | Yield predict route `POST /api/yield/predict` | FEAT-INC2-09 | Plan §6.3, §8 | Doc 4 §2.1 | `test_yield_telemetry.py::TC-YLD-02` |
| `FR-YLD-004` | Extraction of crop vector from listing | FEAT-INC2-09 | Plan §6.3 | Doc 5 §2 Step 1 | API test: verify listing attributes fed to engine |
| `FR-YLD-005` | Forecast output schema (date, kg, advice) | FEAT-INC2-09 | Plan §5.2, §6.3 | Doc 4 §2.1 | Response contract assertion for forecast payload |
| `FR-YLD-006` | Persist output to `yield_forecasts` table | FEAT-INC2-09 | Plan §5.2 | Doc 5 §2 Step 1 | Database query verifying forecast persistence |
| `FR-YLD-007` | Farmer UI "Forecast Yield" button & modal | FEAT-INC2-09 | Plan §7.2 | Doc 4 §2.1 | Manual UI inspection: modal renders metrics |
| `FR-TAX-001` | Taxonomies metadata route `GET /taxonomies` | Backlog | Plan §4.4, §6.3 | Contract Gate | `test_frontend_contract.py::TC-F1` runtime GET |
| `FR-TAX-002` | `crop_names` single source of truth | Backlog | Plan §4.4 | Contract Gate | Assertion: API matches `crops.py:VALID_CROP_NAMES` |
| `FR-TAX-003` | `statuses` single source of truth | Backlog | Plan §4.4, Code Alignment | Contract Gate | Assertion: API matches `crops.py:VALID_STATUSES` (5 statuses) |
| `FR-TAX-004` | Client dropdown bindings (static vs dynamic) | Backlog | Plan §4.4, §7.3 | Contract Gate | `test_frontend_contract.py::TC-F1` AST + E2E buyer test |
| `NFR-PERF-001`| Marketplace catalog latency target (< 1.0s) | Quality | Plan §9 Task 2.1 Target | Target Budget | Timing check in `test_marketplace_api.py` (< 1.0s) |
| `NFR-PERF-002`| Escrow checkout/confirm latency (< 500ms) | Quality | Plan §9 Task 3.1 Target | Target Budget | Timing check in `test_escrow_orders.py` (< 500ms) |
| `NFR-PERF-003`| Telemetry cache retrieval latency (< 100ms) | Quality | Plan §10.2 | Performance Gate | Benchmark timing assertion (< 100ms) |
| `NFR-PERF-004`| Yield prediction calculation latency (< 800ms) | Quality | Plan §9 Task 4.2 Target | Target Budget | Timing check in `test_yield_telemetry.py` (< 800ms) |

---

## 10. Scrum Master Decision List (Determinations Recorded)

The technical choices formulated during the RE phase have been officially adjudicated and signed off by the Scrum Master. All four determinations stand **DECIDED**:

---

### Decision D-INC2-07: Farmer Initial Seed Wallet Balance Policy
- **Context**: In Plan §5.2 and §9 Task 1.2, Sara Buyer is explicitly assigned `SIMULATED_BUYER_STARTING_BALANCE_PKR = 500000.00`. In Plan §5.2, `farmer_wallets.balance_pkr` has `DEFAULT 0.00`.
- **Question**: Should `tahir_farmer`'s initial wallet balance be seeded with `0.00 PKR` (reflecting zero revenue prior to produce sales) or receive simulated working capital balance?
- **Options**:
  - **Option A (Recommended)**: Seed `tahir_farmer` with `0.00 PKR` in `farmer_wallets`, matching the SQL schema default. In an escrow architecture, a farmer's balance strictly represents settled revenue credited via `release_escrow()`. Seeding zero allows automated verification that delivery confirmation increases the balance from exactly 0 to the purchase amount.
  - **Option B**: Seed `tahir_farmer` with `500,000.00 PKR`.
- **Scrum Master Determination**:
  - **Status**: **DECIDED — APPROVED BY SCRUM MASTER**
  - **Decision**: **Option A** (Seed `tahir_farmer` with `0.00 PKR` in `farmer_wallets`, preserving strict financial accounting integrity).
  - **Date**: **2026-11-14**

---

### Decision D-INC2-08: Batch ID Generation Algorithmic Specification
- **Context**: Plan §5.1 adds `batch_id TEXT UNIQUE` to `listings`.
- **Question**: What is the exact algorithmic generation rule for `batch_id` when a farmer creates or updates a listing with commercial pricing?
- **Options**:
  - **Option A (Recommended & Amended)**: Deterministic template `BATCH-{YEAR}-{CROP_CODE3}-{LISTING_ID:04d}` (e.g., `BATCH-2026-WHT-0001` where `WHT` is the 3-letter uppercase abbreviation of `crop_name`, and `LISTING_ID` is zero-padded to 4 digits). Complete 8-crop taxonomy mapping: Wheat `WHT`, Rice `RIC`, Tomato `TOM`, Potato `POT`, Cotton `COT`, Maize `MAI`, Sugarcane `SUG`, Other `OTH`.
  - **Option B**: Random alphanumeric string `BATCH-{YEAR}-{RANDOM_HEX8}`.
- **Scrum Master Determination**:
  - **Status**: **DECIDED — APPROVED BY SCRUM MASTER**
  - **Decision**: **Option A as amended** (Template `BATCH-{YEAR}-{CROP_CODE3}-{LISTING_ID:04d}` with the full 8-crop code table defined in FR-PRC-003).
  - **Date**: **2026-11-14**

---

### Decision D-INC2-09: Telemetry Cache Invalidation & SQLite Housekeeping Policy
- **Context**: Plan §5.2 establishes `telemetry_cache` with a 6-hour TTL (`expires_at`).
- **Question**: How and when should expired telemetry records be purged from `agrigrid.db`?
- **Options**:
  - **Option A (Recommended)**: **Lazy Overwrite + Startup Purge**: On runtime coordinate lookups, if an entry exists but is expired, update that specific record in-place with the fresh payload and new `expires_at`. Additionally, execute `DELETE FROM telemetry_cache WHERE expires_at < CURRENT_TIMESTAMP` once during Flask application startup (`app.py:create_app()`). Requires zero background threads or OS crons.
  - **Option B**: Active background daemon thread running an hourly purge loop.
- **Scrum Master Determination**:
  - **Status**: **DECIDED — APPROVED BY SCRUM MASTER**
  - **Decision**: **Option A** (Lazy on-read overwrite plus single startup purge in `app.py:create_app()`).
  - **Date**: **2026-11-14**

---

### Decision D-INC2-10: Cold-Chain Maximum Temperature Constraint Validation Range
- **Context**: Plan §5.2 and §6.2 define `max_temperature_celsius REAL NOT NULL DEFAULT 8.0` in `orders`.
- **Question**: What are the strict numerical boundaries enforced by the backend on `max_temperature_celsius` during escrow checkout (`POST /api/orders`)?
- **Options**:
  - **Option A (Recommended)**: Range from `-25.0°C` to `+30.0°C`. Accommodates deep-frozen produce, standard refrigerated cold-chain crops (e.g. tomatoes/fruits at 4–8°C), and ambient ventilated transport up to 30°C.
  - **Option B**: Strict cold-chain range from `0.0°C` to `+15.0°C`.
- **Scrum Master Determination**:
  - **Status**: **DECIDED — APPROVED BY SCRUM MASTER**
  - **Decision**: **Option A** (Range `-25.0°C` to `+30.0°C` validated during checkout in FR-ORD-002).
  - **Date**: **2026-11-14**

---

## 11. Discrepancy & Finding Report (Plan vs. Docs vs. Code)

During baseline analysis and document alignment, the Requirements Agent identified five specific discrepancies between briefing notes, documentation artifacts, and physical repository code:

1. **`asking_price` Backend Column Discrepancy (Critical Grounding Finding)**:
   - *Documentation Note*: Briefings previously referenced `asking_price` as existing on listings as nullable Increment 1 scaffolding.
   - *Physical Code Reality*: Inspection of `backend/database/schema.sql` and `backend/crops.py` confirmed that the column **does not exist** in the physical SQLite table or backend validation logic. It existed only as disabled HTML markup (`<span class="inc2-badge">Inc 2</span>`).
   - *SRS Addendum Treatment*: Accurately specified in `FR-PRC-001` that `asking_price_per_kg` is physically created via migration `002_increment_2_marketplace_escrow_telemetry.sql`.

2. **Crop Status Vocabulary Reality (`crops.py` vs. Planning Notes)**:
   - *Planning Note*: Older planning notes mentioned status `"Expired"`.
   - *Physical Code Reality*: `backend/crops.py` defines `VALID_STATUSES = frozenset(["Active", "Sold", "In Transit", "Delivered", "Withdrawn"])`. `"Expired"` does not exist; `"In Transit"` and `"Delivered"` are established lifecycle constants.
   - *SRS Addendum Treatment*: Corrected in `FR-TAX-003` to match `crops.py` verbatim.

3. **Service Layer Extraction vs. AST Contract Test Conflict**:
   - *Plan §4.2 Text*: Recommended extracting `_validate_crop_payload()` and all database queries from `crops.py` into `services/crop_service.py`.
   - *Physical Code Reality*: `backend/test_frontend_contract.py` (`TC-F1` and `TC-F2`) parses `backend/crops.py` directly using Python's `ast` module, scanning `tree.body` for literal `Assign` targets named `VALID_CROP_NAMES` and `VALID_STATUSES`. Extracting these constants or validation logic out of `crops.py` causes the contract tests to fail.
   - *SRS Addendum Treatment*: Refined in `FR-SRV-002` to require that `VALID_CROP_NAMES`, `VALID_STATUSES`, and `_validate_crop_payload()` remain in `backend/crops.py`, while SQL execution and row serialization move to `crop_service.py`.

4. **Stray 0-Byte Database File Elimination**:
   - *Physical Finding*: An empty 0-byte database artifact previously existed at `backend/agrigrid.db` (caused by running scripts directly from `backend/`), while the active database was located at `backend/database/agrigrid.db`.
   - *Current Reality*: The stray file has been permanently deleted.
   - *SRS Addendum Treatment*: Reaffirmed in Section 1.5 that `backend/database/agrigrid.db` is the sole canonical SQLite database.

5. **Currency Standardization from Dollar ($) to Pakistani Rupee (Rs. / PKR)**:
   - *Physical Finding*: Increment 1 presentation templates (`dashboard.html`, `dashboard.js`) rendered `$` characters.
   - *SRS Addendum Treatment*: Standardized across all Increment 2 requirements (`FR-PRC-004`, `NFR-USE-002`) to **`Rs.` / `PKR`**, matching the domestic Pakistani agricultural domain.

6. **SQLite `ALTER TABLE ADD COLUMN` Constraint Restriction (`batch_id UNIQUE`)**:
   - *Physical Code Reality*: In SQLite 3, attempting to execute `ALTER TABLE listings ADD COLUMN batch_id TEXT UNIQUE;` throws `OperationalError: Cannot add a UNIQUE column` because SQLite does not support inline `UNIQUE` constraints during `ADD COLUMN`.
   - *SRS Addendum Treatment*: Refined in `FR-PRC-001` to add column `batch_id TEXT` and enforce uniqueness via companion statement `CREATE UNIQUE INDEX IF NOT EXISTS idx_listings_batch_id ON listings(batch_id)`.

7. **Order History List Endpoints Specification Gap (`GET /api/orders/*`)**:
   - *Master Plan Trace*: Master Plan §6.2 and §8 define `GET /api/orders/buyer` and `GET /api/orders/farmer` for populating the Buyer Order History Table and Farmer Incoming Orders view.
   - *SRS Addendum Treatment*: Added `FR-ORD-008` and `FR-ORD-009` to Section 5.2 and Section 9, establishing strict RBAC, query parameters (`status`, `page`, `limit`), and payload contracts before sequence diagram drafting.

8. **Telemetry Cache Key Disambiguation (`FR-CCH-002`)**:
   - *Discrepancy*: `FR-CCH-001` defined provider values `'OpenWeatherMap'` / `'SoilGrids'`, while `FR-CCH-002` gave `weather:30.3753:69.3451` as the example key format.
   - *SRS Addendum Treatment*: Clarified in `FR-CCH-002` that the key prefix is `<telemetry_type>` (`weather` for OpenWeatherMap, `soil` for SoilGrids).

---

## 12. Revision History & V&V Approval Block

### 12.1 Revision History

| Version | Date | Author | Description of Changes |
|---|---|---|---|
| **v1.0** | 2026-11-14 | Manahil Sohail (Requirements Engineer) | Initial formal release of Increment 2 SRS Addendum (`AG-SRS-INC2-001`) covering FEAT-INC2-01 through FEAT-INC2-12, migration infrastructure, service extraction boundary, status state machine, telemetry caching, and ungrounded decision list. |
| **v1.1** | 2026-11-14 | Manahil Sohail (Requirements Engineer) | Fact-check fix release: corrected status vocabulary in FR-TAX-003 (`backend/crops.py` alignment); aligned 403 vs 404 RBAC/ownership semantics in FR-SET-001, FR-SET-005, FR-STM-005 per NFR-SEC-002; aligned seed specs in FR-BYR-006, FR-WLT-002, FR-PRC-005 with Phase 1 build spec and migration 002 seed path; incorporated §10 determinations (D-INC2-07 through D-INC2-10 marked DECIDED) including full crop-code table in FR-PRC-003; corrected Plan Trace for `GET /api/wallets/me` in FR-WLT-005; aligned `order_number` scheme to deterministic `ORD-{YYYY}-{ORDER_ID:04d}` in FR-ORD-005; downgraded NFR-PERF-001/002/004 to SHOULD and replaced Locust with local timing assertions; corrected proof checks in FR-SRV-001, FR-SRV-004, FR-MIG-007; annotated marketplace 404 message in FR-MKT-007. |
| **v1.2** | 2026-11-14 | Ameer Muawiyah (Lead Data Architect & Scrum Master) | Pre-Sequence Diagram Baseline Pass: added missing order retrieval requirements FR-ORD-008 (`GET /api/orders/buyer`) and FR-ORD-009 (`GET /api/orders/farmer`); refined FR-PRC-001 to resolve SQLite `ALTER TABLE ADD COLUMN UNIQUE` restriction via unique index; disambiguated telemetry cache key prefix in FR-CCH-002; recorded findings 6–8 in Section 11; approved and signed off for sequence diagrams. |

### 12.2 Verification & Validation Sign-Off

```
================================================================================
AGRI-GRID SOFTWARE ENGINEERING V&V ACCEPTANCE GATE
Stage: Increment 2 Requirements Engineering Track (Deliverable 1 of 3)
Document ID: AG-SRS-INC2-001 v1.2
================================================================================

[X] Requirements Engineer:
    Name:      Manahil Sohail
    Role:      Lead Requirements Engineer
    Signature: M. Sohail
    Date:      2026-11-14
    Status:    SPECIFICATION COMPLETE & LOCKED

[X] Scrum Master & Lead Data Architect:
    Name:      Ameer Muawiyah
    Role:      Project Manager, Scrum Master & Lead Data Architect
    Signature: A. Muawiyah (Verified against Project Docs, Inc 1 & SQLite DDL)
    Date:      2026-11-14
    Status:    FORMALLY APPROVED & PASS SIGNATURE GRANTED (GREEN LIGHT)
================================================================================
```

*End of Increment 2 SRS Addendum — Document ID: AG-SRS-INC2-001 v1.2*
