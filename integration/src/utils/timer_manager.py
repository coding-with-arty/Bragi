"""
timer_manager.py - Non-blocking asyncio timer manager[cite: 7].
"""

from __future__ import annotations

import asyncio
import enum
import logging
import time
from typing import Awaitable, Callable, Optional, Union

logger = logging.getLogger("fretboard_trainer.timer")


class TimerState(str, enum.Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"


class PracticeMode(str, enum.Enum):
    SPEED_FLASHCARD = "SPEED_FLASHCARD"
    TUNER_ADAPTIVE = "TUNER_ADAPTIVE"
    INFINITE_PRACTICE = "INFINITE_PRACTICE"


TickCallback = Callable[[float, float, float], Union[None, Awaitable[None]]]
TimeoutCallback = Callable[[], Union[None, Awaitable[None]]]
CompleteCallback = Callable[[bool], Union[None, Awaitable[None]]]
NotePassedCallback = Callable[[], Union[None, Awaitable[None]]]


class TrainerTimer:
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
        self._duration: float = max(0.1, float(duration))
        self._mode: PracticeMode = mode
        self._tick_interval: float = max(0.01, float(tick_interval))
        self._state: TimerState = TimerState.STOPPED

        self.on_tick: Optional[TickCallback] = on_tick
        self.on_timeout: Optional[TimeoutCallback] = on_timeout
        self.on_complete: Optional[CompleteCallback] = on_complete
        self.on_note_passed: Optional[NotePassedCallback] = on_note_passed

        self._start_monotonic: float = 0.0
        self._accumulated_elapsed: float = 0.0

        self._task: Optional[asyncio.Task] = None
        self._lock: asyncio.Lock = asyncio.Lock()

    @property
    def state(self) -> TimerState:
        return self._state

    @property
    def mode(self) -> PracticeMode:
        return self._mode

    @property
    def elapsed(self) -> float:
        if self._state == TimerState.RUNNING:
            return (time.monotonic() - self._start_monotonic) + self._accumulated_elapsed
        return self._accumulated_elapsed

    @property
    def remaining(self) -> float:
        if self._mode == PracticeMode.INFINITE_PRACTICE:
            return float("inf")
        return max(0.0, self._duration - self.elapsed)

    @property
    def progress(self) -> float:
        if self._mode == PracticeMode.INFINITE_PRACTICE or self._duration <= 0:
            return 0.0
        return min(1.0, max(0.0, self.elapsed / self._duration))

    def set_mode(self, mode: PracticeMode) -> None:
        self._mode = mode

    def set_duration(self, seconds: float) -> None:
        self._duration = max(0.1, float(seconds))

    async def start(self, duration: Optional[float] = None) -> None:
        async with self._lock:
            await self._stop_task_internal()

            if duration is not None:
                self.set_duration(duration)

            self._accumulated_elapsed = 0.0
            self._start_monotonic = time.monotonic()
            self._state = TimerState.RUNNING

            self._task = asyncio.create_task(self._run_loop(), name="TrainerTimer_Loop")

    async def reset(self) -> None:
        async with self._lock:
            await self._stop_task_internal()
            self._accumulated_elapsed = 0.0
            self._state = TimerState.STOPPED

    async def pass_note(self) -> bool:
        async with self._lock:
            if self._state not in (TimerState.RUNNING, TimerState.PAUSED):
                return False

            await self._stop_task_internal()
            self._state = TimerState.STOPPED

            await self._safe_invoke(self.on_note_passed)
            await self._safe_invoke(self.on_complete, True)
            return True

    async def _stop_task_internal(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def _run_loop(self) -> None:
        try:
            while self._state == TimerState.RUNNING:
                cur_elapsed = self.elapsed
                cur_remaining = self.remaining
                cur_progress = self.progress

                await self._safe_invoke(self.on_tick, cur_elapsed, cur_remaining, cur_progress)

                if self._mode != PracticeMode.INFINITE_PRACTICE and cur_elapsed >= self._duration:
                    self._state = TimerState.EXPIRED
                    await self._safe_invoke(self.on_tick, self._duration, 0.0, 1.0)
                    await self._safe_invoke(self.on_timeout)
                    await self._safe_invoke(self.on_complete, False)
                    break

                await asyncio.sleep(self._tick_interval)

        except asyncio.CancelledError:
            raise
        except Exception as err:
            logger.exception("Timer error: %s", err)

    @staticmethod
    async def _safe_invoke(callback: Optional[Callable], *args, **kwargs) -> None:
        if callback is None:
            return
        try:
            result = callback(*args, **kwargs)
            if asyncio.iscoroutine(result) or isinstance(result, Awaitable):
                await result
        except Exception as err:
            logger.error("Callback exception: %s", err)
