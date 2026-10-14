"""
src/instruments/bass.py
=======================
Concrete instrument profile for 4-string, 5-string, and 6-string electric bass guitars.
"""

from typing import List, Tuple, Dict
from instruments.base_instrument import BaseInstrument


BASS_PRESET_TUNINGS: Dict[str, List[Tuple[str, int]]] = {
    "Bass (4-String Standard)": [("G", 2), ("D", 2), ("A", 1), ("E", 1)],
    "Bass (Drop D)": [("G", 2), ("D", 2), ("A", 1), ("D", 1)],
    "Bass (5-String Standard)": [("G", 2), ("D", 2), ("A", 1), ("E", 1), ("B", 0)],
    "Bass (6-String Standard)": [("C", 3), ("G", 2), ("D", 2), ("A", 1), ("E", 1), ("B", 0)],
}


class BassProfile(BaseInstrument):
    """Bass guitar instrument profile supporting 4, 5, and 6-string configurations."""

    def __init__(self, preset_name: str = "Bass (4-String Standard)", fret_count: int = 24):
        self._preset_name = preset_name if preset_name in BASS_PRESET_TUNINGS else "Bass (4-String Standard)"
        self._fret_count = max(12, min(24, fret_count))
        self._tuning = BASS_PRESET_TUNINGS[self._preset_name]

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
