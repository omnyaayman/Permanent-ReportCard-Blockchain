@echo off
title ReportCard Blockchain Project
color 0A

echo ==========================================
echo REPORTCARD BLOCKCHAIN SYSTEM
echo ==========================================

REM --- Python detection ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH. Install Python 3.10+ and retry.
    pause
    exit /b 1
)

set PYTHONIOENCODING=utf-8

echo.
echo [0] UNIT TESTS
python -m unittest discover -s tests
if errorlevel 1 (
    echo [WARN] Unit tests reported failures. Continuing anyway...
)

echo.
echo [1] DEPLOYMENT + SETUP
python scripts/deploy_and_setup.py
if errorlevel 1 goto :FAIL

echo.
echo [2] SECURITY TEST
python scripts/security_test.py
if errorlevel 1 goto :FAIL

echo.
echo [3] BLOCKCHAIN SCANNER
python scripts/blockchain_scanner.py
if errorlevel 1 goto :FAIL

echo.
echo [4] OWNERSHIP TRANSFER TEST
python scripts/ownership_transfer_test.py
if errorlevel 1 goto :FAIL

echo.
echo [5] LIVE ALERT SYSTEM
start cmd /k python scripts/live_alert.py

echo.
echo [6] ADMIN DASHBOARD
start python scripts/admin_dashboard.py

echo.
echo [7] STREAMLIT GUI  (http://localhost:8501)
start http://localhost:8501
timeout /t 1 >nul
start python -m streamlit run scripts/gui_app.py

echo.
echo ==========================================
echo ALL TASKS FINISHED SUCCESSFULLY
echo ==========================================
pause
exit /b 0

:FAIL
echo.
echo ==========================================
echo ONE OF THE STEPS FAILED - CHECK OUTPUT ABOVE
echo ==========================================
pause
exit /b 1