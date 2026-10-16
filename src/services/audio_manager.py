"""
src/services/audio_manager.py
==============================
Centralized audio management service handling singleton hardware capture,
pitch analysis, device enumeration, and cross-view notification broadcasting.
"""

import json
import math
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional

from audio.pitch_detector import PitchDetector, list_input_devices

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

        target_id = None
        if self.current_device_id is not None and str(self.current_device_id) != "default":
            try:
                target_id = int(self.current_device_id)
            except ValueError:
                target_id = None

        # Singleton Pitch Detector with -65dB silence floor and 0.3 confidence threshold
        self.detector = PitchDetector(
            silence_threshold_db=-65.0,
            confidence_threshold=0.3,
            device=target_id,
        )
        self._poll_thread: Optional[threading.Thread] = None
        self._stop_polling = threading.Event()
        self._last_pitch_time = 0.0

        # Current Pitch State
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
            "pitch_data": None,
        }

        self.start_listening()

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
                json.dump({"device_id": str(device_id)}, f)
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

        target_id = None
        if device_id is not None and str(device_id) != "default":
            try:
                target_id = int(device_id)
            except ValueError:
                target_id = None

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

    def start_listening(self) -> None:
        """Starts hardware microphone capture and polling thread."""
        if self.is_listening and self.detector._is_running:
            return
        self.is_listening = True
        self._stop_polling.clear()
        try:
            self.detector.start()
        except Exception:
            pass

        if self._poll_thread is None or not self._poll_thread.is_alive():
            self._poll_thread = threading.Thread(target=self._polling_loop, daemon=True)
            self._poll_thread.start()

    def stop_listening(self) -> None:
        """Halts hardware microphone capture."""
        self.is_listening = False
        self._stop_polling.set()
        self.detector.stop()

    def _polling_loop(self) -> None:
        """Dedicated Python thread polling PitchDetector queue at ~40 FPS with 0.4s hold."""
        while not self._stop_polling.is_set() and self.is_listening:
            latest_pdata = None
            # Drain queue to obtain the single most recent audio frame
            while True:
                pdata = self.detector.get_latest(block=False)
                if pdata is None:
                    break
                latest_pdata = pdata

            now = time.time()

            if latest_pdata is not None:
                freq = latest_pdata.frequency
                conf = latest_pdata.confidence

                if freq > 20.0 and not latest_pdata.is_silent and conf >= 0.15:
                    self._last_pitch_time = now
                    midi_num = 69 + 12 * math.log2(freq / A4_FREQ)
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
                        "frequency": round(freq, 1),
                        "target_note": f"{pitch_name}{octave}",
                        "target_freq": round(target_freq, 1),
                        "cents_deviation": round(cents, 1),
                        "confidence": conf,
                        "is_in_tune": is_in_tune,
                        "direction": direction,
                        "raw_chords": [],
                        "pitch_data": latest_pdata,
                    }
                    self.broadcast_state()
                elif now - self._last_pitch_time > 0.4:
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
                        "pitch_data": latest_pdata,
                    }
                    self.broadcast_state()

            time.sleep(0.025)  # 25ms interval (~40 FPS)
