"""Session persistence — remembers the last login on this PC."""
import json, datetime, socket, os
from pathlib import Path
from app.services.paths import get_data_dir


def _session_file() -> Path:
    return get_data_dir() / "session.json"


def save_session(session):
    """Write {user_id, username, full_name, timestamp, pc_name} to session.json."""
    try:
        data = {
            "user_id":   getattr(session, "user_id", ""),
            "username":  getattr(session, "username", ""),
            "full_name": getattr(session, "full_name", ""),
            "modules":   list(getattr(session, "modules", [])),
            "last_login": datetime.datetime.now().isoformat(),
            "pc_name":    socket.gethostname(),
        }
        p = _session_file()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data
    except Exception as e:
        print(f"[session] save failed: {e}")
        return None


def load_session():
    """Return the saved session dict, or None if not present."""
    try:
        p = _session_file()
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def clear_session():
    """Remove the saved session (used on logout)."""
    try:
        p = _session_file()
        if p.exists():
            p.unlink()
    except Exception:
        pass


def log_login_to_sheet(session):
    """Send a login event to the Google Sheet."""
    try:
        from app.services.google_sheet_service import send_to_sheet
        send_to_sheet({
            "action":     "login",
            "user_id":    getattr(session, "user_id", ""),
            "username":   getattr(session, "username", ""),
            "full_name":  getattr(session, "full_name", ""),
            "pc_name":    socket.gethostname(),
            "timestamp":  datetime.datetime.now().isoformat(),
        })
    except Exception as e:
        print(f"[session] log to sheet failed: {e}")
