"""
src/views/components/header.py
==============================
Application header displaying title, navigation links, and theme toggle switch.
"""

from typing import Optional
import flet as ft
from utils.theme_manager import ThemeManager


class Header(ft.Container):
    """Application top header bar with title and theme toggle."""

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.theme_manager = theme_manager

        self.title_text = ft.Text(
            "FRET TRAIN",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.AMBER_400,
        )

        self.subtitle_text = ft.Text(
            "Fretboard & Chord Trainer",
            size=12,
            color=ft.Colors.GREY_400,
        )

        self.theme_icon = ft.IconButton(
            icon=ft.Icons.DARK_MODE_OUTLINED,
            tooltip="Toggle Light/Dark Theme",
            on_click=self._toggle_theme,
        )

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=2,
                    controls=[
                        self.title_text,
                        self.subtitle_text,
                    ],
                ),
                self.theme_icon,
            ],
        )

        self.padding = ft.Padding.symmetric(horizontal=20, vertical=12)
        self.border_radius = 12

        if self.theme_manager:
            self.theme_manager.add_listener(self.apply_theme)
            self.apply_theme()

    def _toggle_theme(self, e):
        if self.theme_manager:
            self.theme_manager.toggle_theme()

    def apply_theme(self) -> None:
        """Applies light/dark theme styling without triggering premature page updates."""
        if not self.theme_manager:
            return
        is_dark = self.theme_manager.is_dark()

        self.bgcolor = "#1A1721" if is_dark else "#F3F0F8"
        self.border = ft.Border.all(1, "#3E354A" if is_dark else "#D0C8DF")
        self.subtitle_text.color = "#C4B5FD" if is_dark else "#5D4B75"
        self.theme_icon.icon = (
            ft.Icons.LIGHT_MODE_OUTLINED if is_dark else ft.Icons.DARK_MODE_OUTLINED
        )
