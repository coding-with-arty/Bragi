from dataclasses import dataclass
from typing import Any


@dataclass
class AudioFrame:
    """
    Immutable data model representing a single captured PCM audio frame's DSP metrics.
    """
    frequency: float = 0.0
    pitch_class: str = "--"
    octave: int = 0
    cents_deviation: float = 0.0
    confidence: float = 0.0
    is_silent: bool = True
    rms_db: float = -100.0

    @property
    def cents(self) -> float:
        """Alias property for cents_deviation to satisfy audio worker callers."""
        return self.cents_deviation

    @property
    def db_level(self) -> float:
        """Alias property for rms_db to satisfy audio worker callers."""
        return self.rms_db

    @property
    def note_name(self) -> str:
        """Alias property for pitch_class to satisfy audio worker callers."""
        return self.pitch_class

    def get(self, key: str, default: Any = None) -> Any:
        """
        Provides dictionary-style key access for backward compatibility with state subscribers.
        """
        if key == "cents":
            return self.cents_deviation
        if key == "db_level":
            return self.rms_db
        if key == "note_name":
            return self.pitch_class
        return getattr(self, key, default)
