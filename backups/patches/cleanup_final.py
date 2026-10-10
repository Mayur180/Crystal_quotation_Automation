"""
Full project cleanup — remove build artifacts, move patches + backups.
"""
import shutil
from pathlib import Path

ROOT = Path.cwd()
BACKUPS = ROOT / "backups"
PATCH_DIR = BACKUPS / "patches"
RESTORE_DIR = BACKUPS / "old_restore_points"

PATCH_DIR.mkdir(parents=True, exist_ok=True)
RESTORE_DIR.mkdir(parents=True, exist_ok=True)


def move_file(src, dest_dir):
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


def delete_dir(path):
    if path.exists():
        try:
            shutil.rmtree(path, ignore_errors=True)
            print(f"  [removed] {path.name}/")
            return True
        except Exception as e:
            print(f"  [error] {path.name}: {e}")
            return False
    return False


def delete_file(path):
    if path.exists():
        try:
            path.unlink()
            print(f"  [removed] {path.name}")
            return True
        except Exception as e:
            print(f"  [error] {path.name}: {e}")
            return False
    return False


print("=" * 60)
print("STEP 1 — Delete build artifacts")
print("=" * 60)
delete_dir(ROOT / "dist")
delete_dir(ROOT / "build")

print()
print("=" * 60)
print("STEP 2 — Delete __pycache__ folders")
print("=" * 60)
for p in ROOT.rglob("__pycache__"):
    if ".venv" in p.parts:
        continue
    try:
        shutil.rmtree(p, ignore_errors=True)
        print(f"  [removed] {p.relative_to(ROOT)}")
    except Exception:
        pass

print()
print("=" * 60)
print("STEP 3 — Move patch scripts to backups/patches/")
print("=" * 60)
moved = 0
for name in [
    "patch_full_customer_data.py",
    "patch_main_singleroot.py",
    "patch_output_folder_ui.py",
    "remove_multiuser.py",
    "reset_data.py",
    "test_minimal.py",
]:
    f = ROOT / name
    if f.is_file():
        if move_file(f, PATCH_DIR):
            print(f"  [moved] {name}")
            moved += 1
print(f"  total: {moved}")

print()
print("=" * 60)
print("STEP 4 — Move .BACKUP files to backups/old_restore_points/")
print("=" * 60)
moved = 0
SCAN_DIRS = [ROOT, ROOT / "ui", ROOT / "app", ROOT / "app" / "services", ROOT / "app" / "generators"]
for d in SCAN_DIRS:
    if not d.is_dir():
        continue
    for f in sorted(d.iterdir()):
        if not f.is_file():
            continue
        name = f.name
        if ".BACKUP" in name or "_BACKUP" in name:
            if move_file(f, RESTORE_DIR):
                print(f"  [moved] {f.relative_to(ROOT)}")
                moved += 1
print(f"  total: {moved}")

print()
print("=" * 60)
print("STEP 5 — Move data_RESET_BACKUP_* to backups/")
print("=" * 60)
moved = 0
for p in ROOT.glob("data_RESET_BACKUP_*"):
    if p.is_dir():
        dest = BACKUPS / p.name
        try:
            shutil.move(str(p), str(dest))
            print(f"  [moved] {p.name}")
            moved += 1
        except Exception as e:
            print(f"  [error] {p.name}: {e}")
print(f"  total: {moved}")

print()
print("=" * 60)
print("STEP 6 — Delete stray files")
print("=" * 60)
for name in ["audit_output.txt", "CRYSTALQuotation.spec"]:
    f = ROOT / name
    if f.is_file():
        delete_file(f)

# CRYSTALQuotation.spec is a keep-worthy file — move instead of delete
spec = ROOT / "CRYSTALQuotation.spec"
if spec.exists():
    move_file(spec, RESTORE_DIR)

print()
print("=" * 60)
print("CLEANUP COMPLETE")
print("=" * 60)
print()
print("Remaining root:")
for item in sorted(ROOT.iterdir()):
    if item.name in {".venv", ".git", "backups"}:
        continue
    kind = "[dir ]" if item.is_dir() else "[file]"
    print(f"  {kind} {item.name}")
