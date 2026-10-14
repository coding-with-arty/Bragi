"""
src/hints/fretboard_mapper.py
=============================
Maps single notes and target chords to physical (string_num, fret_num) coordinates
and fretboard landmarks across active instrument profiles.
"""

from typing import List, Tuple, Dict, Optional
from instruments.base_instrument import BaseInstrument
from models.chord import TargetChord, FingeringCoordinate, ChordVoicing
from utils.music_theory import MusicTheory


class FretboardMapper:
    """Calculates physical fretboard locations, landmarks, and position maps."""

    @staticmethod
    def map_note_locations(
        instrument: BaseInstrument,
        note_name: str,
        octave: int,
        custom_tuning: Optional[List[Tuple[str, int]]] = None,
        active_strings: Optional[List[int]] = None
    ) -> List[Dict[str, int]]:
        """
        Finds all physical (string_num, fret_num) locations for a note on the neck.

        :return: List of dicts containing string_num, fret_num, landmark_fret, landmark_offset
        """
        raw_coords = instrument.get_note_coordinates(
            note_name=note_name,
            octave=octave,
            custom_tuning=custom_tuning,
            active_strings=active_strings
        )

        mapped_locations = []
        for string_num, fret_num in raw_coords:
            closest_landmark, offset = instrument.get_closest_landmark(fret_num)
            mapped_locations.append({
                "string_num": string_num,
                "fret_num": fret_num,
                "landmark_fret": closest_landmark,
                "landmark_offset": offset
            })

        return mapped_locations

    @staticmethod
    def map_chord_voicings(
        target_chord: TargetChord,
        instrument: BaseInstrument
    ) -> List[FingeringCoordinate]:
        """
        Extracts active fingering coordinates for a target chord voicing.

        :return: List of FingeringCoordinate objects describing string, fret, finger, and muting
        """
        if target_chord.required_voicing and target_chord.required_voicing.fingerings:
            return target_chord.required_voicing.fingerings

        # Fallback: calculate open position triad locations on higher strings
        root = target_chord.chord_definition.root_note
        quality = target_chord.chord_definition.quality
        pitch_classes = target_chord.chord_definition.pitch_classes

        fingerings = []
        tuning = instrument.default_tuning

        for idx in range(len(tuning)):
            string_num = idx + 1
            open_midi = instrument.get_open_string_midi(string_num)

            # Find lowest fret matching any chord pitch class
            found = False
            for fret in range(0, 5):
                midi_note = open_midi + fret
                pc = midi_note % 12
                if pc in pitch_classes:
                    is_open = (fret == 0)
                    fingerings.append(FingeringCoordinate(
                        string_num=string_num,
                        fret=fret,
                        finger=None,
                        is_muted=False,
                        is_open=is_open
                    ))
                    found = True
                    break

            if not found:
                fingerings.append(FingeringCoordinate(
                    string_num=string_num,
                    fret=0,
                    finger=None,
                    is_muted=True,
                    is_open=False
                ))

        return fingerings
