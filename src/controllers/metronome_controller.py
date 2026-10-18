# src/controllers/metronome_controller.py
"""
Metronome Controller
====================
Non-blocking tempo pulse controller for rhythmic practice.
Manages tempo (BPM), time signature, accent ticks, and beat callbacks.
"""

import threading
import time
from typing import Callable, Optional
from services.audio_synth import AudioSynth


class MetronomeController:
    """
    Thread-safe metronome controller running a precise background pulse loop.
    """

    def __init__(
        self,
        bpm: int = 120,
        time_signature_beats: int = 4,
        audio_synth: Optional[AudioSynth] = None,
        on_beat: Optional[Callable[[int, bool], None]] = None,
    ):
        self.bpm = max(30, min(260, bpm))
        self.time_signature_beats = max(1, min(12, time_signature_beats))
        self.audio_synth = audio_synth or AudioSynth()
        self.on_beat = on_beat  # Callback signature: (current_beat: int, is_accent: bool)

        self.is_running: bool = False
        self.current_beat: int = 1
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def set_bpm(self, new_bpm: int) -> None:
        """Updates the tempo in beats per minute (30-260 BPM)."""
        self.bpm = max(30, min(260, new_bpm))

    def set_time_signature(self, beats_per_measure: int) -> None:
        """Updates the measure beat count (e.g., 4 for 4/4, 3 for 3/4)."""
        self.time_signature_beats = max(1, min(12, beats_per_measure))
        if self.current_beat > self.time_signature_beats:
            self.current_beat = 1

    def start(self) -> None:
        """Starts the background metronome pulse thread."""
        if self.is_running:
            return

        self.is_running = True
        self._stop_event.clear()
        self.current_beat = 1

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the background metronome pulse thread."""
        self.is_running = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._thread = None

    def toggle(self) -> bool:
        """Toggles the metronome state on or off."""
        if self.is_running:
            self.stop()
        else:
            self.start()
        return self.is_running

    def _run_loop(self) -> None:
        """Background thread loop delivering steady metronome pulses."""
        while not self._stop_event.is_set():
            beat_interval_sec = 60.0 / float(self.bpm)
            is_accent = (self.current_beat == 1)

            # Trigger audio tick synthesization asynchronously
            if hasattr(self.audio_synth, "play_click"):
                try:
                    self.audio_synth.play_click(is_accent=is_accent)
                except Exception:
                    pass

            # Emit UI callback notification if registered
            if self.on_beat:
                try:
                    self.on_beat(self.current_beat, is_accent)
                except Exception:
                    pass

            # Calculate target wake time to avoid accumulation drift
            wake_time = time.time() + beat_interval_sec

            # Advance beat counter for next tick
            self.current_beat = (self.current_beat % self.time_signature_beats) + 1

            # Sleep in small sub-intervals to permit rapid thread cancellation
            while time.time() < wake_time and not self._stop_event.is_set():
                remaining = wake_time - time.time()
                time.sleep(min(0.01, max(0.001, remaining)))
