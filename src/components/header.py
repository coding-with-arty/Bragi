import flet as ft
from utils.theme_manager import ThemeManager

class Header(ft.Container):
    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.padding = ft.Padding.symmetric(horizontal=20, vertical=12)
        self.bgcolor = ft.Colors.with_opacity(0.4, ft.Colors.BLACK)
        self.border_radius = 12

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.MUSIC_NOTE, color=ft.Colors.AMBER_400, size=32),
                        ft.Text(
                            "FretTrain",
                            size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE,
                        ),
                    ]
                ),
                ft.IconButton(
                    icon=ft.Icons.DARK_MODE_OUTLINED,
                    tooltip="Toggle Light/Dark Theme",
                    icon_color=ft.Colors.WHITE,
                    on_click=lambda e: self.theme_manager.toggle_theme(),
                )
            ]
        )
