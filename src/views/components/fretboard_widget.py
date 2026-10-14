"""
src/views/components/fretboard_widget.py
========================================
Visual fretboard widget rendering instrument neck, frets, string lines,
inlay markers, and target fingering dots.
"""

from typing import List, Optional
import flet as ft
from models.chord import FingeringCoordinate


class FretboardWidget(ft.Container):
    """Renders a responsive visual fretboard grid with frets, strings, and fingering markers."""

    def __init__(
        self,
        string_count: int = 6,
        display_fret_count: int = 5,
        start_fret: int = 0,
        fingerings: Optional[List[FingeringCoordinate]] = None
    ):
        super().__init__()
        self.string_count = string_count
        self.display_fret_count = display_fret_count
        self.start_fret = start_fret
        self.fingerings = fingerings or []

        self.padding = 12
        self.border_radius = 12
        self.bgcolor = "#2A2435"
        self.border = ft.Border.all(1, "#4E4162")

        self.content = self._build_fretboard_grid()

    def set_fingerings(
        self,
        fingerings: List[FingeringCoordinate],
        string_count: int = 6,
        start_fret: int = 0
    ) -> None:
        """Updates fingering dot markers and rebuilds grid visual."""
        self.fingerings = fingerings
        self.string_count = string_count
        self.start_fret = start_fret
        self.content = self._build_fretboard_grid()
        if self.page:
            self.page.update()

    def _build_fretboard_grid(self) -> ft.Control:
        """Constructs the fretboard neck layout grid."""
        columns = []

        # Header row showing fret numbers
        fret_header_controls = [ft.Container(width=40, content=ft.Text("Str", size=10, weight=ft.FontWeight.BOLD))]
        for fret_idx in range(self.start_fret, self.start_fret + self.display_fret_count + 1):
            fret_label = "Nut" if fret_idx == 0 else f"F{fret_idx}"
            fret_header_controls.append(
                ft.Container(
                    width=44,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Text(fret_label, size=11, weight=ft.FontWeight.BOLD, color=ft.Colors.AMBER_400)
                )
            )

        columns.append(ft.Row(controls=fret_header_controls, alignment=ft.MainAxisAlignment.CENTER))

        # Render rows per string (1 = High pitch top row)
        fingering_map = {(f.string_num, f.fret): f for f in self.fingerings}

        for s_num in range(1, self.string_count + 1):
            row_controls = [
                ft.Container(
                    width=40,
                    alignment=ft.Alignment.CENTER_LEFT,
                    content=ft.Text(f"S{s_num}", size=11, color=ft.Colors.GREY_400)
                )
            ]

            for fret_idx in range(self.start_fret, self.start_fret + self.display_fret_count + 1):
                coord = fingering_map.get((s_num, fret_idx))

                cell_content = None
                bg_col = "#1E1A26"
                border_style = ft.Border.all(1, "#3E354A")

                if coord:
                    if coord.is_muted:
                        cell_content = ft.Text("X", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.RED_400)
                    elif coord.is_open and fret_idx == 0:
                        cell_content = ft.Text("O", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_400)
                    else:
                        finger_text = str(coord.finger) if coord.finger else "•"
                        cell_content = ft.Container(
                            width=26,
                            height=26,
                            shape=ft.BoxShape.CIRCLE,
                            bgcolor=ft.Colors.AMBER_500,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(finger_text, size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK)
                        )

                cell = ft.Container(
                    width=44,
                    height=36,
                    bgcolor=bg_col,
                    border=border_style,
                    alignment=ft.Alignment.CENTER,
                    content=cell_content
                )
                row_controls.append(cell)

            columns.append(ft.Row(controls=row_controls, alignment=ft.MainAxisAlignment.CENTER))

        return ft.Column(controls=columns, spacing=4)
