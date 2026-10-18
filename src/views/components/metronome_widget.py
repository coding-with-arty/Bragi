# src/views/components/metronome_widget.py
"""
Metronome Widget
================
Interactive Flet UI component for metronome tempo adjustments,
time signature selection, play/pause toggling, and visual beat flashing.
"""

from typing import Optional
import flet as ft
from controllers.metronome_controller import MetronomeController
from utils.theme_manager import ThemeManager


class MetronomeWidget(ft.Container):
    """Compact UI control panel for the MetronomeController subsystem."""

    def __init__(
        self,
        metronome_controller: Optional[MetronomeController] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__()
        self.controller = metronome_controller or MetronomeController()
        self.theme_manager = theme_manager

        # Attach beat callback to trigger visual indicator updates
        self.controller.on_beat = self._on_beat_pulse

        self.padding = 12
        self.border_radius = 12
        self.bgcolor = ft.Colors.with_opacity(0.15, "#130F1C")
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.2, "#3E354A"))

        # Visual Beat Flasher Light
        self.beat_light = ft.Container(
            width=16,
            height=16,
            border_radius=8,
            bgcolor=ft.Colors.GREY_700,
            alignment=ft.Alignment.CENTER,
        )

        # Tempo Readout Text
        self.bpm_text = ft.Text(
            f"{self.controller.bpm} BPM",
            size=16,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.AMBER_400,
        )

        # Play / Pause Toggle Button
        self.play_button = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW_ROUNDED,
            icon_color=ft.Colors.BLACK,
            bgcolor=ft.Colors.AMBER_400,
            tooltip="Toggle Metronome",
            on_click=self._toggle_metronome,
        )

        # Tempo Adjustment Controls (-5, -1, +1, +5)
        self.tempo_controls = ft.Row(
            spacing=4,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.REMOVE_ROUNDED,
                    icon_size=16,
                    tooltip="Decrease BPM",
                    on_click=lambda e: self._adjust_bpm(-5),
                ),
                self.bpm_text,
                ft.IconButton(
                    icon=ft.Icons.ADD_ROUNDED,
                    icon_size=16,
                    tooltip="Increase BPM",
                    on_click=lambda e: self._adjust_bpm(+5),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Time Signature Selector
        self.time_sig_dropdown = ft.Dropdown(
            value=str(self.controller.time_signature_beats),
            options=[
                ft.DropdownOption("2", "2/4"),
                ft.DropdownOption("3", "3/4"),
                ft.DropdownOption("4", "4/4"),
                ft.DropdownOption("6", "6/8"),
            ],
            width=90,
            dense=True,
            on_select=self._on_time_sig_changed,
        )

        self.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Row(
                    controls=[
                        self.play_button,
                        self.beat_light,
                        ft.Text("Metronome", weight=ft.FontWeight.BOLD, size=13),
                    ],
                    spacing=10,
                ),
                self.tempo_controls,
                self.time_sig_dropdown,
            ],
        )

    def _toggle_metronome(self, e=None) -> None:
        is_running = self.controller.toggle()
        self.play_button.icon = (
            ft.Icons.PAUSE_ROUNDED if is_running else ft.Icons.PLAY_ARROW_ROUNDED
        )
        self.play_button.bgcolor = (
            ft.Colors.GREEN_400 if is_running else ft.Colors.AMBER_400
        )
        if self.page:
            self.page.update()

    def _adjust_bpm(self, delta: int) -> None:
        new_bpm = self.controller.bpm + delta
        self.controller.set_bpm(new_bpm)
        self.bpm_text.value = f"{self.controller.bpm} BPM"
        if self.page:
            self.page.update()

    def _on_time_sig_changed(self, e) -> None:
        beats = int(self.time_sig_dropdown.value)
        self.controller.set_time_signature(beats)

    def _on_beat_pulse(self, beat_num: int, is_accent: bool) -> None:
        """Flashes the visual beat light on beat pulses."""
        if is_accent:
            self.beat_light.bgcolor = ft.Colors.AMBER_400
        else:
            self.beat_light.bgcolor = ft.Colors.CYAN_400

        if self.page:
            try:
                self.page.update()
            except Exception:
                pass

    def will_unmount(self):
        """Lifecycle hook: Ensures background audio metronome thread stops when view unmounts."""
        self.controller.stop()
