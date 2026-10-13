"""
CRYSTAL / ARMATECH ASSOCIATES
CATALOG SERVICE

Loads and manages the master product and accessory catalog.
"""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


# ============================================================
# PATH
# ============================================================

from app.services.paths import get_data_dir


def _catalog_file():
    """Resolve catalog path at call time (module-aware)."""
    return get_data_dir() / "catalog.json"


# ============================================================
# LOAD CATALOG
# ============================================================

def load_catalog():
    catalog_path = _catalog_file()

    if not catalog_path.exists():
        raise FileNotFoundError(
            f"Catalog file not found:\n{catalog_path}"
        )

    with open(
        catalog_path,
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# INTERNAL HELPERS (safe coercion)
# ============================================================

def _safe_price(value):
    """Return a float price; blank/None/missing → 0.0."""
    if value is None or value == "":
        return 0.0
    try:
        return float(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        return 0.0


def _safe_quantity(value):
    """Return an int quantity >= 1; blank/None/missing → 1."""
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
        # Empty catalog is OK — return empty list
        return []

    if not catalog:
        return []

    return catalog.get(
        "products",
        [],
    )


def get_product_models():

    products = get_products()

    return [
        product["model"]
        for product in products
    ]


def get_product_categories():

    products = get_products()

    categories = []

    for product in products:

        category = product["category"]

        if category not in categories:

            categories.append(category)

    return categories


def get_products_by_category(category):

    products = get_products()

    return [
        product
        for product in products
        if product["category"] == category
    ]


def get_product(model):

    products = get_products()

    for product in products:

        if product["model"] == model:

            return product

    return None


# ============================================================
# ACCESSORIES
# ============================================================

def get_accessories(active_only=True):
    """
    Return accessory records from data/catalog.json.

    Each record preserves every field present in the JSON
    (code, name, category, description, unit, price,
     default_quantity, status) and adds safe defaults:

        price            → 0.0  if blank/None/missing
        default_quantity → 1    if blank/None/missing or < 1

    If active_only=True (default), only records whose
    status is "active" (case-insensitive) are returned.
    """

    catalog = load_catalog()

    raw = catalog.get("accessories", []) or []

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

        result.append(
            {
                "code": code,
                "name": str(item.get("name", code)).strip() or code,
                "category": str(item.get("category", "Accessory")).strip(),
                "description": str(item.get("description", "")).strip(),
                "unit": str(item.get("unit", "Nos")).strip() or "Nos",
                "price": _safe_price(item.get("price", 0)),
                "default_quantity": _safe_quantity(
                    item.get("default_quantity", 1)
                ),
                "status": status or "active",
            }
        )

    return result


def get_accessory_codes(active_only=True):

    accessories = get_accessories(active_only=active_only)

    return [
        accessory["code"]
        for accessory in accessories
    ]


def get_accessory(code, active_only=True):

    if not code:
        return None

    code = str(code).strip()

    accessories = get_accessories(active_only=active_only)

    for accessory in accessories:

        if accessory["code"] == code:

            return accessory

    return None


# ============================================================
# SUMMARY
# ============================================================

def get_catalog_summary():

    products = get_products()

    accessories = get_accessories()

    return {
        "product_count": len(products),
        "accessory_count": len(accessories),
        "categories": get_product_categories(),
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("CRYSTAL CATALOG SERVICE TEST")
    print("=" * 60)

    summary = get_catalog_summary()

    print(f"Products    : {summary['product_count']}")
    print(f"Accessories : {summary['accessory_count']}")

    print("\nPRODUCT MODELS")
    print("-" * 60)

    for model in get_product_models():

        product = get_product(model)

        print(f"{model:<12} {product['category']}")

    print("\nACCESSORIES (active)")
    print("-" * 60)

    for accessory in get_accessories():

        print(
            f"{accessory['code']:<18} "
            f"{accessory['name']:<22} "
            f"price={accessory['price']:<10} "
            f"qty={accessory['default_quantity']}"
        )

    print("\nCATEGORIES")
    print("-" * 60)

    for category in get_product_categories():

        print(category)

    print("\nCATALOG SERVICE: OK")