"""
src/views/components/custom_tuning_dialog.py
=============================================
Interactive modal dialog allowing users to define custom string counts (1 to 8),
configure individual string tuning notes and octaves, and apply custom instrument presets.
"""

from typing import Callable, List, Tuple, Optional
import flet as ft
from utils.music_theory import MusicTheory, CHROMATIC_SHARPS
from utils.theme_manager import ThemeManager

ElevatedBtn = getattr(ft, "ElevatedButton", None) or getattr(ft, "FilledButton", None) or getattr(ft, "Button", ft.TextButton)
TextBtn = getattr(ft, "TextButton", None) or getattr(ft, "Button", ft.Container)


class CustomTuningDialog(ft.AlertDialog):
    """Custom tuning configuration modal dialog."""

    def __init__(
        self,
        current_tuning: List[Tuple[str, int]],
        on_tuning_saved: Callable[[List[Tuple[str, int]]], None],
        theme_manager: Optional[ThemeManager] = None,
    ):
        self.string_configs: List[Tuple[str, int]] = list(current_tuning) if current_tuning else [
            ("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2)
        ]
        self.on_tuning_saved = on_tuning_saved
        self.theme_manager = theme_manager

        self.string_count_dropdown = ft.Dropdown(
            label="Number of Strings",
            value=str(len(self.string_configs)),
            options=[ft.DropdownOption(key=str(i), text=f"{i} Strings") for i in range(1, 9)],
            width=180,
            on_change=self._on_string_count_changed,
        )

        self.strings_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=280)

        super().__init__(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.TUNE_ROUNDED, color=ft.Colors.AMBER_400),
                    ft.Text("Custom Instrument Tuning", size=18, weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(
                width=420,
                content=ft.Column(
                    tight=True,
                    spacing=14,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("Configure open pitches per string:", size=13, color=ft.Colors.GREY_400),
                                self.string_count_dropdown,
                            ],
                        ),
                        ft.Divider(height=1, color=ft.Colors.GREY_800),
                        self.strings_column,
                    ],
                ),
            ),
            actions=[
                TextBtn("Cancel", on_click=self._close_dialog),
                ElevatedBtn(
                    "Apply Tuning",
                    icon=ft.Icons.CHECK_ROUNDED,
                    style=ft.ButtonStyle(
                        bgcolor=ft.Colors.AMBER_400,
                        color=ft.Colors.BLACK,
                    ),
                    on_click=self._save_tuning,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._render_string_rows()

    def _render_string_rows(self) -> None:
        """Renders dropdown controls for each active string."""
        rows = []
        for idx, (note, octave) in enumerate(self.string_configs):
            string_num = idx + 1

            note_dd = ft.Dropdown(
                label=f"String {string_num} Pitch",
                value=note,
                options=[ft.DropdownOption(key=n, text=n) for n in CHROMATIC_SHARPS],
                width=130,
                dense=True,
                data=idx,
                on_change=self._on_note_changed,
            )

            octave_dd = ft.Dropdown(
                label="Octave",
                value=str(octave),
                options=[ft.DropdownOption(key=str(o), text=f"Octave {o}") for o in range(0, 7)],
                width=110,
                dense=True,
                data=idx,
                on_change=self._on_octave_changed,
            )

            row = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"String {string_num}:", weight=ft.FontWeight.BOLD, size=14, width=70),
                    note_dd,
                    octave_dd,
                ],
            )
            rows.append(row)

        self.strings_column.controls = rows

    def _on_string_count_changed(self, e) -> None:
        """Handles resizing the string count."""
        new_count = int(self.string_count_dropdown.value)
        current_count = len(self.string_configs)

        if new_count > current_count:
            for _ in range(new_count - current_count):
                self.string_configs.append(("E", 2))
        elif new_count < current_count:
            self.string_configs = self.string_configs[:new_count]

        self._render_string_rows()
        if self.page:
            self.page.update()

    def _on_note_changed(self, e) -> None:
        idx = e.control.data
        note = e.control.value
        _, octave = self.string_configs[idx]
        self.string_configs[idx] = (note, octave)

    def _on_octave_changed(self, e) -> None:
        idx = e.control.data
        octave = int(e.control.value)
        note, _ = self.string_configs[idx]
        self.string_configs[idx] = (note, octave)

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

    def _save_tuning(self, e=None) -> None:
        """Saves custom tuning into MusicTheory and notifies parent views."""
        MusicTheory.set_custom_tuning(self.string_configs, preset_name="Custom Tuning")
        self.on_tuning_saved(self.string_configs)
        self._close_dialog()
