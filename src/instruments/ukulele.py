"""
src/instruments/ukulele.py
==========================
Concrete instrument profile for regular and baritone ukuleles.
"""

from typing import List, Tuple, Dict
from instruments.base_instrument import BaseInstrument


UKULELE_PRESET_TUNINGS: Dict[str, List[Tuple[str, int]]] = {
    "Ukulele (Regular 4-String)": [("A", 4), ("E", 4), ("C", 4), ("G", 4)],
    "Ukulele (Baritone 4-String)": [("E", 4), ("B", 3), ("G", 3), ("D", 3)],
}


class UkuleleProfile(BaseInstrument):
    """Ukulele profile supporting standard reentrant and baritone tunings."""

    def __init__(self, preset_name: str = "Ukulele (Regular 4-String)", fret_count: int = 18):
        self._preset_name = preset_name if preset_name in UKULELE_PRESET_TUNINGS else "Ukulele (Regular 4-String)"
        self._fret_count = max(12, min(20, fret_count))
        self._tuning = UKULELE_PRESET_TUNINGS[self._preset_name]

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
        return [5, 7, 10, 12, 15]
