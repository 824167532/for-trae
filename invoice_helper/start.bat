@echo off
REM ============================================================
REM  Invoice Helper - Windows Launcher
REM  Double-click this file to run
REM ============================================================

REM --- Always keep the window open even if something fails ---
if not "%1"=="" goto :%1

cd /d "%~dp0"

echo ========================================
echo   Invoice Helper - Windows Launcher
echo ========================================
echo.

echo [Step 1/3] Checking Python...
where python >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: When installing, TICK the box that says
    echo   "Add Python to PATH"
    echo.
    pause
    exit /b 1
)
for /f "delims=" %%i in ('python --version 2^>^&1') do echo [OK] Found: %%i
echo.

echo [Step 2/3] Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Flask not found. Installing dependencies...
    echo (This may take 1-5 minutes on first run)
    echo.
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies
        echo.
        echo Please try running these commands in a terminal:
        echo   cd /d "%~dp0"
        echo   python -m pip install Flask openpyxl
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies found
)
echo.

echo [Step 3/3] Starting service...
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

python app.py

echo.
echo Server stopped.
pause
