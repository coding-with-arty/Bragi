# src/audio/chord_detector.py
import collections
import numpy as np
from typing import Set, Tuple
from audio.dsp_utils import calculate_rms_dbfs, frequency_to_pitch_class


class ChordDetector:
    """
    Polyphonic DSP chord detector designed for strummed stringed instruments.
    Uses multi-frame rolling PCM accumulation, harmonic overtone salience filtering,
    and top-peak extraction to isolate chord tones from pick noise and overtones.
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        silence_threshold_db: float = -50.0,
        chroma_threshold: float = 0.22,
        buffer_capacity: int = 8192,
        integration_frames: int = 6,
        max_active_pitch_classes: int = 5,
    ) -> None:
        self.sample_rate = sample_rate
        self.silence_threshold_db = silence_threshold_db
        self.chroma_threshold = chroma_threshold
        self.buffer_capacity = buffer_capacity
        self.max_active_pitch_classes = max_active_pitch_classes

        # Rolling PCM ring buffer
        self._pcm_ring_buffer = np.zeros(self.buffer_capacity, dtype=np.float32)

        # Multi-frame chromagram history for strum integration (~150-200ms sweep)
        self._chroma_history = collections.deque(maxlen=integration_frames)

    def process_frame(self, signal: np.ndarray) -> Tuple[Set[int], float, bool, np.ndarray]:
        """
        Processes incoming PCM audio frames, updates the rolling ring buffer,
        computes normalized harmonic-filtered chromagram, and extracts active pitch classes.
        """
        if signal is None or signal.size == 0:
            return set(), -120.0, True, np.zeros(12, dtype=np.float32)

        volume_db = calculate_rms_dbfs(signal)
        is_silent = volume_db < self.silence_threshold_db

        if is_silent:
            self._chroma_history.clear()
            return set(), volume_db, True, np.zeros(12, dtype=np.float32)

        # Push incoming samples into rolling ring buffer
        num_samples = signal.size
        if num_samples >= self.buffer_capacity:
            self._pcm_ring_buffer = signal[-self.buffer_capacity:].astype(np.float32)
        else:
            self._pcm_ring_buffer = np.roll(self._pcm_ring_buffer, -num_samples)
            self._pcm_ring_buffer[-num_samples:] = signal.astype(np.float32)

        # Compute 12-bin pitch class chromagram over full guitar spectrum (C2 ~65Hz to C6 ~1046Hz)
        frame_chroma = self._compute_chromagram(self._pcm_ring_buffer)
        self._chroma_history.append(frame_chroma)

        # Integrate max peak energy across the strum sweep window
        integrated_chroma = np.max(np.array(self._chroma_history), axis=0)

        # Normalize integrated chroma vector globally
        max_val = np.max(integrated_chroma)
        if max_val > 1e-5:
            integrated_chroma /= max_val
        else:
            return set(), volume_db, True, integrated_chroma

        # Extract candidates meeting the relative energy threshold
        candidate_pcs = [
            (pc, integrated_chroma[pc])
            for pc in range(12)
            if integrated_chroma[pc] >= self.chroma_threshold
        ]

        # Sort candidate pitch classes by magnitude and limit to top dominant peaks
        candidate_pcs.sort(key=lambda item: item[1], reverse=True)
        active_pitch_classes = {pc for pc, _ in candidate_pcs[:self.max_active_pitch_classes]}

        return active_pitch_classes, volume_db, False, integrated_chroma

    def _compute_chromagram(self, pcm_data: np.ndarray) -> np.ndarray:
        """Computes 12-bin pitch class profile with overtone salience suppression."""
        chroma = np.zeros(12, dtype=np.float32)
        if pcm_data.size < 1024:
            return chroma

        # Hann windowing to reduce spectral leakage
        windowed = pcm_data * np.hanning(pcm_data.size)
        fft_mags = np.abs(np.fft.rfft(windowed))
        fft_freqs = np.fft.rfftfreq(pcm_data.size, d=1.0 / self.sample_rate)

        # Bin spectral magnitude into 12 pitch classes
        for freq, mag in zip(fft_freqs, fft_mags):
            if 65.0 <= freq <= 1100.0:
                pc, _, _, _ = frequency_to_pitch_class(freq)
                chroma[pc] += mag

        # Normalize single-frame chroma
        max_val = np.max(chroma)
        if max_val > 1e-5:
            chroma /= max_val

        # Harmonic overtone filtering:
        # Dominant fundamental at PC x creates overtones at (x+7)%12 (3rd) and (x+4)%12 (5th)
        filtered_chroma = chroma.copy()
        for pc in range(12):
            if chroma[pc] > 0.65:
                third_harmonic_pc = (pc + 7) % 12
                fifth_harmonic_pc = (pc + 4) % 12

                filtered_chroma[third_harmonic_pc] = max(
                    0.0, filtered_chroma[third_harmonic_pc] - 0.35 * chroma[pc]
                )
                filtered_chroma[fifth_harmonic_pc] = max(
                    0.0, filtered_chroma[fifth_harmonic_pc] - 0.20 * chroma[pc]
                )

        return filtered_chroma
