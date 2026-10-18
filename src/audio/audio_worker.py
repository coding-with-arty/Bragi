# src/audio/audio_worker.py
"""
Audio Processing Worker Thread
==============================
Executes background audio analysis, pitch matching, and arpeggiated chord evaluation loops.
"""

import threading
import time
from typing import Callable, Optional, Set, Dict

from models.settings import TrainerSettings, DetectionMode
from engine.note_evaluator import NoteEvaluator, EvaluatedPitchPayload, SingleNoteMatchStatement
from engine.chord_evaluator import ChordEvaluator, ChordEvaluationStatement
from services.audio_manager import AudioManager


class AudioWorker:
    """Background worker thread processing pitch evaluation payloads (~25-50 Hz)."""

    def __init__(
        self,
        pitch_detector: Optional[object] = None,
        settings: Optional[TrainerSettings] = None,
        on_pitch_update: Optional[Callable[[EvaluatedPitchPayload], None]] = None,
        on_note_matched: Optional[Callable[[SingleNoteMatchStatement], None]] = None,
        on_chord_matched: Optional[Callable[[ChordEvaluationStatement], None]] = None,
        on_chord_pitch_update: Optional[Callable[[Set[int], float], None]] = None,
    ):
        self.settings = settings or TrainerSettings()
        self.note_evaluator = NoteEvaluator()
        self.chord_evaluator = ChordEvaluator()

        self.on_pitch_update = on_pitch_update
        self.on_note_matched = on_note_matched
        self.on_chord_matched = on_chord_matched
        self.on_chord_pitch_update = on_chord_pitch_update

        # Sliding time-window accumulator for strummed/arpeggiated chord pitch classes
        self._chord_note_history: Dict[int, float] = {}

        self._is_running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self._thread = threading.Thread(target=self._processing_loop, name="AudioWorkerThread", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def reset_chord_history(self) -> None:
        """Clears accumulated chord pitches when changing target chords."""
        self._chord_note_history.clear()

    def update_settings(self, new_settings: TrainerSettings) -> None:
        self.settings = new_settings
        val_mode = getattr(new_settings, "validation_mode", None)
        if val_mode and hasattr(self.chord_evaluator, "set_validation_mode"):
            self.chord_evaluator.set_validation_mode(val_mode)

    def set_input_device(self, device_id: Optional[int]) -> None:
        am = AudioManager.get_instance()
        am.start_listening(device_id)

    def set_target_note(self, note_name: str, octave: int = 4) -> None:
        if hasattr(self.note_evaluator, "set_target_note"):
            self.note_evaluator.set_target_note(note_name, octave)

    def set_target_chord(self, chord: object) -> None:
        self.reset_chord_history()
        if hasattr(self.chord_evaluator, "set_target"):
            self.chord_evaluator.set_target(chord)

    def _processing_loop(self) -> None:
        while self._is_running:
            try:
                if self.settings.detection_mode == DetectionMode.NOTE_DETECTION:
                    self._process_note_mode()
                else:
                    self._process_chord_mode()
            except Exception as err:
                print(f"[AudioWorker] Frame processing error: {err}")

            time.sleep(0.03)

    def _process_note_mode(self) -> None:
        am = AudioManager.get_instance()
        state = getattr(am, "current_state", {})
        pdata = state.get("pitch_data", {})

        if isinstance(pdata, dict):
            freq = pdata.get("frequency", pdata.get("pitch", 0.0))
            vol_db = pdata.get("volume_db", state.get("volume_db", -80.0))
            is_silent = pdata.get("is_silent", state.get("is_silent", True))
            cents = pdata.get("cents", 0.0)
            note_name = pdata.get("note_name", "")
        else:
            freq = getattr(pdata, "frequency", getattr(pdata, "pitch", 0.0))
            vol_db = getattr(pdata, "volume_db", -80.0)
            is_silent = getattr(pdata, "is_silent", True)
            cents = getattr(pdata, "cents", 0.0)
            note_name = getattr(pdata, "note_name", "")

        target_note = getattr(self.note_evaluator, "target_note", "").strip().upper()
        detected_clean = note_name.strip().upper()
        detected_note_only = "".join([c for c in detected_clean if not c.isdigit()])

        is_note_match = (
            not is_silent
            and len(detected_note_only) > 0
            and (detected_note_only == target_note)
        )

        is_in_tune = is_note_match and (abs(cents) <= 30.0 or cents == 0.0)

        payload = EvaluatedPitchPayload(
            frequency_hz=freq,
            cents_deviation=cents,
            cents=cents,
            volume_db=vol_db,
            is_silent=is_silent,
            raw_pitch_str=note_name,
            is_in_tune=is_in_tune,
        )

        if self.on_pitch_update:
            self.on_pitch_update(payload)

        if is_in_tune and self.on_note_matched:
            statement = SingleNoteMatchStatement(
                is_correct=True,
                target_note=target_note,
                detected_note=note_name,
                cents_error=cents,
            )
            self.on_note_matched(statement)

    def _process_chord_mode(self) -> None:
        am = AudioManager.get_instance()
        state = getattr(am, "current_state", {})
        vol_db = state.get("volume_db", -80.0)
        pdata = state.get("pitch_data", {})

        if isinstance(pdata, dict):
            is_silent = pdata.get("is_silent", state.get("is_silent", True))
            vol_db = pdata.get("volume_db", vol_db)
            pc_val = pdata.get("pitch_class")
        else:
            is_silent = getattr(pdata, "is_silent", True)
            vol_db = getattr(pdata, "volume_db", vol_db)
            pc_val = getattr(pdata, "pitch_class", None)

        # In src/audio/audio_worker.py inside _process_chord_mode():

        now = time.time()
        audio_sets = getattr(self.settings, "audio_settings", None)
        # Increased window to 2.5s for arpeggiating 4-note 7th chords
        window_sec = getattr(audio_sets, "arpeggio_window_sec", 2.5) if audio_sets else 2.5

        # 1. Store non-silent pitches into history buffer
        if not is_silent and pc_val is not None and vol_db >= -50.0:
            self._chord_note_history[int(pc_val) % 12] = now

        # 2. Expire pitch classes outside the expanded arpeggio window
        expired = [pc for pc, ts in self._chord_note_history.items() if (now - ts) > window_sec]
        for pc in expired:
            del self._chord_note_history[pc]

        accumulated_pcs = set(self._chord_note_history.keys())

        # 3. Dispatch pitch badges update to UI
        if self.on_chord_pitch_update:
            self.on_chord_pitch_update(accumulated_pcs, vol_db)

        # 4. Evaluate accumulated pitch set against target chord
        if accumulated_pcs:
            is_valid, statement = self.chord_evaluator.evaluate_pitch_classes(accumulated_pcs, volume_db=vol_db)
            if is_valid and statement is not None and statement.is_correct:
                self.reset_chord_history()
                if self.on_chord_matched:
                    self.on_chord_matched(statement)
