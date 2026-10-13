"""
pitch_detector.py
=================
Real-time digital signal processing (DSP) pitch detection background worker
for fretted instruments (guitar and bass). Includes audio device enumeration[cite: 2].
"""

import collections
from dataclasses import dataclass
import logging
import math
import queue
import sys
from typing import Callable, Optional, List, Dict, Any

import aubio
import numpy as np
import sounddevice as sd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PitchDetector")

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def list_input_devices() -> List[Dict[str, Any]]:
    """Lists all available input audio devices (microphones) on the system."""
    devices = sd.query_devices()
    input_devices = []
    for idx, dev in enumerate(devices):
        if dev.get("max_input_channels", 0) > 0:
            input_devices.append({
                "index": idx,
                "name": dev.get("name"),
                "channels": dev.get("max_input_channels"),
                "default_samplerate": dev.get("default_samplerate")
            })
    return input_devices


@dataclass(slots=True)
class PitchData:
    """Encapsulates processed pitch detection frame data[cite: 2]."""
    frequency: float
    note_name: str
    octave: int
    cents: float
    db_level: float
    is_silent: bool
    is_stable: bool
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frequency": round(self.frequency, 2),
            "note_name": self.note_name,
            "octave": self.octave,
            "cents": round(self.cents, 1),
            "db_level": round(self.db_level, 1),
            "is_silent": self.is_silent,
            "is_stable": self.is_stable,
            "confidence": round(self.confidence, 3),
        }


def calculate_db_fs(signal: np.ndarray) -> float:
    """Calculate Root Mean Square (RMS) energy converted to dB relative to Full Scale (dBFS)[cite: 2]."""
    rms = np.sqrt(np.mean(np.square(signal)))
    if rms <= 1e-12:
        return -120.0
    return float(20.0 * np.log10(rms))


def freq_to_pitch_info(freq: float) -> tuple[str, int, float]:
    """
    Converts frequency in Hz to closest standard equal-temperament note name,
    octave number, and cents deviation (-50.0 to +50.0 cents, where A4 = 440 Hz)[cite: 2].
    """
    if freq <= 0.0:
        return "N/A", 0, 0.0

    midi_exact = 69.0 + 12.0 * math.log2(freq / 440.0)
    midi_rounded = round(midi_exact)
    cents = (midi_exact - midi_rounded) * 100.0

    note_name = NOTE_NAMES[midi_rounded % 12]
    octave = (midi_rounded // 12) - 1
    return note_name, octave, cents


class PitchDetector:
    """Real-time audio pitch detector with dynamic device switching[cite: 2]."""

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 2048,
        hop_size: int = 1024,
        silence_threshold_db: float = -45.0,
        pitch_method: str = "pitchyin",
        confidence_threshold: float = 0.7,
        stability_window: int = 3,
        device: Optional[int | str] = None,
        callback: Optional[Callable[[PitchData], None]] = None,
        queue_maxsize: int = 32,
    ) -> None:
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.hop_size = hop_size
        self.silence_threshold_db = silence_threshold_db
        self.pitch_method = pitch_method
        self.confidence_threshold = confidence_threshold
        self.stability_window = max(1, stability_window)
        self.device = device
        self.external_callback = callback

        self.data_queue: queue.Queue[PitchData] = queue.Queue(maxsize=queue_maxsize)
        self._is_running = False
        self._stream: Optional[sd.InputStream] = None
        self._pitch_o: Optional[aubio.pitch] = None
        self._history: collections.deque[tuple[str, int]] = collections.deque(
            maxlen=self.stability_window
        )

    def _init_aubio(self) -> None:
        """Initialize Aubio pitch detection instance[cite: 2]."""
        self._pitch_o = aubio.pitch(
            self.pitch_method, self.buffer_size, self.hop_size, self.sample_rate
        )
        self._pitch_o.set_unit("Hz")
        self._pitch_o.set_silence(self.silence_threshold_db)

    def set_device(self, device_id: Optional[int | str]) -> None:
        """Dynamically switch microphone device without destroying object state."""
        was_running = self._is_running
        if was_running:
            self.stop()
        self.device = device_id
        if was_running:
            self.start()

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags
    ) -> None:
        """Low-latency audio stream callback executed on C/audio input thread[cite: 2]."""
        if status:
            logger.warning("SoundDevice status flag: %s", status)

        signal = indata.flatten()
        db_level = calculate_db_fs(signal)
        is_silent = db_level < self.silence_threshold_db

        note_name, octave, cents = "N/A", 0, 0.0
        pitch_hz = 0.0
        confidence = 0.0
        is_stable = False

        if not is_silent and self._pitch_o is not None:
            pitch_hz = float(self._pitch_o(signal)[0])
            confidence = float(self._pitch_o.get_confidence())

            if pitch_hz > 0.0 and confidence >= self.confidence_threshold:
                note_name, octave, cents = freq_to_pitch_info(pitch_hz)

                self._history.append((note_name, octave))
                if (
                    len(self._history) == self.stability_window
                    and len(set(self._history)) == 1
                ):
                    is_stable = True
            else:
                self._history.clear()
        else:
            self._history.clear()

        pitch_data = PitchData(
            frequency=pitch_hz,
            note_name=note_name,
            octave=octave,
            cents=cents,
            db_level=db_level,
            is_silent=is_silent,
            is_stable=is_stable,
            confidence=confidence,
        )

        if self.external_callback is not None:
            try:
                self.external_callback(pitch_data)
            except Exception as err:
                logger.error("Error in external callback: %s", err)

        try:
            self.data_queue.put_nowait(pitch_data)
        except queue.Full:
            try:
                self.data_queue.get_nowait()
                self.data_queue.put_nowait(pitch_data)
            except queue.Empty:
                pass

    def start(self) -> None:
        """Start capturing audio stream and processing pitch[cite: 2]."""
        if self._is_running:
            return

        self._init_aubio()
        self._history.clear()

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=self.hop_size,
                device=self.device,
                channels=1,
                dtype="float32",
                callback=self._audio_callback,
            )
            self._stream.start()
            self._is_running = True
            logger.info("Audio stream started on device %s.", self.device)
        except Exception as err:
            logger.error("Failed to open audio input stream: %s", err)
            raise err

    def stop(self) -> None:
        """Stop audio stream and release DSP resources[cite: 2]."""
        if not self._is_running:
            return

        self._is_running = False
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        self._pitch_o = None
        logger.info("Audio stream stopped.")

    def get_latest(self, block: bool = False, timeout: Optional[float] = None) -> Optional[PitchData]:
        """Fetch processed PitchData frame from queue[cite: 2]."""
        try:
            return self.data_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
