from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Application configuration loaded from environment variables and/or a .env file."""
    db_name: str
    db_user: str
    db_password: str
    db_host: str = "localhost"
    db_port: int = 5432


def executable_dir() -> Path:
    """Return the directory where the app is running from.

    - Dev mode: directory of this file (project).
    - PyInstaller: directory containing the executable.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def load_env_file(env_path: Path) -> None:
    """Load a .env file into os.environ (no external dependencies).

    Rules:
    - Ignores empty lines and comments (#).
    - Supports KEY=VALUE with optional quotes.
    - Does not override variables already present in os.environ.
    """
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def load_config() -> AppConfig:
    """Load config, preferring a .env next to the executable.

    Search order:
      1) <executable_dir>/.env              (PyInstaller onedir / distribution)
      2) <sys._MEIPASS>/.env                (PyInstaller onefile)
      3) <cwd>/.env                         (development fallback)

    Raises:
        ValueError: if required variables are missing after loading.
    """
    meipass = getattr(sys, "_MEIPASS", None)

    candidates = [
        executable_dir() / ".env",
        Path(meipass) / ".env" if meipass else None,
        Path.cwd() / ".env",
    ]

    for env_path in [p for p in candidates if p is not None]:
        load_env_file(env_path)

    required = ("DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(
            f"Missing required database environment variables: {', '.join(missing)}"
        )

    return AppConfig(
        db_name=os.environ["DB_NAME"],
        db_user=os.environ["DB_USER"],
        db_password=os.environ["DB_PASSWORD"],
        db_host=os.getenv("DB_HOST", "localhost"),
        db_port=int(os.getenv("DB_PORT", "5432")),
    )

