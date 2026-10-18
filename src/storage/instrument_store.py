# src/storage/instrument_store.py
"""
Instrument Store Utility
========================
Manages built-in instrument profiles (Guitar, Bass, Ukulele, Mandolin, Banjo)
and user custom profiles stored in custom_instruments.json.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from models.instrument import InstrumentProfile, StringConfig
from storage.path_utils import get_user_instruments_path

# --- BUILT-IN GUITAR PROFILES ---
STANDARD_GUITAR = InstrumentProfile(
    id="standard_guitar",
    name="Standard 6-String Guitar",
    category="Guitar",
    string_count=6,
    fret_count=22,
    tuning=[
        StringConfig(string_num=1, note_name="E", octave=4),
        StringConfig(string_num=2, note_name="B", octave=3),
        StringConfig(string_num=3, note_name="G", octave=3),
        StringConfig(string_num=4, note_name="D", octave=3),
        StringConfig(string_num=5, note_name="A", octave=2),
        StringConfig(string_num=6, note_name="E", octave=2),
    ],
    fretboard_landmarks=[3, 5, 7, 9, 12, 15, 17, 19, 21],
    is_custom=False,
)

GUITAR_7_STRING = InstrumentProfile(
    id="guitar_7_string",
    name="7-String Guitar (Low B)",
    category="Guitar",
    string_count=7,
    fret_count=24,
    tuning=[
        StringConfig(string_num=1, note_name="E", octave=4),
        StringConfig(string_num=2, note_name="B", octave=3),
        StringConfig(string_num=3, note_name="G", octave=3),
        StringConfig(string_num=4, note_name="D", octave=3),
        StringConfig(string_num=5, note_name="A", octave=2),
        StringConfig(string_num=6, note_name="E", octave=2),
        StringConfig(string_num=7, note_name="B", octave=1),
    ],
    fretboard_landmarks=[3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
    is_custom=False,
)

BASS_4_STRING = InstrumentProfile(
    id="bass_4_string",
    name="4-String Bass",
    category="Bass",
    string_count=4,
    fret_count=20,
    tuning=[
        StringConfig(string_num=1, note_name="G", octave=2),
        StringConfig(string_num=2, note_name="D", octave=2),
        StringConfig(string_num=3, note_name="A", octave=1),
        StringConfig(string_num=4, note_name="E", octave=1),
    ],
    fretboard_landmarks=[3, 5, 7, 9, 12, 15, 17, 19],
    is_custom=False,
)

BUILTIN_PROFILES: Dict[str, InstrumentProfile] = {
    "standard_guitar": STANDARD_GUITAR,
    "guitar_7_string": GUITAR_7_STRING,
    "bass_4_string": BASS_4_STRING,
}


class InstrumentStore:
    """Store class managing built-in and custom instrument profiles."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.storage_path = storage_path or get_user_instruments_path()
        self._profiles: Dict[str, InstrumentProfile] = dict(BUILTIN_PROFILES)
        self._load_custom_instruments()

    def get_default_profile(self) -> InstrumentProfile:
        return self._profiles.get("standard_guitar", STANDARD_GUITAR)

    def get_all_profiles(self) -> List[InstrumentProfile]:
        return list(self._profiles.values())

    def get_profile(self, profile_id: str) -> Optional[InstrumentProfile]:
        return self._profiles.get(profile_id)

    def save_custom_instrument(self, profile: InstrumentProfile) -> None:
        """Saves a custom instrument profile and persists it to disk."""
        profile.is_custom = True
        self._profiles[profile.id] = profile
        self._persist_custom_instruments()

    def delete_custom_instrument(self, profile_id: str) -> None:
        """Deletes a custom instrument profile from memory and disk."""
        if profile_id in self._profiles and self._profiles[profile_id].is_custom:
            del self._profiles[profile_id]
            self._persist_custom_instruments()

    def _load_custom_instruments(self) -> None:
        """Loads user custom instrument profiles from custom_instruments.json."""
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    prof = InstrumentProfile.model_validate(item)
                    self._profiles[prof.id] = prof
        except Exception as err:
            print(f"[InstrumentStore] Failed to load custom instruments: {err}")

    def _persist_custom_instruments(self) -> None:
        """Saves all custom profiles to disk as JSON."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            custom_list = [
                p.model_dump() for p in self._profiles.values() if p.is_custom
            ]
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(custom_list, f, indent=2)
        except Exception as err:
            print(f"[InstrumentStore] Failed to save custom instruments: {err}")
