"""
note_display.py - Target note visual container with expanded circle size and high-visibility typography.
"""

import flet as ft
from utils.theme_manager import ThemeManager


class NoteDisplay(ft.Container):
    def __init__(self, on_next_click, theme_manager: ThemeManager = None):
        super().__init__()
        self.on_next_click = on_next_click
        self.theme_manager = theme_manager
        self.alignment = ft.Alignment.CENTER
        self.padding = 20

        # Note display text scaled up for larger circle
        self.note_text = ft.Text("?", size=104, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)

        # String text enlarged and set to bold weight
        self.string_text = ft.Text(
            "Press Next to Start",
            size=26,
            weight=ft.FontWeight.BOLD
        )

        self.audio_feedback_text = ft.Text(
            "",
            size=18,
            color=ft.Colors.GREY_400,
        )

        self.progress_bar = ft.ProgressBar(
            value=0.0,
            width=300,
            color=ft.Colors.AMBER_500,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.GREY),
            visible=False,
        )

        # Circle dimensions enlarged from 300x300 -> 380x380
        self.target_circle = ft.Container(
            width=380,
            height=380,
            shape=ft.BoxShape.CIRCLE,
            border=ft.Border.all(4, ft.Colors.AMBER_400),
            shadow=ft.BoxShadow(
                blur_radius=30,
                color=ft.Colors.with_opacity(0.35, ft.Colors.AMBER_400),
            ),
            alignment=ft.Alignment.CENTER,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=4,
                controls=[
                    self.string_text,
                    self.note_text,
                    self.audio_feedback_text,
                ]
            )
        )

        self.next_button = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=24),
                    ft.Text("Next Note", size=18, weight=ft.FontWeight.BOLD)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                tight=True,
            ),
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=30),
                padding=ft.Padding.symmetric(horizontal=36, vertical=20),
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
                ft.Container(height=16),
                self.progress_bar,
                ft.Container(height=16),
                self.next_button,
            ]
        )

        if self.theme_manager:
            self.theme_manager.add_listener(self.apply_theme)
            self.apply_theme()

    def apply_theme(self):
        if not self.theme_manager:
            return
        is_dark = self.theme_manager.is_dark()
        self.target_circle.bgcolor = ft.Colors.with_opacity(0.35, ft.Colors.BLACK) if is_dark else ft.Colors.with_opacity(0.85, ft.Colors.WHITE)

        # High-contrast solid text color for maximum legibility
        self.string_text.color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK

    def set_target(self, string_num: int, tuning: str, note: str):
        self.note_text.value = note
        self.string_text.value = f"String {string_num} ({tuning})"
        self.reset_circle_visuals()
        if self.page:
            self.page.update()

    def update_pitch_feedback(self, raw_str: str, cents: float, is_in_tune: bool):
        if is_in_tune:
            self.target_circle.border = ft.Border.all(6, ft.Colors.GREEN_ACCENT)
            self.target_circle.shadow = ft.BoxShadow(blur_radius=30, color=ft.Colors.GREEN_ACCENT)
            self.audio_feedback_text.value = "CORRECT!"
            self.audio_feedback_text.color = ft.Colors.GREEN_ACCENT
        else:
            self.target_circle.border = ft.Border.all(4, ft.Colors.AMBER)
            self.target_circle.shadow = ft.BoxShadow(blur_radius=20, color=ft.Colors.AMBER)
            self.audio_feedback_text.value = f"Detected: {raw_str} ({cents:+.0f}c)"
            self.audio_feedback_text.color = ft.Colors.AMBER
        if self.page:
            self.page.update()

    def reset_circle_visuals(self):
        self.target_circle.border = ft.Border.all(4, ft.Colors.AMBER_400)
        self.target_circle.shadow = ft.BoxShadow(
            blur_radius=30,
            color=ft.Colors.with_opacity(0.35, ft.Colors.AMBER_400),
        )
        self.audio_feedback_text.value = ""

    def update_progress(self, progress: float, visible: bool = True):
        self.progress_bar.visible = visible
        self.progress_bar.value = progress
        if self.page:
            self.page.update()
