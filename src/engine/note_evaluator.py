# src/engine/note_evaluator.py
"""
Single Note Evaluator Engine
============================
Provides data models and evaluation logic for single-note pitch accuracy tracking,
cents deviation calculation, and tuning tolerance checks.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvaluatedPitchPayload:
    """Data payload emitted for real-time note pitch analysis."""

    frequency_hz: float = 0.0
    cents_deviation: float = 0.0
    cents: float = 0.0
    volume_db: float = -80.0
    is_silent: bool = True
    raw_pitch_str: str = ""
    is_in_tune: bool = False

    def __post_init__(self):
        # Synchronize cents attribute if cents_deviation was provided
        if self.cents == 0.0 and self.cents_deviation != 0.0:
            self.cents = self.cents_deviation


@dataclass
class SingleNoteMatchStatement:
    """Evaluation result payload emitted upon a successful note match."""

    is_correct: bool = True
    target_note: str = ""
    detected_note: str = ""
    cents_error: float = 0.0


class NoteEvaluator:
    """Evaluates single-note pitch accuracy against a target pitch."""

    def __init__(self, target_note: str = "E", target_octave: int = 4, in_tune_cents_threshold: float = 15.0):
        self.target_note = target_note.upper()
        self.target_octave = target_octave
        self.in_tune_cents_threshold = in_tune_cents_threshold

    def set_target_note(self, note_name: str, octave: int = 4) -> None:
        """Sets the active single-note target."""
        self.target_note = note_name.upper()
        self.target_octave = octave

    def evaluate_pitch(self, detected_note: str, cents_error: float, is_silent: bool = False) -> EvaluatedPitchPayload:
        """Evaluates detected note name and cents error against current target."""
        clean_detected = detected_note.strip().upper()
        is_match = (clean_detected == self.target_note) and not is_silent
        is_in_tune = is_match and (abs(cents_error) <= self.in_tune_cents_threshold)

        return EvaluatedPitchPayload(
            frequency_hz=0.0,
            cents_deviation=cents_error,
            cents=cents_error,
            volume_db=0.0,
            is_silent=is_silent,
            raw_pitch_str=detected_note,
            is_in_tune=is_in_tune,
        )
