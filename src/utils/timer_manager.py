"""
timer_manager.py - Robust Asyncio Practice Mode & Timer Manager for Flet

Designed for high-frequency UI updates (20+ FPS), thread/task safety, and
seamless integration with background audio analysis workers (e.g. pitch detection).
"""

from __future__ import annotations

import asyncio
import enum
import logging
import random
import sys
import time
from typing import Awaitable, Callable, Optional, Union

# Configure Module Logger
logger = logging.getLogger("fretboard_trainer.timer")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class TimerState(str, enum.Enum):
    """Lifecycle states for TrainerTimer."""
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"


class PracticeMode(str, enum.Enum):
    """
    Practice operational modes:
      - SPEED_FLASHCARD: Fixed countdown timer per note. Auto-advances on timeout.
      - TUNER_ADAPTIVE: Max time limit per note. Auto-advances early on pitch match or on timeout.
      - INFINITE_PRACTICE: Continuous stopwatch. Stays on note until correct pitch is detected.
    """
    SPEED_FLASHCARD = "SPEED_FLASHCARD"
    TUNER_ADAPTIVE = "TUNER_ADAPTIVE"
    INFINITE_PRACTICE = "INFINITE_PRACTICE"


# Type definitions for synchronous or asynchronous callbacks
TickCallback = Callable[[float, float, float], Union[None, Awaitable[None]]]
TimeoutCallback = Callable[[], Union[None, Awaitable[None]]]
CompleteCallback = Callable[[bool], Union[None, Awaitable[None]]]
NotePassedCallback = Callable[[], Union[None, Awaitable[None]]]


class TrainerTimer:
    """
    Non-blocking, high-precision timer manager for Flet event loops.

    Provides atomic control over practice sessions, smooth tick callbacks for UI progress
    meters, and safe cancellation guarantees to avoid race conditions.
    """

    def __init__(
        self,
        duration: float = 5.0,
        mode: PracticeMode = PracticeMode.SPEED_FLASHCARD,
        tick_interval: float = 0.05,
        on_tick: Optional[TickCallback] = None,
        on_timeout: Optional[TimeoutCallback] = None,
        on_complete: Optional[CompleteCallback] = None,
        on_note_passed: Optional[NotePassedCallback] = None,
    ) -> None:
        """
        Initialize the TrainerTimer.

        :param duration: Time limit in seconds for countdown modes.
        :param mode: Operational PracticeMode.
        :param tick_interval: Tick loop update frequency in seconds (default 0.05s = 20 Hz).
        :param on_tick: Callback (elapsed, remaining, progress [0.0..1.0]).
        :param on_timeout: Callback triggered when countdown hits 0s without pitch match.
        :param on_complete: Callback triggered when note session ends (success: bool).
        :param on_note_passed: Callback triggered when pitch match occurs before timeout.
        """
        self._duration: float = max(0.1, float(duration))
        self._mode: PracticeMode = mode
        self._tick_interval: float = max(0.01, float(tick_interval))
        self._state: TimerState = TimerState.STOPPED

        # Callbacks
        self.on_tick: Optional[TickCallback] = on_tick
        self.on_timeout: Optional[TimeoutCallback] = on_timeout
        self.on_complete: Optional[CompleteCallback] = on_complete
        self.on_note_passed: Optional[NotePassedCallback] = on_note_passed

        # Internal Time Tracking
        self._start_monotonic: float = 0.0
        self._accumulated_elapsed: float = 0.0

        # Async Task & Synchronization
        self._task: Optional[asyncio.Task] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def state(self) -> TimerState:
        """Current state of the timer machine."""
        return self._state

    @property
    def mode(self) -> PracticeMode:
        """Current active practice mode."""
        return self._mode

    @property
    def duration(self) -> float:
        """Configured target duration in seconds."""
        return self._duration

    @property
    def elapsed(self) -> float:
        """Calculates total active elapsed time in seconds."""
        if self._state == TimerState.RUNNING:
            return (time.monotonic() - self._start_monotonic) + self._accumulated_elapsed
        return self._accumulated_elapsed

    @property
    def remaining(self) -> float:
        """Calculates remaining time in seconds."""
        if self._mode == PracticeMode.INFINITE_PRACTICE:
            return float("inf")
        return max(0.0, self._duration - self.elapsed)

    @property
    def progress(self) -> float:
        """Calculates normalized progress from 0.0 to 1.0."""
        if self._mode == PracticeMode.INFINITE_PRACTICE or self._duration <= 0:
            return 0.0
        return min(1.0, max(0.0, self.elapsed / self._duration))

    def set_mode(self, mode: PracticeMode) -> None:
        """Update active practice mode."""
        self._mode = mode
        logger.debug("Timer mode set to: %s", mode.value)

    def set_duration(self, seconds: float) -> None:
        """Dynamically set timer target duration in seconds."""
        self._duration = max(0.1, float(seconds))

    def extend_time(self, seconds: float) -> None:
        """Add additional time to active timer session."""
        if seconds > 0:
            self._duration += seconds
            logger.debug("Timer extended by %.2fs. New duration: %.2fs", seconds, self._duration)

    async def start(self, duration: Optional[float] = None) -> None:
        """
        Start or restart the timer loop for a new target note.

        :param duration: Optional new duration override for this run.
        """
        async with self._lock:
            await self._stop_task_internal()

            if duration is not None:
                self.set_duration(duration)

            self._accumulated_elapsed = 0.0
            self._start_monotonic = time.monotonic()
            self._state = TimerState.RUNNING

            self._task = asyncio.create_task(self._run_loop(), name="TrainerTimer_Loop")
            logger.debug("Timer STARTED (Mode: %s, Duration: %.2fs)", self._mode.value, self._duration)

    async def pause(self) -> None:
        """Pause running timer without discarding progress."""
        async with self._lock:
            if self._state != TimerState.RUNNING:
                return

            self._accumulated_elapsed += time.monotonic() - self._start_monotonic
            self._state = TimerState.PAUSED
            await self._stop_task_internal()
            logger.debug("Timer PAUSED at elapsed: %.2fs", self._accumulated_elapsed)

    async def resume(self) -> None:
        """Resume timer from paused state."""
        async with self._lock:
            if self._state != TimerState.PAUSED:
                return

            self._start_monotonic = time.monotonic()
            self._state = TimerState.RUNNING
            self._task = asyncio.create_task(self._run_loop(), name="TrainerTimer_Loop")
            logger.debug("Timer RESUMED from elapsed: %.2fs", self._accumulated_elapsed)

    async def reset(self) -> None:
        """Reset timer to initial stopped state."""
        async with self._lock:
            await self._stop_task_internal()
            self._accumulated_elapsed = 0.0
            self._state = TimerState.STOPPED
            logger.debug("Timer RESET.")

    async def pass_note(self) -> bool:
        """
        Signal correct pitch detection from AudioWorker.

        Cancels active countdown, executes pass callbacks, and signals note completion.

        :return: True if match was accepted; False if timer was not active.
        """
        async with self._lock:
            if self._state not in (TimerState.RUNNING, TimerState.PAUSED):
                return False

            await self._stop_task_internal()
            self._state = TimerState.STOPPED
            logger.debug("Note PASSED successfully via Audio Worker signal.")

            await self._safe_invoke(self.on_note_passed)
            await self._safe_invoke(self.on_complete, True)
            return True

    async def _stop_task_internal(self) -> None:
        """Helper to safely cancel background ticker task without raising exceptions."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def _run_loop(self) -> None:
        """Internal high-frequency ticker task loop."""
        try:
            while self._state == TimerState.RUNNING:
                cur_elapsed = self.elapsed
                cur_remaining = self.remaining
                cur_progress = self.progress

                # Emit tick update to UI listeners
                await self._safe_invoke(self.on_tick, cur_elapsed, cur_remaining, cur_progress)

                # Check expiration for countdown modes
                if self._mode != PracticeMode.INFINITE_PRACTICE and cur_elapsed >= self._duration:
                    self._state = TimerState.EXPIRED
                    logger.debug("Timer EXPIRED after %.2fs", cur_elapsed)

                    # Final tick notification showing full expiration
                    await self._safe_invoke(self.on_tick, self._duration, 0.0, 1.0)
                    await self._safe_invoke(self.on_timeout)
                    await self._safe_invoke(self.on_complete, False)
                    break

                await asyncio.sleep(self._tick_interval)

        except asyncio.CancelledError:
            # Expected during explicit stop, pause, or note complete calls
            raise
        except Exception as err:
            logger.exception("Error encountered inside timer execution loop: %s", err)

    @staticmethod
    async def _safe_invoke(callback: Optional[Callable], *args, **kwargs) -> None:
        """Thread & coroutine-safe callback dispatcher."""
        if callback is None:
            return
        try:
            result = callback(*args, **kwargs)
            if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
                await result
        except Exception as err:
            logger.error("Exception in timer event handler '%s': %s", getattr(callback, '__name__', repr(callback)), err, exc_info=True)


# ============================================================================
# STANDALONE ASYNC TEST RUNNER & SIMULATOR
# ============================================================================

async def _simulated_audio_worker(timer: TrainerTimer, target_note: str, probability_of_hit: float = 0.75):
    """Simulates real-time microphone input from background AudioWorker."""
    simulated_delay = random.uniform(0.8, 4.2)
    await asyncio.sleep(simulated_delay)

    # Randomly decide whether student plays correct note or misses/struggles
    if random.random() < probability_of_hit:
        sys.stdout.write(f"\n   [AudioWorker] Pitch Matched! Detected '{target_note}' correctly.\n")
        sys.stdout.flush()
        await timer.pass_note()


def _render_terminal_bar(elapsed: float, remaining: float, progress: float, note: str, mode_name: str) -> None:
    """Renders visual terminal status bar for debugging."""
    bar_length = 25
    filled_length = int(round(bar_length * progress))
    bar = "█" * filled_length + "░" * (bar_length - filled_length)

    if remaining == float("inf"):
        rem_str = " ∞  "
    else:
        rem_str = f"{remaining:4.1f}s"

    sys.stdout.write(
        f"\r[{mode_name[:7]}] Note: {note:<3} | [{bar}] {progress * 100:5.1f}% | Elapsed: {elapsed:4.1f}s | Rem: {rem_str}"
    )
    sys.stdout.flush()


async def main():
    """Terminal harness simulating 5-note practice round across various modes."""
    print("=" * 80)
    print(" FRETBOARD TRAINER - TIMER & PRACTICE MODE MANAGER TEST HARNESS")
    print("=" * 80)

    practice_notes = ["C4", "G4", "D4", "A4", "E4"]
    test_modes = [
        (PracticeMode.SPEED_FLASHCARD, 3.0, "Speed Flashcard Mode (3.0s limit)"),
        (PracticeMode.TUNER_ADAPTIVE, 6.0, "Tuner Adaptive Mode (6.0s limit or audio trigger)"),
        (PracticeMode.INFINITE_PRACTICE, 0.0, "Infinite Practice Mode (Stopwatch, requires hit)"),
    ]

    for mode, duration, mode_desc in test_modes:
        print(f"\n---> Starting Session: {mode_desc}")
        print("-" * 80)

        current_note_idx = 0
        round_finished_event = asyncio.Event()

        # Define Event Callbacks
        def on_tick(elapsed: float, remaining: float, progress: float):
            note = practice_notes[current_note_idx]
            _render_terminal_bar(elapsed, remaining, progress, note, mode.name)

        def on_timeout():
            sys.stdout.write("\n   [Timer] TIMEOUT! Time expired before note match.")
            sys.stdout.flush()

        async def on_complete(success: bool):
            nonlocal current_note_idx
            status = "PASSED" if success else "FAILED"
            sys.stdout.write(f"\n   [Session Manager] Completed Note {practice_notes[current_note_idx]} -> Status: {status}\n")
            sys.stdout.flush()

            current_note_idx += 1
            if current_note_idx < len(practice_notes):
                # Auto-advance to next note
                await timer.start()
                if mode != PracticeMode.SPEED_FLASHCARD:
                    asyncio.create_task(_simulated_audio_worker(timer, practice_notes[current_note_idx]))
            else:
                round_finished_event.set()

        timer = TrainerTimer(
            duration=duration,
            mode=mode,
            tick_interval=0.05,
            on_tick=on_tick,
            on_timeout=on_timeout,
            on_complete=on_complete,
        )

        # Launch first note
        await timer.start()
        if mode != PracticeMode.SPEED_FLASHCARD:
            asyncio.create_task(_simulated_audio_worker(timer, practice_notes[current_note_idx]))

        # Wait until 5 notes are completed
        await round_finished_event.wait()
        await timer.reset()
        print(f"\n Finished Round: {mode.value}\n")

    print("=" * 80)
    print(" ALL PRACTICE SESSION TESTS COMPLETED SUCCESSFULLY.")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
