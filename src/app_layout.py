# src/app_layout.py
from typing import Optional
import flet as ft
from utils.responsive import ResponsiveLayout, DeviceType
from utils.theme_manager import ThemeManager
from storage.progress_repository import ProgressRepository
from views.trainer_view import TrainerView
from views.subviews.ear_training_view import EarTrainingView
from views.subviews.progress_view import ProgressView


class AppLayout(ft.Container):
    """Cross-platform responsive application shell with adaptive navigation."""

    def __init__(
        self,
        page: ft.Page,
        theme_manager: Optional[ThemeManager] = None,
        repository: Optional[ProgressRepository] = None,
    ):
        super().__init__()
        self.main_page = page
        self.theme_manager = theme_manager or ThemeManager(page)
        self.repository = repository or ProgressRepository()
        self.expand = True

        # Instantiate Main Application Views
        self.trainer_view = TrainerView(theme_manager=self.theme_manager)
        self.ear_training_view = EarTrainingView(theme_manager=self.theme_manager)
        self.progress_view = ProgressView(
            repository=self.repository, theme_manager=self.theme_manager
        )

        self.views = [self.trainer_view, self.ear_training_view, self.progress_view]
        self.current_index = 0

        # Viewport Resize Listener
        self.main_page.on_resized = self._on_viewport_resized

        # Mobile Bottom Navigation Bar
        self.bottom_nav = ft.NavigationBar(
            selected_index=self.current_index,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.TUNE_ROUNDED, label="Trainer"),
                ft.NavigationBarDestination(icon=ft.Icons.HEARING_ROUNDED, label="Ear Training"),
                ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART_ROUNDED, label="Analytics"),
            ],
            on_change=self._on_navigation_changed,
        )

        # Tablet/Desktop Side Navigation Rail
        self.side_rail = ft.NavigationRail(
            selected_index=self.current_index,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=72,
            min_extended_width=160,
            destinations=[
                ft.NavigationRailDestination(icon=ft.Icons.TUNE_ROUNDED, label="Trainer"),
                ft.NavigationRailDestination(icon=ft.Icons.HEARING_ROUNDED, label="Ear Training"),
                ft.NavigationRailDestination(icon=ft.Icons.BAR_CHART_ROUNDED, label="Analytics"),
            ],
            on_change=self._on_navigation_changed,
        )

        self.body_container = ft.Container(content=self.views[self.current_index], expand=True)
        self._build_responsive_layout()

    def _build_responsive_layout(self) -> None:
        device = ResponsiveLayout.get_device_type(self.main_page)

        if device == DeviceType.MOBILE:
            self.content = ft.Column(
                controls=[
                    self.body_container,
                    self.bottom_nav,
                ],
                expand=True,
                spacing=0,
            )
        else:
            self.content = ft.Row(
                controls=[
                    self.side_rail,
                    ft.VerticalDivider(width=1, color="#3E354A"),
                    self.body_container,
                ],
                expand=True,
                spacing=0,
            )

        if hasattr(self.trainer_view, "adapt_layout"):
            self.trainer_view.adapt_layout()

    def _on_navigation_changed(self, e) -> None:
        idx = int(e.control.selected_index)
        self.current_index = idx
        self.bottom_nav.selected_index = idx
        self.side_rail.selected_index = idx

        self.body_container.content = self.views[self.current_index]

        # Mount selected view to DOM first
        self.main_page.update()

        # Safely trigger view refresh once mounted
        if self.current_index == 2 and hasattr(self.progress_view, "refresh_stats"):
            self.progress_view.refresh_stats()

    def _on_viewport_resized(self, e) -> None:
        self._build_responsive_layout()
        self.main_page.update()
