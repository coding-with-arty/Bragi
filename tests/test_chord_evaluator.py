"""
tests/test_chord_evaluator.py
==============================
Unit tests for ChordEvaluator domain engine and pitch class set matching.
"""

import pytest
import time
from engine.chord_evaluator import ChordEvaluator
from engine.chord_generator import ChordGenerator
from models.chord import ChordQuality
from models.settings import ValidationMode


def test_exact_chord_match():
    """Verifies that playing exact required chord pitch classes produces a valid match."""
    c_major = ChordGenerator.generate_target()
    evaluator = ChordEvaluator(
        hold_duration_sec=0.1,
        validation_mode=ValidationMode.RELAXED_PITCH_CLASS
    )
    evaluator.set_target(c_major)

    required_pcs = c_major.chord_definition.pitch_classes

    # First frame evaluation
    is_valid, statement = evaluator.evaluate_pitch_classes(
        detected_pitch_classes=required_pcs,
        volume_db=-20.0,
        min_volume_db=-45.0
    )
    assert is_valid is True
    assert statement is None  # Not yet held for duration

    # Hold duration sleep
    time.sleep(0.12)

    # Second frame evaluation after hold duration
    is_valid, statement = evaluator.evaluate_pitch_classes(
        detected_pitch_classes=required_pcs,
        volume_db=-20.0,
        min_volume_db=-45.0
    )
    assert is_valid is True
    assert statement is not None
    assert statement.is_correct is True
    assert statement.missing_pitch_classes == set()


def test_missing_pitch_class_rejection():
    """Verifies that missing a chord tone fails validation."""
    evaluator = ChordEvaluator(hold_duration_sec=0.1)
    target = ChordGenerator.generate_target()
    evaluator.set_target(target)

    required_pcs = target.chord_definition.pitch_classes
    incomplete_pcs = set(list(required_pcs)[:-1])  # Omit one tone

    is_valid, statement = evaluator.evaluate_pitch_classes(
        detected_pitch_classes=incomplete_pcs,
        volume_db=-20.0
    )
    assert is_valid is False
    assert statement is None


def test_silence_threshold_rejection():
    """Verifies that audio below min_volume_db resets evaluation state."""
    evaluator = ChordEvaluator(hold_duration_sec=0.1)
    target = ChordGenerator.generate_target()
    evaluator.set_target(target)

    required_pcs = target.chord_definition.pitch_classes

    is_valid, statement = evaluator.evaluate_pitch_classes(
        detected_pitch_classes=required_pcs,
        volume_db=-60.0,  # Below default -45dB
        min_volume_db=-45.0
    )
    assert is_valid is False
    assert statement is None
