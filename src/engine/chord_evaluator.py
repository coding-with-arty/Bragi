# src/engine/chord_evaluator.py
"""
Chord Evaluator Engine
======================
Evaluates polyphonic pitch detection payloads against target chords,
supporting pitch class matching, volume threshold gating, and essential-tone matching.
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
    detected_pitch_classes: Set[int] = field(default_factory=set)
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
        hold_duration_sec: float = 0.15,
        min_volume_db: float = -45.0,
        validation_mode: ValidationMode = ValidationMode.RELAXED_PITCH_CLASS,
    ):
        self.target_chord = target_chord
        self.hold_duration_sec = hold_duration_sec
        self.min_volume_db = min_volume_db
        self.validation_mode = validation_mode

        self._hold_start_time: Optional[float] = None
        self._last_match_time: Optional[float] = None

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
        self._last_match_time = None

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

    def _get_root_pitch_class(self) -> Optional[int]:
        """Extracts root pitch class integer (0-11) if available."""
        if not self.target_chord:
            return None

        root_note = None
        if hasattr(self.target_chord, "chord_definition") and hasattr(self.target_chord.chord_definition, "root_note"):
            root_note = self.target_chord.chord_definition.root_note
        elif hasattr(self.target_chord, "root_note"):
            root_note = self.target_chord.root_note

        if root_note:
            from utils.music_theory import CHROMATIC_SHARPS
            clean_root = root_note.strip().upper()
            if clean_root in CHROMATIC_SHARPS:
                return CHROMATIC_SHARPS.index(clean_root)
        return None

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
        Uses full subset matching for 3-note triads and essential-tone matching for 4-note 7th chords.
        """
        threshold_db = min_volume_db if min_volume_db is not None else self.min_volume_db
        now = time.time()

        if volume_db < threshold_db:
            if self._last_match_time and (now - self._last_match_time) > 0.2:
                self._hold_start_time = None
            return False, None

        target_pcs = self._get_target_pitch_classes()
        if not target_pcs:
            self._hold_start_time = None
            return False, None

        detected_pcs = {int(pc) % 12 for pc in detected_pitch_classes}
        matching_pcs = target_pcs.intersection(detected_pcs)
        root_pc = self._get_root_pitch_class()

        # Flexible Match Logic:
        # 1. Triads (<= 3 pitch classes): Require all target pitch classes.
        # 2. 7th / Extended Chords (>= 4 pitch classes): Require all target notes OR at least 3 target tones including the root.
        if len(target_pcs) <= 3:
            is_valid_match = target_pcs.issubset(detected_pcs)
        else:
            has_root = (root_pc in detected_pcs) if root_pc is not None else True
            is_valid_match = target_pcs.issubset(detected_pcs) or (len(matching_pcs) >= 3 and has_root)

        if is_valid_match:
            if self._hold_start_time is None:
                self._hold_start_time = now
            self._last_match_time = now

            elapsed = now - self._hold_start_time
            if elapsed >= self.hold_duration_sec:
                statement = ChordEvaluationStatement(
                    is_correct=True,
                    chord_name=self._get_chord_name(),
                    target_pitch_classes=sorted(list(target_pcs)),
                    detected_pitch_classes=detected_pcs,
                    missing_pitch_classes=target_pcs - detected_pcs,
                )
                return True, statement
            return True, None

        if self._last_match_time and (now - self._last_match_time) > 0.2:
            self._hold_start_time = None
        return False, None
