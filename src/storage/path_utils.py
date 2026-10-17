from pathlib import Path
import sys


def get_app_data_dir(app_name: str = "Bragi") -> Path:
    """
    Returns a platform-agnostic, sandboxed directory path for user application data.

    Directory mapping:
    - Windows: %APPDATA%/Bragi
    - macOS: ~/Library/Application Support/Bragi
    - Linux / Unix: ~/.config/Bragi
    """
    home = Path.home()

    if sys.platform == "win32":
        base_dir = home / "AppData" / "Roaming"
    elif sys.platform == "darwin":
        base_dir = home / "Library" / "Application Support"
    else:
        base_dir = home / ".config"

    app_dir = base_dir / app_name
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_db_path(db_name: str = "bragi_progress.db") -> Path:
    """Returns the sandboxed path to the SQLite analytics database."""
    return get_app_data_dir() / db_name


def get_user_instruments_path(filename: str = "custom_instruments.json") -> Path:
    """Returns the sandboxed path to the custom instrument profiles storage file."""
    return get_app_data_dir() / filename


def get_settings_path(filename: str = "settings.json") -> Path:
    """Returns the sandboxed path to the application configuration file."""
    return get_app_data_dir() / filename
