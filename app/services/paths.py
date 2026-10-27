"""
CRYSTAL / ARMATECH ASSOCIATES
Path resolution helper — v4 multi-module aware.
"""

import os
import sys
from pathlib import Path


# ============================================================
# ACTIVE MODULE STATE
# ============================================================

_ACTIVE_MODULE = "VMM"   # Default keeps backward compatibility

VALID_MODULES = ("VMM", "Crystal")


def set_active_module(module_name: str) -> None:
    global _ACTIVE_MODULE
    if module_name not in VALID_MODULES:
        raise ValueError(f"Unknown module: {module_name!r}")
    _ACTIVE_MODULE = module_name


def get_active_module() -> str:
    return _ACTIVE_MODULE


# ============================================================
# CORE PATH RESOLUTION
# ============================================================

def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _project_base() -> Path:
    return Path(__file__).resolve().parents[2]


def _runtime_data_dir() -> Path:
    exe_dir = Path(sys.executable).resolve().parent
    d = exe_dir / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_data_root() -> Path:
    if is_frozen():
        d = _runtime_data_dir()
    else:
        d = _project_base() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_data_dir() -> Path:
    d = get_data_root() / get_active_module()
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_output_dir() -> Path:
    if is_frozen():
        base = Path(sys.executable).resolve().parent / "output"
    else:
        base = _project_base() / "output"
    d = base / get_active_module()
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_project_root() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return _project_base()


# ============================================================
# FROZEN EXE SEEDING
# ============================================================

def seed_data_on_first_run() -> None:
    if not is_frozen():
        return
    try:
        import shutil
        target = _runtime_data_dir()
        if hasattr(sys, "_MEIPASS"):
            bundled = Path(sys._MEIPASS) / "data"
        else:
            bundled = get_project_root() / "data"
        if not bundled.is_dir():
            return
        for item in bundled.rglob("*"):
            if item.is_dir():
                continue
            rel = item.relative_to(bundled)
            dest = target / rel
            if dest.exists():
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)
    except Exception:
        pass
