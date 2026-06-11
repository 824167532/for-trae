#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portable package builder for Invoice Helper (Windows only).

Downloads an embedded Python, installs Flask + openpyxl into it,
then bundles everything into one self-contained folder so end users
do NOT need to install Python themselves.

Run this on a Windows machine (Python 3.8+ required on the builder).
Usage:
    python build_portable.py
Output:
    releases/invoice_helper_portable_v{version}.zip
    -> Unzip on any Windows PC, double-click start.bat, done.
"""

import os
import sys
import io
import re
import shutil
import struct
import zipfile
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE

# --- Load version ----------------------------------------------------------
try:
    import json
    with open(PROJECT_ROOT / "version.json", "r", encoding="utf-8") as f:
        VERSION = json.load(f).get("version", "1.0.0")
except Exception:
    VERSION = "1.0.0"

print(f"Building portable package v{VERSION}")
print("-" * 60)

# --- Options ---------------------------------------------------------------
PYTHON_VERSION = "3.12.4"   # stable, well-tested embed release
PY_ARCH = "amd64" if (struct.calcsize("P") * 8 == 64) else "win32"
DIST_DIR = PROJECT_ROOT / "dist_portable"
PY_DIR = DIST_DIR / "python"
OUT_ZIP = PROJECT_ROOT / "releases" / f"invoice_helper_portable_v{VERSION}.zip"

PY_URL = (
    f"https://www.python.org/ftp/python/{PYTHON_VERSION}/"
    f"python-{PYTHON_VERSION}-embed-{PY_ARCH}.zip"
)
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"


def download(url: str, desc: str) -> bytes:
    print(f"  Downloading {desc} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()
    print(f"    OK ({len(data):,} bytes)")
    return data


def step(msg: str) -> None:
    print(f"\n[ {msg} ]")


# --- 1. Clean ----------------------------------------------------------------
step("1/6  Clean dist folder")
if DIST_DIR.exists():
    shutil.rmtree(DIST_DIR)
DIST_DIR.mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "releases").mkdir(parents=True, exist_ok=True)

# --- 2. Fetch embedded Python ------------------------------------------------
step("2/6  Fetch embedded Python")
python_zip_bytes = download(PY_URL, f"Python {PYTHON_VERSION} embed ({PY_ARCH})")
print(f"  Extracting to {PY_DIR} ...")
with zipfile.ZipFile(io.BytesIO(python_zip_bytes)) as zf:
    zf.extractall(PY_DIR)
print("  OK")

# --- 3. Enable pip in the embedded Python ------------------------------------
step("3/6  Enable pip / site-packages in embedded Python")
# The embed python ships with a `python{XY}._pth` file that lists paths and
# has `import site` commented. Removing the comment (and/or adding
# Lib\site-packages) makes `pip install ... --target` and regular imports work.
py_xy = f"python{PYTHON_VERSION.split('.')[0]}{PYTHON_VERSION.split('.')[1]}"
pth_file = PY_DIR / f"{py_xy}._pth"
# Fallback pattern match in case filename differs
if not pth_file.exists():
    for f in PY_DIR.glob("*._pth"):
        pth_file = f
        break
print(f"  ._pth file: {pth_file.name}")

# Rewrite content: keep existing lines, uncomment "import site", and ensure
# Lib\site-packages is listed.
original = pth_file.read_text(encoding="utf-8", errors="ignore")
lines = [ln for ln in original.splitlines() if ln.strip()]
# Drop existing 'import site' line if any, we'll re-add it
lines = [ln for ln in lines if "import site" not in ln.lower()]
new_lines = lines + ["Lib\\site-packages", "import site"]
pth_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print("  OK")

# --- 4. Bootstrap pip into the embedded python -------------------------------
step("4/6  Bootstrap pip")
get_pip_bytes = download(GET_PIP_URL, "get-pip.py")
get_pip_path = PY_DIR / "get-pip.py"
get_pip_path.write_bytes(get_pip_bytes)

py_exe = PY_DIR / "python.exe"
if not py_exe.exists():
    print(f"  ERROR: python.exe not found in {PY_DIR}")
    sys.exit(1)

print("  Running get-pip.py with embedded python ...")
r = subprocess.run([str(py_exe), str(get_pip_path), "--no-warn-script-location"],
                   cwd=str(PY_DIR))
if r.returncode != 0:
    print("  ERROR: get-pip.py failed")
    sys.exit(1)
get_pip_path.unlink(missing_ok=True)
print("  OK")

# --- 5. Install dependencies into the embedded python ------------------------
step("5/6  Install Flask + openpyxl into embedded Python")
r = subprocess.run(
    [str(py_exe), "-m", "pip", "install",
     "--upgrade", "pip", "Flask", "openpyxl",
     "--no-warn-script-location"],
    cwd=str(PY_DIR),
)
if r.returncode != 0:
    print("  ERROR: pip install failed")
    sys.exit(1)
print("  OK")

# Verify imports work
print("  Verifying imports ...")
r = subprocess.run(
    [str(py_exe), "-c", "import flask, openpyxl; print('flask', flask.__version__); print('openpyxl', openpyxl.__version__)"],
    capture_output=True, text=True, cwd=str(PY_DIR),
)
if r.returncode != 0:
    print("  WARNING: import check failed")
    print(r.stderr)
else:
    print(r.stdout.strip())

# --- 6. Copy application files and build zip ---------------------------------
step("6/6  Copy app files and package")

# Copy the app source tree into dist (everything except build artifacts)
INCLUDE_DIRS = ["routes", "services", "static", "templates", "tools"]
for d in INCLUDE_DIRS:
    src = PROJECT_ROOT / d
    if src.exists():
        shutil.copytree(src, DIST_DIR / d)

for f in ["app.py", "models.py", "version.json", "version_utils.py",
          "requirements.txt", "README.md", "UPGRADE_GUIDE.md"]:
    src = PROJECT_ROOT / f
    if src.exists():
        shutil.copy(src, DIST_DIR / f)

# Drop in a portable start.bat that calls our embedded python
start_bat = DIST_DIR / "start.bat"
start_bat.write_text("""@echo off
REM ============================================================
REM  Invoice Helper - Portable Launcher
REM  Uses the embedded Python under .\\python\\
REM  No system Python installation needed.
REM ============================================================

cd /d "%~dp0"

echo ========================================
echo   Invoice Helper (Portable)
echo ========================================
echo.

if not exist "python\\python.exe" (
    echo [ERROR] python\\python.exe not found.
    echo   The portable package is incomplete.
    echo   Please re-download and re-unzip.
    echo.
    pause
    exit /b 1
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

python\\python.exe app.py

echo.
echo Server stopped.
pause
""", encoding="utf-8")

# Also copy the original start.command / start.sh for macOS users
for src_name, dst_name in [("start.command", "start.command"),
                           ("start.sh", "start.sh")]:
    src = PROJECT_ROOT / src_name
    if src.exists():
        shutil.copy(src, DIST_DIR / dst_name)

# Zip
print(f"  Creating {OUT_ZIP.name} ...")
if OUT_ZIP.exists():
    OUT_ZIP.unlink()
with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
    for p in DIST_DIR.rglob("*"):
        if not p.is_file():
            continue
        arcname = p.relative_to(DIST_DIR).as_posix()
        zf.write(p, arcname)

size_mb = OUT_ZIP.stat().st_size / 1024 / 1024
print(f"  OK ({size_mb:.1f} MB)")

print("\n" + "=" * 60)
print(f"  Portable package ready:")
print(f"    {OUT_ZIP}")
print("=" * 60)
print()
print("Usage for end users (Windows):")
print("  1. Unzip the file to any folder")
print("  2. Double-click start.bat")
print("  3. Browser opens at http://127.0.0.1:5000")
print()
print("No Python installation required.")
