#!/bin/bash
# Invoice Helper - macOS Launcher (double-click to run)
# Run: chmod +x start.command (one-time setup), then double-click

cd "$(dirname "$0")"

echo "========================================"
echo "  Invoice Helper - macOS Launcher"
echo "========================================"
echo

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not detected"
    echo
    echo "Please install Python 3.8 or higher"
    echo "Download: https://www.python.org/downloads/"
    echo
    read -p "Press Enter to exit..."
    exit 1
fi
echo "[OK] Python 3 found"
echo

# Check dependencies
if ! python3 -c "import flask" &> /dev/null; then
    echo "Installing dependencies (may take a few minutes)..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo
        echo "[ERROR] Failed to install dependencies"
        echo "Please check your network or run manually:"
        echo "  python3 -m pip install Flask openpyxl"
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "[OK] Dependencies installed"
else
    echo "[OK] Dependencies already installed"
fi
echo

echo "Starting service..."
echo
echo "========================================"
echo "  Service started"
echo "========================================"
echo
echo "Please visit: http://127.0.0.1:5000"
echo
echo "Tips:"
echo "  1. First visit will open your browser"
echo "  2. If no browser opens, visit the URL manually"
echo "  3. Press Ctrl+C to stop service"
echo "  4. DO NOT close this window while service is running"
echo
echo "========================================"
echo

python3 app.py

read -p "Press Enter to exit..."
