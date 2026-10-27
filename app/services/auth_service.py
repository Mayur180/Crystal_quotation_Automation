"""
CRYSTAL / ARMATECH ASSOCIATES
Authentication service — v4.

Verifies login credentials and returns a session object.
Does NOT touch the UI. Called by login_window.py.
"""

from dataclasses import dataclass, field
from typing import Optional

from app.services.user_service import (
    find_user_by_username,
    get_user_modules,
)


# ============================================================
# SESSION OBJECT
# ============================================================

@dataclass
class UserSession:
    """Represents a logged-in user for the duration of the app session."""
    user_id: str
    username: str
    full_name: str
    modules: list[str] = field(default_factory=list)
    active_module: Optional[str] = None

    def has_module(self, module: str) -> bool:
        return module in self.modules

    def is_multi_module(self) -> bool:
        return len(self.modules) > 1

    def __repr__(self) -> str:
        return f"UserSession({self.username}, modules={self.modules})"


# ============================================================
# AUTHENTICATION
# ============================================================

def verify_credentials(username: str, password: str) -> Optional[UserSession]:
    """
    Verify username + password.

    Returns:
        UserSession on success
        None on failure (bad username, wrong password, inactive account)
    """
    if not username or not password:
        return None

    user = find_user_by_username(username)
    if not user:
        return None

    if not user.get("is_active", True):
        return None

    import bcrypt
    stored = user.get("password", "")
    if not stored:
        return None
    try:
        if not bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8')):
            return None
    except Exception:
        # Fallback to plain text for legacy users not yet migrated
        if stored != password:
            return None

    modules = get_user_modules(user["user_id"])
    if not modules:
        # User exists but has zero module access — reject
        return None

    session = UserSession(
        user_id=user["user_id"],
        username=user["username"],
        full_name=user.get("full_name", user["username"]),
        modules=modules,
        active_module=None,
    )
    
    # Log this login to Google Sheets (background thread, non-blocking)
    _log_login_to_sheet(session)
    
    return session


# ============================================================
# ERROR MESSAGES (for UI)
# ============================================================

def _log_login_to_sheet(session: UserSession) -> None:
    """Log a successful login to Google Sheets (background thread)."""
    try:
        import threading
        import socket
        from app.services.google_sheet_service import send_to_sheet
        
        def _background_log():
            try:
                pc_name = socket.gethostname()
                send_to_sheet({
                    "action": "login",
                    "user_id": session.user_id,
                    "username": session.username,
                    "full_name": session.full_name,
                    "pc_name": pc_name,
                })
            except Exception as e:
                print(f"[login-log] Background error: {e}")
        
        threading.Thread(target=_background_log, daemon=True).start()
    except Exception as e:
        print(f"[login-log] Could not start thread: {e}")


def describe_login_failure(username: str, password: str) -> str:
    """Return a human-friendly error message for a failed login attempt."""
    if not username or not password:
        return "Please enter both username and password."

    user = find_user_by_username(username)
    if not user:
        return "Invalid username or password."
    if not user.get("is_active", True):
        return "This account has been deactivated. Contact admin."
    import bcrypt
    stored = user.get("password", "")
    try:
        if stored.startswith("$2"):
            if not bcrypt.checkpw(password.encode('utf-8'), stored.encode('utf-8')):
                return "Invalid username or password."
        elif stored != password:
            return "Invalid username or password."
    except Exception:
        return "Invalid username or password."
    if not get_user_modules(user["user_id"]):
        return "No modules assigned to this account. Contact admin."

    return "Login failed. Contact admin."
