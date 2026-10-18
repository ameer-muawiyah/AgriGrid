"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    app.py
Module:  Flask Application Factory & Authentication Endpoints
Version: 1.1  (Increment 1 - Run 3: Crop CRUD Blueprint wired)
Source:  AG-API-INC1-003 v1.0  Section 3 & 4 | AG-SRS-INC1-001 v1.1

Endpoints (Run 2)
-----------------
  POST /api/auth/register   — Atomic user + farmer-profile creation
  POST /api/auth/login      — Credential verification + JWT issuance
  POST /api/auth/logout     — Session termination acknowledgement
  GET  /api/auth/me         — Protected JWT/RBAC smoke-test route

Blueprints registered (Run 3)
------------------------------
  crops_bp  — /api/crops  (POST, GET, GET/<id>, PUT/<id>, DELETE/<id>)

Run the server
--------------
  python backend/app.py              (development mode, from project root)
  python app.py                      (from backend/ directory)
"""

import os
import sqlite3

from flask import Flask, g, jsonify, request
from flask_cors import CORS

from auth import (
    hash_password,
    verify_password,
    validate_password_complexity,
    generate_token,
    token_required,
    role_required,
    VALID_ROLES,
)

# ---------------------------------------------------------------------------
# Path resolution — runnable from project root OR backend/ directory
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "database", "agrigrid.db")


# ---------------------------------------------------------------------------
# Application Factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    """
    Create and configure the Flask application instance.
    Using the factory pattern ensures the app is testable and extensible
    for future Blueprints (crops, logistics, etc.).
    """
    app = Flask(__name__)

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------
    # SECURITY: In production, load JWT_SECRET_KEY from an environment
    # variable or secrets manager — never hard-code in source.
    app.config["JWT_SECRET_KEY"] = os.environ.get(
        "AGRIGRID_JWT_SECRET",
        "agrigrid-dev-secret-CHANGE-IN-PRODUCTION-2026",
    )
    try:
        app.config["JWT_EXPIRY_MINUTES"] = int(os.environ.get("JWT_EXPIRY_MINUTES", 30))
    except (TypeError, ValueError):
        print("[WARN] Invalid JWT_EXPIRY_MINUTES; falling back to 30 minutes.")
        app.config["JWT_EXPIRY_MINUTES"] = 30
    app.config["DB_PATH"] = DB_PATH

    # ------------------------------------------------------------------
    # CORS (NFR-SEC-007)
    # Restricts API access to the local dev frontend origin.
    # The origins list should be tightened to the deployed frontend URL
    # before production release.
    # ------------------------------------------------------------------
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5500",   # VS Code Live Server default
                "http://127.0.0.1:5500",
                "http://localhost:3000",   # Alternative dev server
                "http://127.0.0.1:3000",
            ],
            "supports_credentials": True,
        }
    })

    # ------------------------------------------------------------------
    # Database connection helpers
    # ------------------------------------------------------------------

    def get_db() -> sqlite3.Connection:
        """
        Return a per-request SQLite connection stored in Flask's g object.

        Critical (pre-run agreement point 1):
          PRAGMA foreign_keys = ON is executed on EVERY new connection.
          SQLite disables FK enforcement by default; omitting this would
          silently allow orphaned listings and broken farmer references.

        Row factory:
          sqlite3.Row enables column access by name (dict-like), producing
          clean dictionary output for JSON serialisation without manual
          column-index mapping.
        """
        if "db" not in g:
            g.db = sqlite3.connect(
                current_app.config["DB_PATH"],
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            g.db.row_factory = sqlite3.Row
            # ── CRITICAL: enforce referential integrity ──────────────────
            g.db.execute("PRAGMA foreign_keys = ON;")
            # ── WAL mode for better concurrent read performance ──────────
            g.db.execute("PRAGMA journal_mode = WAL;")
        return g.db

    def close_db(exception=None) -> None:
        """Teardown: close DB connection at end of request lifecycle."""
        db = g.pop("db", None)
        if db is not None:
            db.close()

    app.teardown_appcontext(close_db)

    # Make get_db accessible inside route handlers via app context
    app.get_db = get_db  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Register authentication routes
    # ------------------------------------------------------------------
    _register_auth_routes(app, get_db)

    # ------------------------------------------------------------------
    # Register Blueprints (Run 3+)
    # ------------------------------------------------------------------
    from crops import crops_bp          # noqa: E402 (import inside factory)
    app.register_blueprint(crops_bp)

    return app


# ---------------------------------------------------------------------------
# Authentication Route Registration
# ---------------------------------------------------------------------------

def _register_auth_routes(app: Flask, get_db) -> None:
    """Attach all /api/auth/* endpoints to the app instance."""

    # ------------------------------------------------------------------ #
    #  POST /api/auth/register                                            #
    #  AG-API-INC1-003 §3.1                                              #
    # ------------------------------------------------------------------ #
    @app.route("/api/auth/register", methods=["POST"])
    def register():
        """
        Atomic user onboarding.

        Flow (pre-run agreement point 3 — mirrors sequence diagram Flow 1A):
          BEGIN TRANSACTION
            1. Validate payload fields & password complexity.
            2. Check for duplicate username (HTTP 409 if found).
            3. INSERT INTO users (username, password_hash, role, email).
            4. IF role == 'farmer':
                 INSERT INTO farmers (user_id, farm_name).
          COMMIT
          (Any exception triggers ROLLBACK — no orphan records possible)
        """
        db = get_db()

        # -- 1. Parse & validate payload --
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                "success": False,
                "error": "Invalid request format.",
            }), 400

        username  = (data.get("username") or "").strip()
        password  = data.get("password") or ""
        role      = (data.get("role") or "").strip().lower()
        email     = (data.get("email") or "").strip() or None
        farm_name = (data.get("farm_name") or "").strip() or None

        # Required field presence check
        if not username or not password or not role:
            return jsonify({
                "success": False,
                "error": "All fields are required: username, password, role.",
            }), 400

        # Username length (schema CHECK mirrors this)
        if len(username) < 3 or len(username) > 50:
            return jsonify({
                "success": False,
                "error": "Username must be between 3 and 50 characters.",
            }), 400

        # RBAC role validation
        if role not in VALID_ROLES:
            return jsonify({
                "success": False,
                "error": "Invalid role. Must be one of: farmer, buyer, transporter, agronomist, compliance_officer.",
            }), 400

        # Farmer-specific: farm_name is mandatory
        if role == "farmer" and not farm_name:
            return jsonify({
                "success": False,
                "error": "Farm name is required when registering as a farmer.",
            }), 400

        # Password complexity (NFR-SEC-008)
        is_valid, complexity_error = validate_password_complexity(password)
        if not is_valid:
            return jsonify({"success": False, "error": complexity_error}), 400

        # -- 2. Duplicate username check --
        existing = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            return jsonify({
                "success": False,
                "error": "Username already exists.",
            }), 409

        # -- 3 & 4. Atomic transaction (Flow 1A) --
        pw_hash   = hash_password(password)
        farmer_id = None

        try:
            # Explicit transaction — isolation & atomicity guaranteed
            db.execute("BEGIN")

            cursor = db.execute(
                """
                INSERT INTO users (username, password_hash, role, email)
                VALUES (?, ?, ?, ?)
                """,
                (username, pw_hash, role, email),
            )
            user_id = cursor.lastrowid

            if role == "farmer":
                cursor = db.execute(
                    """
                    INSERT INTO farmers (user_id, farm_name)
                    VALUES (?, ?)
                    """,
                    (user_id, farm_name),
                )
                farmer_id = cursor.lastrowid

            db.execute("COMMIT")

        except sqlite3.IntegrityError as exc:
            db.execute("ROLLBACK")
            # Catch any late-stage constraint violations (race condition on
            # username uniqueness between check and insert)
            if "UNIQUE" in str(exc).upper():
                return jsonify({"success": False, "error": "Username already exists."}), 409
            return jsonify({
                "success": False,
                "error": "Registration failed. Please try again.",
            }), 500
        except Exception:
            db.execute("ROLLBACK")
            return jsonify({
                "success": False,
                "error": "Registration failed. Please try again.",
            }), 500

        # -- 5. Success response (AG-API-INC1-003 §3.1 exact structure) --
        return jsonify({
            "success": True,
            "message": "Registration successful. Please log in.",
            "user": {
                "user_id":   user_id,
                "username":  username,
                "role":      role,
                "farmer_id": farmer_id,
            },
        }), 201

    # ------------------------------------------------------------------ #
    #  POST /api/auth/login                                               #
    #  AG-API-INC1-003 §3.2                                              #
    # ------------------------------------------------------------------ #
    @app.route("/api/auth/login", methods=["POST"])
    def login():
        """
        Credential verification + JWT issuance.

        Uses a single LEFT JOIN query (per API contract §3.2) to fetch both
        the user record and the linked farmer_id in one round-trip.
        Returns generic "Invalid credentials." for both bad-username and
        bad-password to prevent username enumeration (FR-LGN-016).
        """
        db = get_db()

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid request format."}), 400

        username = (data.get("username") or "").strip()
        password = data.get("password") or ""

        if not username or not password:
            return jsonify({
                "success": False,
                "error": "Username and password are required.",
            }), 400

        # Single LEFT JOIN: one query covers both users and farmers tables
        # (AG-API-INC1-003 §3.2 — "optimised single LEFT JOIN")
        row = db.execute(
            """
            SELECT  u.id            AS user_id,
                    u.username,
                    u.password_hash,
                    u.role,
                    u.is_active,
                    f.id            AS farmer_id
            FROM    users u
            LEFT JOIN farmers f ON f.user_id = u.id
            WHERE   u.username = ?
            """,
            (username,),
        ).fetchone()

        # Generic 401 for both "not found" and "wrong password" (anti-enum)
        if row is None:
            return jsonify({"success": False, "error": "Invalid credentials."}), 401

        if not row["is_active"]:
            return jsonify({"success": False, "error": "Invalid credentials."}), 401

        if not verify_password(password, row["password_hash"]):
            return jsonify({"success": False, "error": "Invalid credentials."}), 401

        # Issue JWT with exact claim structure (AG-API-INC1-003 §2)
        token = generate_token(
            user_id=row["user_id"],
            farmer_id=row["farmer_id"],   # None for non-farmer roles
            role=row["role"],
        )

        return jsonify({
            "success": True,
            "token":   token,
            "role":    row["role"],
            "user": {
                "user_id":   row["user_id"],
                "farmer_id": row["farmer_id"],
                "username":  row["username"],
                "role":      row["role"],
            },
        }), 200

    # ------------------------------------------------------------------ #
    #  POST /api/auth/logout                                              #
    #  AG-API-INC1-003 §3.3                                              #
    # ------------------------------------------------------------------ #
    @app.route("/api/auth/logout", methods=["POST"])
    @token_required
    def logout():
        """
        Session termination acknowledgement.

        Since JWTs are stateless, true invalidation requires a token
        blocklist (deferred to a future increment when Redis is available).
        The frontend contract is: remove agrigrid_token from sessionStorage
        and redirect to /login (AG-API-INC1-003 §3.3 frontend rule).
        """
        return jsonify({
            "success": True,
            "message": "Logged out successfully.",
        }), 200

    # ------------------------------------------------------------------ #
    #  GET /api/auth/me  (RBAC smoke-test route)                         #
    #  Not in the API contract — internal V&V endpoint for test_auth.py  #
    # ------------------------------------------------------------------ #
    @app.route("/api/auth/me", methods=["GET"])
    @token_required
    def me():
        """
        Returns the authenticated user's identity extracted from the JWT.
        Used by test_auth.py to confirm token validation + g context injection.
        """
        return jsonify({
            "success":   True,
            "user_id":   g.user_id,
            "farmer_id": g.farmer_id,
            "role":      g.role,
        }), 200

    # ------------------------------------------------------------------ #
    #  GET /api/dashboard/<role>  (Placeholder routes — FR-LGN-013)      #
    # ------------------------------------------------------------------ #
    @app.route("/dashboard/farmer", methods=["GET"])
    @token_required
    @role_required("farmer")
    def dashboard_farmer():
        return jsonify({
            "success": True,
            "message": "Farmer Dashboard — functional in Increment 1.",
        }), 200

    for _role in ("buyer", "transporter", "agronomist", "compliance"):
        # Build placeholder routes for non-farmer dashboards (FR-LGN-013)
        def _make_placeholder(role_name):
            @token_required
            @role_required(role_name if role_name != "compliance" else "compliance_officer")
            def _placeholder():
                return jsonify({
                    "success": True,
                    "message": f"Dashboard under construction — available in a future increment.",
                }), 200
            _placeholder.__name__ = f"dashboard_{role_name}"
            return _placeholder

        app.add_url_rule(
            f"/dashboard/{_role}",
            endpoint=f"dashboard_{_role}",
            view_func=_make_placeholder(_role),
            methods=["GET"],
        )


# ---------------------------------------------------------------------------
# Standard Error Handlers (AG-API-INC1-003 §5)
# ---------------------------------------------------------------------------

def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"success": False, "error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(_e):
        return jsonify({"success": False, "error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def internal_error(_e):
        return jsonify({
            "success": False,
            "error": "An internal error occurred. Please try again later.",
        }), 500


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

# Import here to keep module-level clean when imported by test_auth.py
from flask import current_app  # noqa: E402

if __name__ == "__main__":
    application = create_app()
    _register_error_handlers(application)
    print("=" * 60)
    print("  Agri-Grid Backend  —  Increment 1  (Run 2)")
    print(f"  DB : {DB_PATH}")
    print("  Endpoints: /api/auth/register | /api/auth/login | /api/auth/logout")
    print("=" * 60)
    # debug=True enables auto-reloader and detailed tracebacks during dev.
    # MUST be False in production.
    application.run(host="127.0.0.1", port=5000, debug=True)
