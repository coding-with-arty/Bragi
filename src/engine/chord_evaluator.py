# src/engine/chord_evaluator.py
import time
from typing import Set, Tuple, Optional
from models.chord import TargetChord, ChordMatchStatement
from models.settings import ValidationMode


class ChordEvaluator:
    """Evaluates detected audio pitch class sets against active target chord definitions."""

    def __init__(
        self,
        hold_duration_sec: float = 0.20,
        lockout_duration_sec: float = 0.50,
        validation_mode: ValidationMode = ValidationMode.RELAXED_PITCH_CLASS,
        max_grace_frames: int = 2
    ) -> None:
        self.hold_duration_sec = hold_duration_sec
        self.lockout_duration_sec = lockout_duration_sec
        self.validation_mode = validation_mode
        self.max_grace_frames = max_grace_frames

        self._target_chord: Optional[TargetChord] = None
        self._hold_start_time: Optional[float] = None
        self._target_set_timestamp: float = time.monotonic()
        self._lockout_until_timestamp: float = 0.0
        self._grace_count: int = 0

    def set_target(self, target_chord: TargetChord) -> None:
        """Sets active target chord and clears state."""
        self._target_chord = target_chord
        self.reset_state()

    def set_validation_mode(self, mode: ValidationMode) -> None:
        """Sets chord recognition validation mode."""
        self.validation_mode = mode

    def reset_state(self) -> None:
        """Resets hold timers and grace frame counters."""
        self._hold_start_time = None
        self._grace_count = 0
        self._lockout_until_timestamp = 0.0
        self._target_set_timestamp = time.monotonic()

    def evaluate_pitch_classes(
        self,
        detected_pitch_classes: Set[int],
        volume_db: float = -30.0,
        min_volume_db: float = -50.0
    ) -> Tuple[bool, Optional[ChordMatchStatement]]:
        """
        Verifies if detected pitch classes satisfy the active target chord.
        """
        now = time.monotonic()
        target = self._target_chord
        if target is None or volume_db < min_volume_db:
            self._hold_start_time = None
            self._grace_count = 0
            return False, None

        required_pcs = target.chord_definition.pitch_classes
        missing_pcs = required_pcs - detected_pitch_classes
        extra_pcs = detected_pitch_classes - required_pcs

        # Primary chord condition: All required chord pitch classes must be present
        is_pitch_set_satisfied = (len(missing_pcs) == 0)

        # Dynamic extra pitch tolerance (allow up to 2 extra for triads, 3 extra for 7th chords)
        max_allowed_extras = 3 if len(required_pcs) >= 4 else 2
        is_extra_acceptable = (len(extra_pcs) <= max_allowed_extras)

        is_frame_valid = is_pitch_set_satisfied and is_extra_acceptable
        match_statement = None

        if now >= self._lockout_until_timestamp:
            if is_frame_valid:
                self._grace_count = 0
                if self._hold_start_time is None:
                    self._hold_start_time = now

                hold_duration = now - self._hold_start_time
                if hold_duration >= self.hold_duration_sec:
                    elapsed = now - self._target_set_timestamp
                    self._lockout_until_timestamp = now + self.lockout_duration_sec
                    self._hold_start_time = None
                    self._grace_count = 0

                    match_statement = ChordMatchStatement(
                        is_correct=True,
                        target_chord_name=target.display_title,
                        detected_pitch_classes=detected_pitch_classes,
                        missing_pitch_classes=missing_pcs,
                        extra_pitch_classes=extra_pcs,
                        is_valid_voicing=True,
                        cents_error=0.0,
                        elapsed_seconds=elapsed,
                        timestamp=time.time()
                    )
            else:
                # Grace period prevents brief transient noise spikes from resetting hold timer immediately
                if self._hold_start_time is not None and self._grace_count < self.max_grace_frames:
                    self._grace_count += 1
                else:
                    self._hold_start_time = None
                    self._grace_count = 0

        return is_frame_valid, match_statement
