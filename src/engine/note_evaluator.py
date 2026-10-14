"""
src/engine/note_evaluator.py
============================
Pure domain evaluator for single note pitch verification.
Decoupled from audio hardware and UI components.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
import time
from typing import Optional, Tuple, Dict, Any

from instruments.base_instrument import PITCH_CLASS_MAP


class MatchState(Enum):
    SEARCHING = auto()
    HOLDING = auto()
    LOCKED_OUT = auto()


@dataclass(frozen=True, slots=True)
class TargetNote:
    """Single note exercise target representation."""
    note_name: str
    octave: Optional[int] = None
    string_num: Optional[int] = None

    def __post_init__(self) -> None:
        raw = self.note_name.strip()
        if raw.upper() not in PITCH_CLASS_MAP:
            raise ValueError(f"Invalid target note name '{self.note_name}'.")
        formatted = raw[0].upper() + raw[1:] if len(raw) > 1 else raw.upper()
        object.__setattr__(self, 'note_name', formatted)

    @property
    def display_name(self) -> str:
        if self.octave is not None:
            return f"{self.note_name}{self.octave}"
        return self.note_name


@dataclass(frozen=True, slots=True)
class SingleNoteMatchStatement:
    """Validation result statement for single note pitch matching."""
    is_correct: bool
    status: str
    target_note: str
    detected_note: str
    cents_error: float
    frequency_hz: float
    volume_db: float
    elapsed_seconds: float
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class EvaluatedPitchPayload:
    """Payload emitted per frame with pitch evaluation state."""
    frequency: float
    cents: float
    volume_db: float
    detected_note: str
    octave: int
    is_in_tune: bool
    raw_pitch_str: str


class NoteEvaluator:
    """Stateful evaluator for single-note pitch accuracy and debounce tracking."""

    def __init__(
        self,
        tolerance_cents: float = 25.0,
        min_volume_db: float = -45.0,
        hold_duration_sec: float = 0.30,
        lockout_duration_sec: float = 0.50,
        require_octave_match: bool = False,
    ) -> None:
        self.tolerance_cents = tolerance_cents
        self.min_volume_db = min_volume_db
        self.hold_duration_sec = hold_duration_sec
        self.lockout_duration_sec = lockout_duration_sec
        self.require_octave_match = require_octave_match

        self._target_note: Optional[TargetNote] = None
        self._match_state: MatchState = MatchState.SEARCHING
        self._hold_start_time: Optional[float] = None
        self._target_set_timestamp: float = time.monotonic()
        self._lockout_until_timestamp: float = 0.0

    def set_target(self, note_name: str, octave: Optional[int] = None, string_num: Optional[int] = None) -> None:
        """Sets active target note and resets match debounce tracking."""
        self._target_note = TargetNote(note_name=note_name, octave=octave, string_num=string_num)
        self.reset_state()

    def reset_state(self) -> None:
        """Resets debounce hold tracking state."""
        self._match_state = MatchState.SEARCHING
        self._hold_start_time = None
        self._lockout_until_timestamp = 0.0
        self._target_set_timestamp = time.monotonic()

    def evaluate_frame(
        self,
        frequency: float,
        cents: float,
        volume_db: float,
        detected_note: str,
        octave: int
    ) -> Tuple[EvaluatedPitchPayload, Optional[SingleNoteMatchStatement]]:
        """
        Evaluates a single raw audio frame against the target note.

        :return: Tuple of (EvaluatedPitchPayload, Optional[SingleNoteMatchStatement])
        """
        now = time.monotonic()
        match_statement = None
        target = self._target_note

        raw_str = f"{detected_note}{octave}" if octave > 0 else detected_note
        is_above_noise = volume_db >= self.min_volume_db

        is_note_match = False
        if target is not None:
            target_pitch = PITCH_CLASS_MAP.get(target.note_name.upper())
            detected_pitch = PITCH_CLASS_MAP.get(detected_note.upper())
            name_match = (target_pitch is not None and target_pitch == detected_pitch)
            octave_match = (not self.require_octave_match) or (target.octave is None or octave == target.octave)
            is_note_match = name_match and octave_match

        is_cents_in_tune = abs(cents) <= self.tolerance_cents
        is_frame_valid = is_above_noise and is_note_match and is_cents_in_tune

        if now >= self._lockout_until_timestamp:
            if is_frame_valid:
                if self._hold_start_time is None:
                    self._hold_start_time = now
                    self._match_state = MatchState.HOLDING

                hold_duration = now - self._hold_start_time
                if hold_duration >= self.hold_duration_sec:
                    elapsed_match_time = now - self._target_set_timestamp
                    self._lockout_until_timestamp = now + self.lockout_duration_sec
                    self._match_state = MatchState.LOCKED_OUT
                    self._hold_start_time = None

                    match_statement = SingleNoteMatchStatement(
                        is_correct=True,
                        status="MATCH_CONFIRMED",
                        target_note=target.display_name if target else "N/A",
                        detected_note=raw_str,
                        cents_error=cents,
                        frequency_hz=frequency,
                        volume_db=volume_db,
                        elapsed_seconds=elapsed_match_time,
                    )
            else:
                self._hold_start_time = None
                self._match_state = MatchState.SEARCHING

        pitch_payload = EvaluatedPitchPayload(
            frequency=frequency,
            cents=cents,
            volume_db=volume_db,
            detected_note=detected_note,
            octave=octave,
            is_in_tune=is_frame_valid,
            raw_pitch_str=raw_str,
        )

        return pitch_payload, match_statement
