"""
src/services/audio_manager.py
==============================
Centralized audio management service responsible for hardware device enumeration,
low-latency audio capture via PitchDetector, pitch analysis, and cross-view notification broadcasting.
"""

import json
import math
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional
import flet as ft

from audio.pitch_detector import PitchDetector, list_input_devices

# Pitch Constants
A4_FREQ = 440.0
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


class AudioManager:
    """Singleton audio service handling capture, pitch analysis, device enumeration, and state."""

    _instance: Optional["AudioManager"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AudioManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    @classmethod
    def get_instance(cls) -> "AudioManager":
        if cls._instance is None:
            cls._instance = AudioManager()
        return cls._instance

    def _initialize(self) -> None:
        self.config_path = Path(__file__).parent.parent.parent / "audio_config.json"
        self.is_listening = False
        saved_id = self._load_persisted_device()
        self.current_device_id = saved_id if saved_id is not None else "default"
        self.listeners: List[Callable[[Dict], None]] = []

        # Pitch Detector Instance & Polling State
        self.detector = PitchDetector()
        self._poll_thread: Optional[threading.Thread] = None
        self._stop_polling = threading.Event()

        # Set initial device on detector
        target_id = int(self.current_device_id) if (self.current_device_id is not None and str(self.current_device_id) != "default") else None
        self.detector.set_device(target_id)

        # Current Pitch Detection State
        self.current_state = {
            "pitch_class": "--",
            "octave": 0,
            "frequency": 0.0,
            "target_note": "--",
            "target_freq": 0.0,
            "cents_deviation": 0.0,
            "confidence": 0.0,
            "is_in_tune": False,
            "direction": "NO SIGNAL",
            "raw_chords": [],
        }

    def _load_persisted_device(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                    return data.get("device_id")
            except Exception:
                pass
        return None

    def _persist_device(self, device_id) -> None:
        try:
            with open(self.config_path, "w") as f:
                json.dump({"device_id": device_id}, f)
        except Exception:
            pass

    def get_available_devices(self) -> List[Dict]:
        """Enumerates real system audio input devices."""
        devices = []
        try:
            mics = list_input_devices()
            for m in mics:
                idx = m["index"]
                dev_id = "default" if idx is None else idx
                devices.append({
                    "id": dev_id,
                    "name": m["name"],
                    "type": "System Input Device",
                    "is_default": (idx is None or dev_id == "default"),
                    "status": "Available",
                })
        except Exception:
            devices = [
                {
                    "id": "default",
                    "name": "Default Microphone (System)",
                    "type": "Built-in / System",
                    "is_default": True,
                    "status": "Available",
                }
            ]
        return devices

    def set_input_device(self, device_id) -> bool:
        """Globally updates audio input device and notifies all active view subscribers."""
        self.current_device_id = device_id
        self._persist_device(device_id)

        target_id = int(device_id) if (device_id is not None and str(device_id) != "default") else None
        self.detector.set_device(target_id)

        self.broadcast_state({
            "event": "device_changed",
            "device_id": device_id,
        })
        return True

    def subscribe(self, callback: Callable[[Dict], None]) -> None:
        if callback not in self.listeners:
            self.listeners.append(callback)

    def unsubscribe(self, callback: Callable[[Dict], None]) -> None:
        if callback in self.listeners:
            self.listeners.remove(callback)

    def broadcast_state(self, data: Optional[Dict] = None) -> None:
        payload = data or self.current_state
        for callback in list(self.listeners):
            try:
                callback(payload)
            except Exception:
                pass

    def process_frequency(self, frequency: float, confidence: float = 0.95) -> Dict:
        """Calculates chromatic pitch, target frequency, cents deviation, and tuning direction."""
        if frequency <= 20.0 or confidence < 0.15:
            self.current_state = {
                "pitch_class": "--",
                "octave": 0,
                "frequency": 0.0,
                "target_note": "--",
                "target_freq": 0.0,
                "cents_deviation": 0.0,
                "confidence": 0.0,
                "is_in_tune": False,
                "direction": "NO SIGNAL",
                "raw_chords": [],
            }
            self.broadcast_state()
            return self.current_state

        midi_num = 69 + 12 * math.log2(frequency / A4_FREQ)
        nearest_midi = round(midi_num)
        target_freq = A4_FREQ * (2 ** ((nearest_midi - 69) / 12))

        cents = (midi_num - nearest_midi) * 100.0
        note_index = nearest_midi % 12
        pitch_name = NOTE_NAMES[note_index]
        octave = (nearest_midi // 12) - 1

        is_in_tune = abs(cents) <= 5.0
        direction = "IN TUNE" if is_in_tune else ("TOO SHARP" if cents > 0 else "TOO FLAT")

        self.current_state = {
            "pitch_class": pitch_name,
            "octave": octave,
            "frequency": round(frequency, 1),
            "target_note": f"{pitch_name}{octave}",
            "target_freq": round(target_freq, 1),
            "cents_deviation": round(cents, 1),
            "confidence": confidence,
            "is_in_tune": is_in_tune,
            "direction": direction,
            "raw_chords": [],
        }

        self.broadcast_state()
        return self.current_state

    def start_listening(self) -> None:
        """Starts the audio pitch detector and background polling thread."""
        if self.is_listening:
            return
        self.is_listening = True
        self._stop_polling.clear()
        self.detector.start()

        self._poll_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self._poll_thread.start()

    def stop_listening(self) -> None:
        """Stops background pitch polling and halts detector."""
        self.is_listening = False
        self._stop_polling.set()
        self.detector.stop()
        self.process_frequency(0.0, 0.0)

    def _polling_loop(self) -> None:
        """Background loop fetching latest pitch data from PitchDetector."""
        while not self._stop_polling.is_set() and self.is_listening:
            pdata = self.detector.get_latest(block=False)
            if pdata and pdata.frequency > 20.0:
                conf = 0.95 if getattr(pdata, "db_level", -30.0) > -50.0 else 0.2
                self.process_frequency(pdata.frequency, confidence=conf)
            elif pdata is None or pdata.frequency <= 20.0:
                self.process_frequency(0.0, 0.0)
            time.sleep(0.03)
