"""
src/engine/chord_evaluator.py
=============================
Domain evaluator for verifying detected audio pitch class sets against TargetChord definitions.
"""

import time
from typing import Set, Tuple, Optional
from models.chord import TargetChord, ChordMatchStatement
from models.settings import ValidationMode


class ChordEvaluator:
    """Stateful evaluator for chord accuracy, pitch class set matching, and hold timing."""

    def __init__(
        self,
        hold_duration_sec: float = 0.35,
        lockout_duration_sec: float = 0.50,
        validation_mode: ValidationMode = ValidationMode.RELAXED_PITCH_CLASS,
    ) -> None:
        self.hold_duration_sec = hold_duration_sec
        self.lockout_duration_sec = lockout_duration_sec
        self.validation_mode = validation_mode

        self._target_chord: Optional[TargetChord] = None
        self._hold_start_time: Optional[float] = None
        self._target_set_timestamp: float = time.monotonic()
        self._lockout_until_timestamp: float = 0.0

    def set_target(self, target_chord: TargetChord) -> None:
        """Sets the active exercise TargetChord and resets evaluation state."""
        self._target_chord = target_chord
        self.reset_state()

    def set_validation_mode(self, mode: ValidationMode) -> None:
        """Dynamically switches chord validation strictness."""
        self.validation_mode = mode

    def reset_state(self) -> None:
        """Resets debounce hold timestamps."""
        self._hold_start_time = None
        self._lockout_until_timestamp = 0.0
        self._target_set_timestamp = time.monotonic()

    def evaluate_pitch_classes(
        self,
        detected_pitch_classes: Set[int],
        volume_db: float = -30.0,
        min_volume_db: float = -45.0
    ) -> Tuple[bool, Optional[ChordMatchStatement]]:
        """
        Evaluates a set of detected pitch classes against the active target chord.

        :param detected_pitch_classes: Set of integer pitch classes 0..11 present in audio
        :param volume_db: Recorded volume level in dBFS
        :param min_volume_db: Minimum required audio volume threshold
        :return: Tuple of (is_currently_valid_bool, Optional[ChordMatchStatement])
        """
        now = time.monotonic()
        target = self._target_chord
        if target is None or volume_db < min_volume_db:
            self._hold_start_time = None
            return False, None

        required_pcs = target.chord_definition.pitch_classes
        missing_pcs = required_pcs - detected_pitch_classes
        extra_pcs = detected_pitch_classes - required_pcs

        # Core chord validation rule: detected set must be a superset containing all required chord pitch classes
        is_pitch_set_satisfied = len(missing_pcs) == 0

        # Enforce non-chord tone tolerance (allow up to 1 extra pitch class for overtone noise)
        is_extra_acceptable = len(extra_pcs) <= 1

        is_frame_valid = is_pitch_set_satisfied and is_extra_acceptable
        match_statement = None

        if now >= self._lockout_until_timestamp:
            if is_frame_valid:
                if self._hold_start_time is None:
                    self._hold_start_time = now

                hold_duration = now - self._hold_start_time
                if hold_duration >= self.hold_duration_sec:
                    elapsed = now - self._target_set_timestamp
                    self._lockout_until_timestamp = now + self.lockout_duration_sec
                    self._hold_start_time = None

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
                self._hold_start_time = None

        return is_frame_valid, match_statement
