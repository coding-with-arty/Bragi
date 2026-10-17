from dataclasses import dataclass
from typing import List, Set, Optional
from models.chord import TargetChord
from utils.music_theory import MusicTheory


@dataclass(frozen=True)
class ChordMatchStatement:
    """Evaluation result for a multi-note chord attempt."""
    target_chord_name: str
    target_pitch_classes: List[str]
    detected_pitch_classes: List[str]
    is_correct: bool


class ChordEvaluator:
    """
    Evaluates real-time detected multi-pitch frames against target chord specifications.
    Supports flexible validation modes and sustain timing thresholds.
    """

    def __init__(
        self,
        hold_duration_sec: float = 0.5,
        validation_mode: str = "ALL_NOTES",
        cent_tolerance: float = 25.0,
        **kwargs
    ):
        self.hold_duration_sec = hold_duration_sec
        self.validation_mode = validation_mode
        self.cent_tolerance = cent_tolerance

    def evaluate(self, target_chord: Optional[TargetChord], detected_notes: List[str]) -> ChordMatchStatement:
        """
        Evaluates detected note names against the pitch classes required by target_chord.
        """
        if not target_chord or not target_chord.chord_definition:
            return ChordMatchStatement(
                target_chord_name="--",
                target_pitch_classes=[],
                detected_pitch_classes=[],
                is_correct=False
            )

        target_pcs = set(target_chord.chord_definition.pitch_classes)
        detected_pcs = {MusicTheory.note_to_pitch_class(note) for note in detected_notes if note != "--"}

        if self.validation_mode == "ANY_NOTE":
            is_correct = len(target_pcs.intersection(detected_pcs)) > 0
        else:  # Default to "ALL_NOTES" mode
            is_correct = target_pcs.issubset(detected_pcs) if target_pcs else False

        return ChordMatchStatement(
            target_chord_name=target_chord.chord_definition.name,
            target_pitch_classes=sorted(list(target_pcs)),
            detected_pitch_classes=sorted(list(detected_pcs)),
            is_correct=is_correct
        )
