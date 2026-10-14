"""
src/models/chord.py
===================
Pydantic schemas for pitch classes, chord definitions, voicings,
CAGED positions, exercise targets, and match evaluation statements.
"""

from enum import Enum, IntEnum
from typing import Optional, Set, List, Tuple
from time import time
from pydantic import BaseModel, Field, ConfigDict, field_validator


class PitchClass(IntEnum):
    """
    Standard integer pitch class representation modulo 12.
    0 = C, 1 = C#/Db, ..., 11 = B.
    """
    C = 0
    CSHARP = 1
    D = 2
    DSHARP = 3
    E = 4
    F = 5
    FSHARP = 6
    G = 7
    GSHARP = 8
    A = 9
    ASHARP = 10
    B = 11


class ChordQuality(str, Enum):
    """Supported harmonic chord qualities."""
    MAJOR = "Major"
    MINOR = "Minor"
    DIMINISHED = "Diminished"
    AUGMENTED = "Augmented"
    DOMINANT_7TH = "Dominant 7th"
    MAJOR_7TH = "Major 7th"
    MINOR_7TH = "Minor 7th"
    HALF_DIMINISHED_7TH = "Half-Diminished 7th"
    DIMINISHED_7TH = "Diminished 7th"
    SUS2 = "Sus2"
    SUS4 = "Sus4"


class CAGEDPosition(str, Enum):
    """CAGED system fretboard position shapes."""
    C_SHAPE = "C Shape"
    A_SHAPE = "A Shape"
    G_SHAPE = "G Shape"
    E_SHAPE = "E Shape"
    D_SHAPE = "D Shape"
    OPEN = "Open Position"
    CUSTOM = "Custom Position"
    NONE = "Unrestricted"


class FingeringCoordinate(BaseModel):
    """Represents a single string/fret touchpoint for a chord voicing."""
    model_config = ConfigDict(frozen=True)

    string_num: int = Field(..., ge=1, le=8, description="String index (1 = highest pitch string)")
    fret: int = Field(..., ge=0, le=24, description="Fret number (0 = open string)")
    finger: Optional[int] = Field(None, ge=1, le=4, description="Suggested finger (1=Index, 4=Pinky)")
    is_muted: bool = Field(False, description="True if string should be muted/unplayed")
    is_open: bool = Field(False, description="True if string is played un-fretted")


class ChordVoicing(BaseModel):
    """Describes a specific physical arrangement of notes on the fretboard."""
    model_config = ConfigDict(frozen=True)

    voicing_id: str = Field(..., description="Unique voicing identifier, e.g. 'C_Maj_Open'")
    caged_position: CAGEDPosition = Field(CAGEDPosition.NONE)
    fret_range: Tuple[int, int] = Field((0, 3), description="(min_fret, max_fret) span of the shape")
    fingerings: List[FingeringCoordinate] = Field(default_factory=list)
    bass_string: int = Field(5, description="String index producing the primary bass note")


class ChordDefinition(BaseModel):
    """Theoretical definition of a chord (root + quality + pitch class set)."""
    model_config = ConfigDict(frozen=True)

    name: str = Field(..., description="Full display name, e.g., 'C Major'")
    root_note: str = Field(..., description="Root note name, e.g., 'C'")
    quality: ChordQuality = Field(..., description="Chord quality classification")
    pitch_classes: Set[int] = Field(..., description="Set of pitch class integers modulo 12")
    formula_intervals: List[str] = Field(default_factory=list, description="Interval list, e.g. ['1', '3', '5']")

    @field_validator("pitch_classes")
    @classmethod
    def validate_pitch_classes(cls, values: Set[int]) -> Set[int]:
        for p in values:
            if not (0 <= p <= 11):
                raise ValueError(f"Pitch class integer must be between 0 and 11, got {p}")
        return values


class TargetChord(BaseModel):
    """Active exercise target chord presented to the player."""
    model_config = ConfigDict(frozen=True)

    chord_definition: ChordDefinition
    required_voicing: Optional[ChordVoicing] = None
    required_caged_position: CAGEDPosition = CAGEDPosition.NONE
    require_root_bass: bool = False

    @property
    def display_title(self) -> str:
        if self.required_caged_position != CAGEDPosition.NONE:
            return f"{self.chord_definition.name} ({self.required_caged_position.value})"
        return self.chord_definition.name


class ChordMatchStatement(BaseModel):
    """Evaluation result returned when verifying audio input against TargetChord."""
    model_config = ConfigDict(frozen=True)

    is_correct: bool = Field(..., description="True if chord criteria were fully satisfied")
    target_chord_name: str = Field(..., description="Name of target chord")
    detected_pitch_classes: Set[int] = Field(default_factory=set, description="Pitch classes detected in audio")
    missing_pitch_classes: Set[int] = Field(default_factory=set, description="Required chord tones not detected")
    extra_pitch_classes: Set[int] = Field(default_factory=set, description="Non-chord pitch classes detected")
    is_valid_voicing: bool = Field(True, description="True if position/root constraints met")
    cents_error: float = Field(0.0, description="Average pitch deviation in cents")
    elapsed_seconds: float = Field(0.0, description="Time taken to match target")
    timestamp: float = Field(default_factory=time, description="Monotonic evaluation timestamp")
