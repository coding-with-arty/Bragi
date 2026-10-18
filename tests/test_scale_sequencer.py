# tests/test_scale_sequencer.py
"""Unit tests for ScaleSequencer pattern generation and step navigation."""

from engine.scale_sequencer import ScaleSequencer, SequenceDirection


def test_scale_sequencer_ascending():
    notes = ["C", "D", "E", "F", "G", "A", "B"]
    sequencer = ScaleSequencer(scale_notes=notes, direction=SequenceDirection.ASCENDING)

    assert sequencer.get_current_note() == "C"
    assert sequencer.advance() == "D"
    assert sequencer.advance() == "E"


def test_scale_sequencer_descending():
    notes = ["C", "D", "E", "F", "G", "A", "B"]
    sequencer = ScaleSequencer(scale_notes=notes, direction=SequenceDirection.DESCENDING)

    assert sequencer.get_current_note() == "B"
    assert sequencer.advance() == "A"
