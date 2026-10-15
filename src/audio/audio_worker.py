"""
src/audio/audio_worker.py
=========================
Thread-safe background audio processing worker supporting Note and Chord modes.
"""

import sys
import threading
import time
from typing import Callable, Optional, Any, Dict, Set

from models.settings import TrainerSettings, DetectionMode, ValidationMode
from models.chord import TargetChord, ChordMatchStatement
from engine.note_evaluator import NoteEvaluator, SingleNoteMatchStatement, EvaluatedPitchPayload
from engine.chord_evaluator import ChordEvaluator
from engine.arpeggio_buffer import ArpeggioBuffer
from audio.chord_detector import ChordDetector


class AudioWorker:
    """Unified audio processing worker dispatching frames to note or chord evaluators."""

    def __init__(
        self,
        pitch_detector: Any,  # Monophonic PitchDetector (aubio YIN)
        settings: Optional[TrainerSettings] = None,
        on_pitch_update: Optional[Callable[[EvaluatedPitchPayload], None]] = None,
        on_note_matched: Optional[Callable[[SingleNoteMatchStatement], None]] = None,
        on_chord_matched: Optional[Callable[[ChordMatchStatement], None]] = None,
        on_chord_pitch_update: Optional[Callable[[Set[int], float], None]] = None,
    ) -> None:
        self._pitch_detector = pitch_detector
        self._settings = settings or TrainerSettings()

        self._on_pitch_update = on_pitch_update
        self._on_note_matched = on_note_matched
        self._on_chord_matched = on_chord_matched
        self._on_chord_pitch_update = on_chord_pitch_update

        # Domain Evaluators
        self.note_evaluator = NoteEvaluator(
            tolerance_cents=self._settings.audio_settings.tolerance_cents,
            min_volume_db=self._settings.audio_settings.min_volume_db,
            hold_duration_sec=self._settings.audio_settings.hold_duration_sec,
        )

        self.chord_evaluator = ChordEvaluator(
            hold_duration_sec=self._settings.audio_settings.hold_duration_sec,
            validation_mode=self._settings.validation_mode,
        )

        self.arpeggio_buffer = ArpeggioBuffer(
            window_duration_sec=self._settings.audio_settings.arpeggio_window_sec
        )

        self.chord_detector = ChordDetector(
            sample_rate=self._settings.audio_settings.sample_rate,
            silence_threshold_db=self._settings.audio_settings.min_volume_db
        )

        self._lock = threading.Lock()
        self._running_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()

        self._worker_thread: Optional[threading.Thread] = None

    def set_input_device(self, device_id: Optional[int]) -> None:
        """Updates hardware input device index."""
        if hasattr(self._pitch_detector, "set_device"):
            self._pitch_detector.set_device(device_id)

    def set_target_note(self, note_name: str, octave: Optional[int] = None) -> None:
        """Sets active target for single-note mode."""
        with self._lock:
            self.note_evaluator.set_target(note_name, octave)

    def set_target_chord(self, target_chord: TargetChord) -> None:
        """Sets active target for chord mode."""
        with self._lock:
            self.chord_evaluator.set_target(target_chord)
            self.arpeggio_buffer.clear()

    def update_settings(self, new_settings: TrainerSettings) -> None:
        """Dynamically applies updated configuration parameters."""
        with self._lock:
            self._settings = new_settings
            self.note_evaluator.tolerance_cents = new_settings.audio_settings.tolerance_cents
            self.note_evaluator.min_volume_db = new_settings.audio_settings.min_volume_db
            self.note_evaluator.hold_duration_sec = new_settings.audio_settings.hold_duration_sec

            self.chord_evaluator.hold_duration_sec = new_settings.audio_settings.hold_duration_sec
            self.chord_evaluator.set_validation_mode(new_settings.validation_mode)

            self.arpeggio_buffer.set_window_duration(new_settings.audio_settings.arpeggio_window_sec)
            self.chord_detector.silence_threshold_db = new_settings.audio_settings.min_volume_db

    def start(self) -> None:
        """Starts background worker thread."""
        with self._lock:
            if self._running_event.is_set():
                return
            self._running_event.set()
            self._pause_event.set()
            self._worker_thread = threading.Thread(
                target=self._processing_loop,
                name="AudioWorkerThread",
                daemon=True,
            )
            self._worker_thread.start()

    def stop(self) -> None:
        """Stops background worker thread."""
        with self._lock:
            if not self._running_event.is_set():
                return
            self._running_event.clear()
            self._pause_event.set()

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)

    def _processing_loop(self) -> None:
        """Background execution loop."""
        while self._running_event.is_set():
            self._pause_event.wait()
            if not self._running_event.is_set():
                break

            if self._settings.detection_mode == DetectionMode.NOTE_DETECTION:
                self._process_note_mode()
            else:
                self._process_chord_mode()

            time.sleep(0.01)

    def _process_note_mode(self) -> None:
        """Executes single-note processing step using monophonic pitch detector."""
        if not hasattr(self._pitch_detector, "get_latest"):
            return

        pdata = self._pitch_detector.get_latest(block=False)
        if pdata is None:
            return

        pitch_payload, match_statement = self.note_evaluator.evaluate_frame(
            frequency=pdata.frequency,
            cents=pdata.cents,
            volume_db=pdata.db_level,
            detected_note=pdata.note_name,
            octave=pdata.octave
        )

        if self._on_pitch_update:
            try:
                self._on_pitch_update(pitch_payload)
            except Exception as err:
                sys.stderr.write(f"[AudioWorker] Pitch update error: {err}\n")

        if match_statement and match_statement.is_correct and self._on_note_matched:
            try:
                self._on_note_matched(match_statement)
            except Exception as err:
                sys.stderr.write(f"[AudioWorker] Note match callback error: {err}\n")

    # src/audio/audio_worker.py
    def _process_chord_mode(self) -> None:
        if not hasattr(self._pitch_detector, "get_latest"):
            return

        pdata = self._pitch_detector.get_latest(block=False)
        if pdata is None or pdata.raw_signal is None:
            return

        vol_db = pdata.db_level
        min_vol = self._settings.audio_settings.min_volume_db

        detected_pcs: Set[int] = set()

        if self._settings.validation_mode == ValidationMode.ARPEGGIO_SEQUENCE:
            # Retain existing arpeggiator logic using the monophonic tracker
            if vol_db >= min_vol and pdata.note_name != "N/A":
                from utils.music_theory import NOTE_TO_PITCH_INDEX
                pc = NOTE_TO_PITCH_INDEX.get(pdata.note_name.upper())
                if pc is not None:
                    self.arpeggio_buffer.add_pitch_class(pc)
            detected_pcs = self.arpeggio_buffer.get_active_pitch_classes()
        else:
            # FIX: Use the polyphonic DSP engine for single-frame chord evaluation
            active_pcs, _, is_silent, _ = self.chord_detector.process_frame(pdata.raw_signal)
            if not is_silent and vol_db >= min_vol:
                detected_pcs = active_pcs

        if self._on_chord_pitch_update:
            try:
                self._on_chord_pitch_update(detected_pcs, vol_db)
            except Exception as err:
                sys.stderr.write(f"[AudioWorker] Chord pitch update error: {err}\n")

        is_valid, chord_statement = self.chord_evaluator.evaluate_pitch_classes(
            detected_pitch_classes=detected_pcs,
            volume_db=vol_db,
            min_volume_db=min_vol
        )

        if chord_statement and chord_statement.is_correct and self._on_chord_matched:
            try:
                self._on_chord_matched(chord_statement)
            except Exception as err:
                sys.stderr.write(f"[AudioWorker] Chord match callback error: {err}\n")
