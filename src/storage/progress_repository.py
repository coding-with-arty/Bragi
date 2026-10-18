# src/storage/progress_repository.py
"""
Progress Repository
===================
SQLite repository handling multi-user progress analytics, XP, and practice metrics
with automated schema migrations.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Union
from storage.path_utils import get_db_path
from engine.gamification_policy import GamificationPolicy, RewardResult
from models.progress import AttemptRecord


class ProgressRepository:
    """SQLite repository managing multi-user progress profiles and attempt logs."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
        self.active_user_id: int = 1
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes database tables and executes automatic column migrations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Create user_profiles table if missing
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    total_xp INTEGER DEFAULT 0,
                    current_level INTEGER DEFAULT 1,
                    current_streak INTEGER DEFAULT 0,
                    best_streak INTEGER DEFAULT 0,
                    rank_title TEXT DEFAULT 'Fret Novice'
                )
            """)

            # 2. Create attempts table if missing
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    note_name TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    response_time_sec REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES user_profiles(id)
                )
            """)

            # 3. Migration Check: Ensure user_id column exists on pre-existing attempts table
            cursor.execute("PRAGMA table_info(attempts)")
            existing_columns = [row["name"] for row in cursor.fetchall()]
            if "user_id" not in existing_columns:
                cursor.execute("ALTER TABLE attempts ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")

            # 4. Ensure default user profile exists
            cursor.execute("""
                INSERT OR IGNORE INTO user_profiles (id, username, total_xp, current_level, current_streak, best_streak, rank_title)
                VALUES (1, 'Default Player', 0, 1, 0, 0, 'Fret Novice')
            """)

            conn.commit()

    def get_all_users(self) -> List[Dict]:
        """Returns a list of all registered user profiles."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, total_xp, current_level FROM user_profiles")
            return [dict(row) for row in cursor.fetchall()]

    def create_user(self, username: str) -> int:
        """Creates a new user profile and sets it as active."""
        clean_name = username.strip() or "New Player"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_profiles (username, total_xp, current_level) VALUES (?, 0, 1)",
                (clean_name,)
            )
            conn.commit()
            new_id = cursor.lastrowid
            self.active_user_id = new_id
            return new_id

    def set_active_user(self, user_id: int) -> None:
        """Switches the active user profile ID for analytics tracking."""
        self.active_user_id = user_id

    def get_user_stats(self) -> Dict:
        """Fetches consolidated user stats for the currently active user profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_profiles WHERE id = ?", (self.active_user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                cursor.execute("SELECT * FROM user_profiles WHERE id = 1")
                user_row = cursor.fetchone()
                self.active_user_id = 1

            row = dict(user_row)

            cursor.execute(
                "SELECT COUNT(*), SUM(is_correct) FROM attempts WHERE user_id = ?",
                (self.active_user_id,)
            )
            total_attempts, correct_attempts = cursor.fetchone()

            total = total_attempts or 0
            correct = correct_attempts or 0
            accuracy = (correct / total * 100.0) if total > 0 else 0.0

            row["total_attempts"] = total
            row["correct_attempts"] = correct
            row["accuracy_rate"] = accuracy
            return row

    def log_attempt(
        self,
        note_name_or_record: Union[str, AttemptRecord, bool] = "",
        is_correct: Optional[bool] = None,
        response_time_sec: float = 0.0,
        **kwargs,
    ) -> RewardResult:
        """
        Flexibly accepts an AttemptRecord model OR positional/keyword arguments.
        Logs an attempt for the active user profile and updates XP metrics.
        """
        if isinstance(note_name_or_record, AttemptRecord):
            note_name = note_name_or_record.target_name
            correct = note_name_or_record.is_success
            resp_time = note_name_or_record.response_time_sec
        elif isinstance(note_name_or_record, bool):
            note_name = "Target Note"
            correct = note_name_or_record
            resp_time = response_time_sec
        else:
            note_name = str(note_name_or_record) if note_name_or_record else "Target Note"
            correct = is_correct if is_correct is not None else True
            resp_time = response_time_sec

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO attempts (user_id, note_name, is_correct, response_time_sec) VALUES (?, ?, ?, ?)",
                (self.active_user_id, note_name, 1 if correct else 0, resp_time)
            )

            cursor.execute(
                "SELECT total_xp, current_streak, best_streak FROM user_profiles WHERE id = ?",
                (self.active_user_id,)
            )
            stats_row = cursor.fetchone()
            current_xp = stats_row["total_xp"]
            current_streak = stats_row["current_streak"]
            best_streak = stats_row["best_streak"]

            reward = GamificationPolicy.calculate_reward(
                is_correct=correct,
                response_time_sec=resp_time,
                current_streak=current_streak,
                current_total_xp=current_xp
            )

            new_best_streak = max(best_streak, reward.streak_count)

            cursor.execute("""
                UPDATE user_profiles
                SET total_xp = ?,
                    current_level = ?,
                    current_streak = ?,
                    best_streak = ?
                WHERE id = ?
            """, (reward.new_total_xp, reward.current_level, reward.streak_count, new_best_streak, self.active_user_id))

            conn.commit()
            return reward

    def get_detailed_note_mastery(self) -> Dict[str, Dict]:
        """Calculates per-pitch accuracy percentages for the active user."""
        mastery = {}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    note_name,
                    COUNT(*) as attempts_count,
                    SUM(is_correct) as success_count,
                    AVG(response_time_sec) as avg_speed
                FROM attempts
                WHERE user_id = ?
                GROUP BY note_name
            """, (self.active_user_id,))
            rows = cursor.fetchall()

            for row in rows:
                attempts = row["attempts_count"]
                successes = row["success_count"] or 0
                acc = (successes / attempts * 100.0) if attempts > 0 else 0.0
                tier, color = GamificationPolicy.get_mastery_tier(acc, attempts)

                mastery[row["note_name"]] = {
                    "attempts_count": attempts,
                    "success_count": successes,
                    "accuracy_percentage": acc,
                    "avg_response_time_sec": row["avg_speed"] or 0.0,
                    "tier": tier.value,
                    "color": color
                }

        return mastery

    def get_daily_challenges(self) -> List[Dict]:
        """Evaluates today's attempts for the active user profile."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) as today_total,
                    COALESCE(SUM(is_correct), 0) as today_correct,
                    COALESCE(SUM(CASE WHEN response_time_sec <= 2.0 AND is_correct = 1 THEN 1 ELSE 0 END), 0) as today_fast
                FROM attempts
                WHERE user_id = ? AND DATE(timestamp) = DATE('now', 'localtime')
            """, (self.active_user_id,))
            row = cursor.fetchone()
            today_total = row["today_total"] or 0
            today_correct = row["today_correct"] or 0
            today_fast = row["today_fast"] or 0

        return [
            {
                "id": "daily_attempts",
                "title": "Daily Practice Warmup",
                "description": "Complete 5 note identification attempts today.",
                "progress": min(today_total, 5),
                "target": 5,
                "completed": today_total >= 5,
                "xp_reward": 50,
            },
            {
                "id": "daily_accuracy",
                "title": "Pitch Precision",
                "description": "Get 3 correct notes in today's practice session.",
                "progress": min(today_correct, 3),
                "target": 3,
                "completed": today_correct >= 3,
                "xp_reward": 75,
            },
            {
                "id": "speed_demon",
                "title": "Quick Reflexes",
                "description": "Identify 2 notes under 2 seconds.",
                "progress": min(today_fast, 2),
                "target": 2,
                "completed": today_fast >= 2,
                "xp_reward": 100,
            },
        ]

    def get_achievements(self, category: Optional[str] = None) -> List[Dict]:
        """Evaluates milestones for the active user profile."""
        stats = self.get_user_stats()
        total_xp = stats.get("total_xp", 0)
        total_attempts = stats.get("total_attempts", 0)
        best_streak = stats.get("best_streak", 0)
        accuracy = stats.get("accuracy_rate", 0.0)

        achievements = [
            {
                "id": "first_note",
                "title": "First Steps",
                "description": "Log your very first note attempt.",
                "category": "GENERAL",
                "icon": "music_note",
                "unlocked": total_attempts >= 1,
            },
            {
                "id": "streak_5",
                "title": "In the Groove",
                "description": "Achieve a 5-note streak.",
                "category": "STREAK",
                "icon": "local_fire_department",
                "unlocked": best_streak >= 5,
            },
            {
                "id": "streak_10",
                "title": "Unstoppable",
                "description": "Achieve a 10-note streak.",
                "category": "STREAK",
                "icon": "whatshot",
                "unlocked": best_streak >= 10,
            },
            {
                "id": "accuracy_80",
                "title": "Ear Specialist",
                "description": "Maintain over 80% accuracy across 20+ attempts.",
                "category": "MASTERY",
                "icon": "verified",
                "unlocked": total_attempts >= 20 and accuracy >= 80.0,
            },
            {
                "id": "xp_1000",
                "title": "Virtuoso Scholar",
                "description": "Earn a total of 1,000 XP.",
                "category": "GENERAL",
                "icon": "military_tech",
                "unlocked": total_xp >= 1000,
            },
        ]

        if category and category.upper() != "ALL":
            achievements = [a for a in achievements if a["category"].upper() == category.upper()]

        return achievements
