# src/models/progress.py
from typing import List, Optional
from pydantic import BaseModel, Field


class AttemptRecord(BaseModel):
    """Log record for a single exercise attempt."""
    target_name: str
    target_type: str  # "note", "chord", or "ear_training"
    is_success: bool
    response_time_sec: float
    cents_error: float = 0.0
    timestamp: float


class ChordStatSummary(BaseModel):
    """Aggregated performance statistics for a specific chord target."""
    chord_name: str
    attempts_count: int
    success_count: int
    average_response_time_sec: float
    accuracy_percentage: float


class PitchStatSummary(BaseModel):
    """Aggregated performance statistics for single notes or fretboard positions."""
    note_name: str
    attempts_count: int
    success_count: int
    accuracy_percentage: float


class SessionProgress(BaseModel):
    """Aggregated progress summary for practice sessions."""
    total_attempts: int = 0
    successful_attempts: int = 0
    average_response_time_sec: float = 0.0
    accuracy_percentage: float = 0.0


class UserProfile(BaseModel):
    """User profile containing current level, XP, and practice streaks."""
    current_xp: int = 0
    current_level: int = 1
    current_streak: int = 0
    last_practice_day: str = ""
    created_at: float = 0.0


class Achievement(BaseModel):
    """Badge or milestone unlocked through practice milestones."""
    id: str
    title: str
    description: str
    icon_name: str = "EMOJI_EVENTS"
    unlocked: bool = False
    unlocked_at: Optional[float] = None
