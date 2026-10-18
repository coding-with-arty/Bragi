# src/engine/scale_sequencer.py
"""
Scale Sequencer Engine
======================
Generates practice sequence patterns (ascending, descending, broken thirds,
randomized) for scale notes to guide structured fretboard drills.
"""

from enum import Enum
from typing import List, Optional
import random


class SequenceDirection(str, Enum):
    """Supported direction patterns for scale sequence generation."""
    ASCENDING = "ASCENDING"
    DESCENDING = "DESCENDING"
    ASCENDING_DESCENDING = "ASCENDING_DESCENDING"
    THIRD_LEAPS = "THIRD_LEAPS"
    RANDOM = "RANDOM"


class ScaleSequencer:
    """
    Manages sequential note progression for scale practice drills.
    Tracks current step, target notes, and pattern direction.
    """

    def __init__(
        self,
        scale_notes: Optional[List[str]] = None,
        direction: SequenceDirection = SequenceDirection.ASCENDING,
    ):
        self.scale_notes: List[str] = scale_notes or []
        self.direction: SequenceDirection = direction
        self.sequence: List[str] = []
        self.current_index: int = 0

        if self.scale_notes:
            self.generate_sequence(self.scale_notes, self.direction)

    def generate_sequence(
        self,
        scale_notes: List[str],
        direction: Optional[SequenceDirection] = None,
    ) -> List[str]:
        """
        Generates an ordered list of target notes based on the requested pattern.
        """
        self.scale_notes = scale_notes
        if direction is not None:
            self.direction = direction

        if not self.scale_notes:
            self.sequence = []
            self.current_index = 0
            return self.sequence

        notes = list(self.scale_notes)

        if self.direction == SequenceDirection.ASCENDING:
            self.sequence = notes
        elif self.direction == SequenceDirection.DESCENDING:
            self.sequence = list(reversed(notes))
        elif self.direction == SequenceDirection.ASCENDING_DESCENDING:
            self.sequence = notes + list(reversed(notes[:-1]))
        elif self.direction == SequenceDirection.THIRD_LEAPS:
            seq = []
            n = len(notes)
            for i in range(n):
                seq.append(notes[i])
                seq.append(notes[(i + 2) % n])
            self.sequence = seq
        elif self.direction == SequenceDirection.RANDOM:
            shuffled = list(notes)
            random.shuffle(shuffled)
            self.sequence = shuffled
        else:
            self.sequence = notes

        self.current_index = 0
        return self.sequence

    def get_current_note(self) -> Optional[str]:
        """Returns the active target note in the sequence."""
        if not self.sequence or self.current_index >= len(self.sequence):
            return None
        return self.sequence[self.current_index]

    def advance(self) -> Optional[str]:
        """Advances to the next note in the sequence and returns it."""
        if not self.sequence:
            return None
        self.current_index = (self.current_index + 1) % len(self.sequence)
        return self.get_current_note()

    def reset(self) -> None:
        """Resets sequence progress back to the first step."""
        self.current_index = 0
