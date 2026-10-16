"""
src/views/components/tuning_panel.py
====================================
Streamlined sidebar component for custom per-string tuning.
Hides octave complexity from beginners while maintaining underlying pitch calculation accuracy.
"""

from typing import Callable, List, Tuple, Optional
import flet as ft
from utils.music_theory import CHROMATIC_SHARPS
from utils.theme_manager import ThemeManager


class TuningPanel(ft.Container):
    """Clean, beginner-friendly sidebar panel for note-only custom tuning adjustments."""

    def __init__(
        self,
        initial_tuning: List[Tuple[str, int]],
        on_tuning_changed: Optional[Callable[[List[Tuple[str, int]]], None]] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__()
        self.tuning = list(initial_tuning)
        self.on_tuning_changed = on_tuning_changed
        self.theme_manager = theme_manager

        self.border_radius = 12
        self.padding = 12
        self.bgcolor = "#231F2D"
        self.border = ft.Border.all(1, "#3E354A")

        self.title_text = ft.Text(
            "CUSTOM TUNING", size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400
        )

        self.strings_column = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO)

        self.content = ft.Column(
            tight=True,
            spacing=8,
            controls=[
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.TUNE_ROUNDED, size=18, color=ft.Colors.AMBER_400),
                        self.title_text,
                    ],
                    spacing=8,
                ),
                ft.Divider(height=1, color="#3E354A"),
                self.strings_column,
            ],
        )

        self._render_tuning_rows()

    def _render_tuning_rows(self) -> None:
        """Renders per-string note pickers with automatic octave preservation."""
        rows = []
        for idx, (note, octave) in enumerate(self.tuning):
            string_num = idx + 1

            # Clean full-width note name selector
            note_dd = ft.Dropdown(
                value=note,
                options=[ft.DropdownOption(key=n, text=n) for n in CHROMATIC_SHARPS],
                dense=True,
                data=idx,
                expand=True,
                on_select=self._on_note_changed,
            )

            row = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Text(
                        f"String {string_num}:",
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREY_300,
                        width=65,
                    ),
                    note_dd,
                ],
            )
            rows.append(row)

        self.strings_column.controls = rows

    def _on_note_changed(self, e) -> None:
        """Updates note pitch class while preserving string's octave index."""
        idx = e.control.data
        new_note = e.control.value
        existing_octave = self.tuning[idx][1]

        # Preserve the existing octave for this string position
        self.tuning[idx] = (new_note, existing_octave)

        if self.on_tuning_changed:
            self.on_tuning_changed(self.tuning)

    def update_tuning_externally(self, new_tuning: List[Tuple[str, int]]) -> None:
        """Updates internal tuning state and re-renders sidebar rows."""
        self.tuning = list(new_tuning)
        self._render_tuning_rows()
        try:
            self.update()
        except RuntimeError:
            pass
