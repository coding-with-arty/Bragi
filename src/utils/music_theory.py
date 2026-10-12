# src/utils/music_theory.py
import random

NOTES = ["C", "C#", "Db", "D", "D#", "Eb", "E", "F", "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"]

PRESETS = {
    "Guitar (6-String Standard)": ["E", "B", "G", "D", "A", "E"],
    "Guitar (7-String Standard)": ["E", "B", "G", "D", "A", "E", "B"],
    "Guitar (8-String Standard)": ["E", "B", "G", "D", "A", "E", "B", "F#"],
    "Bass (4-String Standard)": ["G", "D", "A", "E"],
    "Bass (5-String Standard)": ["G", "D", "A", "E", "B"],
    "Ukulele (Regular 4-String)": ["A", "E", "C", "G"],
    "Ukulele (5-String)": ["A", "E", "C", "G", "G"],
    "Ukulele (Baritone 4-String)": ["E", "B", "G", "D"],
    "Custom": []
}

class MusicTheory:
    @staticmethod
    def get_notes() -> list[str]:
        return NOTES

    @staticmethod
    def get_presets() -> list[str]:
        return list(PRESETS.keys())

    @staticmethod
    def get_preset_tuning(preset_name: str) -> list[str]:
        return PRESETS.get(preset_name, [])

    @staticmethod
    def generate_random_note(active_strings: list[dict]) -> tuple[int, str, str]:
        enabled = [s for s in active_strings if s.get("active", True)]
        if not enabled:
            return (1, "E", "C")

        target_str = random.choice(enabled)
        note = random.choice(NOTES)
        return (target_str["string_num"], target_str["tuning"], note)
