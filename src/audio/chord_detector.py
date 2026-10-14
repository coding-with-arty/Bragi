"""
src/audio/chord_detector.py
===========================
Polyphonic DSP detector processing raw audio blocks into pitch class vectors.
"""

import numpy as np
from typing import Set, Tuple
from audio.dsp_utils import calculate_rms_dbfs, compute_pitch_class_chroma


class ChordDetector:
    """Polyphonic DSP chord detector analyzing spectral frame energy."""

    def __init__(
        self,
        sample_rate: int = 44100,
        silence_threshold_db: float = -45.0,
        chroma_threshold: float = 0.25
    ) -> None:
        self.sample_rate = sample_rate
        self.silence_threshold_db = silence_threshold_db
        self.chroma_threshold = chroma_threshold

    def process_frame(self, signal: np.ndarray) -> Tuple[Set[int], float, bool, np.ndarray]:
        """
        Processes a 1D PCM audio buffer array.

        :param signal: NumPy array of float32 PCM samples
        :return: Tuple of (active_pitch_classes_set, volume_db, is_silent, chroma_vector)
        """
        volume_db = calculate_rms_dbfs(signal)
        is_silent = volume_db < self.silence_threshold_db

        if is_silent or signal.size == 0:
            return set(), volume_db, True, np.zeros(12, dtype=np.float32)

        active_pcs, chroma_vector = compute_pitch_class_chroma(
            signal=signal,
            sample_rate=self.sample_rate,
            threshold_ratio=self.chroma_threshold
        )

        return active_pcs, volume_db, False, chroma_vector
