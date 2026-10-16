"""
src/views/components/fretboard_view.py
======================================
Interactive Fretboard Map rendering neck geometry, open-string nuts,
fret markers, and dynamic note highlight dots with click/touch interactions.
"""

from typing import Callable, Dict, List, Optional, Tuple
import flet as ft
from models.instrument import InstrumentProfile
from instruments.base_instrument import BaseInstrument
from instruments.universal_instrument import UniversalInstrumentProfile
from utils.music_theory import MusicTheory
from utils.theme_manager import ThemeManager


class FretboardView(ft.Container):
    """Interactive Fretboard Neck Visualizer and Touch Map."""

    def __init__(
        self,
        profile: InstrumentProfile,
        visible_frets: int = 15,
        on_fret_clicked: Optional[Callable[[int, int, str, int], None]] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__()
        self.profile = profile
        self.univ_instrument = UniversalInstrumentProfile(profile)
        self.visible_frets = min(visible_frets, profile.fret_count)
        self.on_fret_clicked = on_fret_clicked
        self.theme_manager = theme_manager

        # Active note markers on the neck: dict of (string_num, fret_num) -> badge state
        self.active_markers: Dict[Tuple[int, int], Dict] = {}

        self.padding = ft.Padding.all(12)
        self.border_radius = 12
        self.bgcolor = ft.Colors.with_opacity(0.25, "#130F1C")
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.2, "#3E354A"))

        # Vertical Column for string rows
        self.neck_column = ft.Column(spacing=2)

        # Wrap in a horizontal scroll Row to prevent horizontal right-side clipping
        self.horizontal_scroll_wrapper = ft.Row(
            controls=[self.neck_column],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.content = self.horizontal_scroll_wrapper

        self.render_fretboard()

    def set_instrument_profile(self, profile: InstrumentProfile) -> None:
        """Updates active instrument geometry and re-renders the neck map."""
        self.profile = profile
        self.univ_instrument = UniversalInstrumentProfile(profile)
        self.visible_frets = min(self.visible_frets, profile.fret_count)
        self.clear_markers()

    def clear_markers(self) -> None:
        """Clears all active note highlights on the neck."""
        self.active_markers.clear()
        self.render_fretboard()

    def highlight_locations(
        self,
        locations: List[Tuple[int, int]],
        color: str = ft.Colors.AMBER_400,
        label: str = "",
    ) -> None:
        """Highlights specific (string_num, fret_num) locations on the neck."""
        self.active_markers.clear()
        tuning = self.profile.to_tuning_tuples()

        for string_num, fret in locations:
            if 1 <= string_num <= len(tuning):
                open_midi = self.univ_instrument.get_open_string_midi(string_num)
                target_midi = open_midi + fret
                note_name, octave = BaseInstrument.midi_to_note(target_midi)

                self.active_markers[(string_num, fret)] = {
                    "note": note_name,
                    "octave": octave,
                    "color": color,
                    "label": label or f"{note_name}{octave}",
                }

        self.render_fretboard()

    def render_fretboard(self) -> None:
        """Renders the physical fretboard grid including frets, strings, and markers."""
        tuning = self.profile.to_tuning_tuples()
        string_count = len(tuning)
        landmarks = self.profile.fretboard_landmarks

        rows = []

        # Top Row: Fret Numbers and Position Markers
        fret_num_controls = [
            ft.Container(
                content=ft.Text("NUT", size=10, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                width=45,
                alignment=ft.Alignment.CENTER,
            )
        ]

        for fret in range(1, self.visible_frets + 1):
            is_landmark = fret in landmarks
            fret_num_controls.append(
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=0,
                        controls=[
                            ft.Text(
                                f"{fret}",
                                size=11,
                                weight=ft.FontWeight.BOLD if is_landmark else ft.FontWeight.NORMAL,
                                color=ft.Colors.AMBER_400 if is_landmark else ft.Colors.GREY_500,
                            ),
                            ft.Icon(
                                ft.Icons.CIRCLE_ROUNDED if is_landmark else None,
                                size=6 if is_landmark else 0,
                                color=ft.Colors.AMBER_400,
                            ),
                        ],
                    ),
                    width=42,
                    alignment=ft.Alignment.CENTER,
                )
            )

        rows.append(ft.Row(controls=fret_num_controls, spacing=2))
        rows.append(ft.Divider(height=1, color=ft.Colors.with_opacity(0.3, "#3E354A")))

        # Render Each String Row (String 1 highest pitch to String N lowest pitch)
        for s_idx in range(string_count):
            string_num = s_idx + 1
            open_note, open_oct = tuning[s_idx]
            string_gauge = max(1, 4 - (s_idx * 2 // max(1, string_count - 1)))

            fret_cells = []

            # Open String Nut Cell (Fret 0)
            open_key = (string_num, 0)
            has_marker = open_key in self.active_markers
            marker_data = self.active_markers.get(open_key, {})

            nut_cell = ft.Container(
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Container(
                            content=ft.Text(
                                marker_data.get("label", f"{open_note}{open_oct}") if has_marker else f"{open_note}{open_oct}",
                                size=11,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLACK if has_marker else ft.Colors.WHITE,
                            ),
                            bgcolor=marker_data.get("color", ft.Colors.AMBER_400) if has_marker else ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
                            border_radius=12,
                            padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                        )
                    ],
                ),
                width=45,
                height=32,
                bgcolor=ft.Colors.with_opacity(0.12, ft.Colors.WHITE),
                border=ft.Border.all(1, ft.Colors.AMBER_400 if has_marker else ft.Colors.GREY_800),
                border_radius=4,
                ink=True,
                data=(string_num, 0),
                on_click=self._on_cell_clicked,
            )
            fret_cells.append(nut_cell)

            # Playable Frets (1 to visible_frets)
            for fret in range(1, self.visible_frets + 1):
                key = (string_num, fret)
                is_marked = key in self.active_markers
                cell_info = self.active_markers.get(key, {})

                if is_marked:
                    cell_content = ft.Container(
                        content=ft.Text(
                            cell_info.get("label", ""),
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLACK,
                        ),
                        bgcolor=cell_info.get("color", ft.Colors.AMBER_400),
                        shape=ft.BoxShape.CIRCLE,
                        width=24,
                        height=24,
                        alignment=ft.Alignment.CENTER,
                    )
                else:
                    cell_content = ft.Container(
                        height=string_gauge,
                        bgcolor=ft.Colors.GREY_600,
                        margin=ft.Margin.symmetric(vertical=15),
                    )

                fret_cell = ft.Container(
                    content=cell_content,
                    width=42,
                    height=32,
                    bgcolor=ft.Colors.with_opacity(0.05, ft.Colors.WHITE),
                    border=ft.Border(
                        right=ft.BorderSide(2 if fret in landmarks else 1, ft.Colors.GREY_700)
                    ),
                    alignment=ft.Alignment.CENTER,
                    ink=True,
                    data=(string_num, fret),
                    on_click=self._on_cell_clicked,
                )
                fret_cells.append(fret_cell)

            rows.append(ft.Row(controls=fret_cells, spacing=2))

        self.neck_column.controls = rows
        try:
            self.update()
        except Exception:
            pass

    def _on_cell_clicked(self, e) -> None:
        string_num, fret = e.control.data
        tuning = self.profile.to_tuning_tuples()

        if 1 <= string_num <= len(tuning):
            open_midi = self.univ_instrument.get_open_string_midi(string_num)
            target_midi = open_midi + fret
            note_name, octave = BaseInstrument.midi_to_note(target_midi)

            self.active_markers[(string_num, fret)] = {
                "note": note_name,
                "octave": octave,
                "color": ft.Colors.CYAN_400,
                "label": f"{note_name}{octave}",
            }
            self.render_fretboard()

            if self.on_fret_clicked:
                self.on_fret_clicked(string_num, fret, note_name, octave)
