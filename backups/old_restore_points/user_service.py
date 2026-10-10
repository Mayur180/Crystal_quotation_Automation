"""
CRYSTAL / ARMATECH ASSOCIATES
User tracking service — reads from setup.json.
"""

try:
    from app.services.setup_service import (
        current_user as _su_current_user,
        current_role as _su_current_role,
        is_admin as _su_is_admin,
    )
except Exception:
    _su_current_user = lambda: None
    _su_current_role = lambda: "member"
    _su_is_admin = lambda: False


def get_current_user():
    try:
        return _su_current_user()
    except Exception:
        return None


def current_role():
    try:
        return _su_current_role()
    except Exception:
        return "member"


def is_admin():
    try:
        return _su_is_admin()
    except Exception:
        return False


# Backwards-compat no-ops (older code may still call these)
def set_current_user(name):
    try:
        from app.services.setup_service import (
            load_setup, save_setup,
        )
        s = load_setup() or {}
        s["user_name"] = (name or "").strip()
        return save_setup(s)
    except Exception:
        return False


def clear_current_user():
    try:
        from app.services.setup_service import clear_setup
        return clear_setup()
    except Exception:
        return False
