"""
tests/test_fretboard_mapper.py
==============================
Unit tests for physical coordinate mapping and multi-instrument profiles.
"""

import pytest
from instruments.guitar import GuitarProfile
from instruments.bass import BassProfile
from instruments.ukulele import UkuleleProfile
from hints.fretboard_mapper import FretboardMapper


def test_guitar_note_coordinates():
    """Verifies physical (string, fret) resolution for C4 on standard 6-string guitar."""
    guitar = GuitarProfile("Guitar (6-String Standard)")

    # C4 = MIDI note 60
    coords = FretboardMapper.map_note_locations(guitar, "C", 4)

    # C4 should be found on String 2 Fret 1 (B string) and String 3 Fret 5 (G string)
    string_fret_pairs = [(c["string_num"], c["fret_num"]) for c in coords]
    assert (2, 1) in string_fret_pairs
    assert (3, 5) in string_fret_pairs


def test_bass_open_string_midi():
    """Verifies standard 4-string bass open tuning pitch conversions."""
    bass = BassProfile("Bass (4-String Standard)")

    # String 4 (Low E1) = MIDI 28
    e1_midi = bass.get_open_string_midi(4)
    assert e1_midi == 28

    # String 1 (G2) = MIDI 43
    g2_midi = bass.get_open_string_midi(1)
    assert g2_midi == 43


def test_ukulele_reentrant_tuning():
    """Verifies reentrant tuning coordinate mapping for standard soprano ukulele."""
    uke = UkuleleProfile("Ukulele (Regular 4-String)")

    # High G4 is on open String 4
    coords = FretboardMapper.map_note_locations(uke, "G", 4)
    string_fret_pairs = [(c["string_num"], c["fret_num"]) for c in coords]
    assert (4, 0) in string_fret_pairs
