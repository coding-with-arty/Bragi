import sys
from pathlib import Path

# Add src/ directory to runtime Python path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import flet as ft
from app_layout import AppLayout
from storage.path_utils import get_app_data_dir
from storage.progress_repository import ProgressRepository


def main(page: ft.Page) -> None:
    # Ensure sandboxed application directories exist
    get_app_data_dir()

    # Configure top-level window properties
    page.title = "Bragi - Stringed Instrument Fret Mastery Tool"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0
    page.window.width = 1200
    page.window.height = 1000
    page.window.min_width = 1024
    page.window.min_height = 700

    # Safely center window across sync and async Flet versions
    if hasattr(page, "window_center"):
        page.window_center()

    # Initialize shared repository
    repository = ProgressRepository()

    # Mount top-level application layout shell
    layout = AppLayout(page=page, repository=repository)
    page.add(layout)
    page.update()


if __name__ == "__main__":
    # Launch application using ft.run() or fallback to ft.app()
    if hasattr(ft, "run"):
        ft.run(main)
    elif hasattr(ft, "app"):
        ft.app(target=main)
    else:
        raise RuntimeError("Unable to locate 'run' or 'app' entry point in Flet installation.")
