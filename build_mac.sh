#!/usr/bin/env bash
# Build a macOS .app bundle for 照片加日期 (Photo Date Stamp).
# Requirements: Python 3.10+ (with tkinter), pip, and macOS `iconutil`.
# Usage:  bash build_mac.sh
set -euo pipefail
cd "$(dirname "$0")"

PY="${PY:-python3}"

echo "==> Checking Python"
"$PY" --version

echo "==> Installing build dependencies"
"$PY" -m pip install --upgrade pip
"$PY" -m pip install -r requirements-dev.txt

echo "==> Generating icons (ICO + iconset)"
"$PY" make_icon.py

echo "==> Converting iconset to .icns with iconutil"
if [ -f assets/icon.icns ]; then
  echo "    icon.icns already present, skipping conversion"
else
  iconutil -c icns assets/icon.iconset -o assets/icon.icns
fi

echo "==> Building .app with PyInstaller"
"$PY" -m PyInstaller build_mac.spec --noconfirm --clean

echo ""
echo "==> Done. App bundle: dist/照片加日期.app"
echo "    You can drag it to /Applications."
