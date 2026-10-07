import shutil
from pathlib import Path

SVC = Path("app/services/quotation_history_service.py")
BACKUP = SVC.with_suffix(".py.FEATURE5_BACKUP")

shutil.copy2(SVC, BACKUP)
print("[backup]", BACKUP)

s = SVC.read_text(encoding="utf-8")

# ---------- 1. Add import + _safe_log helper ----------
IMPORT_ANCHOR = "from datetime import datetime"
IMPORT_BLOCK = '''

try:
    from app.services.activity_log_service import log_event
except Exception:
    log_event = None


def _safe_log(*args, **kwargs):
    if log_event is None:
        return
    try:
        log_event(*args, **kwargs)
    except Exception:
        pass
'''

if "from app.services.activity_log_service import log_event" not in s:
    if IMPORT_ANCHOR in s:
        s = s.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_BLOCK, 1)
        print("[ok] import + _safe_log added")
    else:
        print("[WARN] datetime anchor not found")
else:
    print("[skip] import already present")

# ---------- 2. Hook save_quotation ----------
OLD = """        records.append(record)

        try:
            _save_raw(records)"""
NEW = """        records.append(record)

        _safe_log("created", record["quotation_number"], "")

        try:
            _save_raw(records)"""
if "_safe_log(\"created\"" not in s and OLD in s:
    s = s.replace(OLD, NEW, 1)
    print("[ok] save_quotation hooked")
else:
    print("[skip/WARN] save_quotation hook")

# ---------- 3. Capture old_status in update_quotation_status ----------
OLD = """        if _text(r.get("quotation_number")) == target:
            r["status"] = status
            updated = True"""
NEW = """        if _text(r.get("quotation_number")) == target:
            old_status = r.get("status") or "Draft"
            r["status"] = status
            updated = True"""
if "old_status = r.get" not in s and OLD in s:
    s = s.replace(OLD, NEW, 1)
    print("[ok] old_status captured")
else:
    print("[skip/WARN] old_status capture")

# ---------- 4. Log status_changed ----------
OLD = """    try:
        _save_raw(records)
        return True
    except Exception:
        return False"""
NEW = """    try:
        _save_raw(records)
        _safe_log("status_changed", target,
                  str(old_status) + " -> " + str(status))
        return True
    except Exception:
        return False"""
if "_safe_log(\"status_changed\"" not in s and OLD in s:
    s = s.replace(OLD, NEW, 1)
    print("[ok] status_changed logged")
else:
    print("[skip/WARN] status_changed hook")

# ---------- 5. Log deleted ----------
OLD = """    try:
        _save_raw(kept)
        return True
    except Exception:
        return False"""
NEW = """    try:
        _save_raw(kept)
        _safe_log("deleted", target, "")
        return True
    except Exception:
        return False"""
if "_safe_log(\"deleted\"" not in s and OLD in s:
    s = s.replace(OLD, NEW, 1)
    print("[ok] deleted logged")
else:
    print("[skip/WARN] deleted hook")

# ---------- save ----------
SVC.write_text(s, encoding="utf-8")
print("[written]", SVC)

# ---------- compile check ----------
import py_compile
try:
    py_compile.compile(str(SVC), doraise=True)
    print("[check] SVC OK")
except py_compile.PyCompileError as e:
    print("[check] SYNTAX ERROR:", e)
    shutil.copy2(BACKUP, SVC)
    print("[restore] restored from backup")
