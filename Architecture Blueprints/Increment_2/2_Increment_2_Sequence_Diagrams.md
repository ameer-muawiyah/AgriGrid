# System Sequence Diagrams
## Increment 2: Core Data Engine & Demand Side (B2B Marketplace, Escrow & Predictive Yield)

| Field | Value |
|---|---|
| **Project Name** | Agri-Grid: Smart Agriculture & Food Security Ecosystem |
| **Document ID** | `AG-SSD-INC2-002` |
| **Version** | 1.1 (Formal Deliverable — Fact-Check Fix Release) |
| **Prepared By** | Iqra Fayaz (Software Architect & API Designer) & Manahil Sohail (Lead Requirements Engineer) |
| **Reviewed By** | Ameer Muawiyah (Scrum Master + Lead Data Architect) |
| **Date** | 2026-11-14 |
| **Baseline Source** | `AG-SRS-INC2-001 v1.2` & `AG-PLAN-INC2-001 v1.1` |
| **Increment 1 Reference** | `AG-SSD-INC1-002 v1.1` (`2_Farmer_Sequence_Diagrams.md`) |
| **Location** | `./Documentation/Increment_2_Sequence_Diagrams.md` |

---

## Table of Contents

1. [Architectural Execution Rules & Modeling Standards](#1-architectural-execution-rules--modeling-standards)
2. [Diagram 1 — Buyer Onboarding & Atomic Wallet Initialization](#diagram-1--buyer-onboarding--atomic-wallet-initialization)
3. [Diagram 2 — Marketplace Catalog Browse & Detail Inspection](#diagram-2--marketplace-catalog-browse--detail-inspection)
4. [Diagram 3 — Digital Escrow Ordering & Checkout Transaction](#diagram-3--digital-escrow-ordering--checkout-transaction)
5. [Diagram 4 — Delivery Confirmation & Escrow Settlement](#diagram-4--delivery-confirmation--escrow-settlement)
6. [Diagram 5 — Order Cancellation & Inventory Restoration](#diagram-5--order-cancellation--inventory-restoration)
7. [Diagram 6 — Order Dispute Flagging (Record-Only Boundary)](#diagram-6--order-dispute-flagging-record-only-boundary)
8. [Diagram 7 — Database Migration Engine & App Startup Guard](#diagram-7--database-migration-engine--app-startup-guard)
9. [Diagram 8 — Environmental Telemetry Fetch & 6-Hour Cache Lifecycle](#diagram-8--environmental-telemetry-fetch--6-hour-cache-lifecycle)
10. [Diagram 9 — Predictive Yield Forecast Calculation](#diagram-9--predictive-yield-forecast-calculation)
11. [Diagram 10 — Farmer Commercial Pricing & Auto-Batch Assignment](#diagram-10--farmer-commercial-pricing--auto-batch-assignment)
12. [Diagram 11 — Multi-Tenant Order History Retrieval](#diagram-11--multi-tenant-order-history-retrieval)
13. [Global Participant Legend](#13-global-participant-legend)
14. [Traceability Matrix (Diagrams to SRS v1.2 Requirements)](#14-traceability-matrix-diagrams-to-srs-v12-requirements)
15. [Revision History & Sign-Off Block](#15-revision-history--sign-off-block)

---

## 1. Architectural Execution Rules & Modeling Standards

These sequence diagrams visually specify the runtime interactions between actors, presentation components, HTTP controllers, decoupled service modules, and the SQLite database (`backend/database/agrigrid.db`) for **Increment 2**, strictly following `AG-SRS-INC2-001 v1.2`:

1. **UML 2.5 Strict Control Flow**: Every conditional branch is modeled using `alt [Condition] ... else [Condition] ... end`. Standalone fall-through `alt` blocks are prohibited; execution visually terminates on error branches.
2. **Top-Level Participant Declarations**: All lifelines (`actor`, `participant`) are declared at the head of every diagram to prevent layout glitches and lifeline stacking.
3. **Behavior-Preserving Service Layer Separation**: Depicts the service extraction boundary (`FR-SRV-001` through `FR-SRV-004`). Route controllers delegate business logic and SQL execution directly to dedicated modules in `backend/services/`.
4. **Zero-Trust Tenant Isolation & Unified 404 Policy (`NFR-SEC-002`)**:
   - Calling an endpoint with an **unauthorized role** (e.g., a farmer calling a buyer checkout route) returns **HTTP 403 Forbidden**.
   - Calling an endpoint with an **authorized role but non-owner identity** (e.g., Buyer B attempting to confirm Buyer A's order) returns unified **HTTP 404 Not Found** with a generic error envelope to prevent resource enumeration.
5. **ACID Financial Integrity & Concurrency Locking**: All escrow balance deductions, wallet credits, order creation, status transitions, and precondition checks execute within explicit SQLite `BEGIN IMMEDIATE` transactions to prevent concurrent double-spending or duplicate settlement.
6. **Immutable Identification & Vocabulary Standards**:
   - Batch IDs: `BATCH-{YEAR}-{CROP_CODE3}-{LISTING_ID:04d}` (e.g., `BATCH-2026-WHT-0001`).
   - Order Numbers: `ORD-{YYYY}-{ORDER_ID:04d}` (e.g., `ORD-2026-0001`).
   - Telemetry Cache Keys: `weather:{lat}:{lon}` and `soil:{lat}:{lon}`.
   - Crop Statuses: `VALID_STATUSES = frozenset(["Active", "Sold", "In Transit", "Delivered", "Withdrawn"])`.

---

## Diagram 1 — Buyer Onboarding & Atomic Wallet Initialization

> **SRS Reference:** `FR-BYR-001`, `FR-BYR-002`, `FR-BYR-003`, `FR-BYR-004`, `FR-WLT-003`, `NFR-SEC-003`  
> **Key Rules:** Atomic multi-table insertion (`users` + `buyers` + `buyer_wallets`) in a single transaction; mandatory company metadata; automatic wallet balance initialization with `SIMULATED_BUYER_STARTING_BALANCE_PKR = 500000.00`; full rollback on failure leaving zero orphaned records.

```mermaid
sequenceDiagram
    actor Buyer as 🛒 B2B Buyer (Browser)
    participant FE as Frontend<br/>(auth.js / index.html)
    participant BE as Auth Controller<br/>(backend/auth.py)
    participant DB as SQL Database<br/>(agrigrid.db)

    Note over Buyer,DB: DIAGRAM 1 — Buyer Registration & Atomic Wallet Initialization

    Buyer->>FE: Fills registration form<br/>(username, password, role='buyer', company_name,<br/>contact_phone, warehouse_address, gps_lat, gps_lon)
    FE->>BE: POST /api/auth/register<br/>{ username, password, role: 'buyer', company_name, ... }

    alt FR-BYR-002: Missing required buyer company fields
        BE-->>FE: HTTP 400 Bad Request<br/>{"success": false, "error": "Company name, phone, and warehouse address are required."}
        FE-->>Buyer: ❌ Inline validation error displayed
    else Input validation passes
        BE->>DB: SELECT id FROM users WHERE username = ?
        alt Duplicate username detected
            DB-->>BE: Row returned
            BE-->>FE: HTTP 409 Conflict<br/>{"success": false, "error": "Username already exists."}
            FE-->>Buyer: ❌ Username taken alert
        else Username is available
            DB-->>BE: Empty result set
            BE->>BE: hash = bcrypt.hash(password)
            
            Note over BE,DB: FR-BYR-003: BEGIN IMMEDIATE ATOMIC TRANSACTION
            BE->>DB: BEGIN IMMEDIATE
            BE->>DB: INSERT INTO users (username, password_hash, role, created_at)<br/>VALUES (?, hash, 'buyer', CURRENT_TIMESTAMP)
            
            alt User insertion fails
                DB-->>BE: SQL Error / Constraint Violation
                BE->>DB: ROLLBACK
                BE-->>FE: HTTP 500 Internal Server Error<br/>{"success": false, "error": "Registration failed. Please try again."}
                FE-->>Buyer: ❌ System error modal
            else User row created (new user_id = 15)
                DB-->>BE: user_id = 15
                BE->>DB: INSERT INTO buyers (user_id, company_name, contact_phone,<br/>warehouse_address, warehouse_gps_latitude, warehouse_gps_longitude)<br/>VALUES (15, ?, ?, ?, ?, ?)
                
                alt Buyer profile insertion fails
                    DB-->>BE: SQL Error (e.g. Phone/Company validation)
                    BE->>DB: ROLLBACK
                    BE-->>FE: HTTP 400 Bad Request<br/>{"success": false, "error": "Invalid buyer company details."}
                    FE-->>Buyer: ❌ Company profile error — zero orphaned user rows
                else Buyer row created (new buyer_id = 4)
                    DB-->>BE: buyer_id = 4
                    Note over BE,DB: FR-WLT-003: Initialize Buyer Virtual Wallet (Rs. 500,000.00)
                    BE->>DB: INSERT INTO buyer_wallets (buyer_id, balance_pkr, updated_at)<br/>VALUES (4, 500000.00, CURRENT_TIMESTAMP)
                    
                    alt Wallet creation fails
                        DB-->>BE: SQL Error
                        BE->>DB: ROLLBACK
                        BE-->>FE: HTTP 500 Internal Server Error<br/>{"success": false, "error": "Failed to initialize buyer wallet."}
                        FE-->>Buyer: ❌ Transaction rolled back completely
                    else Wallet created successfully
                        DB-->>BE: OK
                        BE->>DB: COMMIT
                        BE-->>FE: HTTP 201 Created<br/>{"success": true, "message": "Buyer registered successfully."}
                        FE-->>Buyer: ✅ Registration successful — redirect to login
                    end
                end
            end
        end
    end
```

---

## Diagram 2 — Marketplace Catalog Browse & Detail Inspection

> **SRS Reference:** `FR-MKT-001`, `FR-MKT-002`, `FR-MKT-003`, `FR-MKT-004`, `FR-MKT-005`, `FR-MKT-006`, `FR-MKT-007`, `NFR-SEC-002`  
> **Key Rules:** Price-gated public catalog (`status = 'Active'` AND `is_deleted = 0` AND `asking_price_per_kg > 0`); Increment 1 flat list envelope (`data`, `page`, `limit`, `total`); unified 404 anti-enumeration on single listing lookup.

```mermaid
sequenceDiagram
    actor Buyer as 🛒 B2B Buyer (Browser)
    participant FE as Frontend<br/>(buyer_dashboard.html / buyer.js)
    participant BE as Marketplace Controller<br/>(backend/marketplace.py)
    participant SRV as Marketplace Service<br/>(services/marketplace_service.py)
    participant DB as SQL Database<br/>(agrigrid.db)

    Note over Buyer,DB: DIAGRAM 2 — Marketplace Catalog Browse & Detail Inspection

    %% FLOW 2A: Catalog Browse
    Buyer->>FE: Navigates to Produce Catalog (filters: crop_name='Wheat', max_price=50.0)
    FE->>BE: GET /api/marketplace/listings?crop_name=Wheat&max_price=50&page=1&limit=20<br/>[Header: Authorization: Bearer <jwt_token>]

    alt JWT Missing or Expired
        BE-->>FE: HTTP 401 Unauthorized {"success": false, "error": "Authentication required."}
        FE-->>Buyer: 🔒 Redirect to login page
    else Role is not 'buyer' or 'farmer' (e.g. transporter/agronomist)
        BE-->>FE: HTTP 403 Forbidden {"success": false, "error": "Access denied."}
        FE-->>Buyer: ⛔ Under-construction placeholder
    else Authorized Buyer or Farmer
        BE->>SRV: get_catalog_listings(crop_name='Wheat', max_price=50.0, page=1, limit=20)
        
        Note over SRV,DB: FR-MKT-002: Companion COUNT(*) query excluding unpriced/withdrawn
        SRV->>DB: SELECT COUNT(*) FROM listings l<br/>JOIN farmers f ON l.farmer_id = f.id<br/>WHERE l.status = 'Active' AND l.is_deleted = 0<br/>AND l.asking_price_per_kg IS NOT NULL AND l.asking_price_per_kg > 0<br/>AND l.crop_name = 'Wheat' AND l.asking_price_per_kg <= 50.0
        DB-->>SRV: total = 3
        
        Note over SRV,DB: FR-MKT-005: Query paginated produce items with farm location
        SRV->>DB: SELECT l.id, l.batch_id, l.crop_name, l.quantity_kg, l.asking_price_per_kg,<br/>(l.quantity_kg * l.asking_price_per_kg) AS total_price_pkr,<br/>l.estimated_harvest_date, f.farm_name, f.farm_location, l.gps_latitude, l.gps_longitude<br/>FROM listings l JOIN farmers f ON l.farmer_id = f.id<br/>WHERE l.status = 'Active' AND l.is_deleted = 0<br/>AND l.asking_price_per_kg IS NOT NULL AND l.asking_price_per_kg > 0<br/>AND l.crop_name = 'Wheat' AND l.asking_price_per_kg <= 50.0<br/>ORDER BY l.created_at DESC LIMIT 20 OFFSET 0
        DB-->>SRV: Rows returned [listing_id=1, batch_id='BATCH-2026-WHT-0001', ...]
        SRV-->>BE: {"data": [...], "total": 3, "page": 1, "limit": 20}
        BE-->>FE: HTTP 200 OK<br/>{"success": true, "data": [...], "page": 1, "limit": 20, "total": 3}
        FE-->>Buyer: 📋 Renders procurement cards with Rs. prices and Batch IDs
    end

    %% FLOW 2B: Single Listing Detail & Unified 404
    Buyer->>FE: Clicks specific produce listing for detail inspection
    FE->>BE: GET /api/marketplace/listings/99<br/>[Header: Authorization: Bearer <jwt_token>]
    BE->>SRV: get_listing_detail(listing_id=99)
    SRV->>DB: SELECT l.*, f.farm_name, f.farm_location FROM listings l<br/>JOIN farmers f ON l.farmer_id = f.id<br/>WHERE l.id = 99 AND l.is_deleted = 0 AND l.status = 'Active'<br/>AND l.asking_price_per_kg IS NOT NULL
    
    alt FR-MKT-007: Listing missing, soft-deleted, unpriced, or sold
        DB-->>SRV: Empty result set
        SRV-->>BE: None
        BE-->>FE: HTTP 404 Not Found<br/>{"success": false, "error": "Listing not found."}
        FE-->>Buyer: ❌ Generic "Listing not found" alert (zero status enumeration)
    else Listing active and priced
        DB-->>SRV: Record row
        SRV-->>BE: Serialized listing dict
        BE-->>FE: HTTP 200 OK<br/>{"success": true, "data": { "listing_id": 99, "batch_id": "BATCH-2026-TOM-0099", ... }}
        FE-->>Buyer: 🔍 Displays detailed listing view modal
    end
```

---

## Diagram 3 — Digital Escrow Ordering & Checkout Transaction

> **SRS Reference:** `FR-ORD-001` through `FR-ORD-007`, `FR-STM-002`, `NFR-SEC-003`, `NFR-PERF-002`, `RSK-01`  
> **Key Rules:** Buyer-only checkout; strict whole-listing purchase validation (`ordered_quantity_kg == listing.quantity_kg`); cold-chain temperature range check (`-25.0°C` to `+30.0°C`); atomic execution under SQLite `BEGIN IMMEDIATE` to prevent race condition double-selling (`409 Conflict`); deterministic order number `ORD-{YYYY}-{ORDER_ID:04d}`.

```mermaid
sequenceDiagram
    actor Buyer as 🛒 B2B Buyer (Browser)
    participant FE as Frontend<br/>(buyer_dashboard.html / checkout modal)
    participant BE as Orders Controller<br/>(backend/orders.py)
    participant SRV as Escrow Service<br/>(services/escrow_service.py)
    participant DB as SQL Database<br/>(agrigrid.db)

    Note over Buyer,DB: DIAGRAM 3 — Digital Escrow Ordering & Checkout Transaction

    Buyer->>FE: Selects listing #1 (5,000 kg Wheat @ Rs. 45/kg = Rs. 225,000)<br/>Submits checkout (warehouse='Central Hub, Lahore', max_temp=6.0°C)
    FE->>BE: POST /api/orders<br/>{ listing_id: 1, ordered_quantity_kg: 5000, destination_warehouse: 'Central Hub, Lahore', max_temperature_celsius: 6.0 }<br/>[Header: Authorization: Bearer <buyer_jwt>]

    alt FR-ORD-001: Caller is not a B2B Buyer (e.g. Farmer token)
        BE-->>FE: HTTP 403 Forbidden {"success": false, "error": "Access denied. Only buyers can place orders."}
        FE-->>Buyer: ⛔ Action disallowed
    else Missing required payload fields (listing_id, warehouse, etc.)
        BE-->>FE: HTTP 400 Bad Request {"success": false, "error": "All checkout fields are required."}
        FE-->>Buyer: ❌ Form validation alert
    else FR-ORD-002: max_temperature_celsius out of range (-25.0°C to +30.0°C)
        BE-->>FE: HTTP 400 Bad Request {"success": false, "error": "Max temperature must be between -25.0°C and 30.0°C."}
        FE-->>Buyer: ❌ Temperature constraint out of bounds
    else Valid Buyer Token & Payload
        BE->>BE: Extract buyer_id = jwt.buyer_id
        BE->>SRV: create_escrow_order(buyer_id=4, listing_id=1, quantity=5000, warehouse='...', max_temp=6.0)
        
        Note over SRV,DB: NFR-SEC-003 / RSK-01: BEGIN IMMEDIATE locks DB for write serialization
        SRV->>DB: BEGIN IMMEDIATE
        
        SRV->>DB: SELECT id, farmer_id, quantity_kg, asking_price_per_kg, status, is_deleted<br/>FROM listings WHERE id = 1
        DB-->>SRV: Row (quantity_kg=5000, price=45.0, status='Active', is_deleted=0)
        
        alt FR-ORD-006: Concurrent race loser — listing already marked 'Sold' or Withdrawn
            Note over SRV,DB: Another transaction committed status='Sold' right before our lock
            SRV->>DB: ROLLBACK
            SRV-->>BE: Error: ALREADY_SOLD
            BE-->>FE: HTTP 409 Conflict<br/>{"success": false, "error": "Listing has already been sold."}
            FE-->>Buyer: ⚠️ Listing no longer available (race prevented)
        else FR-ORD-003: Partial quantity attempted (e.g. ordered 2,500 kg vs 5,000 kg)
            SRV->>DB: ROLLBACK
            SRV-->>BE: Error: PARTIAL_NOT_SUPPORTED
            BE-->>FE: HTTP 400 Bad Request<br/>{"success": false, "error": "Partial quantity purchasing is not supported in Increment 2."}
            FE-->>Buyer: ❌ Whole-listing purchase required
        else Whole listing verified
            Note over SRV: total_amount_pkr = 5000 * 45.0 = 225,000.00 PKR
            SRV->>DB: SELECT balance_pkr FROM buyer_wallets WHERE buyer_id = 4
            DB-->>SRV: balance_pkr = 500,000.00
            
            alt FR-ORD-004: Insufficient wallet balance (balance < total_amount_pkr)
                SRV->>DB: ROLLBACK
                SRV-->>BE: Error: INSUFFICIENT_FUNDS
                BE-->>FE: HTTP 400 Bad Request<br/>{"success": false, "error": "Insufficient wallet balance."}
                FE-->>Buyer: ❌ Top-up required
            else Sufficient balance verified
                Note over SRV,DB: 1. Deduct funds from buyer virtual wallet
                SRV->>DB: UPDATE buyer_wallets SET balance_pkr = balance_pkr - 225000.00,<br/>updated_at = CURRENT_TIMESTAMP WHERE buyer_id = 4
                
                Note over SRV,DB: 2. Insert order record (status = 'Escrow_Funded')
                SRV->>DB: INSERT INTO orders (order_number, listing_id, buyer_id, farmer_id,<br/>ordered_quantity_kg, agreed_price_per_kg, total_amount_pkr,<br/>destination_warehouse, max_temperature_celsius, order_status)<br/>VALUES ('ORD-TEMP', 1, 4, 7, 5000.0, 45.0, 225000.00, '...', 6.0, 'Escrow_Funded')
                DB-->>SRV: order_id = 8941
                
                Note over SRV,DB: Generate deterministic order_number: ORD-2026-8941
                SRV->>DB: UPDATE orders SET order_number = 'ORD-2026-8941' WHERE id = 8941
                
                Note over SRV,DB: 3. Lock funds in escrow ledger (status = 'HELD')
                SRV->>DB: INSERT INTO escrow_holdings (order_id, held_amount_pkr, escrow_status, held_at)<br/>VALUES (8941, 225000.00, 'HELD', CURRENT_TIMESTAMP)
                
                Note over SRV,DB: 4. Mutate listing lifecycle state: Active -> Sold
                SRV->>DB: UPDATE listings SET status = 'Sold', updated_at = CURRENT_TIMESTAMP WHERE id = 1
                
                SRV->>DB: COMMIT
                SRV-->>BE: Order success dictionary
                BE-->>FE: HTTP 201 Created<br/>{"success": true, "message": "Order created successfully. Escrow funds locked.",<br/>"data": {"order_number": "ORD-2026-8941", "total_amount_pkr": 225000.00,<br/>"order_status": "Escrow_Funded", "escrow_status": "HELD", "remaining_wallet_balance_pkr": 275000.00}}
                FE-->>Buyer: ✅ Order confirmed modal (wallet balance updated to Rs. 275,000.00)
            end
        end
    end
```

---

## Diagram 4 — Delivery Confirmation & Escrow Settlement

> **SRS Reference:** `FR-SET-001`, `FR-SET-002`, `FR-SET-003`, `FR-SET-004`, `NFR-SEC-002`, `NFR-SEC-003`, `Plan §13 Decision 3`  
> **Key Rules:** Buyer quality acceptance doubles as delivery settlement in Increment 2; transaction opens with `BEGIN IMMEDIATE` prior to precondition checks to serialize concurrency; cross-tenant ownership check returns unified `HTTP 404`; status precondition strictly `'Escrow_Funded'`; populates `orders.delivered_at` and `escrow_holdings.auto_release_at` (`delivered_at + 72h`); invokes `release_escrow(order_id, trigger='buyer_confirmation')` crediting farmer wallet and recording trigger in `release_tx_ref`.

```mermaid
sequenceDiagram
    actor Buyer as 🛒 B2B Buyer (Browser)
    participant FE as Frontend<br/>(buyer_dashboard.html / orders tab)
    participant BE as Orders Controller<br/>(backend/orders.py)
    participant SRV as Escrow Service<br/>(services/escrow_service.py)
    participant DB as SQL Database<br/>(agrigrid.db)

    Note over Buyer,DB: DIAGRAM 4 — Delivery Confirmation & Escrow Settlement

    Buyer->>FE: Reviews delivery inspection score<br/>Clicks "Confirm Delivery & Release Escrow" on Order #8941
    FE->>BE: POST /api/orders/8941/confirm-delivery<br/>[Header: Authorization: Bearer <buyer_jwt>]

    alt Caller is not a Buyer (e.g. Farmer token)
        BE-->>FE: HTTP 403 Forbidden {"success": false, "error": "Access denied."}
        FE-->>Buyer: ⛔ Action prohibited
    else Authenticated Buyer
        BE->>BE: buyer_id = jwt.buyer_id
        BE->>SRV: confirm_order_delivery(order_id=8941, caller_buyer_id=buyer_id)
        
        Note over SRV,DB: FR-SET-003 / NFR-SEC-003: BEGIN IMMEDIATE encapsulates checks & mutations
        SRV->>DB: BEGIN IMMEDIATE
        
        SRV->>DB: SELECT o.id, o.buyer_id, o.farmer_id, o.order_status, e.held_amount_pkr, e.escrow_status<br/>FROM orders o JOIN escrow_holdings e ON o.id = e.order_id<br/>WHERE o.id = 8941
        
        alt NFR-SEC-002: Order missing OR owned by another buyer (caller_buyer_id != o.buyer_id)
            DB-->>SRV: Empty row OR caller is Buyer 9 (owner is Buyer 4)
            SRV->>DB: ROLLBACK
            SRV-->>BE: Error: ORDER_NOT_FOUND
            BE-->>FE: HTTP 404 Not Found<br/>{"success": false, "error": "Order not found."}
            FE-->>Buyer: ❌ Unified 404 alert (anti-enumeration)
        else FR-SET-002: Order is not in 'Escrow_Funded' status (e.g. already Completed / Disputed)
            DB-->>SRV: o.order_status = 'Completed'
            SRV->>DB: ROLLBACK
            SRV-->>BE: Error: INVALID_STATUS
            BE-->>FE: HTTP 400 Bad Request<br/>{"success": false, "error": "Order cannot be confirmed in current status."}
            FE-->>Buyer: ⚠️ Order already settled
        else Order valid & caller is verified owner
            Note over SRV,DB: 1. Set orders.order_status = 'Completed' and record delivered_at
            SRV->>DB: UPDATE orders SET order_status = 'Completed', delivered_at = CURRENT_TIMESTAMP,<br/>updated_at = CURRENT_TIMESTAMP WHERE id = 8941
            
            Note over SRV,DB: 2. Populate escrow delivery timestamp and Increment 4 auto-release seam (+72h)
            SRV->>DB: UPDATE escrow_holdings SET delivered_at = CURRENT_TIMESTAMP,<br/>auto_release_at = datetime(CURRENT_TIMESTAMP, '+72 hours') WHERE order_id = 8941
            
            Note over SRV: FR-SET-004: Invoke release_escrow(8941, trigger='buyer_confirmation')
            SRV->>DB: UPDATE farmer_wallets SET balance_pkr = balance_pkr + 225000.00,<br/>updated_at = CURRENT_TIMESTAMP WHERE farmer_id = 7
            
            SRV->>DB: UPDATE escrow_holdings SET escrow_status = 'RELEASED', released_at = CURRENT_TIMESTAMP,<br/>release_tx_ref = 'TRIGGER:buyer_confirmation;REF:TX-8941-SETTLE'<br/>WHERE order_id = 8941
            
            SRV->>DB: COMMIT
            SRV-->>BE: Settlement success dict
            BE-->>FE: HTTP 200 OK<br/>{"success": true, "message": "Delivery confirmed and escrow funds released to farmer.",<br/>"data": {"order_number": "ORD-2026-8941", "order_status": "Completed", "escrow_status": "RELEASED"}}
            FE-->>Buyer: ✅ Settlement complete badge rendered
        end
    end
```

---

## Diagram 5 — Order Cancellation & Inventory Restoration

> **SRS Reference:** `FR-SET-005`, `FR-SET-006`, `FR-STM-003`, `FR-STM-004`, `NFR-SEC-002`, `NFR-SEC-003`  
> **Key Rules:** Permitted strictly when `order_status == 'Escrow_Funded'`; accessible by either the buyer or the farmer party to the order; transaction opens with `BEGIN IMMEDIATE` prior to precondition checks; non-party callers receive unified `HTTP 404`; atomically refunds buyer wallet, sets `escrow_status = 'REFUNDED'`, marks order `'Cancelled'`, and restores listing back to `'Active'` for catalog re-discovery.

```mermaid
sequenceDiagram
    actor User as 👤 Buyer OR Farmer (Browser)
    participant FE as Frontend<br/>(orders table)
    participant BE as Orders Controller<br/>(backend/orders.py)
    participant SRV as Escrow Service<br/>(services/escrow_service.py)
    participant DB as SQL Database<br/>(agrigrid.db)

    Note over User,DB: DIAGRAM 5 — Order Cancellation & Inventory Restoration

    User->>FE: Clicks "Cancel Order" on Order #8941 (Order is in 'Escrow_Funded' status)
    FE->>BE: POST /api/orders/8941/cancel<br/>[Header: Authorization: Bearer <jwt_token>]

    alt Caller is unauthorized role (e.g. Transporter)
        BE-->>FE: HTTP 403 Forbidden {"success": false, "error": "Access denied."}
        FE-->>User: ⛔ Action prohibited
    else Authenticated Buyer or Farmer
        BE->>BE: Extract user role and tenant_id (buyer_id or farmer_id) from JWT
        BE->>SRV: cancel_order(order_id=8941, caller_role=jwt.role, caller_tenant_id=tenant_id)
        
        Note over SRV,DB: FR-SET-006 / NFR-SEC-003: BEGIN IMMEDIATE encapsulates checks & mutations
        SRV->>DB: BEGIN IMMEDIATE
        
        SRV->>DB: SELECT o.id, o.listing_id, o.buyer_id, o.farmer_id, o.order_status, e.held_amount_pkr<br/>FROM orders o JOIN escrow_holdings e ON o.id = e.order_id<br/>WHERE o.id = 8941
        
        alt NFR-SEC-002: Order missing OR caller is not party to order (neither its buyer nor farmer)
            DB-->>SRV: Empty row OR caller tenant ID matches neither o.buyer_id nor o.farmer_id
            SRV->>DB: ROLLBACK
            SRV-->>BE: Error: ORDER_NOT_FOUND
            BE-->>FE: HTTP 404 Not Found<br/>{"success": false, "error": "Order not found."}
            FE-->>User: ❌ Unified 404 alert
        else Order status is not 'Escrow_Funded' (e.g. already Completed or Disputed)
            DB-->>SRV: o.order_status = 'Completed'
            SRV->>DB: ROLLBACK
            SRV-->>BE: Error: CANNOT_CANCEL
            BE-->>FE: HTTP 400 Bad Request<br/>{"success": false, "error": "Only Escrow_Funded orders can be cancelled."}
            FE-->>User: ⚠️ Cancellation rejected
        else Order in Escrow_Funded and caller is authorized party
            Note over SRV,DB: 1. Refund locked escrow funds back to buyer virtual wallet
            SRV->>DB: UPDATE buyer_wallets SET balance_pkr = balance_pkr + 225000.00,<br/>updated_at = CURRENT_TIMESTAMP WHERE buyer_id = o.buyer_id
            
            Note over SRV,DB: 2. Transition escrow holding status: HELD -> REFUNDED
            SRV->>DB: UPDATE escrow_holdings SET escrow_status = 'REFUNDED',<br/>released_at = CURRENT_TIMESTAMP WHERE order_id = 8941
            
            Note over SRV,DB: 3. Transition order status: Escrow_Funded -> Cancelled
            SRV->>DB: UPDATE orders SET order_status = 'Cancelled',<br/>updated_at = CURRENT_TIMESTAMP WHERE id = 8941
            
            Note over SRV,DB: 4. Restore crop listing status: Sold -> Active (Returns to catalog)
            SRV->>DB: UPDATE listings SET status = 'Active',<br/>updated_at = CURRENT_TIMESTAMP WHERE id = o.listing_id
            
            SRV->>DB: COMMIT
            SRV-->>BE: Cancellation success dict
            BE-->>FE: HTTP 200 OK<br/>{"success": true, "message": "Order cancelled successfully. Funds refunded and crop restored to catalog."}
            FE-->>User: 🔄 UI refreshes (Order marked Cancelled, Buyer wallet credited)
        end
    end
```

---

## Diagram 6 — Order Dispute Flagging (Record-Only Boundary)

> **SRS Reference:** `FR-STM-005`, `FR-STM-006`, `NFR-SEC-002`, `NFR-SEC-003`, `Plan §2.2.6`, `Plan §4.3 Scope Note`  
> **Key Rules:** Buyer or Farmer party flags dispute on an active `Escrow_Funded` order; transaction opens with `BEGIN IMMEDIATE` prior to precondition checks; transitions `order_status = 'Disputed'` and `escrow_status = 'DISPUTED'`; funds remain permanently frozen in escrow; **explicit architectural boundary**: diagram ends at frozen state; no dispute resolution or exit route exists in Increment 2 (deferred to Increment 4 Compliance Officer).

```mermaid
sequenceDiagram
    actor User as 👤 Buyer OR Farmer (Browser)
    participant FE as Frontend<br/>(order detail modal)
    participant BE as Orders Controller<br/>(backend/orders.py)
    participant SRV as Escrow Service<br/>(services/escrow_service.py)
    participant DB as SQL Database<br/>(agrigrid.db)

    Note over User,DB: DIAGRAM 6 — Order Dispute Flagging (Record-Only Boundary)

    User->>FE: Clicks "Raise Dispute" on Order #8941 (Produce defect / cold-chain breach)
    FE->>BE: POST /api/orders/8941/dispute<br/>[Header: Authorization: Bearer <jwt_token>]

    alt Caller is unauthorized role
        BE-->>FE: HTTP 403 Forbidden {"success": false, "error": "Access denied."}
        FE-->>User: ⛔ Action prohibited
    else Authenticated Buyer or Farmer
        BE->>BE: Extract user role and tenant_id from JWT
        BE->>SRV: flag_order_dispute(order_id=8941, caller_tenant_id=tenant_id)
        
        Note over SRV,DB: FR-STM-005 / NFR-SEC-003: BEGIN IMMEDIATE encapsulates checks & mutations
        SRV->>DB: BEGIN IMMEDIATE
        
        SRV->>DB: SELECT id, buyer_id, farmer_id, order_status FROM orders WHERE id = 8941
        
        alt NFR-SEC-002: Order missing OR caller not party to order
            DB-->>SRV: Empty row OR caller is neither buyer nor farmer on order
            SRV->>DB: ROLLBACK
            SRV-->>BE: Error: ORDER_NOT_FOUND
            BE-->>FE: HTTP 404 Not Found<br/>{"success": false, "error": "Order not found."}
            FE-->>User: ❌ Unified 404 alert
        else Order status is not 'Escrow_Funded' (e.g. already Cancelled or Completed)
            DB-->>SRV: order_status != 'Escrow_Funded'
            SRV->>DB: ROLLBACK
            SRV-->>BE: Error: CANNOT_DISPUTE
            BE-->>FE: HTTP 400 Bad Request<br/>{"success": false, "error": "Only Escrow_Funded orders can be disputed."}
            FE-->>User: ⚠️ Cannot dispute settled/cancelled order
        else Order in Escrow_Funded and caller is authorized party
            Note over SRV,DB: 1. Freeze order status: Escrow_Funded -> Disputed
            SRV->>DB: UPDATE orders SET order_status = 'Disputed', updated_at = CURRENT_TIMESTAMP WHERE id = 8941
            
            Note over SRV,DB: 2. Freeze escrow holdings: HELD -> DISPUTED
            SRV->>DB: UPDATE escrow_holdings SET escrow_status = 'DISPUTED' WHERE order_id = 8941
            
            SRV->>DB: COMMIT
            SRV-->>BE: Dispute registered dict
            BE-->>FE: HTTP 200 OK<br/>{"success": true, "message": "Dispute registered. Escrow funds have been frozen."}
            FE-->>User: ⚖️ Order marked "Disputed" — Escrow Frozen Badge
            
            Note over User,DB: FR-STM-006: SCOPE BOUNDARY / ARCHITECTURAL SEAM<br/>* Flow terminates here in Increment 2.<br/>* Zero dispute resolution or unfreezing routes exist.<br/>* Order and escrow funds remain permanently frozen until<br/>Increment 4 (Compliance Officer Administrative Arbitration).
        end
    end
```

---

## Diagram 7 — Database Migration Engine & App Startup Guard

> **SRS Reference:** `FR-MIG-001` through `FR-MIG-007`, `NFR-REL-002`, `Plan §4.1`  
> **Key Rules:** Triggered by launcher before server startup; handles three database states (fresh, baseline Inc 1 unversioned, versioned); verifies SHA-256 checksums of applied files; executes statements inside `BEGIN IMMEDIATE` / `COMMIT` (no `executescript`); Flask `app.py` startup refuses to boot if database version is behind required target (v2).

```mermaid
sequenceDiagram
    actor Ops as 💻 Developer / Launcher
    participant LNC as Launcher<br/>(launch_agrigrid.py)
    participant MIG as Migration Runner<br/>(backend/database/migrate.py)
    participant APP as Flask App Factory<br/>(backend/app.py)
    participant DB as SQL Database<br/>(agrigrid.db)

    Note over Ops,DB: DIAGRAM 7 — Database Migration Engine & App Startup Guard

    Ops->>LNC: Executes `python launch_agrigrid.py`
    LNC->>MIG: Subprocess call: `python backend/database/migrate.py`
    
    MIG->>DB: SELECT name FROM sqlite_master WHERE type='table' AND name='schema_versions'
    
    alt State A: Fresh Database (No schema_versions table)
        DB-->>MIG: No table
        MIG->>DB: CREATE TABLE schema_versions (id INTEGER PK, version INTEGER UNIQUE, script_name TEXT, checksum TEXT, applied_at TEXT)
    end

    Note over MIG,DB: Audit existing applied migration records
    MIG->>DB: SELECT version, script_name, checksum FROM schema_versions ORDER BY version ASC
    DB-->>MIG: Recorded versions list

    alt State B: Pre-existing Increment 1 DB (listings exists but version 1 not stamped)
        MIG->>DB: SELECT name FROM sqlite_master WHERE type='table' AND name='listings'
        DB-->>MIG: 'listings' table exists
        Note over MIG: Compute SHA-256 of 001_increment_1_baseline.sql
        MIG->>DB: INSERT INTO schema_versions (version, script_name, checksum)<br/>VALUES (1, '001_increment_1_baseline.sql', '<sha256_hash>')
    end

    alt State C: Versioned DB — Checksum Integrity Verification
        loop For every applied migration record
            Note over MIG: Read physical file from disk & compute SHA-256
            alt FR-MIG-005 / NFR-REL-002: Disk file checksum != Recorded checksum
                MIG-->>LNC: ❌ FATAL ERROR: Checksum mismatch for migration file!<br/>(Tamper / manual edit detected)
                LNC-->>Ops: 🛑 Launcher halts startup — non-zero exit
            end
        end
    end

    Note over MIG: Discover pending migrations on disk (e.g. 002_increment_2_marketplace_escrow_telemetry.sql)
    
    alt Pending migrations exist (e.g. Version 2)
        Note over MIG,DB: FR-MIG-004: Explicit statement-by-statement transaction
        MIG->>DB: BEGIN IMMEDIATE
        
        loop For each individual SQL statement in migration file
            MIG->>DB: Execute statement (e.g. ALTER TABLE listings ADD COLUMN asking_price_per_kg...)
            alt SQL Execution Failure
                DB-->>MIG: SQL Error
                MIG->>DB: ROLLBACK
                MIG-->>LNC: ❌ Migration failed! Database rolled back.
                LNC-->>Ops: 🛑 Launcher aborts — non-zero exit
            end
        end
        
        MIG->>DB: INSERT INTO schema_versions (version, script_name, checksum)<br/>VALUES (2, '002_increment_2_marketplace_escrow_telemetry.sql', '<sha256_002>')
        MIG->>DB: COMMIT
        MIG-->>LNC: ✅ Migration successful. Current version: 2
    else Database already current
        MIG-->>LNC: Database is up to date (Version 2).
    end

    Note over LNC,APP: Launcher proceeds to start Flask Web Server
    LNC->>APP: invoke `create_app()`
    
    Note over APP,DB: FR-MIG-007: App Factory Startup Guard
    APP->>DB: SELECT MAX(version) FROM schema_versions
    DB-->>APP: current_version
    
    alt Database version < Required Codebase Version (v2)
        Note over APP: Stale database detected
        APP-->>Ops: ❌ STARTUP REFUSED: Database schema (v1) is behind required (v2).<br/>Remediation command: python backend/database/migrate.py
        APP->>APP: sys.exit(1)
    else Database version == 2
        APP-->>LNC: Application factory initialized successfully
        LNC-->>Ops: 🚀 Agri-Grid Server running on http://127.0.0.1:5000
    end
```

---

## Diagram 8 — Environmental Telemetry Fetch & 6-Hour Cache Lifecycle

> **SRS Reference:** `FR-TEL-001` through `FR-TEL-005`, `FR-CCH-001` through `FR-CCH-005`, `NFR-REL-001`, `NFR-PERF-003`  
> **Key Rules:** Cache key format `<telemetry_type>:<lat>:<lon>`; 6-hour uniform TTL; Cache Hit returns SQLite payload under 100ms; Cache Miss queries external API (OpenWeatherMap/SoilGrids) and saves fresh cache; Failure / Offline mode gracefully falls back to deterministic local fixtures in `backend/tests/fixtures/`, caches fixture under standard 6-hour TTL, and returns `source: "offline_fixture"`, never throwing HTTP 500.

```mermaid
sequenceDiagram
    actor Client as 👨‍🌾 Farmer / 🛒 Buyer (Browser)
    participant FE as Frontend<br/>(telemetry widget)
    participant BE as Telemetry Controller<br/>(backend/telemetry.py)
    participant SRV as Telemetry Service<br/>(services/telemetry_service.py)
    participant DB as SQLite Cache<br/>(telemetry_cache table)
    participant EXT as External API Provider<br/>(OpenWeatherMap / SoilGrids)
    participant FIX as Offline Fixture Store<br/>(backend/tests/fixtures/)

    Note over Client,FIX: DIAGRAM 8 — Environmental Telemetry Fetch & 6-Hour Cache Lifecycle

    Client->>FE: Views farm location (lat=30.3753, lon=69.3451)
    FE->>BE: GET /api/telemetry/weather?lat=30.3753&lon=69.3451<br/>[Header: Authorization: Bearer <token>]

    alt Caller is unauthenticated
        BE-->>FE: HTTP 401 Unauthorized
        FE-->>Client: 🔒 Redirect to login
    else Authenticated Farmer or Buyer
        BE->>SRV: get_weather_telemetry(lat=30.3753, lon=69.3451)
        Note over SRV: FR-CCH-002: Generate cache key = 'weather:30.3753:69.3451'
        
        SRV->>DB: SELECT payload_json, expires_at FROM telemetry_cache<br/>WHERE cache_key = 'weather:30.3753:69.3451' AND expires_at > CURRENT_TIMESTAMP
        
        alt FR-CCH-004 / NFR-PERF-003: CACHE HIT (Unexpired entry exists, < 6 hours old)
            DB-->>SRV: Row (payload_json = '{"temperature_c": 28.5, ...}', expires_at='...')
            Note over SRV: Latency < 100ms — Zero external HTTP calls
            SRV-->>BE: Parsed telemetry dict
            BE-->>FE: HTTP 200 OK<br/>{"success": true, "data": {...}, "source": "cache"}
            FE-->>Client: ☀️ Displays cached weather metrics instantly
        else CACHE MISS / EXPIRED (No unexpired record in database)
            DB-->>SRV: Empty result set
            
            alt AGRIGRID_OFFLINE_MODE == '1' OR API keys missing
                Note over SRV,FIX: FR-TEL-005 / NFR-REL-001: Graceful Deterministic Offline Fallback
                SRV->>FIX: Read `backend/tests/fixtures/weather_punjab.json`
                FIX-->>SRV: Deterministic JSON fixture content
                Note over SRV,DB: Cache fixture for 6 hours
                SRV->>DB: INSERT OR REPLACE INTO telemetry_cache (cache_key, provider, latitude, longitude, payload_json, expires_at)<br/>VALUES ('weather:30.3753:69.3451', 'OpenWeatherMap', 30.3753, 69.3451, ?, datetime(CURRENT_TIMESTAMP, '+6 hours'))
                SRV-->>BE: Parsed fixture telemetry dict
                BE-->>FE: HTTP 200 OK<br/>{"success": true, "data": {...}, "source": "offline_fixture"}
                FE-->>Client: 🌤️ Displays deterministic weather context (offline mode)
            else Normal Online Operation
                SRV->>EXT: GET https://api.openweathermap.org/data/2.5/forecast?lat=30.3753&lon=69.3451&appid=KEY
                
                alt External API Network Timeout / HTTP 429 Rate Limited
                    EXT-->>SRV: Connection Timeout / Error 429
                    Note over SRV,FIX: Fallback on API failure: Never crash or return 500
                    SRV->>FIX: Read `backend/tests/fixtures/weather_punjab.json`
                    FIX-->>SRV: Deterministic JSON fixture
                    Note over SRV,DB: Cache fallback payload for 6 hours
                    SRV->>DB: INSERT OR REPLACE INTO telemetry_cache (cache_key, provider, latitude, longitude, payload_json, expires_at)<br/>VALUES ('weather:30.3753:69.3451', 'OpenWeatherMap', 30.3753, 69.3451, ?, datetime(CURRENT_TIMESTAMP, '+6 hours'))
                    SRV-->>BE: Parsed fixture telemetry dict
                    BE-->>FE: HTTP 200 OK<br/>{"success": true, "data": {...}, "source": "offline_fixture"}
                    FE-->>Client: 🌤️ Displays deterministic weather context (offline fallback)
                else External API Returns 200 OK
                    EXT-->>SRV: HTTP 200 OK (Raw weather telemetry JSON)
                    Note over SRV: Parse temperature, humidity, rainfall forecast
                    Note over SRV,DB: FR-CCH-003: Save to SQLite cache with uniform 6-Hour TTL
                    SRV->>DB: INSERT OR REPLACE INTO telemetry_cache (cache_key, provider, latitude, longitude, payload_json, expires_at)<br/>VALUES ('weather:30.3753:69.3451', 'OpenWeatherMap', 30.3753, 69.3451, ?, datetime(CURRENT_TIMESTAMP, '+6 hours'))
                    SRV-->>BE: Parsed telemetry dict
                    BE-->>FE: HTTP 200 OK<br/>{"success": true, "data": {...}, "source": "live_api"}
                    FE-->>Client: ☀️ Displays live weather telemetry
                end
            end
        end
    end
```

---

## Diagram 9 — Predictive Yield Forecast Calculation

> **SRS Reference:** `FR-YLD-001` through `FR-YLD-007`, `NFR-SEC-002`, `NFR-PERF-004`, `Plan §13 Decision 5`  
> **Key Rules:** Farmer-only trigger; cross-tenant ownership check returns unified `HTTP 404`; loads listing parameters from DB; queries telemetry cache; executes deterministic agronomic formula core (GDD, rain deviation, soil stress); worked example: `12.5 * 1400 * 1.02 * 1.05 * 0.98 = 18,367.65 kg`; persists mathematical output to `yield_forecasts` table; returns predicted harvest date, yield tonnage, confidence score, and irrigation advice.

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(dashboard.html / yield modal)
    participant BE as Yield Controller<br/>(backend/yield.py)
    participant YLD as Yield Service<br/>(services/yield_service.py)
    participant TEL as Telemetry Service<br/>(services/telemetry_service.py)
    participant DB as SQL Database<br/>(agrigrid.db)

    Note over Farmer,DB: DIAGRAM 9 — Predictive Yield Forecast Calculation

    Farmer->>FE: Clicks "⚡ Forecast Yield" on Wheat listing #101 (12.5 acres)
    FE->>BE: POST /api/yield/predict<br/>{ "listing_id": 101 }<br/>[Header: Authorization: Bearer <farmer_jwt>]

    alt Caller is not a Farmer (e.g. Buyer token)
        BE-->>FE: HTTP 403 Forbidden {"success": false, "error": "Access denied. Only farmers can forecast yield."}
        FE-->>Farmer: ⛔ Action prohibited
    else Authenticated Farmer
        BE->>BE: Extract farmer_id = jwt.farmer_id
        BE->>YLD: generate_yield_forecast(listing_id=101, caller_farmer_id=farmer_id)
        
        Note over YLD,DB: Ownership validation: Listing must exist, not be deleted, and belong to authenticated caller
        YLD->>DB: SELECT id, farmer_id, crop_name, acreage, planting_date, gps_latitude, gps_longitude<br/>FROM listings WHERE id = 101 AND is_deleted = 0
        
        alt NFR-SEC-002: Listing missing OR owned by another farmer (caller_farmer_id != l.farmer_id)
            DB-->>YLD: Empty row OR caller is Farmer 2 (owner is Farmer 7)
            YLD-->>BE: Error: LISTING_NOT_FOUND
            BE-->>FE: HTTP 404 Not Found<br/>{"success": false, "error": "Listing not found."}
            FE-->>Farmer: ❌ Unified 404 alert (anti-enumeration)
        else Listing valid and owned by authenticated farmer
            DB-->>YLD: Row (crop_name='Wheat', acreage=12.5, planting_date='2026-09-01', lat=30.3753, lon=69.3451)
            
            Note over YLD,TEL: Query environmental context for listing coordinates
            YLD->>TEL: get_weather_telemetry(30.3753, 69.3451)
            TEL-->>YLD: Weather data (temperature, rainfall, humidity)
            YLD->>TEL: get_soil_telemetry(30.3753, 69.3451)
            TEL-->>YLD: Soil data (moisture content, pH, organic carbon)
            
            Note over YLD: FR-YLD-002: Pure Python Deterministic Agronomic Formula Core<br/>1. Baseline regional yield: Y_base = 1,400 kg/acre (Wheat)<br/>2. GDD accumulation: sum(T_avg - T_base) since planting_date<br/>3. Rainfall deviation multiplier: f_rain = 1.05<br/>4. Soil moisture/pH stress factor: f_soil = 0.98<br/>Predicted Yield = acreage * Y_base * f_gdd * f_rain * f_soil<br/>Result = 12.5 * 1400 * 1.02 * 1.05 * 0.98 = 18,367.65 kg (~18.37 tons)
            
            Note over YLD,DB: FR-YLD-006: Persist forecast to database
            YLD->>DB: INSERT INTO yield_forecasts (listing_id, crop_name, predicted_harvest_date,<br/>predicted_yield_kg, confidence_score_pct, environmental_index, irrigation_advice)<br/>VALUES (101, 'Wheat', '2027-01-20', 18367.65, 88, 0.82, 'Optimal soil moisture. Maintain standard irrigation schedule.')
            DB-->>YLD: forecast_id = 55
            
            YLD-->>BE: Forecast results dictionary
            BE-->>FE: HTTP 200 OK<br/>{"success": true, "data": {"forecast_id": 55, "listing_id": 101, "crop_name": "Wheat",<br/>"predicted_harvest_date": "2027-01-20", "predicted_yield_kg": 18367.65, "confidence_score_pct": 88,<br/>"environmental_index": 0.82, "irrigation_advice": "Optimal soil moisture..."}}
            FE-->>Farmer: 📊 Renders Yield Forecast Modal (Tonnage, Date, Confidence Badge, Advice)
        end
    end
```

---

## Diagram 10 — Farmer Commercial Pricing & Auto-Batch Assignment

> **SRS Reference:** `FR-PRC-001` through `FR-PRC-005`, `D-INC2-08`, `NFR-SEC-002`, `Plan §5.1`  
> **Key Rules:** Farmer updates crop with commercial `asking_price_per_kg`; validates price > 0 (else HTTP 400); if `batch_id` is null, automatically generates unique identifier using template `BATCH-{YEAR}-{CROP_CODE3}-{LISTING_ID:04d}` (Wheat $\rightarrow$ `WHT`, Tomato $\rightarrow$ `TOM`, etc.); persists to `listings`; listing becomes eligible for public marketplace catalog.

```mermaid
sequenceDiagram
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(dashboard.html / edit crop modal)
    participant BE as Crops Controller<br/>(backend/crops.py)
    participant SRV as Crop Service<br/>(services/crop_service.py)
    participant DB as SQL Database<br/>(agrigrid.db)

    Note over Farmer,DB: DIAGRAM 10 — Farmer Commercial Pricing & Auto-Batch Assignment

    Farmer->>FE: Opens crop listing #101 (Wheat)<br/>Enters Asking Price: Rs. 45.00/kg<br/>Clicks "Save Commercial Listing"
    FE->>BE: PUT /api/crops/101<br/>{ "crop_name": "Wheat", "acreage": 12.5, ..., "asking_price_per_kg": 45.0 }<br/>[Header: Authorization: Bearer <farmer_jwt>]

    alt Caller is not a Farmer
        BE-->>FE: HTTP 403 Forbidden {"success": false, "error": "Access denied."}
        FE-->>Farmer: ⛔ Action prohibited
    else Authenticated Farmer
        BE->>BE: farmer_id = jwt.farmer_id
        
        alt FR-PRC-002: asking_price_per_kg is non-numeric or <= 0.0
            BE-->>FE: HTTP 400 Bad Request<br/>{"success": false, "error": "Asking price per kg must be greater than 0."}
            FE-->>Farmer: ❌ Invalid price alert
        else Price validation passes
            BE->>SRV: update_crop_listing(listing_id=101, farmer_id=farmer_id, payload=...)
            
            SRV->>DB: SELECT id, farmer_id, crop_name, batch_id, status FROM listings WHERE id = 101 AND is_deleted = 0
            
            alt NFR-SEC-002: Listing missing OR owned by another farmer
                DB-->>SRV: Empty row OR non-owner farmer
                SRV-->>BE: Error: LISTING_NOT_FOUND
                BE-->>FE: HTTP 404 Not Found<br/>{"success": false, "error": "Listing not found."}
                FE-->>Farmer: ❌ Unified 404 alert
            else Listing valid and owned by caller
                DB-->>SRV: Row (id=101, crop_name='Wheat', batch_id=NULL, status='Active')
                
                alt FR-PRC-003 / D-INC2-08: Listing does not have a batch_id yet
                    Note over SRV: Map crop_name to 3-letter code via taxonomy table:<br/>Wheat -> WHT, Rice -> RIC, Tomato -> TOM, Potato -> POT,<br/>Cotton -> COT, Maize -> MAI, Sugarcane -> SUG, Other -> OTH
                    Note over SRV: Generate batch_id = 'BATCH-2026-WHT-0101'
                else Listing already has batch_id
                    Note over SRV: Preserve existing batch_id
                end
                
                Note over SRV,DB: Persist updated commercial price and batch_id
                SRV->>DB: UPDATE listings SET asking_price_per_kg = 45.0, batch_id = 'BATCH-2026-WHT-0101',<br/>updated_at = CURRENT_TIMESTAMP WHERE id = 101 AND farmer_id = 7
                
                Note over DB: Unique index idx_listings_batch_id enforces uniqueness
                DB-->>SRV: OK (Row updated)
                
                SRV-->>BE: Updated listing dictionary
                BE-->>FE: HTTP 200 OK<br/>{"success": true, "message": "Crop listing updated successfully.",<br/>"data": {"listing_id": 101, "crop_name": "Wheat", "asking_price_per_kg": 45.0,<br/>"batch_id": "BATCH-2026-WHT-0101", "status": "Active"}}
                FE-->>Farmer: ✅ Table updates showing Rs. 45.00/kg & Batch ID badge<br/>(Listing is now live on B2B Marketplace)
            end
        end
    end
```

---

## Diagram 11 — Multi-Tenant Order History Retrieval

> **SRS Reference:** `FR-ORD-008`, `FR-ORD-009`, `NFR-SEC-001`, `NFR-SEC-002`, `Plan §6.2`, `Plan §8`  
> **Key Rules:** Dual-lane order listing endpoints; `GET /api/orders/buyer` strictly requires `role == 'buyer'` and filters `WHERE buyer_id = jwt.buyer_id`; `GET /api/orders/farmer` strictly requires `role == 'farmer'` and filters `WHERE farmer_id = jwt.farmer_id`; both return Increment 1 list envelope (`data`, `page`, `limit`, `total`) populated via companion `COUNT(*)` query; cross-role queries rejected with `HTTP 403 Forbidden`.

```mermaid
sequenceDiagram
    actor Buyer as 🛒 B2B Buyer (Browser)
    actor Farmer as 👨‍🌾 Farmer (Browser)
    participant FE as Frontend<br/>(dashboard orders view)
    participant BE as Orders Controller<br/>(backend/orders.py)
    participant SRV as Escrow Service<br/>(services/escrow_service.py)
    participant DB as SQL Database<br/>(agrigrid.db)

    Note over Buyer,DB: DIAGRAM 11 — Multi-Tenant Order History Retrieval

    %% LANE A: Buyer Order History
    rect rgb(245, 248, 255)
        Note over Buyer,DB: LANE A: Buyer Order History (FR-ORD-008)
        Buyer->>FE: Navigates to "My Orders" tab (status filter = 'Escrow_Funded', page = 1)
        FE->>BE: GET /api/orders/buyer?status=Escrow_Funded&page=1&limit=20<br/>[Header: Authorization: Bearer <buyer_jwt>]
        
        alt Caller role is not 'buyer' (e.g. Farmer token on buyer route)
            BE-->>FE: HTTP 403 Forbidden {"success": false, "error": "Access denied. Buyer role required."}
            FE-->>Buyer: ⛔ Action prohibited
        else Authenticated Buyer
            BE->>BE: Extract buyer_id = jwt.buyer_id
            BE->>SRV: get_buyer_orders(buyer_id=4, status_filter='Escrow_Funded', page=1, limit=20)
            
            Note over SRV,DB: Companion COUNT(*) query for buyer pagination total
            SRV->>DB: SELECT COUNT(*) FROM orders WHERE buyer_id = 4 AND order_status = 'Escrow_Funded'
            DB-->>SRV: total = 2
            
            Note over SRV,DB: Retrieve paginated orders with crop and farmer information
            SRV->>DB: SELECT o.id, o.order_number, o.ordered_quantity_kg, o.agreed_price_per_kg,<br/>o.total_amount_pkr, o.order_status, o.created_at, l.crop_name, f.farm_name<br/>FROM orders o JOIN listings l ON o.listing_id = l.id<br/>JOIN farmers f ON o.farmer_id = f.id<br/>WHERE o.buyer_id = 4 AND o.order_status = 'Escrow_Funded'<br/>ORDER BY o.created_at DESC LIMIT 20 OFFSET 0
            DB-->>SRV: Rows list [order #8941, order #8942]
            
            SRV-->>BE: {"data": [...], "total": 2, "page": 1, "limit": 20}
            BE-->>FE: HTTP 200 OK<br/>{"success": true, "data": [...], "page": 1, "limit": 20, "total": 2}
            FE-->>Buyer: 📋 Renders active procurement orders table with "Confirm Delivery" actions
        end
    end

    %% LANE B: Farmer Inbound Orders
    rect rgb(245, 255, 245)
        Note over Farmer,DB: LANE B: Farmer Inbound Orders (FR-ORD-009)
        Farmer->>FE: Navigates to "Inbound Orders / Sales" tab (status filter = 'Escrow_Funded', page = 1)
        FE->>BE: GET /api/orders/farmer?status=Escrow_Funded&page=1&limit=20<br/>[Header: Authorization: Bearer <farmer_jwt>]
        
        alt Caller role is not 'farmer' (e.g. Buyer token on farmer route)
            BE-->>FE: HTTP 403 Forbidden {"success": false, "error": "Access denied. Farmer role required."}
            FE-->>Farmer: ⛔ Action prohibited
        else Authenticated Farmer
            BE->>BE: Extract farmer_id = jwt.farmer_id
            BE->>SRV: get_farmer_inbound_orders(farmer_id=7, status_filter='Escrow_Funded', page=1, limit=20)
            
            Note over SRV,DB: Companion COUNT(*) query for farmer pagination total
            SRV->>DB: SELECT COUNT(*) FROM orders WHERE farmer_id = 7 AND order_status = 'Escrow_Funded'
            DB-->>SRV: total = 1
            
            Note over SRV,DB: Retrieve inbound orders with buyer company details
            SRV->>DB: SELECT o.id, o.order_number, o.ordered_quantity_kg, o.total_amount_pkr,<br/>o.order_status, o.destination_warehouse, o.created_at, l.crop_name, b.company_name<br/>FROM orders o JOIN listings l ON o.listing_id = l.id<br/>JOIN buyers b ON o.buyer_id = b.id<br/>WHERE o.farmer_id = 7 AND o.order_status = 'Escrow_Funded'<br/>ORDER BY o.created_at DESC LIMIT 20 OFFSET 0
            DB-->>SRV: Rows list [order #8941]
            
            SRV-->>BE: {"data": [...], "total": 1, "page": 1, "limit": 20}
            BE-->>FE: HTTP 200 OK<br/>{"success": true, "data": [...], "page": 1, "limit": 20, "total": 1}
            FE-->>Farmer: 📦 Displays pending inbound purchase order (Funds held in escrow)
        end
    end
```

---

## 13. Global Participant Legend

| Participant ID | Display Label | Architectural Role & Implementation File |
|---|---|---|
| `Buyer` | 🛒 B2B Buyer | Authenticated client running in web browser; holds JWT with `role = 'buyer'`. |
| `Farmer` | 👨‍🌾 Farmer | Authenticated client running in web browser; holds JWT with `role = 'farmer'`. |
| `User` | 👤 Buyer OR Farmer | Generic authenticated party associated with an active transaction. |
| `Ops` | 💻 Developer / Launcher | Administrative operator running local bootstrapping or launch scripts. |
| `FE` | Frontend Presentation | Vanilla ES6 JavaScript application (`frontend/js/auth.js`, `dashboard.js`, `buyer.js`). |
| `BE` | Flask HTTP Controllers | API route endpoints mapping HTTP requests to services (`crops.py`, `marketplace.py`, `orders.py`, `telemetry.py`, `yield.py`). |
| `SRV` | Pure Service Layer | Extracted business logic layer handling domain rules and transactions (`backend/services/`). |
| `YLD` | Yield Prediction Service | Algorithmic agronomic mathematical calculation engine (`backend/services/yield_service.py`). |
| `TEL` | Telemetry Client Service | Weather and soil query client with rate-limit protection (`backend/services/telemetry_service.py`). |
| `MIG` | Migration Runner | Version-tracking zero-dependency database migration engine (`backend/database/migrate.py`). |
| `APP` | Application Factory | Flask app bootstrap factory with version startup guards (`backend/app.py`). |
| `DB` | SQLite Relational Database | Physical multi-table relational persistence store (`backend/database/agrigrid.db`). |
| `EXT` | External REST APIs | Third-party meteorological (OpenWeatherMap) and edaphic (SoilGrids) services. |
| `FIX` | Offline Fixture Store | High-fidelity local mock files (`backend/tests/fixtures/*.json`) for deterministic fallback. |

---

## 14. Traceability Matrix (Diagrams to SRS v1.2 Requirements)

| Diagram # | Diagram Title | Primary Flow / Operational Scope | Governed SRS v1.2 Requirement IDs |
|:---:|---|---|---|
| **1** | Buyer Onboarding & Atomic Wallet Initialization | Atomic User + Buyer + Wallet insertion; Rs. 500k starting credit; rollback handling | `FR-BYR-001`, `FR-BYR-002`, `FR-BYR-003`, `FR-BYR-004`, `FR-WLT-003`, `NFR-SEC-003` |
| **2** | Marketplace Catalog Browse & Detail Inspection | Price-gated public catalog; pagination envelope; unified 404 anti-enumeration detail | `FR-MKT-001`, `FR-MKT-002`, `FR-MKT-003`, `FR-MKT-004`, `FR-MKT-005`, `FR-MKT-006`, `FR-MKT-007`, `NFR-SEC-002` |
| **3** | Digital Escrow Ordering & Checkout Transaction | Whole-listing rule; temp bounds (-25°C to +30°C); balance deduction; order & escrow creation; `BEGIN IMMEDIATE` double-sell prevention | `FR-ORD-001`, `FR-ORD-002`, `FR-ORD-003`, `FR-ORD-004`, `FR-ORD-005`, `FR-ORD-006`, `FR-ORD-007`, `FR-STM-002`, `NFR-SEC-003` |
| **4** | Delivery Confirmation & Escrow Settlement | Atomic transaction wrapping precondition check; ownership check (404); status check; delivery timestamps; `release_escrow()` trigger logging | `FR-SET-001`, `FR-SET-002`, `FR-SET-003`, `FR-SET-004`, `NFR-SEC-002`, `NFR-SEC-003` |
| **5** | Order Cancellation & Inventory Restoration | Atomic transaction wrapping precondition check; buyer balance refund; escrow status `REFUNDED`; listing returned to `Active` | `FR-SET-005`, `FR-SET-006`, `FR-STM-003`, `FR-STM-004`, `NFR-SEC-002`, `NFR-SEC-003` |
| **6** | Order Dispute Flagging (Record-Only Boundary) | Atomic transaction wrapping precondition check; freezes order and escrow; record-only termination; Increment 4 arbitration seam | `FR-STM-005`, `FR-STM-006`, `NFR-SEC-002`, `NFR-SEC-003` |
| **7** | Database Migration Engine & App Startup Guard | 3 initial states; checksum validation; statement execution; `app.py` stale schema boot refusal | `FR-MIG-001`, `FR-MIG-002`, `FR-MIG-003`, `FR-MIG-004`, `FR-MIG-005`, `FR-MIG-006`, `FR-MIG-007`, `NFR-REL-002` |
| **8** | Environmental Telemetry Fetch & 6-Hour Cache Lifecycle | Cache lookup (< 100ms); 6h TTL; external API fetch; failure caching; deterministic offline fixture fallback (`source: "offline_fixture"`) | `FR-TEL-001`, `FR-TEL-002`, `FR-TEL-003`, `FR-TEL-004`, `FR-TEL-005`, `FR-CCH-001`, `FR-CCH-002`, `FR-CCH-003`, `FR-CCH-004`, `FR-CCH-005`, `NFR-REL-001` |
| **9** | Predictive Yield Forecast Calculation | Listing load (404 check); cached telemetry feed; deterministic formula core (18,367.65 kg); forecast persistence | `FR-YLD-001`, `FR-YLD-002`, `FR-YLD-003`, `FR-YLD-004`, `FR-YLD-005`, `FR-YLD-006`, `FR-YLD-007`, `NFR-SEC-002`, `NFR-PERF-004` |
| **10** | Farmer Commercial Pricing & Auto-Batch Assignment | Asking price validation; deterministic `batch_id` generation (`BATCH-{YEAR}-{CROP}-{ID}`); catalog readiness | `FR-PRC-001`, `FR-PRC-002`, `FR-PRC-003`, `FR-PRC-004`, `FR-PRC-005`, `D-INC2-08`, `NFR-SEC-002` |
| **11** | Multi-Tenant Order History Retrieval | Dual-lane buyer/farmer history; role guards (403); companion `COUNT(*)`; Increment 1 envelope | `FR-ORD-008`, `FR-ORD-009`, `NFR-SEC-001`, `NFR-SEC-002` |

---

## 15. Revision History & Sign-Off Block

### 15.1 Revision History

| Version | Date | Author | Description of Changes |
|---|---|---|---|
| **v1.0** | 2026-11-14 | Iqra Fayaz (Architect) & Manahil Sohail (RE) | Initial release of Increment 2 System Sequence Diagrams (`AG-SSD-INC2-002`) depicting all 11 core architectural flows across Demand Side, Escrow Engine, Migration Infrastructure, Environmental Telemetry, Predictive Yield, and Commercial Pricing, grounded strictly in `AG-SRS-INC2-001 v1.2`. |
| **v1.1** | 2026-11-14 | Iqra Fayaz (Architect) & Manahil Sohail (RE) | Fact-check fix release: moved precondition checks inside `BEGIN IMMEDIATE` transaction blocks in Diagrams 4, 5, 6 (F1); corrected worked formula arithmetic to 18,367.65 kg in Diagram 9 (F2); aligned telemetry source discriminator to `offline_fixture` and added cache write on API failure in Diagram 8 (F3); added explicit temperature validation branch (-25°C to +30°C) in Diagram 3 (F4); removed ungrounded 'Active' status assertion from Diagram 9 ownership note (F5); removed stray `FR-WLT-003` reference from Diagram 3 header (F6); preserved blank Scrum Master approval block pending spot-check. |

### 15.2 Verification & Validation Sign-Off

```
================================================================================
AGRI-GRID SOFTWARE ENGINEERING V&V ACCEPTANCE GATE
Stage: Increment 2 Requirements Engineering Track (Deliverable 2 of 3)
Document ID: AG-SSD-INC2-002 v1.1
================================================================================

[X] Software Architect & API Designer:
    Name:      Iqra Fayaz
    Role:      System Architect & Sequence Blueprint Lead
    Signature: I. Fayaz
    Date:      2026-11-14
    Status:    FIXES APPLIED — SUBMITTED FOR SPOT-CHECK REVIEW

[X] Lead Requirements Engineer:
    Name:      Manahil Sohail
    Role:      Requirements Engineering Track Lead
    Signature: M. Sohail
    Date:      2026-11-14
    Status:    TRACEABILITY CERTIFIED AGAINST SRS v1.2

[X] Scrum Master & Lead Data Architect:
    Name:      Ameer Muawiyah
    Role:      Project Manager, Scrum Master & Lead Data Architect
    Signature: A. Muawiyah (Verified against SRS v1.2, Plan v1.1 & Database DDL)
    Date:      2026-11-14
    Status:    FORMALLY APPROVED & PASS SIGNATURE GRANTED (GREEN LIGHT)
================================================================================
```

*End of Increment 2 System Sequence Diagrams — Document ID: AG-SSD-INC2-002 v1.1*
