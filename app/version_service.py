"""Version identity and on-disk install marker.

The marker lives at <data>/version.json (next to the EXE when frozen) and lets
the updater know which version is installed. It is only written by frozen
builds so running from source never leaves state in the repo's data folder.
"""
import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from app.config import APP_VERSION, APP_VERSION_NAME


def version_label() -> str:
    return f"v{APP_VERSION}"


def marker_path() -> Path:
    from app.services.paths import get_data_root
    return get_data_root() / "version.json"


def read_marker() -> dict:
    try:
        data = json.loads(marker_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".version-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_startup_marker() -> None:
    """Record the running version. Skipped for source checkouts."""
    if not getattr(sys, "frozen", False):
        return
    try:
        data = read_marker()
        now = _now()
        recorded = str(data.get("version") or "")
        if recorded != APP_VERSION:
            if recorded:
                data["previous_version"] = recorded
            data["installed_at"] = now
        data["version"] = APP_VERSION
        data["version_name"] = APP_VERSION_NAME
        data["last_launch"] = now
        data["app_exe"] = sys.executable
        _write_json_atomic(marker_path(), data)
    except Exception:
        pass
