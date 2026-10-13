"""
music_theory.py - Music theory, tuning presets, and pitch conversion helpers[cite: 5].
"""

import random

NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

# Preset string tunings with octave numbers for pitch detection matching
PRESET_TUNINGS = {
    "Guitar (6-String Standard)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2)],
    "Guitar (7-String Standard)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2), ("B", 1)],
    "Guitar (8-String Standard)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2), ("B", 1), ("F#", 1)],
    "Bass (4-String Standard)": [("G", 2), ("D", 2), ("A", 1), ("E", 1)],
    "Bass (5-String Standard)": [("G", 2), ("D", 2), ("A", 1), ("E", 1), ("B", 0)],
    "Ukulele (Regular 4-String)": [("A", 4), ("E", 4), ("C", 4), ("G", 4)],
    "Ukulele (Baritone 4-String)": [("E", 4), ("B", 3), ("G", 3), ("D", 3)],
    "Custom": []
}


class MusicTheory:
    @staticmethod
    def get_notes() -> list[str]:
        return NOTES

    @staticmethod
    def get_presets() -> list[str]:
        return list(PRESET_TUNINGS.keys())

    @staticmethod
    def get_preset_tuning(preset_name: str) -> list[tuple[str, int]]:
        return PRESET_TUNINGS.get(preset_name, [])

    @staticmethod
    def calculate_target_octave(base_note: str, base_octave: int, target_note: str) -> int:
        """Calculates octave for target note relative to base open string tuning."""
        base_idx = NOTES.index(base_note) if base_note in NOTES else 0
        target_idx = NOTES.index(target_note) if target_note in NOTES else 0

        semitone_diff = target_idx - base_idx
        if semitone_diff < 0:
            semitone_diff += 12

        return base_octave + (semitone_diff // 12)

    @staticmethod
    def generate_random_note(active_strings: list[dict]) -> tuple[int, str, int, str, int]:
        """
        Selects a random enabled string and note[cite: 5].
        Returns: (string_num, open_tuning_note, base_octave, target_note, target_octave)
        """
        enabled = [s for s in active_strings if s.get("active", True)]
        if not enabled:
            return (1, "E", 4, "C", 4)

        target_str = random.choice(enabled)
        target_note = random.choice(NOTES)
        base_note = target_str.get("tuning", "E")
        base_octave = target_str.get("octave", 2)

        target_octave = MusicTheory.calculate_target_octave(base_note, base_octave, target_note)
        return (target_str["string_num"], base_note, base_octave, target_note, target_octave)
