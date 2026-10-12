# src/main.py
import sys
from pathlib import Path

# Add src directory dynamically to sys.path for relative imports
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import flet as ft
from utils.theme_manager import ThemeManager
from views.trainer_view import TrainerView


def resolve_flet_app():
    """Dynamically resolves the callable Flet app entry point across Python 3.14 & Flet versions."""
    try:
        if hasattr(ft, "app") and callable(getattr(ft, "app")):
            return getattr(ft, "app")
    except AttributeError:
        pass

    try:
        from flet.flet import app as flet_flet_app
        if callable(flet_flet_app):
            return flet_flet_app
    except (ImportError, AttributeError):
        pass

    try:
        import flet.app as flet_app_module
        if hasattr(flet_app_module, "app") and callable(getattr(flet_app_module, "app")):
            return getattr(flet_app_module, "app")
    except (ImportError, AttributeError):
        pass

    raise AttributeError("Unable to resolve callable 'app' attribute from Flet package.")


def main(page: ft.Page):
    page.title = "FretTrain - Guitar & Bass Note Trainer"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.spacing = 10

    theme_manager = ThemeManager(page)

    bg_container = ft.Container(
        expand=True,
        image_src="/bg.png",
        image_fit=ft.ImageFit.COVER,
        content=TrainerView(page, theme_manager)
    )

    page.add(bg_container)


if __name__ == "__main__":
    assets_dir = ROOT_DIR / "assets"
    app_runner = resolve_flet_app()
    app_runner(target=main, assets_dir=str(assets_dir))
