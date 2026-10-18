# src/utils/music_theory.py
"""
Music Theory Utilities
======================
Provides chromatic pitch definitions, pitch index mappings, scale, chord, and interval
formulas, tuning reference constants (A440_HZ), and the MusicTheory helper class.
"""

import random
from typing import Dict, List, Union, Any, Optional, Tuple

# Standard pitch reference constants
A440_HZ: float = 440.0
CONCERT_A_MIDI: int = 69

# Chromatic pitch class definitions
CHROMATIC_SHARPS: List[str] = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
]

CHROMATIC_FLATS: List[str] = [
    "C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"
]

# Note to Pitch Index Mapping (0-11)
NOTE_TO_PITCH_INDEX: Dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1,
    "D": 2, "D#": 3, "Eb": 3,
    "E": 4,
    "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10,
    "B": 11,
}

# Standard musical interval definitions in semitones
INTERVAL_SEMITONES: Dict[str, int] = {
    "Unison": 0,
    "Minor 2nd": 1,
    "Major 2nd": 2,
    "Minor 3rd": 3,
    "Major 3rd": 4,
    "Perfect 4th": 5,
    "Tritone": 6,
    "Perfect 5th": 7,
    "Minor 6th": 8,
    "Major 6th": 9,
    "Minor 7th": 10,
    "Major 7th": 11,
    "Octave": 12,
}

# Scale interval formulas (semitones from root)
SCALE_PATTERNS: Dict[str, List[int]] = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Minor": [0, 2, 3, 5, 7, 8, 10],
    "Pentatonic Major": [0, 2, 4, 7, 9],
    "Pentatonic Minor": [0, 3, 5, 7, 10],
    "Blues": [0, 3, 5, 6, 7, 10],
    "Dorian": [0, 2, 3, 5, 7, 9, 10],
    "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "Lydian": [0, 2, 4, 6, 7, 9, 11],
    "Phrygian": [0, 1, 3, 5, 7, 8, 10],
    "Harmonic Minor": [0, 2, 3, 5, 7, 8, 11],
    "Melodic Minor": [0, 2, 3, 5, 7, 9, 11],
}

# Chord interval formulas (semitones from root)
CHORD_PATTERNS: Dict[str, List[int]] = {
    "Major": [0, 4, 7],
    "Minor": [0, 3, 7],
    "Dominant 7th": [0, 4, 7, 10],
    "Major 7th": [0, 4, 7, 11],
    "Sus4": [0, 5, 7],
    "Diminished": [0, 3, 6],
    "Augmented": [0, 4, 8],
}


def note_to_pitch_class(note: Union[str, int]) -> int:
    """
    Converts a note string or pitch class integer to its pitch class integer (0-11).
    Handles both integer values and string note names safely.
    """
    if isinstance(note, int):
        return note % 12
    if isinstance(note, str) and note:
        clean_note = note.strip()
        if len(clean_note) > 1:
            clean_note = clean_note[0].upper() + clean_note[1:].lower()
        else:
            clean_note = clean_note.capitalize()
        if clean_note in NOTE_TO_PITCH_INDEX:
            return NOTE_TO_PITCH_INDEX[clean_note]
    return 0


def pitch_class_to_note(
    pitch_class: int,
    prefer_flats: bool = False,
    use_flats: Optional[bool] = None,
) -> str:
    """Converts a pitch class integer (0-11) to its note name string."""
    flats = use_flats if use_flats is not None else prefer_flats
    pc = pitch_class % 12
    return CHROMATIC_FLATS[pc] if flats else CHROMATIC_SHARPS[pc]


def midi_to_frequency(midi_note: int) -> float:
    """Converts a MIDI note number to fundamental frequency in Hertz using A440 reference."""
    return A440_HZ * (2.0 ** ((midi_note - CONCERT_A_MIDI) / 12.0))


def get_chord_pitch_classes(root: str, quality: Union[str, Any]) -> List[int]:
    """Computes pitch class integers (0-11) for a chord given its root note and quality."""
    root_pc = note_to_pitch_class(root)
    q_str = getattr(quality, "value", str(quality))
    intervals = CHORD_PATTERNS.get(q_str, CHORD_PATTERNS.get("Major", [0, 4, 7]))
    return [(root_pc + interval) % 12 for interval in intervals]


def get_chord_note_names(root: str, quality: Union[str, Any]) -> List[str]:
    """Generates note name strings (e.g., ['C', 'E', 'G']) for a given root note and chord quality."""
    pitch_classes = get_chord_pitch_classes(root, quality)
    return [CHROMATIC_SHARPS[pc % 12] for pc in pitch_classes]


def generate_random_note(active_strings: List[Dict[str, Any]]) -> Tuple[int, str, int, str, int]:
    """Generates a random target note along one of the active instrument strings."""
    valid_strings = [s for s in active_strings if s.get("active", True)]
    if not valid_strings:
        valid_strings = active_strings
    chosen_string = random.choice(valid_strings)
    string_num = chosen_string.get("string_num", 1)
    base_tuning = chosen_string.get("tuning", "E")
    base_octave = chosen_string.get("octave", 2)

    fret = random.randint(0, 12)
    open_pc = NOTE_TO_PITCH_INDEX.get(base_tuning, 0)
    target_pc = (open_pc + fret) % 12
    target_note = CHROMATIC_SHARPS[target_pc]
    target_octave = base_octave + ((open_pc + fret) // 12)

    return string_num, base_tuning, base_octave, target_note, target_octave


class MusicTheory:
    """Class wrapper offering core music theory pitch calculations."""

    A440_HZ = A440_HZ
    CONCERT_A_MIDI = CONCERT_A_MIDI
    NOTE_TO_PITCH_INDEX = NOTE_TO_PITCH_INDEX
    CHROMATIC_SHARPS = CHROMATIC_SHARPS
    CHROMATIC_FLATS = CHROMATIC_FLATS
    INTERVAL_SEMITONES = INTERVAL_SEMITONES
    SCALE_PATTERNS = SCALE_PATTERNS
    CHORD_PATTERNS = CHORD_PATTERNS

    @staticmethod
    def note_to_pitch_class(note: Union[str, int]) -> int:
        return note_to_pitch_class(note)

    @staticmethod
    def pitch_class_to_note(
        pitch_class: int,
        prefer_flats: bool = False,
        use_flats: Optional[bool] = None,
    ) -> str:
        return pitch_class_to_note(pitch_class, prefer_flats=prefer_flats, use_flats=use_flats)

    @staticmethod
    def get_scale_notes(root: str, scale_type: str = "Major") -> List[str]:
        """Generates note names for a given root and scale type."""
        root_pc = note_to_pitch_class(root)
        pattern = SCALE_PATTERNS.get(scale_type, SCALE_PATTERNS["Major"])
        return [CHROMATIC_SHARPS[(root_pc + interval) % 12] for interval in pattern]

    @staticmethod
    def get_chord_pitch_classes(root: str, quality: Union[str, Any]) -> List[int]:
        return get_chord_pitch_classes(root, quality)

    @staticmethod
    def get_chord_note_names(root: str, quality: Union[str, Any]) -> List[str]:
        return get_chord_note_names(root, quality)

    @staticmethod
    def generate_random_note(active_strings: List[Dict[str, Any]]) -> Tuple[int, str, int, str, int]:
        return generate_random_note(active_strings)

    @staticmethod
    def midi_to_frequency(midi_note: int) -> float:
        return midi_to_frequency(midi_note)
