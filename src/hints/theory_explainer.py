"""
src/hints/theory_explainer.py
=============================
Generates human-readable theoretical explanations, landmark navigation tips,
harmonic interval breakdowns, and mechanical finger placement instructions.
"""

from typing import List, Dict
from models.chord import TargetChord, ChordQuality, FingeringCoordinate
from utils.music_theory import CHORD_INTERVAL_NAMES, MusicTheory


class TheoryExplainer:
    """Generates natural language explanations for musical concepts and hints."""

    @staticmethod
    def explain_note_landmark(note_name: str, octave: int, string_num: int, fret_num: int, landmark_fret: int) -> str:
        """Generates navigation tip explaining how to locate a note relative to neck landmarks."""
        if fret_num == 0:
            return f"Note {note_name}{octave} is played on Open String {string_num}."

        offset = fret_num - landmark_fret
        if offset == 0:
            return f"Note {note_name}{octave} is located directly at Fret {fret_num} (Marker) on String {string_num}."
        elif offset > 0:
            return f"Note {note_name}{octave} is on String {string_num}, {offset} fret(s) above Fret {landmark_fret} marker."
        else:
            return f"Note {note_name}{octave} is on String {string_num}, {abs(offset)} fret(s) below Fret {landmark_fret} marker."

    @staticmethod
    def explain_chord_construction(target_chord: TargetChord) -> str:
        """Explains harmonic construction and formula intervals for a chord."""
        chord_def = target_chord.chord_definition
        quality = chord_def.quality
        notes = MusicTheory.get_chord_note_names(chord_def.root_note, quality)
        notes_str = ", ".join(notes)
        intervals = chord_def.formula_intervals or CHORD_INTERVAL_NAMES.get(quality, ["1", "3", "5"])
        intervals_str = " - ".join(intervals)

        if quality == ChordQuality.MAJOR:
            explanation = f"{chord_def.name} is a Major triad formed by Root, Major 3rd, and Perfect 5th ({intervals_str}). Tones: {notes_str}."
        elif quality == ChordQuality.MINOR:
            explanation = f"{chord_def.name} is a Minor triad formed by Root, Minor 3rd (b3), and Perfect 5th ({intervals_str}). Tones: {notes_str}."
        elif quality == ChordQuality.DOMINANT_7TH:
            explanation = f"{chord_def.name} is a Dominant 7th chord containing Major triad + Minor 7th ({intervals_str}). Tones: {notes_str}."
        elif quality == ChordQuality.MAJOR_7TH:
            explanation = f"{chord_def.name} is a Major 7th chord containing Major triad + Major 7th ({intervals_str}). Tones: {notes_str}."
        else:
            explanation = f"{chord_def.name} consists of tones [{notes_str}] matching formula ({intervals_str})."

        return explanation

    @staticmethod
    def explain_step_by_step_fingering(fingerings: List[FingeringCoordinate]) -> List[str]:
        """Generates mechanical step-by-step placement instructions for fingers."""
        steps = []
        finger_names = {1: "Index (1)", 2: "Middle (2)", 3: "Ring (3)", 4: "Pinky (4)"}

        # Filter active fretted strings
        fretted = [f for f in fingerings if not f.is_muted and not f.is_open and f.fret > 0]
        fretted.sort(key=lambda x: x.fret)

        for coord in fretted:
            finger_str = finger_names.get(coord.finger, "finger")
            steps.append(f"Place {finger_str} on String {coord.string_num} at Fret {coord.fret}.")

        muted = [f for f in fingerings if f.is_muted]
        if muted:
            muted_strings = ", ".join([str(f.string_num) for f in muted])
            steps.append(f"Mute or leave unplayed: String(s) {muted_strings}.")

        return steps
