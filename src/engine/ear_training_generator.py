# src/engine/ear_training_generator.py
"""
Ear Training Generator Engine
=============================
Generates canonical EarTrainingQuestion payloads for intervals,
chord qualities, and single pitch identification exercises.
"""

import random
from typing import List, Set, Dict, Union

from models.ear_training import (
    EarTrainingCategory,
    EarTrainingDifficulty,
    EarTrainingQuestion,
    IntervalPlayMode,
)
from utils.music_theory import MusicTheory, CHROMATIC_SHARPS


INTERVAL_SEMITONE_MAP: Dict[str, int] = {
    "Unison": 0,
    "Minor 2nd": 1,
    "Major 2nd": 2,
    "Minor 3rd": 3,
    "Major 3rd": 4,
    "Perfect 4th": 5,
    "Tritone": 6,
    "Perfect 5th": 7,
    "Minor 6th": 8,
    "Major 6th": 9,
    "Minor 7th": 10,
    "Major 7th": 11,
    "Octave": 12,
}

CHORD_QUALITY_OFFSETS: Dict[str, List[int]] = {
    "Major": [0, 4, 7],
    "Minor": [0, 3, 7],
    "Diminished": [0, 3, 6],
    "Augmented": [0, 4, 8],
    "Dominant 7th": [0, 4, 7, 10],
    "Major 7th": [0, 4, 7, 11],
    "Minor 7th": [0, 3, 7, 10],
}


class EarTrainingGenerator:
    """Engine generating randomized ear training questions matching the Pydantic schema."""

    @staticmethod
    def generate_question(
        category: Union[EarTrainingCategory, str] = EarTrainingCategory.INTERVAL,
        difficulty: Union[EarTrainingDifficulty, str] = EarTrainingDifficulty.BEGINNER,
    ) -> EarTrainingQuestion:
        cat_enum = (
            category
            if isinstance(category, EarTrainingCategory)
            else EarTrainingGenerator._parse_category_string(str(category))
        )
        diff_enum = (
            difficulty
            if isinstance(difficulty, EarTrainingDifficulty)
            else EarTrainingGenerator._parse_difficulty_string(str(difficulty))
        )

        if cat_enum == EarTrainingCategory.CHORD_QUALITY:
            return EarTrainingGenerator._gen_chord_quality(cat_enum, diff_enum)
        elif cat_enum == EarTrainingCategory.SINGLE_NOTE:
            return EarTrainingGenerator._gen_single_pitch(cat_enum, diff_enum)
        else:
            return EarTrainingGenerator._gen_interval(cat_enum, diff_enum)

    @staticmethod
    def _parse_category_string(cat_str: str) -> EarTrainingCategory:
        clean = cat_str.lower()
        if "chord" in clean:
            return EarTrainingCategory.CHORD_QUALITY
        elif "note" in clean or "pitch" in clean:
            return EarTrainingCategory.SINGLE_NOTE
        return EarTrainingCategory.INTERVAL

    @staticmethod
    def _parse_difficulty_string(diff_str: str) -> EarTrainingDifficulty:
        clean = diff_str.lower()
        if "inter" in clean:
            return EarTrainingDifficulty.INTERMEDIATE
        elif "adv" in clean:
            return EarTrainingDifficulty.ADVANCED
        return EarTrainingDifficulty.BEGINNER

    @staticmethod
    def _gen_interval(
        category: EarTrainingCategory, difficulty: EarTrainingDifficulty
    ) -> EarTrainingQuestion:
        if difficulty == EarTrainingDifficulty.BEGINNER:
            available_intervals = ["Unison", "Major 3rd", "Perfect 5th", "Octave"]
        elif difficulty == EarTrainingDifficulty.INTERMEDIATE:
            available_intervals = [
                "Major 2nd",
                "Minor 3rd",
                "Major 3rd",
                "Perfect 4th",
                "Perfect 5th",
                "Major 6th",
                "Octave",
            ]
        else:
            available_intervals = list(INTERVAL_SEMITONE_MAP.keys())

        correct_interval = random.choice(available_intervals)
        semitones = INTERVAL_SEMITONE_MAP.get(correct_interval, 0)

        root_note = random.choice(CHROMATIC_SHARPS)
        root_pc = MusicTheory.note_to_pitch_class(root_note)
        base_octave = 4

        target_pc = (root_pc + semitones) % 12
        second_octave = base_octave + ((root_pc + semitones) // 12)

        options = list(available_intervals)
        random.shuffle(options)

        return EarTrainingQuestion(
            category=category,
            difficulty=difficulty,
            prompt_text=f"Identify the interval played above root note {root_note}.",
            correct_answer=correct_interval,
            options=options,
            pitch_classes={root_pc, target_pc},
            root_note=root_note,
            octave=base_octave,
            second_note_octave=second_octave,
            second_pitch_class=target_pc,
            interval_mode=IntervalPlayMode.HARMONIC,
            explanation=f"{correct_interval} consists of {semitones} semitone(s).",
        )

    @staticmethod
    def _gen_chord_quality(
        category: EarTrainingCategory, difficulty: EarTrainingDifficulty
    ) -> EarTrainingQuestion:
        if difficulty == EarTrainingDifficulty.BEGINNER:
            available_qualities = ["Major", "Minor"]
        elif difficulty == EarTrainingDifficulty.INTERMEDIATE:
            available_qualities = ["Major", "Minor", "Dominant 7th", "Major 7th"]
        else:
            available_qualities = list(CHORD_QUALITY_OFFSETS.keys())

        correct_quality = random.choice(available_qualities)
        root_note = random.choice(CHROMATIC_SHARPS)
        root_pc = MusicTheory.note_to_pitch_class(root_note)

        offsets = CHORD_QUALITY_OFFSETS.get(correct_quality, [0, 4, 7])
        pitch_classes: Set[int] = {(root_pc + offset) % 12 for offset in offsets}

        options = list(available_qualities)
        random.shuffle(options)

        return EarTrainingQuestion(
            category=category,
            difficulty=difficulty,
            prompt_text=f"Identify the chord quality built on {root_note}.",
            correct_answer=correct_quality,
            options=options,
            pitch_classes=pitch_classes,
            root_note=root_note,
            octave=4,
            explanation=f"A {correct_quality} chord contains pitch classes: {sorted(list(pitch_classes))}.",
        )

    @staticmethod
    def _gen_single_pitch(
        category: EarTrainingCategory, difficulty: EarTrainingDifficulty
    ) -> EarTrainingQuestion:
        target_note = random.choice(CHROMATIC_SHARPS)
        target_pc = MusicTheory.note_to_pitch_class(target_note)

        if difficulty == EarTrainingDifficulty.BEGINNER:
            options = ["C", "E", "G", "A"]
            if target_note not in options:
                options[0] = target_note
        else:
            options = list(CHROMATIC_SHARPS)

        random.shuffle(options)

        return EarTrainingQuestion(
            category=category,
            difficulty=difficulty,
            prompt_text="Listen closely and identify the single pitch played.",
            correct_answer=target_note,
            options=options,
            pitch_classes={target_pc},
            root_note=target_note,
            octave=4,
            explanation=f"The played note is {target_note} (Pitch Class {target_pc}).",
        )
