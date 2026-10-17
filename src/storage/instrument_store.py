import json
from typing import List, Dict, Any, Optional, Tuple


class InstrumentProfile:
    """
    Data structure representing an instrument tuning profile.
    """

    def __init__(
        self,
        id: str,
        name: str,
        strings: List[Tuple[int, str, int]],
        is_custom: bool = False,
        category: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.strings = strings  # List of (string_number, note_name, octave)
        self.is_custom = is_custom
        self._category = category

    @property
    def category(self) -> str:
        """
        Returns the explicit instrument category or infers it from profile attributes.
        """
        if self._category:
            return self._category
        if self.is_custom:
            return "Custom"

        lower_identifier = f"{self.name} {self.id}".lower()
        if "guitar" in lower_identifier:
            return "Guitar"
        elif "bass" in lower_identifier:
            return "Bass"
        elif "ukulele" in lower_identifier:
            return "Ukulele"
        elif "violin" in lower_identifier:
            return "Violin"
        return "Standard"

    @property
    def tuning(self) -> List[Tuple[int, str, int]]:
        """Alias property for strings to satisfy component view callers."""
        return self.strings

    @property
    def string_count(self) -> int:
        """Returns the total number of strings configured for this instrument profile."""
        return len(self.strings)

    def to_tuning_tuples(self) -> List[Tuple[str, int]]:
        """
        Converts internal string definitions into a list of (note_name, octave) tuples
        expected by TrainerView and other UI components.
        """
        result = []
        for item in self.strings:
            if isinstance(item, (list, tuple)):
                if len(item) >= 3:
                    result.append((str(item[1]), int(item[2])))
                elif len(item) == 2:
                    result.append((str(item[0]), int(item[1])))
            elif isinstance(item, dict):
                note = item.get("base_tuning", item.get("note", "E"))
                octave = item.get("base_octave", item.get("octave", 4))
                result.append((str(note), int(octave)))
        return result


# Standard built-in instrument tuning profiles
BUILTIN_PROFILES: List[InstrumentProfile] = [
    InstrumentProfile(
        id="guitar_standard",
        name="Guitar (Standard EADGBE)",
        category="Guitar",
        strings=[(1, "E", 4), (2, "B", 3), (3, "G", 3), (4, "D", 3), (5, "A", 2), (6, "E", 2)]
    ),
    InstrumentProfile(
        id="guitar_drop_d",
        name="Guitar (Drop D DADGBE)",
        category="Guitar",
        strings=[(1, "E", 4), (2, "B", 3), (3, "G", 3), (4, "D", 3), (5, "A", 2), (6, "D", 2)]
    ),
    InstrumentProfile(
        id="bass_standard",
        name="Bass (Standard EADG)",
        category="Bass",
        strings=[(1, "G", 2), (2, "D", 2), (3, "A", 1), (4, "E", 1)]
    ),
    InstrumentProfile(
        id="ukulele_standard",
        name="Ukulele (Standard GCEA)",
        category="Ukulele",
        strings=[(1, "A", 4), (2, "E", 4), (3, "C", 4), (4, "G", 4)]
    ),
    InstrumentProfile(
        id="violin_standard",
        name="Violin (Standard GDAE)",
        category="Violin",
        strings=[(1, "E", 5), (2, "A", 4), (3, "D", 4), (4, "G", 3)]
    ),
]


class InstrumentStore:
    """
    Manages built-in and custom user instrument tuning profiles.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        # Dictionary storing user-created custom profiles keyed by profile ID
        self._custom_profiles: Dict[str, InstrumentProfile] = {}
        self.load_custom_profiles()

    def load_custom_profiles(self) -> None:
        """Loads persistent custom profiles if a file path is provided."""
        if not self.storage_path:
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    prof = InstrumentProfile(
                        id=item.get("id", "custom"),
                        name=item.get("name", "Custom Instrument"),
                        category=item.get("category", "Custom"),
                        strings=[tuple(s) for s in item.get("strings", [])],
                        is_custom=True
                    )
                    self._custom_profiles[prof.id] = prof
        except (FileNotFoundError, json.JSONDecodeError, Exception):
            pass

    def get_all_profiles(self) -> List[InstrumentProfile]:
        """
        Returns built-in profiles combined with user custom profiles.
        """
        return list(BUILTIN_PROFILES) + list(self._custom_profiles.values())

    def get_profile(self, profile_id: str) -> InstrumentProfile:
        """
        Retrieves a profile by ID or name. Defaults to standard guitar if not found.
        """
        for prof in self.get_all_profiles():
            if prof.id == profile_id or prof.name == profile_id:
                return prof
        return BUILTIN_PROFILES[0]

    def add_custom_profile(self, profile: InstrumentProfile) -> None:
        """Adds or updates a custom instrument profile."""
        profile.is_custom = True
        self._custom_profiles[profile.id] = profile

    def remove_custom_profile(self, profile_id: str) -> None:
        """Removes a custom profile by ID."""
        if profile_id in self._custom_profiles:
            del self._custom_profiles[profile_id]
