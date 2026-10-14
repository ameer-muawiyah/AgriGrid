# System Sequence Diagrams
## Increment 1: Foundation & The Farmer Dashboard

| Field               | Value                                                              |
|---------------------|---------------------------------------------------------------------|
| **Project Name**    | Agri-Grid: Smart Agriculture & Food Security Ecosystem              |
| **Document ID**     | `AG-SSD-INC1-002`                                                   |
| **Version**         | 1.1                                                                 |
| **Prepared By**     | Requirements & Architecture Agent (Lead Software Architect)         |
| **Reviewed By**     | Ameer Muawiyah (Project Manager & Lead Data Architect) — CTO Review |
| **Date**            | 2026-10-11                                                          |
| **Source Document** | `AG-SRS-INC1-001 v1.1` — `./Architecture_Blueprints/Increment_1/1_Farmer_Dashboard_SRS.md` |

> **v1.1 Change Summary:** Fixed UML fall-through anti-patterns (all `alt` blocks now use `alt...else...end`). Optimized login to single LEFT JOIN query. Added `COUNT(*)` companion query for pagination. Split Flow 2B into three isolated sub-flows. Declared all participants at diagram top. Added four new diagrams covering the missing 75% of Crop CRUD: READ (List), READ (Single Detail), UPDATE, and WITHDRAW (Soft-Delete).

---

## Table of Contents

1. [Diagram 1 — RBAC Login & Authentication Flow](#diagram-1--rbac-login--authentication-flow)
   - [1A — Farmer Registration (Atomic Transaction)](#1a--farmer-registration-atomic-transaction)
   - [1B — Farmer Login & JWT Issuance](#1b--farmer-login--jwt-issuance)
   - [1C — Protected Route Guard (JWT Middleware)](#1c--protected-route-guard-jwt-middleware)
2. [Diagram 2 — Active Crop CREATE](#diagram-2--active-crop-create)
   - [2A — Happy Path: Successful Crop Creation](#2a--happy-path-successful-crop-creation)
   - [2B-1 — Role & RBAC Rejection](#2b-1--role--rbac-rejection)
   - [2B-2 — Input & Temporal Validation Cascade](#2b-2--input--temporal-validation-cascade)
   - [2B-3 — DB Write Failure & Rollback](#2b-3--db-write-failure--rollback)
3. [Diagram 3 — Active Crop READ (Paginated List)](#diagram-3--active-crop-read-paginated-list)
4. [Diagram 4 — Active Crop READ (Single Detail)](#diagram-4--active-crop-read-single-detail)
   - [4A — Happy Path: Single Listing Retrieved](#4a--happy-path-single-listing-retrieved)
   - [4B — Security Check: Unified 404 Response](#4b--security-check-unified-404-response)
5. [Diagram 5 — Active Crop UPDATE](#diagram-5--active-crop-update)
6. [Diagram 6 — Active Crop WITHDRAW (Soft-Delete)](#diagram-6--active-crop-withdraw-soft-delete)
7. [Participant Legend](#participant-legend)
8. [SRS Requirement Traceability](#srs-requirement-traceability)
9. [Revision History](#revision-history)

---

## Diagram 1 — RBAC Login & Authentication Flow

> **SRS Reference:** FR-LGN-001 through FR-LGN-024, §3.3 JWT Contract, §6.1 Route-Level Access Control, §6.3 RBAC Violation Responses.

---

### 1A — Farmer Registration (Atomic Transaction)

> **Key SRS Rules:** `FR-LGN-017` (empty field rejection) · `FR-LGN-018` (`farm_name` required for farmers) · `FR-LGN-018A` (atomic `Users` + `Farmers` transaction) · `FR-LGN-019` (role whitelist) · `FR-LGN-020` (unique username) · `FR-LGN-021` + `NFR-SEC-001` (bcrypt hashing) · `§8.2` (registration error table)
>
> **v1.1 Fix:** Replaced standalone `alt...end` fall-through blocks with fully nested `alt...else...end` structure. Error branches now visually terminate execution — the happy path only proceeds through the final `else` clause.

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database<br/>(Users + Farmers Tables)

    Note over Farmer,DB: FLOW 1A — Farmer Registration (Atomic Transaction)

    Farmer->>FE: Fills registration form<br/>(username, password, role='farmer', farm_name)
    FE->>BE: POST /api/auth/register<br/>{ username, password, role: 'farmer', farm_name }

    alt FR-LGN-017: Missing username, password, or role
        BE-->>FE: HTTP 400 "All fields are required: username, password, role."
        FE-->>Farmer: ❌ Inline field error displayed
    else FR-LGN-018: role='farmer' but farm_name is absent
        BE-->>FE: HTTP 400 "Farm name is required when registering as a farmer."
        FE-->>Farmer: ❌ farm_name field error
    else NFR-SEC-008: Password fails complexity check
        BE-->>FE: HTTP 400 "Password must be ≥8 chars with uppercase, lowercase, and digit."
        FE-->>Farmer: ❌ Password complexity error
    else FR-LGN-019: role value not in approved list
        BE-->>FE: HTTP 400 "Invalid role. Must be one of: farmer, buyer, transporter, agronomist, compliance_officer."
        FE-->>Farmer: ❌ Role field error
    else All input validation passes
        BE->>DB: SELECT user_id FROM Users WHERE username = ?
        alt FR-LGN-020: Username already exists
            DB-->>BE: Row returned
            BE-->>FE: HTTP 409 "Username already exists."
            FE-->>Farmer: ❌ Username taken
        else Username is available
            DB-->>BE: Empty result set
            Note over BE: FR-LGN-021 + NFR-SEC-001:<br/>hash = bcrypt.hash(password)<br/>Plaintext NEVER stored
            BE->>BE: hash = bcrypt.hash(password)
            Note over BE,DB: FR-LGN-018A: BEGIN ATOMIC TRANSACTION<br/>Both Users + Farmers rows must be created together
            BE->>DB: BEGIN TRANSACTION
            BE->>DB: INSERT INTO Users<br/>(username, password_hash, role)<br/>VALUES (?, ?, 'farmer')
            alt Users INSERT fails
                DB-->>BE: SQL Error
                BE->>DB: ROLLBACK
                BE-->>FE: HTTP 500 "Registration failed. Please try again."
                FE-->>Farmer: ❌ Server error — transaction fully rolled back
            else Users INSERT succeeds
                DB-->>BE: new user_id = 42
                BE->>DB: INSERT INTO Farmers<br/>(user_id, farm_name)<br/>VALUES (42, ?)
                alt FR-LGN-018A: Farmers INSERT fails → ROLLBACK
                    DB-->>BE: SQL Constraint Error
                    BE->>DB: ROLLBACK
                    Note over BE: No orphaned Users row exists.<br/>Atomicity guaranteed.
                    BE-->>FE: HTTP 500 "Registration failed. Please try again."
                    FE-->>Farmer: ❌ Server error — no partial state in DB
                else Farmers INSERT succeeds
                    DB-->>BE: new farmer_id = 7
                    BE->>DB: COMMIT
                    BE-->>FE: HTTP 201 "Registration successful. Please log in."
                    FE-->>Farmer: ✅ Redirected to /login
                end
            end
        end
    end
```

---

### 1B — Farmer Login & JWT Issuance

> **Key SRS Rules:** `FR-LGN-004`–`FR-LGN-008` (credential submission & DB check) · `FR-LGN-009` (HS256 JWT with `user_id`, `farmer_id`, `role`, `exp`) · `FR-LGN-010` (response schema) · `FR-LGN-011` (`sessionStorage` storage) · `FR-LGN-012` (role-based redirect) · `FR-LGN-014`–`FR-LGN-016` (generic error, no enumeration) · `§3.3` JWT Contract · `NFR-PERF-001`
>
> **v1.1 Fixes:** (1) Replaced two sequential DB queries (`SELECT Users` then `SELECT Farmers`) with a single optimized `LEFT JOIN` query — halving DB round-trips to meet `NFR-PERF-001` (p95 < 1s @ 50 concurrent users). (2) Fixed fall-through `alt` blocks to proper `alt...else...end`.

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database<br/>(Users + Farmers Tables)

    Note over Farmer,DB: FLOW 1B — Farmer Login & JWT Issuance

    Farmer->>FE: Navigates to /login<br/>Enters username + password
    FE->>BE: POST /api/auth/login<br/>{ "username": "ali_farmer", "password": "Pass@123" }

    alt FR-LGN-017: Empty username or password field
        BE-->>FE: HTTP 400 "Username and password are required."
        FE-->>Farmer: ❌ Inline field error
    else Payload is valid — proceed to authentication
        Note over BE,DB: NFR-PERF-001 Optimization:<br/>Single LEFT JOIN query replaces two sequential round-trips.<br/>farmer_id is null for non-farmer roles (handled by LEFT JOIN).
        BE->>DB: SELECT u.user_id, u.password_hash, u.role, f.farmer_id<br/>FROM Users u<br/>LEFT JOIN Farmers f ON u.user_id = f.user_id<br/>WHERE u.username = ? AND u.is_active = TRUE
        alt FR-LGN-014/016: Username not found in DB
            DB-->>BE: Empty result set
            Note over BE: FR-LGN-016: Generic error — no distinction<br/>between "user not found" and "wrong password".<br/>Prevents username enumeration.
            BE-->>FE: HTTP 401 "Invalid credentials."
            FE-->>Farmer: ❌ "Invalid credentials."
        else User record found
            DB-->>BE: { user_id: 42, password_hash: "$2b$12$...",<br/>role: "farmer", farmer_id: 7 }
            BE->>BE: bcrypt.verify(submitted_password, password_hash)
            alt FR-LGN-015/016: Password hash mismatch
                Note over BE: Same generic error — no enumeration
                BE-->>FE: HTTP 401 "Invalid credentials."
                FE-->>Farmer: ❌ "Invalid credentials."
            else Password verified — Authentication succeeds
                Note over BE: FR-LGN-009 + §3.3 JWT Contract:<br/>alg: HS256 | Claims: user_id=42, farmer_id=7,<br/>role='farmer', exp=now+JWT_EXPIRY_MINUTES
                BE->>BE: jwt = sign(claims, SERVER_SECRET, HS256)
                BE-->>FE: HTTP 200 { "token": "eyJhbGc...", "role": "farmer" }
                Note over FE: FR-LGN-011: Store JWT in sessionStorage<br/>key: 'agrigrid_token'<br/>HttpOnly cookie is PROHIBITED (breaks Bearer header attachment)
                FE->>FE: sessionStorage.setItem('agrigrid_token', token)
                Note over FE: FR-LGN-012: Read role from response body<br/>Redirect to role-specific dashboard
                FE-->>Farmer: ✅ Redirect to /dashboard/farmer
            end
        end
    end
```

---

### 1C — Protected Route Guard (JWT Middleware)

> **Key SRS Rules:** `FR-LGN-011` (sessionStorage retrieval) · `FR-LGN-022` (Bearer header + signature/expiry validation) · `FR-LGN-023` (401 on invalid/missing JWT) · `FR-LGN-013` (farmer dashboard only functional in Inc 1) · `NFR-SEC-002` (all protected endpoints require JWT) · `NFR-SEC-003` (JWT expiry) · `§6.1` (Route Matrix) · `§6.3` (violation responses) · `FR-CRP-011` (paginated response with `total`)
>
> **v1.1 Fixes:** (1) Fixed fall-through `alt` blocks. (2) Added explicit `COUNT(*)` companion query so the backend agent implements the `total` field mandated by `FR-CRP-011`.

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant RBAC as RBAC Middleware<br/>(Backend Guard)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database

    Note over Farmer,DB: FLOW 1C — Protected Route Guard & Dashboard Load

    Farmer->>FE: Requests GET /dashboard/farmer
    FE->>FE: token = sessionStorage.getItem('agrigrid_token')

    alt FR-LGN-023: Token is null or empty — client-side guard
        FE-->>Farmer: ❌ Redirect to /login<br/>"Authentication required. Please log in."
    else Token present — forward to backend
        FE->>RBAC: GET /dashboard/farmer<br/>Authorization: Bearer eyJhbGc...
        alt FR-LGN-022/023: JWT signature invalid or tampered
            RBAC-->>FE: HTTP 401 "Invalid session. Please log in again."
            FE-->>Farmer: ❌ Redirect to /login
        else NFR-SEC-003: JWT exp claim has expired
            RBAC-->>FE: HTTP 401 "Authentication required. Please log in."
            FE-->>Farmer: ❌ Redirect to /login
        else JWT is cryptographically valid — check role
            RBAC->>RBAC: claims = decode(jwt)<br/>role = claims['role']
            alt §6.1/§6.3: role is NOT 'farmer'
                Note over RBAC: Role-level denial = HTTP 403<br/>(distinct from resource-level 404)
                RBAC-->>FE: HTTP 403 "Access denied. You do not have permission to access this resource."
                FE-->>Farmer: ❌ Access denied
            else role = 'farmer' — attach claims, forward to handler
                RBAC->>BE: Forward request with decoded claims<br/>{ user_id: 42, farmer_id: 7, role: 'farmer' }
                Note over BE: FR-LGN-013: /dashboard/farmer is the<br/>ONLY functional dashboard in Increment 1
                Note over BE,DB: FR-CRP-011: Two-query pagination pattern.<br/>Query 1: COUNT(*) for the 'total' metadata field.<br/>Query 2: Paginated data with LIMIT/OFFSET.
                BE->>DB: SELECT COUNT(*) FROM Listings<br/>WHERE farmer_id = 7 AND is_deleted = FALSE
                DB-->>BE: { total: 47 }
                BE->>DB: SELECT listing_id, crop_name, planting_date,<br/>estimated_harvest_date, acreage, quantity_kg, status<br/>FROM Listings<br/>WHERE farmer_id = 7 AND is_deleted = FALSE<br/>ORDER BY created_at DESC<br/>LIMIT 20 OFFSET 0
                DB-->>BE: 20 listing rows (page 1 of 3)
                BE-->>FE: HTTP 200<br/>{ "data": [...20 listings...], "page": 1, "limit": 20, "total": 47 }
                FE-->>Farmer: ✅ Farmer Dashboard rendered<br/>Showing page 1 of 3 (listings 1–20 of 47)
            end
        end
    end
```

---

## Diagram 2 — Active Crop CREATE

> **SRS Reference:** FR-CRP-001 through FR-CRP-009, FR-CRP-004A, FR-CRP-005, FR-CRP-006A, §3.3, §6.1, §6.2, §6.3, §8.3.

---

### 2A — Happy Path: Successful Crop Creation

> **Key SRS Rules:** `FR-CRP-001`–`FR-CRP-003` (UI → `POST /api/crops`) · `FR-CRP-004` (strict JSON payload) · `FR-CRP-004A` (taxonomy whitelist) · `FR-CRP-005` (`farmer_id` from JWT only) · `FR-CRP-006` (SQL INSERT) · `FR-CRP-006A` (temporal validation) · `FR-CRP-007`–`FR-CRP-009` (HTTP 201, success notification, `status` auto-set) · `NFR-SEC-004` (Zero-Trust) · `NFR-REL-001` (ACID INSERT)

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant RBAC as RBAC Middleware<br/>(Backend Guard)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database<br/>(Listings Table)

    Note over Farmer,DB: FLOW 2A — Crop CREATE Happy Path

    Farmer->>FE: Clicks 'Add New Crop' button (FR-CRP-001)
    Note over FE: FR-CRP-002: Render crop creation form<br/>crop_name as taxonomy dropdown (FR-CRP-004A)
    FE-->>Farmer: Form displayed with dropdown<br/>[Wheat, Rice, Tomato, Potato, Cotton, Maize, Sugarcane, Other]

    Farmer->>FE: Fills form:<br/>crop_name: "Wheat" | planting_date: "2026-09-01"<br/>estimated_harvest_date: "2027-01-15" | acreage: 12.5<br/>gps_latitude: 30.3753 | gps_longitude: 69.3451<br/>quantity_kg: 5000.00
    Farmer->>FE: Clicks Submit
    Note over FE: NFR-USE-004: Show loading spinner<br/>Disable submit button (prevent double submission)
    FE->>FE: token = sessionStorage.getItem('agrigrid_token')
    FE->>RBAC: POST /api/crops<br/>Authorization: Bearer eyJhbGc...<br/>Body: { crop_name, planting_date, estimated_harvest_date,<br/>acreage, gps_latitude, gps_longitude, quantity_kg }

    Note over RBAC: Validate JWT signature + expiry<br/>§6.1: POST /api/crops — Farmer role only
    RBAC->>RBAC: claims = decode(jwt) | verify role = 'farmer'
    Note over RBAC: ✅ JWT valid | role = 'farmer' | farmer_id = 7
    RBAC->>BE: Forward with claims { user_id: 42, farmer_id: 7, role: 'farmer' }

    Note over BE: FR-CRP-005 + NFR-SEC-004 Zero-Trust:<br/>farmer_id = claims['farmer_id'] from JWT ONLY<br/>NEVER from request body
    BE->>BE: farmer_id = 7

    Note over BE: FR-CRP-004A: Validate crop_name in taxonomy<br/>FR-CRP-006A Temporal validation:<br/>planting_date ≤ CURRENT_DATE (2026-10-11)<br/>planting_date ≥ CURRENT_DATE − 365 days<br/>estimated_harvest_date > planting_date<br/>§8.3: acreage > 0, quantity_kg > 0, GPS in valid ranges
    BE->>BE: All validations pass ✅

    Note over BE: FR-CRP-009: status auto-set to 'Active'<br/>is_deleted = FALSE (farmer cannot set these manually)
    BE->>BE: status = 'Active' | is_deleted = FALSE

    Note over BE,DB: NFR-REL-001: ACID-compliant INSERT
    BE->>DB: INSERT INTO Listings<br/>(farmer_id, crop_name, planting_date,<br/>estimated_harvest_date, acreage,<br/>gps_latitude, gps_longitude,<br/>quantity_kg, status, is_deleted)<br/>VALUES (7,'Wheat','2026-09-01','2027-01-15',<br/>12.5, 30.3753, 69.3451, 5000.00,'Active', FALSE)

    DB-->>BE: INSERT successful<br/>listing_id = 101 | created_at = now()
    Note over BE: FR-CRP-007: Return HTTP 201 with full new object
    BE-->>FE: HTTP 201 Created<br/>{ listing_id: 101, farmer_id: 7, crop_name: "Wheat",<br/>planting_date: "2026-09-01",<br/>estimated_harvest_date: "2027-01-15",<br/>acreage: 12.5, quantity_kg: 5000.00,<br/>status: "Active", is_deleted: false,<br/>created_at: "2026-10-11T..." }

    Note over FE: FR-CRP-008: Success notification<br/>NFR-USE-003: Green banner, auto-dismiss after 5s
    FE-->>Farmer: ✅ "Crop listing created successfully."<br/>New listing appears at top of dashboard table
```

---

### 2B-1 — Role & RBAC Rejection

> **v1.1 Fix:** Separated from monolithic 2B diagram. All participants declared at top. Demonstrates `§6.1` (Buyer blocked from Farmer-only route) and `§6.3` (403 for role-level denial).

```mermaid
sequenceDiagram
    actor Buyer as 🏪 B2B Buyer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant RBAC as RBAC Middleware<br/>(Backend Guard)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database

    Note over Buyer,DB: FLOW 2B-1 — Role & RBAC Rejection<br/>Non-Farmer role attempting POST /api/crops

    Buyer->>FE: Attempts to submit crop via POST /api/crops<br/>[JWT contains role='buyer']
    FE->>FE: token = sessionStorage.getItem('agrigrid_token')
    FE->>RBAC: POST /api/crops<br/>Authorization: Bearer eyJhbGc... [role='buyer']

    Note over RBAC: JWT is cryptographically valid.<br/>Extract role claim: role = 'buyer'
    RBAC->>RBAC: claims = decode(jwt)<br/>role = claims['role'] → 'buyer'

    Note over RBAC: §6.1 Route Matrix:<br/>POST /api/crops: Farmer ✅ | B2B Buyer ❌<br/>§6.3: Role-level denial → HTTP 403<br/>(Not 404 — the route exists; the role is wrong)
    RBAC-->>FE: HTTP 403 Forbidden<br/>{ "error": "Access denied. You do not have permission to access this resource." }
    FE-->>Buyer: ❌ Access denied — request terminated at RBAC layer<br/>Backend and DB are never reached
```

---

### 2B-2 — Input & Temporal Validation Cascade

> **v1.1 Fix:** Separated from monolithic 2B. Participant `Farmer` declared at top. Uses `alt...else...end` to show that only ONE branch fires per request — these are mutually exclusive failure modes of a single submission. Demonstrates `FR-CRP-004A` (taxonomy), `FR-CRP-006A` (temporal), and `§8.3` (error table).

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant RBAC as RBAC Middleware<br/>(Backend Guard)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database

    Note over Farmer,DB: FLOW 2B-2 — Input & Temporal Validation Cascade<br/>Mutually exclusive: only ONE branch fires per request

    Farmer->>FE: Submits crop form with invalid data
    FE->>RBAC: POST /api/crops<br/>Authorization: Bearer eyJhbGc... [role='farmer']
    RBAC->>BE: Forward (JWT valid, role=farmer, farmer_id=7)

    Note over BE: Backend runs validation checks in sequence.<br/>Returns on first failure found.

    alt FR-CRP-004A: crop_name not in approved taxonomy
        Note over BE: e.g. crop_name = "Mango" not in<br/>[Wheat, Rice, Tomato, Potato, Cotton, Maize, Sugarcane, Other]
        BE-->>FE: HTTP 400 "Invalid crop name. Must be one of: Wheat, Rice, Tomato, Potato, Cotton, Maize, Sugarcane, Other."
        FE-->>Farmer: ❌ Red border on crop_name dropdown
    else §8.3: acreage ≤ 0
        BE-->>FE: HTTP 400 "Acreage must be a positive number."
        FE-->>Farmer: ❌ Red border on acreage field
    else §8.3: quantity_kg ≤ 0
        BE-->>FE: HTTP 400 "Quantity must be a positive number."
        FE-->>Farmer: ❌ Red border on quantity_kg field
    else §8.3: gps_latitude outside [-90, 90]
        BE-->>FE: HTTP 400 "Latitude must be between -90 and 90."
        FE-->>Farmer: ❌ Red border on gps_latitude field
    else §8.3: gps_longitude outside [-180, 180]
        BE-->>FE: HTTP 400 "Longitude must be between -180 and 180."
        FE-->>Farmer: ❌ Red border on gps_longitude field
    else FR-CRP-006A Rule 1: planting_date is in the future
        Note over BE: e.g. planting_date = "2027-06-01" > CURRENT_DATE = "2026-10-11"
        BE-->>FE: HTTP 400 "Planting date cannot be in the future."
        FE-->>Farmer: ❌ Red border on planting_date field
    else FR-CRP-006A Rule 2: planting_date older than 365 days
        Note over BE: e.g. planting_date = "2020-01-01" < CURRENT_DATE − 365 days
        BE-->>FE: HTTP 400 "Planting date cannot be older than 365 days for an active listing."
        FE-->>Farmer: ❌ Red border on planting_date field
    else FR-CRP-006A Rule 3: estimated_harvest_date ≤ planting_date
        Note over BE: e.g. harvest "2026-08-01" is before planting "2026-09-01"
        BE-->>FE: HTTP 400 "Estimated harvest date must be after planting date."
        FE-->>Farmer: ❌ Red border on estimated_harvest_date field
    else All validations pass
        Note over BE: Proceeds to SQL INSERT — see Diagram 2A
        BE-->>FE: HTTP 201 (see Diagram 2A for full success flow)
        FE-->>Farmer: ✅ Crop created (see Diagram 2A)
    end
```

---

### 2B-3 — DB Write Failure & Rollback

> **v1.1 Fix:** Isolated from 2B monolith. Demonstrates `NFR-REL-001` (ACID rollback on INSERT failure), `§8.3` (HTTP 500 response), `NFR-USE-003` (red error banner), `NFR-USE-004` (spinner removed, button re-enabled).

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant RBAC as RBAC Middleware<br/>(Backend Guard)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database<br/>(Listings Table)

    Note over Farmer,DB: FLOW 2B-3 — DB Write Failure & Rollback<br/>All input validation passes — failure occurs at persistence layer

    Farmer->>FE: Submits fully valid crop form
    Note over FE: NFR-USE-004: Show loading spinner, disable submit button
    FE->>RBAC: POST /api/crops<br/>Authorization: Bearer eyJhbGc...
    RBAC->>BE: Forward (JWT valid, role=farmer, farmer_id=7)

    Note over BE: All validations pass ✅<br/>status = 'Active' | is_deleted = FALSE
    BE->>DB: INSERT INTO Listings (...) VALUES (...)

    alt NFR-REL-001: DB write fails (connection timeout / constraint violation)
        DB-->>BE: SQL Error — INSERT failed
        Note over BE: ACID rollback ensures no partial state.<br/>§8.3: Log error server-side (never expose internals)
        BE-->>FE: HTTP 500 "An internal error occurred. Please try again later."
        Note over FE: NFR-USE-003: Red error banner, auto-dismiss 5s<br/>NFR-USE-004: Remove spinner, re-enable submit button
        FE-->>Farmer: ❌ "An internal error occurred. Please try again later."
    else DB write succeeds
        DB-->>BE: listing_id = 101 returned
        BE-->>FE: HTTP 201 — see Diagram 2A
        FE-->>Farmer: ✅ Crop created (see Diagram 2A)
    end
```

---

## Diagram 3 — Active Crop READ (Paginated List)

> **SRS Reference:** `FR-CRP-010`, `FR-CRP-011`, `FR-CRP-012`, `FR-CRP-013`, `NFR-SEC-004`, `NFR-REL-001`, `§6.1`, `§6.2`
>
> **Key SRS Rules:** `FR-CRP-011` — `GET /api/crops?page=1&limit=20` with pagination metadata `{ data, page, limit, total }`. Two-query pattern: `COUNT(*)` for total, then `SELECT` with `LIMIT/OFFSET`. `NFR-SEC-004` Zero-Trust: `farmer_id` from JWT only. Filter: `is_deleted = FALSE`.

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant RBAC as RBAC Middleware<br/>(Backend Guard)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database<br/>(Listings Table)

    Note over Farmer,DB: DIAGRAM 3 — Crop READ: Paginated List<br/>GET /api/crops?page=1&limit=20

    Farmer->>FE: Views Farmer Dashboard<br/>(or clicks a pagination control — e.g. Next Page)
    Note over FE: FR-CRP-011: Build paginated request URL<br/>page=1, limit=20 (configurable)
    FE->>FE: token = sessionStorage.getItem('agrigrid_token')
    FE->>RBAC: GET /api/crops?page=1&limit=20<br/>Authorization: Bearer eyJhbGc...

    Note over RBAC: Validate JWT signature + expiry<br/>§6.1: GET /api/crops — Farmer role only
    RBAC->>RBAC: claims = decode(jwt) | verify role = 'farmer'
    RBAC->>BE: Forward with claims { farmer_id: 7 }

    Note over BE: NFR-SEC-004 Zero-Trust:<br/>farmer_id = 7 extracted from JWT claims ONLY<br/>Never from query params or request body<br/>§6.2: WHERE clause always includes farmer_id + is_deleted = FALSE

    Note over BE,DB: FR-CRP-011 Two-Query Pagination Pattern:<br/>Query 1 → COUNT(*) for total field in response metadata<br/>Query 2 → paginated data rows with LIMIT/OFFSET

    BE->>DB: SELECT COUNT(*) FROM Listings<br/>WHERE farmer_id = 7<br/>AND is_deleted = FALSE
    DB-->>BE: { total: 47 }

    BE->>DB: SELECT listing_id, crop_name, planting_date,<br/>estimated_harvest_date, acreage,<br/>quantity_kg, status, created_at<br/>FROM Listings<br/>WHERE farmer_id = 7<br/>AND is_deleted = FALSE<br/>ORDER BY created_at DESC<br/>LIMIT 20 OFFSET 0

    alt DB returns 0 rows (FR-CRP-013: Empty state)
        DB-->>BE: Empty result set (total was already 0)
        BE-->>FE: HTTP 200 { "data": [], "page": 1, "limit": 20, "total": 0 }
        Note over FE: FR-CRP-013: Render empty-state message
        FE-->>Farmer: ✅ "You have no active crops.<br/>Click 'Add New Crop' to get started."
    else DB returns 1 or more rows
        DB-->>BE: Up to 20 listing rows
        BE-->>FE: HTTP 200<br/>{ "data": [ {...}, {...}, ... ],<br/>"page": 1, "limit": 20, "total": 47 }
        Note over FE: FR-CRP-012: Display each row with<br/>crop_name, planting_date, estimated_harvest_date,<br/>acreage, quantity_kg, status<br/>Pagination controls: Page 1 of 3 (20 of 47)
        FE-->>Farmer: ✅ Listing table rendered<br/>Showing 20 of 47 listings (Page 1 of 3)
    end
```

---

## Diagram 4 — Active Crop READ (Single Detail)

> **SRS Reference:** `FR-CRP-014`, `FR-CRP-014A`, `§6.1`, `§6.2`, `§6.3`, `§8.3`

---

### 4A — Happy Path: Single Listing Retrieved

> **Key SRS Rules:** `FR-CRP-014` — Farmer clicks listing to view full detail. `FR-CRP-014A` — `GET /api/crops/{listing_id}` returns HTTP 200 with full object including GPS coordinates. Zero-Trust composite query: `WHERE listing_id = ? AND farmer_id = ? AND is_deleted = FALSE`.

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant RBAC as RBAC Middleware<br/>(Backend Guard)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database<br/>(Listings Table)

    Note over Farmer,DB: DIAGRAM 4A — Crop READ Single Detail: Happy Path<br/>GET /api/crops/{listing_id}

    Farmer->>FE: Clicks listing row to view full detail (FR-CRP-014)<br/>listing_id = 101 (from selected row in dashboard)
    FE->>FE: token = sessionStorage.getItem('agrigrid_token')
    FE->>RBAC: GET /api/crops/101<br/>Authorization: Bearer eyJhbGc...

    Note over RBAC: Validate JWT | verify role = 'farmer'
    RBAC->>RBAC: claims = decode(jwt) | farmer_id = 7
    RBAC->>BE: Forward with claims { farmer_id: 7 }

    Note over BE,DB: FR-CRP-014A Zero-Trust Composite Query:<br/>listing_id AND farmer_id AND is_deleted are all in the WHERE clause.<br/>A single query handles both auth and data retrieval atomically.
    BE->>DB: SELECT listing_id, farmer_id, crop_name,<br/>planting_date, estimated_harvest_date,<br/>acreage, gps_latitude, gps_longitude,<br/>quantity_kg, status, is_deleted,<br/>created_at, updated_at<br/>FROM Listings<br/>WHERE listing_id = 101<br/>AND farmer_id = 7<br/>AND is_deleted = FALSE

    DB-->>BE: Full listing row returned
    BE-->>FE: HTTP 200<br/>{ listing_id: 101, farmer_id: 7,<br/>crop_name: "Wheat",<br/>planting_date: "2026-09-01",<br/>estimated_harvest_date: "2027-01-15",<br/>acreage: 12.5,<br/>gps_latitude: 30.3753,<br/>gps_longitude: 69.3451,<br/>quantity_kg: 5000.00,<br/>status: "Active",<br/>created_at: "2026-10-11T...",<br/>updated_at: "2026-10-11T..." }

    FE-->>Farmer: ✅ Full listing detail view displayed<br/>including GPS coordinates (FR-CRP-014)
```

---

### 4B — Security Check: Unified 404 Response

> **Key SRS Rules:** `FR-CRP-014A` — Backend returns HTTP **404** (not 403) for both "listing does not exist" AND "listing belongs to a different farmer." The composite `WHERE` clause makes both scenarios produce an identical empty result — the backend cannot and does not distinguish between them. This is the CTO GAP-3 Fix: prevents integer-based listing ID enumeration across tenants.

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant RBAC as RBAC Middleware<br/>(Backend Guard)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database<br/>(Listings Table)

    Note over Farmer,DB: DIAGRAM 4B — Crop READ Single: Unified 404 Security Check<br/>GET /api/crops/{listing_id}<br/>CTO GAP-3 Fix: Integer ID Enumeration Prevention

    Note over Farmer,DB: Two attack scenarios that produce identical system behavior:
    Note over Farmer,DB: Scenario 1 — Farmer probes listing_id=999 (does not exist in DB)<br/>Scenario 2 — Farmer probes listing_id=200 (exists, owned by farmer_id=12, not farmer_id=7)

    Farmer->>FE: GET /api/crops/999 (or /api/crops/200)
    FE->>RBAC: GET /api/crops/{id}<br/>Authorization: Bearer eyJhbGc... [farmer_id=7]
    RBAC->>RBAC: JWT valid | role = 'farmer'
    RBAC->>BE: Forward with claims { farmer_id: 7 }

    Note over BE,DB: Zero-Trust composite WHERE clause:<br/>listing_id = ? AND farmer_id = 7 AND is_deleted = FALSE<br/>Both scenarios produce an identical empty result set.<br/>The backend cannot distinguish "not found" from "wrong owner" — intentionally.
    BE->>DB: SELECT * FROM Listings<br/>WHERE listing_id = ?<br/>AND farmer_id = 7<br/>AND is_deleted = FALSE

    DB-->>BE: Empty result set<br/>(Scenario 1: no row for id=999 exists)<br/>(Scenario 2: row for id=200 exists but farmer_id=12 ≠ 7)

    Note over BE: FR-CRP-014A: Return HTTP 404 in BOTH scenarios.<br/>Do NOT return 403 — that would confirm the resource exists.<br/>Attacker scanning IDs receives identical 404 for all unauthorized IDs.
    BE-->>FE: HTTP 404 { "error": "Listing not found." }
    FE-->>Farmer: ❌ "Listing not found."

    Note over Farmer,FE: Security Outcome: An attacker probing sequential IDs<br/>(e.g. /api/crops/1 through /api/crops/10000)<br/>receives HTTP 404 for every unauthorized or non-existent ID.<br/>Listing existence across tenants cannot be inferred.
```

---

## Diagram 5 — Active Crop UPDATE

> **SRS Reference:** `FR-CRP-015`, `FR-CRP-016`, `FR-CRP-017`, `FR-CRP-018`, `FR-CRP-019`, `FR-CRP-020`, `FR-CRP-021`, `FR-CRP-004A`, `FR-CRP-006A`, `§6.1`, `§6.2`, `§8.3`, `NFR-REL-001`
>
> **Key SRS Rules:** `FR-CRP-016` — form pre-filled via `GET /api/crops/{id}` (see Diagram 4A). `FR-CRP-018` — `PUT /api/crops/{listing_id}`. `FR-CRP-019` — ownership check returns HTTP **404** (not 403) if not found or belongs to another farmer. `NFR-REL-001` — ACID-compliant SQL UPDATE.

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant RBAC as RBAC Middleware<br/>(Backend Guard)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database<br/>(Listings Table)

    Note over Farmer,DB: DIAGRAM 5 — Crop UPDATE<br/>PUT /api/crops/{listing_id}

    Note over Farmer,FE: STEP 1: Pre-fill Edit Form (FR-CRP-015, FR-CRP-016)
    Farmer->>FE: Clicks 'Edit' button on listing_id = 101 (FR-CRP-015)
    Note over FE: FR-CRP-016: Fetch current values to pre-fill form<br/>Reuses GET /api/crops/{id} endpoint (see Diagram 4A)
    FE->>RBAC: GET /api/crops/101<br/>Authorization: Bearer eyJhbGc...
    RBAC->>BE: Forward (JWT valid, farmer_id=7)
    BE->>DB: SELECT * FROM Listings<br/>WHERE listing_id = 101 AND farmer_id = 7 AND is_deleted = FALSE
    DB-->>BE: Current listing data
    BE-->>FE: HTTP 200 — full listing object
    FE-->>Farmer: Edit form rendered with current values pre-filled<br/>crop_name: "Wheat" | quantity_kg: 5000.00 | etc.

    Note over Farmer,FE: STEP 2: Farmer Edits and Submits (FR-CRP-017, FR-CRP-018)
    Farmer->>FE: Modifies fields:<br/>quantity_kg: 6500.00<br/>estimated_harvest_date: "2027-02-01"
    Farmer->>FE: Clicks 'Save Changes'
    Note over FE: NFR-USE-004: Show loading spinner, disable save button
    FE->>FE: token = sessionStorage.getItem('agrigrid_token')
    FE->>RBAC: PUT /api/crops/101<br/>Authorization: Bearer eyJhbGc...<br/>{ crop_name: "Wheat", planting_date: "2026-09-01",<br/>estimated_harvest_date: "2027-02-01", acreage: 12.5,<br/>gps_latitude: 30.3753, gps_longitude: 69.3451,<br/>quantity_kg: 6500.00 }

    Note over RBAC: §6.1: PUT /api/crops/{id} — Farmer only
    RBAC->>RBAC: JWT valid | role = 'farmer' | farmer_id = 7
    RBAC->>BE: Forward with claims { farmer_id: 7 }

    Note over BE: Run same validations as CREATE:<br/>FR-CRP-004A: crop_name in taxonomy whitelist<br/>FR-CRP-006A: temporal boundaries<br/>§8.3: numeric range checks

    alt Input validation fails (taxonomy / temporal / numeric — see Diagram 2B-2)
        BE-->>FE: HTTP 400 { "error": "..." }
        Note over FE: NFR-USE-002: Inline field error displayed<br/>NFR-USE-004: Spinner removed, save button re-enabled
        FE-->>Farmer: ❌ Specific validation error message
    else All input validation passes
        Note over BE,DB: FR-CRP-019: Zero-Trust ownership verification<br/>before executing UPDATE
        BE->>DB: SELECT listing_id FROM Listings<br/>WHERE listing_id = 101<br/>AND farmer_id = 7<br/>AND is_deleted = FALSE
        alt FR-CRP-019: Listing not found OR belongs to different farmer
            DB-->>BE: Empty result
            Note over BE: HTTP 404 (not 403) — prevents ID enumeration<br/>Same unified response as Diagram 4B
            BE-->>FE: HTTP 404 { "error": "Listing not found." }
            FE-->>Farmer: ❌ "Listing not found."
        else Ownership confirmed — execute UPDATE
            DB-->>BE: listing_id = 101 (confirmed owned by farmer_id=7)
            Note over BE,DB: NFR-REL-001: ACID-compliant SQL UPDATE
            BE->>DB: UPDATE Listings<br/>SET crop_name = 'Wheat',<br/>planting_date = '2026-09-01',<br/>estimated_harvest_date = '2027-02-01',<br/>acreage = 12.5,<br/>gps_latitude = 30.3753,<br/>gps_longitude = 69.3451,<br/>quantity_kg = 6500.00,<br/>updated_at = CURRENT_TIMESTAMP<br/>WHERE listing_id = 101 AND farmer_id = 7
            DB-->>BE: UPDATE successful (1 row affected)
            BE-->>FE: HTTP 200<br/>{ listing_id: 101, crop_name: "Wheat",<br/>quantity_kg: 6500.00,<br/>estimated_harvest_date: "2027-02-01",<br/>status: "Active",<br/>updated_at: "2026-10-11T..." }
            Note over FE: FR-CRP-021: Success notification<br/>NFR-USE-003: Green banner, auto-dismiss 5s
            FE-->>Farmer: ✅ "Crop listing updated successfully."<br/>Dashboard row refreshed with updated values
        end
    end
```

---

## Diagram 6 — Active Crop WITHDRAW (Soft-Delete)

> **SRS Reference:** `FR-CRP-022`, `FR-CRP-023`, `FR-CRP-024`, `FR-CRP-025`, `FR-CRP-026`, `FR-CRP-027`, `§6.1`, `§6.2`, `§6.3`, `§8.3`, `NFR-REL-001`
>
> **Key SRS Rules:** `FR-CRP-022` — UI button labeled **"Withdraw"** (not "Delete"). `FR-CRP-023` — Confirmation dialog. `FR-CRP-024` — HTTP method is `DELETE` but backend behavior is a soft-delete. `FR-CRP-025` — Physical SQL `DELETE` is **PROHIBITED**. Backend executes `UPDATE ... SET is_deleted = TRUE, status = 'Withdrawn'`. `FR-CRP-027` — Remove row from dashboard without reload. Provenance reason: `Listings` rows are FK roots for Increments 2–5 (Escrow, Telemetry, Diagnostics, QR Storyboard).

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(HTML/CSS/JS)
    participant RBAC as RBAC Middleware<br/>(Backend Guard)
    participant BE as Backend Server<br/>(Python Flask/Django)
    participant DB as SQL Database<br/>(Listings Table)

    Note over Farmer,DB: DIAGRAM 6 — Crop WITHDRAW (Soft-Delete)<br/>DELETE /api/crops/{listing_id}<br/>Physical SQL DELETE is PROHIBITED — provenance integrity mandate

    Farmer->>FE: Clicks 'Withdraw' button on listing_id = 101 (FR-CRP-022)
    Note over FE: FR-CRP-023: Show confirmation dialog before any network call
    FE-->>Farmer: ⚠️ Confirmation dialog:<br/>"Are you sure you want to withdraw this crop listing?<br/>The record will be archived and hidden from your active dashboard."

    alt Farmer clicks 'Cancel'
        Farmer->>FE: Cancel
        FE-->>Farmer: Dialog dismissed — no action taken, no request sent
    else Farmer clicks 'Confirm Withdraw'
        Farmer->>FE: Confirm Withdraw
        Note over FE: NFR-USE-004: Show loading spinner, disable withdraw button
        FE->>FE: token = sessionStorage.getItem('agrigrid_token')
        Note over FE: FR-CRP-024: HTTP verb is DELETE for RESTful convention.<br/>Backend semantics are a soft-delete UPDATE, not a physical DELETE.
        FE->>RBAC: DELETE /api/crops/101<br/>Authorization: Bearer eyJhbGc...

        Note over RBAC: §6.1: DELETE /api/crops/{id} — Farmer role only
        RBAC->>RBAC: JWT valid | role = 'farmer' | farmer_id = 7
        RBAC->>BE: Forward with claims { farmer_id: 7 }

        Note over BE,DB: FR-CRP-025: Zero-Trust ownership check before soft-delete
        BE->>DB: SELECT listing_id FROM Listings<br/>WHERE listing_id = 101<br/>AND farmer_id = 7<br/>AND is_deleted = FALSE

        alt FR-CRP-025: Listing not found OR belongs to different farmer
            DB-->>BE: Empty result
            Note over BE: HTTP 404 (not 403) — unified response<br/>prevents integer ID enumeration (CTO GAP-3 Fix)
            BE-->>FE: HTTP 404 { "error": "Listing not found." }
            Note over FE: NFR-USE-004: Remove spinner, re-enable button
            FE-->>Farmer: ❌ "Listing not found."
        else Ownership confirmed — execute soft-delete
            DB-->>BE: listing_id = 101 (confirmed active, owned by farmer_id=7)
            Note over BE,DB: FR-CRP-025: SOFT-DELETE ONLY<br/>Physical SQL DELETE is STRICTLY PROHIBITED.<br/>Listings are FK roots for Inc 2 Escrow, Inc 3 Telemetry,<br/>Inc 4 Diagnostics, and Inc 5 Consumer QR Storyboard.<br/>Hard deletion would orphan all downstream FK chains.
            BE->>DB: UPDATE Listings<br/>SET is_deleted = TRUE,<br/>status = 'Withdrawn',<br/>updated_at = CURRENT_TIMESTAMP<br/>WHERE listing_id = 101<br/>AND farmer_id = 7
            DB-->>BE: UPDATE successful (1 row affected)<br/>Row is now archived — invisible to active queries
            Note over BE: FR-CRP-026: Return success response
            BE-->>FE: HTTP 200 { "message": "Listing withdrawn successfully." }
            Note over FE: FR-CRP-027: Remove row from dashboard view<br/>without full page reload (DOM update only)<br/>NFR-USE-003: Green banner, auto-dismiss 5s
            FE-->>Farmer: ✅ "Listing withdrawn successfully."<br/>Row removed from active dashboard table
        end
    end
```

---

## Participant Legend

| Participant Symbol | Full Name | Technology (Increment 1) | SRS Section |
|---|---|---|---|
| 👨‍🌾 Farmer (Browser) | The Farmer Actor | Any modern browser (Chrome, Firefox, Safari, Edge — latest 2 versions) | §2.2, §2.3 |
| 🏪 B2B Buyer (Browser) | The B2B Buyer Actor (Increment 1: provisioned only) | Same browser stack — shown in 2B-1 for RBAC rejection demo | §2.2 |
| Frontend (HTML/CSS/JS) | The Presentation Layer | HTML5, CSS3, Vanilla JavaScript with fetch/axios | §2.3, Doc 3 §1 |
| RBAC Middleware (Backend Guard) | The Security Gateway | Python decorator / middleware on Flask/Django routes | §6.1, §6.2, §6.3 |
| Backend Server (Python Flask/Django) | The Application Logic Layer | Python 3.x — Flask or Django | §2.3, Doc 3 §1 |
| SQL Database | The Persistence Layer | SQLite3 (prototype) → MySQL/PostgreSQL (deployment) | §2.3, §7.1–7.4, Doc 3 §1 |

---

## SRS Requirement Traceability

| Diagram | Requirement IDs Demonstrated |
|---|---|
| **1A — Farmer Registration** | FR-LGN-017, FR-LGN-018, FR-LGN-018A, FR-LGN-019, FR-LGN-020, FR-LGN-021, NFR-SEC-001, NFR-SEC-008, §8.2 |
| **1B — Login & JWT Issuance** | FR-LGN-004–FR-LGN-016, FR-LGN-022, §3.3 JWT Contract, NFR-SEC-001, NFR-PERF-001 (LEFT JOIN optimization) |
| **1C — Route Guard & Dashboard Load** | FR-LGN-011, FR-LGN-013, FR-LGN-022, FR-LGN-023, FR-CRP-011, NFR-SEC-002, NFR-SEC-003, §6.1, §6.3 |
| **2A — Crop CREATE (Happy Path)** | FR-CRP-001–FR-CRP-009, FR-CRP-004A, FR-CRP-005, FR-CRP-006A, NFR-SEC-004, NFR-REL-001, NFR-USE-003, NFR-USE-004 |
| **2B-1 — RBAC Role Rejection** | §6.1 (Route Matrix), §6.3 (403 role-level denial) |
| **2B-2 — Input & Temporal Validation** | FR-CRP-004A, FR-CRP-006A (Rules 1–3), §8.3 (all validation error rows), NFR-USE-002 |
| **2B-3 — DB Write Failure** | NFR-REL-001 (ACID rollback), §8.3 (HTTP 500 row), NFR-USE-003, NFR-USE-004 |
| **3 — Crop READ (Paginated List)** | FR-CRP-010, FR-CRP-011 (pagination + COUNT(*) + LIMIT/OFFSET), FR-CRP-012, FR-CRP-013, NFR-SEC-004, §6.1, §6.2 |
| **4A — Crop READ (Single — Happy Path)** | FR-CRP-014, FR-CRP-014A, §6.1, §6.2, NFR-SEC-004 |
| **4B — Crop READ (Single — Unified 404)** | FR-CRP-014A, §6.2, §6.3, §8.3 (CTO GAP-3: enumeration prevention) |
| **5 — Crop UPDATE** | FR-CRP-015–FR-CRP-021, FR-CRP-004A, FR-CRP-006A, FR-CRP-019 (404 ownership check), NFR-REL-001, NFR-USE-002, NFR-USE-003, NFR-USE-004, §6.1, §6.2, §8.3 |
| **6 — Crop WITHDRAW (Soft-Delete)** | FR-CRP-022–FR-CRP-027, FR-CRP-025 (soft-delete SQL, hard DELETE PROHIBITED), §6.1, §6.2, §8.3, NFR-REL-001, NFR-USE-003, NFR-USE-004 |

---

## Revision History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-10-11 | Requirements & Architecture Agent | Initial release. Five diagrams covering Flows 1A, 1B, 1C, 2A, 2B (monolithic). |
| 1.1 | 2026-10-11 | Requirements & Architecture Agent — CTO Review Applied | **Critical Fixes:** (1) All `alt...end` fall-through blocks replaced with `alt...else...end` proper branching — errors now visually terminate execution. (2) Login (1B) optimized to single LEFT JOIN query (eliminates redundant DB round-trip, supports NFR-PERF-001). (3) Added COUNT(*) companion query in 1C for pagination `total` field (FR-CRP-011). (4) Split monolithic 2B into three isolated sub-flows: 2B-1 (RBAC rejection), 2B-2 (validation cascade), 2B-3 (DB failure). (5) Moved Buyer actor declaration to diagram top (fixes Mermaid layout rendering bug). **New Diagrams:** Added Diagram 3 (READ paginated list), Diagram 4A/4B (READ single detail + unified 404), Diagram 5 (UPDATE with pre-fill + ownership check), Diagram 6 (WITHDRAW soft-delete with confirmation dialog + SQL). Traceability matrix updated. |

---

*End of Document — AG-SSD-INC1-002 v1.1*
