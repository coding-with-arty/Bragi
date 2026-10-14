"""
src/views/components/filter_panel.py
====================================
Sidebar control panel for setting training mode, chord filters, key selections,
and validation strictness.
"""

from typing import Callable, Optional
import flet as ft
from models.settings import TrainerSettings, DetectionMode, ValidationMode
from models.chord import ChordQuality
from utils.theme_manager import ThemeManager


class FilterPanel(ft.Container):
    """Sidebar configuration panel for chord filtering and training options."""

    def __init__(
        self,
        settings: TrainerSettings,
        on_settings_changed: Callable[[TrainerSettings], None],
        theme_manager: Optional[ThemeManager] = None
    ):
        super().__init__()
        self.settings = settings
        self.on_settings_changed = on_settings_changed
        self.theme_manager = theme_manager

        self.title_text = ft.Text("TRAINING & CHORD FILTERS", size=13, weight=ft.FontWeight.BOLD)

        self.detection_mode_dropdown = ft.Dropdown(
            label="Practice Mode",
            options=[
                ft.DropdownOption(key=DetectionMode.NOTE_DETECTION.value, text="Single Note Training"),
                ft.DropdownOption(key=DetectionMode.CHORD_DETECTION.value, text="Chord Training"),
            ],
            value=self.settings.detection_mode.value,
            expand=True,
            on_select=self._on_detection_mode_changed,
        )

        self.major_chk = ft.Checkbox(
            label="Major Triads",
            value=ChordQuality.MAJOR in self.settings.chord_filters.qualities,
            fill_color=ft.Colors.AMBER_400,
            on_change=self._on_quality_changed
        )
        self.minor_chk = ft.Checkbox(
            label="Minor Triads",
            value=ChordQuality.MINOR in self.settings.chord_filters.qualities,
            fill_color=ft.Colors.AMBER_400,
            on_change=self._on_quality_changed
        )
        self.dom7_chk = ft.Checkbox(
            label="Dominant 7th",
            value=ChordQuality.DOMINANT_7TH in self.settings.chord_filters.qualities,
            fill_color=ft.Colors.AMBER_400,
            on_change=self._on_quality_changed
        )
        self.maj7_chk = ft.Checkbox(
            label="Major 7th",
            value=ChordQuality.MAJOR_7TH in self.settings.chord_filters.qualities,
            fill_color=ft.Colors.AMBER_400,
            on_change=self._on_quality_changed
        )

        self.validation_dropdown = ft.Dropdown(
            label="Chord Recognition Engine",
            options=[
                ft.DropdownOption(
                    key=ValidationMode.RELAXED_PITCH_CLASS.value,
                    text="Relaxed (Strummed Pitch Class Set)"
                ),
                ft.DropdownOption(
                    key=ValidationMode.ARPEGGIO_SEQUENCE.value,
                    text="Arpeggio (Picked Notes Accumulator)"
                ),
            ],
            value=self.settings.validation_mode.value,
            expand=True,
            on_select=self._on_validation_mode_changed,
        )

        self.content = ft.Column(
            controls=[
                self.title_text,
                self.detection_mode_dropdown,
                ft.Text("CHORD QUALITIES", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                self.major_chk,
                self.minor_chk,
                self.dom7_chk,
                self.maj7_chk,
                self.validation_dropdown,
            ],
            spacing=10,
        )

        self.padding = 16
        self.border_radius = 14

        if self.theme_manager:
            self.theme_manager.add_listener(self.apply_theme)
            self.apply_theme()

    def apply_theme(self) -> None:
        """Applies theme colors."""
        if not self.theme_manager:
            return
        is_dark = self.theme_manager.is_dark()
        bg_panel = "#231F2D" if is_dark else "#FFFFFF"
        border_col = "#3E354A" if is_dark else "#D0C8DF"
        text_secondary = "#C4B5FD" if is_dark else "#5D4B75"

        self.bgcolor = bg_panel
        self.border = ft.Border.all(1, border_col)
        self.title_text.color = text_secondary

    def _on_detection_mode_changed(self, e) -> None:
        val = self.detection_mode_dropdown.value
        if val:
            self.settings.detection_mode = DetectionMode(val)
            self.on_settings_changed(self.settings)

    def _on_validation_mode_changed(self, e) -> None:
        val = self.validation_dropdown.value
        if val:
            self.settings.validation_mode = ValidationMode(val)
            self.on_settings_changed(self.settings)

    def _on_quality_changed(self, e) -> None:
        qualities = set()
        if self.major_chk.value:
            qualities.add(ChordQuality.MAJOR)
        if self.minor_chk.value:
            qualities.add(ChordQuality.MINOR)
        if self.dom7_chk.value:
            qualities.add(ChordQuality.DOMINANT_7TH)
        if self.maj7_chk.value:
            qualities.add(ChordQuality.MAJOR_7TH)

        if not qualities:
            qualities = {ChordQuality.MAJOR}
            self.major_chk.value = True

        self.settings.chord_filters.qualities = qualities
        self.on_settings_changed(self.settings)
