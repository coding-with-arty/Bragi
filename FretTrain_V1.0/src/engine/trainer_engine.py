"""
trainer_engine.py
=================
State engine managing note training queues and progression logic.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True, slots=True)
class NotePrompt:
    """Represents a target note prompt on the fretboard."""
    note_name: str        # E.g., "B"
    string_num: int       # 1 to 6 (6 = Low E, 1 = High E)
    fret_num: int         # 0 = Open string
    display_label: str    # E.g., "B on A String (Fret 2)"


class TrainerEngine:
    """Tracks queue progress and handles note sequence transitions."""

    def __init__(self, prompts: Optional[List[NotePrompt]] = None) -> None:
        self._prompts: List[NotePrompt] = prompts or self._default_prompts()
        self._current_index: int = 0
        self.completed_count: int = 0

    @staticmethod
    def _default_prompts() -> List[NotePrompt]:
        """Sample sequence of prompts across different strings."""
        return [
            NotePrompt("B", 5, 2, "B on A String (Fret 2)"),
            NotePrompt("C", 5, 3, "C on A String (Fret 3)"),
            NotePrompt("E", 6, 0, "Open E String (String 6)"),
            NotePrompt("G", 6, 3, "G on Low E String (Fret 3)"),
            NotePrompt("D", 4, 0, "Open D String (String 4)"),
            NotePrompt("A", 1, 5, "A on High E String (Fret 5)"),
        ]

    @property
    def current_prompt(self) -> Optional[NotePrompt]:
        if self._current_index < len(self._prompts):
            return self._prompts[self._current_index]
        return None

    def advance(self) -> Optional[NotePrompt]:
        """Moves to the next note in the trainer queue."""
        self.completed_count += 1
        self._current_index += 1
        if self._current_index >= len(self._prompts):
            self._current_index = 0
        return self.current_prompt

    def reset(self) -> None:
        self._current_index = 0
        self.completed_count = 0
