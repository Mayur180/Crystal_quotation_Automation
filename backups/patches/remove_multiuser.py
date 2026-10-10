"""
Remove multi-user login from the entire project.
Reverts to single-user mode where the app just opens the dashboard.
"""

import shutil
import py_compile
from pathlib import Path


ROOT = Path.cwd()


def backup(p):
    b = p.with_suffix(p.suffix + ".MULTIUSER_REMOVED_BACKUP")
    if not b.exists():
        shutil.copy2(p, b)
        print(f"[backup] {p.name}")


# ============================================================
# 1. Rewrite main.py — no wizard, no setup
# ============================================================

main_py = ROOT / "main.py"
backup(main_py)

main_py.write_text('''"""
Crystal Quotation Automation — Windows Launcher
"""

import sys
from pathlib import Path


def _setup_paths():
    """Set up sys.path for frozen and script modes."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent

    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

    return base


def main():
    base = _setup_paths()

    try:
        from ui.dashboard import Dashboard
    except Exception:
        import traceback
        traceback.print_exc()
        return

    app = Dashboard()

    # Force window to appear on-screen
    try:
        app.update_idletasks()
        sw = app.winfo_screenwidth()
        sh = app.winfo_screenheight()
        w = 1280
        h = 820
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        app.geometry(f"{w}x{h}+{x}+{y}")
        app.deiconify()
        app.lift()
        app.attributes("-topmost", True)
        app.after(500, lambda: app.attributes("-topmost", False))
        app.focus_force()
    except Exception:
        pass

    app.mainloop()


if __name__ == "__main__":
    main()
''', encoding="utf-8")
print("[ok] main.py rewritten (no wizard)")


# ============================================================
# 2. Delete multi-user files
# ============================================================

for rel in [
    "app/services/setup_service.py",
    "app/services/user_service.py",
    "ui/setup_wizard.py",
    "ui/team_activity_window.py",
]:
    p = ROOT / rel
    if p.exists():
        # Move to backups instead of deleting
        dst = ROOT / "backups" / "old_restore_points" / p.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dst))
        print(f"[moved] {rel} -> backups/old_restore_points/")


# ============================================================
# 3. Patch paths.py — remove shared_path dependency
# ============================================================

paths_py = ROOT / "app" / "services" / "paths.py"
backup(paths_py)
s = paths_py.read_text(encoding="utf-8")

# Replace _setup_shared_path to always return None (no shared folder)
old_block = s[s.find("def _setup_shared_path():"):s.find("def _appdata_base")]
new_block = '''def _setup_shared_path():
    """Multi-user shared folder was removed — always return None."""
    return None


'''
if old_block and "def _appdata_base" in s:
    s = s.replace(old_block, new_block, 1)
    paths_py.write_text(s, encoding="utf-8")
    print("[ok] paths.py patched (no shared folder)")


# ============================================================
# 4. Patch activity_log_service.py — remove user_service import
# ============================================================

log_py = ROOT / "app" / "services" / "activity_log_service.py"
backup(log_py)
s = log_py.read_text(encoding="utf-8")

# Remove the user_service import block
old_import = """try:
    from app.services.user_service import get_current_user
except Exception:
    get_current_user = None"""
if old_import in s:
    s = s.replace(old_import, "get_current_user = None", 1)
    log_py.write_text(s, encoding="utf-8")
    print("[ok] activity_log_service.py patched")


# ============================================================
# 5. Patch dashboard.py — remove multi-user references
# ============================================================

dash_py = ROOT / "ui" / "dashboard.py"
backup(dash_py)
s = dash_py.read_text(encoding="utf-8")

# Remove user_service import
old1 = """# Phase 1 — current user
try:
    from app.services.user_service import get_current_user
except Exception:
    get_current_user = None
"""
if old1 in s:
    s = s.replace(old1, "get_current_user = None\n", 1)
    print("[ok] dashboard.py: removed user_service import")

# Remove Team Activity sidebar item + admin check
old2 = '''        # admin-only: Team Activity
        try:
            from app.services.user_service import is_admin
            _show_team = is_admin()
        except Exception:
            _show_team = False
        if _show_team:
            add_item("👨‍👩‍👧", "Team Activity",    self._open_team_activity)'''
if old2 in s:
    s = s.replace(old2, "", 1)
    print("[ok] dashboard.py: removed Team Activity item")

# Remove Reconfigure Setup item
old3 = '        add_item("🔧", "Reconfigure Setup",  self._reconfigure_setup)\n'
if old3 in s:
    s = s.replace(old3, "", 1)
    print("[ok] dashboard.py: removed Reconfigure Setup item")

# Remove _open_team_activity method
start = s.find("    def _open_team_activity(self):")
if start >= 0:
    end = s.find("    def ", start + 10)
    if end > start:
        s = s[:start] + s[end:]
        print("[ok] dashboard.py: removed _open_team_activity method")

# Remove _reconfigure_setup method
start = s.find("    def _reconfigure_setup(self):")
if start >= 0:
    end = s.find("    def ", start + 10)
    if end > start:
        s = s[:start] + s[end:]
        print("[ok] dashboard.py: removed _reconfigure_setup method")

dash_py.write_text(s, encoding="utf-8")


# ============================================================
# 6. Compile check
# ============================================================

print()
print("=" * 60)
print("Compile check")
print("=" * 60)

for p in [
    ROOT / "main.py",
    ROOT / "app" / "services" / "paths.py",
    ROOT / "app" / "services" / "activity_log_service.py",
    ROOT / "ui" / "dashboard.py",
]:
    try:
        py_compile.compile(str(p), doraise=True)
        print(f"[ok] {p.relative_to(ROOT)}")
    except py_compile.PyCompileError as e:
        print(f"[FAIL] {p.relative_to(ROOT)}: {e}")


print()
print("=" * 60)
print("Multi-user removed.")
print("=" * 60)
print()
print("Next steps:")
print("  1. python main.py  (test locally)")
print("  2. Rebuild EXE with PyInstaller")
print("  3. Copy folder to Invoice PC")
