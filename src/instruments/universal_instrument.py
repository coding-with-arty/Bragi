# src/instruments/universal_instrument.py
from typing import List, Tuple
from instruments.base_instrument import BaseInstrument
from models.instrument import InstrumentProfile, StringConfig


class UniversalInstrumentProfile(BaseInstrument):
    """Dynamic BaseInstrument wrapper operating on InstrumentProfile schemas."""

    def __init__(self, profile: InstrumentProfile):
        self._profile = profile

    @property
    def name(self) -> str:
        return self._profile.name

    @property
    def string_count(self) -> int:
        return self._profile.string_count

    @property
    def fret_count(self) -> int:
        return self._profile.fret_count

    @property
    def default_tuning(self) -> List[Tuple[str, int]]:
        return self._profile.to_tuning_tuples()

    @property
    def fretboard_landmarks(self) -> List[int]:
        return self._profile.fretboard_landmarks

    @property
    def profile(self) -> InstrumentProfile:
        return self._profile
