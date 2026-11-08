# Agri-Grid Standing Frontend Change Checklist

> **Mandatory Quality Gate:** This checklist must be executed and verified green for **every** frontend change, pull request, and refactoring effort across Agri-Grid, not just reskins. Any failing item blocks merging.

---

## 1. Automated Regression Gates

- [ ] **ID Cross-Check (Automated by `TC-F4` in `test_frontend_contract.py`)**
  - Every JavaScript element lookup (`document.getElementById(...)`) must resolve to a valid `id` attribute in the corresponding HTML document.
  - Dynamic IDs created at runtime must be explicitly documented and allowlisted in `PAGE_SPECS` with technical justification.

- [ ] **Class Cross-Check (Automated by `TC-F3` in `test_frontend_contract.py`)**
  - Zero undefined CSS classes allowed across `index.html`, `dashboard.html`, `auth.js`, and `dashboard.js`.
  - All classes used in markup or dynamic DOM mutations must exist in `auth.css` or `dashboard.css`.
  - No framework utility classes (e.g., Tailwind, Bootstrap) permitted anywhere in HTML or JS.

- [ ] **Enum & Taxonomy Synchronization (Automated by `TC-F1` & `TC-F2`)**
  - Every `<select>` dropdown option set must strictly match the backend domain model and database constraints:
    - `select#modalCropName` == `crops.py:VALID_CROP_NAMES` (exactly 8 whitelisted crops).
    - `select#statusFilter` == Approved UI subset (`ALL`, `Active`, `Sold`), where every active status is a member of `crops.py:VALID_STATUSES`.

- [ ] **SRS Copy Precision (Automated by `TC-F5` in `test_frontend_contract.py`)**
  - Specification-pinned strings must match byte-for-byte:
    - Empty state: `"You have no active crops. Click 'Add New Crop' to get started."`
    - Non-farmer placeholder: `"Dashboard under construction — available in a future increment."`

- [ ] **Test Suites Green**
  - `python backend/test_auth.py` (Must pass 17/17)
  - `python backend/test_crops_api.py` (Must pass 23/23)
  - `python backend/test_frontend_contract.py` (Must pass 5/5)
  - `node --check frontend/js/auth.js` & `node --check frontend/js/dashboard.js` (Zero syntax errors)

---

## 2. Design & Architectural Invariants

- [ ] **Tokens-Only Color Architecture**
  - No raw hex (`#...`) or `rgb()` / `hsl()` color literals in CSS rules outside `:root` design token blocks.
  - Every color reference must resolve through CSS Custom Properties (`var(--ink)`, `var(--surface)`, `var(--clay)`, etc.).

- [ ] **Agri-Grid Design-Law Compliance**
  - No marquee or ticker text animations.
  - No decorative rainbow or non-semantic top stripe bands.
  - No rotated stamps, skewed badges, or floating non-standard tags.
  - No sideways-scrolling horizontal cards or unconstrained overflow rows.

- [ ] **Behavior Freeze Guarantee**
  - JavaScript diffs must be reviewed line-by-line.
  - Presentation and CSS styling adjustments must remain strictly decoupled from business logic and state machine transitions.
  - Zero changes to API request contracts, payload structures, authentication headers, or response parsing without written specification approval.
  - A reskin or UI refresh that alters application behavior has failed, even if visual rendering appears correct.

- [ ] **Strict Responsive Boundaries**
  - Zero horizontal page scroll at all standard viewports:
    - Mobile: `390px` (portrait iPhone standard) — `document.documentElement.scrollWidth <= document.documentElement.clientWidth`.
    - Tablet / Desktop: `1024px` and `1280px` — `document.documentElement.scrollWidth <= document.documentElement.clientWidth`.
  - Wide tables must be wrapped in `.table-scroll` and scroll strictly within their container boundaries.

---

## 3. Pull Request Report Requirement

Every frontend pull request must include an itemized verification log following the standard:

```
[PASS|FAIL] <ITEM-ID>: <Description>
            Evidence: <Execution output, grep result, test counter, or screenshot reference>
```
