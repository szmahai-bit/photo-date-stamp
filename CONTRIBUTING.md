# Contributing / 贡献指南

Thanks for your interest in improving Film Date Stamp! This document explains how to set up the project and submit changes.

## Development setup

```bat
git clone https://github.com/<your-username>/photo-date-stamp.git
cd photo-date-stamp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
python photo_date_gui.py
```

Requires Windows + Python 3.10+. The GUI depends on `tkinter` (bundled with CPython on Windows).

## Project layout

- `stamp_core.py` — pure rendering/processing logic, Pillow only. Keep it free of GUI and OS-specific code so it stays usable as a library.
- `photo_date_gui.py` — tkinter GUI, Windows native drag-and-drop and font detection.
- `build.spec` / `build.bat` — PyInstaller onefile packaging.

## Making changes

1. Fork the repo and create a branch: `git checkout -b feature/your-change`.
2. Make your change. Keep code style consistent (4-space indent, type hints where helpful).
3. Test locally: add a few photos, verify the preview and batch output, check that EXIF is preserved.
4. Commit with a clear message and push to your fork.
5. Open a Pull Request describing **what** changed and **why**.

## Reporting bugs

Use the bug report issue template. Please include:

- Windows version (10 / 11, build number)
- Python version (if running from source) or the EXE version
- A sample photo that reproduces the issue (remove any private data)
- Steps to reproduce and the expected vs. actual result

## Feature requests

Open an issue with the feature request template. Describe the use case, not just the implementation idea.

## Packaging note

When changing imports in `stamp_core.py` or adding dependencies, update `hiddenimports` in `build.spec` and `requirements*.txt` so the EXE build keeps working.

## Code of conduct

By participating you agree to our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

Contributions are accepted under the [MIT License](LICENSE).
