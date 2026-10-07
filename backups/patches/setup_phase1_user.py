"""
Multi-user Phase 1 — user login + sidebar name.

Creates app/services/user_service.py
Patches main.py to show login dialog
Patches ui/dashboard.py to show current user
"""

import shutil
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SERVICES = ROOT / "app" / "services"
UI = ROOT / "ui"


# ============================================================
# 1. Create app/services/user_service.py
# ============================================================

USER_SERVICE = '''"""
CRYSTAL / ARMATECH ASSOCIATES
User tracking service.

Stores the current user's name in %APPDATA%/CRYSTAL/user.txt
so every action can be tagged with who did it.
"""

import os
from pathlib import Path


def _appdata_dir() -> Path:
    base = Path(os.environ.get("APPDATA", str(Path.home()))) / "CRYSTAL"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _user_file() -> Path:
    return _appdata_dir() / "user.txt"


def get_current_user():
    """Return the saved username, or None if not set."""
    try:
        f = _user_file()
        if f.is_file():
            name = f.read_text(encoding="utf-8").strip()
            return name or None
    except Exception:
        pass
    return None


def set_current_user(name):
    """Save the username to disk."""
    try:
        name = (name or "").strip()
        if not name:
            return False
        _user_file().write_text(name, encoding="utf-8")
        return True
    except Exception:
        return False


def clear_current_user():
    """Remove the saved username."""
    try:
        f = _user_file()
        if f.is_file():
            f.unlink()
        return True
    except Exception:
        return False


def is_admin():
    """True if this PC is the designated admin PC.

    Reads admin.txt from the same folder. If the file doesn't exist,
    we treat the current user as admin (single-PC mode).
    """
    try:
        f = _appdata_dir() / "admin_pc.txt"
        if not f.is_file():
            return True  # default: single-PC → admin
        return f.read_text(encoding="utf-8").strip().lower() == "yes"
    except Exception:
        return True
'''

f = SERVICES / "user_service.py"
if f.exists():
    print(f"[skip] {f.name} already exists")
else:
    f.write_text(USER_SERVICE, encoding="utf-8")
    print(f"[new]  {f.relative_to(ROOT)}")


# ============================================================
# 2. Patch main.py to ask for username on startup
# ============================================================

MAIN = ROOT / "main.py"
shutil.copy2(MAIN, MAIN.with_suffix(".py.PHASE1_BACKUP"))
print(f"[backup] {MAIN.name}")

m = MAIN.read_text(encoding="utf-8")

# Look for "def main" or the entry point call
if "from app.services.user_service import" not in m:
    # insert an import at the top (after the first import block)
    lines = m.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_idx = i + 1
    lines.insert(insert_idx, "\n# Phase 1 — user login\ntry:\n    from app.services.user_service import (\n        get_current_user, set_current_user,\n    )\nexcept Exception:\n    get_current_user = None\n    set_current_user = None\n")
    m = "\n".join(lines)
    print("[ok] main.py: import added")

# Insert a call to a show_login helper before Dashboard()
if "_ensure_user_login" not in m:
    helper = '''

def _ensure_user_login():
    """Show a small dialog asking for the user's name if not already set."""
    if get_current_user is None or set_current_user is None:
        return
    if get_current_user():
        return  # already logged in
    try:
        import tkinter as tk
        from tkinter import simpledialog

        root = tk.Tk()
        root.withdraw()
        name = simpledialog.askstring(
            "Welcome to CRYSTAL",
            "Enter your name:",
            parent=root,
        )
        root.destroy()
        if name:
            set_current_user(name)
    except Exception:
        pass

'''
    # insert before "if __name__" or "def main"
    if 'if __name__ == "__main__":' in m:
        m = m.replace(
            'if __name__ == "__main__":',
            helper + '\nif __name__ == "__main__":',
            1,
        )
    elif "def main(" in m:
        m = m.replace("def main(", helper + "\ndef main(", 1)
    print("[ok] main.py: _ensure_user_login helper added")

# Call it right before the dashboard is created
if "_ensure_user_login()" not in m.split("def _ensure_user_login")[0]:
    # find "Dashboard()" call and insert before it
    for anchor in ["app = Dashboard(", "root = Dashboard(", "Dashboard()"]:
        if anchor in m:
            m = m.replace(anchor, "_ensure_user_login()\n\n    " + anchor, 1)
            print(f"[ok] main.py: _ensure_user_login called before {anchor}")
            break

MAIN.write_text(m, encoding="utf-8")


# ============================================================
# 3. Patch dashboard.py to show current user in sidebar
# ============================================================

DASH = UI / "dashboard.py"
shutil.copy2(DASH, DASH.with_suffix(".py.PHASE1_BACKUP"))
print(f"[backup] {DASH.name}")

d = DASH.read_text(encoding="utf-8")

# Add import at the top
if "from app.services.user_service import get_current_user" not in d:
    lines = d.split("\n")
    insert_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            insert_idx = i + 1
    lines.insert(
        insert_idx,
        "\n# Phase 1 — current user\ntry:\n    from app.services.user_service import get_current_user\nexcept Exception:\n    get_current_user = None\n",
    )
    d = "\n".join(lines)
    print("[ok] dashboard.py: import added")

# Add a "Signed in as" line just before the Quit item in the sidebar
old = '''        add_item("🗑",  "Clear Activity Log", self._clear_activity_log,
                 danger=True)
        add_item("🚪", "Quit",               self._quit, danger=True)'''

new = '''        # ---- signed-in user label ----
        try:
            user = get_current_user() if get_current_user else None
        except Exception:
            user = None
        if user:
            user_lbl = tk.Label(
                self._sidebar,
                text=f"Signed in as: {user}",
                bg=self.CARD, fg=self.MUTED,
                font=("Arial", 8, "italic"),
                anchor="w",
            )
            user_lbl.pack(fill="x", padx=18, pady=(4, 4))

        add_item("🗑",  "Clear Activity Log", self._clear_activity_log,
                 danger=True)
        add_item("🚪", "Quit",               self._quit, danger=True)'''

if "Signed in as:" not in d and old in d:
    d = d.replace(old, new, 1)
    print("[ok] dashboard.py: 'Signed in as' label added")
elif "Signed in as:" in d:
    print("[skip] dashboard.py: label already present")
else:
    print("[warn] dashboard.py: sidebar anchor not found")

DASH.write_text(d, encoding="utf-8")


# ============================================================
# 4. Compile check
# ============================================================

print()
print("=" * 60)
print("Compile check")
print("=" * 60)

failed = False
for p in [f, MAIN, DASH]:
    try:
        py_compile.compile(str(p), doraise=True)
        print(f"[ok] {p.relative_to(ROOT)}")
    except py_compile.PyCompileError as e:
        print(f"[FAIL] {p.relative_to(ROOT)}: {e}")
        failed = True

if failed:
    print()
    print("Some files failed — restore from *.PHASE1_BACKUP if needed.")
else:
    print()
    print("=" * 60)
    print("Phase 1 complete.")
    print("=" * 60)
    print()
    print("Test:")
    print("  1. python main.py")
    print("  2. Enter your name when prompted")
    print("  3. Sidebar shows 'Signed in as: <name>'")
