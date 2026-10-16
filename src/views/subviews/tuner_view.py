"""
src/views/subviews/tuner_view.py
================================
Real-time Chromatic Tuner Subview binding directly to global AudioManager
events for pitch detection, frequency readout (Hz), cents error needle, and string status.
"""

import asyncio
import math
from typing import Optional
import flet as ft

from services.audio_manager import AudioManager
from utils.theme_manager import ThemeManager

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


class TunerView(ft.Container):
    """Real-time Chromatic Tuner visualizer fed by central AudioManager pitch events."""

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.theme_manager = theme_manager
        self.expand = True
        self.padding = ft.Padding.all(20)
        self._is_mounted = False

        # Tuner UI Elements
        self.note_text = ft.Text(
            "--",
            size=72,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
            text_align=ft.TextAlign.CENTER,
        )

        self.freq_text = ft.Text(
            "0.0 Hz",
            size=18,
            color=ft.Colors.GREY_400,
            weight=ft.FontWeight.W_500,
        )

        self.status_badge = ft.Container(
            content=ft.Text(
                "NO SOUND DETECTED",
                size=12,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREY_400,
            ),
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.GREY_700),
            border_radius=16,
            padding=ft.Padding.symmetric(horizontal=16, vertical=6),
        )

        # Cents Offset Meter (-50 to +50)
        self.cents_text = ft.Text("0 cents", size=14, color=ft.Colors.GREY_400)
        self.cents_progress = ft.ProgressBar(value=0.5, color=ft.Colors.AMBER_400, height=8)

        # Visual Tuning Gauge Container
        self.gauge_container = ft.Container(
            width=360,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("-50", size=11, color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD),
                            ft.Text("FLAT", size=10, color=ft.Colors.GREY_500),
                            ft.Text("IN TUNE", size=10, color=ft.Colors.GREEN_400, weight=ft.FontWeight.BOLD),
                            ft.Text("SHARP", size=10, color=ft.Colors.GREY_500),
                            ft.Text("+50", size=11, color=ft.Colors.RED_400, weight=ft.FontWeight.BOLD),
                        ],
                    ),
                    self.cents_progress,
                    self.cents_text,
                ],
            ),
            bgcolor=ft.Colors.with_opacity(0.12, "#130F1C"),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.25, "#3E354A")),
            border_radius=16,
            padding=18,
        )

        # Target Reference Strings (Standard EADGBE)
        standard_strings = [
            ("E2", "82.4 Hz"),
            ("A2", "110.0 Hz"),
            ("D3", "146.8 Hz"),
            ("G3", "196.0 Hz"),
            ("B3", "246.9 Hz"),
            ("E4", "329.6 Hz"),
        ]
        string_badges = [
            ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    controls=[
                        ft.Text(note, size=13, weight=ft.FontWeight.BOLD),
                        ft.Text(hz, size=9, color=ft.Colors.GREY_400),
                    ],
                ),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            )
            for note, hz in standard_strings
        ]

        self.string_reference_row = ft.Row(
            controls=string_badges,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=8,
        )

        self.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Text("Chromatic Tuner", size=22, weight=ft.FontWeight.BOLD),
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            self.note_text,
                            self.freq_text,
                            self.status_badge,
                        ],
                    ),
                    padding=20,
                ),
                self.gauge_container,
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.2, "#3E354A")),
                ft.Text("Standard Reference Pitches", size=12, color=ft.Colors.GREY_400),
                self.string_reference_row,
            ],
        )

    def did_mount(self):
        """Lifecycle hook: Launches active asyncio UI update loop on Flet's event loop."""
        self._is_mounted = True
        am = AudioManager.get_instance()
        am.start_listening()
        asyncio.create_task(self._live_ui_loop())

    def will_unmount(self):
        """Lifecycle hook: Stops continuous UI loop when navigating away."""
        self._is_mounted = False

    async def _live_ui_loop(self):
        """Continuous asyncio loop running on Flet's main event loop (~25 FPS)."""
        am = AudioManager.get_instance()
        while self._is_mounted:
            state = am.current_state
            self._render_state(state)
            if self.page:
                try:
                    self.update()
                except Exception:
                    pass
            await asyncio.sleep(0.04)

    def _render_state(self, data: dict):
        """Updates internal UI control values based on latest pitch state."""
        pitch_class = data.get("pitch_class", "--")
        freq = data.get("frequency", 0.0)
        cents = data.get("cents_deviation", 0.0)
        octave = data.get("octave", 0)

        if pitch_class == "--" or freq <= 20.0:
            self.note_text.value = "--"
            self.freq_text.value = "0.0 Hz"
            self.status_badge.content.value = "NO SOUND DETECTED"
            self.status_badge.bgcolor = ft.Colors.with_opacity(0.15, ft.Colors.GREY_700)
            self.status_badge.content.color = ft.Colors.GREY_400
            self.cents_progress.value = 0.5
            self.cents_progress.color = ft.Colors.GREY_600
            self.cents_text.value = "0 cents"
        else:
            cents_clamped = max(-50.0, min(50.0, cents))
            norm_progress = (cents_clamped + 50.0) / 100.0
            is_in_tune = data.get("is_in_tune", abs(cents_clamped) <= 10.0)

            self.note_text.value = f"{pitch_class}{octave}"
            self.freq_text.value = f"{freq:.1f} Hz"
            self.cents_text.value = f"{cents_clamped:+.1f} cents"
            self.cents_progress.value = norm_progress

            if is_in_tune:
                self.status_badge.content.value = "IN TUNE"
                self.status_badge.bgcolor = ft.Colors.GREEN_400
                self.status_badge.content.color = ft.Colors.BLACK
                self.cents_progress.color = ft.Colors.GREEN_400
                self.note_text.color = ft.Colors.GREEN_400
            elif cents_clamped < 0:
                self.status_badge.content.value = "FLAT (TOO LOW)"
                self.status_badge.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.AMBER_400)
                self.status_badge.content.color = ft.Colors.AMBER_400
                self.cents_progress.color = ft.Colors.AMBER_400
                self.note_text.color = ft.Colors.WHITE
            else:
                self.status_badge.content.value = "SHARP (TOO HIGH)"
                self.status_badge.bgcolor = ft.Colors.with_opacity(0.2, ft.Colors.RED_400)
                self.status_badge.content.color = ft.Colors.RED_400
                self.cents_progress.color = ft.Colors.RED_400
                self.note_text.color = ft.Colors.WHITE
