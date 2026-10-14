"""
src/audio/dsp_utils.py
======================
DSP utilities for frame windowing, RMS volume calculation, pitch-to-chroma conversion,
and harmonic attenuation filtering.
"""

import math
import numpy as np
from typing import Tuple, Set

# Standard A4 reference frequency
A440_HZ = 440.0
NOTE_NAMES_12 = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def calculate_rms_dbfs(signal: np.ndarray) -> float:
    """Calculates Root Mean Square (RMS) energy converted to dBFS."""
    if signal.size == 0:
        return -120.0
    rms = np.sqrt(np.mean(np.square(signal)))
    if rms <= 1e-12:
        return -120.0
    return float(20.0 * np.log10(rms))


def frequency_to_pitch_class(freq_hz: float) -> Tuple[int, str, int, float]:
    """
    Converts frequency in Hz to (pitch_class, note_name, octave, cents_error).

    :return: Tuple of (pitch_class 0..11, note_name, octave, cents)
    """
    if freq_hz <= 0.0:
        return 0, "N/A", 0, 0.0

    midi_exact = 69.0 + 12.0 * math.log2(freq_hz / A440_HZ)
    midi_rounded = round(midi_exact)
    cents = (midi_exact - midi_rounded) * 100.0

    pitch_class = midi_rounded % 12
    note_name = NOTE_NAMES_12[pitch_class]
    octave = (midi_rounded // 12) - 1

    return pitch_class, note_name, octave, cents


def compute_pitch_class_chroma(
    signal: np.ndarray,
    sample_rate: int = 44100,
    min_freq_hz: float = 65.4,   # C2 (~65.4 Hz, covers guitar low E2 = 82.4Hz)
    max_freq_hz: float = 1046.5, # C6 (~1046.5 Hz)
    threshold_ratio: float = 0.25
) -> Tuple[Set[int], np.ndarray]:
    """
    Computes a 12-bin normalized Pitch Class Profile (Chromagram) vector from audio signal frames.
    Applies harmonic attenuation filtering to suppress upper overtone peaks (3rd and 5th harmonics).

    :param signal: 1D NumPy array of float32 PCM samples
    :param sample_rate: Audio sampling frequency in Hz
    :param min_freq_hz: Lower bound frequency cutoff
    :param max_freq_hz: Upper bound frequency cutoff
    :param threshold_ratio: Relative magnitude ratio required for a pitch bin to be considered active
    :return: Tuple of (Set of active pitch class integers 0..11, 12-element normalized chroma vector)
    """
    chroma_vector = np.zeros(12, dtype=np.float32)
    if signal.size == 0:
        return set(), chroma_vector

    # Apply Hann window to minimize spectral leakage
    windowed = signal * np.hanning(signal.size)
    fft_magnitudes = np.abs(np.fft.rfft(windowed))
    fft_freqs = np.fft.rfftfreq(signal.size, d=1.0 / sample_rate)

    # Accumulate spectral magnitude into 12 pitch class bins
    for freq, mag in zip(fft_freqs, fft_magnitudes):
        if min_freq_hz <= freq <= max_freq_hz:
            pc, _, _, _ = frequency_to_pitch_class(freq)
            chroma_vector[pc] += mag

    # Normalize vector to unit peak
    max_val = np.max(chroma_vector)
    if max_val > 1e-6:
        chroma_vector /= max_val
    else:
        return set(), chroma_vector

    # Apply harmonic attenuation filtering:
    # A strong fundamental at PC x creates an artificial overtone peak at (PC + 7) % 12 (3rd harmonic)
    # Filter out secondary peaks if their fundamental is dominant
    filtered_chroma = chroma_vector.copy()
    for pc in range(12):
        fifth_overtone_pc = (pc + 7) % 12
        if chroma_vector[pc] > 0.6:
            filtered_chroma[fifth_overtone_pc] = max(0.0, filtered_chroma[fifth_overtone_pc] - 0.35 * chroma_vector[pc])

    active_pitch_classes = {pc for pc in range(12) if filtered_chroma[pc] >= threshold_ratio}
    return active_pitch_classes, filtered_chroma
