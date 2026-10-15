"""
main.py
=======
Application entry point for FretSense.
Configures page layout, top-level tab navigation, and theme initialization.
"""

import flet as ft
from storage.progress_repository import ProgressRepository
from utils.theme_manager import ThemeManager
from views.trainer_view import TrainerView
from views.subviews.ear_training_view import EarTrainingView
from views.subviews.progress_view import ProgressView


def main(page: ft.Page):
    page.title = "FretSense - Fretboard & Chord Trainer"
    page.padding = 12
    page.theme_mode = ft.ThemeMode.DARK

    # Global state managers & storage
    theme_manager = ThemeManager(page)
    repository = ProgressRepository()

    # Views
    trainer_view = TrainerView(theme_manager=theme_manager)
    ear_training_view = EarTrainingView(theme_manager=theme_manager)
    progress_view = ProgressView(repository=repository, theme_manager=theme_manager)

    # Modern Tab navigation layout using TabBar & TabBarView
    tabs = ft.Tabs(
        length=3,
        selected_index=0,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                ft.TabBar(
                    tabs=[
                        ft.Tab(
                            label="Fretboard Trainer",
                            icon=ft.Icons.MUSIC_NOTE_OUTLINED,
                        ),
                        ft.Tab(
                            label="Ear Training",
                            icon=ft.Icons.GRAPHIC_EQ,
                        ),
                        ft.Tab(
                            label="Analytics & History",
                            icon=ft.Icons.ANALYTICS_OUTLINED,
                        ),
                    ]
                ),
                ft.TabBarView(
                    expand=True,
                    controls=[
                        trainer_view,
                        ear_training_view,
                        progress_view,
                    ],
                ),
            ],
        ),
    )

    page.add(tabs)


if __name__ == "__main__":
    if hasattr(ft, "run"):
        ft.run(main)
    else:
        ft.app(target=main)
