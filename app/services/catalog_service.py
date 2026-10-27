"""
CRYSTAL / ARMATECH ASSOCIATES
CATALOG SERVICE

Loads and manages the master product and accessory catalog.
Supports both JSON shapes:
  (A) list    : [ {product}, ... ]                          <- Crystal v4
  (B) dict    : { "products": [...], "accessories": [...] } <- VMM legacy
Products with key "rate" are normalized so callers can read "price".
"""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

from app.services.paths import get_data_dir


def _catalog_file():
    return get_data_dir() / "catalog.json"


# ============================================================
# LOAD (shape-tolerant)
# ============================================================

def load_catalog():
    catalog_path = _catalog_file()
    if not catalog_path.exists():
        raise FileNotFoundError(f"Catalog file not found:\n{catalog_path}")

    with open(catalog_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Normalize to {"products": [...], "accessories": [...]}
    if isinstance(raw, list):
        products = raw
        accessories = []
    elif isinstance(raw, dict):
        products = raw.get("products", []) or []
        accessories = raw.get("accessories", []) or []
    else:
        products, accessories = [], []

    # Field alias: rate -> price (Crystal) if price missing
    for p in products:
        if isinstance(p, dict) and "price" not in p and "rate" in p:
            p["price"] = p["rate"]

    return {"products": products, "accessories": accessories}


# ============================================================
# HELPERS
# ============================================================

def _safe_price(value):
    if value is None or value == "":
        return 0.0
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        return 0.0


def _safe_quantity(value):
    if value is None or value == "":
        return 1
    try:
        qty = int(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        return 1
    return qty if qty >= 1 else 1


# ============================================================
# PRODUCTS
# ============================================================

def get_products():
    try:
        catalog = load_catalog()
    except FileNotFoundError:
        return []
    return catalog["products"]


def get_product_models():
    return [p["model"] for p in get_products() if p.get("model")]


def get_product_categories():
    seen, out = set(), []
    for p in get_products():
        c = p.get("category") or ""
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def get_products_by_category(category):
    return [p for p in get_products() if p.get("category") == category]


def get_product(model):
    for p in get_products():
        if p.get("model") == model:
            return p
    return None


# ============================================================
# ACCESSORIES
# ============================================================

def get_accessories(active_only=True):
    catalog = load_catalog()
    raw = catalog["accessories"]
    result = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code", "")).strip()
        if not code:
            continue
        status = str(item.get("status", "active")).strip().lower()
        if active_only and status != "active":
            continue
        result.append({
            "code": code,
            "name": str(item.get("name", code)).strip() or code,
            "category": str(item.get("category", "Accessory")).strip(),
            "description": str(item.get("description", "")).strip(),
            "unit": str(item.get("unit", "Nos")).strip() or "Nos",
            "price": _safe_price(item.get("price", 0)),
            "default_quantity": _safe_quantity(item.get("default_quantity", 1)),
            "status": status or "active",
        })
    return result


def get_accessory_codes(active_only=True):
    return [a["code"] for a in get_accessories(active_only=active_only)]


def get_accessory(code, active_only=True):
    if not code:
        return None
    code = str(code).strip()
    for a in get_accessories(active_only=active_only):
        if a["code"] == code:
            return a
    return None


def get_catalog_summary():
    return {
        "product_count": len(get_products()),
        "accessory_count": len(get_accessories()),
        "categories": get_product_categories(),
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CATALOG SERVICE TEST")
    print("=" * 60)

    summary = get_catalog_summary()
    print(f"Products    : {summary['product_count']}")
    print(f"Accessories : {summary['accessory_count']}")
    print(f"Categories  : {summary['categories']}")

    print("\nFirst 5 models:")
    for model in get_product_models()[:5]:
        product = get_product(model)
        print(f"  {model:<20} {product.get('category','')}")

    print("\nCATALOG SERVICE: OK")
