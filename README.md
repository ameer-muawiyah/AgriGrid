# Agri-Grid: Decentralized Smart Agriculture & Food Security Ecosystem

[![Python 3.12](https://img.shields.io/badge/Python-3.12%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Flask 3.0.3](https://img.shields.io/badge/Framework-Flask_3.0.3-black.svg?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Database SQLite3](https://img.shields.io/badge/Database-SQLite3_WAL-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Security JWT](https://img.shields.io/badge/Security-HS256_JWT_%2B_Bcrypt-red.svg?logo=jsonwebtokens&logoColor=white)](https://jwt.io/)
[![Tailwind CSS](https://img.shields.io/badge/Styling-Tailwind_CSS-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![V-Model V&V](https://img.shields.io/badge/V--Model_V%26V-37%2F37_Pass_(100%25)-brightgreen.svg)]()
[![Lifecycle Status](https://img.shields.io/badge/Increment_1-Certified_%26_Closed-success.svg)]()

> **Agri-Grid** is an end-to-end decentralized smart agriculture and transparent food supply ecosystem. Developed as an advanced Software Engineering project, Agri-Grid integrates **IoT agricultural telemetry**, **predictive yield intelligence**, a **B2B digital escrow marketplace**, **cold-chain logistics monitoring**, **agronomist telemedicine**, and **consumer QR provenance tracking**.

---

## 📌 Table of Contents

- [Project Vision & Core Problem Statement](#-project-vision--core-problem-statement)
- [Architectural Philosophy & Security Principles](#-architectural-philosophy--security-principles)
- [Agile-Incremental Delivery Roadmap](#-agile-incremental-delivery-roadmap)
- [System Architecture & Technology Stack](#-system-architecture--technology-stack)
- [Increment 1 Implementation Highlights](#-increment-1-implementation-highlights)
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
│ Increment 2 │ Demand Side & AI Engine (B2B Escrow)     │ 🚀 UP NEXT    │
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
   * Responsive glassmorphic Farmer Console UI.
2. **Increment 2: Core Data Engine & Demand Side (B2B Marketplace)**  
   *Status: Active / Next Milestone*  
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
│           HTML5  •  CSS3  •  Vanilla JavaScript  •  Tailwind CSS        │
│          [index.html (Auth Portal)]   [dashboard.html (Farmer Console)]  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP / JSON (RESTful)
                                     │ Authorization: Bearer <JWT>
┌────────────────────────────────────▼────────────────────────────────────┐
│                            APPLICATION LAYER                            │
│                 Python 3.12+  •  Flask 3.0.3 Application Factory        │
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
| **Styling** | Tailwind CSS CDN | Latest | Modern agro-tech glassmorphism & responsive grid |
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

## 📂 Repository Directory Structure

```text
AgriGrid/
├── .gitignore                                # Excludes databases, venv, caches, and raw videos
├── README.md                                 # Master project blueprint & documentation
│
├── Architecture Blueprints/                  # Formal Software Engineering Blueprints
│   └── Increment_1/
│       ├── 1_Farmer_Dashboard_SRS.md         # IEEE 830 / ISO 29148 SRS Specification (v1.1)
│       ├── 2_Farmer_Sequence_Diagrams.md     # UML 2.5 Sequence Diagrams (v1.1)
│       ├── 3_Farmer_API_Contracts.md         # Strict JSON Interface Specifications (v1.0)
│       └── SRS_AUDIT_LOG_v1.0_to_v1.1.md     # Traceability log of all architectural fixes
│
├── Documentation/                            # Master Project Specification Documents
│   ├── Project Document 1_ Project Foundation, Scope & SE Methodology.pdf
│   ├── Project Document 2_ Team Matrix Organization & Work Distribution.pdf
│   ├── Project Document 3_ System Architecture, Tech Stack & API Design.pdf
│   ├── Project Document 4_ Role Based Access and Feature Specification.pdf
│   ├── Project Document 5_ End-to-End User Workflows & Data Lifecycle.pdf
│   ├── Project Document 6_ Logical Incremental Breakdown Strategy.md
│   └── Project Document 7_ Increment 1 Deep Dive - Foundation & Farmer Dashboard.md
│
├── backend/                                  # Python / Flask Application Core
│   ├── app.py                                # Flask application factory & auth routes
│   ├── auth.py                               # Security core, password hashing, & JWT decorators
│   ├── crops.py                              # Crop CRUD Blueprint with Zero-Trust multi-tenancy
│   ├── requirements.txt                      # Locked Python dependencies
│   ├── test_auth.py                          # Automated V&V test harness for Auth & RBAC
│   ├── test_crops_api.py                     # Automated V&V test harness for Crop CRUD API
│   └── database/
│       ├── schema.sql                        # ACID 3NF DDL with indexes, triggers, & CHECKs
│       ├── init_db.py                        # Database initializer, seeder, & FK verifier
│       └── agrigrid.db                       # Local SQLite3 database (runtime generated)
│
└── frontend/                                 # Client-Side Presentation Layer
    ├── index.html                            # Auth portal (Sign In & Farmer Registration)
    ├── dashboard.html                        # Farmer Console with crop ledger & metrics
    ├── css/
    │   ├── auth.css                          # Glassmorphic auth styles & animations
    │   └── dashboard.css                     # Agro-tech dashboard styles & modal layouts
    └── js/
        ├── auth.js                           # Form submission, validation, & JWT storage
        └── dashboard.js                      # Table rendering, metrics, & CRUD API handlers
```

---

## 🚀 Quickstart & Local Deployment Guide

Follow these steps to run the complete Agri-Grid application on your local workstation.

### 1. Prerequisites
* **Python 3.10+** (Python 3.12 recommended)
* **Git** installed on your system
* A modern web browser (Google Chrome, Firefox, Safari, or Microsoft Edge)

### 2. Clone the Repository
```powershell
git clone https://github.com/<your-username>/AgriGrid.git
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

### 5. Launch the Backend API Server (Port 5000)
Start the Flask application server in your primary terminal:
```powershell
python backend/app.py
```
The API is live at **`http://127.0.0.1:5000/`**.

### 6. Serve the Frontend Web Application (Port 5500)
Open a **second terminal tab** and run Python's built-in HTTP server from the project directory:
```powershell
python -m http.server 5500 --directory frontend
```
*(Alternatively, if using VS Code, right-click `frontend/index.html` and select **"Open with Live Server"**).*

### 7. Open the Web Application
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
*Results: **15 / 15 Passed (100%)***

### Test Harness 2: Active Crop CRUD Pipeline
Exercises full crop lifecycle (Create, Read, Update, Withdraw), zero-trust tenant isolation, anti-enumeration 404s, agricultural taxonomies, and temporal validations:
```powershell
python backend/test_crops_api.py
```
*Results: **22 / 22 Passed (100%)***

```text
=================================================================
  TOTAL AUTOMATED V&V COMPLIANCE: 37 / 37 TESTS PASS (100%)
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

### Team Distribution Matrix
* **Project Manager & Lead Data Architect:** Ameer Muawiyah
* **Requirements & Architecture Agent:** System modeling, SRS, Sequence Diagrams, API Contracts
* **Database Administrator & Backend Agent:** SQLite schema, WAL configuration, Flask API, JWT Middleware
* **UI/UX & Frontend Agent:** Tailwind CSS implementation, Responsive Layouts, Client API integration
* **Master Integration Hub & CTO:** Cross-domain architectural integrity, V-Model QA orchestration, codebase audits

---

## 📄 License & Ongoing Evolution

This repository is maintained as an active Software Engineering project. 

* **Current Stage:** Increment 1 (Certified & Closed).
* **Next Active Sprint:** **Increment 2 (Core Data Engine & Demand Side — B2B Marketplace, OpenWeatherMap/SoilGrids API Telemetry, and Predictive Yield Forecaster).**

Documentation, blueprints, and code are continuously synchronized with our single source of truth across all five increments.
