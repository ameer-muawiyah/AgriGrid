# Agri-Grid: Decentralized Smart Agriculture & Food Security Ecosystem

[![Python 3.12](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask 3.0.3](https://img.shields.io/badge/Framework-Flask_3.0.3-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Database SQLite3](https://img.shields.io/badge/Database-SQLite3_WAL-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Security JWT](https://img.shields.io/badge/Security-HS256_JWT_%2B_Bcrypt-red.svg?logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Styling: CSS3](https://img.shields.io/badge/Styling-CSS3_Design_Tokens-1572B6.svg?logo=css3&logoColor=white)]()
[![V-Model V&V](https://img.shields.io/badge/V--Model_V%26V-98%2F98_Pass_(100%25)-brightgreen.svg)]()
[![Lifecycle Status](https://img.shields.io/badge/Increment_2-Certified_%26_Closed-success.svg)]()

> **Agri-Grid** is an end-to-end decentralized smart agriculture and transparent food supply ecosystem. Developed as an advanced Software Engineering project, Agri-Grid integrates **IoT agricultural telemetry**, **predictive yield intelligence**, a **B2B digital escrow marketplace**, **cold-chain logistics monitoring**, **agronomist telemedicine**, and **consumer QR provenance tracking**.

---

## 📌 Table of Contents

- [Project Vision & Core Problem Statement](#-project-vision--core-problem-statement)
- [Architectural Philosophy & Security Principles](#-architectural-philosophy--security-principles)
- [Agile-Incremental Delivery Roadmap](#-agile-incremental-delivery-roadmap)
- [System Architecture & Technology Stack](#-system-architecture--technology-stack)
- [Increment 1 Implementation Highlights](#-increment-1-implementation-highlights)
- [Increment 2 Implementation Highlights](#-increment-2-implementation-highlights)
- [Repository Directory Structure](#-repository-directory-structure)
- [Quickstart & Local Deployment Guide](#-quickstart--local-deployment-guide)
- [Pre-Seeded Demonstration Accounts](#-pre-seeded-demonstration-accounts)
- [Automated Verification & Validation (V-Model)](#-automated-verification--validation-v-model)
- [Increment 1 API Contract Reference](#-increment-1-api-contract-reference)
- [Academic Project Governance & Team Matrix](#-academic-project-governance--team-matrix)
- [License & Ongoing Evolution](#-license--ongoing-evolution)

---

## 🌍 Project Vision & Core Problem Statement

Modern food supply chains suffer from severe systemic vulnerabilities that jeopardize regional food security, impoverish smallholder farmers, and obscure food safety from consumers:

1. **Opaque Provenance:** Lack of end-to-end traceability enables counterfeit certifications, illegal food adulteration, and untraceable contamination outbreaks.
2. **Post-Harvest Spoilage:** Fragile, unmonitored cold-chain transport networks result in over 30% produce loss before reaching commercial hubs.
3. **Exploitative Intermediary Networks:** Fragmented middleman chains extract up to 60% of crop value, leaving farmers with low margins.
4. **Predictive Yield Blindness:** Farmers lack localized soil, weather, and historical predictive data to forecast harvest timelines and volume.

### The Agri-Grid Solution
Agri-Grid re-engineers this pipeline from the ground up through a cohesive 5-tier architecture:
* **Provenance Ledger:** High-precision field registration with sub-meter GPS anchoring and immutable soft-delete audit trails.
* **Predictive Yield Forecaster:** Mathematical yield estimation fusing OpenWeatherMap and SoilGrids APIs.
* **B2B Digital Escrow:** Contractual multi-party escrow releasing payments only upon verified digital custody transfer.
* **IoT Cold-Chain Telemetry:** In-transit sensor monitoring logging thermal and humidity stability with offline failover.
* **Consumer Transparency:** Instant QR scan access rendering complete farm-to-table storyboards for retail buyers.

---

## 🛡️ Architectural Philosophy & Security Principles

Agri-Grid adheres to strict Software Engineering and Information Security standards throughout all increments:

* **Zero-Trust Multi-Tenancy:**
  The frontend client is never trusted to identify its tenant identity. In crop CRUD operations, client bodies **must never** supply `farmer_id` or `user_id`. The backend extracts tenant identity exclusively from cryptographically verified JWT claims (`g.farmer_id`).
* **Cross-Tenant Anti-Enumeration Defense (CTO Gap 3 Fix):**
  Single-resource endpoints (`/api/crops/{listing_id}`) return a uniform `HTTP 404 Not Found` for both non-existent IDs and records belonging to other farmers. This prevents malicious actors from scanning integer IDs to map competitor crop distributions.
* **Soft-Delete Provenance Architecture (CTO Blocker 3 Fix):**
  Physical SQL `DELETE` queries on the `listings` table are strictly prohibited. Deletion is executed as an archival state transition (`is_deleted = 1`, `status = 'Withdrawn'`). This guarantees foreign key lineage remains intact for downstream escrow contracts, transport logs, and consumer QR storyboards in Increments 2–5.
* **Atomic Transaction Integrity (CTO Blocker 1 Fix):**
  Multi-table operations (e.g., creating a `users` record and linked `farmers` profile on registration) are wrapped in explicit database transactions (`BEGIN` $\rightarrow$ `COMMIT` / `ROLLBACK`). If any step fails, the entire transaction rolls back, preventing orphaned user accounts.
* **Dual-Scheme Cryptographic Engine:**
  Production authentication uses industry-standard `bcrypt` (12 rounds) with OWASP-compliant complexity validation. The system maintains backward compatibility with standard-library `PBKDF2-HMAC-SHA256` for deterministic local prototype seeding.

---

## 🗺️ Agile-Incremental Delivery Roadmap

Agri-Grid follows a disciplined **Agile-Incremental Hybrid Model** coupled with the **V-Model for Verification and Validation (V&V)**. Foundational data layers precede complex analytical and e-commerce layers.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AGRI-GRID 5-INCREMENT ROADMAP                   │
├─────────────┬──────────────────────────────────────────┬───────────────┤
│ Increment   │ Focus & Domain Modules                   │ Status        │
├─────────────┼──────────────────────────────────────────┼───────────────┤
│ Increment 1 │ Foundation & Supply Side (Farmer Portal) │ ✅ CERTIFIED  │
│ Increment 2 │ Demand Side & AI Engine (B2B Escrow)     │ ✅ CERTIFIED  │
│ Increment 3 │ Physical Bridge (Logistics & Cold-Chain) │ 📅 PLANNED    │
│ Increment 4 │ Auditing (Agronomist & Compliance)       │ 📅 PLANNED    │
│ Increment 5 │ Consumer Transparency (Public QR Portal) │ 📅 PLANNED    │
└─────────────┴──────────────────────────────────────────┴───────────────┘
```

### Detailed Increment Breakdown
1. **Increment 1: Foundation & The Supply Side (Farmer Dashboard)**  
   *Status: Complete & Certified*  
   * Core RBAC security gateway (stateless HS256 JWT, route decorators).
   * ACID-compliant 3NF SQL schema (`users`, `farmers`, `listings`).
   * Active Crop CRUD ledger with standardized taxonomy whitelists and temporal date boundary validations.
   * Responsive Terra × Terracotta Farmer Console UI.
2. **Increment 2: Core Data Engine & Demand Side (B2B Marketplace)**  
   *Status: Complete & Certified*  
   * External Telemetry Integration: OpenWeatherMap (ambient weather) & SoilGrids (pH, organic carbon, soil moisture).
   * Algorithmic Predictive Yield Engine.
   * B2B Buyer marketplace catalog & digital escrow checkout logic.
3. **Increment 3: The Physical Bridge (Transporter & Logistics Tracker)**  
   * Mobile-first Transporter console with camera-based QR custody handshake.
   * Cold-chain sensor telemetry logger with offline HTML5 flash caching.
   * Automated spoilage risk alerts based on thermal thresholds.
4. **Increment 4: Specialized Auditing (Agronomist & Compliance Officer)**  
   * Agronomist telemedicine queue & digital prescription pad.
   * Sustainability Compliance Verification Engine (satellite/weather cross-audits for water and pesticide grants).
   * Immutable financial grant disbursement ledger.
5. **Increment 5: Final V&V & Public Transparency (Consumer QR Storyboard)**  
   * Unauthenticated public QR landing page for retail packaging.
   * Dynamic Farm-to-Table interactive visual storyboard rendering the entire provenance chain.
   * Global end-to-end V-Model system integration testing.

---

## 💻 System Architecture & Technology Stack

Agri-Grid utilizes a decoupled, modern multi-tier web architecture:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                            │
│    HTML5  •  CSS3  •  Vanilla JavaScript  •  Custom CSS (Design Tokens)    │
│          [index.html (Auth Portal)]   [dashboard.html (Farmer Console)]  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP / JSON (RESTful)
                                     │ Authorization: Bearer <JWT>
┌────────────────────────────────────▼────────────────────────────────────┐
│                            APPLICATION LAYER                            │
│                 Python 3.10+  •  Flask 3.0.3 Application Factory        │
│    ┌───────────────────────────────┬───────────────────────────────┐    │
│    │  auth.py (Security Core)      │  crops.py (Crop Blueprint)    │    │
│    │  - Bcrypt / PBKDF2 hashing    │  - Zero-Trust validation      │    │
│    │  - JWT HS256 issuance         │  - Agricultural taxonomy      │    │
│    │  - @token_required decorator  │  - Temporal logic cascade     │    │
│    │  - @role_required decorator   │  - Two-query pagination       │    │
│    └───────────────────────────────┴───────────────────────────────┘    │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ SQLite3 Native Driver
                                     │ PRAGMA foreign_keys = ON; WAL Mode
┌────────────────────────────────────▼────────────────────────────────────┐
│                            PERSISTENCE LAYER                            │
│     SQLite 3 Database (agrigrid.db) — Normalization: 3NF                │
│     [users table] <1──1> [farmers table] <1──0..*> [listings table]     │
│     Performance Indexes: idx_users_username, idx_listings_farmer_active│
│     Trigger: trg_listings_updated_at (Automatic UTC ISO-8601 timestamps)│
└─────────────────────────────────────────────────────────────────────────┘
```

### Stack Components

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **Frontend** | HTML5 / CSS3 / ES6+ | — | Native DOM performance, Zero heavyweight JS frameworks |
| **Styling** | Vanilla CSS3 (Custom Properties) | — | Terra × Terracotta hybrid design system; token-driven theming, no CSS framework |
| **Backend** | Python Flask | 3.0.3 | Lightweight, deterministic RESTful application factory |
| **CORS** | Flask-CORS | 4.0.1 | Controlled cross-origin access between ports 5500 & 5000 |
| **Security** | PyJWT | 2.8.0 | Cryptographic HS256 stateless session tokens |
| **Cryptography**| Bcrypt | 4.1.3 | Industry-standard password hashing with individual salts |
| **Database** | SQLite 3 | 3.x | Zero-config ACID local prototype running in WAL mode |
| **Testing** | Requests | 2.32.3 | Standalone automated end-to-end integration test harnesses |

---

## ✨ Increment 1 Implementation Highlights

### 1. Robust RBAC Gateway & Auth Flow
* **Supported System Roles:** `farmer`, `buyer`, `transporter`, `agronomist`, `compliance_officer`.
* **Registration Validation:** `farm_name` is mandatory for farmer roles. Triggers an atomic multi-table transaction creating both `users` and `farmers` rows simultaneously.
* **Single-Query Login:** Authenticates and retrieves `farmer_id` in a single `LEFT JOIN` query, halving database roundtrip latency to meet `NFR-PERF-001` ($p95 < 1\text{s}$ under 50 concurrent requests).

### 2. Zero-Trust Active Crop CRUD Engine
* **Creation (`POST /api/crops`):** Enforces an approved crop taxonomy whitelist (`Wheat`, `Rice`, `Tomato`, `Potato`, `Cotton`, `Maize`, `Sugarcane`, `Other`).
* **Temporal Validation Cascade:**
  * $\text{planting\_date} \le \text{CURRENT\_DATE}$ (no future planting dates).
  * $\text{planting\_date} \ge \text{CURRENT\_DATE} - 365\text{ days}$ (active listings must be within 1 calendar year).
  * $\text{estimated\_harvest\_date} > \text{planting\_date}$ (harvest must strictly follow planting).
* **Two-Query Pagination (`GET /api/crops?page=1&limit=20`):** Companion query `COUNT(*)` returns total count metadata alongside paginated data rows.
* **Unified 404 Protection:** Single-resource endpoints return `404 Not Found` for foreign tenant records, blocking integer ID scanning attacks.
* **Soft-Delete Archive (`DELETE /api/crops/{id}`):** Issues SQL `UPDATE` setting `is_deleted = 1` and `status = 'Withdrawn'`. Hard physical row deletion is barred.

---

## 🌾 Increment 2 Implementation Highlights

### 1. B2B Marketplace & Digital Escrow System
* **Commercial Produce Listings (`GET /api/marketplace/listings`):** Dynamic marketplace catalog with multi-field search and filtering by crop variety, maximum asking price, and price sorting, backed by automated zero-padded batch generation (`BATCH-YYYY-CROP-ID`).
* **Digital Escrow State Machine (`/api/orders`):** Four-boundary checkout validation rules; atomic buyer wallet debit on order creation (`HELD`), automated delivery settlement to farmer wallet (`RELEASED`), mutual buyer/farmer order cancellation with immediate refund (`REFUNDED`), and dispute locking (`DISPUTED`) with exact 72-hour auto-release timers.
* **Buyer Onboarding & Pre-Funded Accounts:** Dedicated buyer profile registration with 500,000 PKR virtual ledger balance for testing and procurement workflows.

### 2. Environmental Telemetry & Deterministic Yield Forecaster
* **Telemetry Fusion Engine (`/api/telemetry/weather`, `/api/telemetry/soil`):** Real-time integration with OpenWeatherMap (ambient temperature, humidity, precipitation, solar radiation) and SoilGrids (soil moisture, organic carbon, pH, texture), coupled with an offline fixture engine and a 6-hour SQLite caching layer (`telemetry_cache`) for deterministic, network-resilient offline execution.
* **Predictive Yield Forecaster (`POST /api/yield/predict`):** Mathematical yield forecasting algorithm parameterized across all 8 crop taxonomies, applying environmental indices and outputting actionable agronomic recommendations and estimated harvest timelines.

### 3. Role-Based Navigation & Page-Split Architecture
* **Decoupled Operator Consoles:** Split monolithic layouts into focused, role-specific views for clear separation of concerns:
  * **Farmer Console** (`dashboard.html`): Farm crop lifecycle management, metrics, and new crop registration.
  * **Farmer Incoming Orders** (`farmer_orders.html`): Fulfillment tracking, status filtering, and order cancellation.
  * **Buyer Marketplace** (`buyer_dashboard.html`): Produce catalog discovery, search/filtering, and modal checkout.
  * **Buyer Purchase Orders** (`buyer_orders.html`): Purchase order tracking, delivery confirmation, and dispute initiation.
* **Farmer Wallet & Balance Visibility (`GET /api/farmer/wallet`):** Dedicated read-only wallet endpoint and live UI balance badge surfacing accumulated sales revenue to verified farmers upon order completion.
* **Interactive Leaflet Map Pin-Drop Location Picker:** Embedded interactive satellite map with default Peshawar view (`[34.0151, 71.5249]`), allowing farmers to select parcel coordinates with a pin-drop.

### 4. Verification & Validation Gate
* Certified at **98/98 tests passing across 7 automated test suites (100% green)**:
  * Authentication & RBAC (`test_auth.py`): **17 / 17**
  * Crop CRUD Engine (`test_crops_api.py`): **23 / 23**
  * Frontend Contract Lock (`test_frontend_contract.py`): **5 / 5**
  * Marketplace & Pricing (`test_marketplace_api.py`): **20 / 20**
  * Escrow Orders & Settlement (`test_escrow_orders.py`): **18 / 18**
  * Telemetry & Predictive Yield (`test_yield_telemetry.py`): **11 / 11**
  * Farmer Wallet API (`test_farmer_wallet.py`): **4 / 4**

---

## 📂 Repository Directory Structure

```text
AgriGrid/
├── .gitignore                                # Excludes databases, venv, caches, and raw videos
├── README.md                                 # Master project blueprint & documentation
├── FRONTEND_CHANGE_CHECKLIST.md              # Standing checklist for frontend modifications
├── FRONTEND_RESKIN_AUDIT_REPORT.md           # Reskin security, consistency & audit report
├── launch_agrigrid.py                        # Unified one-click application launcher
├── start-agri-grid.bat                       # One-click launch script (Windows)
├── start-agri-grid.sh                        # One-click launch script (macOS/Linux)
│
├── Architecture Blueprints/                  # Formal Software Engineering Blueprints
│   ├── Increment_1/
│   │   ├── 1_Farmer_Dashboard_SRS.md         # IEEE 830 / ISO 29148 SRS Specification (v1.1)
│   │   ├── 2_Farmer_Sequence_Diagrams.md     # UML 2.5 Sequence Diagrams (v1.1)
│   │   ├── 3_Farmer_API_Contracts.md         # Strict JSON Interface Specifications (v1.0)
│   │   ├── 4_Increment_1_QA_Test_Plan.md     # V-Model QA test plan
│   │   ├── INCREMENT_1_INTEGRATION_REPORT.md # Integration & verification report
│   │   └── SRS_AUDIT_LOG_v1.0_to_v1.1.md     # Traceability log of all architectural fixes
│   └── Increment_2/
│       ├── 0_Increment_2_Master_Plan.md      # Increment 2 Master Architectural Plan (v1.1)
│       ├── 1_Increment_2_SRS_Addendum.md     # SRS Addendum for B2B Escrow & Yield Engine (v1.3)
│       ├── 2_Increment_2_Sequence_Diagrams.md# UML 2.5 Sequence Diagrams for Increment 2 (v1.1)
│       ├── 3_Increment_2_API_Contracts.md    # API Contracts Delta specification (v1.2)
│       └── INCREMENT_2_INTEGRATION_REPORT.md # Master Integration & V&V Report (Parts I–VI)
│
├── Documentation/                            # Master Project Specification Documents
│   ├── Project Document 1_ Project Foundation, Scope & SE Methodology.pdf
│   ├── Project Document 2_ Team Matrix Organization & Work Distribution.pdf
│   ├── Project Document 3_ System Architecture, Tech Stack & API Integrations.pdf
│   ├── Project Document 4_Role Based Access and Feature Specifications.pdf
│   ├── Project Document 5_ End-to-End User Workflows & Data Lifecycle.pdf
│   ├── Project Document 6_ Logical Incremental Breakdown Strategy.md
│   ├── Project Document 7_ Increment 1 Deep Dive - Foundation & Farmer Dashboard.md
│   ├── Increment_2_SRS_Addendum.md           # Increment 2 SRS Addendum specification
│   ├── Increment_2_Sequence_Diagrams.md      # Increment 2 UML 2.5 sequence models
│   └── Increment_2_API_Contracts_Delta.md    # Increment 2 API Contracts Delta specification
│
├── backend/                                  # Python / Flask Application Core
│   ├── app.py                                # Flask application factory & auth routes
│   ├── auth.py                               # Security core, password hashing, & JWT decorators
│   ├── crops.py                              # Crop CRUD Blueprint with Zero-Trust multi-tenancy
│   ├── marketplace.py                        # B2B marketplace catalog & commercial pricing Blueprint
│   ├── orders.py                             # Escrow order lifecycle & dispute Blueprint
│   ├── telemetry.py                          # Environmental telemetry (weather/soil) Blueprint
│   ├── wallet.py                             # Farmer read-only wallet Blueprint
│   ├── yield.py                              # Deterministic predictive yield forecasting Blueprint
│   ├── requirements.txt                      # Locked Python dependencies
│   ├── test_auth.py                          # Automated V&V test harness for Auth & RBAC
│   ├── test_crops_api.py                     # Automated V&V test harness for Crop CRUD API
│   ├── test_frontend_contract.py             # Frontend-backend contract & drift verification
│   ├── test_marketplace_api.py              # Automated V&V test harness for Marketplace & Pricing
│   ├── test_escrow_orders.py                 # Automated V&V test harness for Escrow & Orders
│   ├── test_yield_telemetry.py               # Automated V&V test harness for Telemetry & Yield
│   ├── test_farmer_wallet.py                 # Automated V&V test harness for Farmer Wallet API
│   ├── database/
│   │   ├── schema.sql                        # ACID 3NF DDL with indexes, triggers, & CHECKs
│   │   ├── init_db.py                        # Database initializer, seeder, & FK verifier
│   │   ├── migrate.py                        # Sequential migration runner (v1 -> v2 -> v3)
│   │   ├── agrigrid.db                       # Local SQLite3 database (runtime generated)
│   │   └── migrations/
│   │       ├── 001_increment_1_baseline.sql  # Baseline schema migration
│   │       ├── 002_increment_2_marketplace_escrow_telemetry.sql # Escrow, orders, & telemetry tables
│   │       └── 003_buyers_legacy_profile.sql # Backward-compatible buyer profile columns
│   └── services/                             # Core Domain & Business Logic Services
│       ├── buyer_service.py                  # Buyer profile & onboarding logic
│       ├── crop_service.py                   # Crop domain rules, validation & queries
│       ├── escrow_service.py                 # Escrow ledger, wallet transfers & balance queries
│       ├── marketplace_service.py            # Produce catalog search, filter & pricing logic
│       ├── order_service.py                  # Order state machine transitions & validations
│       ├── telemetry_service.py              # Weather/soil API fetching & 6h cache management
│       └── yield_service.py                  # Deterministic mathematical yield algorithm
│
└── frontend/                                 # Client-Side Presentation Layer
    ├── index.html                            # Auth portal (Sign In & Farmer Registration)
    ├── dashboard.html                        # Farmer Console with crop ledger & metrics
    ├── farmer_orders.html                    # Farmer incoming orders & fulfillment console
    ├── buyer_dashboard.html                  # Buyer marketplace browse, filter & checkout
    ├── buyer_orders.html                     # Buyer purchase orders & escrow status console
    ├── css/
    │   ├── auth.css                          # Auth styles — Terra × Terracotta design system
    │   ├── buyer.css                         # Buyer marketplace & order styles
    │   └── dashboard.css                     # Dashboard styles — tables, filters & modal layouts
    ├── img/
    │   └── wheat-sunset.jpg                  # Hero photograph
    └── js/
        ├── auth.js                           # Form submission, validation, & JWT storage
        ├── buyer.js                          # Marketplace catalog browsing & checkout modal
        ├── buyer_orders.js                   # Buyer order tracking, delivery confirmation & disputes
        ├── dashboard.js                      # Farmer crop CRUD, metrics & Leaflet map pin-drop
        └── farmer_orders.js                  # Farmer incoming orders, fulfillment & cancellation
```

---

## 🚀 Quickstart & Local Deployment Guide

Follow these steps to run the complete Agri-Grid application on your local workstation.

### ⚡ One-Click Launch (Recommended)
> **One-click launch (recommended):** double-click `start-agri-grid.bat` (Windows) or run `./start-agri-grid.sh` (macOS/Linux). It installs dependencies and creates the database on first run, starts both servers, and opens the app in your browser. Close the launcher window to stop everything. The manual steps below remain available for development.

### 1. Prerequisites
* **Python 3.10+** (Python 3.12 recommended)
* **Git** installed on your system
* A modern web browser (Google Chrome, Firefox, Safari, or Microsoft Edge)

### 2. Clone the Repository
```powershell
git clone https://github.com/ameer-muawiyah/AgriGrid.git
cd AgriGrid
```

### 3. Create Virtual Environment & Install Dependencies
```powershell
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

# Install locked dependencies
pip install -r backend/requirements.txt
```

### 4. Initialize & Seed the Database
Initialize the SQLite schema, triggers, indexes, and test accounts:
```powershell
python backend/database/init_db.py
```
*Expected output:*
```text
============================================================
  AGRI-GRID DB INITIALIZER  —  Increment 1
============================================================
[OK]    Schema executed from: .../backend/database/schema.sql
[SEED]  Inserting users …
[SEED]  Inserting farmer profiles …
[SEED]  Inserting crop listings …
[OK]    Seed transaction committed successfully.
============================================================
```

> [!NOTE]
> Database schema changes require deleting `backend/database/agrigrid.db` (and any associated `-wal` / `-shm` files) and re-running `python backend/database/init_db.py`, as the SQLite database is runtime-generated, git-ignored, and has no automated migration runner in Increment 1.

### 5. (Optional) Configure Live Weather Telemetry
Agri-Grid operates deterministically on built-in offline telemetry fixtures by design, requiring no external network access or API keys for local development and automated testing. To enable live ambient weather queries:
```powershell
# Optional: Set OpenWeatherMap API key (free key from https://openweathermap.org/)
# Windows (PowerShell):
$env:OPENWEATHER_API_KEY="your_api_key_here"
# Linux / macOS:
# export OPENWEATHER_API_KEY="your_api_key_here"
```
*Note: Soil telemetry (SoilGrids) requires no API key and operates out of the box.*

### 6. Launch the Backend API Server (Port 5000)
Start the Flask application server in your primary terminal:
```powershell
python backend/app.py
```
The API is live at **`http://127.0.0.1:5000/`**.

### 7. Serve the Frontend Web Application (Port 5500)
Open a **second terminal tab** and run Python's built-in HTTP server from the project directory:
```powershell
python -m http.server 5500 --directory frontend
```
*(Alternatively, if using VS Code, right-click `frontend/index.html` and select **"Open with Live Server"**).*

### 8. Open the Web Application
Open your browser and navigate to:  
👉 **[http://127.0.0.1:5500/](http://127.0.0.1:5500/)** (or `http://localhost:5500/`)

---

## 🔑 Pre-Seeded Demonstration Accounts

The local database comes pre-seeded with sample actor credentials for immediate testing:

| Role | Username | Password | Purpose & Expected Behavior |
|---|---|---|---|
| 👨‍🌾 **Farmer** | `tahir_farmer` | `FarmSecure1` | **Full CRUD Access:** Enters the Farmer Dashboard, calculates telemetry metrics, and manages active crop listings. |
| 🏪 **B2B Buyer** | `sara_buyer` | `BuyerPass1` | **RBAC Guard Demo:** Successfully logs in, but is blocked with `HTTP 403 Forbidden` if attempting to enter the Farmer Dashboard. |

*You can also click **"Register as Farmer"** on the login page to register a new farm node with custom credentials in real time.*

---

## 🧪 Automated Verification & Validation (V-Model)

Agri-Grid implements automated testing to ensure all functional requirements, security boundaries, and validation rules remain certified.

### Test Harness 1: Authentication & RBAC Engine
Exercises user registration, password complexity, duplicate rejections, PBKDF2 backward compatibility, JWT generation, and route guards:
```powershell
python backend/test_auth.py
```
*Results: **17 / 17 Passed (100%)***

### Test Harness 2: Active Crop CRUD Pipeline
Exercises full crop lifecycle (Create, Read, Update, Withdraw), zero-trust tenant isolation, anti-enumeration 404s, agricultural taxonomies, and temporal validations:
```powershell
python backend/test_crops_api.py
```
*Results: **23 / 23 Passed (100%)***

### Test Harness 3: Frontend–Backend Contract
Verifies the frontend cannot drift from the backend contract — crop taxonomy and status-filter options equal the backend whitelists (parsed from `crops.py`), every CSS class used in HTML/JS is defined, every JS element ID exists in the markup, and SRS-pinned copy is byte-exact. Standalone; needs no running server:
```powershell
python backend/test_frontend_contract.py
```
*Results: **5 / 5 Passed (100%)***

### Test Harness 4: B2B Marketplace & Commercial Pricing API
Exercises buyer registration and onboarding, 500,000 PKR initial wallet balance, marketplace catalog search, filtering by crop and price, sort ordering, single listing detail, and atomic batch generation:
```powershell
python backend/test_marketplace_api.py
```
*Results: **20 / 20 Passed (100%)***

### Test Harness 5: Escrow Orders & Settlement Engine
Exercises full escrow order state transitions (creation, buyer delivery confirmation, buyer/farmer cancellation, disputes), 4 checkout validation rules, auto-release timers (+72h), and buyer/farmer order history:
```powershell
python backend/test_escrow_orders.py
```
*Results: **18 / 18 Passed (100%)***

### Test Harness 6: Environmental Telemetry & Yield Forecaster
Exercises ambient weather and soil data fetching, coordinate validation, 6-hour cache TTL and refresh mechanics, key independence, and deterministic yield prediction across all 8 crop varieties:
```powershell
python backend/test_yield_telemetry.py
```
*Results: **11 / 11 Passed (100%)***

### Test Harness 7: Farmer Wallet & Revenue API
Exercises farmer wallet balance retrieval (`GET /api/farmer/wallet`), zero-balance initial state, exact balance accumulation upon delivery confirmations, and strict RBAC guards:
```powershell
python backend/test_farmer_wallet.py
```
*Results: **4 / 4 Passed (100%)***

```text
=================================================================
  TOTAL AUTOMATED V&V COMPLIANCE: 98 / 98 TESTS PASS (100%)
=================================================================
```

---

## 📑 Increment 1 API Contract Reference

All endpoints conform to the Standard JSON Envelope (`AG-API-INC1-003`). Protected routes require the `Authorization: Bearer <token>` header.

| Method | Endpoint | Auth | Role | Description |
|---|---|:---:|:---:|---|
| `POST` | `/api/auth/register` | Public | Any | Registers user; atomically provisions `farmers` profile if role is `farmer`. |
| `POST` | `/api/auth/login` | Public | Any | Verifies credentials via single `LEFT JOIN`; returns HS256 JWT & role. |
| `POST` | `/api/auth/logout` | Token | Any | Session termination acknowledgement; prompts client token purge. |
| `GET` | `/api/auth/me` | Token | Any | Smoke-test route returning authenticated token claims from Flask context. |
| `POST` | `/api/crops` | Token | `farmer` | Creates new crop listing with strict taxonomy & temporal validation. |
| `GET` | `/api/crops` | Token | `farmer` | Retrieves paginated listings owned by caller (`?page=1&limit=20`). |
| `GET` | `/api/crops/stats` | Token | `farmer` | Platform-wide aggregates behind the dashboard metrics (active fields, total acreage, projected yield). |
| `GET` | `/api/crops/{id}` | Token | `farmer` | Retrieves full crop details including sub-meter GPS coordinates. |
| `PUT` | `/api/crops/{id}` | Token | `farmer` | Updates mutable fields with ownership verification (unified 404). |
| `DELETE` | `/api/crops/{id}` | Token | `farmer` | Soft-deletes listing (`is_deleted=1`, `status='Withdrawn'`). |

### Standard Error Envelope Structure
```json
{
  "success": false,
  "error": "Human-readable description of validation failure or security rejection."
}
```

---

## 👥 Academic Project Governance & Team Matrix

* **Institution:** Department of Computer Science / Software Engineering
* **Curriculum:** 3rd Semester Software Engineering (MICT / SE)
* **Delivery Model:** Agile-Incremental Hybrid with V-Model Verification & Validation
* **Single Source of Truth:** `./Documentation` & `./Architecture Blueprints`

### Project / Development Team
* **Scrum Master + Lead Data Architect:** Ameer Muawiyah
* **Requirements Engineer:** Manahil Sohail
* **Core Backend Engineer:** Hasnain Hamza
* **Database Administrator:** Bareera Noor
* **QA & DevOps Engineer:** Muhammad Hashir
* **UI/UX Designer (Frontend):** Manahil Zardad
* **Software Architect and API Designer:** Iqra Fayaz

---

## 📄 License & Ongoing Evolution

This repository is maintained as an active Software Engineering project. 

* **Current Stage:** Increment 2 (Certified & Closed).
* **Next Active Sprint:** Increment 2 closed 2026-11-15 (94/94); the post-increment patch programme (farmer wallet visibility, role-based page split, UI polish, copy cleanup, map pin-drop location picker) closed 2026-11-17 at **98/98**; the next sprint is **Increment 3 (Physical Bridge (Logistics & Cold-Chain))**.

Documentation, blueprints, and code are continuously synchronized with our single source of truth across all five increments.
