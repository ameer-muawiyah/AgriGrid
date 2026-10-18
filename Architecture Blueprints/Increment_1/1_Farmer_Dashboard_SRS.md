# Software Requirements Specification (SRS)
## Increment 1: Foundation & The Farmer Dashboard

| Field               | Value                                                        |
|---------------------|--------------------------------------------------------------|
| **Project Name**    | Agri-Grid: Smart Agriculture & Food Security Ecosystem       |
| **Document ID**     | `AG-SRS-INC1-001`                                            |
| **Version**         | 1.1                                                          |
| **Prepared By**     | Requirements & Architecture Agent (Lead Requirements Engineer) |
| **Reviewed By**     | Ameer Muawiyah (Project Manager & Lead Data Architect) — CTO Audit Pass |
| **Date**            | 2026-10-11                                                   |
| **Methodology**     | Agile-Incremental Hybrid with V-Model V&V                    |
| **Source Documents** | Master Documents 1–7 (`./Documentation/`)                   |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Functional Requirements — Feature 1: RBAC Login Gateway](#3-functional-requirements--feature-1-rbac-login-gateway)
4. [Functional Requirements — Feature 2: Active Crop CRUD Operations](#4-functional-requirements--feature-2-active-crop-crud-operations)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [RBAC Security Matrix — Role Isolation Model](#6-rbac-security-matrix--role-isolation-model)
7. [Data Dictionary — Increment 1 Database Tables](#7-data-dictionary--increment-1-database-tables)
8. [Error Handling & Invalid Input Specification](#8-error-handling--invalid-input-specification)
9. [Traceability Matrix](#9-traceability-matrix)
10. [Assumptions & Dependencies](#10-assumptions--dependencies)
11. [Glossary](#11-glossary)
12. [Revision History](#12-revision-history)

---

## 1. Introduction

### 1.1 Purpose

This document defines the **complete Functional and Non-Functional Requirements** for **Increment 1** of the Agri-Grid ecosystem. Increment 1 establishes the foundational infrastructure upon which all subsequent increments (B2B Marketplace, Logistics Tracker, Agronomist Console, Compliance Portal, Consumer QR) will be built.

The scope of this SRS is strictly bounded to two system features:

1. **The RBAC Login Gateway** — A secure, role-based authentication system that routes authenticated users to their designated dashboards and denies access to unauthorized resources.
2. **The Farmer Active Crop CRUD** — A complete set of Create, Read, Update, and Delete operations allowing the Farmer actor to manage their active crop listings within the system.

> **Source of Truth:** All requirements in this document are directly derived from, and traceable to, Master Documents 1 through 7 located in the `./Documentation/` directory. No requirement exists in this SRS that is not supported by the master documents.

### 1.2 Document Conventions

| Convention | Meaning |
|---|---|
| **SHALL** | An absolute, mandatory requirement. The system MUST implement this. |
| **SHOULD** | A strongly recommended requirement. Deviation requires PM approval. |
| **MAY** | An optional feature that adds value but is not required for Increment 1 acceptance. |
| `FR-LGN-XXX` | Functional Requirement identifier for the Login Gateway feature. |
| `FR-CRP-XXX` | Functional Requirement identifier for the Crop CRUD feature. |
| `NFR-XXX` | Non-Functional Requirement identifier. |

### 1.3 Intended Audience

| Audience | Usage |
|---|---|
| **Project Manager** (Ameer Muawiyah) | Validate scope alignment with master documents; approve for development. |
| **Database & Backend Agent** (DBA + Core Backend Engineer) | Implement the SQL schemas, backend API endpoints, and RBAC routing logic specified herein. |
| **UI/UX Agent** (Frontend Developer) | Build the Login and Dashboard interfaces that transmit the JSON payloads defined in this document. |
| **Main Workspace Agent** (QA Lead & Integration Hub) | Write V-Model test cases that map 1:1 to each `FR-` and `NFR-` identifier in this document. |

### 1.4 Product Scope

Agri-Grid is a distributed, networked, data-intensive web application designed to modernize and secure the agricultural supply chain by connecting local farming operations directly with B2B wholesale markets, logistics networks, remote agricultural experts, and compliance auditors. It establishes a transparent "Farm-to-Table" pipeline with end-to-end traceability.

**Increment 1 specifically delivers:**
- A secure login gateway implementing RBAC with session token routing.
- The foundational SQL database schema (`Users`, `Farmers`, `Listings` tables).
- A Farmer Dashboard UI for managing active crop data (the system's primary data generation point).

**Increment 1 explicitly does NOT include:**
- Predictive Yield Engine algorithms (Increment 2).
- B2B Marketplace catalog or Escrow logic (Increment 2).
- Transporter/Logistics interfaces (Increment 3).
- Agronomist diagnostic workbench (Increment 4).
- Compliance officer audit logs (Increment 4).
- Consumer QR provenance storyboard (Increment 5).

### 1.5 References

| Document ID | Title | Relevance |
|---|---|---|
| Doc 1 | Project Foundation, Scope & SE Methodology | Project constraints, methodology (Agile-Incremental + V-Model), problem statement. |
| Doc 2 | Team Matrix Organization & Work Distribution | 8 engineering roles, module responsibility mapping. |
| Doc 3 | System Architecture, Tech Stack & API Integrations | Technology stack (Python/Flask/Django, SQL, HTML/CSS/JS), API caching strategy. |
| Doc 4 | Role-Based Access and Feature Specifications | RBAC access levels for all 6 actors, feature specifications per role. |
| Doc 5 | End-to-End User Workflows & Data Lifecycle | SQL data lifecycle for all 4 system workflows. |
| Doc 6 | Logical Incremental Breakdown Strategy | 5-increment sequence and rationale. |
| Doc 7 | Increment 1 Deep Dive — Foundation & Farmer Dashboard | Step-by-step execution plan, agent task delegation, JSON payload requirements. |

---

## 2. Overall Description

### 2.1 Product Perspective

Agri-Grid is a standalone web application. It is not a component of a larger commercial system. It is developed as a core academic deliverable for a 3rd-semester Software Engineering curriculum by a team of 7 members. The system is designed to solve four critical industry problems:

1. **Information Asymmetry** (The Middleman Problem)
2. **Logistical Inefficiencies** (Cold-Chain Failures)
3. **Delayed Diagnostics** (Crop Disease Spread)
4. **Opaque Provenance** (Lack of Traceability)

Increment 1 directly addresses Problem 1 by giving the Farmer a digital ledger to register their supply data into the system.

### 2.2 System Actors (Increment 1 Scope)

The full Agri-Grid ecosystem recognizes **6 system actors**. For Increment 1, only the **Farmer** actor is fully operational. The remaining 5 roles are provisioned in the database schema to support RBAC routing but have no functional dashboard in this increment.

| # | Actor | Increment 1 Status | Access Level (from Doc 4) |
|---|---|---|---|
| 1 | **Farmer** | ✅ **Active** — Full CRUD on crop data | Full CRUD on personal farm data, planting dates, acreage, GPS coordinates. |
| 2 | B2B Buyer | 🔒 Provisioned (schema only) | Read: public catalog. Write: purchase contracts & escrow. |
| 3 | Transporter | 🔒 Provisioned (schema only) | Mobile read: dispatch manifests. Write: delivery status & telemetry. No financial access. |
| 4 | Agronomist | 🔒 Provisioned (schema only) | Read: diagnostic tickets & farm environmental data. Write: prescriptions. Requires manual admin credentialing. |
| 5 | Compliance Officer | 🔒 Provisioned (schema only) | Master read-only audit access. Write: subsidy approve/reject & fund disbursement. |
| 6 | Public Consumer | 🔒 Not implemented | Unauthenticated, read-only access via QR scan. |

### 2.3 Operating Environment

| Constraint | Specification | Source |
|---|---|---|
| Backend Language | Python | Doc 3, §1 |
| Web Framework | Flask or Django | Doc 3, §1 |
| Database | Relational SQL (MySQL, PostgreSQL, or SQLite3 for prototyping) | Doc 3, §1 |
| Frontend | HTML, CSS, JavaScript (vanilla or fetch/axios for API calls) | Doc 3, §1; Doc 7, §3.B |
| Browser Compatibility | Modern browsers (Chrome, Firefox, Safari, Edge — latest 2 versions) | Doc 3, §1 |
| Mobile Responsiveness | All farmer-facing interfaces SHALL be mobile-responsive | Doc 3, §1 |
| Version Control | Git / GitHub with branch protection rules | Doc 3, §2 |
| Testing | PyTest (backend verification), Selenium (frontend validation) | Doc 3, §2 |

### 2.4 Design & Implementation Constraints

| ID | Constraint | Rationale | Source |
|---|---|---|---|
| C-01 | The system SHALL use a relational SQL database with strict schema enforcement. | ACID compliance is mandatory for future financial transactions (escrow, subsidies). NoSQL is explicitly rejected. | Doc 3, §1 |
| C-02 | The system SHALL NOT use a traditional Waterfall development model. | Course requirement mandates modern Agile-Incremental approach. | Doc 1, §1 |
| C-03 | Data isolation SHALL follow a Zero-Trust model from day one. | A Farmer SHALL never see another Farmer's data. Enforced at the SQL query level. | Doc 7, §2 |
| C-04 | The database schema SHALL be normalized. | Prevents data duplication across the 7 planned modules. | Doc 7, §3.C |
| C-05 | The backend SHALL generate session tokens upon successful login. | Stateless HTTP requires token-based session management for RBAC enforcement. | Doc 7, §3.C |

---

## 3. Functional Requirements — Feature 1: RBAC Login Gateway

### 3.1 Feature Description

The RBAC Login Gateway is the single point of entry for all authenticated actors in the Agri-Grid ecosystem. It accepts user credentials, validates them against the `Users` table, determines the user's assigned role, generates a secure session token, and routes the user to their role-specific dashboard endpoint.

> **Critical Constraint (Doc 7, §3.C):** The login route SHALL "securely route valid farmers to `/dashboard/farmer`." In Increment 1, only the Farmer route is functional. All other role routes SHALL return a valid response indicating the dashboard is under construction.

### 3.2 Functional Requirements Table

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **FR-LGN-001** | The system SHALL provide a login page accessible at a public URL (e.g., `/login`). | SHALL | Doc 7, §3.B |
| **FR-LGN-002** | The login page SHALL present two input fields: `username` (or `email`) and `password`. | SHALL | Doc 7, §3.B |
| **FR-LGN-003** | The login page SHALL present a "Login" submit button. | SHALL | Doc 7, §3.B |
| **FR-LGN-004** | Upon form submission, the frontend SHALL transmit a JSON payload to the backend login API endpoint (e.g., `POST /api/auth/login`). | SHALL | Doc 7, §3.B |
| **FR-LGN-005** | The JSON login payload SHALL contain exactly two keys: `username` (string) and `password` (string). | SHALL | Doc 7, §3.A |
| **FR-LGN-006** | The backend SHALL query the `Users` table to verify that a matching `username` exists. | SHALL | Doc 7, §3.C |
| **FR-LGN-007** | The backend SHALL compare the submitted password against the stored hashed password using a secure hashing algorithm (e.g., bcrypt, Argon2). | SHALL | Doc 4, §2.1 (Farmer Access Level); Doc 7, §3.C |
| **FR-LGN-008** | If authentication succeeds, the backend SHALL read the `role` column from the authenticated user's row in the `Users` table. | SHALL | Doc 4, §2.1–2.6 |
| **FR-LGN-009** | If authentication succeeds, the backend SHALL generate a **stateless JWT (JSON Web Token)** signed with a server-side secret key. The JWT payload SHALL contain the following claims: `user_id` (INTEGER), `farmer_id` (INTEGER, nullable — populated only if role is `farmer`), `role` (string), `exp` (Unix timestamp — token expiration). | SHALL | Doc 7, §3.C; CTO Blocker 2 Fix |
| **FR-LGN-010** | The backend SHALL return the signed JWT and the user's `role` to the frontend in the JSON response body: `{ "token": "<jwt_string>", "role": "<role_string>" }`. | SHALL | Doc 7, §3.C |
| **FR-LGN-011** | The frontend SHALL store the JWT in `sessionStorage`. The JWT SHALL NOT be stored in an `HttpOnly` cookie, as the decoupled JS architecture requires programmatic header attachment. Plain `localStorage` MAY be used if `sessionStorage` is impractical, with an acknowledged trade-off in session-persistence scope. | SHALL | CTO Blocker 2 Fix — resolves cookie/header mutual exclusion |
| **FR-LGN-012** | The frontend SHALL use the returned `role` value to redirect the user to their role-specific dashboard URL: `/dashboard/farmer`, `/dashboard/buyer`, `/dashboard/transporter`, `/dashboard/agronomist`, `/dashboard/compliance`. | SHALL | Doc 7, §3.C |
| **FR-LGN-013** | In Increment 1, only the `/dashboard/farmer` route SHALL render a functional dashboard. All other role routes SHALL render a placeholder page stating "Dashboard under construction — available in a future increment." | SHALL | Doc 6, §2 (Increment sequencing) |
| **FR-LGN-014** | If the submitted username does not exist in the `Users` table, the backend SHALL return an HTTP 401 status code with a generic error message: "Invalid credentials." | SHALL | Security best practice; Doc 7, §3.C |
| **FR-LGN-015** | If the submitted password does not match the stored hash, the backend SHALL return an HTTP 401 status code with the same generic error message: "Invalid credentials." | SHALL | Security best practice |
| **FR-LGN-016** | The error message for failed login SHALL NOT distinguish between "user not found" and "wrong password." | SHALL | Security: prevents username enumeration attacks |
| **FR-LGN-017** | If either the `username` or `password` field is empty or missing from the JSON payload, the backend SHALL return an HTTP 400 status code with message: "Username and password are required." | SHALL | Input validation |
| **FR-LGN-018** | The system SHALL provide a registration endpoint (`POST /api/auth/register`). The registration JSON payload SHALL contain: `username` (string, required), `password` (string, required), `role` (string, required), and — **if role is `farmer`** — `farm_name` (string, required). For non-farmer roles, `farm_name` is not required. | SHALL | Doc 7, §3.C; CTO Blocker 1 Fix |
| **FR-LGN-018A** | Upon successful registration of a user with `role = 'farmer'`, the backend SHALL atomically create both a `Users` record **and** a corresponding `Farmers` record within a single database transaction. The `Farmers.farm_name` SHALL be set from the supplied `farm_name` field. If the `Farmers` insert fails, the entire transaction SHALL roll back. This prevents the Foreign Key paradox where a crop `INSERT` references a non-existent `farmer_id`. | SHALL | CTO Blocker 1 Fix — resolves FK registration paradox |
| **FR-LGN-019** | During registration, the system SHALL restrict the selectable roles to the 5 authenticated actor types: `farmer`, `buyer`, `transporter`, `agronomist`, `compliance_officer`. | SHALL | Doc 4, §2.1–2.5 |
| **FR-LGN-020** | The system SHALL NOT allow duplicate usernames. If a registration is attempted with an existing username, the backend SHALL return HTTP 409 with message: "Username already exists." | SHALL | Database integrity |
| **FR-LGN-021** | Upon successful registration, the backend SHALL hash the password before storing it in the `Users` table. Plaintext passwords SHALL NEVER be stored. | SHALL | Security; Doc 7, §3.C |
| **FR-LGN-022** | Every authenticated API request (after login) SHALL include the JWT in the `Authorization` request header using Bearer scheme: `Authorization: Bearer <jwt_string>`. The backend SHALL validate the JWT signature and expiration before processing any request. | SHALL | Doc 7, §3.C; CTO Blocker 2 Fix |
| **FR-LGN-023** | If a request arrives with an expired, invalid, or missing JWT, the backend SHALL return HTTP 401 and redirect the user to the login page. | SHALL | Session security |
| **FR-LGN-024** | The system SHALL provide a logout endpoint (`POST /api/auth/logout`) that instructs the frontend to purge the JWT from client storage. As JWTs are stateless, server-side invalidation is not applicable unless a token blocklist is maintained (deferred to a future increment). | SHALL | Session lifecycle |

### 3.3 JWT Contract Specification

> **v1.1 Addition (CTO Blocker 2 Fix):** This section formally resolves the `HttpOnly cookie` vs. `Authorization: Bearer` ambiguity present in v1.0 and establishes the unambiguous JWT contract binding the frontend and backend agents.

**JWT Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**JWT Payload (Claims):**
```json
{
  "user_id": 42,
  "farmer_id": 7,
  "role": "farmer",
  "exp": 1728700800
}
```
> `farmer_id` is `null` for non-farmer roles. The backend SHALL use `farmer_id` from the token payload for all crop CRUD ownership checks — NOT from the request body.

**Token Transport Protocol:**
- **Storage:** `sessionStorage` key: `agrigrid_token`
- **Transmission:** Every authenticated HTTP request SHALL include the header: `Authorization: Bearer <jwt_string>`
- **Expiration:** 30 minutes of inactivity (configurable via server environment variable `JWT_EXPIRY_MINUTES`)

---


## 4. Functional Requirements — Feature 2: Active Crop CRUD Operations

### 4.1 Feature Description

The Farmer Dashboard is the system's primary data generation point (Doc 6, §2 — "The Farmer is the origin point of the entire system"). It allows authenticated Farmer actors to perform full CRUD operations on their active crop listings. Each listing represents a crop that the farmer is currently cultivating.

> **Zero-Trust Data Isolation (Doc 7, §2):** A farmer SHALL only ever see, modify, or delete their own crop records. The backend SHALL enforce this by filtering all SQL queries with the authenticated user's `farmer_id`.

### 4.2 CREATE — Add New Crop Listing

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **FR-CRP-001** | The Farmer Dashboard SHALL display a clearly labeled button or link: "Add New Crop" (or equivalent). | SHALL | Doc 4, §2.1 (Active Crop Ledger); Doc 7, §3.B |
| **FR-CRP-002** | Clicking "Add New Crop" SHALL present a form with the following input fields: | SHALL | Doc 4, §2.1; Doc 7, §3.A |
| | — `crop_name` (string, required): The name/variety of the crop (e.g., "Wheat", "Tomato"). | | |
| | — `planting_date` (date, required): The date the crop was planted. | | |
| | — `estimated_harvest_date` (date, required): The farmer's estimated harvest date. | | |
| | — `acreage` (decimal, required): The total land area allocated to this crop (in acres or hectares). | | |
| | — `gps_latitude` (decimal, required): The farm's latitude coordinate. | | |
| | — `gps_longitude` (decimal, required): The farm's longitude coordinate. | | |
| | — `quantity_kg` (decimal, required): The estimated or actual quantity in kilograms. | | |
| | — `status` (enum, auto-set): Defaults to `"Active"` on creation. | | |
| **FR-CRP-003** | Upon form submission, the frontend SHALL transmit a JSON payload via `POST /api/crops` to the backend. | SHALL | Doc 7, §3.A, §3.B |
| **FR-CRP-004** | The JSON payload SHALL conform to the following strict structure: | SHALL | Doc 7, §3.A |

```json
{
  "crop_name": "string (required, from standardized list or 'Other')",
  "planting_date": "YYYY-MM-DD (required)",
  "estimated_harvest_date": "YYYY-MM-DD (required)",
  "acreage": "decimal (required, > 0)",
  "gps_latitude": "decimal (required, range: -90 to 90)",
  "gps_longitude": "decimal (required, range: -180 to 180)",
  "quantity_kg": "decimal (required, > 0)"
}
```

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **FR-CRP-004A** | The `crop_name` field SHALL be selected from a standardized enumerated list provided by the frontend (e.g., `["Wheat", "Rice", "Tomato", "Potato", "Cotton", "Maize", "Sugarcane", "Other"]`). The backend SHALL validate that `crop_name` matches one of the allowed values or is `"Other"`. Free-form string entry SHALL NOT be accepted. This prevents API taxonomy mismatches in the Increment 2 Predictive Yield Engine. | SHALL | CTO Gap 1 Fix — crop taxonomy standardization |
| **FR-CRP-005** | The backend SHALL extract the `farmer_id` from the authenticated JWT token claim — NOT from the request body. This prevents a malicious user from creating listings under another farmer's ID. | SHALL | Doc 7, §2 (Zero-Trust) |
| **FR-CRP-006** | The backend SHALL execute an SQL `INSERT` statement into the `Listings` table, linking the new record to the authenticated `farmer_id`. | SHALL | Doc 5, Workflow 1 Step 1 |
| **FR-CRP-006A** | The backend SHALL validate temporal logic before executing the INSERT: (1) `planting_date` SHALL NOT be in the future — i.e., `planting_date <= CURRENT_DATE`. (2) `planting_date` SHALL NOT be older than 365 days from `CURRENT_DATE`. (3) `estimated_harvest_date` SHALL be strictly after `planting_date`. Violations SHALL return HTTP 400 with the specific error message defined in Section 8.3. | SHALL | CTO Gap 2 Fix — temporal boundary validation |
| **FR-CRP-007** | Upon successful creation, the backend SHALL return HTTP 201 with the newly created listing object (including the auto-generated `listing_id`). | SHALL | RESTful convention |
| **FR-CRP-008** | The frontend SHALL display a success notification: "Crop listing created successfully." | SHALL | UX |
| **FR-CRP-009** | The `status` field SHALL be automatically set to `"Active"` by the backend on creation. The farmer SHALL NOT be able to manually set this field during creation. | SHALL | Business logic; Doc 4, §2.1 |

### 4.3 READ — View Crop Listings

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **FR-CRP-010** | The Farmer Dashboard SHALL display a table/list/card view of all crop listings belonging to the authenticated farmer. | SHALL | Doc 4, §2.1 (Active Crop Ledger) |
| **FR-CRP-011** | The dashboard SHALL load the farmer's listings by sending `GET /api/crops?page=1&limit=20` with the JWT Bearer token. The backend SHALL return ONLY listings where `farmer_id` matches the authenticated user AND `is_deleted = FALSE`. The response SHALL include pagination metadata: `{ "data": [...], "page": 1, "limit": 20, "total": <count> }`. | SHALL | Doc 7, §2 (Zero-Trust); Doc 5, Workflow 1; CTO Gap 5 Fix — pagination |
| **FR-CRP-012** | Each listing in the view SHALL display at minimum: `crop_name`, `planting_date`, `estimated_harvest_date`, `acreage`, `quantity_kg`, and `status`. | SHALL | Doc 4, §2.1 |
| **FR-CRP-013** | If the farmer has zero listings, the dashboard SHALL display a friendly empty-state message: "You have no active crops. Click 'Add New Crop' to get started." | SHALL | UX |
| **FR-CRP-014** | The farmer SHALL be able to click on an individual listing to view its full details, including GPS coordinates. | SHALL | Doc 4, §2.1 |
| **FR-CRP-014A** | The system SHALL expose a single-resource query endpoint: `GET /api/crops/{listing_id}`. The backend SHALL return HTTP 200 with the full listing object if the `listing_id` exists and belongs to the authenticated `farmer_id`. If the `listing_id` does not exist, OR belongs to a different farmer, the backend SHALL return HTTP 404 (not 403) to prevent resource enumeration attacks. | SHALL | CTO Blocker 4 Fix + CTO Gap 3 Fix — missing endpoint and enumeration prevention |

### 4.4 UPDATE — Edit Existing Crop Listing

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **FR-CRP-015** | Each listing in the dashboard view SHALL display an "Edit" button or icon. | SHALL | Doc 4, §2.1 (CRUD); Doc 7, §1 |
| **FR-CRP-016** | Clicking "Edit" SHALL populate a form pre-filled with the listing's current values. | SHALL | UX |
| **FR-CRP-017** | The farmer SHALL be able to modify any of the following fields: `crop_name`, `planting_date`, `estimated_harvest_date`, `acreage`, `gps_latitude`, `gps_longitude`, `quantity_kg`. | SHALL | Doc 4, §2.1 |
| **FR-CRP-018** | Upon submission, the frontend SHALL send `PUT /api/crops/{listing_id}` with the updated JSON payload. | SHALL | Doc 7, §3.A, §3.B |
| **FR-CRP-019** | The backend SHALL verify that the `listing_id` belongs to the authenticated `farmer_id` before executing the SQL `UPDATE`. If the `listing_id` does not exist OR belongs to a different farmer, the backend SHALL return HTTP **404** (not 403). Returning 404 in both scenarios prevents integer-based listing ID enumeration across tenants. | SHALL | Doc 7, §2 (Zero-Trust); CTO Gap 3 Fix — enumeration prevention |
| **FR-CRP-020** | Upon successful update, the backend SHALL return HTTP 200 with the updated listing object. | SHALL | RESTful convention |
| **FR-CRP-021** | The frontend SHALL display a success notification: "Crop listing updated successfully." | SHALL | UX |

### 4.5 DELETE — Soft Delete / Withdraw Crop Listing

> **v1.1 Change (CTO Blocker 3 Fix):** Hard SQL `DELETE` has been replaced with a **Soft Delete** pattern. Physical row deletion is prohibited because `Listings` records serve as the provenance root for Escrow transactions (Increment 2), Telemetry Logs (Increment 3), Agronomist Tickets (Increment 4), and Consumer QR Storyboards (Increment 5). Hard deletion would orphan cross-increment foreign key chains and violate the project's core anti-opaque-provenance mandate (Doc 1, Problem Statement §4).

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **FR-CRP-022** | Each listing in the dashboard view SHALL display a "Withdraw" button or icon (replacing "Delete"). The UI label SHALL reflect the non-destructive nature of the action. | SHALL | Doc 4, §2.1 (CRUD); Doc 7, §1; CTO Blocker 3 Fix |
| **FR-CRP-023** | Clicking "Withdraw" SHALL display a confirmation dialog: "Are you sure you want to withdraw this crop listing? The record will be archived and hidden from your active dashboard." | SHALL | UX; Destructive action safeguard |
| **FR-CRP-024** | Upon confirmation, the frontend SHALL send `DELETE /api/crops/{listing_id}` (endpoint name preserved for RESTful convention; backend behavior is soft delete). | SHALL | Doc 7, §3.A, §3.B |
| **FR-CRP-025** | The backend SHALL verify that the `listing_id` exists AND belongs to the authenticated `farmer_id`. If the `listing_id` does not exist OR belongs to a different farmer, the backend SHALL return HTTP 404. If the check passes, the backend SHALL execute a SQL `UPDATE` setting `is_deleted = TRUE` and `status = 'Withdrawn'` — a physical `DELETE` SQL command SHALL NEVER be executed on the `Listings` table. | SHALL | Doc 7, §2 (Zero-Trust); CTO Blocker 3 Fix — soft delete for provenance integrity |
| **FR-CRP-026** | Upon successful soft deletion, the backend SHALL return HTTP 200 with message: `{ "message": "Listing withdrawn successfully." }`. | SHALL | RESTful convention |
| **FR-CRP-027** | The frontend SHALL remove the withdrawn listing from the active dashboard view immediately without requiring a full page reload. | SHOULD | UX |


## 5. Non-Functional Requirements

### 5.1 Security Requirements

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **NFR-SEC-001** | All passwords SHALL be stored using a one-way cryptographic hash (bcrypt, Argon2, or PBKDF2). Plaintext storage is PROHIBITED. | SHALL | Doc 7, §3.C |
| **NFR-SEC-002** | All API endpoints (except `/login`, `/register`, and public routes) SHALL require a valid JWT in the `Authorization: Bearer` header. | SHALL | Doc 7, §3.C; CTO Blocker 2 Fix |
| **NFR-SEC-003** | JWTs SHALL expire after a configurable period (default: 30 minutes), controlled via the `JWT_EXPIRY_MINUTES` server environment variable. | SHALL | Security best practice; CTO Blocker 2 Fix |
| **NFR-SEC-004** | The system SHALL enforce Zero-Trust data isolation. Every database query involving user-specific data SHALL include a `WHERE farmer_id = <authenticated_user_id>` clause (or equivalent role-based filter). | SHALL | Doc 7, §2 |
| **NFR-SEC-005** | The system SHALL sanitize all user inputs to prevent SQL injection attacks. Parameterized queries or ORM-based queries SHALL be used. | SHALL | Doc 3, §1 (SQL database); Security |
| **NFR-SEC-006** | The system SHALL sanitize all user inputs rendered in HTML to prevent Cross-Site Scripting (XSS) attacks. | SHALL | Security |
| **NFR-SEC-007** | The backend SHALL implement CORS (Cross-Origin Resource Sharing) headers to restrict API access to authorized frontend origins only. | SHALL | Doc 7, §2 |
| **NFR-SEC-008** | User registration SHALL enforce minimum password complexity: at least 8 characters, containing at least one uppercase letter, one lowercase letter, and one digit. | SHOULD | Security |

### 5.2 Performance Requirements

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **NFR-PERF-001** | The login authentication flow (`POST /api/auth/login`) SHALL achieve a p95 response latency of **< 1 second** under a simulated load of **50 concurrent requests**. | SHOULD | UX; CTO Gap 4 Fix — quantified benchmark |
| **NFR-PERF-002** | The Farmer Dashboard listing endpoint (`GET /api/crops`) SHALL load and return a paginated response (20 records) within **1.5 seconds** at p95 under **50 concurrent requests**. | SHOULD | UX; CTO Gap 4 Fix |
| **NFR-PERF-003** | All CRUD API endpoints (`POST`, `PUT`, `DELETE /api/crops`) SHALL achieve a p95 response latency of **< 500 milliseconds** under a simulated load of **50 concurrent requests**. | SHOULD | UX; CTO Gap 4 Fix — replaces vague "under normal load" |

### 5.3 Usability Requirements

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **NFR-USE-001** | The Login page and Farmer Dashboard SHALL be mobile-responsive, rendering correctly on screen widths from 320px to 1920px. | SHALL | Doc 3, §1 (mobile-responsive); Doc 7, §3.B |
| **NFR-USE-002** | Form validation errors SHALL be displayed inline next to the offending field, using red text or border highlighting. | SHOULD | UX |
| **NFR-USE-003** | Success and error notifications SHALL be visually distinct (e.g., green for success, red for error) and auto-dismiss after 5 seconds. | SHOULD | UX |
| **NFR-USE-004** | The system SHALL provide clear visual feedback (e.g., loading spinner) during API calls to prevent double submissions. | SHOULD | UX |

### 5.4 Reliability & Data Integrity Requirements

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **NFR-REL-001** | The SQL database SHALL enforce ACID compliance for all write operations. | SHALL | Doc 3, §1; Doc 5 |
| **NFR-REL-002** | The database schema SHALL enforce NOT NULL constraints on all required fields defined in the data dictionary (Section 7). | SHALL | Doc 7, §3.C (strict normalization) |
| **NFR-REL-003** | The database SHALL enforce referential integrity via foreign key constraints (e.g., `Listings.farmer_id` → `Farmers.farmer_id`). | SHALL | Doc 7, §3.C |
| **NFR-REL-004** | The database SHALL enforce UNIQUE constraints on `Users.username`. | SHALL | FR-LGN-020 |

### 5.5 Maintainability & Extensibility Requirements

| Req ID | Requirement | Priority | Source |
|---|---|---|---|
| **NFR-MNT-001** | The `Users.role` column SHALL use an extensible enumeration type (or equivalent constraint) to accommodate the 5 authenticated roles. New roles SHALL be addable without schema migration in future increments. | SHOULD | Doc 4, §2.1–2.5 |
| **NFR-MNT-002** | The backend API SHALL follow RESTful design conventions (`GET`, `POST`, `PUT`, `DELETE`) for all CRUD endpoints. | SHALL | Doc 7, §3.A |
| **NFR-MNT-003** | The codebase SHALL be version-controlled using Git/GitHub with branch protection rules preventing direct pushes to the `main` branch. | SHALL | Doc 3, §2 |

---

## 6. RBAC Security Matrix — Role Isolation Model

This matrix defines the access control rules for Increment 1. The RBAC engine is the backend middleware layer that intercepts every authenticated request, reads the user's role from the **JWT claims**, and enforces the following permissions.

### 6.1 Route-Level Access Control

| Route / Endpoint | Farmer | B2B Buyer | Transporter | Agronomist | Compliance Officer | Unauthenticated |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| `GET /login` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `POST /api/auth/login` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `POST /api/auth/register` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `POST /api/auth/logout` | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| `GET /dashboard/farmer` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `GET /api/crops` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `GET /api/crops/{id}` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `POST /api/crops` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `PUT /api/crops/{id}` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `DELETE /api/crops/{id}` | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `GET /dashboard/buyer` | ❌ | 🔒* | ❌ | ❌ | ❌ | ❌ |
| `GET /dashboard/transporter` | ❌ | ❌ | 🔒* | ❌ | ❌ | ❌ |
| `GET /dashboard/agronomist` | ❌ | ❌ | ❌ | 🔒* | ❌ | ❌ |
| `GET /dashboard/compliance` | ❌ | ❌ | ❌ | ❌ | 🔒* | ❌ |

> 🔒* = Route exists and authenticates the user, but renders a "Dashboard under construction" placeholder (FR-LGN-013).

### 6.2 Data-Level Access Control (Zero-Trust)

| Rule | Enforcement |
|---|---|
| A Farmer SHALL only see their own crop listings. | Backend `WHERE` clause: `farmer_id = <authenticated_farmer_id> AND is_deleted = FALSE` |
| A Farmer SHALL only retrieve a single listing they own. | `GET /api/crops/{id}` returns HTTP **404** if not found OR if owned by another tenant (FR-CRP-014A). |
| A Farmer SHALL only edit their own crop listings. | `PUT /api/crops/{id}` returns HTTP **404** if not found OR if owned by another tenant (FR-CRP-019). |
| A Farmer SHALL only withdraw their own crop listings. | `DELETE /api/crops/{id}` soft-deletes; returns HTTP **404** if not found OR if owned by another tenant (FR-CRP-025). |
| No role other than Farmer SHALL access crop CRUD endpoints. | RBAC middleware rejects non-Farmer JWTs with HTTP 403. |

### 6.3 RBAC Violation Response Specification

| Scenario | HTTP Status | Response Body |
|---|---|---|
| User attempts to access a route for a different role. | `403 Forbidden` | `{"error": "Access denied. You do not have permission to access this resource."}` |
| User attempts to access/modify a listing not belonging to them OR a non-existent listing ID. | `404 Not Found` | `{"error": "Listing not found."}` — *404 used (not 403) to prevent integer ID enumeration (CTO Gap 3 Fix).* |
| Request has no JWT or an expired JWT. | `401 Unauthorized` | `{"error": "Authentication required. Please log in."}` |
| Request has a malformed/tampered JWT. | `401 Unauthorized` | `{"error": "Invalid session. Please log in again."}` |

---

## 7. Data Dictionary — Increment 1 Database Tables

> **Source:** Doc 7, §3.C — "Write ACID-compliant SQL schemas to generate the `Users`, `Farmers`, and `Listings` tables. Ensure strict normalization."

### 7.1 `Users` Table

The master authentication table. Stores credentials and role assignments for all system actors.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for each user. |
| `username` | VARCHAR(50) | NOT NULL, UNIQUE | The user's login name. |
| `password_hash` | VARCHAR(255) | NOT NULL | Bcrypt/Argon2 hashed password. NEVER plaintext. |
| `role` | VARCHAR(30) | NOT NULL, CHECK (role IN ('farmer', 'buyer', 'transporter', 'agronomist', 'compliance_officer')) | The user's RBAC role. Determines dashboard routing. |
| `email` | VARCHAR(100) | UNIQUE | User's email address (optional for Increment 1). |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Account creation timestamp. |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Soft-delete / account deactivation flag. |

> *Note: The physical SQLite column is `id` (surrogate primary key). The API/JSON presentation layer serializes this field as `user_id` / `farmer_id` / `listing_id` per `AG-API-INC1-003` (`crops.py` serializers and the auth response envelopes).*

### 7.2 `Farmers` Table

Extended profile information for users with the `farmer` role. This table establishes the 1:1 relationship between a user account and a farmer profile.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for the farmer profile. |
| `user_id` | INTEGER | NOT NULL, UNIQUE, FOREIGN KEY → `Users.user_id` | Links farmer profile to the user account. |
| `farm_name` | VARCHAR(100) | NOT NULL | The name of the farmer's farm/operation. |
| `farm_location` | VARCHAR(200) | | Human-readable farm address or region. |
| `default_gps_latitude` | DECIMAL(9,6) | | Default GPS latitude for the farm. |
| `default_gps_longitude` | DECIMAL(9,6) | | Default GPS longitude for the farm. |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Profile creation timestamp. |

> *Note: The physical SQLite column is `id` (surrogate primary key). The API/JSON presentation layer serializes this field as `user_id` / `farmer_id` / `listing_id` per `AG-API-INC1-003` (`crops.py` serializers and the auth response envelopes).*

### 7.3 `Listings` Table

The active crop ledger. Each row represents a single crop that a farmer is cultivating or has available. **Rows are NEVER physically deleted** — they are soft-deleted via the `is_deleted` flag.

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | Unique identifier for the crop listing. |
| `farmer_id` | INTEGER | NOT NULL, FOREIGN KEY → `Farmers.farmer_id` | Links the listing to its owner. **Zero-Trust anchor.** |
| `crop_name` | VARCHAR(100) | NOT NULL, CHECK (crop_name IN ('Wheat', 'Rice', 'Tomato', 'Potato', 'Cotton', 'Maize', 'Sugarcane', 'Other')) | Standardized crop type from the approved taxonomy list. |
| `planting_date` | DATE | NOT NULL | Date the crop was planted. Must be ≤ CURRENT_DATE and within 365 days prior. |
| `estimated_harvest_date` | DATE | NOT NULL | Farmer's estimated harvest date. Must be > planting_date. |
| `acreage` | DECIMAL(10,2) | NOT NULL, CHECK (acreage > 0) | Total land area allocated (acres/hectares). |
| `gps_latitude` | DECIMAL(9,6) | NOT NULL | Latitude of the crop's location. |
| `gps_longitude` | DECIMAL(9,6) | NOT NULL | Longitude of the crop's location. |
| `quantity_kg` | DECIMAL(12,2) | NOT NULL, CHECK (quantity_kg > 0) | Estimated or actual quantity in kilograms. |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'Active', CHECK (status IN ('Active', 'Sold', 'In Transit', 'Delivered', 'Withdrawn')) | Lifecycle status. In Increment 1, records are created as 'Active' and retired as 'Withdrawn'. 'Sold', 'In Transit', and 'Delivered' are reserved for Increments 2 and 3 forward compatibility. |
| `is_deleted` | BOOLEAN | NOT NULL, DEFAULT FALSE | **Soft-delete flag.** Set to TRUE when farmer withdraws a listing. Physical row deletion is PROHIBITED. Active dashboard queries filter `WHERE is_deleted = FALSE`. |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP | Listing creation timestamp. |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | Last modification timestamp. |

> *Note: The physical SQLite column is `id` (surrogate primary key). The API/JSON presentation layer serializes this field as `user_id` / `farmer_id` / `listing_id` per `AG-API-INC1-003` (`crops.py` serializers and the auth response envelopes).*

### 7.4 Entity Relationships

```
Users (1) ──── (1) Farmers       [user_id FK]
Farmers (1) ── (0..*) Listings   [farmer_id FK]
```

- A `User` with `role = 'farmer'` has exactly one `Farmers` profile.
- A `Farmers` profile can have zero or more `Listings`.
- Deactivating a `User` SHALL set `Users.is_active = FALSE` (soft-delete). The `Farmers` profile and all `Listings` records SHALL be retained for cross-increment provenance integrity. Physical cascading deletes are PROHIBITED.


---

## 8. Error Handling & Invalid Input Specification

### 8.1 Login Error Handling

| Scenario | System Behavior | HTTP Code | User-Facing Message |
|---|---|---|---|
| Empty username field submitted | Reject request before DB query | 400 | "Username and password are required." |
| Empty password field submitted | Reject request before DB query | 400 | "Username and password are required." |
| Username not found in DB | Return generic error | 401 | "Invalid credentials." |
| Password hash mismatch | Return generic error | 401 | "Invalid credentials." |
| Malformed JSON payload | Reject request | 400 | "Invalid request format." |
| Database connection failure | Log error server-side, return generic error | 500 | "An internal error occurred. Please try again later." |

### 8.2 Registration Error Handling

| Scenario | System Behavior | HTTP Code | User-Facing Message |
|---|---|---|---|
| Username already exists | Reject registration | 409 | "Username already exists." |
| Password does not meet complexity rules | Reject registration | 400 | "Password must be at least 8 characters with uppercase, lowercase, and a digit." |
| Invalid role value submitted | Reject registration | 400 | "Invalid role. Must be one of: farmer, buyer, transporter, agronomist, compliance_officer." |
| `role = 'farmer'` submitted without `farm_name` | Reject registration | 400 | "Farm name is required when registering as a farmer." |
| Missing required fields | Reject registration | 400 | "All fields are required: username, password, role." |
| `Farmers` profile INSERT fails during atomic transaction | Rollback entire transaction, return error | 500 | "Registration failed. Please try again." |

### 8.3 Crop CRUD Error Handling

| Scenario | System Behavior | HTTP Code | User-Facing Message |
|---|---|---|---|
| Missing required field in crop JSON | Reject before DB write | 400 | "Missing required field: {field_name}." |
| `crop_name` is not in the approved taxonomy list | Reject | 400 | "Invalid crop name. Must be one of: Wheat, Rice, Tomato, Potato, Cotton, Maize, Sugarcane, Other." |
| `acreage` ≤ 0 | Reject | 400 | "Acreage must be a positive number." |
| `quantity_kg` ≤ 0 | Reject | 400 | "Quantity must be a positive number." |
| `gps_latitude` outside range [-90, 90] | Reject | 400 | "Latitude must be between -90 and 90." |
| `gps_longitude` outside range [-180, 180] | Reject | 400 | "Longitude must be between -180 and 180." |
| `planting_date` is not a valid date format | Reject | 400 | "Invalid date format. Use YYYY-MM-DD." |
| `planting_date` is in the future | Reject | 400 | "Planting date cannot be in the future." |
| `planting_date` is older than 365 days | Reject | 400 | "Planting date cannot be older than 365 days for an active listing." |
| `estimated_harvest_date` is before or equal to `planting_date` | Reject | 400 | "Estimated harvest date must be after planting date." |
| `listing_id` not found OR belongs to a different farmer | Return not found (unified — prevents enumeration) | 404 | "Listing not found." |
| Non-farmer role attempts crop CRUD | RBAC middleware blocks | 403 | "Access denied. You do not have permission to access this resource." |
| Database write failure | Log error, return generic | 500 | "An internal error occurred. Please try again later." |


---

## 9. Traceability Matrix

This matrix maps each functional requirement back to its authoritative source document, ensuring full bidirectional traceability.

| Req ID | Master Document Source | Section/Context |
|---|---|---|
| FR-LGN-001 to FR-LGN-005 | Doc 7, §3.A (Architecture Agent tasks) & §3.B (UI/UX Agent tasks) | Login page and JSON payload structure |
| FR-LGN-006 to FR-LGN-011 | Doc 7, §3.C (Backend Agent tasks); CTO Blocker 2 Fix | JWT generation, storage, and transport |
| FR-LGN-012 to FR-LGN-013 | Doc 7, §3.C & Doc 6, §2 | Role-based routing, increment scoping |
| FR-LGN-014 to FR-LGN-017 | Doc 7, §3.C (derived) | Error handling, security |
| FR-LGN-018, FR-LGN-018A | Doc 7, §3.C; CTO Blocker 1 Fix | Farmer registration + atomic Farmers profile creation |
| FR-LGN-019 to FR-LGN-021 | Doc 7, §3.C | Role restriction, password hashing |
| FR-LGN-022 to FR-LGN-024 | Doc 7, §3.C; CTO Blocker 2 Fix | JWT validation, logout behavior |
| §3.3 JWT Contract | CTO Blocker 2 Fix | Formal JWT header/payload/transport specification |
| FR-CRP-001 to FR-CRP-004 | Doc 4, §2.1 (Farmer features) & Doc 7, §3.A | CREATE operation, JSON payload |
| FR-CRP-004A | CTO Gap 1 Fix | Crop taxonomy standardization (prevents Yield Engine mismatch in Inc 2) |
| FR-CRP-005 to FR-CRP-006 | Doc 7, §2 (Zero-Trust); Doc 5, Workflow 1 | farmer_id JWT extraction, SQL INSERT |
| FR-CRP-006A | CTO Gap 2 Fix | Temporal boundary validation (future date, 365-day lookback) |
| FR-CRP-007 to FR-CRP-009 | Doc 4, §2.1; RESTful convention | HTTP 201, status auto-set |
| FR-CRP-010 to FR-CRP-013 | Doc 4, §2.1 & Doc 5, Workflow 1 Step 1 | READ list with pagination and soft-delete filter |
| FR-CRP-011 | CTO Gap 5 Fix | Pagination (`page`, `limit`) added to GET /api/crops |
| FR-CRP-014 to FR-CRP-014A | Doc 4, §2.1; CTO Blocker 4 Fix + CTO Gap 3 Fix | Single-resource GET endpoint; 404 enumeration prevention |
| FR-CRP-015 to FR-CRP-021 | Doc 4, §2.1 & Doc 7, §2 (Zero-Trust); CTO Gap 3 Fix | UPDATE with 404-unified ownership check |
| FR-CRP-022 to FR-CRP-027 | Doc 4, §2.1 & Doc 7, §2 (Zero-Trust); CTO Blocker 3 Fix | Soft DELETE (withdraw), provenance integrity |
| NFR-SEC-001 to NFR-SEC-008 | Doc 7, §2 & §3.C; CTO Blocker 2 Fix | Security: JWT, hashing, CORS, Zero-Trust, input sanitization |
| NFR-PERF-001 to NFR-PERF-003 | CTO Gap 4 Fix | Quantified p95 benchmarks (50 concurrent users) |
| NFR-USE-001 to NFR-USE-004 | Doc 3, §1 & Doc 7, §3.B | Mobile responsiveness, UX feedback |
| NFR-REL-001 to NFR-REL-004 | Doc 3, §1 & Doc 7, §3.C | ACID compliance, schema constraints |
| NFR-MNT-001 to NFR-MNT-003 | Doc 3, §2 & Doc 4 | RESTful design, Git workflow |


---

## 10. Assumptions & Dependencies

### 10.1 Assumptions

| ID | Assumption |
|---|---|
| A-01 | The development team has access to a Python 3.x runtime environment. |
| A-02 | SQLite3 will be used for local prototyping; migration to MySQL/PostgreSQL is deferred to deployment. |
| A-03 | The frontend communicates with the backend exclusively via JSON over HTTP (REST). No GraphQL, no server-rendered templates for API data. |
| A-04 | A single farmer account maps to a single farm. Multi-farm support per user is deferred to a future increment. |
| A-05 | GPS coordinates are entered manually by the farmer (or via browser Geolocation API). External geocoding services are out of scope for Increment 1. |

### 10.2 Dependencies

| ID | Dependency | Impact if Unavailable |
|---|---|---|
| D-01 | Python Flask/Django framework installed and configured. | Backend cannot be initialized. |
| D-02 | SQL database engine (SQLite3/MySQL/PostgreSQL) available. | No data persistence. |
| D-03 | GitHub repository initialized with branch protection. | Version control not enforced. |
| D-04 | Modern web browser for frontend testing. | UI cannot be validated. |

---

## 11. Glossary

| Term | Definition |
|---|---|
| **RBAC** | Role-Based Access Control. A security model where permissions are assigned to roles, and users are assigned roles. |
| **Zero-Trust** | A security principle where no user or process is inherently trusted. All data access requires explicit verification. |
| **CRUD** | Create, Read, Update, Delete — the four fundamental database operations. |
| **ACID** | Atomicity, Consistency, Isolation, Durability — properties guaranteeing reliable database transactions. |
| **JWT** | JSON Web Token — a compact, stateless, digitally signed token used for authentication and claim transmission between parties. The Agri-Grid system uses JWTs transmitted via the `Authorization: Bearer` header. |
| **Session Token** | In this document, synonymous with JWT. A cryptographically signed token issued upon successful authentication, carrying user identity claims (`user_id`, `farmer_id`, `role`, `exp`). |
| **Soft Delete** | A data archival pattern in which records are never physically removed from the database; instead, an `is_deleted` flag is set to `TRUE`. Ensures data provenance integrity across all increments. |
| **Farmer** | A system actor who cultivates crops and enters supply-side data into the Agri-Grid platform. |
| **Listing** | A single crop record in the `Listings` table, representing an active crop being cultivated by a Farmer. |
| **Batch ID** | A unique identifier for a commercial produce batch (generated in Increment 2 when a listing is published to the marketplace). |
| **JSON Payload** | The structured data object transmitted between the frontend and backend via HTTP requests. |
| **CORS** | Cross-Origin Resource Sharing — a browser security mechanism that restricts web pages from making requests to a different domain than the one that served the page. |
| **p95 Latency** | The 95th-percentile response time — i.e., 95% of requests complete within this duration. Used as the measurable performance benchmark for V-Model test harnesses. |

---

## 12. Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-10-10 | Requirements & Architecture Agent | Initial SRS for Increment 1. Covers RBAC Login Gateway (FR-LGN-001 to FR-LGN-024) and Active Crop CRUD (FR-CRP-001 to FR-CRP-027). |
| 1.1 | 2026-10-11 | CTO Audit — Ameer Muawiyah (PM) | CTO review pass. Fixed 4 critical blockers and 5 engineering gaps. Added: FR-LGN-018A (atomic farmer registration), §3.3 (JWT contract), FR-CRP-004A (crop taxonomy), FR-CRP-006A (temporal validation), FR-CRP-014A (GET /api/crops/{id}). Replaced hard DELETE with soft-delete pattern (is_deleted flag). Unified 403→404 for cross-tenant ownership checks. Added `is_deleted` column to Listings schema. Quantified all NFR-PERF benchmarks (p95, 50 concurrent users). Added pagination to GET /api/crops. |

---

*End of Document — AG-SRS-INC1-001 v1.1*
