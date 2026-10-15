# src/storage/instrument_store.py
import json
from pathlib import Path
from typing import List, Dict, Optional
from models.instrument import InstrumentProfile, StringConfig


BUILTIN_PROFILES: List[InstrumentProfile] = [
    InstrumentProfile(
        id="guitar_6_std",
        name="Guitar (6-String Standard)",
        category="Guitar",
        string_count=6,
        fret_count=24,
        tuning=[
            StringConfig(string_num=1, note_name="E", octave=4),
            StringConfig(string_num=2, note_name="B", octave=3),
            StringConfig(string_num=3, note_name="G", octave=3),
            StringConfig(string_num=4, note_name="D", octave=3),
            StringConfig(string_num=5, note_name="A", octave=2),
            StringConfig(string_num=6, note_name="E", octave=2),
        ],
        fretboard_landmarks=[3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
        is_custom=False
    ),
    InstrumentProfile(
        id="guitar_drop_d",
        name="Guitar (Drop D)",
        category="Guitar",
        string_count=6,
        fret_count=24,
        tuning=[
            StringConfig(string_num=1, note_name="E", octave=4),
            StringConfig(string_num=2, note_name="B", octave=3),
            StringConfig(string_num=3, note_name="G", octave=3),
            StringConfig(string_num=4, note_name="D", octave=3),
            StringConfig(string_num=5, note_name="A", octave=2),
            StringConfig(string_num=6, note_name="D", octave=2),
        ],
        fretboard_landmarks=[3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
        is_custom=False
    ),
    InstrumentProfile(
        id="guitar_7_std",
        name="Guitar (7-String Standard)",
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
        is_custom=False
    ),
    InstrumentProfile(
        id="guitar_8_std",
        name="Guitar (8-String Standard)",
        category="Guitar",
        string_count=8,
        fret_count=24,
        tuning=[
            StringConfig(string_num=1, note_name="E", octave=4),
            StringConfig(string_num=2, note_name="B", octave=3),
            StringConfig(string_num=3, note_name="G", octave=3),
            StringConfig(string_num=4, note_name="D", octave=3),
            StringConfig(string_num=5, note_name="A", octave=2),
            StringConfig(string_num=6, note_name="E", octave=2),
            StringConfig(string_num=7, note_name="B", octave=1),
            StringConfig(string_num=8, note_name="F#", octave=1),
        ],
        fretboard_landmarks=[3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
        is_custom=False
    ),
    InstrumentProfile(
        id="bass_4_std",
        name="Bass (4-String Standard)",
        category="Bass",
        string_count=4,
        fret_count=24,
        tuning=[
            StringConfig(string_num=1, note_name="G", octave=2),
            StringConfig(string_num=2, note_name="D", octave=2),
            StringConfig(string_num=3, note_name="A", octave=1),
            StringConfig(string_num=4, note_name="E", octave=1),
        ],
        fretboard_landmarks=[3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
        is_custom=False
    ),
    InstrumentProfile(
        id="bass_5_std",
        name="Bass (5-String Standard)",
        category="Bass",
        string_count=5,
        fret_count=24,
        tuning=[
            StringConfig(string_num=1, note_name="G", octave=2),
            StringConfig(string_num=2, note_name="D", octave=2),
            StringConfig(string_num=3, note_name="A", octave=1),
            StringConfig(string_num=4, note_name="E", octave=1),
            StringConfig(string_num=5, note_name="B", octave=0),
        ],
        fretboard_landmarks=[3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
        is_custom=False
    ),
    InstrumentProfile(
        id="bass_6_std",
        name="Bass (6-String Standard)",
        category="Bass",
        string_count=6,
        fret_count=24,
        tuning=[
            StringConfig(string_num=1, note_name="C", octave=3),
            StringConfig(string_num=2, note_name="G", octave=2),
            StringConfig(string_num=3, note_name="D", octave=2),
            StringConfig(string_num=4, note_name="A", octave=1),
            StringConfig(string_num=5, note_name="E", octave=1),
            StringConfig(string_num=6, note_name="B", octave=0),
        ],
        fretboard_landmarks=[3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
        is_custom=False
    ),
    InstrumentProfile(
        id="ukulele_std",
        name="Ukulele (Regular 4-String)",
        category="Ukulele",
        string_count=4,
        fret_count=18,
        tuning=[
            StringConfig(string_num=1, note_name="A", octave=4),
            StringConfig(string_num=2, note_name="E", octave=4),
            StringConfig(string_num=3, note_name="C", octave=4),
            StringConfig(string_num=4, note_name="G", octave=4),
        ],
        fretboard_landmarks=[5, 7, 10, 12, 15],
        is_custom=False
    ),
    InstrumentProfile(
        id="ukulele_baritone",
        name="Ukulele (Baritone 4-String)",
        category="Ukulele",
        string_count=4,
        fret_count=18,
        tuning=[
            StringConfig(string_num=1, note_name="E", octave=4),
            StringConfig(string_num=2, note_name="B", octave=3),
            StringConfig(string_num=3, note_name="G", octave=3),
            StringConfig(string_num=4, note_name="D", octave=3),
        ],
        fretboard_landmarks=[5, 7, 10, 12, 15],
        is_custom=False
    ),
    InstrumentProfile(
        id="mandolin_std",
        name="Mandolin (Standard 4-Course)",
        category="Mandolin",
        string_count=4,
        fret_count=20,
        tuning=[
            StringConfig(string_num=1, note_name="E", octave=5),
            StringConfig(string_num=2, note_name="A", octave=4),
            StringConfig(string_num=3, note_name="D", octave=4),
            StringConfig(string_num=4, note_name="G", octave=3),
        ],
        fretboard_landmarks=[3, 5, 7, 10, 12, 15],
        is_custom=False
    ),
    InstrumentProfile(
        id="banjo_5_std",
        name="Banjo (5-String Open G)",
        category="Banjo",
        string_count=5,
        fret_count=22,
        tuning=[
            StringConfig(string_num=1, note_name="D", octave=4),
            StringConfig(string_num=2, note_name="B", octave=3),
            StringConfig(string_num=3, note_name="G", octave=3),
            StringConfig(string_num=4, note_name="D", octave=3),
            StringConfig(string_num=5, note_name="G", octave=4),
        ],
        fretboard_landmarks=[3, 5, 7, 10, 12, 15, 17, 19, 22],
        is_custom=False
    ),
]


class InstrumentStore:
    """Manages built-in instrument profiles and persisted custom user instruments."""

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            data_dir = Path.home() / ".FretSense"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.storage_file = data_dir / "custom_instruments.json"
        else:
            self.storage_file = storage_path

        self._custom_profiles: Dict[str, InstrumentProfile] = {}
        self._load_custom_instruments()

    def get_all_profiles(self) -> List[InstrumentProfile]:
        """Returns built-in profiles joined with user custom profiles."""
        return BUILTIN_PROFILES + list(self._custom_profiles.values())

    def get_profile_by_name(self, name: str) -> Optional[InstrumentProfile]:
        """Finds profile matching title string."""
        for prof in self.get_all_profiles():
            if prof.name == name:
                return prof
        return None

    def save_custom_instrument(self, profile: InstrumentProfile) -> bool:
        """Saves or updates a custom InstrumentProfile on disk."""
        updated = profile.model_copy(update={"is_custom": True})
        self._custom_profiles[updated.id] = updated
        return self._persist_to_disk()

    def delete_custom_instrument(self, profile_id: str) -> bool:
        """Deletes custom instrument by ID."""
        if profile_id in self._custom_profiles:
            del self._custom_profiles[profile_id]
            return self._persist_to_disk()
        return False

    def _load_custom_instruments(self) -> None:
        if not self.storage_file.exists():
            return
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    prof = InstrumentProfile.model_validate(item)
                    self._custom_profiles[prof.id] = prof
        except Exception as err:
            print(f"[InstrumentStore] Failed to load custom instruments: {err}")

    def _persist_to_disk(self) -> bool:
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json_data = [p.model_dump() for p in self._custom_profiles.values()]
                json.dump(json_data, f, indent=2)
            return True
        except Exception as err:
            print(f"[InstrumentStore] Failed to save custom instruments: {err}")
            return False
