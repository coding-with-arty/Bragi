# src/views/subviews/chord_view.py
"""
Chord Practice View
===================
Interactive polyphonic chord trainer subview integrating ChordGenerator,
ChordEvaluator, opt-in fretboard hint drawers, and real-time validation feedback.
"""

from typing import Optional, Set
import flet as ft

from engine.chord_generator import ChordGenerator, ChordQuality, TargetChord, FOCUSED_QUALITIES
from engine.chord_evaluator import ChordEvaluator, ValidationMode
from models.instrument import InstrumentProfile
from storage.instrument_store import InstrumentStore
from views.components.fretboard_view import FretboardView
from views.components.fretboard_view import get_string_open_pc
from utils.theme_manager import ThemeManager
from utils.music_theory import CHROMATIC_SHARPS


class ChordView(ft.Column):
    """Interactive chord trainer subview for Major, Minor, Dom7, Maj7, and Sus4 practice."""

    def __init__(
        self,
        instrument_profile: Optional[InstrumentProfile] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__()
        self.theme_manager = theme_manager
        self.expand = True
        self.spacing = 16

        # Instrument Profile Configuration
        store = InstrumentStore()
        if hasattr(store, "get_default_profile"):
            default_prof = store.get_default_profile()
        elif hasattr(store, "get_all_profiles"):
            profiles = store.get_all_profiles()
            default_prof = profiles[0] if profiles else InstrumentProfile()
        else:
            default_prof = InstrumentProfile()

        self.profile = instrument_profile or default_prof

        # Engine State
        self.evaluator = ChordEvaluator(
            hold_duration_sec=0.5,
            min_volume_db=-40.0,
            validation_mode=ValidationMode.RELAXED_PITCH_CLASS,
        )
        self.allowed_qualities: Set[ChordQuality] = set(FOCUSED_QUALITIES)
        self.current_target: Optional[TargetChord] = None

        # Fretboard Hint Drawer State (Hidden by default)
        self.show_hints: bool = False

        # --- UI Header ---
        self.title_text = ft.Text(
            "CHORD TRAINER",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.AMBER_400,
        )

        # Target Chord Display Card
        self.chord_name_text = ft.Text(
            "Press 'Next Chord' to Begin",
            size=28,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.WHITE,
        )

        self.chord_tones_text = ft.Text(
            "Required Tones: --",
            size=14,
            color=ft.Colors.GREY_400,
        )

        self.status_banner = ft.Text(
            "Ready for input",
            size=13,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.CYAN_400,
        )

        self.target_card = ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=6,
                controls=[
                    self.chord_name_text,
                    self.chord_tones_text,
                    ft.Container(height=4),
                    self.status_banner,
                ],
            ),
            bgcolor=ft.Colors.with_opacity(0.18, "#130F1C"),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.3, "#3E354A")),
            border_radius=16,
            padding=20,
            alignment=ft.Alignment.CENTER,
        )

        # Action Buttons
        self.next_chord_btn = ft.Button(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.SKIP_NEXT_ROUNDED, size=20),
                    ft.Text("Next Chord", weight=ft.FontWeight.BOLD),
                ],
                tight=True,
                spacing=6,
            ),
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.AMBER_400,
                color=ft.Colors.BLACK,
            ),
            on_click=self._generate_next_chord,
        )

        # Opt-In Fretboard Drawer Controls
        self.fretboard_view = FretboardView(
            profile=self.profile,
            visible_frets=15,
            theme_manager=self.theme_manager,
        )
        self.fretboard_view.visible = False  # Hidden by default

        self.hint_toggle_btn = ft.Button(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_OUTLINE_ROUNDED, size=18),
                    ft.Text("Show Fretboard Hints", weight=ft.FontWeight.BOLD, size=13),
                ],
                tight=True,
                spacing=6,
            ),
            on_click=self._toggle_fretboard_hint,
        )

        # Layout Assembly
        self.controls = [
            ft.Container(
                content=ft.Row(
                    controls=[self.title_text, self.next_chord_btn],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=8),
            ),
            self.target_card,
            ft.Container(
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        self.hint_toggle_btn,
                        ft.Container(height=8),
                        self.fretboard_view,
                    ],
                ),
                padding=ft.Padding.symmetric(horizontal=16),
            ),
        ]

        # Generate initial target chord
        self._generate_next_chord()

    def _safe_update(self) -> None:
        """Safely updates the page if the control is attached to an active Page."""
        try:
            if self.page:
                self.page.update()
        except RuntimeError:
            # Control is not yet attached to a Flet Page hierarchy
            pass

    def _generate_next_chord(self, e=None) -> None:
        """Generates a new random target chord from allowed quality filters."""
        self.current_target = ChordGenerator.generate_target(
            allowed_qualities=self.allowed_qualities
        )
        self.evaluator.set_target(self.current_target)

        # Update Target Readouts
        self.chord_name_text.value = self.current_target.chord_definition.name

        # Extract note names safely from chord definition or map pitch classes
        chord_def = self.current_target.chord_definition
        if hasattr(chord_def, "note_names") and chord_def.note_names:
            note_names = chord_def.note_names
        else:
            pcs = sorted(list(chord_def.pitch_classes))
            note_names = [CHROMATIC_SHARPS[pc % 12] for pc in pcs]

        tones_fmt = " - ".join(note_names)
        self.chord_tones_text.value = f"Required Tones: {tones_fmt}"
        self.status_banner.value = "Listening for chord..."
        self.status_banner.color = ft.Colors.CYAN_400

        if self.show_hints:
            self._update_fretboard_overlay()

        self._safe_update()

    def _toggle_fretboard_hint(self, e=None) -> None:
        """Toggles opt-in fretboard visualizer drawer visibility."""
        self.show_hints = not self.show_hints
        self.fretboard_view.visible = self.show_hints

        self.hint_toggle_btn.content.controls[0].name = (
            ft.Icons.LIGHTBULB_ROUNDED if self.show_hints else ft.Icons.LIGHTBULB_OUTLINE_ROUNDED
        )
        self.hint_toggle_btn.content.controls[1].value = (
            "Hide Fretboard Hints" if self.show_hints else "Show Fretboard Hints"
        )

        if self.show_hints:
            self._update_fretboard_overlay()

        self._safe_update()

    def _update_fretboard_overlay(self) -> None:
        """Highlights matching target chord tones across the fretboard neck."""
        if not self.current_target:
            return

        target_pcs = set(self.current_target.chord_definition.pitch_classes)
        highlight_positions = []

        for string_idx, string_cfg in enumerate(self.profile.tuning):
            open_pc = get_string_open_pc(string_cfg)
            for fret in range(0, 16):
                pos_pc = (open_pc + fret) % 12
                if pos_pc in target_pcs:
                    highlight_positions.append({
                        "string_idx": string_idx,
                        "fret": fret,
                        "is_root": (pos_pc == list(self.current_target.chord_definition.pitch_classes)[0]),
                    })

        if hasattr(self.fretboard_view, "highlight_scale_positions"):
            self.fretboard_view.highlight_scale_positions(highlight_positions)

    def process_audio_frame(self, detected_pitch_classes: list[int], volume_db: float) -> None:
        """
        Processes real-time polyphonic audio frames emitted from the audio capture thread.
        """
        is_valid, statement = self.evaluator.evaluate_pitch_classes(
            detected_pitch_classes=detected_pitch_classes,
            volume_db=volume_db,
        )

        if is_valid and statement is not None and statement.is_correct:
            self.status_banner.value = "CHORD MATCHED! 🎉"
            self.status_banner.color = ft.Colors.GREEN_400
        elif is_valid:
            self.status_banner.value = "Sustaining pitch..."
            self.status_banner.color = ft.Colors.AMBER_400
        else:
            self.status_banner.value = "Listening for chord..."
            self.status_banner.color = ft.Colors.CYAN_400

        self._safe_update()
