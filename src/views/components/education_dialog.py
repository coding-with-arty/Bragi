from typing import Optional
import flet as ft
from utils.theme_manager import ThemeManager


class EducationDialog(ft.AlertDialog):
    """
    Pedagogy modal dialog ("Why Learn This?") explaining the musical rationale
    and real-world application of the active practice topic.
    """

    def __init__(
        self,
        title: str,
        concept_overview: str,
        why_learn_this: str,
        real_world_application: str,
        theme_manager: Optional[ThemeManager] = None,
    ):
        self.theme_manager = theme_manager

        dialog_title = ft.Row(
            controls=[
                ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, color=ft.Colors.AMBER_400, size=24),
                ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
            ],
            spacing=10,
        )

        content = ft.Container(
            width=420,
            content=ft.Column(
                tight=True,
                spacing=14,
                controls=[
                    ft.Text(concept_overview, size=13, color=ft.Colors.GREY_300),
                    ft.Divider(height=1, color=ft.Colors.GREY_800),

                    # Why Learn This Section
                    ft.Column(
                        spacing=4,
                        controls=[
                            ft.Text("WHY LEARN THIS?", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                            ft.Text(why_learn_this, size=12, color=ft.Colors.WHITE),
                        ],
                    ),

                    # Real-World Context Section
                    ft.Container(
                        content=ft.Column(
                            spacing=4,
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.MUSIC_NOTE_ROUNDED, size=16, color=ft.Colors.CYAN_400),
                                        ft.Text("Real-World Context", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.CYAN_400),
                                    ],
                                    spacing=6,
                                ),
                                ft.Text(real_world_application, size=11, color=ft.Colors.GREY_300),
                            ],
                        ),
                        bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                        border_radius=8,
                        padding=12,
                    ),
                ],
            ),
        )

        close_btn = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_ROUNDED, size=16, color=ft.Colors.BLACK),
                    ft.Text("Got It", weight=ft.FontWeight.BOLD, size=12, color=ft.Colors.BLACK),
                ],
                tight=True,
                spacing=4,
            ),
            bgcolor=ft.Colors.AMBER_400,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            ink=True,
            on_click=self._close_dialog,
        )

        super().__init__(
            title=dialog_title,
            content=content,
            actions=[close_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _close_dialog(self, e=None) -> None:
        if self.page and hasattr(self.page, "close"):
            try:
                self.page.close(self)
                return
            except Exception:
                pass
        self.open = False
        if self.page:
            self.page.update()
