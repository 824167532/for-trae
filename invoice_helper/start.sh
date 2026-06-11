#!/bin/bash
# Invoice Helper - Terminal Launcher

echo "========================================"
echo "  Invoice Helper - Terminal Launcher"
echo "========================================"
echo ""

cd "$(dirname "$0")"

echo "Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not detected. Please install Python 3.8 or higher."
    echo "Download: https://www.python.org/downloads/"
    exit 1
fi

echo "Checking dependencies..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "Installing dependencies..."
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install dependencies"
        exit 1
    fi
fi

echo "Starting service..."
echo ""
echo "Please visit: http://127.0.0.1:5000"
echo "Press Ctrl+C to stop service"
echo ""

python3 app.py
