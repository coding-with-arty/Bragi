# src/views/components/fretboard_view.py
"""
Fretboard Visualizer Component
==============================
Interactive graphical fretboard rendering guitar/bass strings, frets, octave markers,
scale/chord tone position highlights, and touch interaction callbacks.
"""

from typing import List, Union, Dict, Tuple, Optional, Callable
import flet as ft

from models.instrument import InstrumentProfile
from utils.theme_manager import ThemeManager
from utils.music_theory import MusicTheory, CHROMATIC_SHARPS


def get_string_open_pc(string_cfg) -> int:
    """Safely computes open string pitch class integer (0-11) from StringConfig."""
    note_name = getattr(string_cfg, "note_name", None)
    if note_name:
        return MusicTheory.note_to_pitch_class(note_name)
    return getattr(string_cfg, "open_pitch_class", getattr(string_cfg, "pitch_class", 0))


class UniversalInstrumentAdapter:
    """Helper adapter providing fretboard note coordinate lookups for TrainerView."""

    def __init__(self, profile: InstrumentProfile):
        self.profile = profile

    def get_note_coordinates(
        self, target_note: str, octave: Optional[int] = None
    ) -> List[Tuple[int, int]]:
        """Calculates (string_num, fret) positions matching a target note and optional octave."""
        coords = []
        target_pc = MusicTheory.note_to_pitch_class(target_note)

        if not self.profile or not self.profile.tuning:
            return coords

        for string_idx, string_cfg in enumerate(self.profile.tuning):
            string_num = string_idx + 1
            open_pc = get_string_open_pc(string_cfg)
            open_octave = getattr(string_cfg, "octave", 2)

            for fret in range(0, 25):
                pos_pc = (open_pc + fret) % 12
                pos_octave = open_octave + ((open_pc + fret) // 12)

                if pos_pc == target_pc:
                    if octave is None or pos_octave == octave:
                        coords.append((string_num, fret))

        return coords


class FretboardView(ft.Container):
    """Visual fretboard component for displaying active note positions and scale highlights."""

    def __init__(
        self,
        profile: InstrumentProfile,
        visible_frets: int = 15,
        on_fret_clicked: Optional[Callable[[int, int, str, int], None]] = None,
        theme_manager: Optional[ThemeManager] = None,
    ):
        super().__init__()
        self.profile = profile
        self.visible_frets = visible_frets
        self.on_fret_clicked = on_fret_clicked
        self.theme_manager = theme_manager

        self.active_markers: List[Dict] = []
        self.univ_instrument = UniversalInstrumentAdapter(self.profile)

        # Container styling
        self.bgcolor = ft.Colors.with_opacity(0.12, "#130F1C")
        self.border = ft.Border.all(1, ft.Colors.with_opacity(0.3, "#3E354A"))
        self.border_radius = 12
        self.padding = 16

        self.content = self._build_fretboard_grid()

    def set_instrument_profile(self, profile: InstrumentProfile) -> None:
        """Updates active instrument profile and rebuilds fretboard grid."""
        self.profile = profile
        self.univ_instrument = UniversalInstrumentAdapter(profile)
        self.content = self._build_fretboard_grid()
        self._safe_update()

    def highlight_locations(
        self,
        locations: List[Tuple[int, int]],
        color: str = ft.Colors.AMBER_400,
        label: str = "",
    ) -> None:
        """Highlights specific (string_num, fret) positions on the fretboard."""
        self.active_markers.clear()
        for loc in locations:
            if isinstance(loc, (list, tuple)) and len(loc) >= 2:
                string_num, fret = loc[0], loc[1]
                string_idx = string_num - 1 if string_num > 0 else 0
                self.active_markers.append({
                    "string_idx": string_idx,
                    "fret": fret,
                    "note_name": label,
                    "color": color,
                    "is_root": True,
                })
        self.content = self._build_fretboard_grid()
        self._safe_update()

    def clear_markers(self) -> None:
        """Clears all active note markers from the fretboard."""
        self.active_markers.clear()
        self.content = self._build_fretboard_grid()
        self._safe_update()

    def highlight_scale_positions(
        self,
        positions: List[Union[Dict, Tuple]],
        root_color: str = ft.Colors.AMBER_400,
        note_color: str = ft.Colors.CYAN_400,
    ) -> None:
        """Highlights scale positions on the fretboard."""
        self.active_markers.clear()

        for item in positions:
            if isinstance(item, dict):
                string_idx = item.get("string_idx", item.get("string_num", 0))
                fret = item.get("fret", 0)
                note_name = item.get("note_name", "")
                is_root = item.get("is_root", False)
            elif isinstance(item, (list, tuple)):
                if len(item) == 4:
                    string_idx, fret, note_name, is_root = item
                elif len(item) == 3:
                    string_idx, fret, is_root = item
                    note_name = ""
                else:
                    continue
            else:
                continue

            marker_color = root_color if is_root else note_color
            self.active_markers.append({
                "string_idx": string_idx,
                "fret": fret,
                "note_name": note_name,
                "color": marker_color,
                "is_root": is_root,
            })

        self.content = self._build_fretboard_grid()
        self._safe_update()

    def _safe_update(self) -> None:
        try:
            if self.page:
                self.page.update()
        except RuntimeError:
            pass

    def _handle_fret_click(self, string_idx: int, fret: int) -> None:
        """Invokes on_fret_clicked callback with pitch class and octave details."""
        if not self.on_fret_clicked or not self.profile or not self.profile.tuning:
            return

        string_num = string_idx + 1
        if string_idx < len(self.profile.tuning):
            string_cfg = self.profile.tuning[string_idx]
            open_pc = get_string_open_pc(string_cfg)
            open_oct = getattr(string_cfg, "octave", 2)
        else:
            open_pc, open_oct = 0, 2

        pos_pc = (open_pc + fret) % 12
        octave = open_oct + ((open_pc + fret) // 12)
        note_name = CHROMATIC_SHARPS[pos_pc]

        self.on_fret_clicked(string_num, fret, note_name, octave)

    def _build_fretboard_grid(self) -> ft.Control:
        fret_columns = []

        # Fret Header Row
        header_cells = [
            ft.Container(
                content=ft.Text(f"{fret}", size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.GREY_500),
                width=36,
                alignment=ft.Alignment.CENTER,
            )
            for fret in range(0, self.visible_frets + 1)
        ]
        fret_columns.append(ft.Row(controls=header_cells, spacing=2))

        # Instrument Strings
        string_count = len(self.profile.tuning) if self.profile and self.profile.tuning else 6

        for string_idx in range(string_count):
            string_cells = []
            for fret in range(0, self.visible_frets + 1):
                marker = next(
                    (m for m in self.active_markers if m["string_idx"] == string_idx and m["fret"] == fret),
                    None
                )

                if marker:
                    cell_content = ft.Container(
                        content=ft.Text(
                            marker["note_name"] if marker["note_name"] else ("R" if marker.get("is_root") else "•"),
                            size=10,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLACK if marker.get("is_root") else ft.Colors.WHITE,
                        ),
                        width=22,
                        height=22,
                        border_radius=11,
                        bgcolor=marker["color"],
                        alignment=ft.Alignment.CENTER,
                    )
                else:
                    cell_content = ft.Container(
                        height=2,
                        bgcolor=ft.Colors.with_opacity(0.3, ft.Colors.GREY_600),
                    )

                s_idx, f_num = string_idx, fret
                cell_container = ft.Container(
                    content=cell_content,
                    width=36,
                    height=28,
                    alignment=ft.Alignment.CENTER,
                    border=ft.Border(
                        right=ft.BorderSide(1, ft.Colors.with_opacity(0.2, ft.Colors.GREY_700))
                    ),
                    ink=True,
                    on_click=lambda e, s=s_idx, f=f_num: self._handle_fret_click(s, f),
                )
                string_cells.append(cell_container)

            fret_columns.append(ft.Row(controls=string_cells, spacing=2))

        return ft.Column(controls=fret_columns, spacing=4)
