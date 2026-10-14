"""
tests/test_dsp.py
=================
Unit tests for DSP utilities, pitch class conversion, and ArpeggioBuffer sliding windows.
"""

import numpy as np
import time
from audio.dsp_utils import calculate_rms_dbfs, frequency_to_pitch_class
from engine.arpeggio_buffer import ArpeggioBuffer


def test_rms_dbfs_silence_and_sine():
    """Verifies dBFS volume calculations for zero signal and full-scale sine wave."""
    silent_signal = np.zeros(1024, dtype=np.float32)
    db_silent = calculate_rms_dbfs(silent_signal)
    assert db_silent == -120.0

    # Sine wave with peak amplitude 1.0 (RMS = 1 / sqrt(2) ≈ 0.707 -> -3.01 dBFS)
    t = np.linspace(0, 1, 44100, endpoint=False)
    sine_signal = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    db_sine = calculate_rms_dbfs(sine_signal)
    assert -3.2 < db_sine < -2.8


def test_frequency_to_pitch_class_a440():
    """Verifies A440 Hz converts to Pitch Class 9 (Note A, Octave 4, 0 cents error)."""
    pc, note_name, octave, cents = frequency_to_pitch_class(440.0)
    assert pc == 9
    assert note_name == "A"
    assert octave == 4
    assert abs(cents) < 0.01


def test_arpeggio_buffer_window_expiration():
    """Verifies that pitch class observations outside the time window expire automatically."""
    buffer = ArpeggioBuffer(window_duration_sec=0.1)

    now = time.monotonic()
    buffer.add_pitch_class(0, timestamp=now - 0.2)  # Expired C
    buffer.add_pitch_class(4, timestamp=now)        # Active E

    active_pcs = buffer.get_active_pitch_classes(current_time=now)
    assert 0 not in active_pcs
    assert 4 in active_pcs
