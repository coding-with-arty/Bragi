"""
src/storage/progress_repository.py
===================================
SQLite repository managing real user practice attempt logs, profile XP/levels,
daily streaks, quest challenges, note mastery tiers, and achievement badges.
"""

from datetime import datetime, date, timedelta
import sqlite3
import time
from pathlib import Path
from typing import List, Optional, Dict
from models.progress import (
    AttemptRecord,
    UserProfile,
    Achievement,
    NoteMastery,
    MasteryTier
)
from utils.music_theory import CHROMATIC_SHARPS

# Rank Titles based on Level
LEVEL_TITLES = {
    1: "Fret Novice",
    2: "Tone Apprentice",
    3: "Scale Explorer",
    4: "Rhythm Artisan",
    5: "Fretboard Specialist",
    6: "Chromatic Virtuoso",
    7: "Harmonic Master",
    8: "Shred Maestro",
    9: "Legendary Picker",
    10: "Grandmaster of Frets",
}


class ProgressRepository:
    """SQLite repository managing real practice attempts, XP leveling, streaks, and achievements."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            data_dir = Path.home() / ".Bragi"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_file = data_dir / "user_progress.db"
        else:
            self.db_file = db_path

        self._init_db()
        self._ensure_default_achievements()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attempt_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_name TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    is_success INTEGER NOT NULL,
                    response_time_sec REAL NOT NULL,
                    cents_error REAL NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profile (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    current_xp INTEGER DEFAULT 0,
                    current_level INTEGER DEFAULT 1,
                    current_streak INTEGER DEFAULT 0,
                    best_streak INTEGER DEFAULT 0,
                    last_practice_day TEXT DEFAULT '',
                    created_at REAL NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT DEFAULT 'General',
                    icon_name TEXT NOT NULL,
                    unlocked INTEGER DEFAULT 0,
                    unlocked_at REAL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_challenges (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    target_count INTEGER NOT NULL,
                    current_count INTEGER DEFAULT 0,
                    xp_reward INTEGER NOT NULL,
                    is_completed INTEGER DEFAULT 0,
                    category TEXT DEFAULT 'Accuracy'
                )
            """)

            # Schema Migration Safety Check
            cursor.execute("PRAGMA table_info(user_profile)")
            cols = [row["name"] for row in cursor.fetchall()]
            if "best_streak" not in cols:
                cursor.execute("ALTER TABLE user_profile ADD COLUMN best_streak INTEGER DEFAULT 0")

            cursor.execute("SELECT COUNT(*) FROM user_profile WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO user_profile (id, current_xp, current_level, current_streak, best_streak, last_practice_day, created_at)
                    VALUES (1, 125, 1, 1, 1, ?, ?)
                """, (date.today().isoformat(), time.time()))

            conn.commit()

    def _ensure_default_achievements(self) -> None:
        defaults = [
            ("a1", "First Steps", "Complete your first pitch recognition attempt", "Trainer", "EMOJI_EVENTS", 0),
            ("a2", "Speed Demon", "Identify 5 notes with response time under 1.5s", "Trainer", "SPEED", 0),
            ("a3", "Perfect Pitch", "Achieve 100% accuracy in a 10-attempt session", "Trainer", "AUTO_AWESOME", 0),
            ("a4", "Consistent Picker", "Maintain a 3-day practice streak", "Streaks", "LOCAL_FIRE_DEPARTMENT", 0),
            ("a5", "On Fire!", "Maintain a 7-day practice streak", "Streaks", "LOCAL_FIRE_DEPARTMENT", 0),
            ("a6", "Ear Specialist", "Score 10 correct recognitions in Ear Training", "Ear Training", "HEARING", 0),
            ("a7", "Chromatic Master", "Reach Platinum tier on any chromatic note", "Trainer", "MILITARY_TECH", 0),
        ]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for id_, title, desc, cat, icon, unl in defaults:
                cursor.execute("""
                    INSERT OR IGNORE INTO achievements (id, title, description, category, icon_name, unlocked, unlocked_at)
                    VALUES (?, ?, ?, ?, ?, ?, NULL)
                """, (id_, title, desc, cat, icon, unl))

            # Default daily quests
            default_quests = [
                ("d1", "Fretboard Warmup", "Identify 10 notes in Trainer Mode", 10, 3, 50, 0, "Trainer"),
                ("d2", "Ear Training Quest", "Correctly identify 5 intervals or chords", 5, 1, 75, 0, "Ear Training"),
                ("d3", "Speed Practice", "Identify 5 notes under 2.0s average response", 5, 0, 100, 0, "Speed"),
            ]
            for q_id, q_title, q_desc, q_target, q_curr, q_xp, q_done, q_cat in default_quests:
                cursor.execute("""
                    INSERT OR IGNORE INTO daily_challenges (id, title, description, target_count, current_count, xp_reward, is_completed, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (q_id, q_title, q_desc, q_target, q_curr, q_xp, q_done, q_cat))

            conn.commit()

    def get_profile(self) -> UserProfile:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT current_xp, current_level, current_streak, last_practice_day, created_at FROM user_profile WHERE id = 1")
            row = cursor.fetchone()
            if row:
                return UserProfile(
                    current_xp=row["current_xp"],
                    current_level=row["current_level"],
                    current_streak=row["current_streak"],
                    last_practice_day=row["last_practice_day"] or "",
                    created_at=row["created_at"]
                )
            return UserProfile()

    def log_attempt(self, record: AttemptRecord) -> Dict:
        """Logs exercise attempt, awards XP, updates streaks, and checks achievements."""
        today_str = date.today().isoformat()
        xp_earned = 0

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Log Attempt
            cursor.execute("""
                INSERT INTO attempt_records
                (target_name, target_type, is_success, response_time_sec, cents_error, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                record.target_name,
                record.target_type,
                1 if record.is_success else 0,
                record.response_time_sec,
                record.cents_error,
                record.timestamp
            ))

            # 2. XP Base Award (+15 XP for success, +10 XP speed bonus under 2.0s)
            if record.is_success:
                xp_earned += 15
                if record.response_time_sec <= 2.0:
                    xp_earned += 10
            else:
                xp_earned += 3  # Participation XP

            # 3. Update Streak & Profile
            cursor.execute("SELECT current_xp, current_level, current_streak, best_streak, last_practice_day FROM user_profile WHERE id = 1")
            prof = cursor.fetchone()

            curr_xp = prof["current_xp"] + xp_earned
            curr_lvl = (curr_xp // 500) + 1
            curr_streak = prof["current_streak"]
            best_streak = prof["best_streak"]
            last_day = prof["last_practice_day"]

            if last_day != today_str:
                if last_day:
                    try:
                        last_date = date.fromisoformat(last_day)
                        if last_date == date.today() - timedelta(days=1):
                            curr_streak += 1
                        elif last_date < date.today() - timedelta(days=1):
                            curr_streak = 1
                    except ValueError:
                        curr_streak = 1
                else:
                    curr_streak = 1

                if curr_streak > best_streak:
                    best_streak = curr_streak

            cursor.execute("""
                UPDATE user_profile
                SET current_xp = ?, current_level = ?, current_streak = ?, best_streak = ?, last_practice_day = ?
                WHERE id = 1
            """, (curr_xp, curr_lvl, curr_streak, best_streak, today_str))

            # 4. Check Unlockable Achievements
            cursor.execute("SELECT COUNT(*) FROM attempt_records")
            total_attempts = cursor.fetchone()[0]
            if total_attempts >= 1:
                cursor.execute("UPDATE achievements SET unlocked = 1, unlocked_at = ? WHERE id = 'a1' AND unlocked = 0", (time.time(),))

            if curr_streak >= 3:
                cursor.execute("UPDATE achievements SET unlocked = 1, unlocked_at = ? WHERE id = 'a4' AND unlocked = 0", (time.time(),))
            if curr_streak >= 7:
                cursor.execute("UPDATE achievements SET unlocked = 1, unlocked_at = ? WHERE id = 'a5' AND unlocked = 0", (time.time(),))

            conn.commit()

        return {
            "xp_earned": xp_earned,
            "total_xp": curr_xp,
            "level": curr_lvl,
            "streak": curr_streak
        }

    def get_user_stats(self) -> dict:
        """Returns live aggregated user metrics directly from SQLite."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT current_xp, current_level, current_streak, best_streak FROM user_profile WHERE id = 1")
            prof = cursor.fetchone()

            cursor.execute("SELECT COUNT(*), SUM(is_success) FROM attempt_records")
            row = cursor.fetchone()

            total_attempts = row[0] or 0
            success_count = row[1] or 0
            acc = (success_count / total_attempts * 100.0) if total_attempts > 0 else 0.0

            xp = prof["current_xp"] if prof else 0
            level = prof["current_level"] if prof else 1
            streak = prof["current_streak"] if prof else 0
            best = prof["best_streak"] if prof else 0

            rank_title = LEVEL_TITLES.get(min(level, 10), "Fretboard Virtuoso")

            return {
                "total_xp": xp,
                "current_level": level,
                "rank_title": rank_title,
                "current_streak": streak,
                "best_streak": best,
                "total_attempts": total_attempts,
                "success_count": success_count,
                "accuracy_rate": round(acc, 1),
            }

    def get_note_mastery(self) -> Dict[str, float]:
        """Returns accuracy percentages for all 12 chromatic note classes."""
        mastery = {note: 0.0 for note in CHROMATIC_SHARPS}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    target_name,
                    COUNT(*) as attempts,
                    SUM(is_success) as successes
                FROM attempt_records
                WHERE target_type = 'note'
                GROUP BY target_name
            """)
            for row in cursor.fetchall():
                note = row["target_name"].upper()
                if note in mastery:
                    attempts = row["attempts"]
                    successes = row["successes"] or 0
                    mastery[note] = round((successes / attempts * 100.0), 1) if attempts > 0 else 0.0
        return mastery

    def get_detailed_note_mastery(self) -> Dict[str, NoteMastery]:
        """Returns full NoteMastery model instances with attempts, accuracy, avg speed, and tier ranking."""
        mastery_map: Dict[str, NoteMastery] = {
            note: NoteMastery(note_name=note) for note in CHROMATIC_SHARPS
        }

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    target_name,
                    COUNT(*) as attempts,
                    SUM(is_success) as successes,
                    AVG(CASE WHEN is_success = 1 THEN response_time_sec END) as avg_speed
                FROM attempt_records
                WHERE target_type = 'note'
                GROUP BY target_name
            """)
            for row in cursor.fetchall():
                note = row["target_name"].upper()
                if note in mastery_map:
                    attempts = row["attempts"]
                    successes = row["successes"] or 0
                    avg_speed = row["avg_speed"] or 0.0
                    acc = (successes / attempts * 100.0) if attempts > 0 else 0.0

                    tier = MasteryTier.UNRANKED
                    if attempts >= 3:
                        if acc >= 90.0 and avg_speed <= 1.2:
                            tier = MasteryTier.PLATINUM
                        elif acc >= 75.0 and avg_speed <= 2.0:
                            tier = MasteryTier.GOLD
                        elif acc >= 50.0:
                            tier = MasteryTier.SILVER
                        elif acc > 0:
                            tier = MasteryTier.BRONZE

                    mastery_map[note] = NoteMastery(
                        note_name=note,
                        attempts_count=attempts,
                        success_count=successes,
                        accuracy_percentage=round(acc, 1),
                        avg_response_time_sec=round(avg_speed, 2),
                        tier=tier
                    )
        return mastery_map

    def get_daily_challenges(self) -> List[Dict]:
        """Returns active daily practice quests."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, description, target_count, current_count, xp_reward, is_completed, category FROM daily_challenges")
            rows = cursor.fetchall()
            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "description": r["description"],
                    "target": r["target_count"],
                    "progress": r["current_count"],
                    "xp_reward": r["xp_reward"],
                    "completed": bool(r["is_completed"]),
                    "category": r["category"]
                }
                for r in rows
            ]

    def get_achievements(self, category: str = "All") -> List[Dict]:
        """Returns filterable achievement badge list."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category == "All":
                cursor.execute("SELECT id, title, description, category, unlocked FROM achievements")
            else:
                cursor.execute("SELECT id, title, description, category, unlocked FROM achievements WHERE category = ?", (category,))

            return [
                {
                    "id": r["id"],
                    "title": r["title"],
                    "description": r["description"],
                    "category": r["category"],
                    "unlocked": bool(r["unlocked"])
                }
                for r in cursor.fetchall()
            ]
