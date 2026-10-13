"""Phase C2.5: make catalog_service module-aware."""
from pathlib import Path

p = Path("app/services/catalog_service.py")
src = p.read_text(encoding="utf-8")

# ---------- CHANGE 1: Replace hardcoded path constant ----------
OLD_PATHS = '''from app.services.paths import get_project_root
PROJECT_ROOT = get_project_root()

CATALOG_FILE = (
    PROJECT_ROOT
    / "data"
    / "catalog.json"
)'''

NEW_PATHS = '''from app.services.paths import get_data_dir


def _catalog_file():
    """Resolve catalog path at call time (module-aware)."""
    return get_data_dir() / "catalog.json"'''

if OLD_PATHS in src:
    src = src.replace(OLD_PATHS, NEW_PATHS, 1)
    print("[OK] Replaced hardcoded path with module-aware function")
else:
    print("[SKIP] Path block not found — checking for partial match")
    # Try looser match
    import re
    pattern = r"from app\.services\.paths import get_project_root\s*\n\s*PROJECT_ROOT\s*=\s*get_project_root\(\)\s*\n\s*CATALOG_FILE\s*=\s*\(\s*\n\s*PROJECT_ROOT\s*\n\s*/\s*[\"']data[\"']\s*\n\s*/\s*[\"']catalog\.json[\"']\s*\n\s*\)"
    if re.search(pattern, src):
        src = re.sub(pattern, NEW_PATHS, src, count=1)
        print("[OK] Replaced via regex fallback")
    else:
        print("[FAIL] Could not find path block")

# ---------- CHANGE 2: Replace CATALOG_FILE references in load_catalog ----------
OLD_LOAD = '''def load_catalog():

    if not CATALOG_FILE.exists():

        raise FileNotFoundError(
            f"Catalog file not found:\\n{CATALOG_FILE}"
        )

    with open(
        CATALOG_FILE,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)'''

NEW_LOAD = '''def load_catalog():
    catalog_path = _catalog_file()

    if not catalog_path.exists():
        raise FileNotFoundError(
            f"Catalog file not found:\\n{catalog_path}"
        )

    with open(
        catalog_path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)'''

if OLD_LOAD in src:
    src = src.replace(OLD_LOAD, NEW_LOAD, 1)
    print("[OK] Rewrote load_catalog to use dynamic path")
else:
    print("[SKIP] load_catalog block mismatch")

# ---------- CHANGE 3: Handle empty catalog gracefully ----------
# If catalog is empty [], get_products should return [] not error
OLD_GET_PRODUCTS_SIG = '''def get_products():

    catalog = load_catalog()'''

NEW_GET_PRODUCTS_SIG = '''def get_products():
    try:
        catalog = load_catalog()
    except FileNotFoundError:
        # Empty catalog is OK — return empty list
        return []

    if not catalog:
        return []'''

if OLD_GET_PRODUCTS_SIG in src:
    src = src.replace(OLD_GET_PRODUCTS_SIG, NEW_GET_PRODUCTS_SIG, 1)
    print("[OK] get_products handles empty catalog")
else:
    print("[SKIP] get_products signature mismatch")

p.write_text(src, encoding="utf-8")
print()
print("✅ catalog_service.py patched")
