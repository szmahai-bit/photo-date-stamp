# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- macOS support: cross-platform GUI (no Windows-only imports on Mac), a PyInstaller
  `.app` build (`build_mac.spec` / `build_mac.sh`), a `.icns` icon generated via
  `iconutil`, and a macOS CI job that publishes the `.dmg` to Releases.
  Windows drag & drop remains; on macOS use the add buttons.

### Fixed

- macOS App is now built on the `macos-15-intel` (x86_64) runner instead of
  `macos-latest` (arm64). The previous arm64 build could not launch on Intel Macs;
  the Intel build runs natively on Intel Macs and via Rosetta 2 on Apple Silicon.
  The CI also verifies `uname -m` and the bundled binary's architecture before
  packaging to prevent an accidental arm64 build.

- Portrait photos no longer get rotated to landscape after export. `ImageOps.exif_transpose`
  already baked the display orientation into the pixels, but the original EXIF Orientation
  tag was still written back, causing image viewers to rotate the photo a second time.
  The Orientation tag (0x0112) is now stripped from the output while all other EXIF/ICC
  metadata is preserved.

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
