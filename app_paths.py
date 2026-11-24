from pathlib import Path
import os
import sys


def app_dir() -> Path:
    """Return the writable application directory (next to the script/executable)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def asset_path(name: str) -> Path:
    """Resolve bundled read-only assets, including PyInstaller one-file builds."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / name
    return app_dir() / name



def data_dir() -> Path:
    """Return a writable per-user directory for settings and runtime state."""
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA")
        if base:
            return Path(base) / "HandGameController"
        return Path.home() / "AppData" / "Local" / "HandGameController"
    return app_dir()
