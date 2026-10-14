"""
src/models/progress.py
======================
Pydantic schemas for tracking user attempts, chord response latency,
session statistics, and performance analytics.
"""

from typing import List, Optional, Literal
from time import time
from pydantic import BaseModel, Field, ConfigDict


class AttemptRecord(BaseModel):
    """Record of a single note or chord exercise attempt."""
    model_config = ConfigDict(frozen=True)

    target_name: str = Field(..., description="Target name, e.g., 'C4' or 'G Major'")
    target_type: Literal["note", "chord"] = Field(..., description="Exercise target type")
    is_success: bool = Field(..., description="True if target was correctly played before timeout")
    response_time_sec: float = Field(..., ge=0.0, description="Time taken to correctly play target")
    cents_error: float = Field(0.0, description="Recorded pitch error deviation in cents")
    timestamp: float = Field(default_factory=time, description="Attempt completion timestamp")


class ChordStatSummary(BaseModel):
    """Aggregated performance metrics for a specific chord."""
    model_config = ConfigDict(frozen=True)

    chord_name: str = Field(..., description="Target chord name")
    attempts_count: int = Field(0, ge=0)
    success_count: int = Field(0, ge=0)
    average_response_time_sec: float = Field(0.0, ge=0.0)
    accuracy_percentage: float = Field(0.0, ge=0.0, le=100.0)


class SessionProgress(BaseModel):
    """Aggregate metrics for an active practice session."""
    model_config = ConfigDict(frozen=False)

    session_id: str = Field(..., description="Unique session identifier")
    start_time: float = Field(default_factory=time)
    end_time: Optional[float] = Field(None)
    total_attempts: int = Field(0, ge=0)
    successful_attempts: int = Field(0, ge=0)
    history: List[AttemptRecord] = Field(default_factory=list)

    @property
    def accuracy_percentage(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return round((self.successful_attempts / self.total_attempts) * 100.0, 1)

    @property
    def average_latency_sec(self) -> float:
        successful = [h.response_time_sec for h in self.history if h.is_success]
        if not successful:
            return 0.0
        return round(sum(successful) / len(successful), 2)
