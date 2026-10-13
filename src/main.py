import sys
from pathlib import Path

# Add src directory dynamically to sys.path
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import flet as ft
from utils.theme_manager import ThemeManager
from views.trainer_view import TrainerView

def main(page: ft.Page):
    page.title = "FretTrain - Guitar & Bass Note Trainer"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.spacing = 10

    theme_manager = ThemeManager(page)

    bg_container = ft.Container(
        expand=True,
        image=ft.DecorationImage(
            src="/bg.png",
            fit=ft.BoxFit.COVER,
        ),
        content=TrainerView(theme_manager)
    )

    page.add(bg_container)

if __name__ == "__main__":
    assets_dir = ROOT_DIR / "assets"
    ft.run(main, assets_dir=str(assets_dir))
