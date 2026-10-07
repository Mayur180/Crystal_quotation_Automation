"""
CRYSTAL / ARMATECH ASSOCIATES
Customer Service

CRUD + lookup for saved customer records.

File:
    app/services/customer_service.py

Storage:
    data/customers.json
"""

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path


from app.services.paths import get_data_dir
DATA_DIR = get_data_dir()
CUSTOMERS_FILE = DATA_DIR / "customers.json"


# ============================================================
# HELPERS
# ============================================================

def _text(value, default=""):
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_raw():
    try:
        if CUSTOMERS_FILE.is_file():
            with open(CUSTOMERS_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _save_raw(records):
    _ensure_dir()
    tmp = CUSTOMERS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, CUSTOMERS_FILE)


def _norm_key(value):
    """Normalise a string for duplicate detection."""
    s = _text(value).lower()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^\w\s@.+-]", "", s)
    return s


# ============================================================
# PUBLIC API
# ============================================================

def list_customers(search=None):
    """Return customers sorted by last_used then name."""
    records = _load_raw()

    if search:
        needle = _norm_key(search)
        if needle:
            def matches(r):
                haystack = " ".join([
                    _text(r.get("name")),
                    _text(r.get("company")),
                    _text(r.get("phone")),
                    _text(r.get("email")),
                ]).lower()
                return needle in haystack
            records = [r for r in records if matches(r)]

    def sort_key(r):
        return (
            _text(r.get("last_used")) or "0",
            _text(r.get("name")).lower(),
        )

    return sorted(records, key=sort_key, reverse=True)


def get_customer(customer_id):
    if not customer_id:
        return None
    for r in _load_raw():
        if _text(r.get("id")) == _text(customer_id):
            return r
    return None


def find_by_phone(phone):
    key = _norm_key(phone)
    if not key:
        return None
    for r in _load_raw():
        if _norm_key(r.get("phone")) == key:
            return r
    return None


def find_by_email(email):
    key = _norm_key(email)
    if not key:
        return None
    for r in _load_raw():
        if _norm_key(r.get("email")) == key:
            return r
    return None


def find_duplicate(name, company, phone, email):
    """
    Return an existing customer record matching any of:
        - same phone (strongest signal)
        - same email
        - same (name + company)
    Otherwise None.
    """
    phone_key = _norm_key(phone)
    email_key = _norm_key(email)
    name_key = _norm_key(name)
    company_key = _norm_key(company)

    records = _load_raw()

    if phone_key:
        for r in records:
            if _norm_key(r.get("phone")) == phone_key:
                return r

    if email_key:
        for r in records:
            if _norm_key(r.get("email")) == email_key:
                return r

    if name_key and company_key:
        for r in records:
            if (
                _norm_key(r.get("name")) == name_key
                and _norm_key(r.get("company")) == company_key
            ):
                return r

    return None


def save_customer(data, customer_id=None):
    """
    Create or update a customer record.

    `data` must contain at least name (or company).
    Returns (record, created_bool) on success, (None, err) on failure.
    """

    if not isinstance(data, dict):
        return None, "customer data must be a dict"

    name = _text(data.get("name"))
    company = _text(data.get("company"))

    if not name and not company:
        return None, "customer must have a name or a company"

    now = datetime.now().isoformat(timespec="seconds")

    records = _load_raw()

    existing = None
    if customer_id:
        for r in records:
            if _text(r.get("id")) == _text(customer_id):
                existing = r
                break

    if existing is None:
        # New record — check for a duplicate
        dup = find_duplicate(
            name, company,
            data.get("phone", ""),
            data.get("email", ""),
        )
        if dup is not None:
            existing = dup

    if existing is not None:
        existing.update({
            "name":           name or existing.get("name", ""),
            "company":        company or existing.get("company", ""),
            "contact_person": _text(data.get("contact_person"), existing.get("contact_person", "")),
            "address":        _text(data.get("address"),        existing.get("address", "")),
            "city":           _text(data.get("city"),           existing.get("city", "")),
            "state":          _text(data.get("state"),          existing.get("state", "")),
            "pincode":        _text(data.get("pincode"),        existing.get("pincode", "")),
            "country":        _text(data.get("country"),        existing.get("country", "")),
            "gstin":          _text(data.get("gstin"),          existing.get("gstin", "")).upper(),
            "phone":          _text(data.get("phone"),          existing.get("phone", "")),
            "email":          _text(data.get("email"),          existing.get("email", "")),
            "updated_at":     now,
        })
        _save_raw(records)
        return existing, False

    record = {
        "id":             str(uuid.uuid4())[:8],
        "name":           name,
        "company":        company,
        "contact_person": _text(data.get("contact_person")),
        "address":        _text(data.get("address")),
        "city":           _text(data.get("city")),
        "state":          _text(data.get("state")),
        "pincode":        _text(data.get("pincode")),
        "country":        _text(data.get("country")),
        "gstin":          _text(data.get("gstin")).upper(),
        "phone":          _text(data.get("phone")),
        "email":          _text(data.get("email")),
        "created_at":     now,
        "updated_at":     now,
        "last_used":      "",
    }
    records.append(record)
    _save_raw(records)
    return record, True


def touch_last_used(customer_id):
    """Update the last_used timestamp for a customer."""
    if not customer_id:
        return False
    records = _load_raw()
    for r in records:
        if _text(r.get("id")) == _text(customer_id):
            r["last_used"] = datetime.now().isoformat(timespec="seconds")
            try:
                _save_raw(records)
                return True
            except Exception:
                return False
    return False


def delete_customer(customer_id):
    if not customer_id:
        return False
    records = _load_raw()
    kept = [r for r in records if _text(r.get("id")) != _text(customer_id)]
    if len(kept) == len(records):
        return False
    try:
        _save_raw(kept)
        return True
    except Exception:
        return False


def count():
    return len(_load_raw())


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CUSTOMER SERVICE")
    print("=" * 60)
    print(f"File: {CUSTOMERS_FILE}")
    print(f"Records: {count()}")
    print()

    for r in list_customers():
        print(f"  {r.get('id', '?'):<10} "
              f"{_text(r.get('name')):<24} "
              f"{_text(r.get('company')):<24} "
              f"{_text(r.get('phone'))}")

    print("=" * 60)