# SRS Audit Change Log
## Document: AG-SRS-INC1-001
## Version Transition: v1.0 → v1.1

| Field | Value |
|---|---|
| **Audited Document** | `AG-SRS-INC1-001` — Increment 1 Farmer Dashboard SRS |
| **Audit Performed By** | CTO & Master Integration Hub |
| **Reviewed With** | Ameer Muawiyah (Project Manager & Lead Data Architect) |
| **v1.0 Date** | 2026-10-10 |
| **v1.1 Date** | 2026-10-11 |
| **Audit Standard** | IEEE 830 / ISO/IEC/IEEE 29148 SRS Quality Attributes |
| **Total Issues Identified** | 9 (4 Critical Blockers + 5 Engineering Gaps) |
| **Total Issues Resolved** | 9 / 9 — All issues closed in v1.1 |

---

## Audit Scorecard Summary

| Quality Attribute | v1.0 Score | v1.1 Score | Delta |
|---|:---:|:---:|:---:|
| Scope & Bounding | 9.5 / 10 | 9.5 / 10 | — |
| Traceability | 9.0 / 10 | 9.5 / 10 | ▲ +0.5 |
| Correctness & Feasibility | 7.5 / 10 | 9.5 / 10 | ▲ +2.0 |
| Unambiguity | 7.0 / 10 | 9.5 / 10 | ▲ +2.5 |
| Completeness | 7.5 / 10 | 9.5 / 10 | ▲ +2.0 |
| Consistency | 8.0 / 10 | 9.5 / 10 | ▲ +1.5 |
| Verifiability / Testability | 7.5 / 10 | 9.5 / 10 | ▲ +2.0 |

---

## Section 1: Critical Architectural Blockers (Severity: 🔴 BLOCKING)

These issues would have caused **immediate runtime failures, security breaches, or broken cross-increment foreign key chains** if passed to engineering without correction.

---

### BLOCKER-1: Foreign Key "Chicken-and-Egg" Paradox in Farmer Registration

| Field | Detail |
|---|---|
| **Severity** | 🔴 Critical — Runtime Database Crash |
| **Classification** | Correctness & Feasibility |
| **Affected v1.0 Requirements** | `FR-LGN-018`, `FR-CRP-005`, `FR-CRP-006`, Table 7.2 (`Farmers`), Table 7.3 (`Listings`) |
| **Root Cause** | `FR-LGN-018` defined farmer registration as accepting only `username`, `password`, and `role`. However, Table 7.2 mandates `Farmers.farm_name VARCHAR(100) NOT NULL`. Table 7.3 requires `Listings.farmer_id NOT NULL FOREIGN KEY → Farmers.farmer_id`. No registration requirement defined the creation of a corresponding `Farmers` row. Result: when a farmer attempted to create a crop listing, the backend had no valid `farmer_id` to reference, causing an immediate SQL Foreign Key Constraint Violation and a 500 Internal Server Error. |
| **Impact** | The entire Farmer CRUD workflow (FR-CRP-001 through FR-CRP-027) was architecturally non-functional. Every `POST /api/crops` call would have crashed at the DB level on Day 1 of implementation. |
| **v1.1 Fix Applied** | **1.** `FR-LGN-018` was rewritten to require `farm_name` in the registration payload when `role = 'farmer'`. **2.** New requirement `FR-LGN-018A` was added mandating that the backend performs an **atomic database transaction** creating both a `Users` record AND a `Farmers` record simultaneously. If the `Farmers` INSERT fails, the entire transaction rolls back. **3.** Section 8.2 (Registration Error Handling) was updated with: a `400` error case for `role='farmer'` without `farm_name`, and a `500` error case for atomic transaction rollback failure. |
| **Requirements Modified** | `FR-LGN-018` (rewritten), `FR-LGN-018A` (new), Section 8.2 (new rows) |

---

### BLOCKER-2: Authentication Architecture Ambiguity — Cookie vs. Bearer Header Mutual Exclusion

| Field | Detail |
|---|---|
| **Severity** | 🔴 Critical — Frontend/Backend Contract Break & Security Violation |
| **Classification** | Unambiguity, Consistency |
| **Affected v1.0 Requirements** | `FR-LGN-009`, `FR-LGN-010`, `FR-LGN-011`, `FR-LGN-022`, `NFR-SEC-002`, `NFR-SEC-003` |
| **Root Cause** | `FR-LGN-009` generically said "generate a cryptographically secure session token" without specifying the token format. `FR-LGN-011` instructed the frontend to store it in "an HttpOnly cookie OR secure localStorage" — two mutually exclusive mechanisms. `FR-LGN-022` simultaneously required "Authorization: Bearer `<token>`" headers from JavaScript. An `HttpOnly` cookie is by definition inaccessible to JavaScript — it cannot be read to populate a Bearer header. This architectural contradiction left the UI/UX Agent and Backend Agent with no valid shared contract, guaranteeing integration failure. Additionally, no `Sessions` table was defined, leaving it ambiguous whether tokens were stateful server-side sessions or stateless JWTs. |
| **Impact** | The UI/UX Agent and Backend Agent would have implemented incompatible authentication mechanisms. The integration phase would have been blocked by a fundamental transport-layer mismatch. |
| **v1.1 Fix Applied** | **1.** Committed formally to **stateless JWTs (JSON Web Tokens)** signed with HS256. **2.** `FR-LGN-009` rewritten to specify the exact JWT payload claims: `user_id`, `farmer_id` (nullable for non-farmers), `role`, `exp`. **3.** `FR-LGN-011` updated: JWT SHALL be stored in `sessionStorage` (key: `agrigrid_token`). `HttpOnly` cookie storage is explicitly PROHIBITED for this architecture. **4.** `FR-LGN-022` updated to formally use `Authorization: Bearer <jwt_string>`. **5.** `FR-LGN-024` updated to reflect that JWT logout is client-side token purge (stateless JWTs cannot be server-side invalidated without a blocklist). **6.** New **§3.3 JWT Contract Specification** added, defining the exact JWT header (`alg: HS256`), payload schema, `sessionStorage` key name, and server environment variable (`JWT_EXPIRY_MINUTES`). **7.** `NFR-SEC-002` updated from "session token" to "valid JWT in Authorization: Bearer header". **8.** `NFR-SEC-003` changed from `SHOULD` to `SHALL` and tied to environment variable. **9.** Three new glossary terms added: `JWT`, updated `Session Token`, `p95 Latency`. |
| **Requirements Modified** | `FR-LGN-009`, `FR-LGN-010`, `FR-LGN-011`, `FR-LGN-022`, `FR-LGN-024`, `NFR-SEC-002`, `NFR-SEC-003`, §3.3 (new), Glossary (3 entries modified/added) |

---

### BLOCKER-3: Hard SQL DELETE Violates Cross-Increment Provenance Integrity

| Field | Detail |
|---|---|
| **Severity** | 🔴 Critical — Data Architecture Violation & Cascade FK Orphaning |
| **Classification** | Correctness, Consistency |
| **Affected v1.0 Requirements** | `FR-CRP-022`, `FR-CRP-023`, `FR-CRP-024`, `FR-CRP-025`, `FR-CRP-026`, Table 7.3 (`Listings`) |
| **Root Cause** | `FR-CRP-025` mandated: *"The backend SHALL...execute the SQL `DELETE`"*. The `Users` table used a soft-delete (`is_active BOOLEAN`) but `Listings` used hard physical deletion. `Listings` records serve as the provenance root for foreign key chains in Increments 2–5: **Escrow Holdings** (Inc 2), **Cold-Chain Telemetry Logs** (Inc 3), **Agronomist Diagnostic Tickets** (Inc 4), and **Consumer QR Storyboards** (Inc 5). Physically deleting a Listing that a later increment references would either: (a) cascade-delete all historical provenance data, or (b) create orphaned FK violations, crashing Increment 2+ modules. This directly violates the project's core mandate of solving **Opaque Provenance** (Doc 1, Problem Statement §4). |
| **Impact** | Any farmer who deleted a crop that had been viewed/purchased/transported in a test scenario would corrupt the entire data lifecycle chain. This was an architectural time bomb that would not surface until Increment 2 integration. |
| **v1.1 Fix Applied** | **1.** Hard SQL `DELETE` on `Listings` is formally **PROHIBITED**. **2.** Section 4.5 heading renamed from "DELETE — Remove Crop Listing" to "DELETE — Soft Delete / Withdraw Crop Listing". **3.** `FR-CRP-022` changed: UI button label updated from "Delete" to "Withdraw" to reflect the non-destructive nature of the action. **4.** `FR-CRP-023` confirmation dialog text updated to reflect archival behavior. **5.** `FR-CRP-025` rewritten: backend executes a SQL `UPDATE` setting `is_deleted = TRUE` AND `status = 'Withdrawn'` — never a physical `DELETE`. **6.** `FR-CRP-026` response message updated to "Listing withdrawn successfully." **7.** Table 7.3 updated with new column: `is_deleted BOOLEAN NOT NULL DEFAULT FALSE`. **8.** Table 7.3 `crop_name` description updated. **9.** Section 7.4 cascade delete note changed from SHOULD to SHALL soft-delete mandate. **10.** Section 6.2 updated: data-level `WHERE` clause now includes `is_deleted = FALSE`. |
| **Requirements Modified** | `FR-CRP-022`, `FR-CRP-023`, `FR-CRP-024`, `FR-CRP-025`, `FR-CRP-026`, §4.5 heading, Table 7.3 (new column), §6.2, §7.4 |

---

### BLOCKER-4: Missing Single-Resource Query Endpoint `GET /api/crops/{id}`

| Field | Detail |
|---|---|
| **Severity** | 🔴 Critical — Incomplete API Contract / Broken UI Feature |
| **Classification** | Completeness |
| **Affected v1.0 Requirements** | `FR-CRP-014`, Section 6.1 (Route Matrix) |
| **Root Cause** | `FR-CRP-014` mandated that a farmer "SHALL be able to click on an individual listing to view its full details." However, the Route-Level Access Control Matrix in Section 6.1 and the functional requirements in Section 4 contained no specification for `GET /api/crops/{listing_id}`. The only read endpoint was `GET /api/crops` (list). Without a single-resource endpoint, the UI/UX Agent had no contract for implementing the listing detail view, and the Backend Agent had no instruction to build it. Furthermore, `FR-CRP-014` was marked `SHOULD` (optional) despite the detail view being required for the UX flow. |
| **Impact** | The "view full listing details" feature (including GPS coordinates) could not have been implemented. The UI/UX and Backend Agents would have had no matching contract, causing integration failure for this specific user flow. |
| **v1.1 Fix Applied** | **1.** New requirement `FR-CRP-014A` added: formally specifies `GET /api/crops/{listing_id}`, HTTP 200 response with full listing object, HTTP 404 if not found or not owned by the requesting farmer. **2.** `FR-CRP-014` priority upgraded from `SHOULD` to `SHALL`. **3.** `GET /api/crops/{id}` added as a new row to the Section 6.1 Route-Level Access Control Matrix. **4.** Section 6.2 Data-Level Access Control updated with an explicit rule for this new endpoint. |
| **Requirements Modified** | `FR-CRP-014` (priority upgrade), `FR-CRP-014A` (new), §6.1 Route Matrix (new row), §6.2 (new rule) |

---

## Section 2: Engineering Gaps (Severity: 🟡 HIGH PRIORITY)

These issues would have resulted in degraded system quality, security vulnerabilities, V-Model test failures, or downstream Increment 2+ integration problems.

---

### GAP-1: Free-Text `crop_name` vs. Predictive Engine Taxonomy Mismatch

| Field | Detail |
|---|---|
| **Severity** | 🟡 High — Cross-Increment Integration Risk |
| **Classification** | Correctness, Consistency |
| **Affected v1.0 Requirements** | `FR-CRP-002`, `FR-CRP-004`, Table 7.3 `crop_name` column |
| **Root Cause** | `crop_name` was defined as a free-text `VARCHAR(100)` with no validation. Master Document 3 specifies that the Increment 2 Predictive Yield Engine executes conditional algorithms like `IF crop_type == "Wheat" AND soil_moisture < 20%`. Free-text entry allows farmers to type "wheat", "WHEAT", "Winter Wheat", or typos like "Whet", all of which the algorithm would fail to match, silently producing incorrect or null yield forecasts. |
| **v1.1 Fix Applied** | **1.** New requirement `FR-CRP-004A` added: `crop_name` must be selected from a standardized frontend enumeration: `["Wheat", "Rice", "Tomato", "Potato", "Cotton", "Maize", "Sugarcane", "Other"]`. **2.** Backend validation added: rejects any value not in the approved list. **3.** Table 7.3 `crop_name` column updated with a SQL `CHECK` constraint enforcing the same taxonomy list. **4.** Section 8.3 error row updated from "crop_name is empty string → 400" to "crop_name not in taxonomy list → 400" with full approved list in the error message. |
| **Requirements Modified** | `FR-CRP-004A` (new), Table 7.3 `crop_name` (CHECK constraint), §8.3 (row updated) |

---

### GAP-2: Missing Temporal Logic Boundaries on `planting_date`

| Field | Detail |
|---|---|
| **Severity** | 🟡 High — Data Quality & Logic Gap |
| **Classification** | Completeness, Correctness |
| **Affected v1.0 Requirements** | Section 8.3 (Crop CRUD Error Handling) |
| **Root Cause** | Section 8.3 validated that `estimated_harvest_date > planting_date` but imposed no boundary constraints on `planting_date` itself. A farmer could set a planting date 5 years in the future (making the "Active" status semantically meaningless) or 20 years in the past (making the crop a historical ghost record). Neither scenario should be representable in an "active crop" ledger. |
| **v1.1 Fix Applied** | **1.** New requirement `FR-CRP-006A` added with three temporal validation rules: (a) `planting_date <= CURRENT_DATE` (cannot be future), (b) `planting_date >= CURRENT_DATE - 365 days` (cannot be older than 1 year for an "active" listing), (c) `estimated_harvest_date > planting_date` (pre-existing, retained). **2.** Section 8.3 updated with two new error rows: "planting_date in the future → 400" and "planting_date older than 365 days → 400". **3.** Table 7.3 `planting_date` column description updated to reflect these constraints. |
| **Requirements Modified** | `FR-CRP-006A` (new), §8.3 (2 new rows), Table 7.3 `planting_date` description |

---

### GAP-3: Information Leakage via HTTP 403 on Cross-Tenant Ownership Checks

| Field | Detail |
|---|---|
| **Severity** | 🟡 High — Security Vulnerability (Integer ID Enumeration) |
| **Classification** | Unambiguity, Security |
| **Affected v1.0 Requirements** | `FR-CRP-019`, `FR-CRP-025`, Section 6.3, Section 8.3 |
| **Root Cause** | v1.0 specified that if `listing_id` was NOT FOUND, return `404`; and if `listing_id` BELONGS TO ANOTHER FARMER, return `403`. This behavioral distinction allowed a malicious actor to sequentially scan integer IDs (e.g., `GET /api/crops/1`, `GET /api/crops/2`, ...) and determine which listing IDs were valid (404 = doesn't exist, 403 = exists but belongs to someone else), effectively enumerating the entire active listing database. |
| **v1.1 Fix Applied** | **1.** `FR-CRP-014A` specified `GET /api/crops/{id}` returns `404` for both "not found" AND "belongs to different farmer." **2.** `FR-CRP-019` (UPDATE) updated: returns HTTP `404` in both cases, not `403`. **3.** `FR-CRP-025` (soft DELETE) updated: returns HTTP `404` in both cases. **4.** Section 6.2 Data-Level Access Control table updated to reflect 404-unified responses for all three cross-tenant operations. **5.** Section 6.3 RBAC Violation Response updated: the "User attempts to CRUD a listing belonging to another farmer → 403" row replaced with "listing not found OR belongs to different farmer → 404" with explicit enumeration-prevention rationale. **6.** Section 8.3 unified the two separate error rows ("not found → 404" and "belongs to different farmer → 403") into a single unified row returning `404`. |
| **Requirements Modified** | `FR-CRP-014A`, `FR-CRP-019`, `FR-CRP-025`, §6.2, §6.3, §8.3 |

---

### GAP-4: Unquantified NFR Performance Benchmarks — V-Model Untestable

| Field | Detail |
|---|---|
| **Severity** | 🟡 High — V-Model QA Failure / Non-Verifiable Requirements |
| **Classification** | Verifiability / Testability |
| **Affected v1.0 Requirements** | `NFR-PERF-001`, `NFR-PERF-002`, `NFR-PERF-003` |
| **Root Cause** | All three performance NFRs used subjective, non-measurable qualifiers: "within 2 seconds **under normal load**", "within 3 seconds **for up to 100 listings**", "within 1 second **under normal load**". The phrase "normal load" has no quantified definition — the V-Model test harness (PyTest/Locust) cannot write a deterministic pass/fail assertion against an undefined benchmark. Per IEEE 29148, every NFR must be measurable. |
| **v1.1 Fix Applied** | All three NFRs replaced with quantified p95 latency benchmarks under a defined concurrent user load of 50: **1.** `NFR-PERF-001`: `POST /api/auth/login` → p95 < 1 second @ 50 concurrent requests. **2.** `NFR-PERF-002`: `GET /api/crops` (paginated, 20 records) → p95 < 1.5 seconds @ 50 concurrent requests. **3.** `NFR-PERF-003`: All CRUD endpoints → p95 < 500ms @ 50 concurrent requests. New glossary term `p95 Latency` added with definition. |
| **Requirements Modified** | `NFR-PERF-001`, `NFR-PERF-002`, `NFR-PERF-003`, Glossary (`p95 Latency` added) |

---

### GAP-5: Unbounded `GET /api/crops` Catalog — No Pagination

| Field | Detail |
|---|---|
| **Severity** | 🟡 High — Performance Degradation Risk |
| **Classification** | Completeness |
| **Affected v1.0 Requirements** | `FR-CRP-010`, `FR-CRP-011` |
| **Root Cause** | `FR-CRP-011` specified `GET /api/crops` with no `limit` or `page` parameters. The endpoint returned an unbounded dataset. An enterprise farmer with 500+ seasonal records would trigger a full-table scan on every dashboard load, violating `NFR-PERF-002`. Mobile clients rendering unbounded lists would also experience severe DOM rendering performance degradation. |
| **v1.1 Fix Applied** | **1.** `FR-CRP-011` updated: endpoint signature changed to `GET /api/crops?page=1&limit=20`. **2.** Response structure updated to include pagination metadata: `{ "data": [...], "page": 1, "limit": 20, "total": <count> }`. **3.** Backend filter updated to include `AND is_deleted = FALSE` (synergistic fix with BLOCKER-3). |
| **Requirements Modified** | `FR-CRP-011` |

---

## Section 3: Comprehensive Change Index

A complete index of every requirement ID that was **added**, **modified**, or had its **priority changed** between v1.0 and v1.1.

| Change Type | Requirement ID | Summary of Change |
|---|---|---|
| ✏️ Modified | `FR-LGN-009` | Generalized "session token" → Formal JWT with defined payload claims |
| ✏️ Modified | `FR-LGN-010` | Added explicit JSON response schema: `{ "token": ..., "role": ... }` |
| ✏️ Modified | `FR-LGN-011` | "HttpOnly cookie OR localStorage" → `sessionStorage` only; HttpOnly explicitly PROHIBITED |
| ✏️ Modified | `FR-LGN-018` | Added `farm_name` field requirement for farmer role registration |
| ➕ Added | `FR-LGN-018A` | Atomic database transaction for Users + Farmers record creation |
| ✏️ Modified | `FR-LGN-022` | "session token" → "JWT"; added "validate signature and expiration" |
| ✏️ Modified | `FR-LGN-024` | Logout = client-side JWT purge (stateless; no server-side invalidation) |
| ➕ Added | `§3.3 JWT Contract` | Full JWT header, payload schema, storage key, expiry env variable specification |
| ✏️ Modified | `FR-CRP-004` | JSON payload comment: "string (required)" → "string (required, from standardized list or 'Other')" |
| ➕ Added | `FR-CRP-004A` | Crop taxonomy standardization — enumerated whitelist, backend validation |
| ✏️ Modified | `FR-CRP-005` | "session token" → "JWT token claim" |
| ➕ Added | `FR-CRP-006A` | Temporal date boundary validation (future date, 365-day lookback) |
| ⬆️ Priority | `FR-CRP-014` | Upgraded from `SHOULD` → `SHALL` |
| ➕ Added | `FR-CRP-014A` | New `GET /api/crops/{listing_id}` endpoint with 404-unified tenant check |
| ✏️ Modified | `FR-CRP-019` | Cross-tenant UPDATE check: 403 → 404 (enumeration prevention) |
| ✏️ Modified | `FR-CRP-022` | UI label: "Delete" → "Withdraw" |
| ✏️ Modified | `FR-CRP-023` | Confirmation dialog text updated to reflect archival (not destruction) |
| ✏️ Modified | `FR-CRP-024` | Note added: endpoint name preserved; backend behavior is soft delete |
| ✏️ Modified | `FR-CRP-025` | Hard SQL DELETE → soft delete (is_deleted = TRUE, status = 'Withdrawn'); 403 → 404 |
| ✏️ Modified | `FR-CRP-026` | Response message: "deleted" → "withdrawn" |
| ✏️ Modified | `NFR-SEC-002` | "session token" → "valid JWT in Authorization: Bearer header" |
| ✏️ Modified | `NFR-SEC-003` | Priority: SHOULD → SHALL; tied to `JWT_EXPIRY_MINUTES` env variable |
| ✏️ Modified | `NFR-PERF-001` | Quantified: p95 < 1s @ 50 concurrent users |
| ✏️ Modified | `NFR-PERF-002` | Quantified: p95 < 1.5s @ 50 concurrent users (paginated 20 records) |
| ✏️ Modified | `NFR-PERF-003` | Quantified: p95 < 500ms @ 50 concurrent users |
| ✏️ Modified | Table 7.3 | Added `is_deleted BOOLEAN NOT NULL DEFAULT FALSE` column |
| ✏️ Modified | Table 7.3 | `crop_name`: added CHECK constraint with approved taxonomy list |
| ✏️ Modified | Table 7.3 | `planting_date` / `estimated_harvest_date` descriptions updated |
| ✏️ Modified | §6.1 Route Matrix | Added `GET /api/crops/{id}` row |
| ✏️ Modified | §6.2 Data-Level Rules | Updated WHERE clause with `is_deleted = FALSE`; added 404-unified rules |
| ✏️ Modified | §6.3 Violation Response | 403 cross-tenant row → 404 with enumeration rationale |
| ✏️ Modified | §7.4 Entity Relationships | Cascade delete changed from SHOULD → SHALL soft-delete mandate |
| ✏️ Modified | §8.2 Registration Errors | Added: `farm_name` missing for farmer → 400; transaction rollback → 500 |
| ✏️ Modified | §8.3 CRUD Errors | Updated: crop_name taxonomy row; added 2 date boundary rows; unified 403→404 row |
| ✏️ Modified | §9 Traceability Matrix | All rows updated to reflect v1.1 requirement IDs and CTO fix citations |
| ➕ Added | Glossary: `JWT` | Formal JWT definition |
| ✏️ Modified | Glossary: `Session Token` | Updated to reference JWT synonym |
| ➕ Added | Glossary: `Soft Delete` | Definition of is_deleted pattern |
| ➕ Added | Glossary: `p95 Latency` | Definition for V-Model test harness use |

---

## Section 4: What Was Preserved (No Change Rationale)

The following core architectural decisions from v1.0 were reviewed and **explicitly confirmed as correct** — no changes required:

| Element | Confirmation |
|---|---|
| 5-increment scoping & exclusions (§1.4) | ✅ Clean. Scope boundary is well-enforced. |
| 6-actor system model (§2.2) | ✅ Correct. Farmer-only active in Inc 1; others provisioned only. |
| Zero-Trust SQL filter pattern | ✅ Correct. `WHERE farmer_id = <auth_farmer_id>` pattern is sound. |
| RBAC middleware 403 for wrong-role access | ✅ Correct. 403 is appropriate for *role-level* denial (not resource-level). |
| `Users` table soft-delete via `is_active` | ✅ Correct. Consistent with overall soft-delete philosophy. |
| `Farmers` table schema (7.2) | ✅ Correct. No changes needed. |
| HTTP 401 for missing/expired/tampered tokens | ✅ Correct. Standard OAuth2/JWT convention. |
| NFR-REL suite (ACID, FK, NOT NULL, UNIQUE) | ✅ Correct. Solid data integrity foundation. |
| NFR-USE suite (mobile responsive, UX feedback) | ✅ Correct. Aligns with Doc 3 mobile mandate. |
| NFR-MNT suite (REST, Git branching) | ✅ Correct. Aligns with Doc 3 DevOps requirements. |
| Bidirectional traceability structure (§9) | ✅ Sound methodology. Updated to reflect v1.1 additions. |

---

*End of Audit Log — AG-SRS-INC1-001 v1.0 → v1.1 | CTO Review: PASSED ✅*
