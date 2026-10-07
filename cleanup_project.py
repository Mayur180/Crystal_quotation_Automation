"""
Clean up project root — move patches and backups to organized folders.
Nothing is deleted except __pycache__ and old dist build.
"""

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
BACKUPS = ROOT / "backups"
PATCHES_DIR = BACKUPS / "patches"
RESTORE_DIR = BACKUPS / "old_restore_points"

# Create target folders
PATCHES_DIR.mkdir(parents=True, exist_ok=True)
RESTORE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# 1. Move patch/setup/cleanup scripts from root → backups/patches/
# ============================================================

SCRIPT_PATTERNS = [
    "patch_*.py",
    "setup_*.py",
    "cleanup*.py",
    "build_*.py",
    "audit.py",
    "test_*.py",
    "fix_*.py",
]


def _move(src, dest_dir):
    if not src.exists():
        return False
    dest = dest_dir / src.name
    n = 1
    while dest.exists():
        dest = dest_dir / f"{src.stem}_{n}{src.suffix}"
        n += 1
    try:
        shutil.move(str(src), str(dest))
        return True
    except Exception as e:
        print(f"  [error] {src.name}: {e}")
        return False


print("=" * 68)
print("Step 1: Moving patch scripts → backups/patches/")
print("=" * 68)

moved_scripts = 0
for pattern in SCRIPT_PATTERNS:
    for f in sorted(ROOT.glob(pattern)):
        if f.is_file() and f.name != "cleanup_project.py":  # don't move self
            if _move(f, PATCHES_DIR):
                print(f"  [moved] {f.name}")
                moved_scripts += 1
print(f"  total: {moved_scripts}")


# ============================================================
# 2. Move backup files from root, ui/, app/, data/ → backups/old_restore_points/
# ============================================================

print()
print("=" * 68)
print("Step 2: Moving backup files")
print("=" * 68)

BACKUP_PATTERNS = [
    "*.BACKUP",
    "*.FEATURE*_BACKUP",
    "*.TERMS_BACKUP",
    "*.PAGE*_BACKUP",
    "*.PHASE*_BACKUP",
    "*.WIZARD_BACKUP",
    "*.AUTOSAVE*",
    "*.BUYBACK*",
    "*.SHORTCUTS*",
    "*.CLEARLOG*",
    "*.SIDEBAR*",
    "*.POLISH*",
    "*.DUPLICATE*",
    "*.ROWCOLOR*",
    "*.WHATSAPP*",
    "*.EMAIL*",
    "*.PREFILL*",
    "*.BEFORE_USERDATA",
    "*.REMOVE_LOGIN*",
    "*.CENTER_TITLE*",
    "*.MANUAL_BACKUP",
    "*.AUTO_BACKUP",
    "*.CABINET_BACKUP",
    "*.VMS_BACKUP",
    "*.SEMIAUTO_BACKUP",
    "*.CNC_REMOVE_BACKUP",
    "*.BUYBACK_FORM_BACKUP",
    "*.OPTIONAL_FIELDS_BACKUP",
    "*.CENTER_TITLE_BACKUP",
]

SCAN_DIRS = [ROOT, ROOT / "ui", ROOT / "app", ROOT / "app" / "services", ROOT / "data"]
moved_backups = 0

for scan_dir in SCAN_DIRS:
    if not scan_dir.is_dir():
        continue
    for f in sorted(scan_dir.iterdir()):
        if not f.is_file():
            continue
        name = f.name
        # Only move if the file looks like a backup (has backup-ish suffix)
        if (
            ".BACKUP" in name
            or "_BACKUP" in name
            or ".BEFORE_USERDATA" in name
            or ".old" in name
        ):
            if _move(f, RESTORE_DIR):
                print(f"  [moved] {f.relative_to(ROOT)}")
                moved_backups += 1

print(f"  total: {moved_backups}")


# ============================================================
# 3. Remove __pycache__ folders
# ============================================================

print()
print("=" * 68)
print("Step 3: Removing __pycache__ folders")
print("=" * 68)

pycache_count = 0
for p in ROOT.rglob("__pycache__"):
    if ".venv" in p.parts:
        continue
    try:
        shutil.rmtree(p, ignore_errors=True)
        print(f"  [removed] {p.relative_to(ROOT)}")
        pycache_count += 1
    except Exception as e:
        print(f"  [error] {p}: {e}")
print(f"  total: {pycache_count}")


# ============================================================
# 4. Remove old dist build (keep the folder, delete contents)
# ============================================================

print()
print("=" * 68)
print("Step 4: Cleaning old dist builds")
print("=" * 68)

DIST = ROOT / "dist"
if DIST.exists():
    for item in DIST.iterdir():
        if item.name.startswith("main."):
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
                print(f"  [removed] dist/{item.name}")
            else:
                item.unlink()
                print(f"  [removed] dist/{item.name}")


# ============================================================
# 5. Final report
# ============================================================

print()
print("=" * 68)
print("CLEANUP COMPLETE")
print("=" * 68)
print()
print("Root folder now:")
for item in sorted(ROOT.iterdir()):
    if item.name in {".venv", ".git"}:
        continue
    kind = "[dir ]" if item.is_dir() else "[file]"
    print(f"  {kind} {item.name}")

print()
print(f"Patches: {len(list(PATCHES_DIR.iterdir()))} files")
print(f"Backups: {len(list(RESTORE_DIR.iterdir()))} files")
print()
print("Done.")
