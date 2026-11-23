"""
Bootstrap the app on a fresh PC.
Creates folders, seeds data from the bundled _MEIPASS copy (frozen),
and downloads catalog/users from Google Sheets if local data is missing.
"""
import json
import sys
import shutil
from pathlib import Path

# Reuse the app's single source of truth for paths
try:
    from app.services.paths import get_data_root, get_project_root
except Exception:
    # Fallback if imported before app is on sys.path
    def get_project_root() -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent

    def get_data_root() -> Path:
        d = get_project_root() / "data"
        d.mkdir(parents=True, exist_ok=True)
        return d


def seed_from_bundle():
    """On frozen exe: copy _MEIPASS/data -> <exe_dir>/data once."""
    if not getattr(sys, "frozen", False):
        return
    seed = Path(sys._MEIPASS) / "data"
    target = get_data_root()
    if not seed.exists():
        return
    # Only seed if target is empty (fresh install)
    if (target / "Crystal" / "catalog.json").exists():
        return
    shutil.copytree(seed, target, dirs_exist_ok=True)
    print("✅ Seeded data from bundle.")


def ensure_folders():
    data_root = get_data_root()
    paths = [
        data_root / "Crystal",
        data_root / "VMM",
        data_root / "Crystal" / "backups",
        get_project_root() / "output",
        get_project_root() / "assets",
    ]
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)
    print("✅ Folders verified.")


def download_catalog():
    data_root = get_data_root()
    catalog_file = data_root / "Crystal" / "catalog.json"
    if catalog_file.exists() and catalog_file.stat().st_size > 100:
        print(f"✅ Catalog already exists ({catalog_file.stat().st_size} bytes).")
        return True

    print("[bootstrap] ⚡ Using offline catalog (skipping download).")
    catalog_file.parent.mkdir(parents=True, exist_ok=True)
    catalog_file.write_text(json.dumps({"products": []}, indent=2), encoding="utf-8")
    print("⚠️  Empty catalog created. Add products via the app.")
    return True


def download_users():
    data_root = get_data_root()
    users_file = data_root / "Users.json"
    if users_file.exists() and users_file.stat().st_size > 10:
        print("✅ Users file already exists.")
        return True

    print("⬇️  Downloading users from Google Sheets...")
    try:
        from app.services.user_service import fetch_users_from_sheet
        result = fetch_users_from_sheet()
        if result:
            print("✅ Users downloaded.")
            return True
    except Exception as e:
        print(f"⚠️  Could not download users: {e}")
    return False


def bootstrap():
    print("=" * 60)
    print("CRYSTAL Quotation Manager — Bootstrap")
    print("=" * 60)
    seed_from_bundle()
    ensure_folders()
    download_catalog()
    download_users()
    print("=" * 60)
    print("✅ Bootstrap complete.")
    print("=" * 60)


if __name__ == "__main__":
    bootstrap()