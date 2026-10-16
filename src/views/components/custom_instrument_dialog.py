# src/views/components/custom_instrument_dialog.py
import uuid
from typing import Callable, Optional, List
import flet as ft
from models.instrument import InstrumentProfile, StringConfig
from storage.instrument_store import InstrumentStore
from utils.music_theory import CHROMATIC_SHARPS
from utils.theme_manager import ThemeManager


class CustomInstrumentDialog(ft.AlertDialog):
    """Interactive Custom Instrument Builder modal dialog."""

    def __init__(
        self,
        instrument_store: InstrumentStore,
        on_instrument_saved: Callable[[InstrumentProfile], None],
        existing_profile: Optional[InstrumentProfile] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        self.store = instrument_store
        self.on_instrument_saved = on_instrument_saved
        self.theme_manager = theme_manager
        self.editing_profile = existing_profile

        initial_string_count = existing_profile.string_count if existing_profile else 6
        initial_name = existing_profile.name if existing_profile else "My Custom Instrument"

        self.name_field = ft.TextField(
            label="Instrument Name",
            value=initial_name,
            expand=True,
            dense=True,
        )

        self.string_count_dropdown = ft.Dropdown(
            label="Strings",
            value=str(initial_string_count),
            options=[ft.DropdownOption(key=str(i), text=f"{i} Strings") for i in range(1, 11)],
            width=140,
            dense=True,
            on_select=self._on_string_count_changed,
        )

        self.string_configs: List[StringConfig] = (
            list(existing_profile.tuning) if existing_profile else [
                StringConfig(string_num=1, note_name="E", octave=4),
                StringConfig(string_num=2, note_name="B", octave=3),
                StringConfig(string_num=3, note_name="G", octave=3),
                StringConfig(string_num=4, note_name="D", octave=3),
                StringConfig(string_num=5, note_name="A", octave=2),
                StringConfig(string_num=6, note_name="E", octave=2),
            ]
        )

        self.strings_column = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, height=260)

        actions = [
            ft.TextButton("Cancel", on_click=self._close_dialog),
            ft.ElevatedButton(
                "Save Instrument",
                icon=ft.Icons.SAVE_ROUNDED,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.AMBER_400,
                    color=ft.Colors.BLACK,
                ),
                on_click=self._save_instrument,
            ),
        ]

        if existing_profile and existing_profile.is_custom:
            actions.insert(
                0,
                ft.TextButton(
                    "Delete",
                    style=ft.ButtonStyle(color=ft.Colors.RED_400),
                    on_click=self._delete_instrument
                )
            )

        super().__init__(
            title=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.BUILD_ROUNDED, color=ft.Colors.AMBER_400),
                    ft.Text("Custom Instrument Builder", size=18, weight=ft.FontWeight.BOLD),
                ],
                spacing=10,
            ),
            content=ft.Container(
                width=460,
                content=ft.Column(
                    tight=True,
                    spacing=14,
                    controls=[
                        ft.Row(controls=[self.name_field, self.string_count_dropdown], spacing=10),
                        ft.Divider(height=1, color=ft.Colors.GREY_800),
                        ft.Text("Assign pitch and octave per string:", size=12, color=ft.Colors.GREY_400),
                        self.strings_column,
                    ],
                ),
            ),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._render_string_rows()

    def _render_string_rows(self) -> None:
        rows = []
        for idx, cfg in enumerate(self.string_configs):
            s_num = idx + 1

            note_dd = ft.Dropdown(
                label="Pitch",
                value=cfg.note_name,
                options=[ft.DropdownOption(key=n, text=n) for n in CHROMATIC_SHARPS],
                width=110,
                dense=True,
                data=idx,
                on_select=self._on_note_changed,
            )

            octave_dd = ft.Dropdown(
                label="Octave",
                value=str(cfg.octave),
                options=[ft.DropdownOption(key=str(o), text=f"Octave {o}") for o in range(0, 8)],
                width=110,
                dense=True,
                data=idx,
                on_select=self._on_octave_changed,
            )

            row = ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(f"String {s_num}:", weight=ft.FontWeight.BOLD, size=13, width=70),
                    note_dd,
                    octave_dd,
                ],
            )
            rows.append(row)

        self.strings_column.controls = rows

    def _on_string_count_changed(self, e) -> None:
        new_count = int(self.string_count_dropdown.value)
        curr_count = len(self.string_configs)

        if new_count > curr_count:
            for i in range(curr_count + 1, new_count + 1):
                self.string_configs.append(StringConfig(string_num=i, note_name="E", octave=2))
        elif new_count < curr_count:
            self.string_configs = self.string_configs[:new_count]

        self._render_string_rows()
        if self.page:
            self.page.update()

    def _on_note_changed(self, e) -> None:
        idx = e.control.data
        note = e.control.value
        curr = self.string_configs[idx]
        self.string_configs[idx] = StringConfig(string_num=curr.string_num, note_name=note, octave=curr.octave)

    def _on_octave_changed(self, e) -> None:
        idx = e.control.data
        octave = int(e.control.value)
        curr = self.string_configs[idx]
        self.string_configs[idx] = StringConfig(string_num=curr.string_num, note_name=curr.note_name, octave=octave)

    def _close_dialog(self, e=None) -> None:
        self.open = False
        if self.page:
            self.page.update()

    def _save_instrument(self, e=None) -> None:
        name = self.name_field.value.strip() or "Custom Instrument"
        profile_id = self.editing_profile.id if self.editing_profile else f"custom_{uuid.uuid4().hex[:8]}"

        profile = InstrumentProfile(
            id=profile_id,
            name=name,
            category="Custom",
            string_count=len(self.string_configs),
            fret_count=24,
            tuning=self.string_configs,
            fretboard_landmarks=[3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
            is_custom=True
        )

        self.store.save_custom_instrument(profile)
        self.on_instrument_saved(profile)
        self._close_dialog()

    def _delete_instrument(self, e=None) -> None:
        if self.editing_profile and self.editing_profile.is_custom:
            self.store.delete_custom_instrument(self.editing_profile.id)
            self.on_instrument_saved(self.store.get_all_profiles()[0])
        self._close_dialog()
