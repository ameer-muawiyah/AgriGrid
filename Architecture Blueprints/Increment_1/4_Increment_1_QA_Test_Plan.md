# Increment 1 QA Test Plan
## V-Model Validation Package: Farmer Dashboard and JWT Authentication

| Field | Value |
|---|---|
| Project | Agri-Grid: Smart Agriculture & Food Security Ecosystem |
| Increment | Increment 1 - Foundation and Farmer Dashboard |
| QA Role | Lead QA Engineer and V-Model Test Architect |
| Prepared For | Ameer Muawiyah, Project Manager |
| Methodology | V-Model verification and validation |
| Source SRS | `1_Farmer_Dashboard_SRS.md` |
| Source Sequence Diagrams | `2_Farmer_Sequence_Diagrams.md` |
| Source API Contracts | `3_Farmer_API_Contracts.md` |

## 1. V-Model Test Scope

This test plan validates the Increment 1 requirements before automation begins. It maps each SRS requirement to at least one integration, system, security, data-integrity, usability, performance, or governance test case.

Primary risk areas:

- JWT authentication and token contract enforcement.
- RBAC route isolation between Farmer and non-Farmer roles.
- Zero-Trust data isolation between Farmer tenants.
- Atomic `Users` plus `Farmers` registration.
- Crop CRUD correctness, validation, and soft-delete behavior.
- SQL schema integrity for `Users`, `Farmers`, and `Listings`.

## 2. Traceability Matrix

| Requirement ID | Requirement Area | Test Case ID(s) | Verification Focus |
|---|---|---|---|
| FR-LGN-001 | Public login page | TC-SYS-001 | `/login` is publicly reachable. |
| FR-LGN-002 | Login inputs | TC-SYS-001 | Login page contains username/email and password fields. |
| FR-LGN-003 | Login submit button | TC-SYS-001 | Login button is present and usable. |
| FR-LGN-004 | Login JSON submission | TC-INT-003 | Frontend/backend contract uses `POST /api/auth/login`. |
| FR-LGN-005 | Login JSON shape | TC-INT-003, TC-INT-004 | Only `username` and `password` are accepted for login. |
| FR-LGN-006 | Users table lookup | TC-INT-003, TC-INT-004 | Backend authenticates against `Users.username`. |
| FR-LGN-007 | Password hash verification | TC-INT-003, TC-INT-004, TC-SEC-001 | Secure hash comparison, no plaintext password use. |
| FR-LGN-008 | Role read after auth | TC-INT-003, TC-INT-006 | Auth response and routing use persisted `Users.role`. |
| FR-LGN-009 | JWT claims | TC-INT-003, TC-SEC-002 | JWT contains `user_id`, `farmer_id`, `role`, `exp`. |
| FR-LGN-010 | Login response body | TC-INT-003 | Response includes signed JWT and role. |
| FR-LGN-011 | `sessionStorage` token storage | TC-SYS-001, TC-INT-003 | Token stored as `agrigrid_token`, not HttpOnly cookie. |
| FR-LGN-012 | Role-based redirect | TC-SYS-001, TC-INT-006 | Farmer routes to `/dashboard/farmer`; other roles to placeholders. |
| FR-LGN-013 | Placeholder dashboards | TC-INT-006 | Non-Farmer dashboards authenticate and show construction page. |
| FR-LGN-014 | Unknown username rejection | TC-INT-004 | Unknown user returns generic 401. |
| FR-LGN-015 | Wrong password rejection | TC-INT-004 | Wrong password returns generic 401. |
| FR-LGN-016 | Anti-enumeration login error | TC-INT-004 | Unknown user and wrong password produce same message. |
| FR-LGN-017 | Missing login fields | TC-INT-004 | Missing username/password returns 400. |
| FR-LGN-018 | Registration endpoint and payload | TC-INT-001, TC-INT-002 | `POST /api/auth/register` accepts required fields. |
| FR-LGN-018A | Atomic Farmer registration | TC-INT-001, TC-REL-001 | `Users` and `Farmers` rows commit or rollback together. |
| FR-LGN-019 | Registration role whitelist | TC-INT-002, TC-SCHEMA-001 | Only five authenticated roles accepted. |
| FR-LGN-020 | Duplicate username rejection | TC-INT-002, TC-SCHEMA-001 | Duplicate username returns 409 and DB UNIQUE holds. |
| FR-LGN-021 | Password hashing on registration | TC-INT-001, TC-SEC-001 | Stored password is a hash, not plaintext. |
| FR-LGN-022 | Bearer JWT on authenticated APIs | TC-INT-005, TC-INT-008, TC-INT-010 | Protected requests require `Authorization: Bearer`. |
| FR-LGN-023 | Missing/expired/invalid JWT | TC-INT-005 | Bad token states return 401. |
| FR-LGN-024 | Logout endpoint | TC-INT-007 | Logout succeeds and frontend clears client token. |
| FR-CRP-001 | Add New Crop control | TC-SYS-002 | Farmer dashboard exposes add control. |
| FR-CRP-002 | Crop creation form fields | TC-SYS-002, TC-INT-008 | Form includes all required crop fields. |
| FR-CRP-003 | Create crop POST | TC-INT-008 | Frontend sends `POST /api/crops`. |
| FR-CRP-004 | Create crop JSON structure | TC-INT-008, TC-INT-009 | Payload fields match API contract. |
| FR-CRP-004A | Crop taxonomy whitelist | TC-INT-009, TC-SCHEMA-001 | Free-form crop names rejected. |
| FR-CRP-005 | `farmer_id` from JWT only | TC-INT-008, TC-SEC-003 | Body-supplied tenant identity ignored/rejected. |
| FR-CRP-006 | SQL INSERT into Listings | TC-INT-008, TC-SCHEMA-001 | Listing persisted with authenticated farmer ownership. |
| FR-CRP-006A | Temporal validation | TC-INT-009 | Future, stale, and invalid harvest dates rejected. |
| FR-CRP-007 | Create response | TC-INT-008 | Successful create returns 201 and new listing object. |
| FR-CRP-008 | Create success notification | TC-SYS-002 | UI shows creation success message. |
| FR-CRP-009 | Auto `Active` status | TC-INT-008 | Backend sets status, farmer cannot override it. |
| FR-CRP-010 | Farmer listings view | TC-SYS-002, TC-INT-010 | Dashboard displays authenticated farmer listings. |
| FR-CRP-011 | Paginated list endpoint | TC-INT-010, TC-PERF-001 | `GET /api/crops?page=1&limit=20` returns data, page, limit, total. |
| FR-CRP-012 | Listing display columns | TC-SYS-002 | Minimum listing fields are visible. |
| FR-CRP-013 | Empty state | TC-SYS-002, TC-INT-010 | Empty farmer account shows defined empty state. |
| FR-CRP-014 | Single listing detail view | TC-SYS-002, TC-INT-011 | Farmer can view full listing details including GPS. |
| FR-CRP-014A | Single listing endpoint and 404 isolation | TC-INT-011, TC-SEC-003 | Own listing returns 200; nonexistent/cross-tenant returns identical 404. |
| FR-CRP-015 | Edit control | TC-SYS-002, TC-INT-012 | Listing row exposes edit action. |
| FR-CRP-016 | Edit pre-fill | TC-SYS-002, TC-INT-012 | Edit form preloads current listing values. |
| FR-CRP-017 | Editable crop fields | TC-INT-012 | Farmer can modify allowed fields only. |
| FR-CRP-018 | Update PUT | TC-INT-012 | Frontend sends `PUT /api/crops/{listing_id}`. |
| FR-CRP-019 | Update ownership check | TC-INT-012, TC-SEC-003 | Cross-tenant update returns 404 before SQL update. |
| FR-CRP-020 | Update response | TC-INT-012 | Successful update returns 200 and updated object. |
| FR-CRP-021 | Update success notification | TC-SYS-002 | UI shows update success message. |
| FR-CRP-022 | Withdraw control | TC-SYS-002, TC-INT-013 | UI label uses Withdraw, not destructive Delete language. |
| FR-CRP-023 | Withdraw confirmation | TC-SYS-002, TC-INT-013 | Confirmation dialog appears before request. |
| FR-CRP-024 | Delete endpoint for withdraw | TC-INT-013 | Frontend sends `DELETE /api/crops/{listing_id}` after confirmation. |
| FR-CRP-025 | Soft delete and ownership | TC-INT-013, TC-SEC-003, TC-SCHEMA-001 | Backend updates `is_deleted` and `status`; no physical delete. |
| FR-CRP-026 | Withdraw response | TC-INT-013 | Success returns 200 and message. |
| FR-CRP-027 | Remove withdrawn row in UI | TC-SYS-002, TC-INT-013 | Withdrawn listing disappears without full page reload. |
| NFR-SEC-001 | Password hash storage | TC-SEC-001, TC-INT-001 | Passwords are one-way hashes only. |
| NFR-SEC-002 | Protected API JWT requirement | TC-INT-005 | All non-public APIs require valid JWT. |
| NFR-SEC-003 | JWT expiration | TC-INT-005, TC-SEC-002 | Expired JWT returns 401. |
| NFR-SEC-004 | Zero-Trust data isolation | TC-SEC-003, TC-INT-010, TC-INT-011, TC-INT-012, TC-INT-013 | Every user-specific query is scoped by authenticated farmer. |
| NFR-SEC-005 | SQL injection prevention | TC-SEC-004 | Parameterized/ORM queries reject injection strings. |
| NFR-SEC-006 | XSS prevention | TC-SEC-005 | Rendered user input is escaped/sanitized. |
| NFR-SEC-007 | CORS restriction | TC-SEC-006 | Unauthorized origins are denied. |
| NFR-SEC-008 | Password complexity | TC-INT-002 | Weak passwords rejected. |
| NFR-PERF-001 | Login p95 latency | TC-PERF-001 | Login p95 < 1s at 50 concurrent requests. |
| NFR-PERF-002 | Listing p95 latency | TC-PERF-001 | `GET /api/crops` p95 < 1.5s at 50 concurrent requests. |
| NFR-PERF-003 | CRUD p95 latency | TC-PERF-001 | Crop create/update/delete p95 < 500ms at 50 concurrent requests. |
| NFR-USE-001 | Responsive UI | TC-SYS-003 | Login and dashboard render from 320px to 1920px. |
| NFR-USE-002 | Inline validation errors | TC-SYS-002, TC-INT-009 | Field-level validation errors appear beside fields. |
| NFR-USE-003 | Distinct notifications | TC-SYS-002 | Success/error notifications are visually distinct and auto-dismiss. |
| NFR-USE-004 | Loading feedback | TC-SYS-002 | API operations show loading feedback and prevent double submit. |
| NFR-REL-001 | ACID writes | TC-REL-001, TC-INT-001, TC-INT-008, TC-INT-012, TC-INT-013 | Write operations are atomic and durable. |
| NFR-REL-002 | NOT NULL constraints | TC-SCHEMA-001 | Required fields enforce NOT NULL. |
| NFR-REL-003 | Foreign key integrity | TC-SCHEMA-001, TC-REL-001 | `Listings.farmer_id` references `Farmers.farmer_id`. |
| NFR-REL-004 | Unique usernames | TC-SCHEMA-001, TC-INT-002 | `Users.username` uniqueness enforced by API and DB. |
| NFR-MNT-001 | Extensible role enumeration | TC-SCHEMA-001 | Role constraint supports authenticated roles. |
| NFR-MNT-002 | RESTful API conventions | TC-INT-008, TC-INT-010, TC-INT-011, TC-INT-012, TC-INT-013 | CRUD uses POST, GET, PUT, DELETE consistently. |
| NFR-MNT-003 | Git branch protection | TC-GOV-001 | Repository settings prevent direct pushes to `main`. |

## 3. Integration and System Test Case Specifications

### TC-INT-001

- **Test ID & Description:** TC-INT-001 - Validate successful Farmer registration with atomic `Users` plus `Farmers` creation.
- **Preconditions:** Database is reachable. No existing `Users.username = "tahir_greenacres"`. Registration endpoint is public.
- **Execution Steps:**
  1. Send `POST /api/auth/register` with username, compliant password, `role = "farmer"`, and `farm_name`.
  2. Query `Users` for the created username.
  3. Query `Farmers` for a row linked to the new `Users.user_id`.
  4. Inspect `Users.password_hash`.
- **Expected JSON/HTTP Result:** HTTP 201 with `success: true`, message `Registration successful. Please log in.`, and user object containing `user_id`, `username`, `role: "farmer"`, and `farmer_id`. Database contains exactly one `Users` row and one linked `Farmers` row. Stored password is a hash and not the submitted plaintext.

### TC-INT-002

- **Test ID & Description:** TC-INT-002 - Validate registration negative paths: missing fields, missing `farm_name`, weak password, invalid role, duplicate username.
- **Preconditions:** At least one user already exists with username `existing_farmer`. Registration endpoint is public.
- **Execution Steps:**
  1. Submit registration payload missing `username`, `password`, or `role`.
  2. Submit `role = "farmer"` without `farm_name`.
  3. Submit weak password such as `abc123`.
  4. Submit invalid role such as `admin`.
  5. Submit duplicate username `existing_farmer`.
  6. Check database row counts after each failed request.
- **Expected JSON/HTTP Result:** Missing fields return HTTP 400 and `All fields are required: username, password, role.` Missing farmer farm name returns HTTP 400 and `Farm name is required when registering as a farmer.` Weak password returns HTTP 400 and password complexity error. Invalid role returns HTTP 400 and approved role list. Duplicate username returns HTTP 409 and `Username already exists.` No failed request creates partial `Users` or `Farmers` rows.

### TC-INT-003

- **Test ID & Description:** TC-INT-003 - Validate successful login, JWT issuance, role response, and Farmer redirect contract.
- **Preconditions:** Active Farmer user exists with a valid hashed password and linked `Farmers` profile.
- **Execution Steps:**
  1. Send `POST /api/auth/login` with valid `username` and `password`.
  2. Decode the returned JWT without altering it.
  3. Verify frontend stores token under `sessionStorage["agrigrid_token"]`.
  4. Verify role-based redirect target for `role = "farmer"`.
- **Expected JSON/HTTP Result:** HTTP 200 with `success: true`, `token`, `role: "farmer"`, and user object containing `user_id`, `farmer_id`, and `username`. JWT algorithm is HS256 and claims include `user_id`, `farmer_id`, `role`, and `exp`. Frontend redirects to `/dashboard/farmer`.

### TC-INT-004

- **Test ID & Description:** TC-INT-004 - Validate login negative paths and anti-enumeration behavior.
- **Preconditions:** Active user exists. Login endpoint is public.
- **Execution Steps:**
  1. Submit login payload with missing `username`.
  2. Submit login payload with missing `password`.
  3. Submit unknown username with any password.
  4. Submit known username with wrong password.
  5. Compare response status and response body for steps 3 and 4.
- **Expected JSON/HTTP Result:** Missing username/password returns HTTP 400 and `Username and password are required.` Unknown username and wrong password both return HTTP 401 with identical body `{"success": false, "error": "Invalid credentials."}`. Response must not reveal whether the username exists.

### TC-INT-005

- **Test ID & Description:** TC-INT-005 - Validate JWT middleware for missing, expired, malformed, and tampered tokens.
- **Preconditions:** `/api/crops` and `/dashboard/farmer` are protected. Test harness can generate expired and tampered JWTs.
- **Execution Steps:**
  1. Call `GET /api/crops` without `Authorization`.
  2. Call `GET /api/crops` with `Authorization: Bearer <expired_token>`.
  3. Call `GET /api/crops` with malformed token text.
  4. Call `GET /api/crops` with a valid-looking JWT whose signature was modified.
- **Expected JSON/HTTP Result:** Missing or expired JWT returns HTTP 401 with `Authentication required. Please log in.` Malformed or tampered JWT returns HTTP 401 with `Invalid session. Please log in again.` No protected handler or database query processes the request after middleware rejection.

### TC-INT-006

- **Test ID & Description:** TC-INT-006 - Validate RBAC route isolation and non-Farmer dashboard placeholders.
- **Preconditions:** Valid users exist for `farmer`, `buyer`, `transporter`, `agronomist`, and `compliance_officer`.
- **Execution Steps:**
  1. Log in as each role and capture JWT plus `role`.
  2. Access each role-specific dashboard route using the matching role token.
  3. Attempt to access `/dashboard/farmer` using each non-Farmer token.
  4. Attempt to access non-Farmer dashboard routes using a Farmer token.
- **Expected JSON/HTTP Result:** Farmer token gets functional `/dashboard/farmer`. Non-Farmer matching dashboard routes return authenticated placeholder page containing `Dashboard under construction - available in a future increment.` Cross-role route access returns HTTP 403 and `Access denied. You do not have permission to access this resource.`

### TC-INT-007

- **Test ID & Description:** TC-INT-007 - Validate logout endpoint and client token purge.
- **Preconditions:** User is logged in and `agrigrid_token` exists in `sessionStorage`.
- **Execution Steps:**
  1. Send `POST /api/auth/logout` with `Authorization: Bearer <valid_token>`.
  2. Verify frontend removes `agrigrid_token` from `sessionStorage`.
  3. Attempt to call `GET /api/crops` after token removal.
- **Expected JSON/HTTP Result:** Logout returns HTTP 200 with `{"success": true, "message": "Logged out successfully."}`. Token is removed client-side and subsequent protected access returns HTTP 401.

### TC-INT-008

- **Test ID & Description:** TC-INT-008 - Validate successful crop creation using JWT-owned `farmer_id`.
- **Preconditions:** Farmer A is logged in with valid JWT containing `farmer_id = 7`. Database contains Farmer A profile.
- **Execution Steps:**
  1. Send `POST /api/crops` with valid crop JSON and Bearer token.
  2. Include an attempted malicious `farmer_id` in the body in a separate run.
  3. Query `Listings` for the created row.
  4. Verify `status` and `is_deleted`.
- **Expected JSON/HTTP Result:** HTTP 201 with `success: true`, message `Crop listing created successfully.`, and listing object. Persisted `farmer_id` must equal JWT claim, not any body value. `status` is `Active`; `is_deleted` is `false`; response includes generated `listing_id`.

### TC-INT-009

- **Test ID & Description:** TC-INT-009 - Validate crop creation negative input and temporal validation cascade.
- **Preconditions:** Farmer is logged in with valid JWT.
- **Execution Steps:**
  1. Submit crop payload missing each required field one at a time.
  2. Submit invalid crop name such as `Dragonfruit-X`.
  3. Submit `acreage <= 0` and `quantity_kg <= 0`.
  4. Submit latitude outside `[-90, 90]` and longitude outside `[-180, 180]`.
  5. Submit invalid date format.
  6. Submit future `planting_date`.
  7. Submit `planting_date` older than 365 days.
  8. Submit `estimated_harvest_date <= planting_date`.
- **Expected JSON/HTTP Result:** Each invalid request returns HTTP 400 with the exact error specified by the API/SRS, such as `Missing required field: {field_name}.`, taxonomy error, numeric range error, GPS range error, date format error, future/stale planting date error, or harvest-date ordering error. No listing is inserted.

### TC-INT-010

- **Test ID & Description:** TC-INT-010 - Validate paginated Farmer listing read and active-only tenant filtering.
- **Preconditions:** Farmer A has 25 active listings and 1 withdrawn listing. Farmer B has 3 active listings. Farmer A is logged in.
- **Execution Steps:**
  1. Call `GET /api/crops?page=1&limit=20` using Farmer A token.
  2. Call `GET /api/crops?page=2&limit=20` using Farmer A token.
  3. Verify no Farmer B listings appear.
  4. Verify withdrawn Farmer A listing does not appear.
  5. Repeat with a Farmer account that has zero active listings.
- **Expected JSON/HTTP Result:** HTTP 200 with `success: true`, `data`, `page`, `limit`, and `total`. Farmer A page 1 returns up to 20 own active rows and `total: 25`; page 2 returns remaining own active rows. Zero-listing account returns `data: []`, correct page metadata, and `total: 0`.

### TC-INT-011

- **Test ID & Description:** TC-INT-011 - Validate single listing detail and unified 404 for nonexistent or cross-tenant IDs.
- **Preconditions:** Farmer A owns `listing_id = 101`. Farmer B owns `listing_id = 200`. Farmer A is logged in.
- **Execution Steps:**
  1. Call `GET /api/crops/101` with Farmer A token.
  2. Call `GET /api/crops/200` with Farmer A token.
  3. Call `GET /api/crops/999999` with Farmer A token.
  4. Compare responses from steps 2 and 3.
- **Expected JSON/HTTP Result:** Own listing returns HTTP 200 with full listing object including GPS coordinates. Cross-tenant and nonexistent listing requests both return HTTP 404 with identical body `{"success": false, "error": "Listing not found."}`.

### TC-INT-012

- **Test ID & Description:** TC-INT-012 - Validate crop update happy path, validation failures, and cross-tenant 404.
- **Preconditions:** Farmer A owns `listing_id = 101`. Farmer B owns `listing_id = 200`. Farmer A is logged in.
- **Execution Steps:**
  1. Fetch `GET /api/crops/101` to pre-fill edit form.
  2. Send valid `PUT /api/crops/101` with updated `quantity_kg` and `estimated_harvest_date`.
  3. Query database to verify update.
  4. Send invalid update payload using same invalid cases from TC-INT-009.
  5. Send valid `PUT /api/crops/200` using Farmer A token.
- **Expected JSON/HTTP Result:** Successful update returns HTTP 200 with `success: true`, message `Crop listing updated successfully.`, updated listing object, and refreshed `updated_at`. Invalid update returns HTTP 400 with specific validation error. Cross-tenant update returns HTTP 404 and `Listing not found.` No cross-tenant row is modified.

### TC-INT-013

- **Test ID & Description:** TC-INT-013 - Validate withdraw soft-delete, ownership check, and no physical delete.
- **Preconditions:** Farmer A owns active `listing_id = 101`. Farmer B owns active `listing_id = 200`. Farmer A is logged in.
- **Execution Steps:**
  1. Trigger Withdraw on `listing_id = 101`.
  2. Confirm the dialog.
  3. Send `DELETE /api/crops/101` with Farmer A token.
  4. Query `Listings` row `101`.
  5. Call `GET /api/crops` for Farmer A.
  6. Attempt `DELETE /api/crops/200` using Farmer A token.
- **Expected JSON/HTTP Result:** Successful withdraw returns HTTP 200 with `{"success": true, "message": "Listing withdrawn successfully."}`. Database row remains physically present with `is_deleted = TRUE` and `status = "Withdrawn"`. Row no longer appears in active dashboard list. Cross-tenant withdraw returns HTTP 404 and does not modify Farmer B row.

### TC-INT-014

- **Test ID & Description:** TC-INT-014 - Validate non-Farmer crop CRUD rejection.
- **Preconditions:** Valid non-Farmer JWTs exist for Buyer, Transporter, Agronomist, and Compliance Officer.
- **Execution Steps:**
  1. For each non-Farmer token, call `GET /api/crops`.
  2. For each non-Farmer token, call `POST /api/crops` with otherwise valid crop JSON.
  3. For each non-Farmer token, call `GET`, `PUT`, and `DELETE /api/crops/{listing_id}`.
  4. Verify backend handler and database are not reached for rejected write operations.
- **Expected JSON/HTTP Result:** Every crop CRUD request from non-Farmer roles returns HTTP 403 with `{"success": false, "error": "Access denied. You do not have permission to access this resource."}`. No listings are read, inserted, updated, or withdrawn.

### TC-SCHEMA-001

- **Test ID & Description:** TC-SCHEMA-001 - Validate Increment 1 database schema constraints for `Users`, `Farmers`, and `Listings`.
- **Preconditions:** Test database has migrations applied. Direct DB inspection is available.
- **Execution Steps:**
  1. Inspect `Users` columns, primary key, unique username, role constraint, `password_hash NOT NULL`, and `is_active` default.
  2. Inspect `Farmers` columns, unique `user_id`, FK to `Users.user_id`, and `farm_name NOT NULL`.
  3. Inspect `Listings` columns, FK to `Farmers.farmer_id`, required crop fields, crop/status checks, `is_deleted` default, and numeric checks.
  4. Attempt direct invalid inserts in a transaction and roll them back.
- **Expected JSON/HTTP Result:** Schema enforces NOT NULL, UNIQUE, CHECK, and FK constraints. Invalid direct inserts fail at DB level. No API JSON is expected for direct DB checks.

### TC-REL-001

- **Test ID & Description:** TC-REL-001 - Validate transaction rollback and ACID behavior on registration and crop writes.
- **Preconditions:** Test harness can simulate DB insert failure or constraint failure inside a transaction.
- **Execution Steps:**
  1. Force `Farmers` insert failure after successful `Users` insert during Farmer registration.
  2. Force crop `Listings` insert/update failure during create/update.
  3. Inspect database after each failure.
- **Expected JSON/HTTP Result:** Registration failure returns HTTP 500 with `Registration failed. Please try again.` Crop write failure returns HTTP 500 with `An internal error occurred. Please try again later.` Database shows no orphaned `Users` row, no partial `Farmers` row, and no partially written `Listings` update.

### TC-SEC-001

- **Test ID & Description:** TC-SEC-001 - Validate password storage security.
- **Preconditions:** One or more users registered through API.
- **Execution Steps:**
  1. Register a new user with a known password.
  2. Inspect `Users.password_hash`.
  3. Verify the value follows bcrypt, Argon2, or PBKDF2 format.
  4. Verify login succeeds using hash verification, not plaintext comparison.
- **Expected JSON/HTTP Result:** Registration returns HTTP 201. Stored password is not plaintext and uses an approved one-way hash. Login with correct password returns HTTP 200; wrong password returns HTTP 401.

### TC-SEC-002

- **Test ID & Description:** TC-SEC-002 - Validate JWT signing, claims, and expiration configuration.
- **Preconditions:** Server secret and `JWT_EXPIRY_MINUTES` are configured in test environment.
- **Execution Steps:**
  1. Log in successfully.
  2. Decode JWT header and payload.
  3. Verify HS256 signature with server secret.
  4. Verify `exp` aligns with configured expiration.
  5. Use token after forced expiration.
- **Expected JSON/HTTP Result:** JWT has HS256 header and required claims. Valid token authorizes protected access. Expired token returns HTTP 401 with authentication-required message.

### TC-SEC-003

- **Test ID & Description:** TC-SEC-003 - Validate Zero-Trust tenant isolation across create, read, update, and withdraw.
- **Preconditions:** Farmer A and Farmer B each own listings. Farmer A token is available.
- **Execution Steps:**
  1. Attempt to create a listing while sending Farmer B `farmer_id` in request body.
  2. Attempt to list crops with query/body values suggesting Farmer B ownership.
  3. Attempt to read, update, and withdraw Farmer B listing ID.
  4. Inspect database for Farmer B records.
- **Expected JSON/HTTP Result:** Create binds to Farmer A JWT identity only. List returns Farmer A active rows only. Read/update/withdraw against Farmer B IDs return unified HTTP 404 with `Listing not found.` Farmer B records remain unchanged.

### TC-SEC-004

- **Test ID & Description:** TC-SEC-004 - Validate SQL injection resistance.
- **Preconditions:** API and database are running with test data.
- **Execution Steps:**
  1. Submit injection strings in username, password, crop_name, and other text/date fields.
  2. Submit path parameter payloads such as `/api/crops/1 OR 1=1`.
  3. Inspect logs and database state.
- **Expected JSON/HTTP Result:** Requests are rejected with appropriate 400/401/404 responses or treated as literal values. No unauthorized data is returned. Database schema and row counts remain intact.

### TC-SEC-005

- **Test ID & Description:** TC-SEC-005 - Validate XSS sanitization for rendered user input.
- **Preconditions:** Test harness can render the Farmer Dashboard in browser automation.
- **Execution Steps:**
  1. Attempt to register or create allowed text fields containing script-like payloads where applicable.
  2. Render dashboard and detail views.
  3. Observe whether any script executes.
- **Expected JSON/HTTP Result:** Script payloads are escaped, sanitized, or rejected. No JavaScript executes from user-controlled data. UI remains stable.

### TC-SEC-006

- **Test ID & Description:** TC-SEC-006 - Validate CORS restrictions.
- **Preconditions:** Authorized frontend origin and unauthorized test origin are known.
- **Execution Steps:**
  1. Send preflight and API requests from authorized origin.
  2. Send equivalent requests from unauthorized origin.
  3. Inspect CORS headers.
- **Expected JSON/HTTP Result:** Authorized origin receives allowed CORS headers. Unauthorized origin is denied or receives no permissive CORS headers. Protected data is not exposed cross-origin.

### TC-SYS-001

- **Test ID & Description:** TC-SYS-001 - Validate login UI, token storage, and Farmer dashboard redirect end to end.
- **Preconditions:** Browser automation is available. Farmer account exists.
- **Execution Steps:**
  1. Navigate to `/login`.
  2. Verify username/email input, password input, and Login button.
  3. Submit valid Farmer credentials.
  4. Inspect browser `sessionStorage`.
  5. Verify final route and dashboard load.
- **Expected JSON/HTTP Result:** Login UI renders publicly. Successful login stores JWT at `agrigrid_token` and redirects to `/dashboard/farmer`. Initial dashboard API call uses `Authorization: Bearer <token>`.

### TC-SYS-002

- **Test ID & Description:** TC-SYS-002 - Validate Farmer Dashboard UI workflows for create, read, update, withdraw, notifications, and loading states.
- **Preconditions:** Farmer is logged in. Browser automation is available.
- **Execution Steps:**
  1. Verify Add New Crop control and form fields.
  2. Submit valid crop and observe loading state plus success notification.
  3. Verify listing table/card displays required columns.
  4. Open listing detail and verify GPS values.
  5. Edit listing, save, and observe success notification.
  6. Trigger validation errors and verify inline field feedback.
  7. Click Withdraw, cancel once, then confirm once.
  8. Verify row removal without full page reload.
- **Expected JSON/HTTP Result:** UI matches SRS labels and behavior. Notifications are visually distinct and auto-dismiss. Loading indicators prevent double submissions. Empty-state message appears for farmers with no active crops.

### TC-SYS-003

- **Test ID & Description:** TC-SYS-003 - Validate responsive rendering from 320px to 1920px.
- **Preconditions:** Browser automation can resize viewport.
- **Execution Steps:**
  1. Render `/login` at 320, 375, 768, 1024, 1440, and 1920 px widths.
  2. Render `/dashboard/farmer` at the same widths.
  3. Inspect layout, readable labels, tappable controls, and absence of overlap.
- **Expected JSON/HTTP Result:** Pages render correctly at all required widths. Inputs, buttons, table/card views, dialogs, and notifications remain usable with no clipping or overlap.

### TC-PERF-001

- **Test ID & Description:** TC-PERF-001 - Validate Increment 1 API p95 performance at 50 concurrent requests.
- **Preconditions:** Test environment contains representative seed data. Load tool can generate 50 concurrent requests with valid JWTs.
- **Execution Steps:**
  1. Run 50-concurrent load against `POST /api/auth/login`.
  2. Run 50-concurrent load against `GET /api/crops?page=1&limit=20`.
  3. Run 50-concurrent load against `POST /api/crops`, `PUT /api/crops/{id}`, and `DELETE /api/crops/{id}` using isolated test records.
  4. Capture p95 latency and error rate.
- **Expected JSON/HTTP Result:** Login p95 is < 1s. Paginated listing p95 is < 1.5s. Crop create/update/delete p95 is < 500ms. Functional correctness remains intact under load.

### TC-GOV-001

- **Test ID & Description:** TC-GOV-001 - Validate repository governance and branch protection.
- **Preconditions:** GitHub repository settings are accessible to the PM/QA reviewer.
- **Execution Steps:**
  1. Inspect repository branch protection rules.
  2. Verify direct pushes to `main` are blocked.
  3. Verify changes require pull request workflow.
- **Expected JSON/HTTP Result:** No HTTP API contract result required. Repository governance evidence confirms direct `main` pushes are prevented.

## 4. Entry and Exit Criteria

### Entry Criteria

- SRS, sequence diagrams, and API contracts are approved for Increment 1.
- Backend routes and frontend pages are deployed in a testable environment.
- Test database has deterministic seed users for all five authenticated roles.
- JWT secret and expiry configuration are known to QA.

### Exit Criteria

- All SHALL requirements pass mapped tests.
- All Zero-Trust and RBAC negative tests pass with exact status codes and error bodies.
- No cross-tenant data exposure is observed.
- No physical delete occurs on `Listings`.
- All critical defects are resolved or formally accepted by the Project Manager.

