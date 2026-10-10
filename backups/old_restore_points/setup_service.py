"""
CRYSTAL / ARMATECH ASSOCIATES
Setup service — first-run configuration.

Stores:
  %APPDATA%/CRYSTAL/setup.json
    {
      "user_name":  "Mayuresh",
      "pc_role":    "admin" | "member",
      "server_pc":  "Invoice",
      "shared_path":"D:\\CRYSTAL_data"  or  "\\\\Invoice\\CRYSTAL_data",
      "configured_at": "2026-10-06T20:00:00"
    }
"""

import os
import json
import socket
from pathlib import Path
from datetime import datetime


DEFAULT_SERVER_PC = "Invoice"
DEFAULT_SHARED_FOLDER = "CRYSTAL_data"


def _appdata_dir() -> Path:
    base = Path(os.environ.get("APPDATA", str(Path.home()))) / "CRYSTAL"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _setup_file() -> Path:
    return _appdata_dir() / "setup.json"


def load_setup():
    """Return the saved setup dict, or None if not configured yet."""
    try:
        f = _setup_file()
        if not f.is_file():
            return None
        data = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "user_name" not in data:
            return None
        return data
    except Exception:
        return None


def save_setup(data):
    """Persist the setup dict to disk."""
    try:
        payload = dict(data)
        payload["configured_at"] = datetime.now().isoformat(timespec="seconds")
        _setup_file().write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def clear_setup():
    """Remove the setup file — forces wizard to show again."""
    try:
        f = _setup_file()
        if f.is_file():
            f.unlink()
        return True
    except Exception:
        return False


def is_configured() -> bool:
    return load_setup() is not None


def current_role() -> str:
    """Return 'admin' or 'member'."""
    s = load_setup()
    return (s or {}).get("pc_role", "member")


def is_admin() -> bool:
    return current_role() == "admin"


def current_user():
    s = load_setup()
    return (s or {}).get("user_name") or None


def shared_path():
    """Return the Path to the shared data folder, or None."""
    s = load_setup()
    if not s:
        return None
    p = s.get("shared_path")
    if not p:
        return None
    try:
        return Path(p)
    except Exception:
        return None


def shared_path_available() -> bool:
    """Check if the shared folder exists and is reachable."""
    p = shared_path()
    if p is None:
        return False
    try:
        return p.is_dir()
    except Exception:
        return False


def build_shared_path(role, server_pc=None, custom_path=None):
    """Build the shared_path for the given role.

    - admin:   D:\\CRYSTAL_data  (or custom_path)
    - member:  \\\\<server_pc>\\CRYSTAL_data
    """
    if custom_path:
        return custom_path.strip()
    if role == "admin":
        return "D:\\" + DEFAULT_SHARED_FOLDER
    # member
    server = (server_pc or DEFAULT_SERVER_PC).strip()
    return "\\\\" + server + "\\" + DEFAULT_SHARED_FOLDER
