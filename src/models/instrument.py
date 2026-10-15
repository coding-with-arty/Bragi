# src/models/instrument.py
from typing import List, Tuple
from pydantic import BaseModel, Field, ConfigDict


class StringConfig(BaseModel):
    """Configuration for a single physical string."""
    model_config = ConfigDict(frozen=True)

    string_num: int = Field(..., ge=1, le=10, description="String index (1 = highest pitch string)")
    note_name: str = Field(..., description="Open tuning pitch note name (e.g. 'E', 'F#')")
    octave: int = Field(..., ge=0, le=8, description="Standard octave number (e.g. 2, 4)")


class InstrumentProfile(BaseModel):
    """Complete specification for built-in or custom fretted instrument profiles."""
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique profile identifier")
    name: str = Field(..., description="User-facing display title")
    category: str = Field("Guitar", description="Category classification ('Guitar', 'Bass', 'Ukulele', 'Mandolin', 'Banjo', 'Custom')")
    string_count: int = Field(6, ge=1, le=10, description="Total physical playable strings")
    fret_count: int = Field(24, ge=12, le=24, description="Total frets on fretboard")
    tuning: List[StringConfig] = Field(default_factory=list, description="Open tuning array ordered from String 1 down to String N")
    fretboard_landmarks: List[int] = Field(
        default_factory=lambda: [3, 5, 7, 9, 12, 15, 17, 19, 21, 24],
        description="Fret numbers with position markers"
    )
    is_custom: bool = Field(False, description="True if profile was created by user")

    def to_tuning_tuples(self) -> List[Tuple[str, int]]:
        """Converts internal StringConfig list into [('Note', octave)] tuple format."""
        return [(s.note_name, s.octave) for s in self.tuning]
