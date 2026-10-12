# src/components/header.py
import flet as ft
from utils.theme_manager import ThemeManager

class Header(ft.Container):
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.padding = ft.padding.symmetric(horizontal=20, vertical=12)
        self.bgcolor = ft.colors.WITH_OPACITY(0.4, ft.colors.BLACK)
        self.border_radius = 12

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.icons.MUSIC_NOTE, color=ft.colors.AMBER_400, size=32),
                        ft.Text(
                            "FretTrain",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.WHITE,
                        ),
                    ]
                ),
                ft.IconButton(
                    icon=ft.icons.DARK_MODE_OUTLINED,
                    tooltip="Toggle Light/Dark Theme",
                    icon_color=ft.colors.WHITE,
                    on_click=lambda e: self.theme_manager.toggle_theme(),
                )
            ]
        )
