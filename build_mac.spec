# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: macOS .app bundle (tkinter + Pillow + render core).
# Paths are resolved relative to this spec file so the repo stays portable.
import os

HERE = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['photo_date_gui.py'],
    pathex=[HERE],
    binaries=[],
    datas=[],
    hiddenimports=['stamp_core', 'PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='照片加日期',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,               # UPX is not commonly available on macOS runners
    console=False,
    icon=os.path.join(HERE, 'assets', 'icon.icns'),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='照片加日期',
)
app = BUNDLE(
    coll,
    name='照片加日期.app',
    icon=os.path.join(HERE, 'assets', 'icon.icns'),
    bundle_identifier='com.photo-date-stamp.app',
    info_plist={
        'NSHighResolutionCapable': True,
        'CFBundleName': '照片加日期',
        'CFBundleDisplayName': '照片加日期',
        'NSHumanReadableCopyright': 'MIT License',
    },
)
