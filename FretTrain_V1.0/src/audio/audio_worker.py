"""
audio_worker.py - Thread-Safe Background Audio Processing Engine[cite: 1]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
import json
import math
import sys
import threading
import time
from typing import Callable, Optional, Tuple, Any, Dict

CHROMATIC_NOTES: list[str] = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
]

GUITAR_STRINGS: dict[int, Tuple[str, int]] = {
    6: ("E", 2),
    5: ("A", 2),
    4: ("D", 3),
    3: ("G", 3),
    2: ("B", 3),
    1: ("E", 4),
}


class MatchState(Enum):
    """Internal state tracking for pitch matching debouncer[cite: 1]."""
    SEARCHING = auto()
    HOLDING = auto()
    LOCKED_OUT = auto()


@dataclass(frozen=True, slots=True)
class TargetNote:
    """Represents a target note to be matched by the audio worker[cite: 1]."""
    note_name: str
    octave: Optional[int] = None

    def __post_init__(self) -> None:
        formatted = self.note_name.strip().upper()
        if formatted not in CHROMATIC_NOTES:
            raise ValueError(f"Invalid note name '{self.note_name}'. Must be one of {CHROMATIC_NOTES}")
        object.__setattr__(self, 'note_name', formatted)

    @property
    def display_name(self) -> str:
        return f"{self.note_name}{self.octave}" if self.octave is not None else self.note_name


@dataclass(frozen=True, slots=True)
class ToneMatchStatement:
    """Structured evaluation statement emitted for frettrain consumption."""
    is_correct: bool
    status: str
    target_note: str
    detected_note: str
    cents_error: float
    frequency_hz: float
    volume_db: float
    elapsed_seconds: float
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_correct": self.is_correct,
            "status": self.status,
            "target_note": self.target_note,
            "detected_note": self.detected_note,
            "cents_error": round(self.cents_error, 1),
            "frequency_hz": round(self.frequency_hz, 2),
            "volume_db": round(self.volume_db, 1),
            "elapsed_seconds": round(self.elapsed_seconds, 2),
            "timestamp": self.timestamp,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass(frozen=True, slots=True)
class PitchData:
    """Immutable real-time payload dispatched on every audio processing frame[cite: 1]."""
    frequency: float
    cents: float
    volume_db: float
    detected_note: str
    octave: int
    is_in_tune: bool
    raw_pitch_str: str


@dataclass
class AudioWorkerConfig:
    """Configurable thresholds for audio engine matching and debouncing logic[cite: 1]."""
    tolerance_cents: float = 25.0
    min_volume_db: float = -45.0
    hold_duration_sec: float = 0.30
    lockout_duration_sec: float = 0.50
    require_octave_match: bool = True


class AudioWorker:
    """Thread-safe background audio manager wrapper[cite: 1]."""

    def __init__(
        self,
        pitch_detector: Any,
        config: Optional[AudioWorkerConfig] = None,
        on_pitch_update: Optional[Callable[[PitchData], None]] = None,
        on_note_matched: Optional[Callable[[ToneMatchStatement], None]] = None,
    ) -> None:
        self._pitch_detector = pitch_detector
        self._config = config or AudioWorkerConfig()

        self._on_pitch_update = on_pitch_update
        self._on_note_matched = on_note_matched

        self._lock = threading.Lock()
        self._running_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()

        self._worker_thread: Optional[threading.Thread] = None

        self._target_note: Optional[TargetNote] = None
        self._match_state: MatchState = MatchState.SEARCHING
        self._hold_start_time: Optional[float] = None
        self._target_set_timestamp: float = time.monotonic()
        self._lockout_until_timestamp: float = 0.0

    def set_input_device(self, device_id: Optional[int | str]) -> None:
        """Forward microphone selection to pitch detector."""
        if hasattr(self._pitch_detector, "set_device"):
            self._pitch_detector.set_device(device_id)

    def set_target_note(self, note_name: str, octave: Optional[int] = None) -> None:
        """Dynamically updates the active target pitch[cite: 1]."""
        new_target = TargetNote(note_name=note_name, octave=octave)
        with self._lock:
            self._target_note = new_target
            self._reset_match_state_locked()

    def set_target_note_by_string_fret(self, string_num: int, fret_num: int) -> None:
        """Helper to set target note according to guitar standard tuning string number and fret offset[cite: 1]."""
        if string_num not in GUITAR_STRINGS:
            raise ValueError(f"Invalid string number {string_num}.")
        if fret_num < 0:
            raise ValueError("Fret number cannot be negative.")

        base_note, base_octave = GUITAR_STRINGS[string_num]
        base_index = CHROMATIC_NOTES.index(base_note)

        total_semitones = base_index + fret_num
        target_note_name = CHROMATIC_NOTES[total_semitones % 12]
        target_octave = base_octave + (total_semitones // 12)

        self.set_target_note(note_name=target_note_name, octave=target_octave)

    def set_callbacks(
        self,
        on_pitch_update: Optional[Callable[[PitchData], None]] = None,
        on_note_matched: Optional[Callable[[ToneMatchStatement], None]] = None,
    ) -> None:
        """Rebind callback functions dynamically[cite: 1]."""
        with self._lock:
            if on_pitch_update is not None:
                self._on_pitch_update = on_pitch_update
            if on_note_matched is not None:
                self._on_note_matched = on_note_matched

    def update_config(self, config: AudioWorkerConfig) -> None:
        """Update algorithm configuration parameters[cite: 1]."""
        with self._lock:
            self._config = config

    def start(self) -> None:
        """Starts the audio processing background daemon thread[cite: 1]."""
        with self._lock:
            if self._running_event.is_set():
                return
            self._running_event.set()
            self._pause_event.set()
            self._worker_thread = threading.Thread(
                target=self._audio_processing_loop,
                name="AudioWorkerDaemonThread",
                daemon=True,
            )
            self._worker_thread.start()

    def pause(self) -> None:
        """Pauses processing loop without terminating background thread[cite: 1]."""
        self._pause_event.clear()

    def resume(self) -> None:
        """Resumes paused background worker thread[cite: 1]."""
        self._pause_event.set()

    def stop(self) -> None:
        """Gracefully halts background worker thread and releases audio stream[cite: 1]."""
        with self._lock:
            if not self._running_event.is_set():
                return
            self._running_event.clear()
            self._pause_event.set()

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

    @property
    def is_running(self) -> bool:
        return self._running_event.is_set()

    @property
    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def _reset_match_state_locked(self) -> None:
        """Reset match tracking timers[cite: 1]."""
        self._match_state = MatchState.SEARCHING
        self._hold_start_time = None
        self._lockout_until_timestamp = 0.0
        self._target_set_timestamp = time.monotonic()

    def _audio_processing_loop(self) -> None:
        """Main execution loop executed inside the background daemon thread[cite: 1]."""
        while self._running_event.is_set():
            self._pause_event.wait()
            if not self._running_event.is_set():
                break

            frame = self._fetch_pitch_frame()
            if frame is None:
                time.sleep(0.01)
                continue

            pitch_data, statement = self._evaluate_frame(frame)

            if pitch_data and self._on_pitch_update:
                try:
                    self._on_pitch_update(pitch_data)
                except Exception as err:
                    sys.stderr.write(f"[AudioWorker] Update callback error: {err}\n")

            if statement and statement.is_correct and self._on_note_matched:
                try:
                    self._on_note_matched(statement)
                except Exception as err:
                    sys.stderr.write(f"[AudioWorker] Match callback error: {err}\n")

    def _fetch_pitch_frame(self) -> Optional[dict[str, Any]]:
        """Wraps pitch detector polling safely[cite: 1]."""
        try:
            if hasattr(self._pitch_detector, "get_latest"):
                pdata = self._pitch_detector.get_latest(block=False)
                if pdata:
                    return {
                        "frequency": pdata.frequency,
                        "cents": pdata.cents,
                        "volume": pdata.db_level,
                        "note": pdata.note_name,
                        "octave": pdata.octave,
                    }
            elif hasattr(self._pitch_detector, "read_frame"):
                return self._pitch_detector.read_frame()
            return None
        except Exception as err:
            sys.stderr.write(f"[AudioWorker] Error fetching audio frame: {err}\n")
            return None

    def _evaluate_frame(
        self, raw_frame: dict[str, Any]
    ) -> Tuple[Optional[PitchData], Optional[ToneMatchStatement]]:
        """Core Match Logic & Debouncing State Machine[cite: 1]."""
        now = time.monotonic()
        match_statement = None

        with self._lock:
            target = self._target_note
            config = self._config

            freq = float(raw_frame.get("frequency", 0.0))
            cents = float(raw_frame.get("cents", 0.0))
            vol = float(raw_frame.get("volume", -100.0))
            detected_note = str(raw_frame.get("note", "N/A")).upper()
            octave = int(raw_frame.get("octave", 0))
            raw_str = f"{detected_note}{octave}" if octave > 0 else detected_note

            is_above_noise = vol >= config.min_volume_db
            is_note_match = False
            if target is not None:
                name_match = (detected_note == target.note_name)
                octave_match = (not config.require_octave_match) or (octave == target.octave)
                is_note_match = name_match and octave_match

            is_cents_in_tune = abs(cents) <= config.tolerance_cents
            is_frame_valid = is_above_noise and is_note_match and is_cents_in_tune

            if now >= self._lockout_until_timestamp:
                if is_frame_valid:
                    if self._hold_start_time is None:
                        self._hold_start_time = now
                        self._match_state = MatchState.HOLDING

                    hold_duration = now - self._hold_start_time
                    if hold_duration >= config.hold_duration_sec:
                        elapsed_match_time = now - self._target_set_timestamp
                        self._lockout_until_timestamp = now + config.lockout_duration_sec
                        self._match_state = MatchState.LOCKED_OUT
                        self._hold_start_time = None

                        match_statement = ToneMatchStatement(
                            is_correct=True,
                            status="MATCH_CONFIRMED",
                            target_note=target.display_name if target else "N/A",
                            detected_note=raw_str,
                            cents_error=cents,
                            frequency_hz=freq,
                            volume_db=vol,
                            elapsed_seconds=elapsed_match_time,
                        )
                else:
                    self._hold_start_time = None
                    self._match_state = MatchState.SEARCHING

            pitch_data = PitchData(
                frequency=freq,
                cents=cents,
                volume_db=vol,
                detected_note=detected_note,
                octave=octave,
                is_in_tune=is_frame_valid,
                raw_pitch_str=raw_str,
            )

            return pitch_data, match_statement
