"""
src/views/components/help_dialog.py
====================================
Interactive modal dialog providing structured directions and app usage guides.
Version-agnostic control structure for seamless cross-platform execution.
"""

from typing import Optional
import flet as ft
from utils.theme_manager import ThemeManager


class HelpDialog(ft.AlertDialog):
    """Categorized user guide and instructions dialog."""

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        self.theme_manager = theme_manager
        self.active_index = 0

        title = ft.Row(
            controls=[
                ft.Icon(ft.Icons.HELP_OUTLINE_ROUNDED, color=ft.Colors.AMBER_400, size=24),
                ft.Text("Bragi User Guide", size=18, weight=ft.FontWeight.BOLD),
            ],
            spacing=10,
        )

        # Pre-build content guide sections
        self.guides = [
            ("Trainer", ft.Icons.TUNE_ROUNDED, self._build_trainer_guide()),
            ("Ear Training", ft.Icons.HEARING_ROUNDED, self._build_ear_training_guide()),
            ("Instruments", ft.Icons.BUILD_ROUNDED, self._build_instruments_guide()),
            ("Analytics", ft.Icons.BAR_CHART_ROUNDED, self._build_analytics_guide()),
        ]

        # Header Pill Navigation & View Container
        self.tab_buttons_row = ft.Row(spacing=6, scroll=ft.ScrollMode.AUTO)
        self.content_container = ft.Container(
            height=310,
            expand=True,
        )

        self._render_tabs()

        content = ft.Container(
            width=540,
            height=390,
            content=ft.Column(
                controls=[
                    self.tab_buttons_row,
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    self.content_container,
                ],
                spacing=10,
                expand=True,
            ),
        )

        # Version-agnostic action button
        close_button = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.CHECK_ROUNDED, size=18, color=ft.Colors.BLACK),
                    ft.Text("Got it!", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ],
                tight=True,
                spacing=6,
            ),
            bgcolor=ft.Colors.AMBER_400,
            border_radius=8,
            padding=ft.Padding.symmetric(horizontal=16, vertical=10),
            ink=True,
            on_click=self._close_dialog,
        )

        super().__init__(
            title=title,
            content=content,
            actions=[close_button],
            actions_alignment=ft.MainAxisAlignment.END,
        )

    def _render_tabs(self) -> None:
        """Renders version-safe tab pills with active highlight styling."""
        buttons = []
        for idx, (label, icon_data, _) in enumerate(self.guides):
            is_active = idx == self.active_index
            btn = ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Icon(
                            icon_data,
                            size=16,
                            color=ft.Colors.BLACK if is_active else ft.Colors.AMBER_400,
                        ),
                        ft.Text(
                            label,
                            size=12,
                            weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                            color=ft.Colors.BLACK if is_active else ft.Colors.WHITE,
                        ),
                    ],
                    spacing=6,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                bgcolor=ft.Colors.AMBER_400
                if is_active
                else ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                ink=True,
                data=idx,
                on_click=self._on_tab_click,
            )
            buttons.append(btn)

        self.tab_buttons_row.controls = buttons
        self.content_container.content = self.guides[self.active_index][2]

    def _on_tab_click(self, e) -> None:
        self.active_index = e.control.data
        self._render_tabs()
        try:
            self.update()
        except Exception:
            if self.page:
                self.page.update()

    def _build_guide_section(self, title: str, steps: list[tuple[str, str]]) -> ft.Control:
        controls = [
            ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
            ft.Divider(height=1, color=ft.Colors.GREY_800),
        ]
        for header, desc in steps:
            controls.append(
                ft.Column(
                    spacing=2,
                    controls=[
                        ft.Text(f"• {header}", weight=ft.FontWeight.BOLD, size=13),
                        ft.Text(desc, size=12, color=ft.Colors.GREY_300),
                    ],
                )
            )
        return ft.Container(
            padding=8,
            content=ft.Column(controls=controls, spacing=10, scroll=ft.ScrollMode.AUTO),
        )

    def _build_trainer_guide(self) -> ft.Control:
        return self._build_guide_section(
            "Fretboard Trainer & Pitch Recognition",
            [
                (
                    "Microphone Detection",
                    "Click 'Start Listening' to activate real-time pitch detection for your instrument.",
                ),
                (
                    "Single Notes & Chords",
                    "Play single notes or strum full chords. The DSP engine detects note pitch classes and chord qualities automatically.",
                ),
                (
                    "Custom Tuning Sidebar",
                    "Use the left sidebar to tweak per-string notes. Octaves are managed automatically under the hood.",
                ),
                (
                    "Interactive Fretboard",
                    "Click any fret on the screen to highlight notes or hear synthesized audio reference tones.",
                ),
            ],
        )

    def _build_ear_training_guide(self) -> ft.Control:
        return self._build_guide_section(
            "Ear Training Modules",
            [
                (
                    "Exercise Types",
                    "Practice Single Notes, Intervals, Chord Qualities (Major, Minor, Dom7), or Inversions.",
                ),
                (
                    "Acoustic Playback",
                    "Click 'Play Sound' to hear the target note or chord synthesized using realistic string acoustics.",
                ),
                (
                    "Submit Answers",
                    "Select your guess from the choice grid. Instant visual feedback will highlight correct and incorrect notes.",
                ),
                (
                    "Difficulty Adjustment",
                    "Customise accidentals, octave ranges, and chord complexity in the settings header.",
                ),
            ],
        )

    def _build_instruments_guide(self) -> ft.Control:
        return self._build_guide_section(
            "Multi-Instrument & Custom Builder",
            [
                (
                    "Preset Profiles",
                    "Switch seamlessly between Standard Guitar, 7/8 String, Bass, Ukulele, Mandolin, and Banjo.",
                ),
                (
                    "Custom Builder",
                    "Click '+' to create a custom instrument with 1 to 10 strings and assign custom string pitches.",
                ),
                (
                    "Persistence",
                    "Your custom instruments and tunings are saved automatically and remain available across sessions.",
                ),
            ],
        )

    def _build_analytics_guide(self) -> ft.Control:
        return self._build_guide_section(
            "Progress & Gamification",
            [
                (
                    "XP & Daily Streaks",
                    "Earn XP for every correct pitch recognized or ear training challenge completed.",
                ),
                (
                    "Note Mastery Tiers",
                    "Track your accuracy for all 12 chromatic notes from Bronze to Platinum mastery.",
                ),
                (
                    "Daily Challenges",
                    "Complete daily practice goals to maintain your streak and unlock exclusive achievement badges.",
                ),
            ],
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
