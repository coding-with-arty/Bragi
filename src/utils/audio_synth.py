# src/utils/audio_synth.py
import math
import threading
import numpy as np
import sounddevice as sd
from typing import List, Set, Optional
from audio.dsp_utils import A440_HZ


class AudioSynth:
    """Low-latency audio synthesizer for ear training playback and interval generation."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    @staticmethod
    def pitch_class_to_freq(pitch_class: int, octave: int = 4) -> float:
        """Calculates frequency in Hz for a pitch class (0..11) and octave integer."""
        midi_num = 12 * (octave + 1) + (pitch_class % 12)
        return A440_HZ * (2.0 ** ((midi_num - 69) / 12.0))

    def generate_plucked_tone(
        self,
        freq_hz: float,
        duration_sec: float = 1.2,
        pluck_hardness: float = 0.8
    ) -> np.ndarray:
        """
        Generates a synthetic plucked-string acoustic waveform with exponential decay
        and physical overtone damping (1st, 2nd, 3rd, 4th, and 5th harmonics).
        """
        num_samples = int(self.sample_rate * duration_sec)
        t = np.linspace(0, duration_sec, num_samples, endpoint=False, dtype=np.float32)

        # Harmonic overtone amplitudes for an acoustic plucked string
        harmonics = [
            (1.0, 1.0),                  # Fundamental
            (2.0, 0.50 * pluck_hardness), # 2nd Harmonic (Octave)
            (3.0, 0.25 * pluck_hardness), # 3rd Harmonic (Octave + 5th)
            (4.0, 0.12 * pluck_hardness), # 4th Harmonic (2 Octaves)
            (5.0, 0.06 * pluck_hardness), # 5th Harmonic (2 Octaves + M3)
        ]

        signal = np.zeros(num_samples, dtype=np.float32)
        for mult, amp in harmonics:
            h_freq = freq_hz * mult
            if h_freq < self.sample_rate / 2.0:
                # Higher harmonics decay faster than the fundamental
                decay_rate = 2.5 + (mult - 1.0) * 1.2
                h_env = np.exp(-decay_rate * t)
                signal += amp * np.sin(2.0 * np.pi * h_freq * t) * h_env

        # Quick attack envelope (5ms linear ramp up) to remove audio clicks
        attack_samples = int(self.sample_rate * 0.005)
        if attack_samples < num_samples:
            attack_ramp = np.linspace(0.0, 1.0, attack_samples, dtype=np.float32)
            signal[:attack_samples] *= attack_ramp

        return signal

    def generate_interval_audio(
        self,
        pc1: int,
        oct1: int,
        pc2: int,
        oct2: int,
        mode: str = "Harmonic (Simultaneous)",
        duration_sec: float = 1.6
    ) -> np.ndarray:
        """Synthesizes melodic or harmonic two-note interval audio."""
        freq1 = self.pitch_class_to_freq(pc1, oct1)
        freq2 = self.pitch_class_to_freq(pc2, oct2)

        total_samples = int(self.sample_rate * duration_sec)
        output = np.zeros(total_samples, dtype=np.float32)

        if "Harmonic" in mode:
            t1 = self.generate_plucked_tone(freq1, duration_sec)
            t2 = self.generate_plucked_tone(freq2, duration_sec)
            output = t1 + t2
        else:
            half_dur = duration_sec / 2.0
            if "Ascending" in mode:
                first_freq, second_freq = freq1, freq2
            else:
                first_freq, second_freq = freq2, freq1

            t1 = self.generate_plucked_tone(first_freq, half_dur)
            t2 = self.generate_plucked_tone(second_freq, half_dur)

            n1 = t1.size
            output[:n1] += t1
            rem = total_samples - n1
            output[n1 : n1 + min(rem, t2.size)] += t2[: min(rem, t2.size)]

        max_val = np.max(np.abs(output))
        if max_val > 0:
            output = (output / max_val) * 0.85

        return output.astype(np.float32)

    def generate_chord_audio(
        self,
        pitch_classes: Set[int],
        octave: int = 4,
        duration_sec: float = 1.6
    ) -> np.ndarray:
        """Synthesizes a polyphonic chord buffer by summing component string overtones."""
        num_samples = int(self.sample_rate * duration_sec)
        mixed = np.zeros(num_samples, dtype=np.float32)

        if not pitch_classes:
            return mixed

        sorted_pcs = sorted(list(pitch_classes))
        for idx, pc in enumerate(sorted_pcs):
            # Slightly stagger pitch octaves and voice spread for natural chord voicing
            oct_offset = octave + (1 if idx >= 3 else 0)
            freq = self.pitch_class_to_freq(pc, oct_offset)
            mixed += self.generate_plucked_tone(freq, duration_sec)

        max_val = np.max(np.abs(mixed))
        if max_val > 0:
            mixed = (mixed / max_val) * 0.85

        return mixed.astype(np.float32)

    def play_audio_async(self, audio_data: np.ndarray) -> None:
        """Plays PCM audio signal asynchronously in background thread."""
        def _play():
            try:
                sd.play(audio_data, samplerate=self.sample_rate, blocking=False)
            except Exception as err:
                print(f"[AudioSynth] Async playback error: {err}")

        threading.Thread(target=_play, daemon=True).start()

    def play_note_async(self, pitch_class: int, octave: int = 4, duration_sec: float = 1.2) -> None:
        freq = self.pitch_class_to_freq(pitch_class, octave)
        audio = self.generate_plucked_tone(freq, duration_sec)
        self.play_audio_async(audio)

    def play_interval_async(
        self, pc1: int, oct1: int, pc2: int, oct2: int, mode: str = "Harmonic (Simultaneous)"
    ) -> None:
        audio = self.generate_interval_audio(pc1, oct1, pc2, oct2, mode)
        self.play_audio_async(audio)

    def play_chord_async(self, pitch_classes: Set[int], octave: int = 4) -> None:
        audio = self.generate_chord_audio(pitch_classes, octave)
        self.play_audio_async(audio)
