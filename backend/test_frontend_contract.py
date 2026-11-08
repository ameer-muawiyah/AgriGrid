"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    test_frontend_contract.py
Module:  Frontend-Backend Contract & Invariant Self-Verification
Version: 1.0  (Increment 1 - Foundation & Farmer Dashboard)
Source:  AG-API-INC1-003 & 1_Farmer_Dashboard_SRS.md

Purpose
-------
Standalone, stdlib-only contract test suite (no server, no network).
Fails whenever the frontend drifts from the backend contract or architectural
specifications. Verifies crop taxonomy lock, status filter lock, CSS class
continuity, DOM element ID cross-bindings, and pinned SRS copy.

Test Cases
----------
  TC-F1  Crop taxonomy lock (select#modalCropName matches crops.py VALID_CROP_NAMES)
  TC-F2  Status filter lock (select#statusFilter approved UI subset & VALID_STATUSES member)
  TC-F3  Class cross-check (used classes in HTML/JS <= defined classes in CSS)
  TC-F4  ID cross-check (getElementById calls match id attributes in matching HTML)
  TC-F5  Pinned SRS copy (byte-for-byte exact copy checks)

Usage
-----
  python backend/test_frontend_contract.py        (from project root)
  python test_frontend_contract.py                (from backend/ directory)
"""

import ast
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path resolution: repo root resolved relative to this test file (backend/ -> ..)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
CROPS_PY_PATH = SCRIPT_DIR / "crops.py"

RESULTS = []


# ---------------------------------------------------------------------------
# Test Reporting Helpers (Matches test_auth.py / test_crops_api.py style)
# ---------------------------------------------------------------------------
def _pass(tc: str, desc: str, detail: str = "") -> None:
    status = f"[PASS] {tc}: {desc}"
    if detail:
        status += f"\n       {detail}"
    print(status)
    RESULTS.append({"tc": tc, "status": "PASS", "desc": desc})


def _fail(tc: str, desc: str, detail: str = "") -> None:
    status = f"[FAIL] {tc}: {desc}"
    if detail:
        status += f"\n       {detail}"
    print(status)
    RESULTS.append({"tc": tc, "status": "FAIL", "desc": desc})


# ---------------------------------------------------------------------------
# AST Extraction for Backend Whitelists (Hard rule: never re-type whitelists)
# ---------------------------------------------------------------------------
def _extract_elements_from_ast(node: ast.AST) -> set[str]:
    """Helper to extract string constants from an AST sequence or call."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id in ("frozenset", "set") and node.args:
            return _extract_elements_from_ast(node.args[0])
    if isinstance(node, (ast.List, ast.Set, ast.Tuple)):
        return {
            elt.value for elt in node.elts
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        }
    return set()


def load_backend_whitelists(crops_path: Path) -> tuple[set[str], set[str]]:
    """Parse VALID_CROP_NAMES and VALID_STATUSES literals from backend/crops.py via AST."""
    if not crops_path.exists():
        raise FileNotFoundError(f"Cannot find backend/crops.py at {crops_path}")

    tree = ast.parse(crops_path.read_text(encoding="utf-8"))
    crop_names = None
    statuses = None

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "VALID_CROP_NAMES":
                        crop_names = _extract_elements_from_ast(node.value)
                    elif target.id == "VALID_STATUSES":
                        statuses = _extract_elements_from_ast(node.value)

    if crop_names is None or statuses is None:
        raise ValueError("Failed to extract VALID_CROP_NAMES and VALID_STATUSES from backend/crops.py AST")

    return crop_names, statuses


# ---------------------------------------------------------------------------
# HTML, JS & CSS Class Parsing Helpers
# ---------------------------------------------------------------------------
def _extract_classes_from_html(text: str) -> set[str]:
    """Extract class names from HTML class="..." or class='...' attributes."""
    classes = set()
    for m in re.finditer(r'class=["\']([^"\']+)["\']', text):
        for c in m.group(1).split():
            classes.add(c)
    return classes


def _extract_classes_from_js(text: str) -> set[str]:
    """Extract class names used in JavaScript files:
    - class="..." or class='...' in embedded HTML/template strings
    - className template strings and assignments
    - classList.add/toggle/remove arguments
    """
    classes = set()

    # 1. Embedded HTML string class attributes (e.g. `<span class="badge ${color}">`)
    for m in re.finditer(r'class=["\']([^"\']+)["\']', text):
        for token in m.group(1).split():
            clean = re.sub(r'\$\{[^}]*\}', '', token).strip()
            if clean and re.match(r'^[a-zA-Z_-][a-zA-Z0-9_-]*$', clean):
                classes.add(clean)

    # 2. className assignments and template strings (e.g. `alertBox.className = `${alertClass} mb-5`;`)
    for m in re.finditer(r'className\s*=\s*([^;]+);', text):
        expr = m.group(1)
        for s in re.finditer(r'["\'`]([^"\'`]+)["\'`]', expr):
            for token in s.group(1).split():
                clean = re.sub(r'\$\{[^}]*\}', '', token).strip()
                if clean and re.match(r'^[a-zA-Z_-][a-zA-Z0-9_-]*$', clean):
                    classes.add(clean)

    # 3. classList.add, classList.toggle, classList.remove arguments
    for m in re.finditer(r'classList\.(?:add|toggle|remove)\s*\(([^)]+)\)', text):
        args_str = m.group(1)
        for str_match in re.finditer(r'["\']([a-zA-Z_-][a-zA-Z0-9_-]*)["\']', args_str):
            classes.add(str_match.group(1))

    return classes


def _extract_classes_from_css(text: str) -> set[str]:
    """Extract class names defined in CSS rules.
    Strips comments and quoted strings to avoid false positives.
    """
    # Strip comments
    clean = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # Strip quoted strings (e.g. content: "...", url("..."))
    clean = re.sub(r'"[^"]*"', '', clean)
    clean = re.sub(r"'[^']*'", '', clean)

    classes = set()
    for m in re.finditer(r'\.([a-zA-Z_-][a-zA-Z0-9_-]*)', clean):
        classes.add(m.group(1))
    return classes


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def tc_f1_crop_taxonomy_lock(dashboard_html_path: Path, valid_crop_names: set[str]) -> None:
    """TC-F1: Crop taxonomy lock
    Parse the <option value="..."> values inside <select id="modalCropName"> in frontend/dashboard.html.
    Assert the set equals VALID_CROP_NAMES.
    """
    content = dashboard_html_path.read_text(encoding="utf-8")
    m = re.search(r'<select[^>]*id=["\']modalCropName["\'][^>]*>(.*?)</select>', content, re.DOTALL)
    if not m:
        _fail("TC-F1", "Crop taxonomy lock", "Could not locate <select id=\"modalCropName\"> in dashboard.html")
        return

    select_body = m.group(1)
    raw_options = re.findall(r'<option[^>]*value=["\']([^"\']*)["\']', select_body)
    # Filter empty placeholder value=""
    crop_options = {val for val in raw_options if val}

    if crop_options == valid_crop_names:
        _pass("TC-F1", "Crop taxonomy lock",
              f"Frontend options exactly match backend VALID_CROP_NAMES ({len(crop_options)} crops)")
    else:
        unexpected = crop_options - valid_crop_names
        missing = valid_crop_names - crop_options
        detail_parts = []
        if unexpected:
            detail_parts.append(f"Unexpected options in frontend: {sorted(unexpected)}")
        if missing:
            detail_parts.append(f"Missing crops in frontend: {sorted(missing)}")
        _fail("TC-F1", "Crop taxonomy lock", " | ".join(detail_parts))


def tc_f2_status_filter_lock(dashboard_html_path: Path, valid_statuses: set[str]) -> None:
    """TC-F2: Status filter lock
    Parse option values inside <select id="statusFilter">.
    Assert the set equals {"ALL", "Active", "Sold"} — the approved UI subset —
    and that every non-ALL value is a member of VALID_STATUSES.
    """
    # Note: The full backend status set is larger (Increment 2); widening this UI set
    # is a deliberate, reviewed change, and this test is where it gets updated.
    APPROVED_UI_STATUSES = {"ALL", "Active", "Sold"}

    content = dashboard_html_path.read_text(encoding="utf-8")
    m = re.search(r'<select[^>]*id=["\']statusFilter["\'][^>]*>(.*?)</select>', content, re.DOTALL)
    if not m:
        _fail("TC-F2", "Status filter lock", "Could not locate <select id=\"statusFilter\"> in dashboard.html")
        return

    select_body = m.group(1)
    status_options = set(re.findall(r'<option[^>]*value=["\']([^"\']*)["\']', select_body))

    if status_options != APPROVED_UI_STATUSES:
        _fail("TC-F2", "Status filter lock",
              f"Options {sorted(status_options)} != approved UI subset {sorted(APPROVED_UI_STATUSES)}")
        return

    invalid_statuses = {s for s in status_options if s != "ALL" and s not in valid_statuses}
    if invalid_statuses:
        _fail("TC-F2", "Status filter lock",
              f"Non-ALL statuses not in backend VALID_STATUSES: {sorted(invalid_statuses)}")
        return

    _pass("TC-F2", "Status filter lock",
          f"UI set {sorted(status_options)} matches approved subset; all non-ALL statuses valid in backend")


def tc_f3_class_cross_check(frontend_dir: Path) -> None:
    """TC-F3: Class cross-check
    Collect every class name used in frontend/index.html, frontend/dashboard.html,
    frontend/js/auth.js, and frontend/js/dashboard.js.
    Collect every class defined in frontend/css/auth.css and frontend/css/dashboard.css.
    Assert used <= defined, and on failure list the undefined class names.
    """
    used = set()
    for html_file in [frontend_dir / "index.html", frontend_dir / "dashboard.html"]:
        used.update(_extract_classes_from_html(html_file.read_text(encoding="utf-8")))

    for js_file in [frontend_dir / "js" / "auth.js", frontend_dir / "js" / "dashboard.js"]:
        used.update(_extract_classes_from_js(js_file.read_text(encoding="utf-8")))

    defined = set()
    for css_file in [frontend_dir / "css" / "auth.css", frontend_dir / "css" / "dashboard.css"]:
        defined.update(_extract_classes_from_css(css_file.read_text(encoding="utf-8")))

    undefined = used - defined
    if not undefined:
        _pass("TC-F3", "Class cross-check",
              f"All {len(used)} used classes are defined in stylesheets")
    else:
        _fail("TC-F3", "Class cross-check",
              f"Undefined classes ({len(undefined)}): {sorted(undefined)}")


def tc_f4_id_cross_check(frontend_dir: Path) -> None:
    """TC-F4: ID cross-check
    For each page, collect the getElementById('...') targets in its JS file
    and assert each exists as an id="..." in the matching HTML file.
    """
    # Page specifications and documented allowlists:
    PAGE_SPECS = [
        {
            "html": frontend_dir / "index.html",
            "js": frontend_dir / "js" / "auth.js",
            # Documented Exception:
            # switchLinkToLogin for index.html is created dynamically by the auth.js tab logic;
            # any new dynamic ID must be added to this allowlist with a justification comment,
            # which makes the exception visible in review.
            "allowlist": {"switchLinkToLogin"},
        },
        {
            "html": frontend_dir / "dashboard.html",
            "js": frontend_dir / "js" / "dashboard.js",
            "allowlist": set(),
        },
    ]

    missing_by_page = {}
    for spec in PAGE_SPECS:
        html_ids = set(re.findall(r'id=["\']([^"\']+)["\']', spec["html"].read_text(encoding="utf-8")))
        js_ids = set(re.findall(r'getElementById\(["\']([^"\']+)["\']\)', spec["js"].read_text(encoding="utf-8")))

        missing = (js_ids - html_ids) - spec["allowlist"]
        if missing:
            missing_by_page[spec["html"].name] = missing

    if not missing_by_page:
        _pass("TC-F4", "ID cross-check",
              "All getElementById targets exist in corresponding HTML markup (dynamic IDs accounted for)")
    else:
        detail = "; ".join(f"{page}: {sorted(ids)}" for page, ids in missing_by_page.items())
        _fail("TC-F4", "ID cross-check", f"Missing IDs in HTML markup: {detail}")


def tc_f5_pinned_srs_copy(frontend_dir: Path) -> None:
    """TC-F5: Pinned SRS copy
    Assert these strings appear byte-for-byte:
    In frontend/dashboard.html: You have no active crops. Click 'Add New Crop' to get started.
    In frontend/js/dashboard.js: Dashboard under construction — available in a future increment.
    """
    EXPECTED_HTML_STRING = "You have no active crops. Click 'Add New Crop' to get started."
    EXPECTED_JS_STRING = "Dashboard under construction \u2014 available in a future increment."

    dash_html_content = (frontend_dir / "dashboard.html").read_text(encoding="utf-8")
    dash_js_content = (frontend_dir / "js" / "dashboard.js").read_text(encoding="utf-8")

    html_match = EXPECTED_HTML_STRING in dash_html_content
    js_match = EXPECTED_JS_STRING in dash_js_content

    if html_match and js_match:
        _pass("TC-F5", "Pinned SRS copy", "Both SRS copy strings matched byte-for-byte")
    else:
        failures = []
        if not html_match:
            failures.append(f"Missing in dashboard.html: '{EXPECTED_HTML_STRING}'")
        if not js_match:
            failures.append(f"Missing in dashboard.js: '{EXPECTED_JS_STRING}'")
        _fail("TC-F5", "Pinned SRS copy", " | ".join(failures))


# ---------------------------------------------------------------------------
# Main Execution Runner
# ---------------------------------------------------------------------------
def main() -> None:
    print("=" * 65)
    print("  AGRI-GRID  Frontend-Backend Contract Verification  *  Run 4")
    print("=" * 65)
    print(f"  Target Root: {REPO_ROOT}")
    print(f"  Frontend:    {FRONTEND_DIR}")
    print()

    # Load whitelists dynamically from crops.py
    try:
        valid_crop_names, valid_statuses = load_backend_whitelists(CROPS_PY_PATH)
        print(f"[INIT] Loaded {len(valid_crop_names)} crops & {len(valid_statuses)} statuses from backend/crops.py AST")
        print()
    except Exception as exc:
        print(f"[FATAL] Failed to load backend whitelists: {exc}")
        sys.exit(1)

    dashboard_html_path = FRONTEND_DIR / "dashboard.html"

    tests = [
        ("TC-F1", lambda: tc_f1_crop_taxonomy_lock(dashboard_html_path, valid_crop_names)),
        ("TC-F2", lambda: tc_f2_status_filter_lock(dashboard_html_path, valid_statuses)),
        ("TC-F3", lambda: tc_f3_class_cross_check(FRONTEND_DIR)),
        ("TC-F4", lambda: tc_f4_id_cross_check(FRONTEND_DIR)),
        ("TC-F5", lambda: tc_f5_pinned_srs_copy(FRONTEND_DIR)),
    ]

    for tc_code, test_fn in tests:
        try:
            test_fn()
        except Exception as exc:
            _fail(tc_code, "Unexpected exception", str(exc))

    # Summary report
    passed = sum(1 for r in RESULTS if r["status"] == "PASS")
    failed = sum(1 for r in RESULTS if r["status"] == "FAIL")
    total = len(RESULTS)

    print()
    print("=" * 65)
    print(f"  RESULTS: {passed}/{total} passed  |  {failed} failed")
    print("=" * 65)

    if failed:
        print("\n  Failed tests:")
        for r in RESULTS:
            if r["status"] == "FAIL":
                print(f"    - {r['tc']}: {r['desc']}")
        print()
        sys.exit(1)
    else:
        print("\n  All tests passed. Frontend conforms to Backend contracts.")
        print()
        sys.exit(0)


if __name__ == "__main__":
    main()
