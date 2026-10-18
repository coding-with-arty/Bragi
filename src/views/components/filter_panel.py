# src/views/components/filter_panel.py
"""
Sidebar Control Panel
=====================
Filter controls for selecting practice modes, full chord qualities,
and chord recognition options.
"""

from typing import Callable, Optional, Dict
import flet as ft
from models.settings import TrainerSettings, DetectionMode, ValidationMode
from models.chord import ChordQuality
from utils.theme_manager import ThemeManager


class FilterPanel(ft.Container):
    """Sidebar configuration panel for practice modes and chord filters."""

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

        # 1. Practice Mode Switcher
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

        # 2. Checkbox mapping for all available chord qualities
        self.quality_checkboxes: Dict[ChordQuality, ft.Checkbox] = {}
        active_qualities = self.settings.chord_filters.qualities

        # Define quality definitions categorized by harmonic structure
        triad_definitions = [
            (ChordQuality.MAJOR, "Major Triads"),
            (ChordQuality.MINOR, "Minor Triads"),
            (ChordQuality.DIMINISHED, "Diminished"),
            (ChordQuality.AUGMENTED, "Augmented"),
        ]

        seventh_definitions = [
            (ChordQuality.DOMINANT_7TH, "Dominant 7th"),
            (ChordQuality.MAJOR_7TH, "Major 7th"),
            (ChordQuality.MINOR_7TH, "Minor 7th"),
            (ChordQuality.DIMINISHED_7TH, "Diminished 7th"),
            (ChordQuality.HALF_DIMINISHED_7TH, "Half-Diminished 7th"),
        ]

        suspended_definitions = [
            (ChordQuality.SUS2, "Sus2"),
            (ChordQuality.SUS4, "Sus4"),
        ]

        # Helper method to create formatted checkboxes
        def build_checkbox_controls(definitions):
            controls = []
            for quality, label in definitions:
                chk = ft.Checkbox(
                    label=label,
                    value=(quality in active_qualities),
                    fill_color=ft.Colors.AMBER_400,
                    on_change=self._on_quality_changed,
                )
                self.quality_checkboxes[quality] = chk
                controls.append(chk)
            return controls

        # 3. Validation Mode Dropdown
        self.validation_dropdown = ft.Dropdown(
            label="Chord Recognition Engine",
            options=[
                ft.DropdownOption(
                    key=ValidationMode.RELAXED_PITCH_CLASS.value,
                    text="Relaxed (Strummed Pitch Class Set)"
                ),
                ft.DropdownOption(
                    key=ValidationMode.ARPEGGIO_SEQUENCE.value,
                    text="Arpeggio (Accumulator Window)"
                ),
            ],
            value=self.settings.validation_mode.value,
            expand=True,
            on_select=self._on_validation_mode_changed,
        )

        # 4. Construct Responsive Column Layout
        self.content = ft.Column(
            controls=[
                self.title_text,
                self.detection_mode_dropdown,
                ft.Divider(height=1, color=ft.Colors.with_opacity(0.2, ft.Colors.GREY)),

                ft.Text("TRIADS & BASIC", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                *build_checkbox_controls(triad_definitions),

                ft.Text("SEVENTH CHORDS", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                *build_checkbox_controls(seventh_definitions),

                ft.Text("SUSPENDED CHORDS", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400),
                *build_checkbox_controls(suspended_definitions),

                ft.Divider(height=1, color=ft.Colors.with_opacity(0.2, ft.Colors.GREY)),
                self.validation_dropdown,
            ],
            spacing=8,
            tight=True,  # Shrink-wrap around options to eliminate dead space
        )

        self.padding = 16
        self.border_radius = 14

        if self.theme_manager:
            self.theme_manager.add_listener(self.apply_theme)
            self.apply_theme()

    def apply_theme(self) -> None:
        """Applies light/dark theme colors."""
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
        selected_qualities = {
            quality for quality, chk in self.quality_checkboxes.items() if chk.value
        }

        # Fallback to Major if all options are unchecked
        if not selected_qualities:
            selected_qualities = {ChordQuality.MAJOR}
            if ChordQuality.MAJOR in self.quality_checkboxes:
                self.quality_checkboxes[ChordQuality.MAJOR].value = True

        self.settings.chord_filters.qualities = selected_qualities
        self.on_settings_changed(self.settings)
