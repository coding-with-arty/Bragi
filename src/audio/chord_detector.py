# src/audio/chord_detector.py
import collections
import numpy as np
from typing import Set, Tuple
from audio.dsp_utils import calculate_rms_dbfs, frequency_to_pitch_class


class ChordDetector:
    """
    Polyphonic DSP chord detector designed for strummed stringed instruments.
    Maintains an internal 8192-sample rolling PCM ring buffer for fine FFT resolution
    and integrates chromagram peaks across a multi-frame sliding window to capture strummed notes.
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        silence_threshold_db: float = -45.0,
        chroma_threshold: float = 0.18,
        buffer_capacity: int = 8192,
        integration_frames: int = 6
    ) -> None:
        self.sample_rate = sample_rate
        self.silence_threshold_db = silence_threshold_db
        self.chroma_threshold = chroma_threshold
        self.buffer_capacity = buffer_capacity

        # Rolling PCM sample accumulation ring buffer
        self._pcm_ring_buffer = np.zeros(self.buffer_capacity, dtype=np.float32)

        # Multi-frame chromagram peak history (holds energy across ~200ms strum sweep)
        self._chroma_history = collections.deque(maxlen=integration_frames)

    def process_frame(self, signal: np.ndarray) -> Tuple[Set[int], float, bool, np.ndarray]:
        """
        Processes an incoming PCM audio frame. Pushes samples to the ring buffer,
        computes high-resolution chromagram energy, and extracts active pitch classes.

        :param signal: 1D NumPy float32 PCM sample array
        :return: Tuple of (active_pitch_classes_set, volume_db, is_silent, integrated_chroma_vector)
        """
        if signal is None or signal.size == 0:
            return set(), -120.0, True, np.zeros(12, dtype=np.float32)

        volume_db = calculate_rms_dbfs(signal)
        is_silent = volume_db < self.silence_threshold_db

        if is_silent:
            self._chroma_history.clear()
            return set(), volume_db, True, np.zeros(12, dtype=np.float32)

        # Append incoming frame samples to the 8192-sample rolling ring buffer
        num_samples = signal.size
        if num_samples >= self.buffer_capacity:
            self._pcm_ring_buffer = signal[-self.buffer_capacity:].astype(np.float32)
        else:
            self._pcm_ring_buffer = np.roll(self._pcm_ring_buffer, -num_samples)
            self._pcm_ring_buffer[-num_samples:] = signal.astype(np.float32)

        # Compute high-resolution 12-bin pitch class chromagram on 8192 window
        frame_chroma = self._compute_chromagram(self._pcm_ring_buffer)
        self._chroma_history.append(frame_chroma)

        # Aggregate maximum peak magnitude across the strum integration window
        integrated_chroma = np.max(np.array(self._chroma_history), axis=0)

        # Peak normalize integrated chromagram vector
        max_val = np.max(integrated_chroma)
        if max_val > 1e-5:
            integrated_chroma /= max_val
        else:
            return set(), volume_db, True, integrated_chroma

        # Extract active pitch classes exceeding calibrated chroma detection threshold
        active_pitch_classes = {
            pc for pc in range(12) if integrated_chroma[pc] >= self.chroma_threshold
        }

        return active_pitch_classes, volume_db, False, integrated_chroma

    def _compute_chromagram(self, pcm_data: np.ndarray) -> np.ndarray:
        """Computes 12-bin normalized chromagram with tuned harmonic filtering."""
        chroma = np.zeros(12, dtype=np.float32)
        if pcm_data.size < 1024:
            return chroma

        # Apply Hann window to minimize spectral leakage
        windowed = pcm_data * np.hanning(pcm_data.size)
        fft_mags = np.abs(np.fft.rfft(windowed))
        fft_freqs = np.fft.rfftfreq(pcm_data.size, d=1.0 / self.sample_rate)

        # Accumulate magnitude into pitch class bins across guitar pitch range (C2 ~65Hz to C6 ~1046Hz)
        for freq, mag in zip(fft_freqs, fft_mags):
            if 65.0 <= freq <= 1046.5:
                pc, _, _, _ = frequency_to_pitch_class(freq)
                chroma[pc] += mag

        # Peak normalize single frame chroma
        max_val = np.max(chroma)
        if max_val > 1e-5:
            chroma /= max_val

        # Gentle overtone filter: attenuate 3rd harmonic (7 semitones) only if fundamental is dominant
        filtered_chroma = chroma.copy()
        for pc in range(12):
            fifth_overtone_pc = (pc + 7) % 12
            if chroma[pc] > 0.88:
                filtered_chroma[fifth_overtone_pc] = max(
                    0.0, filtered_chroma[fifth_overtone_pc] - 0.20 * chroma[pc]
                )

        return filtered_chroma
