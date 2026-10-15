# src/models/ear_training.py
from enum import Enum
from typing import List, Set, Optional
from pydantic import BaseModel, Field


class EarTrainingCategory(str, Enum):
    """Ear training practice categories."""
    SINGLE_NOTE = "Single Note Identification"
    INTERVAL = "Interval Recognition"
    CHORD_QUALITY = "Chord Quality Identification"
    CHORD_INVERSION = "Chord Inversion Training"


class EarTrainingDifficulty(str, Enum):
    """Skill levels controlling pitch ranges and options."""
    BEGINNER = "Beginner"          # Natural notes, basic triads, open intervals
    INTERMEDIATE = "Intermediate"  # Sharps/Flats, 7th chords, all intervals
    ADVANCED = "Advanced"          # Inversions, extended chords, fast melodic intervals


class IntervalPlayMode(str, Enum):
    """Interval audio playback style."""
    HARMONIC = "Harmonic (Simultaneous)"
    MELODIC_ASCENDING = "Melodic (Ascending)"
    MELODIC_DESCENDING = "Melodic (Descending)"


class EarTrainingQuestion(BaseModel):
    """Data container for an ear training question."""
    category: EarTrainingCategory
    difficulty: EarTrainingDifficulty
    prompt_text: str
    correct_answer: str
    options: List[str]
    pitch_classes: Set[int]
    root_note: str = "C"
    octave: int = 4
    second_note_octave: Optional[int] = None
    second_pitch_class: Optional[int] = None
    interval_mode: IntervalPlayMode = IntervalPlayMode.HARMONIC
    explanation: str = ""
