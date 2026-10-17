import random
from typing import List, Optional, Set
from models.chord import ChordQuality, ChordDefinition, TargetChord, CAGEDPosition
from utils.music_theory import CHROMATIC_SHARPS, MusicTheory

# Target qualities: Major, Minor, Dom7, Maj7, Sus4
FOCUSED_QUALITIES: List[ChordQuality] = [
    ChordQuality.MAJOR,
    ChordQuality.MINOR,
    ChordQuality.DOMINANT_7TH,
    ChordQuality.MAJOR_7TH,
    ChordQuality.SUS4,
]


class ChordGenerator:
    """Generates target chord prompts restricted strictly to core chord qualities."""

    @staticmethod
    def generate_target(
        allowed_qualities: Optional[Set[ChordQuality]] = None,
        root_note: Optional[str] = None
    ) -> TargetChord:
        qualities = list(allowed_qualities) if allowed_qualities else FOCUSED_QUALITIES
        selected_quality = random.choice(qualities)
        root = root_note or random.choice(CHROMATIC_SHARPS)

        pitch_classes = MusicTheory.get_chord_pitch_classes(root, selected_quality)
        note_names = MusicTheory.get_chord_note_names(root, selected_quality)

        chord_def = ChordDefinition(
            root_note=root,
            quality=selected_quality,
            name=f"{root} {selected_quality.value}",
            pitch_classes=pitch_classes,
            note_names=note_names
        )

        return TargetChord(
            chord_definition=chord_def,
            required_caged_position=CAGEDPosition.NONE
        )
