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

    if user.get("password") != password:
        return None

    modules = get_user_modules(user["user_id"])
    if not modules:
        # User exists but has zero module access — reject
        return None

    return UserSession(
        user_id=user["user_id"],
        username=user["username"],
        full_name=user.get("full_name", user["username"]),
        modules=modules,
        active_module=None,
    )


# ============================================================
# ERROR MESSAGES (for UI)
# ============================================================

def describe_login_failure(username: str, password: str) -> str:
    """Return a human-friendly error message for a failed login attempt."""
    if not username or not password:
        return "Please enter both username and password."

    user = find_user_by_username(username)
    if not user:
        return "Invalid username or password."
    if not user.get("is_active", True):
        return "This account has been deactivated. Contact admin."
    if user.get("password") != password:
        return "Invalid username or password."
    if not get_user_modules(user["user_id"]):
        return "No modules assigned to this account. Contact admin."

    return "Login failed. Contact admin."
