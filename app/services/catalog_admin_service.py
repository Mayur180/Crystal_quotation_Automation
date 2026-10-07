"""
CRYSTAL / ARMATECH ASSOCIATES
Catalog Admin Service

Safe read/write for data/catalog.json with:
    • Automatic timestamped backups
    • Atomic file replacement
    • Bulk price adjust
    • Restore from backup

File:
    app/services/catalog_admin_service.py
"""

import json
import os
import shutil
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

from app.services.paths import get_data_dir
DATA_DIR = get_data_dir()
BACKUP_DIR = DATA_DIR / "backups"
CATALOG_FILE = DATA_DIR / "catalog.json"


# ============================================================
# HELPERS
# ============================================================

def _text(value, default=""):
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _dec(value, default=Decimal("0")):
    if value is None:
        return default
    if isinstance(value, Decimal):
        return value
    try:
        s = str(value).replace(",", "").replace("₹", "").strip()
        return Decimal(s) if s else default
    except (InvalidOperation, ValueError, TypeError):
        return default


def _ensure_dirs():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


# ============================================================
# LOAD / SAVE
# ============================================================

def load_catalog():
    """Return the full catalog dict, or {} on error."""
    try:
        if CATALOG_FILE.is_file():
            with open(CATALOG_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def make_backup():
    """Copy the current catalog.json to data/backups/. Returns path or None."""
    _ensure_dirs()
    if not CATALOG_FILE.is_file():
        return None
    name = f"catalog_{_timestamp()}.json"
    target = BACKUP_DIR / name
    try:
        shutil.copy2(CATALOG_FILE, target)
        return target
    except Exception:
        return None


def _write_catalog(catalog):
    """Atomic write: temp file then os.replace."""
    _ensure_dirs()
    tmp = CATALOG_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, indent=4, ensure_ascii=False)
    os.replace(tmp, CATALOG_FILE)


def list_backups():
    """Return list of (timestamp_str, Path) sorted newest first."""
    _ensure_dirs()
    items = []
    for p in BACKUP_DIR.glob("catalog_*.json"):
        try:
            items.append((p.stem.replace("catalog_", ""), p))
        except Exception:
            pass
    items.sort(reverse=True, key=lambda x: x[0])
    return items


def restore_backup(backup_path):
    """Overwrite catalog.json with a backup. Returns (ok, err)."""
    backup_path = Path(backup_path)
    if not backup_path.is_file():
        return False, "backup file not found"

    try:
        data = json.loads(backup_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False, "backup is not a valid catalog"

        # Backup the current state before restoring
        make_backup()
        _write_catalog(data)
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


# ============================================================
# PRODUCT / ACCESSORY UPDATES
# ============================================================

def update_product(model, updates):
    """
    Patch a product record. `updates` is a dict of fields to set.
    Returns (ok, err).
    """
    catalog = load_catalog()
    products = catalog.get("products")
    if not isinstance(products, list):
        return False, "catalog has no products list"

    found = False
    for product in products:
        if isinstance(product, dict) and product.get("model") == model:
            for key, value in updates.items():
                product[key] = value
            found = True
            break

    if not found:
        return False, f"product {model} not found"

    try:
        make_backup()
        _write_catalog(catalog)
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def update_accessory(code, updates):
    """Patch an accessory record. Returns (ok, err)."""
    catalog = load_catalog()
    accessories = catalog.get("accessories")
    if not isinstance(accessories, list):
        return False, "catalog has no accessories list"

    found = False
    for item in accessories:
        if isinstance(item, dict) and item.get("code") == code:
            for key, value in updates.items():
                item[key] = value
            found = True
            break

    if not found:
        return False, f"accessory {code} not found"

    try:
        make_backup()
        _write_catalog(catalog)
        return True, ""
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


# ============================================================
# BULK PRICE ADJUST
# ============================================================

def bulk_adjust_product_prices(category, percent):
    """
    Multiply each product price in the given category by (1 + percent/100).
    `category=None` means all products.
    Returns (ok, count_or_err).
    """
    try:
        pct = Decimal(str(percent))
    except Exception:
        return False, "invalid percent"

    factor = Decimal("1") + pct / Decimal("100")

    catalog = load_catalog()
    products = catalog.get("products")
    if not isinstance(products, list):
        return False, "catalog has no products list"

    touched = 0
    for product in products:
        if not isinstance(product, dict):
            continue
        if category and product.get("category") != category:
            continue
        try:
            current = _dec(product.get("price", 0))
            new_price = (current * factor).quantize(Decimal("1"))
            product["price"] = int(new_price)
            touched += 1
        except Exception:
            continue

    if touched == 0:
        return False, "no products matched"

    try:
        make_backup()
        _write_catalog(catalog)
        return True, touched
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CATALOG ADMIN SERVICE")
    print("=" * 60)
    print(f"File: {CATALOG_FILE}")
    print(f"Exists: {CATALOG_FILE.is_file()}")

    catalog = load_catalog()
    print(f"Products: {len(catalog.get('products', []))}")
    print(f"Accessories: {len(catalog.get('accessories', []))}")

    print("\nBackups:")
    for ts, path in list_backups()[:5]:
        print(f"  {ts}  {path.name}")

    print("=" * 60)