"""
Clean up project root — move patches and backups to organized folders.
Nothing is deleted, everything is moved to backups/.
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
    "test_picker.py",
    "fix_*.py",
    "test_*.py",
]


def _move(src, dest_dir):
    if not src.exists():
        return False
    dest = dest_dir / src.name
    # avoid collision
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
print("Step 1: Moving scripts from root → backups/patches/")
print("=" * 68)

moved = 0
for pattern in SCRIPT_PATTERNS:
    for f in sorted(ROOT.glob(pattern)):
        if f.is_file():
            if _move(f, PATCHES_DIR):
                print(f"  [moved] {f.name}")
                moved += 1

print(f"  total: {moved} scripts moved")


# ============================================================
# 2. Move *.BACKUP files from ui/ and app/ → backups/old_restore_points/
# ============================================================

print()
print("=" * 68)
print("Step 2: Moving .BACKUP files from ui/ and app/")
print("=" * 68)

backup_count = 0

# Look for backups in these locations
SCAN_DIRS = [
    ROOT / "ui",
    ROOT / "app",
    ROOT / "app" / "services",
]

for scan_dir in SCAN_DIRS:
    if not scan_dir.is_dir():
        continue
    for f in sorted(scan_dir.iterdir()):
        if not f.is_file():
            continue
        name = f.name
        # Match things like:  file.py.BACKUP, file.py.FEATURE*_BACKUP, etc.
        if (
            ".BACKUP" in name or
            "_BACKUP" in name or
            ".BEFORE_USERDATA" in name
        ):
            if _move(f, RESTORE_DIR):
                print(f"  [moved] {f.relative_to(ROOT)}")
                backup_count += 1

print(f"  total: {backup_count} backup files moved")


# ============================================================
# 3. Remove __pycache__ folders
# ============================================================

print()
print("=" * 68)
print("Step 3: Removing __pycache__ folders")
print("=" * 68)

pycache_count = 0
for p in ROOT.rglob("__pycache__"):
    # skip .venv
    if ".venv" in p.parts:
        continue
    try:
        shutil.rmtree(p, ignore_errors=True)
        print(f"  [removed] {p.relative_to(ROOT)}")
        pycache_count += 1
    except Exception as e:
        print(f"  [error] {p}: {e}")

print(f"  total: {pycache_count} __pycache__ folders removed")


# ============================================================
# 4. Remove test artifacts
# ============================================================

print()
print("=" * 68)
print("Step 4: Removing test artifacts")
print("=" * 68)

TEST_FILES = [
    ROOT / "test_report.csv",
    ROOT / "test_report.pdf",
    ROOT / "nuitka-crash-report.xml",
    ROOT / "build_log.txt",
    ROOT / "run_log.txt",
]

test_count = 0
for f in TEST_FILES:
    if f.exists():
        try:
            f.unlink()
            print(f"  [removed] {f.name}")
            test_count += 1
        except Exception as e:
            print(f"  [error] {f.name}: {e}")

# Also remove data test backups
for p in ROOT.glob("data.MIGRATION_BACKUP_*"):
    try:
        shutil.rmtree(p, ignore_errors=True)
        print(f"  [removed] {p.name}")
        test_count += 1
    except Exception:
        pass

print(f"  total: {test_count} test artifacts removed")


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
print("Backups stored in:")
print(f"  {PATCHES_DIR.relative_to(ROOT)}  ({len(list(PATCHES_DIR.iterdir()))} files)")
print(f"  {RESTORE_DIR.relative_to(ROOT)}  ({len(list(RESTORE_DIR.iterdir()))} files)")
print()
print("Done.")
