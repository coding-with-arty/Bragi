"""
src/utils/audio_synth.py
========================
Low-latency audio synthesizer generating synthesized piano/guitar tones
for ear training playback.
"""

import math
import numpy as np
import sounddevice as sd
from typing import List, Set
from utils.music_theory import MusicTheory
from audio.dsp_utils import A440_HZ


class AudioSynth:
    """Synthesizes and plays polyphonic audio samples using sounddevice."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    @staticmethod
    def pitch_class_to_freq(pitch_class: int, octave: int = 4) -> float:
        """Calculates frequency in Hz for a pitch class and octave integer."""
        midi_num = 12 * (octave + 1) + (pitch_class % 12)
        return A440_HZ * (2.0 ** ((midi_num - 69) / 12.0))

    def generate_tone(self, freq_hz: float, duration_sec: float = 1.0) -> np.ndarray:
        """Generates a single harmonic sine wave with ADSR amplitude envelope."""
        num_samples = int(self.sample_rate * duration_sec)
        t = np.linspace(0, duration_sec, num_samples, endpoint=False)

        # Fundamental + 2nd & 3rd harmonic overtones
        signal = (
            0.6 * np.sin(2 * np.pi * freq_hz * t) +
            0.25 * np.sin(2 * np.pi * (freq_hz * 2) * t) +
            0.15 * np.sin(2 * np.pi * (freq_hz * 3) * t)
        )

        # Exponential decay amplitude envelope
        envelope = np.exp(-3.0 * t)
        sound = signal * envelope
        return sound.astype(np.float32)

    def generate_chord_audio(self, pitch_classes: Set[int], octave: int = 4, duration_sec: float = 1.5) -> np.ndarray:
        """Synthesizes a polyphonic chord by summing component pitch frequencies."""
        num_samples = int(self.sample_rate * duration_sec)
        mixed_signal = np.zeros(num_samples, dtype=np.float32)

        if not pitch_classes:
            return mixed_signal

        for pc in pitch_classes:
            freq = self.pitch_class_to_freq(pc, octave)
            mixed_signal += self.generate_tone(freq, duration_sec)

        # Normalize amplitude to prevent digital clipping
        max_val = np.max(np.abs(mixed_signal))
        if max_val > 0:
            mixed_signal = (mixed_signal / max_val) * 0.85

        return mixed_signal

    def play_chord_async(self, pitch_classes: Set[int], octave: int = 4, duration_sec: float = 1.5) -> None:
        """Synthesizes and plays a chord audio sample asynchronously in background."""
        try:
            audio_data = self.generate_chord_audio(pitch_classes, octave, duration_sec)
            sd.play(audio_data, samplerate=self.sample_rate, blocking=False)
        except Exception as err:
            print(f"[AudioSynth] Playback error: {err}")
