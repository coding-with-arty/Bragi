"""
src/instruments/base_instrument.py
==================================
Abstract base class defining the instrument profile interface and physical
fretboard coordinate mapping logic for fretted instruments.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Optional

# Standard pitch class semitone mapping modulo 12
PITCH_CLASS_MAP: Dict[str, int] = {
    "C": 0, "C#": 1, "DB": 1,
    "D": 2, "D#": 3, "EB": 3,
    "E": 4, "F": 5, "F#": 6, "GB": 6,
    "G": 7, "G#": 8, "AB": 8,
    "A": 9, "A#": 10, "BB": 10,
    "B": 11
}

NOTE_NAMES_BY_PITCH_CLASS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


class BaseInstrument(ABC):
    """Abstract contract for fretted instruments."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Display name of instrument profile."""
        pass

    @property
    @abstractmethod
    def string_count(self) -> int:
        """Number of physical strings (1 = highest pitch string)."""
        pass

    @property
    @abstractmethod
    def fret_count(self) -> int:
        """Total playable frets available on the neck."""
        pass

    @property
    @abstractmethod
    def default_tuning(self) -> List[Tuple[str, int]]:
        """
        Default open tuning list ordered from String 1 (highest pitch)
        down to String N (lowest pitch).
        Format: [("E", 4), ("B", 3), ("G", 3), ("D", 3), ("A", 2), ("E", 2)]
        """
        pass

    @property
    @abstractmethod
    def fretboard_landmarks(self) -> List[int]:
        """Fret numbers marked with inlay position markers (e.g., [3, 5, 7, 9, 12, 15, 17, 19, 21, 24])."""
        pass

    @staticmethod
    def note_to_midi(note_name: str, octave: int) -> int:
        """Converts note name and octave integer to standard MIDI note number."""
        clean_note = note_name.strip().upper()
        pitch_class = PITCH_CLASS_MAP.get(clean_note)
        if pitch_class is None:
            raise ValueError(f"Invalid note name '{note_name}'.")
        return 12 * (octave + 1) + pitch_class

    @staticmethod
    def midi_to_note(midi_num: int) -> Tuple[str, int]:
        """Converts standard MIDI note number to (note_name, octave)."""
        pitch_class = midi_num % 12
        octave = (midi_num // 12) - 1
        return NOTE_NAMES_BY_PITCH_CLASS[pitch_class], octave

    def get_open_string_midi(self, string_num: int, custom_tuning: Optional[List[Tuple[str, int]]] = None) -> int:
        """
        Calculates open string MIDI pitch for string_num (1-indexed).
        String 1 is highest pitch, String N is lowest pitch.
        """
        tuning = custom_tuning or self.default_tuning
        if not (1 <= string_num <= len(tuning)):
            raise ValueError(f"String index {string_num} out of bounds for {self.name} (1 to {len(tuning)}).")
        note_name, octave = tuning[string_num - 1]
        return self.note_to_midi(note_name, octave)

    def get_note_coordinates(
        self,
        note_name: str,
        octave: int,
        custom_tuning: Optional[List[Tuple[str, int]]] = None,
        active_strings: Optional[List[int]] = None
    ) -> List[Tuple[int, int]]:
        """
        Calculates all playable (string_num, fret_num) physical coordinates for a target note.

        :param note_name: Pitch name, e.g. "C"
        :param octave: Octave integer, e.g. 4
        :param custom_tuning: Optional custom tuning override
        :param active_strings: Optional list of enabled string indices (1-indexed)
        :return: List of (string_num, fret_num) tuples
        """
        target_midi = self.note_to_midi(note_name, octave)
        tuning = custom_tuning or self.default_tuning
        enabled = active_strings if active_strings is not None else list(range(1, len(tuning) + 1))

        coordinates: List[Tuple[int, int]] = []

        for string_num in enabled:
            if not (1 <= string_num <= len(tuning)):
                continue
            open_midi = self.get_open_string_midi(string_num, tuning)
            fret_diff = target_midi - open_midi
            if 0 <= fret_diff <= self.fret_count:
                coordinates.append((string_num, fret_diff))

        return coordinates

    def get_closest_landmark(self, fret_num: int) -> Tuple[int, int]:
        """
        Finds the nearest fretboard landmark fret relative to fret_num.

        :return: Tuple of (landmark_fret, offset_from_landmark)
        """
        if fret_num == 0:
            return 0, 0
        landmarks = self.fretboard_landmarks
        closest = min(landmarks, key=lambda l: abs(l - fret_num))
        offset = fret_num - closest
        return closest, offset
