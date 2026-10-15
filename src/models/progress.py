# src/models/progress.py
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class MasteryTier(str, Enum):
    UNRANKED = "Unranked"
    BRONZE = "Bronze"       # >60% accuracy
    SILVER = "Silver"       # >75% accuracy, <3.0s avg
    GOLD = "Gold"           # >85% accuracy, <2.0s avg
    PLATINUM = "Platinum"   # >95% accuracy, <1.2s avg


class NoteMastery(BaseModel):
    """Detailed mastery metrics for a single pitch class."""
    note_name: str
    attempts_count: int = 0
    success_count: int = 0
    accuracy_percentage: float = 0.0
    avg_response_time_sec: float = 0.0
    tier: MasteryTier = MasteryTier.UNRANKED


class Challenge(BaseModel):
    """Daily/Weekly practice challenge specification."""
    id: str
    title: str
    description: str
    target_count: int
    current_count: int = 0
    xp_reward: int
    is_completed: bool = False
    category: str = "Accuracy"  # "Accuracy", "Speed", "Memorization", "Ear Training"


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
    """Aggregate progress metrics for an active practice session."""
    session_id: str = ""
    start_time: float = 0.0
    end_time: Optional[float] = None
    total_attempts: int = 0
    successful_attempts: int = 0
    total_response_time_sec: float = 0.0
    accuracy_percentage: float = 0.0
    average_response_time_sec: float = 0.0


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
    category: str = "General"  # "Memorization", "Accuracy", "Speed", "Ear Training"
    icon_name: str = "EMOJI_EVENTS"
    unlocked: bool = False
    unlocked_at: Optional[float] = None
