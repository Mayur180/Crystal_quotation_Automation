import shutil
import py_compile
from pathlib import Path

MAIN = Path("main.py")
shutil.copy2(MAIN, MAIN.with_suffix(".py.REMOVE_LOGIN_BACKUP"))
print(f"[backup] {MAIN.name}")

s = MAIN.read_text(encoding="utf-8")

# --- 1. Remove the _ensure_user_login() call in main() ---
old_call = "    _ensure_user_login()\n\n    _ensure_first_run_setup()"
new_call = "    _ensure_first_run_setup()"
if old_call in s:
    s = s.replace(old_call, new_call, 1)
    print("[ok] removed _ensure_user_login() call")
else:
    print("[warn] call pattern not found")

# --- 2. Remove the old _ensure_user_login function definition ---
old_func = '''def _ensure_user_login():
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
if old_func in s:
    s = s.replace(old_func, "", 1)
    print("[ok] removed _ensure_user_login function")
else:
    print("[warn] function pattern not found")

# --- 3. Remove Phase 1 import block ---
old_import = '''# Phase 1 — user login
try:
    from app.services.user_service import (
        get_current_user, set_current_user,
    )
except Exception:
    get_current_user = None
    set_current_user = None


'''
if old_import in s:
    s = s.replace(old_import, "", 1)
    print("[ok] removed Phase 1 import block")
else:
    print("[warn] import block pattern not found")

MAIN.write_text(s, encoding="utf-8")

# --- compile ---
print()
try:
    py_compile.compile(str(MAIN), doraise=True)
    print("[check] main.py compiles OK")
except py_compile.PyCompileError as e:
    print(f"[check] FAIL: {e}")
    shutil.copy2(MAIN.with_suffix(".py.REMOVE_LOGIN_BACKUP"), MAIN)
    print("[restore] reverted")
