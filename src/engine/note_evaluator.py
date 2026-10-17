from dataclasses import dataclass
from typing import Optional, Tuple, Any
from models.audio_frame import AudioFrame
from utils.music_theory import MusicTheory


@dataclass(frozen=True)
class EvaluatedPitchPayload:
    """
    Lightweight payload representing evaluated pitch analysis results for UI consumption.
    """
    frequency_hz: float = 0.0
    pitch_class: str = "--"
    octave: int = 0
    midi_note: int = 0
    cents_deviation: float = 0.0
    confidence: float = 0.0
    is_in_tune: bool = False
    raw_pitch_str: str = "--"

    @property
    def cents(self) -> float:
        """Alias property for cents_deviation to satisfy audio worker consumers."""
        return self.cents_deviation

    @property
    def frequency(self) -> float:
        """Alias property for frequency_hz."""
        return self.frequency_hz

    @property
    def note_name(self) -> str:
        """Alias property for pitch_class."""
        return self.pitch_class

    @property
    def is_silent(self) -> bool:
        """Returns True if no pitch is detected or frame is silent."""
        return self.pitch_class in ("--", "", "SILENCE")


@dataclass(frozen=True)
class SingleNoteMatchStatement:
    """Evaluation result for a single-note pitch attempt."""
    target_note: str
    target_octave: Optional[int]
    detected_note: str
    detected_octave: int
    cents_error: float
    is_correct: bool
    is_octave_match: bool


class NoteEvaluator:
    """
    Evaluates single-note pitch accuracy with octave flexibility and customizable DSP tolerance settings.
    """

    def __init__(
        self,
        require_octave_match: bool = False,
        cent_tolerance: float = 25.0,
        tolerance_cents: Optional[float] = None,
        min_volume_db: float = -40.0,
        hold_duration_sec: float = 0.5,
        **kwargs
    ):
        self.require_octave_match = require_octave_match
        self.cent_tolerance = tolerance_cents if tolerance_cents is not None else cent_tolerance
        self.min_volume_db = min_volume_db
        self.hold_duration_sec = hold_duration_sec
        self.target_note: Optional[str] = None
        self.target_octave: Optional[int] = None

    def set_target(self, target_note: str, octave: Optional[int] = None) -> None:
        """Updates the active target pitch class and optional octave."""
        self.target_note = target_note
        self.target_octave = octave

    def evaluate(
        self,
        target_note: Optional[str] = None,
        target_octave: Optional[int] = None,
        frame: Optional[AudioFrame] = None,
        detected_note: Optional[str] = None,
        detected_octave: Optional[int] = None,
        cents_error: Optional[float] = None,
        **kwargs
    ) -> SingleNoteMatchStatement:
        """
        Evaluates detected frame audio against the target pitch.
        Uses stored instance target state if explicit target parameters are omitted.
        """
        tgt_note = target_note if target_note is not None else (self.target_note or "--")
        tgt_octave = target_octave if target_octave is not None else self.target_octave

        if frame is not None:
            det_note = frame.pitch_class
            det_oct = frame.octave
            cents_dev = frame.cents_deviation
            is_silent = frame.is_silent
        else:
            det_note = detected_note or kwargs.get("note_name", "--")
            det_oct = detected_octave if detected_octave is not None else kwargs.get("octave", 0)
            cents_dev = cents_error if cents_error is not None else kwargs.get("cents", 0.0)
            is_silent = (det_note == "--")

        if is_silent or det_note == "--":
            return SingleNoteMatchStatement(
                target_note=tgt_note,
                target_octave=tgt_octave,
                detected_note="--",
                detected_octave=0,
                cents_error=0.0,
                is_correct=False,
                is_octave_match=False
            )

        target_pc = MusicTheory.note_to_pitch_class(tgt_note)
        detected_pc = MusicTheory.note_to_pitch_class(det_note)

        is_pc_match = (target_pc == detected_pc) and (abs(cents_dev) <= self.cent_tolerance)
        is_oct_match = (tgt_octave is None) or (tgt_octave == det_oct)

        is_correct = (is_pc_match and is_oct_match) if self.require_octave_match else is_pc_match

        return SingleNoteMatchStatement(
            target_note=tgt_note,
            target_octave=tgt_octave,
            detected_note=det_note,
            detected_octave=det_oct,
            cents_error=cents_dev,
            is_correct=is_correct,
            is_octave_match=is_oct_match
        )

    def evaluate_frame(
        self,
        frame: Optional[AudioFrame] = None,
        target_note: Optional[str] = None,
        target_octave: Optional[int] = None,
        frequency: Optional[float] = None,
        note_name: Optional[str] = None,
        cents: Optional[float] = None,
        volume_db: Optional[float] = None,
        octave: Optional[int] = None,
        **kwargs
    ) -> Tuple[EvaluatedPitchPayload, SingleNoteMatchStatement]:
        """
        Processes incoming pitch metrics (via AudioFrame or explicit keyword arguments)
        and returns a tuple of (EvaluatedPitchPayload, SingleNoteMatchStatement).
        """
        if frame is not None:
            freq = frame.frequency
            pc = frame.pitch_class
            oct_val = frame.octave
            cents_val = frame.cents_deviation
            conf = frame.confidence
            is_silent = frame.is_silent
        else:
            freq = frequency or 0.0
            pc = note_name or kwargs.get("pitch_class", "--")
            oct_val = octave if octave is not None else 0
            cents_val = cents if cents is not None else 0.0
            conf = kwargs.get("confidence", 1.0)
            is_silent = (pc == "--")

        match_stmt = self.evaluate(
            target_note=target_note,
            target_octave=target_octave,
            frame=frame,
            detected_note=pc,
            detected_octave=oct_val,
            cents_error=cents_val
        )

        if not is_silent and pc != "--":
            formatted_pitch = f"{pc}{oct_val}" if oct_val > 0 else pc
            payload = EvaluatedPitchPayload(
                frequency_hz=freq,
                pitch_class=pc,
                octave=oct_val,
                cents_deviation=cents_val,
                confidence=conf,
                is_in_tune=abs(cents_val) <= self.cent_tolerance,
                raw_pitch_str=formatted_pitch
            )
        else:
            payload = EvaluatedPitchPayload()

        return payload, match_stmt
