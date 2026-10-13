"""
pitch_detector.py
=================
A real-time digital signal processing (DSP) pitch detection background worker
for fretted instruments (guitar and bass).

Dependencies:
    pip install sounddevice aubio numpy
"""

import collections
from dataclasses import dataclass
import logging
import math
import queue
import sys
from typing import Callable, Optional

import aubio
import numpy as np
import sounddevice as sd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("PitchDetector")

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass(slots=True)
class PitchData:
    """Encapsulates processed pitch detection frame data."""
    frequency: float
    note_name: str
    octave: int
    cents: float
    db_level: float
    is_silent: bool
    is_stable: bool
    confidence: float


def calculate_db_fs(signal: np.ndarray) -> float:
    """Calculate Root Mean Square (RMS) energy converted to dB relative to Full Scale (dBFS)."""
    rms = np.sqrt(np.mean(np.square(signal)))
    if rms <= 1e-12:
        return -120.0
    return float(20.0 * np.log10(rms))


def freq_to_pitch_info(freq: float) -> tuple[str, int, float]:
    """
    Converts frequency in Hz to closest standard equal-temperament note name,
    octave number, and cents deviation (-50.0 to +50.0 cents, where A4 = 440 Hz).
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
    """
    Real-time audio pitch detector using sounddevice and Aubio pitch tracking algorithms.

    Acts as a decoupled background worker emitting structured PitchData via thread-safe
    queues or callbacks.
    """

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

        # Thread-safe queue for async consumer integration (e.g., Flet UI event loop)
        self.data_queue: queue.Queue[PitchData] = queue.Queue(maxsize=queue_maxsize)

        # Internal state
        self._is_running = False
        self._stream: Optional[sd.InputStream] = None
        self._pitch_o: Optional[aubio.pitch] = None
        self._history: collections.deque[tuple[str, int]] = collections.deque(
            maxlen=self.stability_window
        )

    def _init_aubio(self) -> None:
        """Initialize the Aubio pitch detection instance."""
        self._pitch_o = aubio.pitch(
            self.pitch_method, self.buffer_size, self.hop_size, self.sample_rate
        )
        self._pitch_o.set_unit("Hz")
        self._pitch_o.set_silence(self.silence_threshold_db)

    def _audio_callback(
        self, indata: np.ndarray, frames: int, time_info: dict, status: sd.CallbackFlags
    ) -> None:
        """Low-latency audio stream callback executed on C/audio input thread."""
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

                # Transient debouncing: check for N consecutive matching readings
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
        """Start capturing audio stream and processing pitch."""
        if self._is_running:
            logger.warning("PitchDetector is already running.")
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
            logger.info("Audio stream started successfully.")
        except Exception as err:
            logger.error("Failed to open audio input stream: %s", err)
            raise err

    def stop(self) -> None:
        """Stop audio stream and release DSP resources."""
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
        """Fetch processed PitchData frame from queue."""
        try:
            return self.data_queue.get(block=block, timeout=timeout)
        except queue.Empty:
            return None

    def __enter__(self) -> "PitchDetector":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


def format_tuning_status(cents: float) -> str:
    """Formats cents into a human-readable string."""
    if abs(cents) <= 5.0:
        return "In-Tune"
    elif cents < -5.0:
        return f"{cents:.1f} Flat"
    else:
        return f"+{cents:.1f} Sharp"


if __name__ == "__main__":
    print("\n--- Real-Time Instrument Pitch Detector ---")
    print("Streaming microphone audio. Press Ctrl+C to stop.\n")

    detector = PitchDetector(
        sample_rate=44100,
        buffer_size=2048,
        hop_size=1024,
        silence_threshold_db=-45.0,
        stability_window=3,
    )

    try:
        detector.start()
        while True:
            data = detector.get_latest(block=True, timeout=0.5)
            if data is None:
                continue

            if data.is_silent:
                status_str = f"[Silent] Volume: {data.db_level:.1f} dB"
            else:
                tuning = format_tuning_status(data.cents)
                stability_flag = "✓" if data.is_stable else "…"
                status_str = (
                    f"[Playing {stability_flag}] Note: {data.note_name}{data.octave} | "
                    f"Freq: {data.frequency:6.2f} Hz | Cents: {data.cents:+5.1f} ({tuning}) | "
                    f"Volume: {data.db_level:.1f} dB"
                )

            sys.stdout.write(f"\r{status_str:<85}")
            sys.stdout.flush()

    except KeyboardInterrupt:
        print("\n\nShutting down pitch detector...")
    finally:
        detector.stop()
        print("Shutdown complete.")
