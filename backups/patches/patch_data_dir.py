"""
Patch _resolve_data_dir() so JSON data always lives in get_data_dir(),
not the user's Downloads folder.
"""

import shutil
import py_compile
from pathlib import Path


SVC = Path("app/services/quotation_history_service.py")
shutil.copy2(SVC, SVC.with_suffix(".py.DATA_DIR_BACKUP"))
print(f"[backup] {SVC.name}")

s = SVC.read_text(encoding="utf-8")

# Replace the old _resolve_data_dir with a clean version
old = '''def _resolve_data_dir() -> Path:
    """
    Return the folder where user data should live.

    Priority:
      1. settings_service.get_output_folder() / 'data'
      2. <project_root> / 'data' (fallback)
    """
    try:
        from app.services.settings_service import get_output_folder
        user_output = get_output_folder()
        if user_output:
            user_data = user_output / "data"
            user_data.mkdir(parents=True, exist_ok=True)
            return user_data
    except Exception:
        pass

    _LEGACY_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _LEGACY_DATA_DIR'''

new = '''def _resolve_data_dir() -> Path:
    """Return the folder where JSON data lives.

    Uses app.services.paths.get_data_dir(), which respects:
      1. setup.json's shared_path  (multi-user / shared folder)
      2. %APPDATA%/CRYSTAL/data    (frozen EXE)
      3. <project>/data            (dev)
    """
    try:
        from app.services.paths import get_data_dir
        d = get_data_dir()
        d.mkdir(parents=True, exist_ok=True)
        return d
    except Exception:
        pass

    # Fallback to legacy behavior
    _LEGACY_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _LEGACY_DATA_DIR'''

if old in s:
    s = s.replace(old, new, 1)
    SVC.write_text(s, encoding="utf-8")
    print("[ok] _resolve_data_dir patched")
elif "get_data_dir()" in s and "def _resolve_data_dir" in s:
    print("[skip] already uses get_data_dir()")
else:
    print("[warn] pattern not found — inspect manually")

print()
print("=" * 60)
print("Compile check")
print("=" * 60)
try:
    py_compile.compile(str(SVC), doraise=True)
    print("[ok] SERVICE OK")
    print()
    print("Now run:")
    print("  python -c \"from app.services.quotation_history_service import HISTORY_FILE; print(HISTORY_FILE)\"")
    print("Should print: D:\\\\VMM\\\\VMM\\\\CRYSTAL_Quotation_Automation\\\\data\\\\quotations.json")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(SVC.with_suffix(".py.DATA_DIR_BACKUP"), SVC)
    print("[restore] reverted")
