# src/app_layout.py
"""
src/app_layout.py
=================
Main application navigation scaffold managing Material Design 3 tab routing,
theme state synchronization, and audio worker lifecycle teardown.
"""

import flet as ft
from storage.progress_repository import ProgressRepository
from utils.theme_manager import ThemeManager
from views.trainer_view import TrainerView
from views.subviews.ear_training_view import EarTrainingView
from views.subviews.progress_view import ProgressView


class AppLayout(ft.Container):
    """Encapsulates top-level tab views, theme state, and child view instances."""

    def __init__(self, app_page: ft.Page):
        super().__init__()
        self.app_page = app_page
        self.expand = True

        # Core State & Repositories
        self.theme_manager = ThemeManager(self.app_page)
        self.repository = ProgressRepository()

        # Instantiate Primary Views
        self.trainer_view = TrainerView(theme_manager=self.theme_manager)
        self.ear_training_view = EarTrainingView(theme_manager=self.theme_manager)
        self.progress_view = ProgressView(
            repository=self.repository,
            theme_manager=self.theme_manager
        )

        # Build Navigation UI
        self.tabs = ft.Tabs(
            length=3,
            selected_index=0,
            expand=True,
            on_change=self._on_tab_changed,
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
                            self.trainer_view,
                            self.ear_training_view,
                            self.progress_view,
                        ],
                    ),
                ],
            ),
        )

        self.content = self.tabs

    def _on_tab_changed(self, e):
        """Triggers data refreshes when navigating to specific subviews."""
        if self.tabs.selected_index == 2:
            self.progress_view.refresh_stats()

    def clean_up(self):
        """Safely terminates audio DSP threads upon window closure or app exit."""
        if hasattr(self.trainer_view, "will_unmount"):
            self.trainer_view.will_unmount()
