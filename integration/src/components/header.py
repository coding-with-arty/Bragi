"""
header.py - Header navigation bar[cite: 9].
"""

import flet as ft
from utils.theme_manager import ThemeManager


class Header(ft.Container):
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.padding = ft.Padding.symmetric(horizontal=20, vertical=12)
        self.border_radius = 12

        self.title_text = ft.Text(
            "FretTrain",
            size=24,
            weight=ft.FontWeight.BOLD,
        )
        self.theme_button = ft.IconButton(
            tooltip="Toggle Light/Dark Theme",
            on_click=lambda e: self.theme_manager.toggle_theme(),
        )

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.MUSIC_NOTE, color=ft.Colors.AMBER_400, size=32),
                        self.title_text,
                    ]
                ),
                self.theme_button,
            ]
        )

        self.theme_manager.add_listener(self.apply_theme)
        self.apply_theme()

    def apply_theme(self):
        is_dark = self.theme_manager.is_dark()
        self.bgcolor = ft.Colors.with_opacity(0.5, ft.Colors.BLACK) if is_dark else ft.Colors.with_opacity(0.85, ft.Colors.WHITE)
        self.title_text.color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK
        self.theme_button.icon = ft.Icons.WB_SUNNY_OUTLINED if is_dark else ft.Icons.NIGHTLIGHT_ROUNDED
        self.theme_button.icon_color = ft.Colors.AMBER_300 if is_dark else ft.Colors.DEEP_PURPLE_700
