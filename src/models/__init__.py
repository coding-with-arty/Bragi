"""
src/models/__init__.py
======================
Re-exports all core data schemas for models module.
"""

from models.chord import (
    PitchClass,
    ChordQuality,
    CAGEDPosition,
    FingeringCoordinate,
    ChordVoicing,
    ChordDefinition,
    TargetChord,
    ChordMatchStatement,
)

from models.settings import (
    DetectionMode,
    PracticeMode,
    ValidationMode,
    AudioSettings,
    ChordFilterSettings,
    TrainerSettings,
)

from models.progress import (
    AttemptRecord,
    ChordStatSummary,
    SessionProgress,
)

__all__ = [
    # Chord schemas
    "PitchClass",
    "ChordQuality",
    "CAGEDPosition",
    "FingeringCoordinate",
    "ChordVoicing",
    "ChordDefinition",
    "TargetChord",
    "ChordMatchStatement",
    # Settings schemas
    "DetectionMode",
    "PracticeMode",
    "ValidationMode",
    "AudioSettings",
    "ChordFilterSettings",
    "TrainerSettings",
    # Progress schemas
    "AttemptRecord",
    "ChordStatSummary",
    "SessionProgress",
]
