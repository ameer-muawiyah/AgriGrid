#!/usr/bin/env python3
"""
Agri-Grid — One-Click Launcher (Increment 1)
============================================
Starts the Flask backend API (port 5000) and the static frontend server
(port 5500), waits until both respond, then opens the app in the default
browser. No commands to remember.

Usage:
    Windows : double-click  start-agri-grid.bat   (or: python launch_agrigrid.py)
    macOS   : ./start-agri-grid.sh  (rename to .command for double-click)
    Linux   : ./start-agri-grid.sh  (or: python3 launch_agrigrid.py)

Press Ctrl+C in this window (or just close it) to stop both servers.
Standard library only — no new dependencies.
"""

import os
import sys
import time
import socket
import subprocess
import threading
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_PORT = 5000
FRONTEND_PORT = 5500
APP_URL = f"http://127.0.0.1:{FRONTEND_PORT}/"
LOG_DIR = os.path.join(ROOT, "logs")


def pick_python():
    """Prefer the project virtualenv when present, else the current interpreter."""
    candidates = [
        os.path.join(ROOT, "venv", "Scripts", "python.exe"),  # Windows venv
        os.path.join(ROOT, "venv", "bin", "python"),           # macOS/Linux venv
        sys.executable,
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(candidate):
            return candidate
    return sys.executable


def port_is_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def wait_for_port(port, timeout=25):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if port_is_open(port):
            return True
        time.sleep(0.4)
    return False


def ensure_dependencies(py):
    """Install backend requirements on first run if Flask (etc.) is missing."""
    probe = subprocess.run(
        [py, "-c", "import flask, flask_cors, bcrypt, jwt, requests"],
        capture_output=True,
    )
    if probe.returncode != 0:
        print(">> First run: installing backend dependencies (one-time)...")
        subprocess.run(
            [py, "-m", "pip", "install", "-r",
             os.path.join(ROOT, "backend", "requirements.txt")],
            check=True,
        )
        print(">> Dependencies installed.")


def ensure_database(py):
    """Create + seed agrigrid.db on first run."""
    db_path = os.path.join(ROOT, "backend", "database", "agrigrid.db")
    if not os.path.isfile(db_path):
        print(">> First run: creating and seeding the database...")
        subprocess.run(
            [py, os.path.join(ROOT, "backend", "database", "init_db.py")],
            check=True, cwd=ROOT,
        )


def start_backend(py, log_file):
    """
    Run the Flask app WITHOUT the debug reloader so it stays a single
    process that shuts down cleanly. Identical routes, error handlers and
    config to `python backend/app.py` — only auto-reload is off.
    """
    code = (
        "import sys; sys.path.insert(0, 'backend');"
        "from app import create_app, _register_error_handlers;"
        "app = create_app(); _register_error_handlers(app);"
        f"app.run(host='127.0.0.1', port={BACKEND_PORT}, debug=False, use_reloader=False)"
    )
    return subprocess.Popen(
        [py, "-c", code],
        cwd=ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )


def start_frontend(py, log_file):
    return subprocess.Popen(
        [py, "-m", "http.server", str(FRONTEND_PORT), "--directory", "frontend"],
        cwd=ROOT,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )


def print_log_tail(path, lines=20):
    try:
        with open(path, "r", errors="replace") as fh:
            tail = fh.read().splitlines()[-lines:]
        print(f"--- last {lines} lines of {os.path.basename(path)} ---")
        for line in tail:
            print("    " + line)
    except OSError:
        print(f"    (no log file at {path})")


def main():
    print("=" * 58)
    print("  Agri-Grid Launcher — starting Increment 1")
    print("=" * 58)

    os.makedirs(LOG_DIR, exist_ok=True)
    backend_log = open(os.path.join(LOG_DIR, "backend.log"), "w")
    frontend_log = open(os.path.join(LOG_DIR, "frontend.log"), "w")

    py = pick_python()
    print(f">> Using Python: {py}")

    for port, name in ((BACKEND_PORT, "backend (5000)"),
                       (FRONTEND_PORT, "frontend (5500)")):
        if port_is_open(port):
            print(f">> ERROR: port {port} is already in use — cannot start {name}.")
            print("   Close whatever is using it (maybe an old Agri-Grid window) and try again.")
            backend_log.close(); frontend_log.close()
            if os.name == "nt":
                os.system("pause")
            sys.exit(1)

    ensure_dependencies(py)
    ensure_database(py)

    print(">> Starting backend API (port 5000)...")
    backend = start_backend(py, backend_log)
    print(">> Starting frontend server (port 5500)...")
    frontend = start_frontend(py, frontend_log)

    print(">> Waiting for servers to respond...")
    ok = wait_for_port(BACKEND_PORT) and wait_for_port(FRONTEND_PORT)
    if not ok:
        print(">> ERROR: a server did not start in time. Recent log output:")
        print_log_tail(os.path.join(LOG_DIR, "backend.log"))
        print_log_tail(os.path.join(LOG_DIR, "frontend.log"))
        backend.terminate(); frontend.terminate()
        backend_log.close(); frontend_log.close()
        if os.name == "nt":
            os.system("pause")
        sys.exit(1)

    print(">> Opening Agri-Grid in your browser...")
    threading.Thread(target=webbrowser.open, args=(APP_URL,), daemon=True).start()

    print()
    print(f"  App is running at {APP_URL}")
    print("  Keep this window open. Press Ctrl+C (or close it) to stop everything.")
    print("=" * 58)

    try:
        while True:
            time.sleep(1)
            if backend.poll() is not None or frontend.poll() is not None:
                print(">> A server stopped unexpectedly — shutting down the other.")
                break
    except KeyboardInterrupt:
        print("\n>> Stopping Agri-Grid...")
    finally:
        for proc in (backend, frontend):
            if proc.poll() is None:
                proc.terminate()
        backend_log.close(); frontend_log.close()
        print(">> All servers stopped. You can close this window.")


if __name__ == "__main__":
    main()
