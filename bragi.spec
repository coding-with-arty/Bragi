# bragi.spec
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect binaries and data for hardware audio C-libraries
sounddevice_datas, sounddevice_binaries, sounddevice_hiddenimports = collect_all('sounddevice')
aubio_datas, aubio_binaries, aubio_hiddenimports = collect_all('aubio')

hidden_imports = [
    'flet',
    'pydantic',
    'numpy',
    'sqlite3',
] + sounddevice_hiddenimports + aubio_hiddenimports

datas = [
    ('assets', 'assets'),
] + sounddevice_datas + aubio_datas

binaries = sounddevice_binaries + aubio_binaries

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Bragi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Bragi',
)
