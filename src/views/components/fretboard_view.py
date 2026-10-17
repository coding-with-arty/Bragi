import flet as ft
from typing import Optional, Callable, Any, List, Tuple
from utils.music_theory import MusicTheory, NOTE_TO_PITCH_INDEX


class UniversalInstrument:
    """
    Calculates fretboard note coordinates (string number, fret number)
    based on the active instrument tuning profile.
    """

    def __init__(self, profile: Any = None):
        self.profile = profile

    def _get_string_tunings(self) -> List[Tuple[int, str, int]]:
        """
        Extracts string tuning tuples (string_num, note_name, octave) from profile.
        Defaults to standard 6-string EADGBE guitar tuning if profile is omitted or empty.
        """
        default_tuning = [
            (1, "E", 4),
            (2, "B", 3),
            (3, "G", 3),
            (4, "D", 3),
            (5, "A", 2),
            (6, "E", 2),
        ]

        if not self.profile:
            return default_tuning

        strings_data = getattr(self.profile, "strings", getattr(self.profile, "tuning", None))
        if not strings_data:
            return default_tuning

        parsed_strings = []
        for idx, item in enumerate(strings_data, start=1):
            if isinstance(item, (list, tuple)):
                s_num = item[0] if len(item) > 0 else idx
                s_note = item[1] if len(item) > 1 else "E"
                s_oct = item[2] if len(item) > 2 else 4
            elif isinstance(item, dict):
                s_num = item.get("string_num", item.get("number", idx))
                s_note = item.get("base_tuning", item.get("note", "E"))
                s_oct = item.get("base_octave", item.get("octave", 4))
            else:
                s_num = getattr(item, "string_number", getattr(item, "number", idx))
                s_note = getattr(item, "note_name", getattr(item, "note", "E"))
                s_oct = getattr(item, "octave", 4)

            parsed_strings.append((int(s_num), str(s_note), int(s_oct)))

        return parsed_strings if parsed_strings else default_tuning

    def get_note_coordinates(
        self,
        target_note: str,
        target_octave: Optional[int] = None,
        max_fret: int = 12
    ) -> List[Tuple[int, int]]:
        """
        Returns a list of (string_number, fret_number) locations matching target note and optional octave.
        """
        locations = []
        target_pc = MusicTheory.note_to_pitch_class(target_note)
        string_tunings = self._get_string_tunings()

        for s_num, base_note, base_oct in string_tunings:
            base_pc = MusicTheory.note_to_pitch_class(base_note)
            base_idx = NOTE_TO_PITCH_INDEX.get(base_pc, 0)
            open_midi = (base_oct + 1) * 12 + base_idx

            for fret in range(0, max_fret + 1):
                fret_midi = open_midi + fret
                note_pc, note_oct = MusicTheory.midi_to_note_and_octave(fret_midi)

                if note_pc == target_pc:
                    if target_octave is None or note_oct == target_octave:
                        locations.append((s_num, fret))

        return locations


class FretboardView(ft.Container):
    """
    Interactive fretboard UI component displaying instrument strings, frets,
    tuning markers, and active target pitch highlights.
    """

    def __init__(
        self,
        profile: Optional[Any] = None,
        instrument_profile: Optional[Any] = None,
        theme_manager: Optional[Any] = None,
        on_fret_click: Optional[Callable] = None,
        on_note_click: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__()
        # Flexible assignment for both 'profile' and 'instrument_profile' arguments
        self.profile = profile or instrument_profile
        self.theme_manager = theme_manager
        self.on_fret_click = on_fret_click or on_note_click

        # Active note target visualizer state
        self.highlighted_locations: List[Tuple[int, int]] = []
        self.highlight_color: Optional[str] = None
        self.highlight_label: Optional[str] = None

        # Expose instrument note-location lookup engine
        self.univ_instrument = UniversalInstrument(self.profile)

        # Visual container configuration
        self.padding = 10
        self.border_radius = 8
        self.bgcolor = getattr(ft.Colors, "SURFACE_VARIANT", "#2A2830")
        self.content = self._build_fretboard()

    def _create_border(self, width: float, color: str) -> Optional[Any]:
        """Safely constructs container borders across different Flet API versions."""
        if hasattr(ft, "Border") and hasattr(ft.Border, "all"):
            return ft.Border.all(width=width, color=color)
        elif hasattr(ft, "border") and hasattr(ft.border, "all"):
            return ft.border.all(width, color)
        elif hasattr(ft, "BorderSide") and hasattr(ft, "Border"):
            side = ft.BorderSide(width, color)
            return ft.Border(top=side, bottom=side, left=side, right=side)
        return None

    def _build_fretboard(self) -> ft.Control:
        """Generates the interactive fretboard layout shell."""
        profile_name = getattr(self.profile, "name", "Standard Guitar") if self.profile else "Standard Guitar"
        num_strings = len(getattr(self.profile, "tuning", [1, 2, 3, 4, 5, 6])) if self.profile else 6

        border_color = getattr(ft.Colors, "OUTLINE_VARIANT", "#444444")
        text_color_primary = getattr(ft.Colors, "WHITE", "#FFFFFF")
        text_color_secondary = getattr(ft.Colors, "GREY_400", "#B0B0B0")
        text_color_tertiary = getattr(ft.Colors, "GREY_300", "#D0D0D0")

        # Format status message based on active target highlights
        if self.highlighted_locations:
            loc_str = ", ".join([f"S{s}:F{f}" for s, f in self.highlighted_locations])
            status_text = f"Target Note: {self.highlight_label or 'Active'} | Locations: [{loc_str}]"
        else:
            status_text = "Fretboard visualizer ready. Play notes on your instrument to see live feedback."

        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Text(
                            f"Fretboard - {profile_name}",
                            size=16,
                            weight=ft.FontWeight.BOLD,
                            color=text_color_primary,
                        ),
                        ft.Text(
                            f"({num_strings} Strings)",
                            size=12,
                            color=text_color_secondary,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    height=140,
                    alignment=ft.Alignment(0, 0),
                    border=self._create_border(1, border_color),
                    border_radius=6,
                    padding=10,
                    content=ft.Text(
                        status_text,
                        size=13,
                        italic=True,
                        color=self.highlight_color or text_color_tertiary,
                    ),
                ),
            ],
            spacing=10,
        )

    def highlight_locations(
        self,
        locations: List[Tuple[int, int]],
        color: Optional[str] = None,
        label: Optional[str] = None
    ) -> None:
        """
        Highlights target fretboard coordinates on the UI.

        Args:
            locations: List of (string_number, fret_number) tuples.
            color: Optional color hex string or Flet color constant.
            label: Target note label (e.g. 'C#').
        """
        self.highlighted_locations = locations or []
        self.highlight_color = color or getattr(ft.Colors, "AMBER_400", "#FFC107")
        self.highlight_label = label or ""
        self.content = self._build_fretboard()
        if self.page:
            self.update()

    def set_profile(self, new_profile: Any) -> None:
        """Updates active profile and re-renders fretboard strings and tuning."""
        self.profile = new_profile
        self.univ_instrument = UniversalInstrument(self.profile)
        self.content = self._build_fretboard()
        if self.page:
            self.update()

    def set_instrument_profile(self, profile: Any) -> None:
        """Updates active instrument profile to support TrainerView component calls."""
        self.set_profile(profile)
