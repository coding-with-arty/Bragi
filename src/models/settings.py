# src/models/settings.py
from enum import Enum
from typing import Set, Optional
from pydantic import BaseModel, Field, ConfigDict
from models.chord import ChordQuality, CAGEDPosition


class DetectionMode(str, Enum):
    """Primary operational mode of the audio trainer."""
    NOTE_DETECTION = "Note Detection"
    CHORD_DETECTION = "Chord Detection"


class PracticeMode(str, Enum):
    """Practice workflow modes."""
    SPEED_FLASHCARD = "Speed Flashcard"
    TUNER_ADAPTIVE = "Adaptive Tuner"
    INFINITE_PRACTICE = "Infinite Practice"
    EAR_TRAINING = "Ear Training"
    POSITION_CHALLENGE = "Position Challenge"


class ValidationMode(str, Enum):
    """Chord matching stringency levels."""
    RELAXED_PITCH_CLASS = "Relaxed Pitch Class"  # Any matching set of pitch classes
    STRICT_VOICING = "Strict Voicing"            # Must match exact fretboard region / CAGED shape
    ARPEGGIO_SEQUENCE = "Arpeggio Accumulator"   # Notes played sequentially over time window


class AudioSettings(BaseModel):
    """Audio DSP processing parameters."""
    model_config = ConfigDict(frozen=False)

    sample_rate: int = Field(44100, ge=8000, le=96000, description="Input sample rate in Hz")
    buffer_size: int = Field(2048, ge=512, le=8192, description="FFT buffer size in frames")
    hop_size: int = Field(1024, ge=128, le=4096, description="Hop size between DSP frames")
    tolerance_cents: float = Field(25.0, ge=5.0, le=50.0, description="Pitch error tolerance in cents")
    min_volume_db: float = Field(-50.0, ge=-90.0, le=0.0, description="Silence threshold in dBFS")
    hold_duration_sec: float = Field(0.20, ge=0.05, le=2.0, description="Required match hold duration")
    arpeggio_window_sec: float = Field(2.0, ge=0.5, le=5.0, description="Accumulator memory duration")
    device_id: Optional[int] = Field(None, description="Selected input device index or None for default")


class ChordFilterSettings(BaseModel):
    """Filter criteria used when generating random target chords."""
    model_config = ConfigDict(frozen=False)

    qualities: Set[ChordQuality] = Field(
        default_factory=lambda: {ChordQuality.MAJOR, ChordQuality.MINOR},
        description="Active chord qualities included in practice"
    )
    selected_keys: Set[str] = Field(
        default_factory=lambda: {"C", "G", "D", "A", "E"},
        description="Active musical keys included in practice"
    )
    caged_positions: Set[CAGEDPosition] = Field(
        default_factory=lambda: {CAGEDPosition.NONE},
        description="Active CAGED position restrictions"
    )
    allow_open_chords: bool = Field(True, description="Include open position voicings")
    allow_barre_chords: bool = Field(True, description="Include barre chord voicings")
    min_fret: int = Field(0, ge=0, le=24, description="Minimum fret position")
    max_fret: int = Field(12, ge=0, le=24, description="Maximum fret position")


class TrainerSettings(BaseModel):
    """Master application configuration state model."""
    model_config = ConfigDict(frozen=False)

    detection_mode: DetectionMode = Field(DetectionMode.NOTE_DETECTION)
    practice_mode: PracticeMode = Field(PracticeMode.SPEED_FLASHCARD)
    validation_mode: ValidationMode = Field(ValidationMode.RELAXED_PITCH_CLASS)
    timer_duration_sec: float = Field(3.0, ge=1.0, le=30.0)
    auto_advance: bool = Field(False, description="Auto advance when timer expires or note matched")
    audio_enabled: bool = Field(True, description="Microphone pitch detection active switch")
    instrument_preset: str = Field("Guitar (6-String Standard)")
    audio_settings: AudioSettings = Field(default_factory=AudioSettings)
    chord_filters: ChordFilterSettings = Field(default_factory=ChordFilterSettings)
