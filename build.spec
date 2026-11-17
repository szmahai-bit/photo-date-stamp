# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec: single-file EXE bundling tkinter + Pillow + render core.
# Paths are resolved relative to this spec file so the repo stays portable.
import os

HERE = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['photo_date_gui.py'],
    pathex=[HERE],
    binaries=[],
    datas=[],
    hiddenimports=['stamp_core', 'PIL._tkinter_finder', 'ctypes.wintypes'],
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
    a.binaries,
    a.datas,
    [],
    name='照片加日期',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=os.path.join(HERE, 'assets', 'icon.ico'),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
