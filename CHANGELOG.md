# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-17

### Added

- Initial public release.
- Independent GUI tool (`photo_date_gui.py`) for batch-adding film-style date stamps.
- `stamp_core.py` rendering core: Pentax-orange seven-segment digits, soft glow, ghost segments, `screen` blend mode.
- EXIF-based capture date detection with manual date fallback.
- Landscape (bottom-right) and portrait (top-right, rotated 90°) layouts calibrated from real Pentax film samples.
- Three import methods: multi-select files, recursive folder add, and native Windows drag-and-drop of files/folders.
- Live preview, adjustable format/size/color/position/margins/glow.
- Batch processing with progress bar and log; configurable output directory; originals preserved, EXIF/ICC kept.
- UI font follows Windows system UI font and DPI scaling.
- Self-contained single-file PyInstaller EXE.
- Documentation: README (中文/English), CONTRIBUTING, CHANGELOG, CODE_OF_CONDUCT, SECURITY, issue templates, CI workflow.
