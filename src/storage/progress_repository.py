"""
src/storage/progress_repository.py
===================================
SQLite persistence repository for user exercise attempt history and analytical metrics.
"""

import sqlite3
from pathlib import Path
from typing import List, Optional
import time

from models.progress import AttemptRecord, ChordStatSummary, SessionProgress


class ProgressRepository:
    """Manages SQLite database storage for exercise attempt logs and analytics."""

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
            conn.commit()

    def log_attempt(self, record: AttemptRecord) -> None:
        """Saves a new AttemptRecord to SQLite."""
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
        """Retrieves recent attempt records."""
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

    def get_chord_summaries(self) -> List[ChordStatSummary]:
        """Calculates performance statistics grouped by chord target."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    target_name,
                    COUNT(*) as total_attempts,
                    SUM(is_success) as total_success,
                    AVG(CASE WHEN is_success = 1 THEN response_time_sec END) as avg_latency
                FROM attempt_records
                WHERE target_type = 'chord'
                GROUP BY target_name
                ORDER BY total_attempts DESC
            """)
            rows = cursor.fetchall()

            summaries = []
            for row in rows:
                attempts = row["total_attempts"]
                successes = row["total_success"] or 0
                avg_time = row["avg_latency"] or 0.0
                accuracy = (successes / attempts * 100.0) if attempts > 0 else 0.0

                summaries.append(ChordStatSummary(
                    chord_name=row["target_name"],
                    attempts_count=attempts,
                    success_count=successes,
                    average_response_time_sec=round(avg_time, 2),
                    accuracy_percentage=round(accuracy, 1)
                ))

            return summaries
