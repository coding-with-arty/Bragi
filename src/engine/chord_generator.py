"""
src/engine/chord_generator.py
==============================
Target chord definition factory and exercise target generator.
Filters chord pools by quality, key, fret range, and CAGED positions.
"""

import random
from typing import List, Optional
from models.chord import ChordDefinition, TargetChord, ChordQuality, CAGEDPosition
from models.settings import ChordFilterSettings
from utils.music_theory import MusicTheory, CHORD_INTERVAL_NAMES
from engine.caged_system import CAGEDSystem


class ChordGenerator:
    """Factory engine for constructing and selecting exercise target chords."""

    @staticmethod
    def create_definition(root_note: str, quality: ChordQuality) -> ChordDefinition:
        """
        Constructs a pure ChordDefinition for a root note and chord quality.

        :param root_note: Root note string (e.g. "C", "F#")
        :param quality: ChordQuality enum
        :return: Fully populated ChordDefinition instance
        """
        pitch_classes = MusicTheory.get_chord_pitch_classes(root_note, quality)
        intervals = CHORD_INTERVAL_NAMES.get(quality, ["1", "3", "5"])
        full_name = f"{root_note} {quality.value}"

        return ChordDefinition(
            name=full_name,
            root_note=root_note,
            quality=quality,
            pitch_classes=pitch_classes,
            formula_intervals=intervals
        )

    @staticmethod
    def generate_target(filters: Optional[ChordFilterSettings] = None) -> TargetChord:
        """
        Generates a single random TargetChord target matching filter criteria.

        :param filters: Active ChordFilterSettings or None for defaults
        :return: TargetChord instance ready for display and audio validation
        """
        active_filters = filters or ChordFilterSettings()

        # Resolve available keys and qualities
        available_keys = list(active_filters.selected_keys) if active_filters.selected_keys else ["C", "G", "D", "A", "E"]
        available_qualities = list(active_filters.qualities) if active_filters.qualities else [ChordQuality.MAJOR, ChordQuality.MINOR]

        root_note = random.choice(available_keys)
        quality = random.choice(available_qualities)

        chord_def = ChordGenerator.create_definition(root_note, quality)

        # Resolve CAGED shape position target if restricted
        caged_target = CAGEDPosition.NONE
        voicing = None

        if active_filters.caged_positions and active_filters.caged_positions != {CAGEDPosition.NONE}:
            caged_target = random.choice(list(active_filters.caged_positions))
            if caged_target != CAGEDPosition.NONE:
                voicing = CAGEDSystem.build_caged_voicing(root_note, quality, caged_target)

        return TargetChord(
            chord_definition=chord_def,
            required_voicing=voicing,
            required_caged_position=caged_target,
            require_root_bass=False
        )

    @staticmethod
    def get_all_triads(root_note: str) -> List[ChordDefinition]:
        """Returns all basic triad definitions (Major, Minor, Diminished, Augmented) for root_note."""
        triad_qualities = [ChordQuality.MAJOR, ChordQuality.MINOR, ChordQuality.DIMINISHED, ChordQuality.AUGMENTED]
        return [ChordGenerator.create_definition(root_note, q) for q in triad_qualities]
