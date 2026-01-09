from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """Return the project root folder in development mode.

    This file must live in the project root (same level as main.py).
    """
    return Path(__file__).resolve().parent


def runtime_root() -> Path:
    """Return the runtime root folder for resolving bundled resources.

    Rules:
    - PyInstaller onefile: resources are extracted to sys._MEIPASS
    - PyInstaller onedir: resources live next to the executable (sys.executable parent)
    - Development: project root
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return project_root()


def resource_path(*parts: str) -> str:
    """Build an absolute path to a bundled resource.

    Examples:
        resource_path("assets", "quiz_app.png")
        resource_path("assets", "quiz_app.ico")
    """
    return str(runtime_root().joinpath(*parts))


def env_path() -> str:
    """Return the .env path used by the application.

    Priority:
    1) .env next to the executable (onedir distribution-friendly)
    2) .env inside sys._MEIPASS (onefile bundled data)
    3) .env in project root (development fallback)
    """
    if getattr(sys, "frozen", False):
        exe_env = Path(sys.executable).resolve().parent / ".env"
        if exe_env.exists():
            return str(exe_env)

        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled_env = Path(meipass) / ".env"
            if bundled_env.exists():
                return str(bundled_env)

    return str(project_root() / ".env")


def app_icon_path() -> str:
    """Return the best available icon path for the current platform."""
    ico = Path(resource_path("assets", "quiz_app.ico"))
    if ico.exists():
        return str(ico)

    return str(Path(resource_path("assets", "quiz_app.png")))

