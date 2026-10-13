"""
CRYSTAL / ARMATECH ASSOCIATES
Path resolution helper.

Data source priority:
  1. setup.json's shared_path   (multi-PC mode)
  2. %APPDATA%/CRYSTAL/data     (frozen EXE fallback)
  3. <project>/data             (source mode)
"""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _setup_shared_path():
    """Multi-user shared folder was removed — always return None."""
    return None


def _appdata_base() -> Path:
    base = Path(os.environ.get("APPDATA", str(Path.home()))) / "CRYSTAL"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _project_base() -> Path:
    return Path(__file__).resolve().parents[2]


def _runtime_data_dir() -> Path:
    """Portable data dir next to the EXE when frozen.

    Keeps `data/` sitting beside CRYSTALQuotation.exe so the whole
    folder (exe + data) can be copied to another PC as a unit, and
    so users can edit catalog.json without rebuilding.
    """
    exe_dir = Path(sys.executable).resolve().parent
    d = exe_dir / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_data_dir() -> Path:
    """Where the JSON/JSONL data lives."""
    sp = _setup_shared_path()
    if sp is not None:
        sp.mkdir(parents=True, exist_ok=True)
        return sp
    if is_frozen():
        d = _runtime_data_dir()
    else:
        d = _project_base() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_output_dir() -> Path:
    """Where generated DOCX/PDF files go."""
    sp = _setup_shared_path()
    if sp is not None:
        d = sp / "output"
        d.mkdir(parents=True, exist_ok=True)
        return d
    if is_frozen():
        exe_dir = Path(sys.executable).resolve().parent
        d = exe_dir / "output"
    else:
        d = _project_base() / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_project_root() -> Path:
    """For code that needs project root (assets, etc.)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return _project_base()


def seed_data_on_first_run():
    """Copy bundled default data into <exe_dir>/data on first run.

    Runs only when frozen. Missing files are copied; existing files
    are left untouched so user edits are preserved across upgrades.
    """
    if not is_frozen():
        return
    try:
        import shutil

        target = _runtime_data_dir()

        # Source: data bundled inside the EXE at build time
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
