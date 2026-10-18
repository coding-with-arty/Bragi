# src/views/components/chord_display.py
"""
Chord Display Component
=======================
Visual target display for chord identification practice, matched in size
to NoteDisplay with adaptive font scaling to prevent text clipping.
"""

from typing import Optional, Callable, Set
import flet as ft
from models.chord import TargetChord
from utils.music_theory import CHROMATIC_SHARPS
from utils.theme_manager import ThemeManager


class ChordDisplay(ft.Container):
    """Target display badge for Chord Detection mode."""

    def __init__(
        self,
        on_next_click: Optional[Callable[[], None]] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__()
        self.on_next_click = on_next_click
        self.theme_manager = theme_manager

        # Enforce exact height & width matching NoteDisplay
        self.height = 240
        self.width = 240
        self.alignment = ft.Alignment.CENTER

        # Chord Title Text Control with adaptive sizing & wrapping
        self.chord_title = ft.Text(
            "C Major",
            size=22,
            weight=ft.FontWeight.BOLD,
            text_align=ft.TextAlign.CENTER,
            max_lines=2,
            overflow=ft.TextOverflow.ELLIPSIS,
            color=ft.Colors.AMBER_400,
        )

        # Caged Position / Subtitle Tag
        self.position_subtitle = ft.Text(
            "Open Position",
            size=12,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.GREY_400,
            text_align=ft.TextAlign.CENTER,
        )

        # Container for pitch badges (detected chord tones)
        self.badges_row = ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=6,
            wrap=True,
        )

        # Next Button
        self.next_btn = ft.IconButton(
            icon=ft.Icons.SKIP_NEXT_ROUNDED,
            icon_color=ft.Colors.BLACK,
            bgcolor=ft.Colors.AMBER_400,
            tooltip="Next Chord Target",
            on_click=lambda e: self.on_next_click() if self.on_next_click else None,
        )

        # Inner Content Stack/Column inside circular badge
        self.circle_badge = ft.Container(
            width=220,
            height=220,
            border_radius=110,
            border=ft.Border.all(3, ft.Colors.AMBER_400),
            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.AMBER_400),
            padding=16,
            content=ft.Column(
                controls=[
                    self.position_subtitle,
                    self.chord_title,
                    self.badges_row,
                    self.next_btn,
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
            ),
        )

        self.content = self.circle_badge

    def set_target_chord(self, target_chord: TargetChord) -> None:
        """Updates the active target chord display and adjusts font size dynamically."""
        title = target_chord.display_title
        self.chord_title.value = title

        # Dynamically scale font size based on title string length
        if len(title) > 20:
            self.chord_title.size = 16
        elif len(title) > 12:
            self.chord_title.size = 18
        else:
            self.chord_title.size = 22

        if target_chord.required_caged_position != target_chord.required_caged_position.NONE:
            self.position_subtitle.value = target_chord.required_caged_position.value
            self.position_subtitle.visible = True
        else:
            self.position_subtitle.visible = False

        self.render_pitch_badges(set())
        if self.page:
            self.page.update()

    def render_pitch_badges(self, detected_pcs: Set[int]) -> None:
        """Renders small badge tags for detected pitch class tones."""
        badge_controls = []
        for pc in sorted(list(detected_pcs)):
            note_name = CHROMATIC_SHARPS[pc % 12]
            badge = ft.Container(
                content=ft.Text(note_name, size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                bgcolor=ft.Colors.AMBER_400,
                border_radius=10,
                padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            )
            badge_controls.append(badge)

        self.badges_row.controls = badge_controls
        if self.page:
            self.page.update()

    def update_progress(self, progress: float, visible: bool = True) -> None:
        """Optional progress ring update for timer auto-advance."""
        if self.page:
            self.page.update()

    def update_pitch_feedback(self, detected_pcs: Set[int], is_correct: bool) -> None:
        """Highlights badge frame on correct match."""
        if is_correct:
            self.circle_badge.border = ft.Border.all(4, ft.Colors.GREEN_400)
            self.circle_badge.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.GREEN_400)
        if self.page:
            self.page.update()
