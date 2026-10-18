# src/engine/chord_evaluator.py
"""
Chord Evaluator Engine
======================
Evaluates polyphonic pitch detection payloads against target chords,
supporting pitch class matching, volume threshold gating, and hold duration tracking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Tuple, Union
import time

from engine.chord_generator import TargetChord, ChordDefinition


class ValidationMode(str, Enum):
    """Validation modes for chord tone matching."""
    RELAXED_PITCH_CLASS = "RELAXED_PITCH_CLASS"
    STRICT_OCTAVE = "STRICT_OCTAVE"


@dataclass
class ChordEvaluationStatement:
    """Evaluation result payload emitted upon a successful chord hold completion."""
    is_correct: bool = True
    chord_name: str = ""
    target_pitch_classes: List[int] = field(default_factory=list)
    missing_pitch_classes: Set[int] = field(default_factory=set)

    def __str__(self) -> str:
        return self.chord_name


class ChordEvaluator:
    """
    Evaluates polyphonic audio input against a target chord and tracks
    pitch stability over a required hold duration threshold.
    """

    def __init__(
        self,
        target_chord: Optional[Union[TargetChord, ChordDefinition]] = None,
        hold_duration_sec: float = 0.5,
        min_volume_db: float = -40.0,
        validation_mode: ValidationMode = ValidationMode.RELAXED_PITCH_CLASS,
    ):
        self.target_chord = target_chord
        self.hold_duration_sec = hold_duration_sec
        self.min_volume_db = min_volume_db
        self.validation_mode = validation_mode

        self._hold_start_time: Optional[float] = None

    def set_validation_mode(self, mode: Union[ValidationMode, str]) -> None:
        """Updates the validation mode for chord tone matching."""
        if isinstance(mode, ValidationMode):
            self.validation_mode = mode
        else:
            try:
                self.validation_mode = ValidationMode(str(mode))
            except ValueError:
                self.validation_mode = ValidationMode.RELAXED_PITCH_CLASS

    def set_target(self, target: Union[TargetChord, ChordDefinition]) -> None:
        """Sets the active target chord and resets hold time tracking."""
        self.target_chord = target
        self._hold_start_time = None

    def set_target_chord(self, target: Union[TargetChord, ChordDefinition]) -> None:
        """Alias for set_target for backward compatibility."""
        self.set_target(target)

    def _get_target_pitch_classes(self) -> Set[int]:
        """Extracts target pitch classes from target_chord across all schema wrappers."""
        if not self.target_chord:
            return set()

        if hasattr(self.target_chord, "chord_definition") and hasattr(self.target_chord.chord_definition, "pitch_classes"):
            return set(self.target_chord.chord_definition.pitch_classes)
        if hasattr(self.target_chord, "chord_def") and hasattr(self.target_chord.chord_def, "pitch_classes"):
            return set(self.target_chord.chord_def.pitch_classes)
        if hasattr(self.target_chord, "pitch_classes") and self.target_chord.pitch_classes is not None:
            return set(self.target_chord.pitch_classes)

        return set()

    def _get_chord_name(self) -> str:
        """Extracts chord name representation from target_chord."""
        if not self.target_chord:
            return ""

        if hasattr(self.target_chord, "chord_definition") and hasattr(self.target_chord.chord_definition, "name"):
            return self.target_chord.chord_definition.name
        if hasattr(self.target_chord, "chord_def") and hasattr(self.target_chord.chord_def, "name"):
            return self.target_chord.chord_def.name
        if hasattr(self.target_chord, "name"):
            return self.target_chord.name

        return str(self.target_chord)

    def evaluate_pitch_classes(
        self,
        detected_pitch_classes: Union[List[int], Set[int]],
        volume_db: float = 0.0,
        min_volume_db: Optional[float] = None,
    ) -> Tuple[bool, Optional[ChordEvaluationStatement]]:
        """
        Evaluates a set or list of detected pitch classes against the target chord.

        Returns:
            (True, None): Pitch classes match, but required hold duration is not yet reached.
            (True, ChordEvaluationStatement): Pitch classes match and sustained for >= hold_duration_sec.
            (False, None): Pitch class mismatch or volume below threshold.
        """
        threshold_db = min_volume_db if min_volume_db is not None else self.min_volume_db

        if volume_db < threshold_db:
            self._hold_start_time = None
            return False, None

        target_pcs = self._get_target_pitch_classes()
        if not target_pcs:
            self._hold_start_time = None
            return False, None

        detected_pcs = {int(pc) % 12 for pc in detected_pitch_classes}

        if target_pcs.issubset(detected_pcs):
            now = time.time()
            if self._hold_start_time is None:
                self._hold_start_time = now

            elapsed = now - self._hold_start_time
            if elapsed >= self.hold_duration_sec:
                statement = ChordEvaluationStatement(
                    is_correct=True,
                    chord_name=self._get_chord_name(),
                    target_pitch_classes=sorted(list(target_pcs)),
                    missing_pitch_classes=target_pcs - detected_pcs,
                )
                return True, statement
            return True, None

        self._hold_start_time = None
        return False, None

    def evaluate(
        self,
        detected_pitches: List[Union[int, object]],
        volume_db: float = 0.0,
    ) -> bool:
        pcs = []
        for p in detected_pitches:
            if isinstance(p, int):
                pcs.append(p)
            elif hasattr(p, "pitch_class"):
                pcs.append(getattr(p, "pitch_class"))

        is_valid, statement = self.evaluate_pitch_classes(pcs, volume_db=volume_db)
        return is_valid and (statement is not None)
