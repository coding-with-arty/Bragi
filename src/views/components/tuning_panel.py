# src/views/components/tuning_panel.py
import flet as ft
from typing import List, Tuple, Callable

class TuningPanel(ft.Column):
    """
    Dynamic interface for editing individual string tunings.
    Provides Dropdowns for note names and octaves per string.
    """
    def __init__(
        self,
        initial_tuning: List[Tuple[str, int]],
        on_tuning_changed: Callable[[List[Tuple[str, int]]], None]
    ):
        super().__init__()
        self.current_tuning = initial_tuning
        self.on_tuning_changed = on_tuning_changed
        self.spacing = 8
        self.notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self._build_ui()

    def _build_ui(self):
        self.controls.clear()

        for i, (note, octave) in enumerate(self.current_tuning):
            string_num = i + 1

            # Instantiate without the event kwarg to bypass validation errors
            note_dd = ft.Dropdown(
                value=note,
                options=[ft.DropdownOption(n) for n in self.notes],
                width=70,
                dense=True,
                content_padding=ft.Padding(10, 0, 10, 0)
            )
            # Bind the event listener post-initialization
            note_dd.on_change = lambda e, idx=i: self._update_tuning_note(idx, e.control.value)

            octave_dd = ft.Dropdown(
                value=str(octave),
                options=[ft.DropdownOption(str(o)) for o in range(0, 9)],
                width=70,
                dense=True,
                content_padding=ft.Padding(10, 0, 10, 0)
            )
            octave_dd.on_change = lambda e, idx=i: self._update_tuning_octave(idx, int(e.control.value))

            row = ft.Row([
                ft.Text(f"Str {string_num}", width=40, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_400),
                note_dd,
                octave_dd
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

            self.controls.append(row)

    def _update_tuning_note(self, index: int, new_note: str):
        _, octave = self.current_tuning[index]
        self.current_tuning[index] = (new_note, octave)
        self.on_tuning_changed(self.current_tuning)

    def _update_tuning_octave(self, index: int, new_octave: int):
        note, _ = self.current_tuning[index]
        self.current_tuning[index] = (note, new_octave)
        self.on_tuning_changed(self.current_tuning)

    def update_tuning_externally(self, new_tuning: List[Tuple[str, int]]):
        """Called by parent when a preset is selected or string count changes."""
        self.current_tuning = new_tuning
        self._build_ui()
        self.update()
