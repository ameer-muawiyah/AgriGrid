# API & JSON Payload Contracts Delta
## Increment 2: Core Data Engine & Demand Side (B2B Marketplace, Escrow & Predictive Yield)

| Field | Value |
|---|---|
| **Project Name** | Agri-Grid: Smart Agriculture & Food Security Ecosystem |
| **Document ID** | `AG-API-INC2-003` |
| **Version** | 1.0 (Formal Deliverable) |
| **Prepared By** | Iqra Fayaz (Software Architect & API Designer — author of Increment 1 API Contracts) |
| **Reviewed By** | Manahil Sohail (Lead Requirements Engineer) & Ameer Muawiyah (Scrum Master + Lead Data Architect) |
| **Date** | 2026-11-14 |
| **Baseline Source** | `AG-SRS-INC2-001 v1.2`, `AG-SSD-INC2-002 v1.1`, `0_Increment_2_Master_Plan.md v1.1` |
| **Increment 1 Base Reference** | `AG-API-INC1-003 v1.0` (`3_Farmer_API_Contracts.md`) |
| **Primary Location** | `./Documentation/Increment_2_API_Contracts_Delta.md` |
| **Mirror Location** | `./Architecture Blueprints/Increment_2/3_Increment_2_API_Contracts.md` |

---

## Table of Contents
1. [Overview & Delta Specification Scope](#1-overview--delta-specification-scope)
2. [Global Architectural Standards & Pinned Decisions](#2-global-architectural-standards--pinned-decisions)
   - 2.1 [Zero-Trust Multi-Tenancy & Identity Enforcement](#21-zero-trust-multi-tenancy--identity-enforcement)
   - 2.2 [Universal List Envelope Standard](#22-universal-list-envelope-standard)
   - 2.3 [403 vs Unified 404 Anti-Enumeration Doctrine](#23-403-vs-unified-404-anti-enumeration-doctrine)
   - 2.4 [Pinned 404 Error Strings](#24-pinned-404-error-strings)
   - 2.5 [Atomic Financial Integrity & Order Number Generation](#25-atomic-financial-integrity--order-number-generation)
   - 2.6 [Scope Boundaries & Deferred Seams](#26-scope-boundaries--deferred-seams)
3. [Global Authentication & Extended JWT Claims Delta](#3-global-authentication--extended-jwt-claims-delta)
4. [Module 1: Authentication & Identity Delta Endpoints](#4-module-1-authentication--identity-delta-endpoints)
   - 4.1 [Endpoint 1: Buyer Registration Delta (`POST /api/auth/register`)](#41-endpoint-1-buyer-registration-delta-post-apiauthregister)
   - 4.2 [Endpoint 2: User Login Claims & Response Delta (`POST /api/auth/login`)](#42-endpoint-2-user-login-claims--response-delta-post-apiauthlogin)
5. [Module 2: B2B Marketplace Procurement Endpoints](#5-module-2-b2b-marketplace-procurement-endpoints)
   - 5.1 [Endpoint 3: Marketplace Catalog Browse (`GET /api/marketplace/listings`)](#51-endpoint-3-marketplace-catalog-browse-get-apimarketplacelistings)
   - 5.2 [Endpoint 4: Single Marketplace Listing Detail (`GET /api/marketplace/listings/<id>`)](#52-endpoint-4-single-marketplace-listing-detail-get-apimarketplacelistingsid)
6. [Module 3: Escrow Orders & Settlement Endpoints](#6-module-3-escrow-orders--settlement-endpoints)
   - 6.1 [Endpoint 5: Escrow Checkout (`POST /api/orders`)](#61-endpoint-5-escrow-checkout-post-apiorders)
   - 6.2 [Endpoint 6: Delivery Confirmation & Escrow Release (`POST /api/orders/<id>/confirm-delivery`)](#62-endpoint-6-delivery-confirmation--escrow-release-post-apiordersidconfirm-delivery)
   - 6.3 [Endpoint 7: Order Cancellation & Inventory Restoration (`POST /api/orders/<id>/cancel`)](#63-endpoint-7-order-cancellation--inventory-restoration-post-apiordersidcancel)
   - 6.4 [Endpoint 8: Order Dispute Flagging (`POST /api/orders/<id>/dispute`)](#64-endpoint-8-order-dispute-flagging-post-apiordersiddispute)
   - 6.5 [Endpoint 9: Buyer Order History (`GET /api/orders/buyer`)](#65-endpoint-9-buyer-order-history-get-apiordersbuyer)
   - 6.6 [Endpoint 10: Farmer Incoming Orders (`GET /api/orders/farmer`)](#66-endpoint-10-farmer-incoming-orders-get-apiordersfarmer)
7. [Module 4: Environmental Telemetry & Predictive Intelligence Endpoints](#7-module-4-environmental-telemetry--predictive-intelligence-endpoints)
   - 7.1 [Endpoint 11: Environmental Telemetry Fetch (`GET /api/telemetry/weather` & `GET /api/telemetry/soil`)](#71-endpoint-11-environmental-telemetry-fetch-get-apitelemetryweather--get-apitelemetrysoil)
   - 7.2 [Endpoint 12: Predictive Yield Forecast (`POST /api/yield/predict`)](#72-endpoint-12-predictive-yield-forecast-post-apiyieldpredict)
8. [Module 5: Active Crop Commercial Pricing Delta](#8-module-5-active-crop-commercial-pricing-delta)
   - 8.1 [Endpoint 13: Commercial Pricing & Batch Publication Delta (`PUT /api/crops/<id>`)](#81-endpoint-13-commercial-pricing--batch-publication-delta-put-apicropsid)
9. [Master Role × Outcome Authorization Matrix](#9-master-role--outcome-authorization-matrix)
10. [Traceability Matrix (Contracts to SRS v1.2 & Sequence Diagrams v1.1)](#10-traceability-matrix-contracts-to-srs-v12--sequence-diagrams-v11)
11. [Verification & Validation Sign-Off Block](#11-verification--validation-sign-off-block)

---

## 1. Overview & Delta Specification Scope

This document serves as the formal **Increment 2 API Contracts Delta (`AG-API-INC2-003`)**, defining the precise interface specifications, role authorization boundaries, JSON request/response envelopes, field validation taxonomies, and exact error strings between the **Frontend Presentation Layer** and the **Flask/SQLite Backend Engine**.

### Relationship to Baseline Contracts (`AG-API-INC1-003`)
* This is a **strict delta companion document**. It specifies ONLY the 13 endpoints added, extended, or mutated in Increment 2.
* All unchanged Increment 1 endpoints (`GET /api/crops`, `POST /api/crops` base fields, `GET /api/crops/<id>`, `DELETE /api/crops/<id>`, `GET /api/crops/stats`, `POST /api/auth/logout`, `GET /api/auth/me`) retain their definitions and payload formats as specified in `AG-API-INC1-003 v1.0` (`3_Farmer_API_Contracts.md`).
* **Zero Standalone Wallet Endpoint**: Increment 2 features **no** independent `/api/wallets/*` endpoint. Virtual ledger balances are reported directly within buyer onboarding (`POST /api/auth/register`), buyer login (`POST /api/auth/login`), and escrow checkout confirmation (`POST /api/orders`) responses.
* **Inactive Role Policy**: Roles reserved for future increments (`transporter` in Increment 3, `agronomist` and `compliance_officer` in Increment 4) possess zero access grants and receive immediate `HTTP 403 Forbidden` on all protected Increment 2 endpoints.

---

## 2. Global Architectural Standards & Pinned Decisions

### 2.1 Zero-Trust Multi-Tenancy & Identity Enforcement (`NFR-SEC-001`)
* Tenant identities (`farmer_id`, `buyer_id`, `user_id`) are **strictly extracted on the backend from signed JWT claims**.
* The client application **must never transmit tenant IDs** inside request query parameters or JSON request bodies.
* If a request payload includes `buyer_id`, `farmer_id`, or `user_id`, the backend must silently discard or reject these fields, binding the transaction exclusively to the authenticated JWT identity.

### 2.2 Universal List Envelope Standard (`Plan §6 Universal Rule`, `FR-MKT-004`, `FR-ORD-008`, `FR-ORD-009`)
All Increment 2 collection/list endpoints (`/api/marketplace/listings`, `/api/orders/buyer`, `/api/orders/farmer`) strictly adhere to the established Increment 1 flat list envelope without nesting:
```json
{
  "success": true,
  "data": [ ... ],
  "page": 1,
  "limit": 20,
  "total": 1
}
```
* `success`: boolean (`true` on HTTP 200).
* `data`: array of objects representing the paginated result items.
* `page`: integer representing the requested/current 1-indexed page.
* `limit`: integer representing the maximum items per page.
* `total`: integer representing the total matching records across the entire dataset (computed via companion `SELECT COUNT(*)` query).

### 2.3 403 vs Unified 404 Anti-Enumeration Doctrine (`NFR-SEC-002`)
To guarantee tenant privacy and prevent malicious database enumeration:
1. **Wrong Role $\rightarrow$ `HTTP 403 Forbidden`**: Calling an endpoint with a valid token whose role is not authorized for that endpoint (e.g., a farmer calling buyer checkout or a buyer calling farmer inbound orders) immediately returns `HTTP 403 Forbidden` with `"error": "Access denied."`.
2. **Right Role, Wrong Owner $\rightarrow$ Unified `HTTP 404 Not Found`**: Calling an endpoint with an authorized role targeting a record that either does not exist OR belongs to another tenant returns `HTTP 404 Not Found`. Identical payloads are returned regardless of whether the ID is missing, belongs to a competitor, or is soft-deleted.

### 2.4 Pinned 404 Error Strings (`Pinned Decision 1`)
* **New Increment 2 Marketplace & Yield Listing Lookups**:
  ```json
  { "success": false, "error": "Listing not found." }
  ```
  *(Governed by `FR-MKT-007` and `FR-YLD-003`; deliberately distinct from legacy phrasing).*
* **New Increment 2 Order Lookups** (`confirm-delivery`, `cancel`, `dispute`):
  ```json
  { "success": false, "error": "Order not found." }
  ```
  *(Governed by `NFR-SEC-002`, `FR-SET-001`, `FR-SET-005`, `FR-STM-005`).*
* **Legacy Increment 1 Crop Endpoints**:
  `PUT /api/crops/<id>` retains its pinned string:
  ```json
  { "success": false, "error": "Listing not found." }
  ```
  *(Verified by `backend/test_crops_api.py::TC-13` and `AG-API-INC1-003` §4.4).*

### 2.5 Atomic Financial Integrity & Order Number Generation (`Pinned Decision 2 & 5`, `NFR-SEC-003`)
* **SQLite Transaction Serialization**: All multi-table state transitions (`buyer_wallets`, `orders`, `escrow_holdings`, `listings`, `farmer_wallets`) execute inside explicit `BEGIN IMMEDIATE` transactions.
* **Deterministic Order Numbering**: Inside the `BEGIN IMMEDIATE` transaction, the order row is inserted, its autoincrement integer ID is obtained, and `order_number` is updated before commit to conform to:
  $$\text{order\_number} = \text{ORD-}\{\text{YYYY}\}\text{-}\{\text{ORDER\_ID:04d}\} \quad (\text{e.g. } \text{ORD-2026-8941})$$
  No intermediate state or placeholder number is ever visible or committed.
* **Deterministic Server-Computed Pricing**:
  $$\text{total\_amount\_pkr} = \text{ordered\_quantity\_kg} \times \text{listing.asking\_price\_per\_kg}$$
  The total amount is computed strictly on the backend. Client-provided prices or totals are rejected or ignored.

### 2.6 Scope Boundaries & Deferred Seams (`FR-STM-006`, `Plan §4.3`)
* **Dispute Seam**: In Increment 2, `POST /api/orders/<id>/dispute` permanently transitions the order to `'Disputed'` and escrow to `'DISPUTED'`, freezing funds. No unfreezing, refund, or settlement endpoint exists in Increment 2. Formal dispute resolution is deferred to Increment 4 (Compliance Officer).
* **Auto-Release Seam**: Upon delivery confirmation, `escrow_holdings.auto_release_at` is populated with `datetime(delivered_at + 72 hours)`. This timestamp is stamped as an architectural seam for Increment 4's automated cron worker.

---

## 3. Global Authentication & Extended JWT Claims Delta

### Request Authentication Header
All authenticated endpoints require the standard Bearer header:
```http
Authorization: Bearer <jwt_token>
```

### Extended JWT Token Specification (`Pinned Decision 3`, `NFR-SEC-001`, `FR-BYR-005`)
* **Algorithm**: `HS256`
* **Session Storage Key**: `agrigrid_token`
* **Token Lifetime**: 1,800 seconds (30 minutes)
* **Claims Structure**:

| Claim Key | Data Type | Nullable | Description & Sourcing |
|---|---|:---:|---|
| `user_id` | integer | No | Primary key `users.id` of the authenticated user. |
| `farmer_id` | integer | Yes | Primary key `farmers.id` if `role == 'farmer'`; otherwise `null`. |
| `buyer_id` | integer | Yes | **NEW IN INC 2:** Primary key `buyers.id` if `role == 'buyer'`; otherwise `null`. |
| `role` | string | No | Enum: `['farmer', 'buyer', 'transporter', 'agronomist', 'compliance_officer']`. |
| `exp` | integer | No | Unix epoch timestamp indicating token expiration (issued_at + 1800s). |

#### Example Extended JWT Payload Decoded:
```json
{
  "user_id": 43,
  "farmer_id": null,
  "buyer_id": 4,
  "role": "buyer",
  "exp": 1794695000
}
```

---

## 4. Module 1: Authentication & Identity Delta Endpoints

### 4.1 Endpoint 1: Buyer Registration Delta (`POST /api/auth/register`)
Atomic onboarding for B2B buyers, creating linked `users`, `buyers`, and `buyer_wallets` records in a single database transaction.

* **HTTP Method & Path**: `POST /api/auth/register`
* **Purpose**: Onboard B2B buyer accounts and initialize virtual escrow ledger wallets with Rs. 500,000.00.
* **Authentication**: None (Public endpoint).
* **Traced Requirements**: `FR-BYR-001`, `FR-BYR-002`, `FR-BYR-003`, `FR-BYR-004`, `FR-WLT-003`, `NFR-SEC-003`.
* **Diagram Trace**: Diagram 1 (§3).

#### Role × Outcome Matrix
| Caller Role / State | Expected Status | Outcome Description |
|---|:---:|---|
| Public / Unauthenticated (Valid Buyer Payload) | `201 Created` | User, buyer profile, and Rs. 500k wallet created atomically. |
| Public (Missing Company / Phone / Address) | `400 Bad Request` | Transaction aborted, validation error returned. |
| Public (Password Complexity Violation) | `400 Bad Request` | Password complexity enforced. |
| Public (Duplicate Username) | `409 Conflict` | Conflict returned, zero records created. |
| Database Insert / Rollback Failure | `500 Internal Server Error` | Atomic rollback, zero orphaned records. |

#### Request Specification
* **Headers**: `Content-Type: application/json`
* **JSON Body Fields**:

| Field Name | Type | Required | Validation Rules |
|---|---|:---:|---|
| `username` | string | Yes | 3–50 characters, alphanumeric and underscores, unique. |
| `password` | string | Yes | Min 8 characters, at least 1 uppercase, 1 lowercase, 1 digit. |
| `role` | string | Yes | Must be `"buyer"`. |
| `company_name` | string | Yes | Required for buyer. 2–100 characters. |
| `contact_phone` | string | Yes | Required for buyer. 7–20 characters. |
| `warehouse_address` | string | Yes | Required for buyer. Minimum 5 characters. |
| `warehouse_gps_latitude` | number | No | Optional float between `-90.0` and `90.0`. |
| `warehouse_gps_longitude` | number | No | Optional float between `-180.0` and `180.0`. |

#### Example Request
```json
{
  "username": "sara_buyer",
  "password": "BuyerSecurePass1!",
  "role": "buyer",
  "company_name": "Metro Wholesale Foods",
  "contact_phone": "+92-300-1234567",
  "warehouse_address": "Metro Central Hub, Industrial Area, Lahore",
  "warehouse_gps_latitude": 31.5204,
  "warehouse_gps_longitude": 74.3587
}
```

#### Response Payloads
##### Success (`201 Created`)
```json
{
  "success": true,
  "message": "Buyer registration successful. Please log in.",
  "user": {
    "user_id": 43,
    "username": "sara_buyer",
    "role": "buyer",
    "buyer_id": 4,
    "company_name": "Metro Wholesale Foods",
    "wallet_balance_pkr": 500000.00
  }
}
```

##### Error Catalogue
* **`400 Bad Request` — Missing Base Credentials**:
  ```json
  { "success": false, "error": "All fields are required: username, password, role." }
  ```
* **`400 Bad Request` — Missing Buyer Profile Fields (`FR-BYR-002`)**:
  ```json
  { "success": false, "error": "Company name, phone, and warehouse address are required." }
  ```
* **`400 Bad Request` — Password Complexity**:
  ```json
  { "success": false, "error": "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number." }
  ```
* **`400 Bad Request` — Field Validation / Out-of-Bounds**:
  ```json
  { "success": false, "error": "Invalid buyer company details." }
  ```
* **`409 Conflict` — Duplicate Username**:
  ```json
  { "success": false, "error": "Username already exists." }
  ```
* **`500 Internal Server Error` — Transaction Rollback**:
  ```json
  { "success": false, "error": "Registration failed. Please try again." }
  ```

---

### 4.2 Endpoint 2: User Login Claims & Response Delta (`POST /api/auth/login`)
Authenticates credentials, issues an extended JWT containing `buyer_id`, and serializes buyer profile details in the response body.

* **HTTP Method & Path**: `POST /api/auth/login`
* **Purpose**: Authenticate credentials and return signed JWT with extended claims (`buyer_id`) and role profile.
* **Authentication**: None (Public endpoint).
* **Traced Requirements**: `FR-BYR-005`, `NFR-SEC-001`, `Pinned Decision 3`.
* **Diagram Trace**: Diagram 1 / Increment 1 Foundation.

#### Role × Outcome Matrix
| Caller Role / State | Expected Status | Outcome Description |
|---|:---:|---|
| Public (Valid Buyer Credentials) | `200 OK` | Issues JWT with `buyer_id`, returns user & buyer profile. |
| Public (Valid Farmer Credentials) | `200 OK` | Issues JWT with `farmer_id`, returns user & farmer profile. |
| Public (Invalid Credentials) | `401 Unauthorized` | Generic credential rejection (anti-enumeration). |
| Public (Empty / Missing Fields) | `400 Bad Request` | Missing field rejection. |

#### Request Specification
* **Headers**: `Content-Type: application/json`
* **JSON Body Fields**:
  - `username` (string, required)
  - `password` (string, required)

#### Example Request
```json
{
  "username": "sara_buyer",
  "password": "BuyerSecurePass1!"
}
```

#### Response Payloads
##### Success (`200 OK`) — Buyer Account Variant
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo0MywiZmFybWVyX2lkIjpudWxsLCJidXllcl9pZCI6NCwicm9sZSI6ImJ1eWVyIiwiZXhwIjoxNzk0Njk1MDAwfQ...",
  "role": "buyer",
  "user": {
    "user_id": 43,
    "buyer_id": 4,
    "username": "sara_buyer",
    "company_name": "Metro Wholesale Foods",
    "wallet_balance_pkr": 500000.00
  }
}
```

##### Error Catalogue
* **`400 Bad Request` — Missing Fields**:
  ```json
  { "success": false, "error": "Username and password are required." }
  ```
* **`401 Unauthorized` — Invalid Credentials (Anti-Enumeration)**:
  ```json
  { "success": false, "error": "Invalid credentials." }
  ```

---

## 5. Module 2: B2B Marketplace Procurement Endpoints

### 5.1 Endpoint 3: Marketplace Catalog Browse (`GET /api/marketplace/listings`)
Returns paginated, active, purchasable crops with commercial pricing, batch IDs, and farm origin.

* **HTTP Method & Path**: `GET /api/marketplace/listings`
* **Purpose**: Browse available commercial produce listings in the wholesale marketplace.
* **Authentication**: Required (`Authorization: Bearer <jwt_token>`).
* **Traced Requirements**: `FR-MKT-001`, `FR-MKT-002`, `FR-MKT-003`, `FR-MKT-004`, `FR-MKT-005`, `NFR-PERF-001`.
* **Diagram Trace**: Diagram 2 (§4).

#### Role × Outcome Matrix
| Caller Role | Expected Status | Outcome Description |
|---|:---:|---|
| B2B Buyer (`buyer`) | `200 OK` | Retrieves paginated active catalog listings. |
| Farmer (`farmer`) | `200 OK` | Retrieves paginated active catalog listings (market transparency). |
| Transporter (`transporter`) | `403 Forbidden` | Access denied (role inactive in Increment 2). |
| Agronomist (`agronomist`) | `403 Forbidden` | Access denied (role inactive in Increment 2). |
| Compliance Officer (`compliance_officer`) | `403 Forbidden` | Access denied (role inactive in Increment 2). |
| Unauthenticated / Invalid Token | `401 Unauthorized` | Authentication required. |

#### Request Specification
* **Headers**: `Authorization: Bearer <jwt_token>`
* **Query Parameters**:

| Parameter | Type | Required | Default | Validation / Filtering Rule |
|---|---|:---:|:---:|---|
| `page` | integer | No | `1` | Min value `1`. |
| `limit` | integer | No | `20` | Min value `1`, max value `100`. |
| `crop_name` | string | No | `null` | Must belong to valid crop taxonomy if supplied. |
| `max_price` | number | No | `null` | Must be numeric and strictly `> 0`. Filters `asking_price_per_kg <= max_price`. |
| `sort` | string | No | `date_desc` | Enum: `['price_asc', 'price_desc', 'date_desc']`. |

#### Response Payloads
##### Success (`200 OK`) — Flat List Envelope
```json
{
  "success": true,
  "data": [
    {
      "listing_id": 1,
      "batch_id": "BATCH-2026-WHT-0001",
      "crop_name": "Wheat",
      "quantity_kg": 5000.0,
      "asking_price_per_kg": 45.00,
      "total_price_pkr": 225000.00,
      "estimated_harvest_date": "2027-01-15",
      "farm_name": "Green Acres",
      "farm_location": "Vehari, Punjab",
      "gps_latitude": 30.0444,
      "gps_longitude": 72.3441
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1
}
```

##### Error Catalogue
* **`400 Bad Request` — Invalid Query Parameters**:
  ```json
  { "success": false, "error": "Invalid filter parameters." }
  ```
* **`401 Unauthorized` — Missing / Expired Bearer Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Unauthorized Role**:
  ```json
  { "success": false, "error": "Access denied." }
  ```

---

### 5.2 Endpoint 4: Single Marketplace Listing Detail (`GET /api/marketplace/listings/<id>`)
Retrieves comprehensive commercial and agronomic detail for a single active marketplace listing.

* **HTTP Method & Path**: `GET /api/marketplace/listings/<id>`
* **Purpose**: Inspect single crop listing details for checkout review.
* **Authentication**: Required (`Authorization: Bearer <jwt_token>`).
* **Traced Requirements**: `FR-MKT-006`, `FR-MKT-007`, `NFR-SEC-002`, `Pinned Decision 1`.
* **Diagram Trace**: Diagram 2 (§4).

#### Role × Outcome Matrix
| Caller Role | Target Listing State | Expected Status | Outcome Description |
|---|---|:---:|---|
| Buyer or Farmer | Active, priced, non-deleted | `200 OK` | Returns full listing details. |
| Buyer or Farmer | Non-existent ID | `404 Not Found` | Unified 404 anti-enumeration. |
| Buyer or Farmer | `is_deleted = 1` OR `status != 'Active'` | `404 Not Found` | Unified 404 anti-enumeration. |
| Buyer or Farmer | Unpriced (`asking_price_per_kg IS NULL`) | `404 Not Found` | Unified 404 anti-enumeration. |
| Inactive Roles | Any | `403 Forbidden` | Access denied. |
| Unauthenticated | Any | `401 Unauthorized` | Authentication required. |

#### Request Specification
* **Headers**: `Authorization: Bearer <jwt_token>`
* **URL Parameter**: `id` (integer, required): Target listing primary key.

#### Response Payloads
##### Success (`200 OK`)
```json
{
  "success": true,
  "data": {
    "listing_id": 1,
    "batch_id": "BATCH-2026-WHT-0001",
    "farmer_id": 7,
    "crop_name": "Wheat",
    "acreage": 12.5,
    "quantity_kg": 5000.0,
    "asking_price_per_kg": 45.00,
    "total_price_pkr": 225000.00,
    "planting_date": "2026-09-01",
    "estimated_harvest_date": "2027-01-15",
    "status": "Active",
    "farm_name": "Green Acres",
    "farm_location": "Vehari, Punjab",
    "gps_latitude": 30.0444,
    "gps_longitude": 72.3441,
    "created_at": "2026-10-12T03:15:00Z"
  }
}
```

##### Error Catalogue
* **`401 Unauthorized` — Missing / Invalid Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Unauthorized Role**:
  ```json
  { "success": false, "error": "Access denied." }
  ```
* **`404 Not Found` — Unified Anti-Enumeration (`FR-MKT-007`, `Pinned Decision 1`)**:
  ```json
  { "success": false, "error": "Listing not found." }
  ```

---

## 6. Module 3: Escrow Orders & Settlement Endpoints

### 6.1 Endpoint 5: Escrow Checkout (`POST /api/orders`)
Atomic B2B procurement checkout, locking funds in escrow and transitioning the listing to `'Sold'`.

* **HTTP Method & Path**: `POST /api/orders`
* **Purpose**: Atomically purchase a produce listing, locking funds in escrow under SQLite `BEGIN IMMEDIATE`.
* **Authentication**: Required (`Authorization: Bearer <buyer_jwt>`). Role must be `buyer`.
* **Traced Requirements**: `FR-ORD-001` through `FR-ORD-007`, `NFR-SEC-001`, `NFR-SEC-003`, `NFR-PERF-002`, `Pinned Decision 2 & 5`.
* **Diagram Trace**: Diagram 3 (§5).

#### Role × Outcome Matrix
| Caller Role | Precondition State | Expected Status | Outcome Description |
|---|---|:---:|---|
| B2B Buyer (`buyer`) | Active listing, full quantity, sufficient funds | `201 Created` | Order created, funds locked, listing sold. |
| B2B Buyer (`buyer`) | Missing required fields | `400 Bad Request` | Missing field rejection. |
| B2B Buyer (`buyer`) | Temperature out of range (`<-25°C` or `>30°C`) | `400 Bad Request` | Cold-chain constraint violation. |
| B2B Buyer (`buyer`) | Partial quantity (`ordered != available`) | `400 Bad Request` | Whole-listing invariant violation. |
| B2B Buyer (`buyer`) | Insufficient wallet balance | `400 Bad Request` | Insufficient funds rejection. |
| B2B Buyer (`buyer`) | Non-existent listing | `404 Not Found` | Listing not found. |
| B2B Buyer (`buyer`) | Listing already `status = 'Sold'` | `409 Conflict` | Double-spend concurrency block. |
| Farmer / Other Roles | Any | `403 Forbidden` | Access denied. |
| Unauthenticated | Any | `401 Unauthorized` | Authentication required. |

#### Request Specification
* **Headers**: `Content-Type: application/json`, `Authorization: Bearer <buyer_jwt>`
* **JSON Body Fields**:

| Field Name | Type | Required | Validation Rules |
|---|---|:---:|---|
| `listing_id` | integer | Yes | Primary key of target active listing. |
| `ordered_quantity_kg` | number | Yes | Must exactly equal `listing.quantity_kg` (`FR-ORD-003`). |
| `destination_warehouse` | string | Yes | Delivery location. Minimum 5 characters. |
| `max_temperature_celsius` | number | Yes | Cold-chain threshold. Range: `-25.0` to `+30.0` °C (`D-INC2-10`). |

#### Example Request
```json
{
  "listing_id": 1,
  "ordered_quantity_kg": 5000.0,
  "destination_warehouse": "Metro Central Hub, Industrial Area, Lahore",
  "max_temperature_celsius": 6.0
}
```

#### Response Payloads
##### Success (`201 Created`)
```json
{
  "success": true,
  "message": "Order created successfully. Escrow funds locked.",
  "data": {
    "order_id": 8941,
    "order_number": "ORD-2026-8941",
    "listing_id": 1,
    "ordered_quantity_kg": 5000.0,
    "total_amount_pkr": 225000.00,
    "order_status": "Escrow_Funded",
    "escrow_status": "HELD",
    "destination_warehouse": "Metro Central Hub, Industrial Area, Lahore",
    "max_temperature_celsius": 6.0,
    "remaining_wallet_balance_pkr": 275000.00,
    "created_at": "2026-11-14T10:15:00Z"
  }
}
```

##### Error Catalogue
* **`400 Bad Request` — Missing Required Fields**:
  ```json
  { "success": false, "error": "All checkout fields are required." }
  ```
* **`400 Bad Request` — Temperature Constraint Violation (`D-INC2-10`)**:
  ```json
  { "success": false, "error": "Max temperature must be between -25.0°C and 30.0°C." }
  ```
* **`400 Bad Request` — Partial Quantity Attempted (`FR-ORD-003`)**:
  ```json
  { "success": false, "error": "Partial quantity purchasing is not supported in Increment 2." }
  ```
* **`400 Bad Request` — Insufficient Wallet Balance (`FR-ORD-004`)**:
  ```json
  { "success": false, "error": "Insufficient wallet balance." }
  ```
* **`401 Unauthorized` — Missing / Expired Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Non-Buyer Role Access**:
  ```json
  { "success": false, "error": "Access denied." }
  ```
* **`404 Not Found` — Target Listing Missing or Deleted**:
  ```json
  { "success": false, "error": "Listing not found." }
  ```
* **`409 Conflict` — Race Condition / Double-Selling (`FR-ORD-006`)**:
  ```json
  { "success": false, "error": "Listing has already been sold." }
  ```

---

### 6.2 Endpoint 6: Delivery Confirmation & Escrow Release (`POST /api/orders/<id>/confirm-delivery`)
Buyer quality acceptance and escrow release endpoint, transferring funds to the farmer wallet.

* **HTTP Method & Path**: `POST /api/orders/<id>/confirm-delivery`
* **Purpose**: Confirm delivery of produce and release held escrow funds to the selling farmer.
* **Authentication**: Required (`Authorization: Bearer <buyer_jwt>`). Must be buyer owner of the order.
* **Status Precondition**: Target order must be in status `'Escrow_Funded'`.
* **Traced Requirements**: `FR-SET-001`, `FR-SET-002`, `FR-SET-003`, `FR-SET-004`, `NFR-SEC-002`, `NFR-SEC-003`.
* **Diagram Trace**: Diagram 4 (§6).

#### Role × Outcome Matrix
| Caller Role | Caller Identity vs Order | Order Status | Expected Status | Outcome Description |
|---|---|---|:---:|---|
| B2B Buyer | Order Owner (`buyer_id == o.buyer_id`) | `'Escrow_Funded'` | `200 OK` | Delivery confirmed, farmer wallet credited. |
| B2B Buyer | Order Owner | Non-`'Escrow_Funded'` (e.g. Completed) | `400 Bad Request` | Settlement precondition failure. |
| B2B Buyer | Non-Owner (`buyer_id != o.buyer_id`) | Any | `404 Not Found` | Unified 404 anti-enumeration. |
| Farmer / Other | Any | Any | `403 Forbidden` | Access denied. |
| Unauthenticated | Any | Any | `401 Unauthorized` | Authentication required. |

#### Request Specification
* **Headers**: `Authorization: Bearer <buyer_jwt>`
* **URL Parameter**: `id` (integer, required): Order primary key.
* **Request Body**: `{}` (Empty JSON object or omitted).

#### Response Payloads
##### Success (`200 OK`)
```json
{
  "success": true,
  "message": "Delivery confirmed and escrow funds released to farmer.",
  "data": {
    "order_id": 8941,
    "order_number": "ORD-2026-8941",
    "order_status": "Completed",
    "escrow_status": "RELEASED",
    "delivered_at": "2026-11-14T11:30:00Z",
    "release_tx_ref": "TRIGGER:buyer_confirmation;REF:TX-8941-SETTLE"
  }
}
```

##### Error Catalogue
* **`400 Bad Request` — Precondition State Mismatch (`FR-SET-002`)**:
  ```json
  { "success": false, "error": "Order cannot be confirmed in current status." }
  ```
* **`401 Unauthorized` — Missing / Invalid Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Wrong Role (e.g. Farmer)**:
  ```json
  { "success": false, "error": "Access denied." }
  ```
* **`404 Not Found` — Missing or Non-Owner Order (`Pinned Decision 1`)**:
  ```json
  { "success": false, "error": "Order not found." }
  ```

---

### 6.3 Endpoint 7: Order Cancellation & Inventory Restoration (`POST /api/orders/<id>/cancel`)
Order cancellation endpoint accessible by either the purchasing buyer or the selling farmer.

* **HTTP Method & Path**: `POST /api/orders/<id>/cancel`
* **Purpose**: Cancel an active escrow order, refunding the buyer's wallet and restoring the listing to `'Active'`.
* **Authentication**: Required (`Authorization: Bearer <jwt_token>`). Caller must be a party to the order.
* **Status Precondition**: Target order must be in status `'Escrow_Funded'`.
* **Traced Requirements**: `FR-SET-005`, `FR-SET-006`, `FR-STM-003`, `FR-STM-004`, `NFR-SEC-002`, `NFR-SEC-003`.
* **Diagram Trace**: Diagram 5 (§7).

#### Role × Outcome Matrix
| Caller Role | Caller Identity vs Order | Order Status | Expected Status | Outcome Description |
|---|---|---|:---:|---|
| Buyer | Buyer Party (`buyer_id == o.buyer_id`) | `'Escrow_Funded'` | `200 OK` | Order cancelled, wallet refunded, crop active. |
| Farmer | Farmer Party (`farmer_id == o.farmer_id`) | `'Escrow_Funded'` | `200 OK` | Order cancelled, wallet refunded, crop active. |
| Buyer / Farmer | Associated Party | Not `'Escrow_Funded'` | `400 Bad Request` | Only Escrow_Funded orders can be cancelled. |
| Buyer / Farmer | NOT Party to Order | Any | `404 Not Found` | Unified 404 anti-enumeration. |
| Non-existent ID | Any | Any | `404 Not Found` | Unified 404 anti-enumeration. |
| Inactive Roles | Any | Any | `403 Forbidden` | Access denied. |
| Unauthenticated | Any | Any | `401 Unauthorized` | Authentication required. |

#### Request Specification
* **Headers**: `Authorization: Bearer <jwt_token>`
* **URL Parameter**: `id` (integer, required): Order primary key.
* **Request Body**: `{}` (Empty JSON object or omitted).

#### Response Payloads
##### Success (`200 OK`)
```json
{
  "success": true,
  "message": "Order cancelled successfully. Funds refunded and crop restored to catalog.",
  "data": {
    "order_id": 8941,
    "order_number": "ORD-2026-8941",
    "order_status": "Cancelled",
    "escrow_status": "REFUNDED",
    "refunded_amount_pkr": 225000.00,
    "listing_id": 1,
    "listing_status": "Active"
  }
}
```

##### Error Catalogue
* **`400 Bad Request` — Invalid Order Status (`FR-SET-005`)**:
  ```json
  { "success": false, "error": "Only Escrow_Funded orders can be cancelled." }
  ```
* **`401 Unauthorized` — Missing / Invalid Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Unauthorized Role**:
  ```json
  { "success": false, "error": "Access denied." }
  ```
* **`404 Not Found` — Missing or Non-Party Order (`Pinned Decision 1`)**:
  ```json
  { "success": false, "error": "Order not found." }
  ```

---

### 6.4 Endpoint 8: Order Dispute Flagging (`POST /api/orders/<id>/dispute`)
Dispute notification endpoint, freezing order and escrow holdings permanently at the Increment 2 boundary.

* **HTTP Method & Path**: `POST /api/orders/<id>/dispute`
* **Purpose**: Flag a formal dispute on an active escrow order, freezing funds in escrow.
* **Authentication**: Required (`Authorization: Bearer <jwt_token>`). Caller must be a party to the order.
* **Status Precondition**: Target order must be in status `'Escrow_Funded'`.
* **Traced Requirements**: `FR-STM-005`, `FR-STM-006`, `NFR-SEC-002`, `NFR-SEC-003`.
* **Diagram Trace**: Diagram 6 (§8).

#### Role × Outcome Matrix
| Caller Role | Caller Identity vs Order | Order Status | Expected Status | Outcome Description |
|---|---|---|:---:|---|
| Buyer / Farmer | Associated Party | `'Escrow_Funded'` | `200 OK` | Order and escrow frozen in Disputed state. |
| Buyer / Farmer | Associated Party | Not `'Escrow_Funded'` | `400 Bad Request` | Dispute rejected (must be Escrow_Funded). |
| Buyer / Farmer | NOT Party to Order | Any | `404 Not Found` | Unified 404 anti-enumeration. |
| Inactive Roles | Any | Any | `403 Forbidden` | Access denied. |
| Unauthenticated | Any | Any | `401 Unauthorized` | Authentication required. |

#### Request Specification
* **Headers**: `Content-Type: application/json`, `Authorization: Bearer <jwt_token>`
* **URL Parameter**: `id` (integer, required): Order primary key.
* **JSON Body Fields**:

| Field Name | Type | Required | Validation Rules |
|---|---|:---:|---|
| `reason` | string | No | Optional dispute description (e.g. cold-chain breach), 5–255 chars. |

#### Example Request
```json
{
  "reason": "Cold-chain violation detected. Temperature reached 14.5C during transit."
}
```

#### Response Payloads
##### Success (`200 OK`)
```json
{
  "success": true,
  "message": "Dispute registered. Escrow funds have been frozen.",
  "data": {
    "order_id": 8941,
    "order_number": "ORD-2026-8941",
    "order_status": "Disputed",
    "escrow_status": "DISPUTED",
    "disputed_at": "2026-11-14T11:45:00Z"
  }
}
```

##### Error Catalogue
* **`400 Bad Request` — Invalid Order Status (`FR-STM-005`)**:
  ```json
  { "success": false, "error": "Only Escrow_Funded orders can be disputed." }
  ```
* **`401 Unauthorized` — Missing / Invalid Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Unauthorized Role**:
  ```json
  { "success": false, "error": "Access denied." }
  ```
* **`404 Not Found` — Missing or Non-Party Order (`Pinned Decision 1`)**:
  ```json
  { "success": false, "error": "Order not found." }
  ```

---

### 6.5 Endpoint 9: Buyer Order History (`GET /api/orders/buyer`)
Paginated retrieval of procurement orders placed by the authenticated buyer.

* **HTTP Method & Path**: `GET /api/orders/buyer`
* **Purpose**: Retrieve order procurement history for the calling buyer.
* **Authentication**: Required (`Authorization: Bearer <buyer_jwt>`). Role must be `buyer`.
* **Traced Requirements**: `FR-ORD-008`, `NFR-SEC-001`, `FR-MKT-004`.
* **Diagram Trace**: Diagram 11 (§12).

#### Role × Outcome Matrix
| Caller Role | Expected Status | Outcome Description |
|---|:---:|---|
| B2B Buyer (`buyer`) | `200 OK` | Retrieves own paginated order history. |
| Farmer (`farmer`) | `403 Forbidden` | Access denied. |
| Other Inactive Roles | `403 Forbidden` | Access denied. |
| Unauthenticated | `401 Unauthorized` | Authentication required. |

#### Request Specification
* **Headers**: `Authorization: Bearer <buyer_jwt>`
* **Query Parameters**:

| Parameter | Type | Required | Default | Validation / Filtering Rules |
|---|---|:---:|:---:|---|
| `status` | string | No | `null` | Enum: `['Escrow_Funded', 'Completed', 'Cancelled', 'Disputed']`. |
| `page` | integer | No | `1` | Min value `1`. |
| `limit` | integer | No | `20` | Min value `1`, max value `100`. |

#### Response Payloads
##### Success (`200 OK`) — Flat List Envelope
```json
{
  "success": true,
  "data": [
    {
      "order_id": 8941,
      "order_number": "ORD-2026-8941",
      "listing_id": 1,
      "crop_name": "Wheat",
      "batch_id": "BATCH-2026-WHT-0001",
      "farmer_id": 7,
      "farm_name": "Green Acres",
      "ordered_quantity_kg": 5000.0,
      "agreed_price_per_kg": 45.00,
      "total_amount_pkr": 225000.00,
      "destination_warehouse": "Metro Central Hub, Industrial Area, Lahore",
      "max_temperature_celsius": 6.0,
      "order_status": "Escrow_Funded",
      "escrow_status": "HELD",
      "created_at": "2026-11-14T10:15:00Z"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1
}
```

##### Error Catalogue
* **`400 Bad Request` — Invalid Filter Parameters**:
  ```json
  { "success": false, "error": "Invalid filter parameters." }
  ```
* **`401 Unauthorized` — Missing / Expired Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Non-Buyer Role Access**:
  ```json
  { "success": false, "error": "Access denied." }
  ```

---

### 6.6 Endpoint 10: Farmer Incoming Orders (`GET /api/orders/farmer`)
Paginated retrieval of inbound sales orders for crops cultivated by the authenticated farmer.

* **HTTP Method & Path**: `GET /api/orders/farmer`
* **Purpose**: Retrieve inbound purchase orders placed by buyers for the calling farmer's crops.
* **Authentication**: Required (`Authorization: Bearer <farmer_jwt>`). Role must be `farmer`.
* **Traced Requirements**: `FR-ORD-009`, `NFR-SEC-001`, `FR-MKT-004`.
* **Diagram Trace**: Diagram 11 (§12).

#### Role × Outcome Matrix
| Caller Role | Expected Status | Outcome Description |
|---|:---:|---|
| Farmer (`farmer`) | `200 OK` | Retrieves own paginated inbound sales orders. |
| B2B Buyer (`buyer`) | `403 Forbidden` | Access denied. |
| Other Inactive Roles | `403 Forbidden` | Access denied. |
| Unauthenticated | `401 Unauthorized` | Authentication required. |

#### Request Specification
* **Headers**: `Authorization: Bearer <farmer_jwt>`
* **Query Parameters**:

| Parameter | Type | Required | Default | Validation / Filtering Rules |
|---|---|:---:|:---:|---|
| `status` | string | No | `null` | Enum: `['Escrow_Funded', 'Completed', 'Cancelled', 'Disputed']`. |
| `page` | integer | No | `1` | Min value `1`. |
| `limit` | integer | No | `20` | Min value `1`, max value `100`. |

#### Response Payloads
##### Success (`200 OK`) — Flat List Envelope
```json
{
  "success": true,
  "data": [
    {
      "order_id": 8941,
      "order_number": "ORD-2026-8941",
      "listing_id": 1,
      "crop_name": "Wheat",
      "batch_id": "BATCH-2026-WHT-0001",
      "buyer_id": 4,
      "buyer_company_name": "Metro Wholesale Foods",
      "ordered_quantity_kg": 5000.0,
      "agreed_price_per_kg": 45.00,
      "total_amount_pkr": 225000.00,
      "destination_warehouse": "Metro Central Hub, Industrial Area, Lahore",
      "max_temperature_celsius": 6.0,
      "order_status": "Escrow_Funded",
      "escrow_status": "HELD",
      "created_at": "2026-11-14T10:15:00Z"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1
}
```

##### Error Catalogue
* **`400 Bad Request` — Invalid Filter Parameters**:
  ```json
  { "success": false, "error": "Invalid filter parameters." }
  ```
* **`401 Unauthorized` — Missing / Expired Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Non-Farmer Role Access**:
  ```json
  { "success": false, "error": "Access denied." }
  ```

---

## 7. Module 4: Environmental Telemetry & Predictive Intelligence Endpoints

### 7.1 Endpoint 11: Environmental Telemetry Fetch (`GET /api/telemetry/weather` & `GET /api/telemetry/soil`)
Queries meteorological or edaphic conditions for given coordinates, backed by 6-hour SQLite cache and deterministic fallback fixtures.

* **HTTP Method & Path**:
  - `GET /api/telemetry/weather`
  - `GET /api/telemetry/soil`
* **Purpose**: Fetch normalized environmental telemetry for crop monitoring and yield forecasting.
* **Authentication**: Required (`Authorization: Bearer <jwt_token>`). Accessible by `farmer` and `buyer`.
* **Traced Requirements**: `FR-TEL-001` through `FR-TEL-005`, `FR-CCH-001` through `FR-CCH-005`, `NFR-REL-001`, `NFR-PERF-003`, `Pinned Decision 4`.
* **Diagram Trace**: Diagram 8 (§10).

#### Role × Outcome Matrix
| Caller Role | Coordinate Validity | External API / Cache State | Expected Status | Outcome Description |
|---|---|---|:---:|---|
| Farmer or Buyer | Valid `lat`, `lon` | Unexpired cache entry | `200 OK` | Cache hit (`source: "cache"`), latency < 100ms. |
| Farmer or Buyer | Valid `lat`, `lon` | Cache miss, external API up | `200 OK` | Live API query (`source: "live_api"`), cached for 6h. |
| Farmer or Buyer | Valid `lat`, `lon` | API timeout / 429 / offline | `200 OK` | Offline fixture (`source: "offline_fixture"`), cached for 6h. |
| Farmer or Buyer | Missing / invalid coordinates | Any | `400 Bad Request` | Coordinate validation rejection. |
| Inactive Roles | Any | Any | `403 Forbidden` | Access denied. |
| Unauthenticated | Any | Any | `401 Unauthorized` | Authentication required. |

#### Request Specification
* **Headers**: `Authorization: Bearer <jwt_token>`
* **Query Parameters**:

| Parameter | Type | Required | Range & Validation Rules |
|---|---|:---:|---|
| `lat` | number | Yes | Float between `-90.0` and `90.0`. |
| `lon` | number | Yes | Float between `-180.0` and `180.0`. |

#### Response Payloads
##### Shared Envelope & Discriminator Structure
Both endpoints share a common top-level envelope:
```json
{
  "success": true,
  "source": "live_api | cache | offline_fixture",
  "data": { ... }
}
```
* `source` is strictly one of:
  - `"live_api"`: Freshly retrieved from OpenWeatherMap or SoilGrids API.
  - `"cache"`: Retrieved from `telemetry_cache` table within 6-hour TTL.
  - `"offline_fixture"`: Deterministic local fallback loaded from `backend/tests/fixtures/`.

##### Success (`200 OK`) — Weather Endpoint (`GET /api/telemetry/weather`)
```json
{
  "success": true,
  "source": "cache",
  "data": {
    "temperature_c": 28.5,
    "relative_humidity_pct": 55.0,
    "cumulative_precipitation_14d_mm": 12.4,
    "solar_radiation_index": 0.85,
    "description": "Clear sky",
    "timestamp": "2026-11-14T10:00:00Z"
  }
}
```

##### Success (`200 OK`) — Soil Endpoint (`GET /api/telemetry/soil`)
```json
{
  "success": true,
  "source": "live_api",
  "data": {
    "topsoil_moisture_vol_pct": 24.5,
    "soil_organic_carbon_g_per_kg": 11.2,
    "soil_ph": 7.4,
    "soil_texture_class": "Clay Loam",
    "timestamp": "2026-11-14T10:00:00Z"
  }
}
```

##### Error Catalogue
* **`400 Bad Request` — Invalid Coordinates**:
  ```json
  { "success": false, "error": "Valid latitude (-90 to 90) and longitude (-180 to 180) are required." }
  ```
* **`401 Unauthorized` — Missing / Expired Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Unauthorized Role**:
  ```json
  { "success": false, "error": "Access denied." }
  ```

---

### 7.2 Endpoint 12: Predictive Yield Forecast (`POST /api/yield/predict`)
Computes deterministic agronomic yield estimates for a farmer's crop listing using telemetry context.

* **HTTP Method & Path**: `POST /api/yield/predict`
* **Purpose**: Calculate mathematical yield projection, harvest date, and irrigation advice for an active listing.
* **Authentication**: Required (`Authorization: Bearer <farmer_jwt>`). Must be listing owner.
* **Traced Requirements**: `FR-YLD-001` through `FR-YLD-007`, `NFR-SEC-002`, `NFR-PERF-004`, `Plan §13 Decision 5`.
* **Diagram Trace**: Diagram 9 (§11).

#### Role × Outcome Matrix
| Caller Role | Caller Identity vs Listing | Expected Status | Outcome Description |
|---|---|:---:|---|
| Farmer (`farmer`) | Listing Owner (`farmer_id == l.farmer_id`) | `200 OK` | Forecast computed, saved to DB, returned. |
| Farmer (`farmer`) | Non-Owner (`farmer_id != l.farmer_id`) | `404 Not Found` | Unified 404 anti-enumeration. |
| Farmer (`farmer`) | Non-existent listing ID | `404 Not Found` | Unified 404 anti-enumeration. |
| Farmer (`farmer`) | Missing `listing_id` field | `400 Bad Request` | Missing field rejection. |
| Buyer / Other Roles | Any | `403 Forbidden` | Access denied. |
| Unauthenticated | Any | `401 Unauthorized` | Authentication required. |

#### Request Specification
* **Headers**: `Content-Type: application/json`, `Authorization: Bearer <farmer_jwt>`
* **JSON Body Fields**:

| Field Name | Type | Required | Validation Rules |
|---|---|:---:|---|
| `listing_id` | integer | Yes | Primary key of target crop listing owned by authenticated farmer. |

#### Example Request
```json
{
  "listing_id": 101
}
```

#### Response Payloads
##### Success (`200 OK`)
```json
{
  "success": true,
  "message": "Yield forecast generated successfully.",
  "data": {
    "forecast_id": 55,
    "listing_id": 101,
    "crop_name": "Wheat",
    "acreage": 12.5,
    "predicted_harvest_date": "2027-01-20",
    "predicted_yield_kg": 18367.65,
    "confidence_score_pct": 88,
    "environmental_index": 0.82,
    "irrigation_advice": "Optimal soil moisture. Maintain standard irrigation schedule.",
    "generated_at": "2026-11-14T11:00:00Z"
  }
}
```
*(Agronomic arithmetic benchmark: $12.5 \times 1,400 \times 1.02 \times 1.05 \times 0.98 = 18,367.65\text{ kg}$, matching Diagram 9 v1.1).*

##### Error Catalogue
* **`400 Bad Request` — Missing Field**:
  ```json
  { "success": false, "error": "Listing ID is required." }
  ```
* **`401 Unauthorized` — Missing / Expired Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Non-Farmer Role**:
  ```json
  { "success": false, "error": "Access denied." }
  ```
* **`404 Not Found` — Listing Missing or Non-Owner (`Pinned Decision 1`)**:
  ```json
  { "success": false, "error": "Listing not found." }
  ```

---

## 8. Module 5: Active Crop Commercial Pricing Delta

### 8.1 Endpoint 13: Commercial Pricing & Batch Publication Delta (`PUT /api/crops/<id>`)
Extends Increment 1's crop update endpoint to accept commercial asking prices and assign unique batch IDs.

* **HTTP Method & Path**: `PUT /api/crops/<id>`
* **Purpose**: Update an active crop listing with commercial pricing, triggering automated `batch_id` generation.
* **Authentication**: Required (`Authorization: Bearer <farmer_jwt>`). Must be listing owner.
* **Traced Requirements**: `FR-PRC-001`, `FR-PRC-002`, `FR-PRC-003`, `FR-PRC-004`, `FR-PRC-005`, `D-INC2-08`.
* **Diagram Trace**: Diagram 10 (§12).

#### Role × Outcome Matrix
| Caller Role | Caller Identity vs Listing | Payload State | Expected Status | Outcome Description |
|---|---|---|:---:|---|
| Farmer (`farmer`) | Listing Owner | Valid `asking_price_per_kg > 0` | `200 OK` | Price set, `batch_id` generated, listing published. |
| Farmer (`farmer`) | Listing Owner | `asking_price_per_kg <= 0` | `400 Bad Request` | Price validation rejection. |
| Farmer (`farmer`) | Non-Owner | Any | `404 Not Found` | Unified 404 anti-enumeration. |
| Buyer / Other Roles | Any | Any | `403 Forbidden` | Access denied. |
| Unauthenticated | Any | Any | `401 Unauthorized` | Authentication required. |

#### Request Specification Delta
* **Headers**: `Content-Type: application/json`, `Authorization: Bearer <farmer_jwt>`
* **URL Parameter**: `id` (integer, required): Listing primary key.
* **Delta JSON Body Fields** (Added to Increment 1 fields):

| Field Name | Type | Required | Validation Rules |
|---|---|:---:|---|
| `asking_price_per_kg` | number | No (Optional) | If provided, must be numeric and strictly `> 0.00` PKR. |

#### Batch ID Auto-Generation Rule (`FR-PRC-003`, `D-INC2-08`)
When `asking_price_per_kg` is assigned to a listing whose `batch_id` is currently null, the backend automatically generates:
$$\text{batch\_id} = \text{BATCH-}\{\text{YEAR}\}\text{-}\{\text{CROP\_CODE3}\}\text{-}\{\text{LISTING\_ID:04d}\}$$
* **Taxonomy Code Mapping**:
  Wheat $\rightarrow$ `WHT`, Rice $\rightarrow$ `RIC`, Tomato $\rightarrow$ `TOM`, Potato $\rightarrow$ `POT`, Cotton $\rightarrow$ `COT`, Maize $\rightarrow$ `MAI`, Sugarcane $\rightarrow$ `SUG`, Other $\rightarrow$ `OTH`.
* **Example**: For listing ID 101 (Wheat) updated in 2026: `BATCH-2026-WHT-0101`.

#### Example Request
```json
{
  "crop_name": "Wheat",
  "planting_date": "2026-09-01",
  "estimated_harvest_date": "2027-01-15",
  "acreage": 12.5,
  "gps_latitude": 30.0444,
  "gps_longitude": 72.3441,
  "quantity_kg": 5000.0,
  "asking_price_per_kg": 45.00
}
```

#### Response Payloads
##### Success (`200 OK`) — Extended Serialization
```json
{
  "success": true,
  "message": "Crop listing updated successfully.",
  "data": {
    "listing_id": 101,
    "farmer_id": 7,
    "crop_name": "Wheat",
    "batch_id": "BATCH-2026-WHT-0101",
    "acreage": 12.5,
    "quantity_kg": 5000.0,
    "asking_price_per_kg": 45.00,
    "planting_date": "2026-09-01",
    "estimated_harvest_date": "2027-01-15",
    "gps_latitude": 30.0444,
    "gps_longitude": 72.3441,
    "status": "Active",
    "is_deleted": false,
    "created_at": "2026-10-12T03:15:00Z",
    "updated_at": "2026-11-14T11:15:00Z"
  }
}
```

##### Error Catalogue
* **`400 Bad Request` — Invalid Commercial Price (`FR-PRC-002`)**:
  ```json
  { "success": false, "error": "Asking price per kg must be greater than 0." }
  ```
* **`401 Unauthorized` — Missing / Expired Token**:
  ```json
  { "success": false, "error": "Authentication required. Please log in." }
  ```
* **`403 Forbidden` — Non-Farmer Role**:
  ```json
  { "success": false, "error": "Access denied." }
  ```
* **`404 Not Found` — Listing Missing or Non-Owner (`Pinned Decision 1`, `TC-13`)**:
  ```json
  { "success": false, "error": "Listing not found." }
  ```

---

## 9. Master Role × Outcome Authorization Matrix

The following matrix documents the authoritative HTTP status response for every system role across all 13 Increment 2 delta operations.

| # | Endpoint / Operation | Public / Anon | Farmer | B2B Buyer | Transporter *(Inc 3)* | Agronomist *(Inc 4)* | Compliance *(Inc 4)* |
|:---:|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | `POST /api/auth/register` (Buyer) | `201` / `400` / `409` | `201` / `400` / `409` | `201` / `400` / `409` | `201` / `400` / `409` | `201` / `400` / `409` | `201` / `400` / `409` |
| **2** | `POST /api/auth/login` | `200` / `401` | `200` (farmer JWT) | `200` (buyer JWT) | `200` | `200` | `200` |
| **3** | `GET /api/marketplace/listings` | `401` | `200 OK` | `200 OK` | `403` | `403` | `403` |
| **4** | `GET /api/marketplace/listings/<id>` | `401` | `200` / `404` | `200` / `404` | `403` | `403` | `403` |
| **5** | `POST /api/orders` | `401` | `403` | `201` / `400` / `409` | `403` | `403` | `403` |
| **6** | `POST /api/orders/<id>/confirm-delivery` | `401` | `403` | `200` / `400` / `404` | `403` | `403` | `403` |
| **7** | `POST /api/orders/<id>/cancel` | `401` | `200` / `400` / `404` | `200` / `400` / `404` | `403` | `403` | `403` |
| **8** | `POST /api/orders/<id>/dispute` | `401` | `200` / `400` / `404` | `200` / `400` / `404` | `403` | `403` | `403` |
| **9** | `GET /api/orders/buyer` | `401` | `403` | `200 OK` | `403` | `403` | `403` |
| **10** | `GET /api/orders/farmer` | `401` | `200 OK` | `403` | `403` | `403` | `403` |
| **11** | `GET /api/telemetry/weather` & `soil` | `401` | `200 OK` | `200 OK` | `403` | `403` | `403` |
| **12** | `POST /api/yield/predict` | `401` | `200` / `404` | `403` | `403` | `403` | `403` |
| **13** | `PUT /api/crops/<id>` (Pricing) | `401` | `200` / `400` / `404` | `403` | `403` | `403` | `403` |

---

## 10. Traceability Matrix (Contracts to SRS v1.2 & Sequence Diagrams v1.1)

| # | Endpoint / Route | HTTP Method | Governing SRS v1.2 Requirements | Sequence Diagram Reference | Phase 3 Test Suite Binding |
|:---:|---|:---:|---|---|---|
| **1** | `/api/auth/register` (Buyer) | `POST` | `FR-BYR-001`, `FR-BYR-002`, `FR-BYR-003`, `FR-BYR-004`, `FR-WLT-003`, `NFR-SEC-003` | Diagram 1 (§3) | `test_marketplace_api.py::TC-BYR-01..02` |
| **2** | `/api/auth/login` (Claims) | `POST` | `FR-BYR-005`, `NFR-SEC-001`, `Pinned Decision 3` | Diagram 1 / Inc 1 Base | `test_auth.py` extension |
| **3** | `/api/marketplace/listings` | `GET` | `FR-MKT-001`, `FR-MKT-002`, `FR-MKT-003`, `FR-MKT-004`, `FR-MKT-005`, `NFR-PERF-001` | Diagram 2 (§4) | `test_marketplace_api.py::TC-MKT-01..03` |
| **4** | `/api/marketplace/listings/<id>` | `GET` | `FR-MKT-006`, `FR-MKT-007`, `NFR-SEC-002` | Diagram 2 (§4) | `test_marketplace_api.py::TC-MKT-04..05` |
| **5** | `/api/orders` | `POST` | `FR-ORD-001`..`007`, `NFR-SEC-001`, `NFR-SEC-003`, `D-INC2-10` | Diagram 3 (§5) | `test_escrow_orders.py::TC-ORD-01..05` |
| **6** | `/api/orders/<id>/confirm-delivery` | `POST` | `FR-SET-001`, `FR-SET-002`, `FR-SET-003`, `FR-SET-004`, `NFR-SEC-002` | Diagram 4 (§6) | `test_escrow_orders.py::TC-SET-01..03` |
| **7** | `/api/orders/<id>/cancel` | `POST` | `FR-SET-005`, `FR-SET-006`, `FR-STM-003`, `FR-STM-004`, `NFR-SEC-002` | Diagram 5 (§7) | `test_escrow_orders.py::TC-SET-04..05` |
| **8** | `/api/orders/<id>/dispute` | `POST` | `FR-STM-005`, `FR-STM-006`, `NFR-SEC-002`, `NFR-SEC-003` | Diagram 6 (§8) | `test_escrow_orders.py::TC-STM-01..02` |
| **9** | `/api/orders/buyer` | `GET` | `FR-ORD-008`, `NFR-SEC-001`, `FR-MKT-004` | Diagram 11 (§12) | `test_escrow_orders.py::TC-ORD-06` |
| **10** | `/api/orders/farmer` | `GET` | `FR-ORD-009`, `NFR-SEC-001`, `FR-MKT-004` | Diagram 11 (§12) | `test_escrow_orders.py::TC-ORD-07` |
| **11** | `/api/telemetry/weather` & `soil` | `GET` | `FR-TEL-001`..`005`, `FR-CCH-001`..`005`, `NFR-REL-001` | Diagram 8 (§10) | `test_yield_telemetry.py::TC-TEL-01..02` |
| **12** | `/api/yield/predict` | `POST` | `FR-YLD-001`..`007`, `NFR-SEC-002`, `NFR-PERF-004` | Diagram 9 (§11) | `test_yield_telemetry.py::TC-YLD-01..02` |
| **13** | `/api/crops/<id>` (Pricing) | `PUT` | `FR-PRC-001`, `FR-PRC-002`, `FR-PRC-003`, `FR-PRC-004`, `FR-PRC-005` | Diagram 10 (§12) | `test_crops_api.py::TC-PRC-01` |

---

## 11. Verification & Validation Sign-Off Block

```
================================================================================
AGRI-GRID SOFTWARE ENGINEERING V&V ACCEPTANCE GATE
Stage: Increment 2 Requirements Engineering Track (Deliverable 3 of 3)
Document ID: AG-API-INC2-003 v1.0
================================================================================

[X] Software Architect & API Designer:
    Name:      Iqra Fayaz
    Role:      System Architect & Increment 1 API Author
    Signature: I. Fayaz
    Date:      2026-11-14
    Status:    CONTRACT COMPLETE & COMPLIANT WITH PINNED DECISIONS 1–5

[X] Lead Requirements Engineer:
    Name:      Manahil Sohail
    Role:      Requirements Engineering Track Lead
    Signature: M. Sohail
    Date:      2026-11-14
    Status:    TRACEABILITY CERTIFIED AGAINST SRS v1.2 & SSD v1.1

[ ] Scrum Master & Lead Data Architect:
    Name:      Ameer Muawiyah
    Role:      Project Manager, Scrum Master & Lead Data Architect
    Signature: __________________________________
    Date:      __________________________________
    Status:    PENDING FACT-CHECK & APPROVAL
================================================================================
```

*End of Increment 2 API Contracts Delta — Document ID: AG-API-INC2-003 v1.0*
