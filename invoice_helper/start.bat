@echo off
REM ============================================================
REM  Invoice Helper - Launcher
REM  Priority: 1) embedded python\python.exe (portable)
REM            2) system python.exe
REM ============================================================

cd /d "%~dp0"

REM --- Detect which python to use -----------------------------
set "PY_EXE="
if exist "python\python.exe" (
    set "PY_EXE=python\python.exe"
    set "PY_MODE=PORTABLE"
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        set "PY_EXE=python"
        set "PY_MODE=SYSTEM"
    )
)

if "%PY_EXE%"=="" (
    echo ========================================
    echo   Invoice Helper
    echo ========================================
    echo.
    echo [ERROR] Python not found.
    echo.
    echo You have two options:
    echo   1) Portable: run "python build_portable.py" on a Windows
    echo      machine once, then it will create python\ folder.
    echo      After that, double-click start.bat works on any PC.
    echo   2) System install: install Python 3.8+ from
    echo      https://www.python.org/downloads/
    echo      (remember to tick "Add Python to PATH" during install)
    echo.
    pause
    exit /b 1
)

echo ========================================
echo   Invoice Helper (%PY_MODE%)
echo ========================================
echo.

REM --- First-run dependency install (system mode only) ---------
if "%PY_MODE%"=="SYSTEM" (
    "%PY_EXE%" -c "import flask" >nul 2>&1
    if errorlevel 1 (
        echo Flask not found. Installing dependencies...
        echo (may take 1-5 minutes on first run)
        echo.
        "%PY_EXE%" -m pip install --upgrade pip
        "%PY_EXE%" -m pip install -r requirements.txt
        if errorlevel 1 (
            echo.
            echo [ERROR] Failed to install dependencies.
            echo   Please run this command manually in a terminal:
            echo     cd /d "%~dp0"
            echo     python -m pip install Flask openpyxl
            echo.
            pause
            exit /b 1
        )
        echo.
        echo [OK] Dependencies installed.
        echo.
    )
)

echo Starting service...
echo.
echo ========================================
echo   Service started
echo ========================================
echo.
echo Please open your browser and visit:
echo   http://127.0.0.1:5000
echo.
echo Tips:
echo   - First visit usually opens your browser automatically
echo   - If no browser opens, type the URL manually
echo   - Press Ctrl+C in this window to stop the service
echo   - DO NOT close this window while using the tool
echo.
echo ========================================
echo.

"%PY_EXE%" app.py

echo.
echo Server stopped.
pause
