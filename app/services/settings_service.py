"""
CRYSTAL / ARMATECH ASSOCIATES
Application Settings Service

Stores user preferences (like output folder) in:
    %APPDATA%\\CrystalQuotation\\settings.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


# ============================================================
# PATHS
# ============================================================

def _settings_dir() -> Path:
    """Return the app data folder (per-user)."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "CrystalQuotation"
    # Fallback for non-Windows
    return Path.home() / ".crystalquotation"


def _settings_file() -> Path:
    return _settings_dir() / "settings.json"


# ============================================================
# DEFAULTS
# ============================================================

def default_output_folder() -> Path:
    """Default output folder — user's Downloads/CrystalQuotation."""
    return Path.home() / "Downloads" / "CrystalQuotation"


# ============================================================
# NETWORK PATH HELPERS
# ============================================================

def normalize_path(folder) -> str:
    """Clean up a folder path. Handles forward slashes and UNC."""
    if folder is None:
        return ""

    raw = str(folder).strip()
    if not raw:
        return ""

    # Convert forward slashes to backslashes
    raw = raw.replace("/", "\\")

    # Collapse multiple backslashes into one (except leading UNC)
    is_unc = raw.startswith("\\\\")

    # Split into parts by backslash, dropping empties
    parts = [p for p in raw.split("\\") if p]

    if is_unc:
        return "\\\\" + "\\".join(parts)
    return "\\".join(parts)


def is_network_path(folder) -> bool:
    """True if folder is a network path starting with two backslashes or //"""
    if folder is None:
        return False
    raw = str(folder).strip()
    return raw.startswith("\\\\") or raw.startswith("//")


def is_folder_available(folder) -> bool:
    """Check if a folder exists and is reachable."""
    if folder is None:
        return False
    try:
        p = Path(folder)
        if not p.is_dir():
            return False
        # Try listing to detect unreachable network paths
        next(iter(p.iterdir()), None)
        return True
    except Exception:
        return False


def try_create_folder(folder) -> bool:
    """Attempt to create the folder. Returns True on success."""
    try:
        Path(folder).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False



# ============================================================
# LOAD / SAVE
# ============================================================

def load_settings() -> dict:
    """Read settings.json; return {} if missing or invalid."""
    path = _settings_file()
    if not path.is_file():
        return {}

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {}


def save_settings(data: dict) -> bool:
    """Write settings.json atomically."""
    try:
        sdir = _settings_dir()
        sdir.mkdir(parents=True, exist_ok=True)

        tmp = _settings_file().with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, _settings_file())
        return True
    except Exception:
        return False


# ============================================================
# PUBLIC API
# ============================================================

def has_settings() -> bool:
    """True if a settings file with an output folder exists."""
    data = load_settings()
    return bool(data.get("output_folder"))


def get_output_folder() -> Path:
    """Return the user's chosen output folder (or default)."""
    data = load_settings()
    raw = data.get("output_folder")

    if raw:
        normalized = normalize_path(raw)
        if normalized:
            return Path(normalized)

    return default_output_folder()


def set_output_folder(folder: Path | str) -> bool:
    """Save the chosen output folder (normalized)."""
    data = load_settings()
    normalized = normalize_path(folder)
    data["output_folder"] = normalized
    return save_settings(data)


def is_confirmed() -> bool:
    """
    True if the user has explicitly chosen an output folder.
    Used to decide whether to show the first-run picker.
    """
    data = load_settings()
    return bool(data.get("confirmed"))


def mark_confirmed() -> bool:
    """Mark settings as confirmed so the picker never shows again."""
    data = load_settings()
    data["confirmed"] = True
    return save_settings(data)


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    print("Settings file:", _settings_file())
    print("Has settings:", has_settings())
    print("Output folder:", get_output_folder())
