"""
main.py
=======
Main application entry point for Frettrain with background asset rendering.
"""

import sys
from pathlib import Path

# Determine runtime root directory
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    ROOT_DIR = Path(sys._MEIPASS)
else:
    ROOT_DIR = Path(__file__).resolve().parent

SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import flet as ft
from utils.theme_manager import ThemeManager
from views.trainer_view import TrainerView


def main(page: ft.Page):
    page.title = "FretTrain - Guitar & Bass Note Trainer"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0  # Edge-to-edge full window layout for background
    page.spacing = 0

    theme_manager = ThemeManager(page)

    bg_container = ft.Container(
        expand=True,
        padding=10,
        image=ft.DecorationImage(
            src="bg.png",
            fit=ft.BoxFit.COVER,  # Corrected to ft.BoxFit.COVER
        ),
        content=TrainerView(theme_manager),
    )

    page.add(bg_container)


if __name__ == "__main__":
    assets_dir = ROOT_DIR / "assets"
    ft.run(main, assets_dir=str(assets_dir))
