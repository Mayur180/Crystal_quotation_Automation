"""Session persistence — remembers the last login on this PC.

The saved file holds a random device token and an expiry date; the
password is never stored. After SESSION_DAYS the user logs in again.
"""
import datetime
import json
import secrets
import socket

from app.services.paths import get_data_root


SESSION_DAYS = 30
_TOKEN_BYTES = 24


def _session_file():
    return get_data_root() / "session.json"


def _now():
    return datetime.datetime.now()


def save_session(session):
    """Write the auto-login record for this PC. Returns the saved dict."""
    try:
        now = _now()
        data = {
            "token":     secrets.token_hex(_TOKEN_BYTES),
            "user_id":   getattr(session, "user_id", ""),
            "username":  getattr(session, "username", ""),
            "full_name": getattr(session, "full_name", ""),
            "modules":   list(getattr(session, "modules", []) or []),
            "pc_name":   socket.gethostname(),
            "created_at": now.isoformat(timespec="seconds"),
            "expires_at": (now + datetime.timedelta(days=SESSION_DAYS))
                          .isoformat(timespec="seconds"),
        }
        p = _session_file()
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(p)
        return data
    except Exception as e:
        print(f"[session] save failed: {e}")
        return None


def load_session():
    """Return the saved session dict, or None if absent/invalid/expired."""
    try:
        p = _session_file()
        if not p.exists():
            return None
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not data.get("username"):
            raise ValueError("incomplete session")
        if not data.get("token"):
            raise ValueError("no token")

        expires = data.get("expires_at")
        if not expires:
            raise ValueError("no expiry")
        expiry = datetime.datetime.fromisoformat(expires)
        if expiry <= _now():
            raise ValueError("expired")

        return data
    except Exception as e:
        print(f"[session] saved session cleared: {e}")
        clear_session()
        return None


def clear_session():
    """Remove the saved session (used on logout / invalid token)."""
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
