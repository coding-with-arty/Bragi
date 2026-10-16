# src/app_layout.py
from pathlib import Path
from typing import Optional
import flet as ft

from utils.responsive import ResponsiveLayout, DeviceType
from utils.theme_manager import ThemeManager
from storage.progress_repository import ProgressRepository
from views.trainer_view import TrainerView
from views.subviews.ear_training_view import EarTrainingView
from views.subviews.progress_view import ProgressView
from views.components.help_dialog import HelpDialog


class AppLayout(ft.Container):
    """Cross-platform responsive application shell with robust image stack and help button."""

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

        # Resolve asset background path with desktop fallback verification
        assets_dir = Path(__file__).parent.parent / "assets"
        local_bg_file = assets_dir / "bg.png"

        if local_bg_file.exists():
            self.image_path = str(local_bg_file.resolve())
        else:
            self.image_path = "bg.png"

        # Background Image Control
        self.bg_image = ft.Image(
            src=self.image_path,
            fit="cover",
            expand=True,
            width=float("inf"),
            height=float("inf"),
        )

        # Scrim overlay for light/dark mode contrast
        self.scrim_overlay = ft.Container(expand=True)

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

        # Navigation Controls
        self.bottom_nav = ft.NavigationBar(
            selected_index=self.current_index,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.TUNE_ROUNDED, label="Trainer"),
                ft.NavigationBarDestination(icon=ft.Icons.HEARING_ROUNDED, label="Ear Training"),
                ft.NavigationBarDestination(icon=ft.Icons.BAR_CHART_ROUNDED, label="Analytics"),
            ],
            on_change=self._on_navigation_changed,
        )

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

        self.divider = ft.VerticalDivider(width=1)

        # Floating Top-Right Help Button (?)
        self.help_button = ft.Container(
            top=12,
            right=16,
            content=ft.IconButton(
                icon=ft.Icons.QUESTION_MARK_ROUNDED,
                tooltip="App Directions & Help",
                icon_color=ft.Colors.BLACK,
                bgcolor=ft.Colors.AMBER_400,
                on_click=self._open_help_dialog,
            ),
        )

        # Transparent body view container
        self.body_container = ft.Container(
            content=self.views[self.current_index],
            expand=True,
            bgcolor=ft.Colors.TRANSPARENT,
        )

        self.layout_content = ft.Container(expand=True)

        # Build Layered Stack
        self.content = ft.Stack(
            controls=[
                self.bg_image,
                self.scrim_overlay,
                self.layout_content,
                self.help_button,
            ],
            expand=True,
        )

        if hasattr(self.theme_manager, "add_listener"):
            self.theme_manager.add_listener(self.apply_theme)

        self.apply_theme()
        self._build_responsive_layout()

    def apply_theme(self) -> None:
        """Dynamically updates overlay contrast and navigation colors for theme mode."""
        is_dark = self.main_page.theme_mode == ft.ThemeMode.DARK or getattr(
            self.theme_manager, "is_dark", True
        )

        if is_dark:
            nav_bg = ft.Colors.with_opacity(0.85, "#130F1C")
            divider_color = ft.Colors.with_opacity(0.3, "#3E354A")
            scrim_bg = ft.Colors.with_opacity(0.55, "#0B0812")
        else:
            nav_bg = ft.Colors.with_opacity(0.88, "#FFFFFF")
            divider_color = ft.Colors.with_opacity(0.15, "#000000")
            scrim_bg = ft.Colors.with_opacity(0.82, "#F4F4F6")

        self.bottom_nav.bgcolor = nav_bg
        self.side_rail.bgcolor = nav_bg
        self.divider.color = divider_color
        self.scrim_overlay.bgcolor = scrim_bg

        try:
            self.update()
        except Exception:
            pass

    def _build_responsive_layout(self) -> None:
        device = ResponsiveLayout.get_device_type(self.main_page)

        if device == DeviceType.MOBILE:
            self.layout_content.content = ft.Column(
                controls=[
                    self.body_container,
                    self.bottom_nav,
                ],
                expand=True,
                spacing=0,
            )
        else:
            self.layout_content.content = ft.Row(
                controls=[
                    self.side_rail,
                    self.divider,
                    self.body_container,
                ],
                expand=True,
                spacing=0,
            )

        if hasattr(self.trainer_view, "adapt_layout"):
            self.trainer_view.adapt_layout()

    def _open_help_dialog(self, e=None) -> None:
        """Opens modal dialog with universal overlay mounting."""
        dialog = HelpDialog(theme_manager=self.theme_manager)
        if dialog not in self.main_page.overlay:
            self.main_page.overlay.append(dialog)
        self.main_page.dialog = dialog
        dialog.open = True
        self.main_page.update()

    def _on_navigation_changed(self, e) -> None:
        idx = int(e.control.selected_index)
        self.current_index = idx
        self.bottom_nav.selected_index = idx
        self.side_rail.selected_index = idx

        self.body_container.content = self.views[self.current_index]
        self.main_page.update()

        if self.current_index == 2 and hasattr(self.progress_view, "refresh_stats"):
            self.progress_view.refresh_stats()

    def _on_viewport_resized(self, e) -> None:
        self._build_responsive_layout()
        self.main_page.update()
