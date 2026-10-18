# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Specification for Bragi Desktop Application
======================================================
Bundles Flet UI, C-extensions (PortAudio/aubio), DSP audio engines,
Pydantic models, and application storage files into a standalone executable.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs

block_cipher = None

# Resolve absolute paths for the repository root and source directory
project_root = os.path.abspath(os.path.dirname(__file__))
src_dir = os.path.join(project_root, "src")

# Collect dynamic C-libraries for PortAudio (sounddevice) and aubio
sounddevice_libs = collect_dynamic_libs("sounddevice")
aubio_libs = collect_dynamic_libs("aubio")
binaries = sounddevice_libs + aubio_libs

# Bundle static asset directories and default instrument profile storage
datas = []

assets_dir = os.path.join(project_root, "assets")
if os.path.exists(assets_dir):
    datas.append((assets_dir, "assets"))

storage_dir = os.path.join(src_dir, "storage")
if os.path.exists(storage_dir):
    datas.append((storage_dir, "storage"))

a = Analysis(
    [os.path.join(src_dir, "main.py")],
    pathex=[project_root, src_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=[
        # Core third-party dependencies
        "sounddevice",
        "aubio",
        "numpy",
        "scipy",
        "scipy.signal",
        "flet",
        "flet.version",
        "pydantic",
        "pydantic_core",
        "sqlite3",
        # Internal application modules & packages
        "audio",
        "controllers",
        "engine",
        "models",
        "services",
        "storage",
        "utils",
        "views",
        "controllers.metronome_controller",
        "controllers.session_controller",
        "engine.chord_evaluator",
        "engine.chord_generator",
        "engine.note_evaluator",
        "engine.scale_engine",
        "engine.scale_sequencer",
        "models.chord",
        "models.instrument",
        "models.session",
        "services.audio_manager",
        "services.audio_synth",
        "services.dsp_processor",
        "storage.instrument_store",
        "utils.fretboard_mapper",
        "utils.music_theory",
        "utils.theme_manager",
        "views.main_view",
        "views.components.fretboard_view",
        "views.components.metronome_widget",
        "views.subviews.chord_view",
        "views.subviews.scale_view",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "django", "flask"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# Resolve platform icon file path
icon_path = None
if sys.platform == "win32":
    win_ico = os.path.join(project_root, "assets", "icon.ico")
    win_png = os.path.join(project_root, "assets", "icon.png")
    icon_path = win_ico if os.path.exists(win_ico) else (win_png if os.path.exists(win_png) else None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Bragi",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Bragi",
)
