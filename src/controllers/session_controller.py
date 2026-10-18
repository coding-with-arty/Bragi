# src/controllers/session_controller.py
"""
Session Controller
==================
Orchestrates real-time practice sessions by evaluating audio match events against
target notes/scales and persisting XP and accuracy metrics into ProgressRepository.
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, List
import time

from engine.note_evaluator import NoteEvaluator, EvaluatedPitchPayload
from storage.progress_repository import ProgressRepository
from utils.music_theory import NOTE_TO_PITCH_INDEX


@dataclass
class PracticeSessionStats:
    """Immutable snapshot of the current practice session metrics."""
    total_attempts: int = 0
    successful_matches: int = 0
    current_streak: int = 0
    total_xp_gained: int = 0
    session_start_time: float = field(default_factory=time.time)

    @property
    def accuracy_percentage(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return (self.successful_matches / self.total_attempts) * 100.0


class SessionController:
    """
    Central controller managing active practice state, match evaluation,
    and database progress logging.
    """

    def __init__(
        self,
        repository: Optional[ProgressRepository] = None,
        evaluator: Optional[NoteEvaluator] = None,
        on_target_changed: Optional[Callable[[str], None]] = None,
        on_match_success: Optional[Callable[[str, int], None]] = None,
    ):
        self.repository = repository or ProgressRepository()
        self.evaluator = evaluator or NoteEvaluator()

        self.on_target_changed = on_target_changed
        self.on_match_success = on_match_success

        self.current_target_note: str = "C"
        self.target_pitch_class: int = 0
        self.stats = PracticeSessionStats()
        self.is_session_active: bool = False
        self._hold_start_time: Optional[float] = None
        self.required_hold_duration_sec: float = 0.5  # Time pitch must remain stable

    def start_session(self, initial_target: str = "C") -> None:
        """Starts a new practice tracking session."""
        self.is_session_active = True
        self.stats = PracticeSessionStats()
        self.set_target_note(initial_target)

    def stop_session(self) -> PracticeSessionStats:
        """Stops the active session and returns final statistics."""
        self.is_session_active = False
        return self.stats

    def set_target_note(self, note_name: str) -> None:
        """Sets a new target note for the trainer."""
        self.current_target_note = note_name.strip().upper()
        self.target_pitch_class = NOTE_TO_PITCH_INDEX.get(self.current_target_note, -1)
        self._hold_start_time = None

        if self.on_target_changed:
            self.on_target_changed(self.current_target_note)

    def process_audio_payload(self, payload: EvaluatedPitchPayload) -> bool:
        """
        Processes incoming real-time audio detection payloads.
        Returns True if target note was successfully matched and sustained.
        """
        if not self.is_session_active or getattr(payload, "is_silent", False):
            self._hold_start_time = None
            return False

        # Compare integer pitch classes (0-11) for type safety
        detected_pc = getattr(payload, "pitch_class", -1) % 12
        is_correct = (detected_pc == self.target_pitch_class)

        # Fallback check if note_name is provided as a string
        note_name_val = getattr(payload, "note_name", None)
        if isinstance(note_name_val, str) and not is_correct:
            is_correct = (note_name_val.strip().upper() == self.current_target_note)

        if is_correct and payload.is_in_tune:
            now = time.time()
            if self._hold_start_time is None:
                self._hold_start_time = now

            # Check if user held the note long enough to satisfy stability threshold
            held_duration = now - self._hold_start_time
            if held_duration >= self.required_hold_duration_sec:
                self._record_successful_attempt(payload)
                self._hold_start_time = None  # Reset hold timer for next target
                return True
        else:
            # Pitch dropped or was incorrect; reset hold timer
            self._hold_start_time = None

        return False

    def _record_successful_attempt(self, payload: EvaluatedPitchPayload) -> None:
        """Records a successful match in memory and writes progress to SQLite database."""
        self.stats.total_attempts += 1
        self.stats.successful_matches += 1
        self.stats.current_streak += 1

        # Calculate XP gained (Base 10 XP + Bonus for high streak)
        xp_earned = 10 + min(self.stats.current_streak * 2, 20)
        self.stats.total_xp_gained += xp_earned

        # Persist to database if repository is available
        if hasattr(self.repository, "log_attempt"):
            try:
                self.repository.log_attempt(
                    note_name=self.current_target_note,
                    is_correct=True,
                    cents_deviation=payload.cents_deviation,
                    xp_earned=xp_earned,
                )
            except Exception:
                pass  # Gracefully catch store log errors without breaking live session

        # Trigger match success callback
        if self.on_match_success:
            self.on_match_success(self.current_target_note, xp_earned)
