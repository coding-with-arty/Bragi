# tests/test_system_integration.py
"""
Bragi System Integration Verification Test
==========================================
Verifies schema integrity, data model validation, chord generation,
and progress logging across all core subsystems.
"""

import sys
from pathlib import Path

# Resolve project root from tests directory
project_root = Path(__file__).resolve().parent.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from models.audio_frame import AudioFrame
from models.chord import PitchClass, ChordQuality, ChordDefinition, TargetChord, CAGEDPosition
from models.ear_training import EarTrainingCategory, EarTrainingDifficulty, EarTrainingQuestion
from models.instrument import StringConfig, InstrumentProfile
from models.progress import AttemptRecord, UserProfile
from models.settings import TrainerSettings, DetectionMode, ValidationMode
from storage.progress_repository import ProgressRepository
from storage.instrument_store import InstrumentStore
from storage.settings_store import SettingsStore
from engine.chord_generator import ChordGenerator
from utils.music_theory import MusicTheory


def run_diagnostics():
    print("=" * 65)
    print("🚀 RUNNING BRAGI SYSTEM INTEGRATION DIAGNOSTIC SUITE")
    print("=" * 65)

    # 1. Verify AudioFrame model compatibility
    frame = AudioFrame(frequency=440.0, pitch_class="A", octave=4, cents_deviation=2.5, rms_db=-20.0, is_silent=False)
    assert frame.cents == 2.5, "AudioFrame cents property failed"
    assert frame.db_level == -20.0, "AudioFrame db_level property failed"
    assert frame.note_name == "A", "AudioFrame note_name property failed"
    assert frame.get("cents") == 2.5, "AudioFrame dictionary compatibility failed"
    print("✅ [1/6] AudioFrame Data Model & Compatibility: PASSED")

    # 2. Verify Chord Models & Music Theory Utilities
    root_pc = MusicTheory.note_to_pitch_class("C")
    assert root_pc == 0, f"Expected 0 for C, got {root_pc}"

    chord_def = ChordDefinition(
        name="C Major",
        root_note="C",
        quality=ChordQuality.MAJOR,
        pitch_classes={0, 4, 7},
        formula_intervals=["1", "3", "5"],
    )
    target_chord = TargetChord(chord_definition=chord_def, required_caged_position=CAGEDPosition.OPEN)
    assert target_chord.display_title == "C Major (Open Position)", "TargetChord display title mismatch"
    print("✅ [2/6] Chord Schemas & Music Theory Utilities: PASSED")

    # 3. Verify Instrument Profiles & Tuning Computations
    profile = InstrumentProfile(
        id="test_guitar",
        name="Test 6-String",
        category="Guitar",
        string_count=6,
        tuning=[
            StringConfig(string_num=1, note_name="E", octave=4),
            StringConfig(string_num=2, note_name="B", octave=3),
            StringConfig(string_num=3, note_name="G", octave=3),
            StringConfig(string_num=4, note_name="D", octave=3),
            StringConfig(string_num=5, note_name="A", octave=2),
            StringConfig(string_num=6, note_name="E", octave=2),
        ],
    )
    tuning_tuples = profile.to_tuning_tuples()
    assert len(tuning_tuples) == 6, "InstrumentProfile tuning tuple conversion failed"
    assert tuning_tuples[0] == ("E", 4), "String 1 should be High E (E4)"
    print("✅ [3/6] Instrument Profiles & String Configurations: PASSED")

    # 4. Verify Settings & SettingsStore Persistence
    settings = TrainerSettings(
        detection_mode=DetectionMode.NOTE_DETECTION,
        validation_mode=ValidationMode.ARPEGGIO_SEQUENCE,
    )
    settings_store = SettingsStore()
    settings_store.save_settings(settings)
    loaded_settings = settings_store.load_settings()
    assert loaded_settings.detection_mode == DetectionMode.NOTE_DETECTION, "SettingsStore load/save mismatch"
    print("✅ [4/6] Settings Store & Application State: PASSED")

    # 5. Verify Chord Generator Defensiveness
    generated_target = ChordGenerator.generate_target(settings.chord_filters)
    assert generated_target.chord_definition is not None, "ChordGenerator produced invalid target"
    print(f"   ➔ Generated Random Target: {generated_target.chord_definition.name}")
    print("✅ [5/6] Chord Generator Defensive Unpacking: PASSED")

    # 6. Verify ProgressRepository & Gamification Logging
    repo = ProgressRepository()
    attempt = AttemptRecord(
        target_name="C",
        target_type="note",
        is_success=True,
        response_time_sec=1.2,
        cents_error=1.0,
        timestamp=1000000.0,
    )
    reward1 = repo.log_attempt(attempt)
    reward2 = repo.log_attempt("G", is_correct=True, response_time_sec=0.9)

    stats = repo.get_user_stats()
    assert stats["total_attempts"] >= 2, "ProgressRepository attempt logging failed"
    print(f"   ➔ Active User: {stats.get('username', 'Default')} | XP: {stats['total_xp']} | Level: {stats['current_level']}")
    print("✅ [6/6] Progress Repository & Multi-User Analytics: PASSED")

    print("=" * 65)
    print("🎉 ALL SYSTEM DIAGNOSTICS PASSED PERFECTLY!")
    print("=" * 65)


if __name__ == "__main__":
    run_diagnostics()
