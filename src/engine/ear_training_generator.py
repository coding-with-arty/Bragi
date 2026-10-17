import random
from typing import List
from enum import Enum
from pydantic import BaseModel
from utils.music_theory import (
    MusicTheory,
    NOTE_TO_PITCH_INDEX,
    CHROMATIC_SHARPS,
    INTERVAL_SEMITONES,
)
from models.chord import ChordQuality


class EarTrainingCategory(str, Enum):
    INTERVAL = "INTERVAL"
    CHORD_QUALITY = "CHORD_QUALITY"
    PITCH_DISCRIMINATION = "PITCH_DISCRIMINATION"


class EarTrainingQuestion(BaseModel):
    category: EarTrainingCategory
    question_text: str
    options: List[str]
    correct_answer: str
    pitch_classes: List[int]
    explanation: str
    octave: int = 4

    @property
    def prompt_text(self) -> str:
        """Alias property mapping question_text to prompt_text for EarTrainingView compatibility."""
        return self.question_text


class EarTrainingGenerator:
    """Generates dynamic ear training quiz questions with validated Pydantic models."""

    @staticmethod
    def generate_question(
        category: EarTrainingCategory,
        difficulty: str = "BEGINNER"
    ) -> EarTrainingQuestion:
        if category == EarTrainingCategory.CHORD_QUALITY:
            return EarTrainingGenerator._gen_chord_quality(difficulty)
        elif category == EarTrainingCategory.INTERVAL:
            return EarTrainingGenerator._gen_interval(difficulty)
        else:
            return EarTrainingGenerator._gen_chord_quality(difficulty)

    @staticmethod
    def _gen_chord_quality(difficulty: str) -> EarTrainingQuestion:
        root = random.choice(CHROMATIC_SHARPS)
        qualities = [
            ChordQuality.MAJOR,
            ChordQuality.MINOR,
            ChordQuality.DOMINANT_7TH,
            ChordQuality.MAJOR_7TH,
            ChordQuality.SUS4,
        ]
        selected_quality = random.choice(qualities)
        correct_name = selected_quality.value if isinstance(selected_quality.value, str) else str(selected_quality)

        note_names = MusicTheory.get_chord_pitch_classes(root, selected_quality)

        # Map pitch class string note names into integer chromatic indices (0-11) for Pydantic validation
        pitch_indices = [
            NOTE_TO_PITCH_INDEX.get(MusicTheory.note_to_pitch_class(note), 0)
            for note in note_names
        ]

        options = [q.value if isinstance(q.value, str) else str(q) for q in qualities]

        return EarTrainingQuestion(
            category=EarTrainingCategory.CHORD_QUALITY,
            question_text=f"Identify the chord quality with root note {root}:",
            options=options,
            correct_answer=correct_name,
            pitch_classes=pitch_indices,
            explanation=f"{root} {correct_name} consists of pitch classes: {', '.join(note_names)}.",
            octave=4,
        )

    @staticmethod
    def _gen_interval(difficulty: str) -> EarTrainingQuestion:
        root = random.choice(CHROMATIC_SHARPS)
        interval_names = list(INTERVAL_SEMITONES.keys())
        selected_interval = random.choice(interval_names)

        root_idx = NOTE_TO_PITCH_INDEX.get(MusicTheory.note_to_pitch_class(root), 0)
        semi_offset = INTERVAL_SEMITONES.get(selected_interval, 0)
        target_idx = (root_idx + semi_offset) % 12

        return EarTrainingQuestion(
            category=EarTrainingCategory.INTERVAL,
            question_text=f"Identify the interval starting from {root}:",
            options=interval_names[:5],
            correct_answer=selected_interval,
            pitch_classes=[root_idx, target_idx],
            explanation=f"The interval from {root} ({selected_interval}) measures {semi_offset} semitones.",
            octave=4,
        )
