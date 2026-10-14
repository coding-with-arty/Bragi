"""
src/instruments/guitar.py
=========================
Concrete instrument profile for standard, 7-string, and 8-string guitars.
"""

from typing import List, Tuple, Dict
from instruments.base_instrument import BaseInstrument


GUITAR_PRESET_TUNINGS: Dict[str, List[Tuple[str, int]]] = {
    "Guitar (6-String Standard)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2)],
    "Guitar (Drop D)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("D", 2)],
    "Guitar (DADGAD)": [("D", 4), ("A", 3), ("G", 3), ("D", 3), ("A", 2), ("D", 2)],
    "Guitar (7-String Standard)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2), ("B", 1)],
    "Guitar (8-String Standard)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2), ("B", 1), ("F#", 1)],
}


class GuitarProfile(BaseInstrument):
    """Guitar instrument profile supporting 6, 7, and 8-string configurations."""

    def __init__(self, preset_name: str = "Guitar (6-String Standard)", fret_count: int = 24):
        self._preset_name = preset_name if preset_name in GUITAR_PRESET_TUNINGS else "Guitar (6-String Standard)"
        self._fret_count = max(12, min(24, fret_count))
        self._tuning = GUITAR_PRESET_TUNINGS[self._preset_name]

    @property
    def name(self) -> str:
        return self._preset_name

    @property
    def string_count(self) -> int:
        return len(self._tuning)

    @property
    def fret_count(self) -> int:
        return self._fret_count

    @property
    def default_tuning(self) -> List[Tuple[str, int]]:
        return self._tuning

    @property
    def fretboard_landmarks(self) -> List[int]:
        return [3, 5, 7, 9, 12, 15, 17, 19, 21, 24]
