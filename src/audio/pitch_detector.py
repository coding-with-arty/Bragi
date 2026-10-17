from dataclasses import dataclass
from typing import Optional
import numpy as np
from utils.music_theory import MusicTheory, A440_HZ


@dataclass(frozen=True)
class PitchDetectionResult:
    """
    Data payload holding evaluated single-note pitch metrics.
    """
    frequency: float = 0.0
    confidence: float = 0.0
    pitch_class: str = "--"
    octave: int = 0
    midi_note: int = 0
    cents_deviation: float = 0.0
    is_in_tune: bool = False


class PitchDetector:
    """
    Analyzes raw PCM audio buffers using signal correlation algorithms
    to detect fundamental frequencies, pitch classes, and tuning deviations.
    """

    def __init__(self, sample_rate: int = 44100, buffer_size: int = 2048):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size

    def process_frame(self, signal: np.ndarray) -> Optional[PitchDetectionResult]:
        """
        Processes a raw audio numpy array frame and returns detected pitch metrics.
        """
        if signal is None or len(signal) == 0:
            return None

        # Calculate signal autocorrelation to isolate the fundamental period
        corr = np.correlate(signal, signal, mode='full')
        corr = corr[len(corr) // 2:]

        # Find the first positive slope shift to avoid zero-lag peak
        d_corr = np.diff(corr)
        start_indices = np.where(d_corr > 0)[0]
        if len(start_indices) == 0:
            return None

        first_dip = start_indices[0]
        peak_index = np.argmax(corr[first_dip:]) + first_dip

        if peak_index == 0:
            return None

        # Convert peak sample offset into fundamental frequency (Hz)
        frequency = float(self.sample_rate / peak_index)

        # Filter out unrealistic pitch frequencies for standard musical instruments
        if frequency < 30.0 or frequency > 4000.0:
            return None

        # Convert frequency to floating-point MIDI note number relative to A440 Hz
        midi_float = 69.0 + 12.0 * np.log2(frequency / A440_HZ)
        midi_note = int(round(midi_float))
        cents_dev = float((midi_float - midi_note) * 100.0)

        # Convert MIDI note to pitch class string and octave
        pitch_class, octave = MusicTheory.midi_to_note_and_octave(midi_note)
        is_in_tune = abs(cents_dev) <= 10.0
        confidence = float(corr[peak_index] / (corr[0] + 1e-9))

        return PitchDetectionResult(
            frequency=frequency,
            confidence=confidence,
            pitch_class=pitch_class,
            octave=octave,
            midi_note=midi_note,
            cents_deviation=cents_dev,
            is_in_tune=is_in_tune,
        )
