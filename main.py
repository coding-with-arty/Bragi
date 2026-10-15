# main.py
import sys
from pathlib import Path

# Adjust import paths
project_root = Path(__file__).resolve().parent
src_path = project_root / "src"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if src_path.exists() and str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import flet as ft
from app_layout import AppLayout


def main(page: ft.Page):
    page.title = "FretTrain - Fretboard & Polyphonic Chord Trainer"
    page.padding = 12
    page.theme_mode = ft.ThemeMode.DARK

    layout = AppLayout(page)
    page.add(layout)

    def window_event(e):
        if e.data == "close":
            layout.clean_up()
            page.window.destroy()

    page.window.on_event = window_event


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
