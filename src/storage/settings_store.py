"""
src/storage/settings_store.py
==============================
JSON file-based persistence store for application TrainerSettings.
"""

import json
from pathlib import Path
from typing import Optional
from models.settings import TrainerSettings
from storage.path_utils import get_settings_path


class SettingsStore:
    """Handles thread-safe reading and writing of TrainerSettings to disk."""

    def __init__(self, filepath: Optional[Path] = None):
        self.filepath = filepath or get_settings_path()

    def load_settings(self) -> TrainerSettings:
        """Loads settings from disk or returns default configuration if missing."""
        if not self.storage_file.exists():
            default_settings = TrainerSettings()
            self.save_settings(default_settings)
            return default_settings

        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                content = f.read()
                return TrainerSettings.model_validate_json(content)
        except Exception as err:
            print(f"[SettingsStore] Failed to load settings ({err}). Using defaults.")
            return TrainerSettings()

    def save_settings(self, settings: TrainerSettings) -> bool:
        """Persists current TrainerSettings instance to disk."""
        try:
            self.storage_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.storage_file, "w", encoding="utf-8") as f:
                f.write(settings.model_dump_json(indent=2))
            return True
        except Exception as err:
            print(f"[SettingsStore] Failed to save settings: {err}")
            return False
