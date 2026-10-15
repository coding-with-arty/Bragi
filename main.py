# main.py
import sys
from pathlib import Path

# Ensure src directory is on the Python module search path
sys.path.insert(0, str(Path(__file__).parent / "src"))

import flet as ft
from app_layout import AppLayout
from storage.progress_repository import ProgressRepository
from utils.theme_manager import ThemeManager


def main(page: ft.Page):
    page.title = "FretSense - Fretboard & Ear Trainer"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    theme_manager = ThemeManager(page)
    repository = ProgressRepository()

    layout = AppLayout(page=page, theme_manager=theme_manager, repository=repository)
    page.add(layout)


if __name__ == "__main__":
    # ft.run() replaces ft.app() in modern Flet
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
