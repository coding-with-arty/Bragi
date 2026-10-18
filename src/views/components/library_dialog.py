# src/views/components/library_dialog.py
"""
Chord & Scale Library Dialog
============================
Interactive library modal allowing users to search chord formulas and scale structures
by Key and Type, featuring an 'Apply as Target' button to load selections into practice mode.
"""

from typing import Optional, Callable, Any
import flet as ft
from utils.music_theory import CHROMATIC_SHARPS, MusicTheory, CHORD_PATTERNS, SCALE_PATTERNS
from engine.chord_generator import ChordQuality, ChordGenerator
from models.chord import TargetChord
from utils.theme_manager import ThemeManager


class LibraryDialog(ft.AlertDialog):
    """Searchable Chord and Scale reference library modal."""

    def __init__(
        self,
        on_apply_chord_target: Optional[Callable[[TargetChord], None]] = None,
        on_apply_scale_target: Optional[Callable[[str, str], None]] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        self.on_apply_chord_target = on_apply_chord_target
        self.on_apply_scale_target = on_apply_scale_target
        self.theme_manager = theme_manager

        self.selected_category = "Chords"
        self.selected_key = "C"

        self.key_dropdown = ft.Dropdown(
            label="Root Key",
            value=self.selected_key,
            options=[ft.DropdownOption(key=k, text=k) for k in CHROMATIC_SHARPS],
            width=110,
            dense=True,
            on_select=self._on_filter_changed,
        )

        self.category_segmented = ft.CupertinoSegmentedButton(
            selected_index=0,
            controls=[
                ft.Text("Chords", size=12, weight=ft.FontWeight.BOLD),
                ft.Text("Scales", size=12, weight=ft.FontWeight.BOLD),
            ],
            on_change=self._on_category_changed,
        )

        self.type_dropdown = ft.Dropdown(
            label="Type Filter",
            value="All",
            options=[ft.DropdownOption(key="All", text="All Types")],
            width=220,
            dense=True,
            on_select=self._on_filter_changed,
        )

        self.results_column = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            height=320,
        )

        content = ft.Container(
            width=520,
            content=ft.Column(
                tight=True,
                spacing=14,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[self.category_segmented, self.key_dropdown],
                    ),
                    self.type_dropdown,
                    ft.Divider(height=1, color=ft.Colors.GREY_800),
                    self.results_column,
                ],
            ),
        )

        close_btn = ft.Button(
            "Close",
            style=ft.ButtonStyle(
                color=ft.Colors.BLACK,
                bgcolor=ft.Colors.AMBER_400,
            ),
            on_click=self._close_dialog,
        )

        super().__init__(
            title=ft.Row([
                ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color=ft.Colors.AMBER_400),
                ft.Text("Chord & Scale Library", weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=content,
            actions=[close_btn],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._populate_type_options()
        self._render_results()

    def _on_category_changed(self, e) -> None:
        idx = int(self.category_segmented.selected_index)
        self.selected_category = "Chords" if idx == 0 else "Scales"
        self._populate_type_options()
        self._render_results()

    def _populate_type_options(self) -> None:
        patterns = CHORD_PATTERNS if self.selected_category == "Chords" else SCALE_PATTERNS
        options = [ft.DropdownOption(key="All", text="All Types")]
        for name in patterns.keys():
            options.append(ft.DropdownOption(key=name, text=name))

        self.type_dropdown.options = options
        self.type_dropdown.value = "All"
        if self.page:
            self.page.update()

    def _on_filter_changed(self, e) -> None:
        self.selected_key = self.key_dropdown.value or "C"
        self._render_results()

    def _render_results(self) -> None:
        key = self.selected_key
        filter_type = self.type_dropdown.value or "All"
        cards = []

        if self.selected_category == "Chords":
            patterns = CHORD_PATTERNS
            for q_name, semitones in patterns.items():
                if filter_type != "All" and filter_type != q_name:
                    continue

                pcs = [(MusicTheory.note_to_pitch_class(key) + s) % 12 for s in semitones]
                notes = [CHROMATIC_SHARPS[pc] for pc in pcs]
                notes_fmt = " - ".join(notes)

                apply_btn = ft.Button(
                    content=ft.Row([
                        ft.Icon(ft.Icons.TARGET, size=14),
                        ft.Text("Apply Target", size=11, weight=ft.FontWeight.BOLD)
                    ], tight=True, spacing=4),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.AMBER_400, color=ft.Colors.BLACK),
                    data={"type": "chord", "key": key, "quality": q_name},
                    on_click=self._on_apply_clicked,
                )

                card = ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(f"{key} {q_name}", weight=ft.FontWeight.BOLD, size=15),
                                    ft.Text(f"Tones: {notes_fmt}", size=12, color=ft.Colors.AMBER_400),
                                ],
                            ),
                            apply_btn,
                        ],
                    ),
                    bgcolor=ft.Colors.with_opacity(0.12, "#1A1523"),
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.25, "#3E354A")),
                    border_radius=10,
                    padding=12,
                )
                cards.append(card)
        else:
            patterns = SCALE_PATTERNS
            for s_name, semitones in patterns.items():
                if filter_type != "All" and filter_type != s_name:
                    continue

                notes = MusicTheory.get_scale_notes(key, s_name)
                notes_fmt = " - ".join(notes)

                apply_btn = ft.Button(
                    content=ft.Row([
                        ft.Icon(ft.Icons.TARGET, size=14),
                        ft.Text("Apply Target", size=11, weight=ft.FontWeight.BOLD)
                    ], tight=True, spacing=4),
                    style=ft.ButtonStyle(bgcolor=ft.Colors.CYAN_400, color=ft.Colors.BLACK),
                    data={"type": "scale", "key": key, "scale_name": s_name},
                    on_click=self._on_apply_clicked,
                )

                card = ft.Container(
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(f"{key} {s_name}", weight=ft.FontWeight.BOLD, size=15),
                                    ft.Text(f"Sequence: {notes_fmt}", size=12, color=ft.Colors.CYAN_400),
                                ],
                            ),
                            apply_btn,
                        ],
                    ),
                    bgcolor=ft.Colors.with_opacity(0.12, "#1A1523"),
                    border=ft.Border.all(1, ft.Colors.with_opacity(0.25, "#3E354A")),
                    border_radius=10,
                    padding=12,
                )
                cards.append(card)

        self.results_column.controls = cards
        if self.page:
            self.page.update()

    def _on_apply_clicked(self, e) -> None:
        data = e.control.data
        if data["type"] == "chord" and self.on_apply_chord_target:
            target = ChordGenerator.generate_target({"selected_keys": [data["key"]], "qualities": [data["quality"]]})
            self.on_apply_chord_target(target)
        elif data["type"] == "scale" and self.on_apply_scale_target:
            self.on_apply_scale_target(data["key"], data["scale_name"])
        self._close_dialog()

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
