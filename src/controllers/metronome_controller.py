import threading
import time
from typing import Callable, Optional
from services.audio_synth import AudioSynth


class MetronomeController:
    """
    High-precision background metronome operating on a dedicated timing thread.
    Generates accented pulse clicks without blocking main event loops.
    """

    def __init__(
        self,
        bpm: int = 120,
        beats_per_measure: int = 4,
        on_tick: Optional[Callable[[int, bool], None]] = None,
    ):
        self.bpm = max(30, min(260, bpm))
        self.beats_per_measure = beats_per_measure
        self.on_tick = on_tick  # UI callback receiving (current_beat, is_accent)

        self.is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._synth = AudioSynth()

    def set_bpm(self, new_bpm: int) -> None:
        """Updates tempo bounded between 30 and 260 BPM."""
        self.bpm = max(30, min(260, new_bpm))

    def set_time_signature(self, beats_per_measure: int) -> None:
        """Sets measure beat division (e.g., 4 for 4/4, 3 for 3/4, 6 for 6/8)."""
        self.beats_per_measure = beats_per_measure

    def start(self) -> None:
        """Starts metronome thread if not already active."""
        if self.is_running:
            return

        self.is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops metronome thread."""
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.2)
        self._thread = None

    def toggle(self) -> bool:
        """Toggles active state and returns new running status."""
        if self.is_running:
            self.stop()
        else:
            self.start()
        return self.is_running

    def _run_loop(self) -> None:
        """Timing thread loop using monotonic clocks for low drift."""
        current_beat = 0

        while self.is_running:
            start_time = time.monotonic()
            seconds_per_beat = 60.0 / self.bpm

            is_accent = (current_beat == 0)

            # Synthesize beat tick audio
            if is_accent:
                self._synth.play_note_async(pitch_class=9, octave=5, duration_sec=0.08)  # High A5 tick
            else:
                self._synth.play_note_async(pitch_class=9, octave=4, duration_sec=0.05)  # Medium A4 tick

            if self.on_tick:
                try:
                    self.on_tick(current_beat + 1, is_accent)
                except Exception as err:
                    print(f"[MetronomeController] UI tick callback error: {err}")

            current_beat = (current_beat + 1) % self.beats_per_measure

            # Sleep remaining beat interval accounting for execution duration
            elapsed = time.monotonic() - start_time
            sleep_time = max(0.001, seconds_per_beat - elapsed)
            time.sleep(sleep_time)
