# src/engine/ear_training_generator.py
import random
from typing import List, Set
from models.ear_training import (
    EarTrainingCategory,
    EarTrainingDifficulty,
    EarTrainingQuestion,
    IntervalPlayMode,
)
from utils.music_theory import MusicTheory, INTERVAL_SEMITONES, CHORD_FORMULAS, NOTES
from models.chord import ChordQuality


class EarTrainingGenerator:
    """Generates dynamic ear training quiz questions with options and theory hints."""

    @staticmethod
    def generate_question(
        category: EarTrainingCategory,
        difficulty: EarTrainingDifficulty
    ) -> EarTrainingQuestion:
        if category == EarTrainingCategory.SINGLE_NOTE:
            return EarTrainingGenerator._gen_single_note(difficulty)
        elif category == EarTrainingCategory.INTERVAL:
            return EarTrainingGenerator._gen_interval(difficulty)
        elif category == EarTrainingCategory.CHORD_INVERSION:
            return EarTrainingGenerator._gen_chord_inversion(difficulty)
        else:
            return EarTrainingGenerator._gen_chord_quality(difficulty)

    @staticmethod
    def _gen_single_note(difficulty: EarTrainingDifficulty) -> EarTrainingQuestion:
        if difficulty == EarTrainingDifficulty.BEGINNER:
            note_pool = ["C", "D", "E", "F", "G", "A", "B"]
            octave = 4
        elif difficulty == EarTrainingDifficulty.INTERMEDIATE:
            note_pool = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            octave = random.choice([3, 4])
        else:
            note_pool = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            octave = random.choice([2, 3, 4, 5])

        target_note = random.choice(note_pool)
        pc = MusicTheory.note_to_pitch_class(target_note)

        # Distractor selection
        choices = {target_note}
        while len(choices) < 4:
            choices.add(random.choice(note_pool))

        ordered_choices = sorted(list(choices))

        return EarTrainingQuestion(
            category=EarTrainingCategory.SINGLE_NOTE,
            difficulty=difficulty,
            prompt_text=f"Listen to the note played in Octave {octave} and identify its note name.",
            correct_answer=target_note,
            options=ordered_choices,
            pitch_classes={pc},
            root_note=target_note,
            octave=octave,
            explanation=f"The played pitch was {target_note} ({pc} semitones above C)."
        )

    @staticmethod
    def _gen_interval(difficulty: EarTrainingDifficulty) -> EarTrainingQuestion:
        if difficulty == EarTrainingDifficulty.BEGINNER:
            interval_pool = ["P1", "M3", "P5", "P8"]
            play_mode = IntervalPlayMode.HARMONIC
        elif difficulty == EarTrainingDifficulty.INTERMEDIATE:
            interval_pool = ["m2", "M2", "m3", "M3", "P4", "d5", "P5", "M6", "m7", "M7", "P8"]
            play_mode = random.choice([IntervalPlayMode.HARMONIC, IntervalPlayMode.MELODIC_ASCENDING])
        else:
            interval_pool = list(INTERVAL_SEMITONES.keys())
            play_mode = random.choice([
                IntervalPlayMode.HARMONIC,
                IntervalPlayMode.MELODIC_ASCENDING,
                IntervalPlayMode.MELODIC_DESCENDING
            ])

        interval_code = random.choice(interval_pool)
        semitones = INTERVAL_SEMITONES[interval_code]

        root_pc = random.randint(0, 11)
        root_note = MusicTheory.pitch_class_to_note(root_pc)

        second_pc = (root_pc + semitones) % 12
        second_octave = 4 + ((root_pc + semitones) // 12)

        # Name formatting lookup
        interval_names = {
            "P1": "Unison (P1)", "m2": "Minor 2nd (m2)", "M2": "Major 2nd (M2)",
            "m3": "Minor 3rd (m3)", "M3": "Major 3rd (M3)", "P4": "Perfect 4th (P4)",
            "d5": "Tritone / Dim 5th (d5)", "P5": "Perfect 5th (P5)", "A5": "Augmented 5th (A5)",
            "m6": "Minor 6th (m6)", "M6": "Major 6th (M6)", "m7": "Minor 7th (m7)",
            "M7": "Major 7th (M7)", "P8": "Octave (P8)"
        }

        correct_title = interval_names.get(interval_code, interval_code)

        choices = {correct_title}
        all_titles = [interval_names.get(k, k) for k in interval_pool]
        while len(choices) < 4 and len(choices) < len(all_titles):
            choices.add(random.choice(all_titles))

        return EarTrainingQuestion(
            category=EarTrainingCategory.INTERVAL,
            difficulty=difficulty,
            prompt_text=f"Listen to the two notes ({play_mode.value}) and identify the interval.",
            correct_answer=correct_title,
            options=sorted(list(choices)),
            pitch_classes={root_pc, second_pc},
            root_note=root_note,
            octave=4,
            second_pitch_class=second_pc,
            second_note_octave=second_octave,
            interval_mode=play_mode,
            explanation=f"{correct_title} spans {semitones} semitone(s) (Root: {root_note})."
        )

    @staticmethod
    def _gen_chord_quality(difficulty: EarTrainingDifficulty) -> EarTrainingQuestion:
        if difficulty == EarTrainingDifficulty.BEGINNER:
            qualities = [ChordQuality.MAJOR, ChordQuality.MINOR]
        elif difficulty == EarTrainingDifficulty.INTERMEDIATE:
            qualities = [ChordQuality.MAJOR, ChordQuality.MINOR, ChordQuality.DOMINANT_7TH, ChordQuality.MAJOR_7TH]
        else:
            qualities = [
                ChordQuality.MAJOR, ChordQuality.MINOR, ChordQuality.DIMINISHED,
                ChordQuality.AUGMENTED, ChordQuality.DOMINANT_7TH, ChordQuality.MAJOR_7TH,
                ChordQuality.MINOR_7TH, ChordQuality.SUS2, ChordQuality.SUS4
            ]

        target_q = random.choice(qualities)
        root_note = random.choice(["C", "G", "D", "A", "E", "F"])
        pcs = MusicTheory.get_chord_pitch_classes(root_note, target_q)

        correct_name = f"{root_note} {target_q.value}"

        choices = {correct_name}
        for q in qualities:
            choices.add(f"{root_note} {q.value}")
            if len(choices) >= 4:
                break

        return EarTrainingQuestion(
            category=EarTrainingCategory.CHORD_QUALITY,
            difficulty=difficulty,
            prompt_text="Listen to the chord and select the correct chord title.",
            correct_answer=correct_name,
            options=sorted(list(choices)),
            pitch_classes=pcs,
            root_note=root_note,
            octave=4,
            explanation=f"{correct_name} contains pitch classes: {[MusicTheory.pitch_class_to_note(p) for p in sorted(list(pcs))]}."
        )

    @staticmethod
    def _gen_chord_inversion(difficulty: EarTrainingDifficulty) -> EarTrainingQuestion:
        root_note = random.choice(["C", "G", "D", "A", "E", "F"])
        inversions = ["Root Position", "1st Inversion", "2nd Inversion"]
        target_inv = random.choice(inversions)

        pcs = MusicTheory.get_chord_pitch_classes(root_note, ChordQuality.MAJOR)
        correct_title = f"{root_note} Major ({target_inv})"

        return EarTrainingQuestion(
            category=EarTrainingCategory.CHORD_INVERSION,
            difficulty=difficulty,
            prompt_text="Identify the inversion position of the played triad.",
            correct_answer=correct_title,
            options=[f"{root_note} Major ({inv})" for inv in inversions],
            pitch_classes=pcs,
            root_note=root_note,
            octave=4,
            explanation=f"The chord was played in {target_inv}."
        )
    
