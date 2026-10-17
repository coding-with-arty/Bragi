import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
from storage.path_utils import get_db_path
from engine.gamification_policy import GamificationPolicy, RewardResult


class ProgressRepository:
    """
    SQLite repository handling persistent storage of exercise attempts, XP,
    daily practice quests, achievements, and user statistics within atomic transactions.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or get_db_path()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes database schema tables and indexes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Attempts log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_name TEXT NOT NULL,
                    is_correct INTEGER NOT NULL,
                    response_time_sec REAL NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User profile statistics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    total_xp INTEGER DEFAULT 0,
                    current_level INTEGER DEFAULT 1,
                    current_streak INTEGER DEFAULT 0,
                    best_streak INTEGER DEFAULT 0,
                    rank_title TEXT DEFAULT 'Fret Novice'
                )
            """)

            # Initialize single user profile row if missing
            cursor.execute("""
                INSERT OR IGNORE INTO user_stats (id, total_xp, current_level, current_streak, best_streak, rank_title)
                VALUES (1, 0, 1, 0, 0, 'Fret Novice')
            """)

            conn.commit()

    def get_user_stats(self) -> Dict:
        """Fetches consolidated user stats and overall accuracy metrics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_stats WHERE id = 1")
            row = dict(cursor.fetchone())

            cursor.execute("SELECT COUNT(*), SUM(is_correct) FROM attempts")
            total_attempts, correct_attempts = cursor.fetchone()

            total = total_attempts or 0
            correct = correct_attempts or 0
            accuracy = (correct / total * 100.0) if total > 0 else 0.0

            row["total_attempts"] = total
            row["correct_attempts"] = correct
            row["accuracy_rate"] = accuracy
            return row

    def log_attempt(self, note_name: str, is_correct: bool, response_time_sec: float) -> RewardResult:
        """
        Executes an atomic transaction that logs an attempt, updates total XP,
        level status, and active streaks.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Log raw attempt entry
            cursor.execute(
                "INSERT INTO attempts (note_name, is_correct, response_time_sec) VALUES (?, ?, ?)",
                (note_name, 1 if is_correct else 0, response_time_sec)
            )

            # Fetch existing stats
            cursor.execute("SELECT total_xp, current_streak, best_streak FROM user_stats WHERE id = 1")
            stats_row = cursor.fetchone()
            current_xp = stats_row["total_xp"]
            current_streak = stats_row["current_streak"]
            best_streak = stats_row["best_streak"]

            # Calculate reward via GamificationPolicy
            reward = GamificationPolicy.calculate_reward(
                is_correct=is_correct,
                response_time_sec=response_time_sec,
                current_streak=current_streak,
                current_total_xp=current_xp
            )

            new_best_streak = max(best_streak, reward.streak_count)

            # Update user stats row
            cursor.execute("""
                UPDATE user_stats
                SET total_xp = ?,
                    current_level = ?,
                    current_streak = ?,
                    best_streak = ?
                WHERE id = 1
            """, (reward.new_total_xp, reward.current_level, reward.streak_count, new_best_streak))

            conn.commit()
            return reward

    def get_detailed_note_mastery(self) -> Dict[str, Dict]:
        """Calculates per-pitch accuracy percentages, average speeds, and mastery tiers."""
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
                GROUP BY note_name
            """)
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
        """
        Evaluates today's attempt logs and returns progress toward daily practice goals.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) as today_total,
                    COALESCE(SUM(is_correct), 0) as today_correct,
                    COALESCE(SUM(CASE WHEN response_time_sec <= 2.0 AND is_correct = 1 THEN 1 ELSE 0 END), 0) as today_fast
                FROM attempts
                WHERE DATE(timestamp) = DATE('now', 'localtime')
            """)
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
        """
        Evaluates user stats and attempt records against achievement milestones.
        Filters by category if specified (e.g. 'GENERAL', 'STREAK', 'MASTERY').
        """
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
