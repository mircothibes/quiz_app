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

    - Dev mode: directory of this file (project folder).
    - PyInstaller onedir: directory containing the executable.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def runtime_root() -> Path:
    """Return the runtime root folder.

    - PyInstaller onefile: sys._MEIPASS (temporary extraction folder)
    - Otherwise: executable_dir()
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return executable_dir()


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
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


def _env_candidates() -> list[Path]:
    """Return .env candidate paths in priority order.

    Priority is important because we do NOT override existing os.environ values.
    We load the most likely location first.
    """
    exe_dir = executable_dir()
    root = runtime_root()

    candidates: list[Path] = []

    # 1) Most common on Linux/WSL PyInstaller onedir output:
    #    dist/<AppName>/_internal/.env
    candidates.append(exe_dir / "_internal" / ".env")

    # 2) Next to the executable (less common on Linux/WSL but valid)
    candidates.append(exe_dir / ".env")

    # 3) PyInstaller onefile extraction folder
    candidates.append(root / ".env")
    candidates.append(root / "_internal" / ".env")

    # 4) Dev fallback: current working directory
    candidates.append(Path.cwd() / ".env")

    # De-duplicate while preserving order
    unique: list[Path] = []
    seen: set[str] = set()
    for p in candidates:
        s = str(p)
        if s not in seen:
            seen.add(s)
            unique.append(p)

    return unique


def load_config() -> AppConfig:
    """Load config from environment and/or a .env file.

    Search order:
      1) <executable_dir>/_internal/.env    (PyInstaller onedir on Linux/WSL)
      2) <executable_dir>/.env
      3) <sys._MEIPASS>/.env               (PyInstaller onefile)
      4) <sys._MEIPASS>/_internal/.env
      5) <cwd>/.env                        (development fallback)

    Raises:
        ValueError: If required variables are missing after loading.
    """
    for env_path in _env_candidates():
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


