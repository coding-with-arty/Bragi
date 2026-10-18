# src/engine/scale_engine.py
from enum import Enum
from typing import List, Tuple, Dict, Set, Optional
from models.instrument import InstrumentProfile
from instruments.base_instrument import BaseInstrument
from instruments.universal_instrument import UniversalInstrumentProfile
from utils.music_theory import MusicTheory, NOTE_TO_PITCH_INDEX, CHROMATIC_SHARPS
from utils.music_theory import MusicTheory, NOTE_TO_PITCH_INDEX, CHROMATIC_FLATS


class ScaleType(str, Enum):
    MAJOR = "Major"
    NATURAL_MINOR = "Natural Minor"
    MAJOR_PENTATONIC = "Major Pentatonic"
    MINOR_PENTATONIC = "Minor Pentatonic"


SCALE_FORMULAS: Dict[ScaleType, List[int]] = {
    ScaleType.MAJOR: [0, 2, 4, 5, 7, 9, 11],
    ScaleType.NATURAL_MINOR: [0, 2, 3, 5, 7, 8, 10],
    ScaleType.MAJOR_PENTATONIC: [0, 2, 4, 7, 9],
    ScaleType.MINOR_PENTATONIC: [0, 3, 5, 7, 10],
}


class ScaleDefinition:
    """Represents a specific key and scale combination."""

    def __init__(self, root_note: str, scale_type: ScaleType):
        clean_root = root_note.strip().upper()
        if clean_root not in NOTE_TO_PITCH_INDEX:
            raise ValueError(f"Invalid root note: '{root_note}'")

        self.root_note = clean_root
        self.scale_type = scale_type
        self.root_pitch_class = NOTE_TO_PITCH_INDEX[clean_root]

        offsets = SCALE_FORMULAS.get(scale_type, [0, 2, 4, 5, 7, 9, 11])
        self.pitch_classes: Set[int] = {(self.root_pitch_class + offset) % 12 for offset in offsets}
        self.ordered_pitch_classes: List[int] = [(self.root_pitch_class + offset) % 12 for offset in offsets]

    def get_note_names(self, use_flats: bool = False) -> List[str]:
        """Returns the list of note names for the scale degrees."""
        return [MusicTheory.pitch_class_to_note(pc, use_flats=use_flats) for pc in self.ordered_pitch_classes]


class ScaleEngine:
    """Calculates fretboard layout overlays and note mappings for scales."""

    @staticmethod
    def calculate_scale_positions(
        profile: InstrumentProfile,
        scale_def: ScaleDefinition,
        max_frets: int = 15
    ) -> List[Tuple[int, int, str, bool]]:
        """
        Calculates all matching fret coordinates on the neck for a scale.
        Returns a list of tuples: (string_num, fret_num, note_name, is_root)
        """
        univ = UniversalInstrumentProfile(profile)
        locations = []
        tuning = profile.to_tuning_tuples()

        for s_idx in range(len(tuning)):
            string_num = s_idx + 1
            open_midi = univ.get_open_string_midi(string_num)

            for fret in range(0, min(max_frets, profile.fret_count) + 1):
                target_midi = open_midi + fret
                note_name, _ = BaseInstrument.midi_to_note(target_midi)
                pc = NOTE_TO_PITCH_INDEX.get(note_name.upper(), 0)

                if pc in scale_def.pitch_classes:
                    is_root = (pc == scale_def.root_pitch_class)
                    locations.append((string_num, fret, note_name, is_root))

        return locations


class ScaleSequencer:
    """Tracks step-by-step user progress through a scale sequence exercise."""

    def __init__(self, scale_def: ScaleDefinition, ascending: bool = True):
        self.scale_def = scale_def
        self.ascending = ascending
        self.sequence_pcs = list(scale_def.ordered_pitch_classes)
        if not ascending:
            self.sequence_pcs.reverse()

        self.current_step_index = 0
        self.is_completed = False

    @property
    def current_target_pitch_class(self) -> int:
        if self.is_completed:
            return -1
        return self.sequence_pcs[self.current_step_index]

    @property
    def current_target_note_name(self) -> str:
        if self.is_completed:
            return "COMPLETE"
        return MusicTheory.pitch_class_to_note(self.current_target_pitch_class)

    def evaluate_note(self, detected_pitch_class: int) -> bool:
        """Evaluates detected pitch against active step. Advances step index if matched."""
        if self.is_completed or detected_pitch_class < 0:
            return False

        if detected_pitch_class % 12 == self.current_target_pitch_class:
            self.current_step_index += 1
            if self.current_step_index >= len(self.sequence_pcs):
                self.is_completed = True
            return True

        return False

    def reset(self) -> None:
        self.current_step_index = 0
        self.is_completed = False
