# API & JSON Payload Contracts
## Increment 1: Foundation & The Farmer Dashboard

| Field | Value |
|---|---|
| **Project Name** | Agri-Grid: Smart Agriculture & Food Security Ecosystem |
| **Document ID** | `AG-API-INC1-003` |
| **Version** | 1.0 |
| **Prepared By** | Requirements & Architecture Agent (Lead Software Architect) |
| **Reviewed By** | Ameer Muawiyah (Project Manager & Lead Data Architect) |
| **Date** | 2026-10-12 |
| **Source Documents** | `AG-SRS-INC1-001 v1.1` & `AG-SSD-INC1-002 v1.1` |
| **Location** | `./Architecture_Blueprints/Increment_1/3_Farmer_API_Contracts.md` |

---

## Table of Contents
1. [Overview & Architectural Standards](#1-overview--architectural-standards)
2. [Global Authentication & Header Standards](#2-global-authentication--header-standards)
3. [Module 1: Authentication & RBAC Gateway Endpoints](#3-module-1-authentication--rbac-gateway-endpoints)
   - [3.1 User Registration (`POST /api/auth/register`)](#31-user-registration-post-apiauthregister)
   - [3.2 User Login & Token Issuance (`POST /api/auth/login`)](#32-user-login--token-issuance-post-apiauthlogin)
   - [3.3 User Logout (`POST /api/auth/logout`)](#33-user-logout-post-apiauthlogout)
4. [Module 2: Active Crop Management (CRUD) Endpoints](#4-module-2-active-crop-management-crud-endpoints)
   - [4.1 Create Crop Listing (`POST /api/crops`)](#41-create-crop-listing-post-apicrops)
   - [4.2 Read All Crop Listings - Paginated (`GET /api/crops`)](#42-read-all-crop-listings---paginated-get-apicrops)
   - [4.3 Read Single Crop Listing (`GET /api/crops/{listing_id}`)](#43-read-single-crop-listing-get-apicropslisting_id)
   - [4.4 Update Crop Listing (`PUT /api/crops/{listing_id}`)](#44-update-crop-listing-put-apicropslisting_id)
   - [4.5 Withdraw / Soft-Delete Crop Listing (`DELETE /api/crops/{listing_id}`)](#45-withdraw--soft-delete-crop-listing-delete-apicropslisting_id)
5. [Standard Error Envelope Specification](#5-standard-error-envelope-specification)
6. [Contract Binding & Verification Checklist](#6-contract-binding--verification-checklist)

---

## 1. Overview & Architectural Standards

This document serves as the **formal interface specification and communication contract** between the **UI/UX Agent (Frontend)** and the **Database & Backend Agent (Backend/DBA)** for Increment 1.

### Architectural Principles
* **Stateless RESTful Design:** Communication occurs strictly over HTTPS/HTTP via JSON payloads.
* **Zero-Trust Multi-Tenancy:** The tenant identity (`farmer_id`) is strictly extracted on the backend from the signed JWT claim. The frontend **must never** send `farmer_id` or `user_id` inside the request body for crop CRUD operations.
* **Enumeration Prevention (CTO Gap 3 Fix):** For resource-specific endpoints (`/api/crops/{listing_id}`), attempting to access or mutate a record that belongs to another tenant returns **HTTP 404 Not Found**, intentionally identical to non-existent IDs.
* **Soft-Delete Provenance Integrity (CTO Blocker 3 Fix):** The `DELETE` endpoint is non-destructive at the physical SQL level; it performs a soft-delete (`is_deleted = TRUE`, `status = 'Withdrawn'`).

---

## 2. Global Authentication & Header Standards

### Request Headers
For all endpoints under `/api/crops*` and authenticated auth routes:
```http
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

### JWT Token Format (SessionStorage Key: `agrigrid_token`)
* **Algorithm:** `HS256`
* **Payload Claims Structure:**
```json
{
  "user_id": 42,
  "farmer_id": 7,
  "role": "farmer",
  "exp": 1728700800
}
```
*(Note: `farmer_id` is `null` for non-farmer accounts).*

---

## 3. Module 1: Authentication & RBAC Gateway Endpoints

### 3.1 User Registration (`POST /api/auth/register`)
Handles atomic user onboarding and automatic profile creation for farmers.

* **Method:** `POST`
* **URL Route:** `/api/auth/register`
* **Authentication Required:** No (Public endpoint)
* **RBAC Rule:** Allows role selection from: `["farmer", "buyer", "transporter", "agronomist", "compliance_officer"]`. When `role == "farmer"`, `farm_name` is strictly required. Backend performs an atomic SQL transaction across `Users` and `Farmers` tables.

#### Request JSON Payload
```json
{
  "username": "string (required, unique, 3-50 chars)",
  "password": "string (required, min 8 chars, 1 uppercase, 1 lowercase, 1 number)",
  "role": "string (required, enum: farmer|buyer|transporter|agronomist|compliance_officer)",
  "farm_name": "string (required ONLY if role == 'farmer', 1-100 chars)"
}
```

#### Example Request
```json
{
  "username": "tahir_greenacres",
  "password": "FarmSecurePass1!",
  "role": "farmer",
  "farm_name": "Green Acres Organic Field"
}
```

#### Response Payloads

##### Success (`201 Created`)
```json
{
  "success": true,
  "message": "Registration successful. Please log in.",
  "user": {
    "user_id": 42,
    "username": "tahir_greenacres",
    "role": "farmer",
    "farmer_id": 7
  }
}
```

##### Failure Scenarios

* **`400 Bad Request` — Missing Required Fields / Password Complexity:**
```json
{
  "success": false,
  "error": "All fields are required: username, password, role."
}
```
* **`400 Bad Request` — Missing `farm_name` for Farmer Role:**
```json
{
  "success": false,
  "error": "Farm name is required when registering as a farmer."
}
```
* **`400 Bad Request` — Password Complexity Violation:**
```json
{
  "success": false,
  "error": "Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number."
}
```
* **`409 Conflict` — Duplicate Username:**
```json
{
  "success": false,
  "error": "Username already exists."
}
```
* **`500 Internal Server Error` — DB Transaction Rollback:**
```json
{
  "success": false,
  "error": "Registration failed. Please try again."
}
```

---

### 3.2 User Login & Token Issuance (`POST /api/auth/login`)
Authenticates credentials, performs optimized single `LEFT JOIN` on `Users` and `Farmers`, and returns a signed JWT.

* **Method:** `POST`
* **URL Route:** `/api/auth/login`
* **Authentication Required:** No (Public endpoint)

#### Request JSON Payload
```json
{
  "username": "string (required)",
  "password": "string (required)"
}
```

#### Example Request
```json
{
  "username": "tahir_greenacres",
  "password": "FarmSecurePass1!"
}
```

#### Response Payloads

##### Success (`200 OK`)
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "role": "farmer",
  "user": {
    "user_id": 42,
    "farmer_id": 7,
    "username": "tahir_greenacres"
  }
}
```
*Frontend Contract Rule:* Frontend stores `token` in `sessionStorage` under key `agrigrid_token` and inspects `role` to redirect (e.g., `role === 'farmer'` ➔ `/dashboard/farmer`).

##### Failure Scenarios

* **`400 Bad Request` — Empty / Missing Payload Fields:**
```json
{
  "success": false,
  "error": "Username and password are required."
}
```
* **`401 Unauthorized` — Invalid Credentials (Generic, Anti-Enumeration):**
```json
{
  "success": false,
  "error": "Invalid credentials."
}
```

---

### 3.3 User Logout (`POST /api/auth/logout`)
Client session termination endpoint.

* **Method:** `POST`
* **URL Route:** `/api/auth/logout`
* **Authentication Required:** Yes (`Authorization: Bearer <token>`)

#### Request JSON Payload
```json
{}
```

#### Response Payloads

##### Success (`200 OK`)
```json
{
  "success": true,
  "message": "Logged out successfully."
}
```
*Frontend Contract Rule:* The frontend removes `agrigrid_token` from `sessionStorage` and immediately redirects to `/login`.

---

## 4. Module 2: Active Crop Management (CRUD) Endpoints

### 4.1 Create Crop Listing (`POST /api/crops`)
Allows an authenticated farmer to register an active cultivating crop.

* **Method:** `POST`
* **URL Route:** `/api/crops`
* **Authentication Required:** Yes (`Authorization: Bearer <jwt_token>`)
* **RBAC Rule:** Role must be `farmer`.

#### Request JSON Payload
```json
{
  "crop_name": "string (required, enum: ['Wheat', 'Rice', 'Tomato', 'Potato', 'Cotton', 'Maize', 'Sugarcane', 'Other'])",
  "planting_date": "string (required, format: 'YYYY-MM-DD', <= CURRENT_DATE, >= CURRENT_DATE - 365 days)",
  "estimated_harvest_date": "string (required, format: 'YYYY-MM-DD', > planting_date)",
  "acreage": "number/float (required, > 0)",
  "gps_latitude": "number/float (required, -90.0 to 90.0)",
  "gps_longitude": "number/float (required, -180.0 to 180.0)",
  "quantity_kg": "number/float (required, > 0)"
}
```

#### Example Request
```json
{
  "crop_name": "Wheat",
  "planting_date": "2026-09-01",
  "estimated_harvest_date": "2027-01-15",
  "acreage": 12.5,
  "gps_latitude": 30.3753,
  "gps_longitude": 69.3451,
  "quantity_kg": 5000.00
}
```

#### Response Payloads

##### Success (`201 Created`)
```json
{
  "success": true,
  "message": "Crop listing created successfully.",
  "data": {
    "listing_id": 101,
    "farmer_id": 7,
    "crop_name": "Wheat",
    "planting_date": "2026-09-01",
    "estimated_harvest_date": "2027-01-15",
    "acreage": 12.5,
    "gps_latitude": 30.3753,
    "gps_longitude": 69.3451,
    "quantity_kg": 5000.00,
    "status": "Active",
    "is_deleted": false,
    "created_at": "2026-10-12T03:15:00Z"
  }
}
```

##### Failure Scenarios

* **`400 Bad Request` — Crop Taxonomy Violation:**
```json
{
  "success": false,
  "error": "Invalid crop name. Must be one of: Wheat, Rice, Tomato, Potato, Cotton, Maize, Sugarcane, Other."
}
```
* **`400 Bad Request` — Future Planting Date:**
```json
{
  "success": false,
  "error": "Planting date cannot be in the future."
}
```
* **`400 Bad Request` — Planting Date Older Than 365 Days:**
```json
{
  "success": false,
  "error": "Planting date cannot be older than 365 days for an active listing."
}
```
* **`400 Bad Request` — Invalid Harvest Date:**
```json
{
  "success": false,
  "error": "Estimated harvest date must be after planting date."
}
```
* **`400 Bad Request` — Numeric Range / Out-of-Bounds:**
```json
{
  "success": false,
  "error": "Acreage must be a positive number."
}
```
* **`401 Unauthorized` — Missing / Expired JWT:**
```json
{
  "success": false,
  "error": "Authentication required. Please log in."
}
```
* **`403 Forbidden` — Non-Farmer Role Access:**
```json
{
  "success": false,
  "error": "Access denied. You do not have permission to access this resource."
}
```
* **`500 Internal Server Error` — Database Persistence Failure:**
```json
{
  "success": false,
  "error": "An internal error occurred. Please try again later."
}
```

---

### 4.2 Read All Crop Listings - Paginated (`GET /api/crops`)
Returns a paginated list of active crop listings belonging exclusively to the authenticated farmer.

* **Method:** `GET`
* **URL Route:** `/api/crops`
* **Query Parameters:**
  * `page` (optional, integer, default: `1`, minimum: `1`)
  * `limit` (optional, integer, default: `20`, minimum: `1`, maximum: `100`)
* **Example URL:** `/api/crops?page=1&limit=20`
* **Authentication Required:** Yes (`Authorization: Bearer <jwt_token>`)
* **Backend Filter:** `WHERE farmer_id = <jwt_farmer_id> AND is_deleted = FALSE`

#### Request Payload
*None (HTTP GET request)*

#### Response Payloads

##### Success (`200 OK`) — Populated State
```json
{
  "success": true,
  "data": [
    {
      "listing_id": 101,
      "crop_name": "Wheat",
      "planting_date": "2026-09-01",
      "estimated_harvest_date": "2027-01-15",
      "acreage": 12.5,
      "quantity_kg": 5000.00,
      "status": "Active",
      "created_at": "2026-10-12T03:15:00Z"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 1
}
```

##### Success (`200 OK`) — Empty State (No crops registered)
```json
{
  "success": true,
  "data": [],
  "page": 1,
  "limit": 20,
  "total": 0
}
```

##### Failure Scenarios
* **`401 Unauthorized`:**
```json
{
  "success": false,
  "error": "Authentication required. Please log in."
}
```
* **`403 Forbidden`:**
```json
{
  "success": false,
  "error": "Access denied. You do not have permission to access this resource."
}
```

---

### 4.3 Read Single Crop Listing (`GET /api/crops/{listing_id}`)
Retrieves full details for a single crop, including GPS coordinates.

* **Method:** `GET`
* **URL Route:** `/api/crops/{listing_id}`
* **Path Parameter:** `listing_id` (integer, required)
* **Authentication Required:** Yes (`Authorization: Bearer <jwt_token>`)

#### Request Payload
*None (HTTP GET request)*

#### Response Payloads

##### Success (`200 OK`)
```json
{
  "success": true,
  "data": {
    "listing_id": 101,
    "farmer_id": 7,
    "crop_name": "Wheat",
    "planting_date": "2026-09-01",
    "estimated_harvest_date": "2027-01-15",
    "acreage": 12.5,
    "gps_latitude": 30.3753,
    "gps_longitude": 69.3451,
    "quantity_kg": 5000.00,
    "status": "Active",
    "is_deleted": false,
    "created_at": "2026-10-12T03:15:00Z",
    "updated_at": "2026-10-12T03:15:00Z"
  }
}
```

##### Failure Scenarios

* **`404 Not Found` — Listing Does Not Exist OR Belongs to Another Farmer:**
```json
{
  "success": false,
  "error": "Listing not found."
}
```
*(Note: Unified 404 response to eliminate tenant resource enumeration).*

---

### 4.4 Update Crop Listing (`PUT /api/crops/{listing_id}`)
Updates mutable fields of an active crop listing.

* **Method:** `PUT`
* **URL Route:** `/api/crops/{listing_id}`
* **Path Parameter:** `listing_id` (integer, required)
* **Authentication Required:** Yes (`Authorization: Bearer <jwt_token>`)

#### Request JSON Payload
```json
{
  "crop_name": "string (required, enum taxonomy)",
  "planting_date": "string (required, format: 'YYYY-MM-DD')",
  "estimated_harvest_date": "string (required, format: 'YYYY-MM-DD')",
  "acreage": "number/float (required, > 0)",
  "gps_latitude": "number/float (required, -90.0 to 90.0)",
  "gps_longitude": "number/float (required, -180.0 to 180.0)",
  "quantity_kg": "number/float (required, > 0)"
}
```

#### Example Request
```json
{
  "crop_name": "Wheat",
  "planting_date": "2026-09-01",
  "estimated_harvest_date": "2027-02-01",
  "acreage": 12.5,
  "gps_latitude": 30.3753,
  "gps_longitude": 69.3451,
  "quantity_kg": 6500.00
}
```

#### Response Payloads

##### Success (`200 OK`)
```json
{
  "success": true,
  "message": "Crop listing updated successfully.",
  "data": {
    "listing_id": 101,
    "crop_name": "Wheat",
    "planting_date": "2026-09-01",
    "estimated_harvest_date": "2027-02-01",
    "acreage": 12.5,
    "gps_latitude": 30.3753,
    "gps_longitude": 69.3451,
    "quantity_kg": 6500.00,
    "status": "Active",
    "updated_at": "2026-10-12T03:30:00Z"
  }
}
```

##### Failure Scenarios

* **`400 Bad Request` — Validation Error:**
```json
{
  "success": false,
  "error": "Estimated harvest date must be after planting date."
}
```
* **`404 Not Found` — Listing Not Found / Unauthorized Cross-Tenant Update:**
```json
{
  "success": false,
  "error": "Listing not found."
}
```

---

### 4.5 Withdraw / Soft-Delete Crop Listing (`DELETE /api/crops/{listing_id}`)
Safely archives a crop listing by setting `is_deleted = TRUE` and `status = 'Withdrawn'`.

* **Method:** `DELETE`
* **URL Route:** `/api/crops/{listing_id}`
* **Path Parameter:** `listing_id` (integer, required)
* **Authentication Required:** Yes (`Authorization: Bearer <jwt_token>`)
* **Database Action:** `UPDATE Listings SET is_deleted = TRUE, status = 'Withdrawn' WHERE listing_id = ? AND farmer_id = ?`

#### Request Payload
*None (HTTP DELETE request)*

#### Response Payloads

##### Success (`200 OK`)
```json
{
  "success": true,
  "message": "Listing withdrawn successfully."
}
```

##### Failure Scenarios

* **`404 Not Found` — Listing Not Found / Belongs to Different Farmer:**
```json
{
  "success": false,
  "error": "Listing not found."
}
```
* **`401 Unauthorized`:**
```json
{
  "success": false,
  "error": "Authentication required. Please log in."
}
```
* **`403 Forbidden`:**
```json
{
  "success": false,
  "error": "Access denied. You do not have permission to access this resource."
}
```

---

## 5. Standard Error Envelope Specification

To ensure seamless frontend error parsing and user feedback:
1. **All Error Responses** must return HTTP status codes in the `4xx` or `5xx` range.
2. **Error Payload Format:**
```json
{
  "success": false,
  "error": "Detailed human-readable message describing the rejection reason."
}
```
3. The frontend error handler must check `response.data.error` to render toast alerts or form validation borders (`NFR-USE-002`, `NFR-USE-003`).

---

## 6. Contract Binding & Verification Checklist

| Actor | Action / Responsibility |
|---|---|
| **UI/UX Agent** | Enforces dropdown selection matching the taxonomy list on `crop_name`. |
| **UI/UX Agent** | Never includes `farmer_id` or `user_id` inside CRUD POST/PUT request bodies. |
| **UI/UX Agent** | Binds token from `sessionStorage.getItem('agrigrid_token')` to `Authorization: Bearer <token>`. |
| **UI/UX Agent** | Interprets `DELETE` button as a **Withdraw** action with confirmation modal. |
| **Backend Agent** | Uses `LEFT JOIN` on `/api/auth/login` to embed `farmer_id` into the JWT. |
| **Backend Agent** | Enforces atomic transaction (`BEGIN` / `COMMIT` / `ROLLBACK`) on `/api/auth/register`. |
| **Backend Agent** | Returns unified `404` for missing IDs and cross-tenant queries on `/api/crops/{id}`. |
| **Backend Agent** | Prohibits physical `DELETE` queries on the `Listings` table; uses `UPDATE` soft-delete. |

---
*End of Document — AG-API-INC1-003 v1.0*
