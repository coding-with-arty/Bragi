# src/storage/progress_repository.py
import sqlite3
import time
from pathlib import Path
from typing import List, Optional, Tuple
from models.progress import AttemptRecord, ChordStatSummary, PitchStatSummary, UserProfile, Achievement


class ProgressRepository:
    """Manages SQLite database storage for exercise attempt logs, analytics, user profile, and achievements."""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            data_dir = Path.home() / ".FretSense"
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_file = data_dir / "user_progress.db"
        else:
            self.db_file = db_path

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initializes database schema tables."""
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
                    last_practice_day TEXT DEFAULT '',
                    created_at REAL NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS achievements (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    icon_name TEXT NOT NULL,
                    unlocked INTEGER DEFAULT 0,
                    unlocked_at REAL
                )
            """)

            cursor.execute("SELECT COUNT(*) FROM user_profile WHERE id = 1")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO user_profile (id, current_xp, current_level, current_streak, last_practice_day, created_at)
                    VALUES (1, 0, 1, 0, '', ?)
                """, (time.time(),))

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

    def save_profile(self, profile: UserProfile) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE user_profile
                SET current_xp = ?, current_level = ?, current_streak = ?, last_practice_day = ?
                WHERE id = 1
            """, (profile.current_xp, profile.current_level, profile.current_streak, profile.last_practice_day))
            conn.commit()

    def log_attempt(self, record: AttemptRecord) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
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
            conn.commit()

    def get_recent_attempts(self, limit: int = 50) -> List[AttemptRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT target_name, target_type, is_success, response_time_sec, cents_error, timestamp
                FROM attempt_records
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [
                AttemptRecord(
                    target_name=row["target_name"],
                    target_type=row["target_type"],
                    is_success=bool(row["is_success"]),
                    response_time_sec=row["response_time_sec"],
                    cents_error=row["cents_error"],
                    timestamp=row["timestamp"]
                )
                for row in rows
            ]

    def get_pitch_accuracies(self) -> Tuple[List[PitchStatSummary], List[PitchStatSummary]]:
        """Calculates performance statistics grouped by note name and splits into strongest and weakest notes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    target_name,
                    COUNT(*) as total_attempts,
                    SUM(is_success) as total_success
                FROM attempt_records
                WHERE target_type = 'note'
                GROUP BY target_name
                HAVING total_attempts >= 3
                ORDER BY (CAST(SUM(is_success) AS REAL) / COUNT(*)) DESC
            """)
            rows = cursor.fetchall()

            all_stats = []
            for row in rows:
                attempts = row["total_attempts"]
                successes = row["total_success"] or 0
                acc = (successes / attempts * 100.0) if attempts > 0 else 0.0
                all_stats.append(PitchStatSummary(
                    note_name=row["target_name"],
                    attempts_count=attempts,
                    success_count=successes,
                    accuracy_percentage=round(acc, 1)
                ))

            strongest = all_stats[:3]
            weakest = sorted(all_stats, key=lambda x: x.accuracy_percentage)[:3] if len(all_stats) > 3 else []
            return strongest, weakest

    def get_achievements(self) -> List[Achievement]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, description, icon_name, unlocked, unlocked_at FROM achievements")
            rows = cursor.fetchall()
            return [
                Achievement(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    icon_name=row["icon_name"],
                    unlocked=bool(row["unlocked"]),
                    unlocked_at=row["unlocked_at"]
                )
                for row in rows
            ]

    def unlock_achievement(self, achievement_id: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE achievements
                SET unlocked = 1, unlocked_at = ?
                WHERE id = ? AND unlocked = 0
            """, (time.time(), achievement_id))
            conn.commit()

    def sync_default_achievements(self, defaults: List[Achievement]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            for ach in defaults:
                cursor.execute("""
                    INSERT OR IGNORE INTO achievements (id, title, description, icon_name, unlocked, unlocked_at)
                    VALUES (?, ?, ?, ?, 0, NULL)
                """, (ach.id, ach.title, ach.description, ach.icon_name))
            conn.commit()
