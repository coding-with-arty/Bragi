# src/engine/chord_generator.py
"""
Chord Generator Engine
======================
Generates target chords with pitch class mapping, defensive filter unpacking,
and Pydantic model validation compatibility.
"""

from enum import Enum
import random
from typing import Any, List, Optional, Set
from models.chord import ChordDefinition, TargetChord
from utils.music_theory import CHROMATIC_SHARPS, get_chord_pitch_classes


class ChordQuality(str, Enum):
    """Core chord quality definitions matching standard musical notation."""

    MAJOR = "Major"
    MINOR = "Minor"
    DOM7 = "Dominant 7th"
    MAJ7 = "Major 7th"
    SUS4 = "Sus4"
    DIMINISHED = "Diminished"
    AUGMENTED = "Augmented"
    MIN7 = "Minor 7th"
    HALF_DIM7 = "Half-Diminished 7th"
    DIM7 = "Diminished 7th"
    SUS2 = "Sus2"


# Default focused qualities for chord practice
FOCUSED_QUALITIES: List[ChordQuality] = [
    ChordQuality.MAJOR,
    ChordQuality.MINOR,
    ChordQuality.DOM7,
    ChordQuality.MAJ7,
    ChordQuality.SUS4,
]

VALID_QUALITY_VALUES: Set[str] = {q.value for q in ChordQuality}


class ChordGenerator:
    """Generates random target chords from filtered qualities with schema safety."""

    @staticmethod
    def _extract_qualities_list(allowed_qualities: Any) -> List[Any]:
        """Defensively unpacks chord filters from dicts, Pydantic models, sets, or lists."""
        if not allowed_qualities:
            return list(FOCUSED_QUALITIES)

        # Handle dictionary containers (e.g. {'selected_keys': [...]})
        if isinstance(allowed_qualities, dict):
            if "selected_keys" in allowed_qualities:
                return allowed_qualities["selected_keys"]
            if "qualities" in allowed_qualities:
                return allowed_qualities["qualities"]
            if "allowed_qualities" in allowed_qualities:
                return allowed_qualities["allowed_qualities"]
            return list(allowed_qualities.values())

        # Handle Pydantic objects or custom settings classes with properties
        if hasattr(allowed_qualities, "selected_keys"):
            return getattr(allowed_qualities, "selected_keys")
        if hasattr(allowed_qualities, "qualities"):
            return getattr(allowed_qualities, "qualities")
        if hasattr(allowed_qualities, "allowed_qualities"):
            return getattr(allowed_qualities, "allowed_qualities")

        if isinstance(allowed_qualities, (list, set, tuple)):
            return list(allowed_qualities)

        return list(FOCUSED_QUALITIES)

    @classmethod
    def generate_target(
        cls,
        allowed_qualities: Optional[Any] = None
    ) -> TargetChord:
        """
        Generates a TargetChord object for a random root note and chord quality.
        Unpacks filter inputs defensively and aligns with Pydantic ChordDefinition schema.
        """
        raw_list = cls._extract_qualities_list(allowed_qualities)

        # Filter and extract valid chord quality strings
        valid_extracted: List[str] = []
        for item in raw_list:
            if hasattr(item, "value"):
                q_str = str(item.value)
            elif isinstance(item, tuple) and len(item) > 0:
                first = item[0]
                q_str = str(first.value) if hasattr(first, "value") else str(first)
            else:
                q_str = str(item)

            if q_str in VALID_QUALITY_VALUES:
                valid_extracted.append(q_str)

        if not valid_extracted:
            valid_extracted = [q.value for q in FOCUSED_QUALITIES]

        selected_quality_str = random.choice(valid_extracted)
        root = random.choice(CHROMATIC_SHARPS)

        # Compute pitch classes (0-11)
        pitch_classes = get_chord_pitch_classes(root, selected_quality_str)
        note_names = [CHROMATIC_SHARPS[pc % 12] for pc in pitch_classes]

        # Construct Pydantic model with required field names
        try:
            chord_def = ChordDefinition(
                name=f"{root} {selected_quality_str}",
                root_note=root,
                quality=selected_quality_str,
                pitch_classes=pitch_classes,
                note_names=note_names,
            )
        except Exception:
            # Fallback for alternative model field naming variants
            kwargs = {
                "name": f"{root} {selected_quality_str}",
                "root_note": root,
                "root": root,
                "quality": selected_quality_str,
                "pitch_classes": pitch_classes,
                "note_names": note_names,
            }
            chord_def = ChordDefinition(**kwargs)

        return TargetChord(chord_definition=chord_def)
