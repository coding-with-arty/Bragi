# src/views/components/chord_display.py
"""
Chord Display Component
=======================
Visual target widget for chord identification training, styled identically
to NoteDisplay with dynamic title font scaling and pitch badge indicators.
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
        self.padding = 10

        self.current_target: Optional[TargetChord] = None

        # Typography matching NoteDisplay sizing hierarchy
        self.subtitle_text = ft.Text("Target Chord", size=15, weight=ft.FontWeight.BOLD)
        self.chord_title_text = ft.Text("Select Mode", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)
        self.audio_feedback_text = ft.Text("Play Chord", size=14, color=ft.Colors.GREY_400)

        # Container for pitch badges
        self.pitch_badges_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
            wrap=True,
            controls=[]
        )

        # Progress bar matching NoteDisplay (width 260px)
        self.progress_bar = ft.ProgressBar(
            value=0.0,
            width=260,
            color=ft.Colors.AMBER_500,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.GREY),
            visible=False,
        )

        # Target Circle matching NoteDisplay (300x300px)
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
                    self.subtitle_text,
                    self.chord_title_text,
                    self.pitch_badges_row,
                    self.audio_feedback_text,
                ]
            )
        )

        # Next Button matching NoteDisplay styling
        self.next_button = ft.Button(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.PLAY_ARROW_ROUNDED, size=22),
                    ft.Text("Next Chord", size=16, weight=ft.FontWeight.BOLD)
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
        """Applies light/dark theme styles."""
        if not self.theme_manager:
            return
        is_dark = self.theme_manager.is_dark()
        self.target_circle.bgcolor = (
            ft.Colors.with_opacity(0.35, ft.Colors.BLACK) if is_dark else ft.Colors.with_opacity(0.85, ft.Colors.WHITE)
        )
        self.subtitle_text.color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK

    def set_target_chord(self, target: TargetChord) -> None:
        """Updates display for new target chord with dynamic font scaling."""
        self.current_target = target
        name = target.chord_definition.name
        self.chord_title_text.value = name

        # Adapt font size to prevent text overflow inside 300px circle
        if len(name) > 16:
            self.chord_title_text.size = 22
        elif len(name) > 10:
            self.chord_title_text.size = 26
        else:
            self.chord_title_text.size = 32

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
        """Renders pitch class badges for required chord tones."""
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
                    size=12,
                    weight=ft.FontWeight.BOLD,
                    color=text_color
                ),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
                border_radius=12,
                bgcolor=bg_color,
                animate=ft.Animation(150, ft.AnimationCurve.EASE_IN_OUT),
            )
            controls.append(badge)

        self.pitch_badges_row.controls = controls
        if self.page:
            self.page.update()

    def update_pitch_feedback(self, detected_pcs: Set[int], is_correct: bool) -> None:
        """Updates borders and text on chord match."""
        self.render_pitch_badges(detected_pcs)

        if is_correct:
            self.target_circle.border = ft.Border.all(6, ft.Colors.GREEN_ACCENT)
            self.target_circle.shadow = ft.BoxShadow(blur_radius=20, color=ft.Colors.GREEN_ACCENT)
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
        """Resets default circle styling."""
        self.target_circle.border = ft.Border.all(4, ft.Colors.AMBER_400)
        self.target_circle.shadow = ft.BoxShadow(
            blur_radius=20,
            color=ft.Colors.with_opacity(0.35, ft.Colors.AMBER_400),
        )
        self.audio_feedback_text.value = "Listening..."
        self.audio_feedback_text.color = ft.Colors.GREY_400

    def update_progress(self, progress: float, visible: bool = True) -> None:
        """Updates timer progress bar."""
        self.progress_bar.visible = visible
        self.progress_bar.value = progress
        if self.page:
            self.page.update()
