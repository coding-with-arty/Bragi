"""
src/views/components/hint_drawer.py
===================================
Expandable hint panel displaying CAGED position diagrams, fretboard note maps,
and music theory explanations.
"""

from typing import Optional
import flet as ft
from utils.theme_manager import ThemeManager


class HintDrawer(ft.Container):
    """Drawer container displaying interactive theory and fretboard hints."""

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.theme_manager = theme_manager

        self.title_text = ft.Text("THEORY & CAGED HINTS", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)
        self.explanation_text = ft.Text("Select a chord target to view CAGED fingerings and formula notes.", size=13)

        self.toggle_button = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINED, size=18),
                    ft.Text("Show Hint", size=13, weight=ft.FontWeight.BOLD)
                ],
                tight=True,
            ),
            style=ft.ButtonStyle(
                padding=ft.Padding.symmetric(horizontal=12, vertical=8),
            ),
            on_click=self._toggle_expanded,
        )

        self.details_container = ft.Column(
            controls=[
                self.explanation_text,
            ],
            visible=False,
            spacing=8,
        )

        self.content = ft.Column(
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[self.title_text, self.toggle_button],
                ),
                self.details_container,
            ],
            spacing=8,
        )

        self.padding = 12
        self.border_radius = 10
        self.border = ft.Border.all(1, "#3E354A")

    def _toggle_expanded(self, e):
        self.details_container.visible = not self.details_container.visible
        btn_text = "Hide Hint" if self.details_container.visible else "Show Hint"
        self.toggle_button.content.controls[1].value = btn_text
        if self.page:
            self.page.update()

    def set_hint_text(self, text: str) -> None:
        """Updates the hint explanation body."""
        self.explanation_text.value = text
        if self.page:
            self.page.update()
