"""
src/engine/caged_system.py
==========================
CAGED system fretboard shape definitions, root string references,
and physical voicing coordinate generators.
"""

from typing import Dict, List, Tuple, Optional
from models.chord import CAGEDPosition, ChordQuality, ChordVoicing, FingeringCoordinate
from utils.music_theory import MusicTheory


# Base open voicings relative to nut (fret offset 0)
# Array format per shape: [String 6 (Low E), String 5, String 4, String 3, String 2, String 1 (High E)]
# Value: fret integer (-1 for muted, 0 for open)
CAGED_OPEN_TEMPLATES: Dict[CAGEDPosition, Dict[ChordQuality, Tuple[List[int], List[Optional[int]], int]]] = {
    CAGEDPosition.C_SHAPE: {
        ChordQuality.MAJOR: (
            [-1, 3, 2, 0, 1, 0],          # Frets relative to root
            [None, 3, 2, None, 1, None],   # Fingerings
            5                             # Root bass string index (String 5 = A string)
        )
    },
    CAGEDPosition.A_SHAPE: {
        ChordQuality.MAJOR: (
            [-1, 0, 2, 2, 2, 0],
            [None, None, 2, 3, 4, None],
            5
        ),
        ChordQuality.MINOR: (
            [-1, 0, 2, 2, 1, 0],
            [None, None, 2, 3, 1, None],
            5
        )
    },
    CAGEDPosition.G_SHAPE: {
        ChordQuality.MAJOR: (
            [3, 2, 0, 0, 0, 3],
            [3, 2, None, None, None, 4],
            6
        )
    },
    CAGEDPosition.E_SHAPE: {
        ChordQuality.MAJOR: (
            [0, 2, 2, 1, 0, 0],
            [None, 2, 3, 1, None, None],
            6
        ),
        ChordQuality.MINOR: (
            [0, 2, 2, 0, 0, 0],
            [None, 2, 3, None, None, None],
            6
        )
    },
    CAGEDPosition.D_SHAPE: {
        ChordQuality.MAJOR: (
            [-1, -1, 0, 2, 3, 2],
            [None, None, None, 1, 3, 2],
            4
        ),
        ChordQuality.MINOR: (
            [-1, -1, 0, 2, 3, 1],
            [None, None, None, 2, 3, 1],
            4
        )
    }
}


class CAGEDSystem:
    """CAGED system position lookup and voicing calculator."""

    @staticmethod
    def get_root_fret_for_shape(root_note: str, shape: CAGEDPosition) -> int:
        """
        Calculates the fret location of the root note for a given CAGED shape shape.

        :param root_note: Target root note name (e.g. "C", "G")
        :param shape: Target CAGED position enum
        :return: Fret index (0..12) where the shape is rooted
        """
        root_pc = MusicTheory.note_to_pitch_class(root_note)

        # Base open root pitch classes for standard tuning reference
        # String 6 = E (4), String 5 = A (9), String 4 = D (2)
        if shape in (CAGEDPosition.E_SHAPE, CAGEDPosition.G_SHAPE):
            base_pc = 4  # Low E string root
        elif shape in (CAGEDPosition.A_SHAPE, CAGEDPosition.C_SHAPE):
            base_pc = 9  # A string root
        elif shape == CAGEDPosition.D_SHAPE:
            base_pc = 2  # D string root
        else:
            base_pc = 0

        fret = (root_pc - base_pc) % 12
        return fret

    @staticmethod
    def build_caged_voicing(root_note: str, quality: ChordQuality, shape: CAGEDPosition) -> Optional[ChordVoicing]:
        """
        Generates a concrete ChordVoicing model for a root, quality, and CAGED shape.

        :return: ChordVoicing model or None if shape/quality combination is not templated
        """
        shape_dict = CAGED_OPEN_TEMPLATES.get(shape)
        if not shape_dict or quality not in shape_dict:
            return None

        frets_template, fingers_template, bass_string = shape_dict[quality]
        root_fret = CAGEDSystem.get_root_fret_for_shape(root_note, shape)

        fingerings: List[FingeringCoordinate] = []
        active_frets: List[int] = []

        for idx, rel_fret in enumerate(frets_template):
            string_num = idx + 1  # 1-indexed (1=High E, 6=Low E)
            finger_num = fingers_template[idx]

            if rel_fret == -1:
                fingerings.append(FingeringCoordinate(string_num=string_num, fret=0, is_muted=True))
            else:
                abs_fret = rel_fret if shape == CAGEDPosition.OPEN else rel_fret + root_fret
                is_open = (abs_fret == 0)
                fingerings.append(FingeringCoordinate(
                    string_num=string_num,
                    fret=abs_fret,
                    finger=finger_num,
                    is_muted=False,
                    is_open=is_open
                ))
                if not is_open:
                    active_frets.append(abs_fret)

        min_fret = min(active_frets) if active_frets else 0
        max_fret = max(active_frets) if active_frets else 3

        voicing_id = f"{root_note}_{quality.value}_{shape.value}".replace(" ", "_")

        return ChordVoicing(
            voicing_id=voicing_id,
            caged_position=shape,
            fret_range=(min_fret, max_fret),
            fingerings=fingerings,
            bass_string=bass_string
        )
