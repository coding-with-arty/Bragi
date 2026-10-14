"""
src/engine/arpeggio_buffer.py
=============================
Thread-safe sliding time-window accumulator for tracking picked/arpeggiated pitch classes.
"""

import threading
import time
from typing import Set, List, Tuple


class ArpeggioBuffer:
    """Sliding-window buffer accumulating pitch classes over a specified time duration."""

    def __init__(self, window_duration_sec: float = 2.0) -> None:
        self.window_duration_sec = window_duration_sec
        self._lock = threading.Lock()
        # Storage format: List of (timestamp, pitch_class_int)
        self._buffer: List[Tuple[float, int]] = []

    def set_window_duration(self, seconds: float) -> None:
        """Dynamically adjusts the sliding window duration."""
        with self._lock:
            self.window_duration_sec = max(0.5, float(seconds))

    def add_pitch_class(self, pitch_class: int, timestamp: float = None) -> None:
        """
        Registers a detected pitch class (0..11) into the sliding memory buffer.
        """
        if not (0 <= pitch_class <= 11):
            return

        ts = timestamp if timestamp is not None else time.monotonic()
        with self._lock:
            self._buffer.append((ts, pitch_class))
            self._purge_expired_locked(ts)

    def get_active_pitch_classes(self, current_time: float = None) -> Set[int]:
        """
        Returns the set of unique pitch classes currently active within the sliding time window.
        """
        now = current_time if current_time is not None else time.monotonic()
        with self._lock:
            self._purge_expired_locked(now)
            return {pc for _, pc in self._buffer}

    def clear(self) -> None:
        """Empties the accumulator buffer."""
        with self._lock:
            self._buffer.clear()

    def _purge_expired_locked(self, now: float) -> None:
        """Internal helper removing pitch class observations outside the time window."""
        cutoff = now - self.window_duration_sec
        self._buffer = [(ts, pc) for ts, pc in self._buffer if ts >= cutoff]
