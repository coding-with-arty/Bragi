import time
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable
from models.audio_frame import AudioFrame
from storage.progress_repository import ProgressRepository


class SessionMode(Enum):
    SINGLE_NOTE = "Single Note"
    CHORD = "Chord"
    SCALE = "Scale"


@dataclass
class SessionState:
    mode: SessionMode
    current_target_name: str = "--"
    score: int = 0
    total_attempts: int = 0
    streak: int = 0
    is_active: bool = False
    start_time: float = 0.0


class SessionController:
    """
    Central controller managing training exercise sessions, response timing,
    auto-advance triggers, and atomic progress persistence.
    """

    def __init__(
        self,
        repository: Optional[ProgressRepository] = None,
        on_state_changed: Optional[Callable[[SessionState], None]] = None,
    ):
        self.repository = repository or ProgressRepository()
        self.on_state_changed = on_state_changed

        self.state = SessionState(mode=SessionMode.SINGLE_NOTE)
        self.hold_start_time: Optional[float] = None
        self.required_hold_sec: float = 0.8

    def start_session(self, mode: SessionMode) -> None:
        """Initializes new exercise training session."""
        self.state = SessionState(
            mode=mode,
            score=0,
            total_attempts=0,
            streak=0,
            is_active=True,
            start_time=time.monotonic(),
        )
        self._notify()

    def set_target(self, target_name: str) -> None:
        """Sets active prompt target and resets hold timers."""
        self.state.current_target_name = target_name
        self.hold_start_time = None
        self._notify()

    def process_match_result(self, is_matched: bool, note_name: str) -> bool:
        """
        Evaluates match state over required hold duration.
        Returns True when match hold condition is fully satisfied.
        """
        if not self.state.is_active or not is_matched:
            self.hold_start_time = None
            return False

        now = time.monotonic()
        if self.hold_start_time is None:
            self.hold_start_time = now
            return False

        elapsed_hold = now - self.hold_start_time
        if elapsed_hold >= self.required_hold_sec:
            # Target successfully matched and held
            self.state.score += 1
            self.state.total_attempts += 1
            self.state.streak += 1

            # Log attempt atomically to SQLite storage repository
            self.repository.log_attempt(
                note_name=note_name,
                is_correct=True,
                response_time_sec=round(now - self.state.start_time, 2),
            )

            self.hold_start_time = None
            self._notify()
            return True

        return False

    def register_incorrect_attempt(self, note_name: str) -> None:
        """Logs an incorrect attempt and resets active streak."""
        if not self.state.is_active:
            return

        self.state.total_attempts += 1
        self.state.streak = 0
        self.repository.log_attempt(
            note_name=note_name,
            is_correct=False,
            response_time_sec=0.0,
        )
        self._notify()

    def _notify(self) -> None:
        if self.on_state_changed:
            try:
                self.on_state_changed(self.state)
            except Exception as err:
                print(f"[SessionController] Notification error: {err}")
