# src/utils/music_theory.py
import random
from typing import List, Tuple, Dict, Set, Optional
from models.chord import PitchClass, ChordQuality

NOTES: List[str] = [
    "C", "C#", "Db", "D", "D#", "Eb", "E", "F",
    "F#", "Gb", "G", "G#", "Ab", "A", "A#", "Bb", "B"
]

CHROMATIC_SHARPS: List[str] = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
CHROMATIC_FLATS: List[str] = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

NOTE_TO_PITCH_INDEX: Dict[str, int] = {
    "C": 0, "C#": 1, "DB": 1,
    "D": 2, "D#": 3, "EB": 3,
    "E": 4, "F": 5, "F#": 6, "GB": 6,
    "G": 7, "G#": 8, "AB": 8,
    "A": 9, "A#": 10, "BB": 10,
    "B": 11
}

# Musical Interval Semitone Distances
INTERVAL_SEMITONES: Dict[str, int] = {
    "P1": 0,   # Perfect Unison / Root
    "m2": 1,   # Minor 2nd
    "M2": 2,   # Major 2nd
    "m3": 3,   # Minor 3rd
    "M3": 4,   # Major 3rd
    "P4": 5,   # Perfect 4th
    "d5": 6,   # Diminished 5th / Tritone
    "P5": 7,   # Perfect 5th
    "A5": 8,   # Augmented 5th
    "m6": 8,   # Minor 6th
    "M6": 9,   # Major 6th
    "d7": 9,   # Diminished 7th
    "m7": 10,  # Minor 7th
    "M7": 11,  # Major 7th
    "P8": 12,  # Octave
    "M9": 14,  # Major 9th
}

A440_HZ: float = 440.0

CHORD_FORMULAS: Dict[ChordQuality, List[int]] = {
    ChordQuality.MAJOR: [0, 4, 7],                    # Root, M3, P5
    ChordQuality.MINOR: [0, 3, 7],                    # Root, m3, P5
    ChordQuality.DIMINISHED: [0, 3, 6],               # Root, m3, d5
    ChordQuality.AUGMENTED: [0, 4, 8],                # Root, M3, A5
    ChordQuality.DOMINANT_7TH: [0, 4, 7, 10],         # Root, M3, P5, m7
    ChordQuality.MAJOR_7TH: [0, 4, 7, 11],            # Root, M3, P5, M7
    ChordQuality.MINOR_7TH: [0, 3, 7, 10],            # Root, m3, P5, m7
    ChordQuality.HALF_DIMINISHED_7TH: [0, 3, 6, 10],   # Root, m3, d5, m7
    ChordQuality.DIMINISHED_7TH: [0, 3, 6, 9],        # Root, m3, d5, d7
    ChordQuality.SUS2: [0, 2, 7],                     # Root, M2, P5
    ChordQuality.SUS4: [0, 5, 7],                     # Root, P4, P5
}

CHORD_INTERVAL_NAMES: Dict[ChordQuality, List[str]] = {
    ChordQuality.MAJOR: ["1", "3", "5"],
    ChordQuality.MINOR: ["1", "b3", "5"],
    ChordQuality.DIMINISHED: ["1", "b3", "b5"],
    ChordQuality.AUGMENTED: ["1", "3", "#5"],
    ChordQuality.DOMINANT_7TH: ["1", "3", "5", "b7"],
    ChordQuality.MAJOR_7TH: ["1", "3", "5", "7"],
    ChordQuality.MINOR_7TH: ["1", "b3", "5", "b7"],
    ChordQuality.HALF_DIMINISHED_7TH: ["1", "b3", "b5", "b7"],
    ChordQuality.DIMINISHED_7TH: ["1", "b3", "b5", "bb7"],
    ChordQuality.SUS2: ["1", "2", "5"],
    ChordQuality.SUS4: ["1", "4", "5"],
}

PRESET_TUNINGS: Dict[str, List[Tuple[str, int]]] = {
    "Guitar (6-String Standard)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2)],
    "Guitar (Drop D)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("D", 2)],
    "Guitar (DADGAD)": [("D", 4), ("A", 3), ("G", 3), ("D", 3), ("A", 2), ("D", 2)],
    "Guitar (7-String Standard)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2), ("B", 1)],
    "Guitar (8-String Standard)": [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2), ("B", 1), ("F#", 1)],
    "Bass (4-String Standard)": [("G", 2), ("D", 2), ("A", 1), ("E", 1)],
    "Bass (5-String Standard)": [("G", 2), ("D", 2), ("A", 1), ("E", 1), ("B", 0)],
    "Ukulele (Regular 4-String)": [("A", 4), ("E", 4), ("C", 4), ("G", 4)],
    "Ukulele (Baritone 4-String)": [("E", 4), ("B", 3), ("G", 3), ("D", 3)],
    "Custom": []
}


class MusicTheory:
    """Core music theory static helpers and harmonic calculators."""

    @staticmethod
    def get_notes() -> List[str]:
        return NOTES

    @staticmethod
    def get_presets() -> List[str]:
        return list(PRESET_TUNINGS.keys())

    @staticmethod
    def get_preset_tuning(preset_name: str) -> List[Tuple[str, int]]:
        return PRESET_TUNINGS.get(preset_name, [])

    @staticmethod
    def set_custom_tuning(tuning_list: List[Tuple[str, int]], preset_name: str = "Custom") -> None:
        """Sets or updates a custom tuning configuration in the preset lookup."""
        PRESET_TUNINGS[preset_name] = list(tuning_list)

    @staticmethod
    def note_to_pitch_class(note_name: str) -> int:
        clean = note_name.strip().upper()
        if clean not in NOTE_TO_PITCH_INDEX:
            raise ValueError(f"Unknown note name: '{note_name}'")
        return NOTE_TO_PITCH_INDEX[clean]

    @staticmethod
    def pitch_class_to_note(pitch_class: int, use_flats: bool = False) -> str:
        pc = pitch_class % 12
        return CHROMATIC_FLATS[pc] if use_flats else CHROMATIC_SHARPS[pc]

    @staticmethod
    def get_chord_pitch_classes(root_note: str, quality: ChordQuality) -> Set[int]:
        root_pc = MusicTheory.note_to_pitch_class(root_note)
        offsets = CHORD_FORMULAS.get(quality, [0, 4, 7])
        return {(root_pc + offset) % 12 for offset in offsets}

    @staticmethod
    def get_chord_note_names(root_note: str, quality: ChordQuality, use_flats: bool = False) -> List[str]:
        root_pc = MusicTheory.note_to_pitch_class(root_note)
        offsets = CHORD_FORMULAS.get(quality, [0, 4, 7])
        return [MusicTheory.pitch_class_to_note(root_pc + offset, use_flats=use_flats) for offset in offsets]

    @staticmethod
    def calculate_target_octave(base_note: str, base_octave: int, target_note: str) -> int:
        base_idx = NOTE_TO_PITCH_INDEX.get(base_note.upper(), 0)
        target_idx = NOTE_TO_PITCH_INDEX.get(target_note.upper(), 0)

        semitone_diff = target_idx - base_idx
        if semitone_diff < 0:
            semitone_diff += 12

        return base_octave + (semitone_diff // 12)

    @staticmethod
    def generate_random_note(active_strings: List[dict]) -> Tuple[int, str, int, str, int]:
        enabled = [s for s in active_strings if s.get("active", True)]
        if not enabled:
            return (1, "E", 4, "C", 4)

        target_str = random.choice(enabled)
        target_note = random.choice(NOTES)
        base_note = target_str.get("tuning", "E")
        base_octave = target_str.get("octave", 2)

        target_octave = MusicTheory.calculate_target_octave(base_note, base_octave, target_note)
        return (target_str["string_num"], base_note, base_octave, target_note, target_octave)
