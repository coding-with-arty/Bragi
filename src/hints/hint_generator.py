"""
src/hints/hint_generator.py
===========================
Unified hint generator constructing complete hint payloads for notes and chords.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, ConfigDict
from instruments.base_instrument import BaseInstrument
from models.chord import TargetChord, FingeringCoordinate
from hints.fretboard_mapper import FretboardMapper
from hints.theory_explainer import TheoryExplainer


class NoteHintPayload(BaseModel):
    """Payload container for single-note target hints."""
    model_config = ConfigDict(frozen=True)

    target_note_name: str
    octave: int
    primary_location: Dict[str, int]
    all_locations: List[Dict[str, int]]
    navigation_tip: str


class ChordHintPayload(BaseModel):
    """Payload container for chord target hints."""
    model_config = ConfigDict(frozen=True)

    chord_name: str
    construction_explanation: str
    fingerings: List[FingeringCoordinate]
    step_by_step_instructions: List[str]
    fret_span: str


class HintGenerator:
    """Orchestrates FretboardMapper and TheoryExplainer to produce unified hint payloads."""

    @staticmethod
    def generate_note_hint(
        note_name: str,
        octave: int,
        instrument: BaseInstrument,
        preferred_string: Optional[int] = None
    ) -> NoteHintPayload:
        """Constructs a NoteHintPayload for a target note."""
        all_locs = FretboardMapper.map_note_locations(instrument, note_name, octave)

        primary = all_locs[0] if all_locs else {"string_num": 1, "fret_num": 0, "landmark_fret": 0, "landmark_offset": 0}
        if preferred_string is not None:
            for loc in all_locs:
                if loc["string_num"] == preferred_string:
                    primary = loc
                    break

        nav_tip = TheoryExplainer.explain_note_landmark(
            note_name=note_name,
            octave=octave,
            string_num=primary["string_num"],
            fret_num=primary["fret_num"],
            landmark_fret=primary["landmark_fret"]
        )

        return NoteHintPayload(
            target_note_name=note_name,
            octave=octave,
            primary_location=primary,
            all_locations=all_locs,
            navigation_tip=nav_tip
        )

    @staticmethod
    def generate_chord_hint(
        target_chord: TargetChord,
        instrument: BaseInstrument
    ) -> ChordHintPayload:
        """Constructs a ChordHintPayload for a target chord."""
        fingerings = FretboardMapper.map_chord_voicings(target_chord, instrument)
        construction = TheoryExplainer.explain_chord_construction(target_chord)
        steps = TheoryExplainer.explain_step_by_step_fingering(fingerings)

        frets = [f.fret for f in fingerings if not f.is_muted and not f.is_open]
        fret_span_str = f"Frets {min(frets)} - {max(frets)}" if frets else "Open Position"

        return ChordHintPayload(
            chord_name=target_chord.display_title,
            construction_explanation=construction,
            fingerings=fingerings,
            step_by_step_instructions=steps,
            fret_span=fret_span_str
        )
