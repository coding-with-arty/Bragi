"""
src/views/components/chord_display.py
=====================================
Target chord visualization component with real-time pitch-class completion badges,
CAGED position tags, timer progress bar, and next button.
"""

from typing import Set, Optional, Callable
import flet as ft
from models.chord import TargetChord
from utils.music_theory import MusicTheory
from utils.theme_manager import ThemeManager


class ChordDisplay(ft.Container):
    """Visual widget displaying target chord, pitch-class badges, and audio status."""

    def __init__(self, on_next_click: Callable[[], None], theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.on_next_click = on_next_click
        self.theme_manager = theme_manager
        self.alignment = ft.Alignment.CENTER
        self.padding = 20

        self.current_target: Optional[TargetChord] = None

        self.chord_title_text = ft.Text("Select Mode", size=64, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)
        self.subtitle_text = ft.Text("Press Next Chord to Start", size=22, weight=ft.FontWeight.BOLD)
        self.audio_feedback_text = ft.Text("", size=18, color=ft.Colors.GREY_400)

        self.pitch_badges_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
            wrap=True,
            controls=[]
        )

        self.progress_bar = ft.ProgressBar(
            value=0.0,
            width=320,
            color=ft.Colors.AMBER_500,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.GREY),
            visible=False,
        )

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
                spacing=8,
                controls=[
                    self.subtitle_text,
                    self.chord_title_text,
                    self.pitch_badges_row,
                    self.audio_feedback_text,
                ]
            )
        )

        self.next_button = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=24),
                    ft.Text("Next Chord", size=18, weight=ft.FontWeight.BOLD)
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

    def apply_theme(self) -> None:
        """Applies light/dark theme styles without premature updates."""
        if not self.theme_manager:
            return
        is_dark = self.theme_manager.is_dark()
        self.target_circle.bgcolor = (
            ft.Colors.with_opacity(0.35, ft.Colors.BLACK) if is_dark else ft.Colors.with_opacity(0.85, ft.Colors.WHITE)
        )
        self.subtitle_text.color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK

    def set_target_chord(self, target: TargetChord) -> None:
        """Updates the visual state for a new target chord."""
        self.current_target = target
        self.chord_title_text.value = target.chord_definition.name
        self.subtitle_text.value = (
            f"Position: {target.required_caged_position.value}"
            if target.required_caged_position != target.required_caged_position.NONE
            else "Target Chord"
        )
        self.reset_visuals()
        self.render_pitch_badges(set())

        if self.page:
            self.page.update()

    def render_pitch_badges(self, detected_pcs: Set[int]) -> None:
        """Renders pitch-class status badges showing required chord tones and highlighting detected ones."""
        if self.current_target is None:
            return

        required_pcs = self.current_target.chord_definition.pitch_classes
        controls = []

        for pc in sorted(required_pcs):
            note_name = MusicTheory.pitch_class_to_note(pc)
            is_detected = pc in detected_pcs

            bg_color = ft.Colors.GREEN_600 if is_detected else ft.Colors.AMBER_800
            text_color = ft.Colors.WHITE

            badge = ft.Container(
                content=ft.Text(
                    note_name,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=text_color
                ),
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                border_radius=16,
                bgcolor=bg_color,
                animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            )
            controls.append(badge)

        self.pitch_badges_row.controls = controls
        if self.page:
            self.page.update()

    def update_pitch_feedback(self, detected_pcs: Set[int], is_correct: bool) -> None:
        """Updates circle borders and pitch badges based on detected pitch class set."""
        self.render_pitch_badges(detected_pcs)

        if is_correct:
            self.target_circle.border = ft.Border.all(6, ft.Colors.GREEN_ACCENT)
            self.target_circle.shadow = ft.BoxShadow(blur_radius=30, color=ft.Colors.GREEN_ACCENT)
            self.audio_feedback_text.value = "CHORD MATCHED!"
            self.audio_feedback_text.color = ft.Colors.GREEN_ACCENT
        else:
            self.target_circle.border = ft.Border.all(4, ft.Colors.AMBER)
            self.target_circle.shadow = ft.BoxShadow(blur_radius=20, color=ft.Colors.AMBER)
            self.audio_feedback_text.value = f"Listening... ({len(detected_pcs)} tones active)"
            self.audio_feedback_text.color = ft.Colors.AMBER

        if self.page:
            self.page.update()

    def reset_visuals(self) -> None:
        """Resets target circle styling."""
        self.target_circle.border = ft.Border.all(4, ft.Colors.AMBER_400)
        self.target_circle.shadow = ft.BoxShadow(
            blur_radius=30,
            color=ft.Colors.with_opacity(0.35, ft.Colors.AMBER_400),
        )
        self.audio_feedback_text.value = ""

    def update_progress(self, progress: float, visible: bool = True) -> None:
        """Updates timer progress bar."""
        self.progress_bar.visible = visible
        self.progress_bar.value = progress
        if self.page:
            self.page.update()
