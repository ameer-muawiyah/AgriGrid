#!/bin/sh
# Agri-Grid one-click launcher for macOS / Linux.
# Run: ./start-agri-grid.sh   (macOS: rename to start-agri-grid.command for double-click)
cd "$(dirname "$0")"
if command -v python3 >/dev/null 2>&1; then
  python3 launch_agrigrid.py
else
  python launch_agrigrid.py
fi
