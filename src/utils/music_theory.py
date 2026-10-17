import random
from typing import List, Tuple, Dict, Any
from models.chord import ChordQuality

# Base pitch lists and constants
CHROMATIC_SHARPS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTES = CHROMATIC_SHARPS
A440_HZ = 440.0

# Lookup dictionary mapping note spellings to chromatic pitch indices (0-11)
NOTE_TO_PITCH_INDEX: Dict[str, int] = {
    "C": 0, "C#": 1, "DB": 1,
    "D": 2, "D#": 3, "EB": 3,
    "E": 4, "FB": 4, "E#": 5,
    "F": 5, "F#": 6, "GB": 6,
    "G": 7, "G#": 8, "AB": 8,
    "A": 9, "A#": 10, "BB": 10,
    "B": 11, "CB": 11, "B#": 0,
}

# Musical interval semitone distances for ear training analysis
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

# Chord structure interval definitions
CHORD_FORMULAS: Dict[Any, List[int]] = {
    ChordQuality.MAJOR: [0, 4, 7],
    ChordQuality.MINOR: [0, 3, 7],
    ChordQuality.DOMINANT_7TH: [0, 4, 7, 10],
    ChordQuality.MAJOR_7TH: [0, 4, 7, 11],
    ChordQuality.SUS4: [0, 5, 7],
    "Major": [0, 4, 7],
    "Minor": [0, 3, 7],
    "Dominant 7th": [0, 4, 7, 10],
    "Major 7th": [0, 4, 7, 11],
    "Sus4": [0, 5, 7],
}


class MusicTheory:
    """Utility class for music theory calculations, chromatic pitch indexing, and MIDI conversions."""

    @staticmethod
    def note_to_pitch_class(note_name: str) -> str:
        """Normalizes note names into standard chromatic sharps (e.g., Db -> C#)."""
        cleaned = str(note_name).strip().upper()
        enharmonics = {
            "DB": "C#", "EB": "D#", "FB": "E", "GB": "F#",
            "AB": "G#", "BB": "A#", "CB": "B", "E#": "F", "B#": "C"
        }
        return enharmonics.get(cleaned, cleaned)

    @staticmethod
    def pitch_class_to_note(pitch_class: Any) -> str:
        """
        Converts an integer pitch index (0-11) or pitch class string into standard note notation.
        """
        if isinstance(pitch_class, int):
            return CHROMATIC_SHARPS[pitch_class % 12]
        return MusicTheory.note_to_pitch_class(str(pitch_class))

    @staticmethod
    def midi_to_note_and_octave(midi_note: int) -> Tuple[str, int]:
        """
        Converts a MIDI note integer (e.g., 60) into pitch class string ("C") and octave (4).
        """
        pitch_class = CHROMATIC_SHARPS[midi_note % 12]
        octave = (midi_note // 12) - 1
        return pitch_class, octave

    @staticmethod
    def get_chord_pitch_classes(root: str, quality: ChordQuality) -> List[str]:
        """Returns the list of pitch classes comprising a chord defined by root and quality."""
        root_pc = MusicTheory.note_to_pitch_class(root)
        root_idx = CHROMATIC_SHARPS.index(root_pc)
        intervals = CHORD_FORMULAS.get(quality, [0, 4, 7])
        return [CHROMATIC_SHARPS[(root_idx + semi) % 12] for semi in intervals]

    @staticmethod
    def get_chord_note_names(root: str, quality: ChordQuality) -> List[str]:
        """Returns full note names for a given chord specification."""
        return MusicTheory.get_chord_pitch_classes(root, quality)

    @staticmethod
    def generate_random_note(active_strings: Any, max_fret: int = 12) -> Tuple[int, str, int, str, int]:
        """
        Selects a random string from active_strings and a random fret (0 to max_fret),
        calculating the resulting target note and octave.

        Returns: (string_num, base_tuning, base_octave, target_note, target_octave)
        """
        if not active_strings:
            string_item = (1, "E", 4)
        else:
            string_item = random.choice(list(active_strings))

        if isinstance(string_item, (list, tuple)):
            string_num = string_item[0]
            base_tuning = string_item[1] if len(string_item) > 1 else "E"
            base_octave = string_item[2] if len(string_item) > 2 else 4
        elif isinstance(string_item, dict):
            string_num = string_item.get("string_num", string_item.get("number", 1))
            base_tuning = string_item.get("base_tuning", string_item.get("note", "E"))
            base_octave = string_item.get("base_octave", string_item.get("octave", 4))
        else:
            string_num = getattr(string_item, "string_number", getattr(string_item, "number", 1))
            base_tuning = getattr(string_item, "note_name", getattr(string_item, "note", "E"))
            base_octave = getattr(string_item, "octave", 4)

        base_pc = MusicTheory.note_to_pitch_class(str(base_tuning))
        base_idx = NOTE_TO_PITCH_INDEX.get(base_pc, 0)
        base_midi = (int(base_octave) + 1) * 12 + base_idx

        fret = random.randint(0, max_fret)
        target_midi = base_midi + fret
        target_note, target_octave = MusicTheory.midi_to_note_and_octave(target_midi)

        return int(string_num), base_pc, int(base_octave), target_note, target_octave
