import math
import threading
import time
import numpy as np
import sounddevice as sd
from typing import List, Set, Optional
from utils.music_theory import A440_HZ


class AudioSynth:
    """Low-latency audio synthesizer with active playback state guards."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate
        self.is_playing: bool = False
        self.last_playback_time: float = 0.0

    @staticmethod
    def pitch_class_to_freq(pitch_class: int, octave: int = 4) -> float:
        midi_num = 12 * (octave + 1) + (pitch_class % 12)
        return A440_HZ * (2.0 ** ((midi_num - 69) / 12.0))

    def generate_plucked_tone(
        self,
        freq_hz: float,
        duration_sec: float = 1.2,
        pluck_hardness: float = 0.8
    ) -> np.ndarray:
        num_samples = int(self.sample_rate * duration_sec)
        t = np.linspace(0, duration_sec, num_samples, endpoint=False, dtype=np.float32)

        harmonics = [
            (1.0, 1.0),
            (2.0, 0.50 * pluck_hardness),
            (3.0, 0.25 * pluck_hardness),
            (4.0, 0.12 * pluck_hardness),
            (5.0, 0.06 * pluck_hardness),
        ]

        signal = np.zeros(num_samples, dtype=np.float32)
        for mult, amp in harmonics:
            h_freq = freq_hz * mult
            if h_freq < self.sample_rate / 2.0:
                decay_rate = 2.5 + (mult - 1.0) * 1.2
                h_env = np.exp(-decay_rate * t)
                signal += amp * np.sin(2.0 * np.pi * h_freq * t) * h_env

        attack_samples = int(self.sample_rate * 0.005)
        if attack_samples < num_samples:
            attack_ramp = np.linspace(0.0, 1.0, attack_samples, dtype=np.float32)
            signal[:attack_samples] *= attack_ramp

        return signal

    def play_audio_async(self, audio_data: np.ndarray) -> None:
        """Plays PCM audio signal asynchronously while setting playback state flags."""
        def _play():
            try:
                self.is_playing = True
                sd.play(audio_data, samplerate=self.sample_rate, blocking=True)
            except Exception as err:
                print(f"[AudioSynth] Playback error: {err}")
            finally:
                self.is_playing = False
                self.last_playback_time = time.time()

        threading.Thread(target=_play, daemon=True).start()

    def play_note_async(self, pitch_class: int, octave: int = 4, duration_sec: float = 1.2) -> None:
        freq = self.pitch_class_to_freq(pitch_class, octave)
        audio = self.generate_plucked_tone(freq, duration_sec)
        self.play_audio_async(audio)

    def play_chord_async(self, pitch_classes: Set[int], octave: int = 4) -> None:
        num_samples = int(self.sample_rate * 1.6)
        mixed = np.zeros(num_samples, dtype=np.float32)

        if pitch_classes:
            sorted_pcs = sorted(list(pitch_classes))
            for idx, pc in enumerate(sorted_pcs):
                oct_offset = octave + (1 if idx >= 3 else 0)
                freq = self.pitch_class_to_freq(pc, oct_offset)
                mixed += self.generate_plucked_tone(freq, 1.6)

            max_val = np.max(np.abs(mixed))
            if max_val > 0:
                mixed = (mixed / max_val) * 0.85

        self.play_audio_async(mixed.astype(np.float32))
