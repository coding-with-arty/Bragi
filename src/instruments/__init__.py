"""
src/instruments/__init__.py
===========================
Re-exports instrument profiles and factory loader.
"""

from typing import Dict, Type
from instruments.base_instrument import BaseInstrument, PITCH_CLASS_MAP, NOTE_NAMES_BY_PITCH_CLASS
from instruments.guitar import GuitarProfile, GUITAR_PRESET_TUNINGS
from instruments.bass import BassProfile, BASS_PRESET_TUNINGS
from instruments.ukulele import UkuleleProfile, UKULELE_PRESET_TUNINGS


def get_instrument_profile(preset_name: str) -> BaseInstrument:
    """
    Factory function instantiating the appropriate BaseInstrument profile
    matching preset_name.
    """
    if preset_name in GUITAR_PRESET_TUNINGS:
        return GuitarProfile(preset_name)
    elif preset_name in BASS_PRESET_TUNINGS:
        return BassProfile(preset_name)
    elif preset_name in UKULELE_PRESET_TUNINGS:
        return UkuleleProfile(preset_name)
    else:
        # Default fallback
        return GuitarProfile("Guitar (6-String Standard)")


__all__ = [
    "BaseInstrument",
    "GuitarProfile",
    "BassProfile",
    "UkuleleProfile",
    "PITCH_CLASS_MAP",
    "NOTE_NAMES_BY_PITCH_CLASS",
    "get_instrument_profile",
]
