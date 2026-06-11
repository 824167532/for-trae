@echo off
chcp 65001 >nul
title Invoice Helper
setlocal

echo ========================================
echo   Invoice Helper - Windows Launcher
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not detected
    echo.
    echo Please install Python 3.8 or higher
    echo Download: https://www.python.org/downloads/
    echo.
    echo When installing, make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
echo [OK] Python found
echo.

echo [2/3] Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies (may take a few minutes)...
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies
        echo Please check your network connection or run manually:
        echo   python -m pip install Flask openpyxl
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies already installed
)
echo.

echo [3/3] Starting service...
echo.
echo ========================================
echo   Service started
echo ========================================
echo.
echo Please visit: http://127.0.0.1:5000
echo.
echo Tips:
echo   1. First visit will open your browser
echo   2. If no browser opens, visit the URL manually
echo   3. Press Ctrl+C to stop service
echo   4. DO NOT close this window while service is running
echo.
echo ========================================
echo.

python app.py

pause
endlocal
