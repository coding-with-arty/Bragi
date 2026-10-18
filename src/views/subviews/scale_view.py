# src/views/subviews/scale_view.py
"""
Scale Practice View
===================
Interactive scale trainer subview integrating ScaleEngine, ScaleSequencer,
live note-by-note play-along tracking, opt-in fretboard drawer, and pedagogy.
"""

from typing import Optional, List
import flet as ft

from engine.scale_engine import ScaleEngine, ScaleType, ScaleDefinition
from engine.scale_sequencer import ScaleSequencer, SequenceDirection
from models.instrument import InstrumentProfile
from storage.instrument_store import InstrumentStore
from views.components.fretboard_view import FretboardView
from views.components.fretboard_view import get_string_open_pc
from views.components.education_dialog import EducationDialog
from utils.theme_manager import ThemeManager
from utils.music_theory import CHROMATIC_SHARPS


class ScaleView(ft.Column):
    """Interactive scale trainer view supporting live step-by-step play-along tracking."""

    def __init__(
        self,
        instrument_profile: Optional[InstrumentProfile] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__()
        self.theme_manager = theme_manager
        self.expand = True
        self.spacing = 16

        # Instrument Store Profile Resolution
        store = InstrumentStore()
        self.profile = instrument_profile or store.get_default_profile()

        # Scale Configuration Defaults
        self.root_note = "C"
        self.scale_type = ScaleType.MAJOR
        self.direction = SequenceDirection.ASCENDING

        # Engine Components
        self.scale_def = ScaleDefinition(self.root_note, self.scale_type)
        self.sequencer = ScaleSequencer(
            scale_notes=self.scale_def.get_note_names(),
            direction=self.direction,
        )

        # Fretboard Hint State
        self.show_hints = True

        # --- UI Header & Title ---
        self.title_text = ft.Text(
            "SCALE TRAINER",
            size=22,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.AMBER_400,
        )

        self.help_btn = ft.IconButton(
            icon=ft.Icons.HELP_OUTLINE_ROUNDED,
            icon_color=ft.Colors.AMBER_400,
            tooltip="Why Learn Scales?",
            on_click=self._open_education_dialog,
        )

        # Dropdown Selectors
        self.root_dropdown = ft.Dropdown(
            label="Root Note",
            value=self.root_note,
            options=[ft.dropdown.Option(note) for note in CHROMATIC_SHARPS],
            width=110,
            dense=True,
            on_select=self._on_scale_config_change,
        )

        self.type_dropdown = ft.Dropdown(
            label="Scale Type",
            value=self.scale_type.value,
            options=[ft.dropdown.Option(stype.value) for stype in ScaleType],
            width=180,
            dense=True,
            on_select=self._on_scale_config_change,
        )

        self.dir_dropdown = ft.Dropdown(
            label="Pattern Direction",
            value=self.direction.value,
            options=[
                ft.dropdown.Option(SequenceDirection.ASCENDING.value, "Ascending"),
                ft.dropdown.Option(SequenceDirection.DESCENDING.value, "Descending"),
                ft.dropdown.Option(SequenceDirection.ASCENDING_DESCENDING.value, "Up & Down"),
            ],
            width=160,
            dense=True,
            on_select=self._on_scale_config_change,
        )

        # --- Active Target & Step Progress Card ---
        self.target_note_text = ft.Text(
            "C",
            size=42,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.AMBER_400,
        )

        self.step_counter_text = ft.Text(
            "Step 1 / 7",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREY_300,
        )

        self.progress_bar = ft.ProgressBar(
            value=0.14,
            color=ft.Colors.AMBER_400,
            bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.WHITE),
            height=8,
        )

        self.status_banner = ft.Text(
            "Play the target note to advance",
            size=13,
            weight=ft.FontWeight.W_500,
            color=ft.Colors.CYAN_400,
        )

        self.target_card = ft.Container(
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text(f"{self.root_note} {self.scale_type.value}", size=16, color=ft.Colors.GREY_400),
                    self.target_note_text,
                    self.step_counter_text,
                    ft.Container(content=self.progress_bar, width=320),
                    self.status_banner,
                ],
            ),
            bgcolor=ft.Colors.with_opacity(0.18, "#130F1C"),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.3, "#3E354A")),
            border_radius=16,
            padding=20,
            alignment=ft.Alignment.CENTER,
        )

        # --- Interactive Fretboard Visualizer ---
        self.fretboard_view = FretboardView(
            profile=self.profile,
            visible_frets=15,
            theme_manager=self.theme_manager,
        )

        self.hint_toggle_btn = ft.Button(
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.LIGHTBULB_ROUNDED, size=18),
                    ft.Text("Hide Fretboard Hints", weight=ft.FontWeight.BOLD, size=13),
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
                    controls=[
                        ft.Row(controls=[self.title_text, self.help_btn], spacing=6),
                        ft.Row(controls=[self.root_dropdown, self.type_dropdown, self.dir_dropdown], spacing=8),
                    ],
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

        self._refresh_scale_state()

    def _safe_update(self) -> None:
        try:
            if self.page:
                self.page.update()
        except RuntimeError:
            pass

    def _open_education_dialog(self, e=None) -> None:
        dialog = EducationDialog(module_key="scale_trainer", theme_manager=self.theme_manager)
        if self.page:
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()

    def _on_scale_config_change(self, e=None) -> None:
        self.root_note = self.root_dropdown.value or "C"
        stype_val = self.type_dropdown.value or "Major"
        self.scale_type = next((s for s in ScaleType if s.value == stype_val), ScaleType.MAJOR)
        dir_val = self.dir_dropdown.value or SequenceDirection.ASCENDING.value
        self.direction = SequenceDirection(dir_val)

        self._refresh_scale_state()

    def _refresh_scale_state(self) -> None:
        """Re-computes active scale sequence and updates visual readouts."""
        self.scale_def = ScaleDefinition(self.root_note, self.scale_type)
        scale_notes = self.scale_def.get_note_names()

        self.sequencer.generate_sequence(scale_notes, self.direction)
        self._update_step_display()
        self._update_fretboard_highlights()
        self._safe_update()

    def _update_step_display(self) -> None:
        """Updates target note, step counter, and progress bar."""
        curr_note = self.sequencer.get_current_note()
        total_steps = len(self.sequencer.sequence) or 1
        curr_idx = self.sequencer.current_index + 1

        if curr_note:
            self.target_note_text.value = curr_note
            self.step_counter_text.value = f"Step {curr_idx} of {total_steps}"
            self.progress_bar.value = curr_idx / float(total_steps)
            self.status_banner.value = f"Play target note: {curr_note}"
            self.status_banner.color = ft.Colors.CYAN_400
        else:
            self.target_note_text.value = "COMPLETE! 🎉"
            self.step_counter_text.value = f"{total_steps} / {total_steps} Notes Matched"
            self.progress_bar.value = 1.0
            self.status_banner.value = "Great job! Resetting sequence..."
            self.status_banner.color = ft.Colors.GREEN_400

    def _toggle_fretboard_hint(self, e=None) -> None:
        self.show_hints = not self.show_hints
        self.fretboard_view.visible = self.show_hints

        self.hint_toggle_btn.content.controls[0].name = (
            ft.Icons.LIGHTBULB_ROUNDED if self.show_hints else ft.Icons.LIGHTBULB_OUTLINE_ROUNDED
        )
        self.hint_toggle_btn.content.controls[1].value = (
            "Hide Fretboard Hints" if self.show_hints else "Show Fretboard Hints"
        )
        self._safe_update()

    def _update_fretboard_highlights(self) -> None:
        """Maps scale pitch classes to instrument fretboard positions accurately."""
        if not self.show_hints:
            return

        curr_target = self.sequencer.get_current_note()
        scale_pcs = set(self.scale_def.pitch_classes)
        root_pc = self.scale_def.root_pitch_class

        highlight_positions = []
        for string_idx, string_cfg in enumerate(self.profile.tuning):
            open_pc = get_string_open_pc(string_cfg)
            for fret in range(0, 16):
                pos_pc = (open_pc + fret) % 12
                if pos_pc in scale_pcs:
                    is_active_target = (curr_target and CHROMATIC_SHARPS[pos_pc] == curr_target)
                    highlight_positions.append({
                        "string_idx": string_idx,
                        "fret": fret,
                        "note_name": CHROMATIC_SHARPS[pos_pc],
                        "is_root": (pos_pc == root_pc or is_active_target),
                    })

        if hasattr(self.fretboard_view, "highlight_scale_positions"):
            self.fretboard_view.highlight_scale_positions(highlight_positions)

    def process_audio_frame(self, detected_note: str, volume_db: float) -> None:
        """Processes real-time single-note pitch input and advances step cursor on match."""
        active_target = self.sequencer.get_current_note()
        if not active_target or not detected_note:
            return

        if detected_note.strip().upper() == active_target.upper():
            next_note = self.sequencer.advance()
            if next_note is None:
                # Sequence completed; reset for another run
                self.sequencer.reset()

            self._update_step_display()
            self._update_fretboard_highlights()
            self._safe_update()
