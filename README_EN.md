# Film Date Stamp

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows / macOS](https://img.shields.io/badge/Platform-Windows%20%2F%20macOS-blue.svg)](https://github.com/szmahai-bit/photo-date-stamp)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)

A standalone GUI tool that burns a **film-camera-style date stamp** onto your photos in batch. Warm Pentax-orange seven-segment digits with soft glow and uneven segment brightness, composited in `screen` blend mode — it glows on dark areas and fades naturally on bright areas, recreating the look of real film backprint.

Landscape shots get the stamp at the bottom-right; portrait shots at the top-right, rotated 90°. Positions are calibrated from real Pentax film samples. Your originals are never modified, and EXIF / ICC data is preserved.

Fully standalone — no dependency on Alcedo Studio or any private skill.

> 中文文档：[README.md](README.md)

---

## Features

- 🖼️ **Three import methods**: pick individual photos, add a whole folder (recursive), or drag & drop on Windows (macOS uses the add buttons)
- 🔍 **Live preview**: click any photo in the list to see the stamped result instantly
- 📅 **Date source**: auto-read EXIF `DateTimeOriginal` → `DateTimeDigitized` → `DateTime`, or specify a date manually
- 🎨 **Fully tunable**: date format, size, color, position, margins, glow/ghost — all update the preview live
- 🧾 **Batch processing**: progress bar + log, configurable output directory (defaults to a `dated/` subfolder next to each photo)
- 💾 **Non-destructive**: originals untouched; EXIF and ICC profile preserved, with EXIF orientation fixed so portrait exports stay portrait
- 📦 **Cross-platform**: self-contained EXE for Windows, `.app` / `.dmg` for macOS — both double-click ready
- 🔤 **System font aware**: UI font size follows the system UI font (registry on Windows, system font on macOS) and DPI scaling

---

## Quick start

### Windows: prebuilt EXE (recommended)

Download `照片加日期.exe` from [Releases](../../releases), place it anywhere, and double-click. No Python or dependencies needed.

### macOS: prebuilt .app / .dmg (recommended)

Download the latest `照片加日期.dmg` (or the `照片加日期.app` from Actions artifacts) from [Releases](../../releases):

- `.dmg`: open it and drag "照片加日期" into Applications.
- `.app`: double-click to run. If macOS says it "can't be opened because it is from an unidentified developer", right-click → Open → Open again, or allow it in System Settings → Privacy & Security.

> **Architecture**: the build is an **Intel (x86_64)** app — native on Intel Macs, and runs on Apple Silicon (M1/M2/M3…) via macOS's built-in Rosetta 2. **One installer works on every Mac.** Earlier builds used `macos-latest` (arm64) and could not run on Intel Macs; the CI now builds on `macos-15-intel` with an architecture check.
>
> **⚠️ Pick the right architecture — don't grab the wrong batch**: GitHub Actions has two historical runs with identically-named artifacts. Choose the ones whose name contains **`intel`** (`photo-date-stamp-macos-intel-...`), or download from the run whose runner is `macos-15-intel`. The old batch (`macos-latest`, 2026-11-17 13:45) is arm64; opening it on an Intel Mac shows "this Mac does not support this app" with a prohibited icon — if you see that, you downloaded the wrong one, just re-download the Intel build. To be sure, drag the app into Terminal and run `lipo -info <AppPath>/Contents/MacOS/照片加日期`; only `x86_64` is correct.

> The macOS app is built automatically by GitHub Actions on an Intel macOS runner; no Mac installer made on Windows is shipped in this repo.

### Run from source (Windows / macOS)

Requires Python 3.10+ (with tkinter):

```bash
git clone https://github.com/szmahai-bit/photo-date-stamp.git
cd photo-date-stamp
pip install -r requirements.txt
python photo_date_gui.py
```

> System-level drag & drop uses Win32 APIs and works on Windows; on macOS use the "Add photos / Add folder" buttons. Everything else is identical. The render core `stamp_core.py` needs only Pillow and works on all platforms.

---

## How it works

The stamp is not a semi-transparent text overlay. It emulates the physics of film backprint:

1. Seven-segment glyphs are drawn from polygons with per-segment brightness variance.
2. Unlit segments retain a faint "ghost", mimicking incomplete extinguishing.
3. Gaussian blur produces soft edges and a halo.
4. A black-background, colored-light layer is composited with **screen** blending:
   - on dark pixels it glows;
   - on bright pixels it fades naturally.

That is why real film date prints are vivid on dark scenes and faint on bright ones.

---

## Project structure

```
photo-date-stamp/
├── photo_date_gui.py      # GUI main program (tkinter)
├── stamp_core.py          # Render/process core (Pillow only, usable as a library)
├── assets/
│   ├── icon.ico           # Windows EXE icon (generated, not committed)
│   └── icon.iconset/      # macOS icon PNG sources (generated, not committed)
├── make_icon.py           # Pure-Pillow calendar icon generator (ico + iconset)
├── docs/screenshots/      # UI screenshots
├── .github/               # Issue templates & CI (Windows EXE + macOS App)
├── build.spec             # PyInstaller onefile config (Windows)
├── build_mac.spec         # PyInstaller .app config (macOS)
├── build.bat              # Windows build script
├── build_mac.sh           # macOS build script
├── run.bat                # Windows source launch script
├── requirements.txt
└── README.md
```

Use the core as a library:

```python
from stamp_core import process_file

ok, text = process_file("input.jpg", "output.jpg")
```

---

## Build from source

### Windows EXE

```bat
pip install -r requirements-dev.txt
build.bat
```

Output: `dist/照片加日期.exe` (single file, ~30 MB).

### macOS App

On macOS (Python 3.10+ and the built-in `iconutil`):

```bash
pip install -r requirements-dev.txt
bash build_mac.sh
```

This generates icons (ico + iconset → `.icns` via `iconutil`) and builds `dist/照片加日期.app` with `build_mac.spec`. To make a `.dmg`:

```bash
hdiutil create -volname "照片加日期" -srcfolder "dist/照片加日期.app" -ov -format UDZO "dist/照片加日期.dmg"
```

> PyInstaller cannot cross-compile — the macOS app must be built on macOS. This repo's GitHub Actions builds it on `macos-15-intel` (x86_64, works on both Intel and Apple Silicon Macs) and attaches the `.dmg` to a Release when you push a tag (e.g. `v1.1.0`).

---

## Contributing

Issues and PRs welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

[MIT](LICENSE) © 2026 Horse

## Credits

- [Pillow](https://python-pillow.org/) — image processing
- Real Pentax film samples — layout & color reference
