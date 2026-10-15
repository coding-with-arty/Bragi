# src/engine/gamification.py
import math
import time
from datetime import datetime, timezone
from typing import List, Tuple
from models.progress import UserProfile, Achievement, AttemptRecord
from storage.progress_repository import ProgressRepository

# Reward Constants
XP_NOTE_MATCH = 10
XP_CHORD_MATCH = 25
XP_EAR_TRAINING = 15
XP_DAILY_STREAK = 50

DEFAULT_ACHIEVEMENTS = [
    Achievement(id="first_note", title="First Steps", description="Play your first correct note", icon_name="MUSIC_NOTE"),
    Achievement(id="notes_50", title="Fretboard Explorer", description="Match 50 correct notes", icon_name="EXPLORER"),
    Achievement(id="notes_200", title="Fretboard Virtuoso", description="Match 200 correct notes", icon_name="STAR"),
    Achievement(id="chord_10", title="Chord Detective", description="Identify 10 full chords", icon_name="TUNE"),
    Achievement(id="ear_master", title="Ear Training Prodigy", description="Complete 25 ear training questions", icon_name="HEARING"),
    Achievement(id="streak_3", title="Consistent Strummer", description="Maintain a 3-day practice streak", icon_name="LOCAL_FIRE_DEPARTMENT"),
]


class GamificationEngine:
    """Handles experience points (XP), leveling curves, daily practice streaks, and achievement checks."""

    def __init__(self, repository: ProgressRepository):
        self.repo = repository
        self.repo.sync_default_achievements(DEFAULT_ACHIEVEMENTS)

    @staticmethod
    def calculate_level(xp: int) -> int:
        """
        Calculates user level based on total XP.
        Formula: Level = floor(sqrt(XP / 50)) + 1
        """
        if xp <= 0:
            return 1
        return int(math.floor(math.sqrt(xp / 50.0))) + 1

    @staticmethod
    def xp_for_level(level: int) -> int:
        """Calculates minimum cumulative XP required to reach a specific level."""
        if level <= 1:
            return 0
        return int(50 * ((level - 1) ** 2))

    def process_attempt_reward(self, record: AttemptRecord) -> Tuple[UserProfile, List[Achievement]]:
        """
        Logs an attempt record, updates user XP, advances daily streak, and checks for newly unlocked achievements.
        Returns: (Updated UserProfile, List of newly unlocked achievements)
        """
        self.repo.log_attempt(record)
        profile = self.repo.get_profile()
        newly_unlocked = []

        if record.is_success:
            # Add base XP depending on exercise type
            if record.target_type == "note":
                profile.current_xp += XP_NOTE_MATCH
            elif record.target_type == "chord":
                profile.current_xp += XP_CHORD_MATCH
            elif record.target_type == "ear_training":
                profile.current_xp += XP_EAR_TRAINING

            # Calculate and update current level
            profile.current_level = self.calculate_level(profile.current_xp)

            # Daily Streak Evaluation
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if profile.last_practice_day != today_str:
                if profile.last_practice_day:
                    try:
                        last_dt = datetime.strptime(profile.last_practice_day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        today_dt = datetime.strptime(today_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        diff_days = (today_dt - last_dt).days
                        if diff_days == 1:
                            profile.current_streak += 1
                            profile.current_xp += XP_DAILY_STREAK
                        elif diff_days > 1:
                            profile.current_streak = 1
                    except Exception:
                        profile.current_streak = 1
                else:
                    profile.current_streak = 1

                profile.last_practice_day = today_str

            self.repo.save_profile(profile)

            # Evaluate Achievement Criteria
            newly_unlocked = self._check_achievements(profile)

        return profile, newly_unlocked

    def _check_achievements(self, profile: UserProfile) -> List[Achievement]:
        attempts = self.repo.get_recent_attempts(limit=500)
        successful_notes = sum(1 for a in attempts if a.target_type == "note" and a.is_success)
        successful_chords = sum(1 for a in attempts if a.target_type == "chord" and a.is_success)
        successful_ear = sum(1 for a in attempts if a.target_type == "ear_training" and a.is_success)

        achievements_to_unlock = []

        if (successful_notes + successful_chords + successful_ear) >= 1:
            achievements_to_unlock.append("first_note")
        if successful_notes >= 50:
            achievements_to_unlock.append("notes_50")
        if successful_notes >= 200:
            achievements_to_unlock.append("notes_200")
        if successful_chords >= 10:
            achievements_to_unlock.append("chord_10")
        if successful_ear >= 25:
            achievements_to_unlock.append("ear_master")
        if profile.current_streak >= 3:
            achievements_to_unlock.append("streak_3")

        newly_unlocked = []
        for ach_id in achievements_to_unlock:
            for db_ach in self.repo.get_achievements():
                if db_ach.id == ach_id and not db_ach.unlocked:
                    self.repo.unlock_achievement(ach_id)
                    newly_unlocked.append(db_ach)

        return newly_unlocked
