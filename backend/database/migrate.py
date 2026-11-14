"""
Agri-Grid: Smart Agriculture & Food Security Ecosystem
File:    migrate.py
Module:  Database Migration Engine
Version: 2.0  (Increment 2 — Core Data Engine & Demand Side)
Author:  Bareera Noor (Database Administrator)
Date:    2026-11-14
Source:  AG-PLAN-INC2-001 §4.1, §5 & Phase 1 Build Package (Part A)

Purpose
-------
Automated, zero-dependency database migration runner ensuring forward schema
evolution without destroying existing production or development data.
Applies incremental, version-controlled SQL migrations statement-by-statement
under strict ACID transaction boundaries (BEGIN IMMEDIATE ... COMMIT/ROLLBACK).
Guarantees immutability through SHA-256 file checksum verification.

Execution Rules
---------------
1. sqlite3.executescript() is STRICTLY FORBIDDEN (implicit commit destroys transactions).
2. SQL statements are accumulated and split via sqlite3.complete_statement().
3. schema_versions table is created outside migration transactions.
4. Handles three states:
   - Empty DB: applies 001, 002, etc.
   - Pre-existing Inc 1 DB: stamps 001 without executing, applies 002.
   - Versioned DB: verifies applied checksums, applies pending.
5. Emits one status line per migration (APPLIED / SKIP / STAMPED) and a final
   'Schema version: N' summary.
"""

import hashlib
import os
import re
import sqlite3
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path resolution — strictly resolved relative to this script's directory
# Canonical DB: backend/database/agrigrid.db (never a relative path)
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CANONICAL_DB_PATH = os.environ.get(
    "AGRIGRID_DB_PATH",
    os.path.join(SCRIPT_DIR, "agrigrid.db"),
)
MIGRATIONS_DIR = os.environ.get(
    "AGRIGRID_MIGRATIONS_DIR",
    os.path.join(SCRIPT_DIR, "migrations"),
)


def split_sql_statements(sql_text: str) -> list[str]:
    """
    Split SQL script into individual executable statements using
    sqlite3.complete_statement() accumulation.
    NEVER uses str.split(';') because triggers and blocks contain inner semicolons.
    """
    statements = []
    buffer = ""
    for line in sql_text.splitlines(keepends=True):
        buffer += line
        if sqlite3.complete_statement(buffer):
            stmt = buffer.strip()
            if stmt:
                statements.append(stmt)
            buffer = ""

    trailing = buffer.strip()
    if trailing:
        # Only add trailing if it contains non-comment characters
        non_comment_lines = [
            l for l in trailing.splitlines()
            if l.strip() and not l.strip().startswith("--")
        ]
        if non_comment_lines:
            statements.append(trailing)

    return statements


def compute_checksum(file_path: str) -> str:
    """Compute SHA-256 hexadecimal digest of file contents (UTF-8)."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_available_migrations(migrations_dir: str) -> list[tuple[int, str, str]]:
    """
    Scan migrations directory for files named like 001_description.sql.
    Returns sorted list of (version_int, filename, full_path).
    """
    if not os.path.isdir(migrations_dir):
        return []

    pattern = re.compile(r"^(\d+)_(.+)\.sql$")
    migrations = []
    for entry in os.listdir(migrations_dir):
        match = pattern.match(entry)
        if match:
            version_int = int(match.group(1))
            full_path = os.path.join(migrations_dir, entry)
            migrations.append((version_int, entry, full_path))

    migrations.sort(key=lambda x: x[0])
    return migrations


def run_migrations(target_db_path: str = None) -> int:
    """
    Execute migration engine against the target SQLite database.
    Returns 0 on success/no-op, non-zero on failure.
    """
    db_file = os.path.abspath(target_db_path) if target_db_path else CANONICAL_DB_PATH
    os.makedirs(os.path.dirname(db_file), exist_ok=True)

    # Open connection with autocommit (isolation_level=None) for manual transaction management
    conn = sqlite3.connect(db_file, isolation_level=None)
    conn.execute("PRAGMA foreign_keys = ON;")

    try:
        # Step 1: Create schema_versions outside migration transactions
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                version     INTEGER NOT NULL UNIQUE,
                script_name TEXT NOT NULL,
                checksum    TEXT NOT NULL,
                applied_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
            );
        """)

        # Step 2: Inspect existing user tables to identify pre-existing Inc 1 DB
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
             WHERE type = 'table' 
               AND name NOT LIKE 'sqlite_%' 
               AND name != 'schema_versions';
        """)
        existing_tables = set(row[0] for row in cursor.fetchall())

        # Step 3: Inspect applied versions in schema_versions
        cursor.execute("SELECT version, script_name, checksum FROM schema_versions ORDER BY version ASC;")
        applied_rows = cursor.fetchall()
        applied_map = {row[0]: (row[1], row[2]) for row in applied_rows}

        # Step 4: Scan disk migrations
        available = get_available_migrations(MIGRATIONS_DIR)
        if not available:
            print("No migration scripts found in migrations directory.", file=sys.stderr)
            return 1

        is_pre_existing_inc1 = ("users" in existing_tables) and (1 not in applied_map)

        for ver, script_name, file_path in available:
            checksum = compute_checksum(file_path)

            if ver in applied_map:
                # State 3: Already versioned — verify checksum immutability
                rec_name, rec_checksum = applied_map[ver]
                if checksum != rec_checksum:
                    print(
                        f"FATAL: Checksum mismatch for migration {script_name} (version {ver})!\n"
                        f"  Recorded checksum: {rec_checksum}\n"
                        f"  Disk file checksum: {checksum}\n"
                        f"Applied migration files must be immutable. Halting startup.",
                        file=sys.stderr,
                    )
                    return 1
                print(f"SKIP: {script_name}")

            elif ver == 1 and is_pre_existing_inc1:
                # State 2: Pre-existing Increment 1 database — stamp version 1 without executing DDL
                conn.execute(
                    "INSERT INTO schema_versions (version, script_name, checksum) VALUES (?, ?, ?);",
                    (1, script_name, checksum),
                )
                applied_map[1] = (script_name, checksum)
                print(f"STAMPED: {script_name}")

            else:
                # State 1 or Pending Migration: Apply inside explicit BEGIN IMMEDIATE ... COMMIT
                with open(file_path, "r", encoding="utf-8") as f:
                    sql_text = f.read()

                statements = split_sql_statements(sql_text)

                conn.execute("BEGIN IMMEDIATE;")
                try:
                    for stmt in statements:
                        conn.execute(stmt)
                    conn.execute(
                        "INSERT INTO schema_versions (version, script_name, checksum) VALUES (?, ?, ?);",
                        (ver, script_name, checksum),
                    )
                    conn.execute("COMMIT;")
                    print(f"APPLIED: {script_name}")
                    applied_map[ver] = (script_name, checksum)
                except Exception as exc:
                    conn.execute("ROLLBACK;")
                    print(
                        f"FATAL: Migration failed on {script_name}: {exc}\n"
                        f"Transaction rolled back. Database remains at previous version.",
                        file=sys.stderr,
                    )
                    return 1

        # Step 5: Output current schema version
        cursor.execute("SELECT MAX(version) FROM schema_versions;")
        row = cursor.fetchone()
        latest_version = row[0] if (row and row[0] is not None) else 0
        print(f"Schema version: {latest_version}")
        return 0

    finally:
        conn.close()


def main() -> None:
    target_db = sys.argv[1] if len(sys.argv) > 1 else CANONICAL_DB_PATH
    exit_code = run_migrations(target_db)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
