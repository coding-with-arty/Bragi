# src/engine/gamification.py
import math
from datetime import datetime, timezone
from typing import List, Tuple
from models.progress import UserProfile, Achievement, AttemptRecord, Challenge, MasteryTier
from storage.progress_repository import ProgressRepository

XP_NOTE_MATCH = 10
XP_CHORD_MATCH = 25
XP_EAR_TRAINING = 15
XP_DAILY_STREAK = 50

ACHIEVEMENT_DEFAULTS = [
    # Memorization Category
    Achievement(id="first_note", title="First Step", description="Find your first fretboard note", category="Memorization", icon_name="MUSIC_NOTE"),
    Achievement(id="chromatic_bronze", title="Fretboard Novice", description="Reach Bronze mastery on all 12 notes", category="Memorization", icon_name="EXPLORER"),
    Achievement(id="chromatic_gold", title="Fretboard Virtuoso", description="Reach Gold mastery on all 12 notes", category="Memorization", icon_name="STAR"),

    # Speed Category
    Achievement(id="lightning_fast", title="Speed Demon", description="Match 5 notes under 1.5 seconds each", category="Speed", icon_name="BOLT"),
    Achievement(id="sub_second", title="Reflex Master", description="Match a note in under 1.0 second", category="Speed", icon_name="TIMER"),

    # Accuracy Category
    Achievement(id="sharp_shooter", title="Bullseye", description="Achieve 10 consecutive perfect matches", category="Accuracy", icon_name="GOLF_COURSE"),
    Achievement(id="chord_detective", title="Chord Master", description="Successfully decode 10 full chord structures", category="Accuracy", icon_name="TUNE"),

    # Ear Training Category
    Achievement(id="ear_prodigy", title="Ear Prodigy", description="Complete 25 ear training listening exercises", category="Ear Training", icon_name="HEARING"),
]


class GamificationEngine:
    """Gamification engine processing XP, challenges, and fretboard achievements."""

    def __init__(self, repository: ProgressRepository):
        self.repo = repository
        self.repo.sync_default_achievements(ACHIEVEMENT_DEFAULTS)

    @staticmethod
    def calculate_level(xp: int) -> int:
        if xp <= 0:
            return 1
        return int(math.floor(math.sqrt(xp / 50.0))) + 1

    @staticmethod
    def xp_for_level(level: int) -> int:
        if level <= 1:
            return 0
        return int(50 * ((level - 1) ** 2))

    def get_active_challenges(self) -> List[Challenge]:
        """Returns dynamic daily challenge targets based on user attempt history."""
        attempts = self.repo.get_recent_attempts(limit=50)

        speed_matches = sum(1 for a in attempts if a.is_success and a.response_time_sec <= 2.0)
        recent_successes = sum(1 for a in attempts if a.is_success)

        return [
            Challenge(
                id="daily_speed",
                title="Speed Burst",
                description="Identify 10 notes in under 2.0 seconds each",
                target_count=10,
                current_count=min(10, speed_matches),
                xp_reward=100,
                is_completed=speed_matches >= 10,
                category="Speed"
            ),
            Challenge(
                id="daily_accuracy",
                title="Precision Strummer",
                description="Complete 15 successful note or chord exercises",
                target_count=15,
                current_count=min(15, recent_successes),
                xp_reward=150,
                is_completed=recent_successes >= 15,
                category="Accuracy"
            ),
        ]

    def process_attempt_reward(self, record: AttemptRecord) -> Tuple[UserProfile, List[Achievement]]:
        self.repo.log_attempt(record)
        profile = self.repo.get_profile()

        if record.is_success:
            if record.target_type == "note":
                profile.current_xp += XP_NOTE_MATCH
            elif record.target_type == "chord":
                profile.current_xp += XP_CHORD_MATCH
            elif record.target_type == "ear_training":
                profile.current_xp += XP_EAR_TRAINING

            profile.current_level = self.calculate_level(profile.current_xp)

            # Daily Streak Evaluation
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if profile.last_practice_day != today_str:
                if profile.last_practice_day:
                    try:
                        last_dt = datetime.strptime(profile.last_practice_day, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        today_dt = datetime.strptime(today_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        if (today_dt - last_dt).days == 1:
                            profile.current_streak += 1
                            profile.current_xp += XP_DAILY_STREAK
                        elif (today_dt - last_dt).days > 1:
                            profile.current_streak = 1
                    except Exception:
                        profile.current_streak = 1
                else:
                    profile.current_streak = 1

                profile.last_practice_day = today_str

            self.repo.save_profile(profile)

        newly_unlocked = self._check_achievements(profile)
        return profile, newly_unlocked

    def _check_achievements(self, profile: UserProfile) -> List[Achievement]:
        attempts = self.repo.get_recent_attempts(limit=500)
        mastery = self.repo.get_chromatic_mastery()

        successful_notes = sum(1 for a in attempts if a.target_type == "note" and a.is_success)
        successful_chords = sum(1 for a in attempts if a.target_type == "chord" and a.is_success)
        successful_ear = sum(1 for a in attempts if a.target_type == "ear_training" and a.is_success)

        fast_matches = sum(1 for a in attempts if a.is_success and a.response_time_sec <= 1.5)
        sub_sec_matches = sum(1 for a in attempts if a.is_success and a.response_time_sec < 1.0)

        all_bronze = all(m.tier != MasteryTier.UNRANKED for m in mastery.values())
        all_gold = all(m.tier in (MasteryTier.GOLD, MasteryTier.PLATINUM) for m in mastery.values())

        unlocked_ids = []
        if (successful_notes + successful_chords + successful_ear) >= 1:
            unlocked_ids.append("first_note")
        if all_bronze:
            unlocked_ids.append("chromatic_bronze")
        if all_gold:
            unlocked_ids.append("chromatic_gold")
        if fast_matches >= 5:
            unlocked_ids.append("lightning_fast")
        if sub_sec_matches >= 1:
            unlocked_ids.append("sub_second")
        if successful_chords >= 10:
            unlocked_ids.append("chord_detective")
        if successful_ear >= 25:
            unlocked_ids.append("ear_prodigy")

        newly_unlocked = []
        for ach_id in unlocked_ids:
            for db_ach in self.repo.get_achievements():
                if db_ach.id == ach_id and not db_ach.unlocked:
                    self.repo.unlock_achievement(ach_id)
                    newly_unlocked.append(db_ach)

        return newly_unlocked
