@echo off
title Agri-Grid Launcher
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
    py -3 launch_agrigrid.py
) else (
    python launch_agrigrid.py
)
echo.
pause
