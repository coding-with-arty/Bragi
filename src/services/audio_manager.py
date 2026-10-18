# src/services/audio_manager.py
"""
Audio Manager Singleton
=======================
Handles hardware microphone capture, real-time autocorrelation pitch detection,
device filtering, and audio sample distribution with low-frequency bass optimization.
"""

import math
import numpy as np
import sounddevice as sd
from typing import List, Dict, Any, Optional, Callable
from utils.music_theory import CHROMATIC_SHARPS


class PitchDetector:
    """Real-time pitch detector using FFT autocorrelation, peak normalization, and sub-sample interpolation."""

    def __init__(self, sample_rate: int = 44100):
        self.sample_rate = sample_rate

    def process_samples(self, samples: np.ndarray, sample_rate: int = 44100) -> dict:
        """Processes raw audio samples and returns frequency, note name, and cents deviation."""
        if samples is None or len(samples) < 512:
            return {
                "pitch": 0.0,
                "frequency": 0.0,
                "volume_db": -80.0,
                "is_silent": True,
                "cents": 0.0,
                "note_name": "",
                "pitch_class": 0,
            }

        sr = sample_rate or self.sample_rate

        # 1. Remove DC offset to center the waveform
        centered_samples = samples - np.mean(samples)

        # 2. Compute RMS volume before normalization
        rms = np.sqrt(np.mean(centered_samples**2))
        volume_db = 20.0 * math.log10(rms) if rms > 1e-5 else -80.0

        # Silence gating threshold (-52 dBFS allows quiet low strings to register)
        if volume_db < -52.0:
            return {
                "pitch": 0.0,
                "frequency": 0.0,
                "volume_db": volume_db,
                "is_silent": True,
                "cents": 0.0,
                "note_name": "",
                "pitch_class": 0,
            }

        # 3. Software Peak Normalization (boosts low signals safely without hardware clipping)
        max_amplitude = np.max(np.abs(centered_samples))
        if max_amplitude > 1e-4:
            normalized_samples = centered_samples / max_amplitude
        else:
            normalized_samples = centered_samples

        # 4. Apply Hanning window to prevent spectral leakage
        windowed = normalized_samples * np.hanning(len(normalized_samples))
        n = len(windowed)

        # 5. Calculate autocorrelation via FFT
        f = np.fft.rfft(windowed, n=2 * n)
        acf = np.fft.irfft(f * np.conj(f))[:n]

        if acf[0] <= 0:
            return {
                "pitch": 0.0,
                "frequency": 0.0,
                "volume_db": volume_db,
                "is_silent": True,
                "cents": 0.0,
                "note_name": "",
                "pitch_class": 0,
            }

        acf = acf / acf[0]

        # 6. Expanded frequency search bounds (30 Hz ~ Low B on 5-string bass up to 1400 Hz)
        min_period = max(1, int(sr / 1400))
        max_period = min(len(acf) - 2, int(sr / 30))

        if min_period >= max_period or max_period >= len(acf):
            return {
                "pitch": 0.0,
                "frequency": 0.0,
                "volume_db": volume_db,
                "is_silent": True,
                "cents": 0.0,
                "note_name": "",
                "pitch_class": 0,
            }

        lag_search = acf[min_period:max_period]
        if len(lag_search) == 0:
            return {
                "pitch": 0.0,
                "frequency": 0.0,
                "volume_db": volume_db,
                "is_silent": True,
                "cents": 0.0,
                "note_name": "",
                "pitch_class": 0,
            }

        peak_idx = np.argmax(lag_search) + min_period
        peak_val = acf[peak_idx]

        # Relaxed peak threshold (0.18) allows low fundamental frequencies to register
        if peak_val < 0.18:
            return {
                "pitch": 0.0,
                "frequency": 0.0,
                "volume_db": volume_db,
                "is_silent": True,
                "cents": 0.0,
                "note_name": "",
                "pitch_class": 0,
            }

        # 7. Parabolic interpolation for sub-sample accuracy
        if 0 < peak_idx < len(acf) - 1:
            alpha = acf[peak_idx - 1]
            beta = acf[peak_idx]
            gamma = acf[peak_idx + 1]
            denom = alpha - 2 * beta + gamma
            delta = (alpha - gamma) / (2 * denom) if denom != 0 else 0
            fine_period = peak_idx + delta
        else:
            fine_period = float(peak_idx)

        if fine_period <= 0:
            return {
                "pitch": 0.0,
                "frequency": 0.0,
                "volume_db": volume_db,
                "is_silent": True,
                "cents": 0.0,
                "note_name": "",
                "pitch_class": 0,
            }

        freq_hz = sr / fine_period

        # 8. Convert Hz to MIDI Note & Cents Error (A4 = 440 Hz = MIDI 69)
        midi_note = 69.0 + 12.0 * math.log2(freq_hz / 440.0)
        nearest_midi = int(round(midi_note))
        cents_error = (midi_note - nearest_midi) * 100.0

        pitch_class = nearest_midi % 12
        note_name = CHROMATIC_SHARPS[pitch_class]

        return {
            "pitch": freq_hz,
            "frequency": freq_hz,
            "volume_db": volume_db,
            "is_silent": False,
            "cents": cents_error,
            "note_name": note_name,
            "pitch_class": pitch_class,
        }


class AudioManager:
    """Singleton service managing audio input streams and device selection."""

    _instance: Optional["AudioManager"] = None

    def __init__(self) -> None:
        if AudioManager._instance is not None:
            raise RuntimeError("AudioManager is a singleton. Use AudioManager.get_instance().")

        self.stream: Optional[sd.InputStream] = None
        self.current_device_id: Optional[int] = None
        self.sample_rate: int = 44100

        # Expanded block_size to 4096 for reliable low E / bass guitar detection
        self.block_size: int = 4096
        self.is_listening: bool = False

        self.detector = PitchDetector(self.sample_rate)
        self.listeners: List[Callable[[dict], None]] = []
        self.latest_volume_db: float = -80.0

        self._current_state: Dict[str, Any] = {
            "pitch_data": {
                "pitch": 0.0,
                "frequency": 0.0,
                "volume_db": -80.0,
                "is_silent": True,
                "cents": 0.0,
                "note_name": "",
                "pitch_class": 0,
            },
            "volume_db": -80.0,
            "is_silent": True,
            "samples": np.array([], dtype=np.float32),
            "sample_rate": 44100,
        }

    @classmethod
    def get_instance(cls) -> "AudioManager":
        if cls._instance is None:
            cls._instance = AudioManager()
        return cls._instance

    @property
    def current_state(self) -> Dict[str, Any]:
        return self._current_state

    @staticmethod
    def get_filtered_input_devices() -> List[Dict[str, Any]]:
        try:
            all_devices = sd.query_devices()
            host_apis = sd.query_hostapis()
            default_hostapi = sd.default.hostapi
        except Exception:
            return [{"id": None, "name": "Default Microphone", "is_default": True}]

        filtered_devices: List[Dict[str, Any]] = []
        seen_names = set()

        for idx, dev in enumerate(all_devices):
            if dev.get("max_input_channels", 0) > 0:
                host_idx = dev.get("hostapi", 0)
                if host_idx == default_hostapi:
                    clean_name = dev["name"].strip()
                    if clean_name not in seen_names:
                        seen_names.add(clean_name)
                        filtered_devices.append({
                            "id": idx,
                            "name": clean_name,
                            "channels": dev["max_input_channels"],
                            "default_samplerate": int(dev.get("default_samplerate", 44100)),
                            "is_default": (idx == sd.default.device[0]),
                        })

        for idx, dev in enumerate(all_devices):
            if dev.get("max_input_channels", 0) > 0:
                clean_name = dev["name"].strip()
                if clean_name not in seen_names:
                    seen_names.add(clean_name)
                    host_name = host_apis[dev.get("hostapi", 0)]["name"]
                    filtered_devices.append({
                        "id": idx,
                        "name": f"{clean_name} ({host_name})",
                        "channels": dev["max_input_channels"],
                        "default_samplerate": int(dev.get("default_samplerate", 44100)),
                        "is_default": False,
                    })

        return filtered_devices

    def start_listening(self, device_id: Optional[int] = None) -> bool:
        self.stop_listening()

        devices = self.get_filtered_input_devices()
        if not devices:
            return False

        target_id = device_id
        if target_id is None:
            default_dev = next((d for d in devices if d["is_default"]), devices[0])
            target_id = default_dev["id"]

        try:
            dev_info = sd.query_devices(target_id)
            self.sample_rate = int(dev_info.get("default_samplerate", 44100))
        except Exception:
            self.sample_rate = 44100

        self.current_device_id = target_id
        self.detector = PitchDetector(self.sample_rate)

        try:
            self.stream = sd.InputStream(
                device=self.current_device_id,
                channels=1,
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                dtype="float32",
                callback=self._audio_callback,
            )
            self.stream.start()
            self.is_listening = True
            print(f"[AudioManager] Hardware capture started on device ID: {self.current_device_id}")
            return True
        except Exception as err:
            print(f"[AudioManager] Failed to open device {self.current_device_id}: {err}")
            if target_id is not None:
                return self.start_listening(device_id=None)
            return False

    def stop_listening(self) -> None:
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        self.is_listening = False

    def subscribe(self, listener: Callable[[dict], None]) -> None:
        if listener not in self.listeners:
            self.listeners.append(listener)

    def unsubscribe(self, listener: Callable[[dict], None]) -> None:
        if listener in self.listeners:
            self.listeners.remove(listener)

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
        if status:
            print(f"[AudioManager] Stream status warning: {status}")

        samples = indata[:, 0]
        rms = np.sqrt(np.mean(samples**2)) if len(samples) > 0 else 0.0
        self.latest_volume_db = 20.0 * math.log10(rms) if rms > 1e-5 else -80.0

        # Execute autocorrelation pitch analysis on current frame
        pitch_info = self.detector.process_samples(samples, self.sample_rate)

        self._current_state = {
            "pitch_data": pitch_info,
            "volume_db": self.latest_volume_db,
            "is_silent": pitch_info.get("is_silent", True),
            "samples": samples,
            "sample_rate": self.sample_rate,
        }

        payload = {
            "event": "audio_frame",
            "samples": samples,
            "sample_rate": self.sample_rate,
            "volume_db": self.latest_volume_db,
            "is_silent": pitch_info.get("is_silent", True),
            "pitch_data": pitch_info,
        }

        for listener in list(self.listeners):
            try:
                listener(payload)
            except Exception as err:
                print(f"[AudioManager] Subscriber error: {err}")
