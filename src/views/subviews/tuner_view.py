"""
src/views/subviews/tuner_view.py
================================
Interactive Chromatic Instrument Tuner with Cents Deviation Needle Gauge,
Frequency readout, Signal Stability metrics, and String Preset targets.
"""

import math
from typing import Optional
import flet as ft
from services.audio_manager import AudioManager
from utils.theme_manager import ThemeManager


class TunerView(ft.Container):
    """Chromatic Instrument Tuner view connected to the shared Audio Manager."""

    def __init__(self, theme_manager: Optional[ThemeManager] = None):
        super().__init__()
        self.theme_manager = theme_manager
        self.audio_manager = AudioManager.get_instance()
        self.expand = True
        self.padding = ft.Padding.all(16)

        # Active Tuning Mode
        self.current_mode = "Guitar"
        self.modes = {
            "Guitar": [("E2", 82.4), ("A2", 110.0), ("D3", 146.8), ("G3", 196.0), ("B3", 246.9), ("E4", 329.6)],
            "Bass": [("E1", 41.2), ("A1", 55.0), ("D2", 73.4), ("G2", 98.0)],
            "Ukulele": [("G4", 392.0), ("C4", 261.6), ("E4", 329.6), ("A4", 440.0)],
            "Chromatic": [],
        }

        # Header Mode Selectors
        self.mode_row = ft.Row(spacing=8, alignment=ft.MainAxisAlignment.CENTER)

        # Display Readouts
        self.pitch_text = ft.Text("--", size=64, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE)
        self.freq_text = ft.Text("0.0 Hz", size=16, color=ft.Colors.GREY_400)
        self.status_text = ft.Text("START LISTENING TO TUNE", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500)

        # Cents Gauge Controls
        self.cents_indicator_bar = ft.Container(
            width=6,
            height=32,
            bgcolor=ft.Colors.GREY_600,
            border_radius=3,
        )
        self.gauge_container = ft.Container(
            content=ft.Stack(
                controls=[
                    # Center Line (In-Tune Target)
                    ft.Container(
                        left=147,
                        top=0,
                        width=6,
                        height=40,
                        bgcolor=ft.Colors.GREEN_400,
                        border_radius=3,
                    ),
                    self.cents_indicator_bar,
                ],
            ),
            width=300,
            height=40,
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            border_radius=8,
            border=ft.Border.all(1, ft.Colors.with_opacity(0.2, "#3E354A")),
        )

        self.cents_text = ft.Text("0.0 Cents", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400)
        self.confidence_progress = ft.ProgressBar(value=0.0, color=ft.Colors.AMBER_400, height=6)

        # Target String Buttons
        self.string_targets_row = ft.Row(spacing=8, alignment=ft.MainAxisAlignment.CENTER)

        # Audio Toggle Button
        self.listen_button = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.MIC_ROUNDED, size=20, color=ft.Colors.BLACK),
                    ft.Text("Start Listening", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ],
                tight=True,
                spacing=8,
            ),
            bgcolor=ft.Colors.AMBER_400,
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=24, vertical=12),
            ink=True,
            on_click=self._toggle_listening,
        )

        # Assemble View Card
        self.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                self.mode_row,
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=12,
                        controls=[
                            self.pitch_text,
                            self.freq_text,
                            self.status_text,
                            self.gauge_container,
                            self.cents_text,
                            ft.Container(width=200, content=self.confidence_progress),
                        ],
                    ),
                    bgcolor=ft.Colors.with_opacity(0.25, "#130F1C"),
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.2, "#3E354A")),
                    border_radius=16,
                    padding=24,
                    width=380,
                ),
                self.string_targets_row,
                self.listen_button,
            ],
        )

        self._render_mode_pills()
        self._render_string_targets()

    def did_mount(self) -> None:
        self.audio_manager.subscribe(self._on_audio_update)
        if not self.audio_manager.is_listening:
            self.audio_manager.start_listening()
        self.listen_button.content.controls[1].value = "Stop Listening"
        self.listen_button.bgcolor = ft.Colors.RED_400
        try:
            self.update()
        except Exception:
            pass

    def will_unmount(self) -> None:
        self.audio_manager.unsubscribe(self._on_audio_update)

    def _render_mode_pills(self) -> None:
        pills = []
        for mode in self.modes.keys():
            active = mode == self.current_mode
            btn = ft.Container(
                content=ft.Text(
                    mode,
                    size=12,
                    weight=ft.FontWeight.BOLD if active else ft.FontWeight.NORMAL,
                    color=ft.Colors.BLACK if active else ft.Colors.WHITE,
                ),
                bgcolor=ft.Colors.AMBER_400 if active else ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                ink=True,
                data=mode,
                on_click=self._on_mode_selected,
            )
            pills.append(btn)
        self.mode_row.controls = pills

    def _render_string_targets(self) -> None:
        targets = self.modes.get(self.current_mode, [])
        controls = []
        for note, freq in targets:
            btn = ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    controls=[
                        ft.Text(note, weight=ft.FontWeight.BOLD, size=13, color=ft.Colors.WHITE),
                        ft.Text(f"{freq:.0f}Hz", size=10, color=ft.Colors.GREY_400),
                    ],
                ),
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                border_radius=8,
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
            )
            controls.append(btn)
        self.string_targets_row.controls = controls

    def _on_mode_selected(self, e) -> None:
        self.current_mode = e.control.data
        self._render_mode_pills()
        self._render_string_targets()
        try:
            self.update()
        except Exception:
            pass

    def _toggle_listening(self, e) -> None:
        if self.audio_manager.is_listening:
            self.audio_manager.stop_listening()
            self.listen_button.content.controls[1].value = "Start Listening"
            self.listen_button.bgcolor = ft.Colors.AMBER_400
        else:
            self.audio_manager.start_listening()
            self.listen_button.content.controls[1].value = "Stop Listening"
            self.listen_button.bgcolor = ft.Colors.RED_400

        try:
            self.update()
        except Exception:
            pass

    def _on_audio_update(self, data: dict) -> None:
        """Processes live audio payloads and updates needle position and color state."""
        note = data.get("pitch_class", "--")
        octave = data.get("octave", 0)
        freq = data.get("frequency", 0.0)
        cents = data.get("cents_deviation", 0.0)
        confidence = data.get("confidence", 0.0)
        direction = data.get("direction", "NO SIGNAL")

        if note != "--":
            self.pitch_text.value = f"{note}{octave}"
            self.freq_text.value = f"{freq:.1f} Hz"
            self.cents_text.value = f"{cents:+.1f} Cents"
            self.confidence_progress.value = min(1.0, max(0.0, confidence))

            abs_cents = abs(cents)
            if abs_cents <= 5.0:
                color = ft.Colors.GREEN_400
            elif abs_cents <= 20.0:
                color = ft.Colors.AMBER_400
            else:
                color = ft.Colors.RED_400

            self.pitch_text.color = color
            self.status_text.value = direction
            self.status_text.color = color
            self.cents_indicator_bar.bgcolor = color

            clamped_cents = max(-50.0, min(50.0, cents))
            left_pos = 147 + (clamped_cents / 50.0) * 140
            self.cents_indicator_bar.left = left_pos
        else:
            self.pitch_text.value = "--"
            self.pitch_text.color = ft.Colors.WHITE
            self.freq_text.value = "0.0 Hz"
            self.cents_text.value = "0.0 Cents"
            self.status_text.value = "NO SIGNAL DETECTED" if self.audio_manager.is_listening else "START LISTENING TO TUNE"
            self.status_text.color = ft.Colors.GREY_500
            self.cents_indicator_bar.bgcolor = ft.Colors.GREY_600
            self.cents_indicator_bar.left = 147
            self.confidence_progress.value = 0.0

        try:
            self.update()
        except Exception:
            pass
