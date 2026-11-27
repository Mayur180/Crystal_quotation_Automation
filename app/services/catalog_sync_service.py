"""
CRYSTAL / ARMATECH ASSOCIATES
PRODUCT CATALOG SYNC

Two-way sync for the product catalog between this PC's
data/Crystal/catalog.json and the shared "Catalog" tab of the Google
Sheet, through the same Apps Script webhook used by quotations.

Pull merges the sheet into the local catalog (matched by model), so
extra local-only details such as dimensions or measuring range are
kept. Push replaces the sheet with this PC's catalog; the caller must
confirm that intent.
"""

from app.services.cloud_sync import APPS_SCRIPT_URL

import requests


_READ_TIMEOUT = 60
_WRITE_TIMEOUT = 180


def _num(value, default=0.0):
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _text(value):
    return "" if value is None else str(value).strip()


def _core_fields(row):
    """Normalize one sheet row into the core catalog fields."""
    model = _text(row.get("model"))
    if not model:
        return None
    name = _text(row.get("name")) or _text(row.get("product_name"))
    price = _num(row.get("price") if row.get("price") not in (None, "") else row.get("rate"))
    tax = _num(row.get("tax") if row.get("tax") not in (None, "") else row.get("tax_percent"), 18.0)
    return {
        "model": model,
        "name": name,
        "product_name": name,
        "description": _text(row.get("description")),
        "price": price,
        "rate": price,
        "category": _text(row.get("category")),
        "hsn": _text(row.get("hsn")),
        "unit": _text(row.get("unit")),
        "tax_percent": tax,
    }


def fetch_catalog_from_cloud():
    """Return the shared catalog as a list of product dicts."""
    try:
        res = requests.get(
            APPS_SCRIPT_URL,
            params={"action": "get_catalog"},
            timeout=_READ_TIMEOUT,
        )
        data = res.json()
    except Exception as exc:
        raise RuntimeError(f"Could not reach the shared catalog: {exc}")

    if data.get("status") != "ok":
        raise RuntimeError(
            "The shared catalog could not be read: "
            + str(data.get("message") or "unknown error")
        )

    products = []
    for row in data.get("products") or []:
        if isinstance(row, dict):
            core = _core_fields(row)
            if core:
                products.append(core)
    return products


def merge_products(local_products, cloud_products):
    """Merge cloud products into local ones by model, keeping local extras."""
    index = {}
    merged = []
    for product in local_products:
        if isinstance(product, dict):
            merged.append(dict(product))
            model = _text(product.get("model"))
            if model:
                index[model] = merged[-1]

    added = updated = 0
    for cloud in cloud_products:
        model = cloud["model"]
        target = index.get(model)
        if target is None:
            target = {
                "model": model,
                "category": cloud["category"] or "Uncategorized",
                "description": cloud["description"],
                "hsn": cloud["hsn"] or "85059000",
                "unit": cloud["unit"] or "NOS",
                "price": cloud["price"],
                "rate": cloud["rate"],
                "tax_percent": cloud["tax_percent"],
                "default_discount": 0.0,
                "accessories": [],
                "product_name": cloud["product_name"],
                "status": "Active",
            }
            merged.append(target)
            index[model] = target
            added += 1
            continue

        target["name"] = cloud["name"]
        target["product_name"] = cloud["product_name"]
        target["description"] = cloud["description"]
        target["price"] = cloud["price"]
        target["rate"] = cloud["rate"]
        if cloud["category"]:
            target["category"] = cloud["category"]
        if cloud["hsn"]:
            target["hsn"] = cloud["hsn"]
        if cloud["unit"]:
            target["unit"] = cloud["unit"]
        target["tax_percent"] = cloud["tax_percent"]
        updated += 1

    return merged, added, updated


def pull_catalog_from_cloud():
    """Merge the shared catalog into this PC. Returns (added, updated, total)."""
    from app.services.catalog_admin_service import load_catalog, save_catalog

    local = load_catalog() or {}
    cloud = fetch_catalog_from_cloud()
    if not cloud:
        raise RuntimeError(
            "The shared catalog is empty. Push this PC's catalog first."
        )

    merged, added, updated = merge_products(local.get("products") or [], cloud)
    ok, err = save_catalog({
        "products": merged,
        "accessories": local.get("accessories") or [],
    })
    if not ok:
        raise RuntimeError(err or "Could not write the local catalog.")
    return added, updated, len(merged)


def push_catalog_to_cloud():
    """Replace the shared catalog with this PC's catalog. Returns row count."""
    from app.services.catalog_admin_service import load_catalog

    catalog = load_catalog() or {}
    rows = []
    for product in catalog.get("products") or []:
        if not isinstance(product, dict):
            continue
        model = _text(product.get("model"))
        if not model:
            continue
        rows.append({
            "model": model,
            "name": _text(product.get("product_name")) or _text(product.get("name")),
            "description": _text(product.get("description")),
            "price": _num(product.get("price"), _num(product.get("rate"))),
            "category": _text(product.get("category")),
            "hsn": _text(product.get("hsn")),
            "unit": _text(product.get("unit")),
            "tax": _text(product.get("tax_percent")),
        })

    if not rows:
        raise RuntimeError("This PC's catalog is empty — nothing to push.")

    try:
        res = requests.post(
            APPS_SCRIPT_URL,
            json={"action": "catalog_bulk", "products": rows},
            timeout=_WRITE_TIMEOUT,
        )
        data = res.json()
    except Exception as exc:
        raise RuntimeError(
            "Could not upload the catalog. If this keeps failing, the "
            "Google Apps Script may need to be redeployed.\n\n" + str(exc)
        )

    if data.get("status") != "ok":
        raise RuntimeError(
            "The shared catalog rejected the upload: "
            + str(data.get("message") or "unknown error")
        )
    return int(data.get("count") or len(rows))
