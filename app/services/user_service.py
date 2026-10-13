"""
CRYSTAL / ARMATECH ASSOCIATES
User database service — v4 multi-module.

Reads/writes:
  data/Users.json         — user accounts
  data/User_Access.json   — which user can access which module

Note: These files live at data/ root (NOT per-module), because
they are shared across all modules.
"""

import json
from pathlib import Path
from typing import Optional

from app.services.paths import get_data_root


# ============================================================
# FILE PATHS
# ============================================================

def _users_file() -> Path:
    return get_data_root() / "Users.json"


def _access_file() -> Path:
    return get_data_root() / "User_Access.json"


# ============================================================
# USERS
# ============================================================

def load_users() -> list[dict]:
    """Load all users from Users.json. Returns [] if file missing."""
    p = _users_file()
    if not p.exists():
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("users", [])
    except Exception:
        return []


def save_users(users: list[dict]) -> None:
    """Write all users back to Users.json."""
    p = _users_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"users": users}, f, indent=2)


def find_user_by_username(username: str) -> Optional[dict]:
    """Find a single user by username (case-insensitive)."""
    if not username:
        return None
    target = username.strip().lower()
    for u in load_users():
        if u.get("username", "").lower() == target:
            return u
    return None


def find_user_by_id(user_id: str) -> Optional[dict]:
    for u in load_users():
        if u.get("user_id") == user_id:
            return u
    return None


def add_user(user: dict) -> None:
    """Append a new user (assumes user_id is unique)."""
    users = load_users()
    users.append(user)
    save_users(users)


# ============================================================
# PERMISSIONS
# ============================================================

def load_permissions() -> list[dict]:
    p = _access_file()
    if not p.exists():
        return []
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("permissions", [])
    except Exception:
        return []


def save_permissions(perms: list[dict]) -> None:
    p = _access_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"permissions": perms}, f, indent=2)


def get_user_modules(user_id: str) -> list[str]:
    """Return list of module names this user can access, e.g. ['VMM', 'Crystal']."""
    modules = []
    for p in load_permissions():
        if p.get("user_id") == user_id:
            mod = p.get("module")
            if mod and mod not in modules:
                modules.append(mod)
    return modules


def grant_module(user_id: str, module: str) -> None:
    """Grant a user access to a module (idempotent)."""
    perms = load_permissions()
    for p in perms:
        if p.get("user_id") == user_id and p.get("module") == module:
            return  # already granted
    perms.append({"user_id": user_id, "module": module})
    save_permissions(perms)


def revoke_module(user_id: str, module: str) -> None:
    perms = [p for p in load_permissions()
             if not (p.get("user_id") == user_id and p.get("module") == module)]
    save_permissions(perms)
