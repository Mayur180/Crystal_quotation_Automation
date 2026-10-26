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


# ============================================================
# ROLE / ADMIN HELPERS
# ============================================================

def is_admin(user_or_username) -> bool:
    if isinstance(user_or_username, dict):
        return (user_or_username.get("role") or "").lower() == "admin"
    u = find_user_by_username(str(user_or_username))
    return bool(u) and (u.get("role") or "").lower() == "admin"


def get_role(user_id: str) -> str:
    u = find_user_by_id(user_id)
    return (u.get("role") or "user").lower() if u else ""


# ============================================================
# CREATE / UPDATE / DEACTIVATE / PASSWORD
# ============================================================

def _next_user_id() -> str:
    existing = {u.get("user_id", "") for u in load_users()}
    i = 1
    while True:
        candidate = f"U{i:03d}"
        if candidate not in existing:
            return candidate
        i += 1


def create_user(*, username, password, full_name="", role="user",
                modules=None, created_by=""):
    import datetime
    username = (username or "").strip()
    password = (password or "").strip()
    role = (role or "user").strip().lower()

    if not username:
        raise ValueError("Username is required.")
    if not password:
        raise ValueError("Password is required.")
    if role not in ("admin", "user"):
        raise ValueError("Role must be 'admin' or 'user'.")
    if find_user_by_username(username):
        raise ValueError(f"Username '{username}' already exists.")

    # Hash the password with bcrypt
    import bcrypt
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user_id = _next_user_id()
    user = {
        "user_id":    user_id,
        "username":   username,
        "password":   hashed_password,
        "full_name":  full_name.strip() or username,
        "role":       role,
        "is_active":  True,
        "created_at": datetime.date.today().isoformat(),
        "created_by": created_by,
    }
    add_user(user)
    for mod in (modules or []):
        grant_module(user_id, mod)
    sync_user_to_sheet(user)
    return user


def update_user(user_id, **fields):
    allowed = {"full_name", "role", "is_active", "username", "password"}
    users = load_users()
    found = None
    for u in users:
        if u.get("user_id") == user_id:
            found = u
            break
    if not found:
        raise ValueError(f"User {user_id} not found.")

    if "role" in fields:
        role = (fields["role"] or "user").strip().lower()
        if role not in ("admin", "user"):
            raise ValueError("Role must be 'admin' or 'user'.")
        fields["role"] = role

    if "username" in fields:
        new_name = (fields["username"] or "").strip()
        if not new_name:
            raise ValueError("Username cannot be empty.")
        for u in users:
            if u.get("user_id") != user_id and \
               u.get("username", "").lower() == new_name.lower():
                raise ValueError(f"Username '{new_name}' already in use.")
        fields["username"] = new_name

    for k, v in fields.items():
        if k in allowed:
            if k == "password" and v:
                import bcrypt
                found[k] = bcrypt.hashpw(str(v).encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            else:
                found[k] = v

    save_users(users)
    sync_user_to_sheet(found)
    return found


def deactivate_user(user_id):
    users = load_users()
    target = next((u for u in users if u.get("user_id") == user_id), None)
    if not target:
        raise ValueError(f"User {user_id} not found.")
    if (target.get("role") or "user").lower() == "admin":
        active_admins = [
            u for u in users
            if u.get("is_active", True)
            and (u.get("role") or "").lower() == "admin"
            and u.get("user_id") != user_id
        ]
        if not active_admins:
            raise ValueError("Cannot deactivate the last active admin.")
    target["is_active"] = False
    save_users(users)
    sync_user_to_sheet(target)
    return target


def set_password(user_id, new_password):
    if not (new_password or "").strip():
        raise ValueError("Password cannot be empty.")
    users = load_users()
    found = None
    for u in users:
        if u.get("user_id") == user_id:
            found = u
            break
    if not found:
        raise ValueError(f"User {user_id} not found.")
    found["password"] = new_password.strip()
    save_users(users)
    return found


def set_user_modules(user_id, modules):
    for m in ("VMM", "Crystal"):
        revoke_module(user_id, m)
    for m in modules or []:
        if m in ("VMM", "Crystal"):
            grant_module(user_id, m)


def sync_user_to_sheet(user):
    try:
        import threading
        from app.services.google_sheet_service import send_to_sheet
        
        def _background_sync():
            try:
                send_to_sheet(user)
            except Exception as e:
                print(f"[sheet-sync] Background error: {e}")
        
        threading.Thread(target=_background_sync, daemon=True).start()
    except Exception as e:
        print(f"[sheet-sync] Import error: {e}")

def activate_user(user_id):
    """Mark a user active again."""
    users = load_users()
    target = next((u for u in users if u.get("user_id") == user_id), None)
    if not target:
        raise ValueError(f"User {user_id} not found.")
    target["is_active"] = True
    save_users(users)
    sync_user_to_sheet(target)
    return target


def delete_user(user_id, *, by_username=""):
    """Permanently remove a user and all their module permissions.

    Safety checks:
      - Cannot delete the last active admin.
      - Cannot delete yourself.
      - Cannot delete the base U001 'admin' account.
    """
    users = load_users()
    target = next((u for u in users if u.get("user_id") == user_id), None)
    if not target:
        raise ValueError(f"User {user_id} not found.")

    if by_username and target.get("username", "").lower() == by_username.lower():
        raise ValueError("You cannot delete your own account.")

    if target.get("user_id") == "U001":
        raise ValueError("The base admin account (U001) cannot be deleted.")

    if (target.get("role") or "user").lower() == "admin":
        other_admins = [
            u for u in users
            if u.get("user_id") != user_id
            and u.get("is_active", True)
            and (u.get("role") or "").lower() == "admin"
        ]
        if not other_admins:
            raise ValueError("Cannot delete the last active admin.")

    users = [u for u in users if u.get("user_id") != user_id]
    save_users(users)

    perms = [p for p in load_permissions() if p.get("user_id") != user_id]
    save_permissions(perms)

    return target


def fetch_users_from_sheet():
    """Fetch users from Google Sheets and update local Users.json.
    
    Returns True if successful, False otherwise.
    """
    try:
        import requests
        from app.services.google_sheet_service import WEBHOOK_URL
        from app.services.paths import get_data_root
        import json
        
        # Send GET request to fetch users
        response = requests.get(
            WEBHOOK_URL,
            params={"action": "get_users"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            sheet_users = data.get("users", [])
            
            # Merge sheet users with local users (sheet is master)
            local_users = load_users()
            local_by_id = {u.get("user_id"): u for u in local_users}
            
            merged = []
            for su in sheet_users:
                uid = su.get("user_id")
                if uid in local_by_id:
                    local_user = local_by_id[uid]
                    for key in ("username", "full_name", "role", "is_active", "modules"):
                        if key in su:
                            local_user[key] = su[key]
                    merged.append(local_user)
                else:
                    merged.append(su)
            
            # Add any local-only users (not in sheet yet)
            sheet_ids = {u.get("user_id") for u in sheet_users}
            for lu in local_users:
                if lu.get("user_id") not in sheet_ids:
                    merged.append(lu)
            
            if merged:
                save_users(merged)
            print(f"[user-sync] Fetched {len(sheet_users)} users from Google Sheets.")
            return True
    except Exception as e:
        print(f"[user-sync] Could not fetch users: {e}")
    
    return False
