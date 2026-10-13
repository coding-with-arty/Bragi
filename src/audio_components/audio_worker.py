"""
audio_worker.py - Thread-Safe Background Audio Engine for Flet UI Applications.

This module provides an asynchronous, thread-safe background audio processing worker
that interfaces between low-level pitch detection algorithms (e.g., PitchDetector)
and event-driven UI frameworks such as Flet, PyQt, or Tkinter.

Architecture & Concurrency Design:
    - Daemon Listener Thread: Audio processing runs continuously on an isolated background thread.
    - Thread-Safe Shared State: Lock-protected mutations ensure UI-driven updates do not race with audio loops.
    - Non-Blocking Callbacks: Event callbacks are invoked OUTSIDE state locks to eliminate UI/worker deadlocks.
    - State Machine & Debounce: Built-in noise filtering, pitch tolerance windows, hold-time debouncing,
      and post-match lockout cooldowns prevent false positives and rapid re-triggering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
import math
import random
import sys
import threading
import time
from typing import Callable, Optional, Tuple, Any

# ============================================================================
# Constants & Musical Mappings
# ============================================================================

CHROMATIC_NOTES: list[str] = [
    "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
]

# Standard Guitar Tuning (String Number -> (Base Note, Base Octave))
# String 6: E2 (Lowest pitch), String 1: E4 (Highest pitch)
GUITAR_STRINGS: dict[int, Tuple[str, int]] = {
    6: ("E", 2),
    5: ("A", 2),
    4: ("D", 3),
    3: ("G", 3),
    2: ("B", 3),
    1: ("E", 4),
}


class MatchState(Enum):
    """Internal state tracking for pitch matching debouncer."""
    SEARCHING = auto()  # Listening for target pitch
    HOLDING = auto()    # Pitch matched; holding to satisfy debounce duration
    LOCKED_OUT = auto() # Match confirmed; cooling down before accepting new triggers


# ============================================================================
# Data Structures
# ============================================================================

@dataclass(frozen=True, slots=True)
class TargetNote:
    """Represents a target note to be matched by the audio worker."""
    note_name: str
    octave: Optional[int] = None

    def __post_init__(self) -> None:
        formatted = self.note_name.strip().upper()
        if formatted not in CHROMATIC_NOTES:
            raise ValueError(f"Invalid note name '{self.note_name}'. Must be one of {CHROMATIC_NOTES}")
        object.__setattr__(self, 'note_name', formatted)

    @property
    def display_name(self) -> str:
        """Returns string representation (e.g., 'A2' or 'A')."""
        return f"{self.note_name}{self.octave}" if self.octave is not None else self.note_name


@dataclass(frozen=True, slots=True)
class PitchData:
    """Immutable real-time payload dispatched on every audio processing frame."""
    frequency: float        # Hz
    cents: float            # Deviation from nearest note (-50.0 to +50.0)
    volume_db: float        # Signal strength in dB or RMS
    detected_note: str      # E.g., "A", "C#"
    octave: int             # Pitch octave number
    is_in_tune: bool        # True if pitch meets current target match criteria
    raw_pitch_str: str      # Combined string representation (e.g., "A2")


@dataclass
class AudioWorkerConfig:
    """Configurable thresholds for audio engine matching and debouncing logic."""
    tolerance_cents: float = 25.0       # Max pitch deviation in cents (+/-)
    min_volume_db: float = -45.0        # Minimum signal floor to consider valid pitch
    hold_duration_sec: float = 0.30     # Required continuous match duration (300 ms debounce)
    lockout_duration_sec: float = 0.50  # Cooldown lockout post-hit (500 ms)
    require_octave_match: bool = True   # If True, octave must match TargetNote.octave


# ============================================================================
# Thread-Safe Audio Worker Engine
# ============================================================================

class AudioWorker:
    """
    Thread-safe background audio manager wrapper.

    Continuously monitors microphone streams using `PitchDetector`, evaluates incoming audio
    against configurable pitch targets and noise thresholds, and safely dispatches events to
    UI event loops (such as Flet).
    """

    def __init__(
        self,
        pitch_detector: Any,
        config: Optional[AudioWorkerConfig] = None,
        on_pitch_update: Optional[Callable[[PitchData], None]] = None,
        on_note_matched: Optional[Callable[[TargetNote, float], None]] = None,
    ) -> None:
        """
        Initialize the AudioWorker instance.

        :param pitch_detector: Instance of PitchDetector providing `read_frame()` or pitch callback.
        :param config: Matching parameters and noise floor configuration.
        :param on_pitch_update: UI callback triggered on every frame. Signature: (data: PitchData) -> None.
        :param on_note_matched: UI callback triggered ONCE when target note is hit. Signature: (target: TargetNote, elapsed_sec: float) -> None.
        """
        self._pitch_detector = pitch_detector
        self._config = config or AudioWorkerConfig()

        # Callbacks (Protected by _lock for assignment)
        self._on_pitch_update = on_pitch_update
        self._on_note_matched = on_note_matched

        # Synchronization Primitives
        self._lock = threading.Lock()
        self._running_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Default: Not paused

        # Thread reference
        self._worker_thread: Optional[threading.Thread] = None

        # Protected Engine State Variables
        self._target_note: Optional[TargetNote] = None
        self._match_state: MatchState = MatchState.SEARCHING
        self._hold_start_time: Optional[float] = None
        self._target_set_timestamp: float = time.monotonic()
        self._lockout_until_timestamp: float = 0.0

    # ------------------------------------------------------------------------
    # Public Thread-Safe API
    # ------------------------------------------------------------------------

    def set_target_note(self, note_name: str, octave: Optional[int] = None) -> None:
        """
        # THREAD-SAFE
        Dynamically updates the active target pitch. Resets current match timers and lockout states.
        """
        new_target = TargetNote(note_name=note_name, octave=octave)
        with self._lock:
            self._target_note = new_target
            self._reset_match_state_locked()

    def set_target_note_by_string_fret(self, string_num: int, fret_num: int) -> None:
        """
        # THREAD-SAFE
        Helper to set target note according to guitar standard tuning string number and fret offset.

        :param string_num: Guitar string (1 to 6).
        :param fret_num: Fret index (0 = open string).
        """
        if string_num not in GUITAR_STRINGS:
            raise ValueError(f"Invalid string number {string_num}. Expected 1-6.")
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
        on_note_matched: Optional[Callable[[TargetNote, float], None]] = None,
    ) -> None:
        """# THREAD-SAFE: Rebind callback functions dynamically."""
        with self._lock:
            if on_pitch_update is not None:
                self._on_pitch_update = on_pitch_update
            if on_note_matched is not None:
                self._on_note_matched = on_note_matched

    def update_config(self, config: AudioWorkerConfig) -> None:
        """# THREAD-SAFE: Update algorithm configuration parameters."""
        with self._lock:
            self._config = config

    def start(self) -> None:
        """# THREAD-SAFE: Starts the audio processing background daemon thread."""
        with self._lock:
            if self._running_event.is_set():
                return  # Already running

            self._running_event.set()
            self._pause_event.set()
            self._worker_thread = threading.Thread(
                target=self._audio_processing_loop,
                name="AudioWorkerDaemonThread",
                daemon=True,
            )
            self._worker_thread.start()

    def pause(self) -> None:
        """# THREAD-SAFE: Pauses processing loop without terminating the background thread."""
        self._pause_event.clear()

    def resume(self) -> None:
        """# THREAD-SAFE: Resumes a paused background worker thread."""
        self._pause_event.set()

    def stop(self) -> None:
        """# THREAD-SAFE: Gracefully halts background worker thread and releases audio stream."""
        with self._lock:
            if not self._running_event.is_set():
                return
            self._running_event.clear()
            self._pause_event.set()  # Unblock thread if paused

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

    @property
    def is_running(self) -> bool:
        """# THREAD-SAFE: Returns True if the daemon thread is alive and running."""
        return self._running_event.is_set()

    @property
    def is_paused(self) -> bool:
        """# THREAD-SAFE: Returns True if worker processing is currently paused."""
        return not self._pause_event.is_set()

    # ------------------------------------------------------------------------
    # Internal Engine Methods
    # ------------------------------------------------------------------------

    def _reset_match_state_locked(self) -> None:
        """Reset match tracking timers. MUST BE CALLED UNDER `_lock`."""
        self._match_state = MatchState.SEARCHING
        self._hold_start_time = None
        self._lockout_until_timestamp = 0.0
        self._target_set_timestamp = time.monotonic()

    def _audio_processing_loop(self) -> None:
        """
        Main execution loop executed inside the background daemon thread.
        Retrieves raw audio analysis frames, processes state logic, and emits UI events.
        """
        while self._running_event.is_set():
            # Wait if paused
            self._pause_event.wait()
            if not self._running_event.is_set():
                break

            # Fetch frame from pitch detector
            frame = self._fetch_pitch_frame()
            if frame is None:
                time.sleep(0.01)  # Throttle fallback if stream yields no data
                continue

            # Process state machine & criteria
            pitch_data, match_triggered, target, elapsed = self._evaluate_frame(frame)

            # Safely invoke callbacks OUTSIDE lock to prevent UI deadlocks
            if pitch_data and self._on_pitch_update:
                try:
                    self._on_pitch_update(pitch_data)
                except Exception as err:
                    sys.stderr.write(f"[AudioWorker] Exception in on_pitch_update callback: {err}\n")

            if match_triggered and target and self._on_note_matched:
                try:
                    self._on_note_matched(target, elapsed)
                except Exception as err:
                    sys.stderr.write(f"[AudioWorker] Exception in on_note_matched callback: {err}\n")

    def _fetch_pitch_frame(self) -> Optional[dict[str, Any]]:
        """Wraps pitch detector polling safely."""
        try:
            if hasattr(self._pitch_detector, "read_frame"):
                return self._pitch_detector.read_frame()
            elif hasattr(self._pitch_detector, "get_pitch"):
                return self._pitch_detector.get_pitch()
            return None
        except Exception as err:
            sys.stderr.write(f"[AudioWorker] Error reading audio stream frame: {err}\n")
            return None

    def _evaluate_frame(
        self, raw_frame: dict[str, Any]
    ) -> Tuple[Optional[PitchData], bool, Optional[TargetNote], float]:
        """
        Core Match Logic & Debouncing State Machine.

        Evaluates incoming pitch data against current target note criteria,
        noise floors, tolerance thresholds, continuous hold duration, and lockout states.
        """
        now = time.monotonic()
        match_triggered = False
        elapsed_match_time = 0.0

        with self._lock:
            target = self._target_note
            config = self._config

            freq = float(raw_frame.get("frequency", 0.0))
            cents = float(raw_frame.get("cents", 0.0))
            vol = float(raw_frame.get("volume", -100.0))
            detected_note = str(raw_frame.get("note", "N/A")).upper()
            octave = int(raw_frame.get("octave", 0))
            raw_str = f"{detected_note}{octave}" if octave > 0 else detected_note

            # Step 1: Check noise floor
            is_above_noise = vol >= config.min_volume_db

            # Step 2: Check target note name & octave match
            is_note_match = False
            if target is not None:
                name_match = (detected_note == target.note_name)
                octave_match = (not config.require_octave_match) or (octave == target.octave)
                is_note_match = name_match and octave_match

            # Step 3: Check pitch accuracy tolerance
            is_cents_in_tune = abs(cents) <= config.tolerance_cents

            # Composite pitch validity
            is_frame_valid = is_above_noise and is_note_match and is_cents_in_tune

            # Step 4: Lockout state management
            if now < self._lockout_until_timestamp:
                self._match_state = MatchState.LOCKED_OUT
                self._hold_start_time = None
            else:
                # Debounce Hold logic
                if is_frame_valid:
                    if self._hold_start_time is None:
                        self._hold_start_time = now
                        self._match_state = MatchState.HOLDING

                    hold_duration = now - self._hold_start_time

                    # Hit confirmation threshold met!
                    if hold_duration >= config.hold_duration_sec:
                        match_triggered = True
                        elapsed_match_time = now - self._target_set_timestamp
                        self._lockout_until_timestamp = now + config.lockout_duration_sec
                        self._match_state = MatchState.LOCKED_OUT
                        self._hold_start_time = None
                else:
                    # Pitch criteria lost -> reset debounce timer
                    self._hold_start_time = None
                    self._match_state = MatchState.SEARCHING

            # Construct immutable PitchData event payload
            pitch_data = PitchData(
                frequency=freq,
                cents=cents,
                volume_db=vol,
                detected_note=detected_note,
                octave=octave,
                is_in_tune=is_frame_valid,
                raw_pitch_str=raw_str,
            )

            return pitch_data, match_triggered, target, elapsed_match_time


# ============================================================================
# Interactive CLI Test Runner & Mock Stream Simulator
# ============================================================================

class MockPitchDetector:
    """Simulates realistic microphone input and pitch detection for testing."""

    def __init__(self) -> None:
        self.current_freq: float = 110.0  # Default A2
        self.current_cents: float = 0.0
        self.current_vol: float = -20.0
        self.current_note: str = "A"
        self.current_octave: int = 2

    def simulate_pitch(self, note: str, octave: int, cents: float = 0.0, vol: float = -20.0) -> None:
        self.current_note = note
        self.current_octave = octave
        self.current_cents = cents
        self.current_vol = vol

    def read_frame(self) -> dict[str, Any]:
        time.sleep(0.05)  # Simulate 20 Hz frame rate (50 ms chunks)
        # Add subtle natural micro-jitter
        jitter = random.uniform(-1.5, 1.5)
        return {
            "frequency": 110.0,
            "cents": self.current_cents + jitter,
            "volume": self.current_vol,
            "note": self.current_note,
            "octave": self.current_octave,
        }


if __name__ == "__main__":
    print("=" * 70)
    print("      AUDIO WORKER MODULE - INTERACTIVE STANDALONE TEST RUNNER      ")
    print("=" * 70)

    # Initialize Mock Pitch Detector and Audio Worker
    mock_detector = MockPitchDetector()

    # Matching config: 25 cents tolerance, 300ms hold debounce, 500ms lockout
    worker_config = AudioWorkerConfig(
        tolerance_cents=25.0,
        min_volume_db=-40.0,
        hold_duration_sec=0.30,
        lockout_duration_sec=0.50,
        require_octave_match=True,
    )

    matched_event_signal = threading.Event()
    last_matched_target: list[str] = []

    def on_pitch_update_callback(data: PitchData) -> None:
        tune_status = "IN TUNE" if data.is_in_tune else "OFF TARGET"
        sys.stdout.write(
            f"\r[AUDIO MON] Live: {data.raw_pitch_str:<3} | Cents: {data.cents:+5.1f} | "
            f"Vol: {data.volume_db:5.1f} dB | Status: {tune_status:<10}"
        )
        sys.stdout.flush()

    def on_note_matched_callback(target: TargetNote, elapsed_sec: float) -> None:
        print(f"\n\n{'*'*50}")
        print(f" SUCCESS: Target Matched! [{target.display_name}] in {elapsed_sec:.2f} seconds!")
        print(f"{'*'*50}\n")
        last_matched_target.append(target.display_name)
        matched_event_signal.set()

    # Create Worker
    worker = AudioWorker(
        pitch_detector=mock_detector,
        config=worker_config,
        on_pitch_update=on_pitch_update_callback,
        on_note_matched=on_note_matched_callback,
    )

    # Start Background Daemon
    worker.start()

    # Target Playlist for simulation loop
    targets_to_test = [
        ("String 6 Open (E2)", 6, 0),
        ("String 5 Open (A2)", 5, 0),
        ("String 5 Fret 3 (C3)", 5, 3),
        ("String 1 Fret 5 (A4)", 1, 5),
    ]

    try:
        for desc, string_num, fret_num in targets_to_test:
            matched_event_signal.clear()

            # Dynamically set target note via string/fret helper
            worker.set_target_note_by_string_fret(string_num, fret_num)

            # Read current set target back safely
            with worker._lock:
                target_str = worker._target_note.display_name if worker._target_note else "N/A"

            print(f"\n---> NEW TARGET ASSIGNED: {desc} -> Target Note: '{target_str}'")

            # Phase 1: Simulate wrong note input for 0.5s
            mock_detector.simulate_pitch(note="F", octave=2, cents=40.0)
            time.sleep(0.5)

            # Phase 2: Simulate target note with bad cents (out of tolerance) for 0.5s
            note_name = worker._target_note.note_name if worker._target_note else "E"
            octave_val = worker._target_note.octave if worker._target_note else 2
            mock_detector.simulate_pitch(note=note_name, octave=octave_val, cents=-35.0)
            time.sleep(0.5)

            # Phase 3: Simulate PERFECT target note (holds for 0.4s to trigger 0.3s debounce)
            print(f"\n>>> [Player playing correct note '{target_str}']...")
            mock_detector.simulate_pitch(note=note_name, octave=octave_val, cents=2.0)

            # Wait for event trigger
            success = matched_event_signal.wait(timeout=3.0)
            if not success:
                print("\n[TEST WARNING] Target match timed out.")

            time.sleep(0.2)

    finally:
        print("\nStopping AudioWorker background thread cleanly...")
        worker.stop()
        print("AudioWorker stopped. Test suite complete.")
