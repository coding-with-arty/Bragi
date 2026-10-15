"""
src/views/components/note_display.py
====================================
Visual target widget for single-note pitch training with responsive resizing.
"""

from typing import Optional, Callable
import flet as ft
from utils.theme_manager import ThemeManager
from utils.responsive import ResponsiveLayout


class NoteDisplay(ft.Container):
    """Target display showing requested string number and note to play."""

    def __init__(self, on_next_click: Callable[[], None], theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.on_next_click = on_next_click
        self.theme_manager = theme_manager
        self.alignment = ft.Alignment.CENTER
        self.padding = 10

        self.string_info_text = ft.Text("String 1 (E)", size=18, weight=ft.FontWeight.BOLD)
        self.target_note_text = ft.Text("C", size=56, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)
        self.feedback_text = ft.Text("Play Note", size=15, color=ft.Colors.GREY_400)

        self.progress_bar = ft.ProgressBar(
            value=0.0,
            width=260,
            color=ft.Colors.AMBER_500,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.GREY),
            visible=False,
        )

        self.target_circle = ft.Container(
            width=300,
            height=300,
            shape=ft.BoxShape.CIRCLE,
            border=ft.Border.all(4, ft.Colors.AMBER_400),
            shadow=ft.BoxShadow(
                blur_radius=20,
                color=ft.Colors.with_opacity(0.35, ft.Colors.AMBER_400),
            ),
            alignment=ft.Alignment.CENTER,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    self.string_info_text,
                    self.target_note_text,
                    self.feedback_text,
                ]
            )
        )

        self.next_button = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=22),
                    ft.Text("Next Note", size=16, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=28),
                padding=ft.Padding.symmetric(horizontal=28, vertical=16),
                color=ft.Colors.BLACK,
                bgcolor=ft.Colors.AMBER_400,
            ),
            on_click=lambda e: self.on_next_click(),
        )

        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                self.target_circle,
                ft.Container(height=10),
                self.progress_bar,
                ft.Container(height=10),
                self.next_button,
            ]
        )

        if self.theme_manager:
            self.theme_manager.add_listener(self.apply_theme)
            self.apply_theme()

    def apply_theme(self) -> None:
        """Applies light/dark theme styles without premature updates."""
        if not self.theme_manager:
            return
        is_dark = self.theme_manager.is_dark()
        self.target_circle.bgcolor = (
            ft.Colors.with_opacity(0.35, ft.Colors.BLACK) if is_dark else ft.Colors.with_opacity(0.85, ft.Colors.WHITE)
        )
        self.string_info_text.color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK

    def set_target(self, string_num: int, base_tuning: str, note_name: str) -> None:
        """Updates string target and note name."""
        self.string_info_text.value = f"String {string_num} ({base_tuning})"
        self.target_note_text.value = note_name
        self.feedback_text.value = "Listening..."
        self.feedback_text.color = ft.Colors.GREY_400
        self.target_circle.border = ft.Border.all(4, ft.Colors.AMBER_400)
        if self.page:
            self.page.update()

    def update_pitch_feedback(self, raw_pitch: str, cents: float, is_in_tune: bool) -> None:
        """Updates visual state based on detected pitch."""
        if is_in_tune:
            self.target_circle.border = ft.Border.all(6, ft.Colors.GREEN_ACCENT)
            self.feedback_text.value = f"MATCHED! ({raw_pitch})"
            self.feedback_text.color = ft.Colors.GREEN_ACCENT
        else:
            self.target_circle.border = ft.Border.all(4, ft.Colors.AMBER)
            cents_str = f"+{cents:.0f}c" if cents >= 0 else f"{cents:.0f}c"
            self.feedback_text.value = f"Detected: {raw_pitch} ({cents_str})"
            self.feedback_text.color = ft.Colors.AMBER

        if self.page:
            self.page.update()

    def update_progress(self, progress: float, visible: bool = True) -> None:
        """Updates progress bar."""
        self.progress_bar.visible = visible
        self.progress_bar.value = progress
        if self.page:
            self.page.update()

    def adapt_dimensions(self) -> None:
        """Adapts circle dimensions to active viewport size."""
        if not self.page:
            return
        sz = ResponsiveLayout.get_target_circle_size(self.page)
        self.target_circle.width = sz
        self.target_circle.height = sz

        if sz < 250:
            self.target_note_text.size = 42
            self.string_info_text.size = 15
        else:
            self.target_note_text.size = 56
            self.string_info_text.size = 18

        if self.page:
            self.update()
