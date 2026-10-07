"""
Multi-user Phase 2 — tag every activity log event with the current user.

Patches app/services/activity_log_service.py so log_event() automatically
picks up the current user from user_service when user=None.
"""

import shutil
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_SVC = ROOT / "app" / "services" / "activity_log_service.py"


shutil.copy2(LOG_SVC, LOG_SVC.with_suffix(".py.PHASE2_BACKUP"))
print(f"[backup] {LOG_SVC.name}")

s = LOG_SVC.read_text(encoding="utf-8")

# ---- 1. Import user_service at the top ----
if "from app.services.user_service import" not in s:
    anchor = "from datetime import datetime"
    if anchor in s:
        s = s.replace(
            anchor,
            anchor + "\n\ntry:\n    from app.services.user_service import get_current_user\nexcept Exception:\n    get_current_user = None",
            1,
        )
        print("[ok] import: user_service.get_current_user")
    else:
        print("[warn] 'from datetime import datetime' not found")

# ---- 2. Modify log_event to fall back to current user ----
old = '''def log_event(event, quotation_number="", detail="", user=None):
    """Append an event line to the activity log.
    Never raises - logging failures must not break the app.
    """
    try:
        _ensure_dir()
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event": _text(event) or "unknown",
            "quotation_number": _text(quotation_number),
            "detail": _text(detail),
            "user": _text(user) or os.environ.get("USERNAME") or "user",
        }'''

new = '''def log_event(event, quotation_number="", detail="", user=None):
    """Append an event line to the activity log.
    Never raises - logging failures must not break the app.
    """
    try:
        _ensure_dir()
        # ---- resolve user: explicit > logged-in > Windows env ----
        resolved_user = _text(user)
        if not resolved_user and get_current_user is not None:
            try:
                resolved_user = get_current_user() or ""
            except Exception:
                resolved_user = ""
        if not resolved_user:
            resolved_user = os.environ.get("USERNAME") or "user"

        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "event": _text(event) or "unknown",
            "quotation_number": _text(quotation_number),
            "detail": _text(detail),
            "user": resolved_user,
        }'''

if old in s:
    s = s.replace(old, new, 1)
    print("[ok] log_event now resolves the current user")
elif '"user": resolved_user' in s:
    print("[skip] log_event already patched")
else:
    print("[warn] log_event pattern not found")

LOG_SVC.write_text(s, encoding="utf-8")


# ============================================================
# compile check
# ============================================================

print()
print("=" * 60)
print("Compile check")
print("=" * 60)

try:
    py_compile.compile(str(LOG_SVC), doraise=True)
    print(f"[ok] {LOG_SVC.relative_to(ROOT)}")
    print()
    print("=" * 60)
    print("Phase 2 complete.")
    print("=" * 60)
    print()
    print("Test:")
    print("  1. python main.py")
    print("  2. Create a new quotation")
    print("  3. Open Activity Log")
    print("  4. The 'User' column should show: Mayuresh")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(LOG_SVC.with_suffix(".py.PHASE2_BACKUP"), LOG_SVC)
    print("[restore] reverted")
