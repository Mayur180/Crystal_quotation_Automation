"""
CRYSTAL / ARMATECH ASSOCIATES
Quotation Number Service
"""

import json
import re
from pathlib import Path

try:
    from app.services.file_lock import FileLock
except Exception:
    FileLock = None


# ============================================================
# PATHS
# ============================================================

from app.services.paths import get_data_dir
_LEGACY_DATA_DIR = get_data_dir()


def _resolve_data_dir() -> Path:
    """Return the folder where data lives.

    Uses app.services.paths.get_data_dir() which respects:
      1. setup.json shared_path
      2. %APPDATA%/CRYSTAL/data (frozen)
      3. <project>/data (dev)
    """
    try:
        from app.services.paths import get_data_dir
        d = get_data_dir()
        d.mkdir(parents=True, exist_ok=True)
        return d
    except Exception:
        pass
    _LEGACY_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _LEGACY_DATA_DIR


# ============================================================
# PATHS + CONSTANTS
# ============================================================

DATA_DIR = _resolve_data_dir()
COUNTER_FILE = DATA_DIR / "quotation_counter.json"
# Module-aware prefix
# VMM   → "AA/VMM"
# Crystal → "CRY"

_DEFAULT_PREFIX = "AA/VMM"

def _get_quotation_prefix() -> str:
    """Return the prefix for the active module."""
    try:
        from app.services.paths import get_active_module
        module = get_active_module()
    except Exception:
        module = "VMM"
    if module == "Crystal":
        return "CRY"
    return _DEFAULT_PREFIX

# Kept for backwards-compat (some code may read _get_quotation_prefix() directly)
QUOTATION_PREFIX = _DEFAULT_PREFIX
FINANCIAL_YEAR = "26-27"

# Proforma invoices run their own independent series: PI/26-27/001, 002, ...
PROFORMA_PREFIX = "PI"


def _load_counter():

    if not COUNTER_FILE.exists():

        return {
            "financial_year": FINANCIAL_YEAR,
            "last_number": 0,
        }

    try:

        with open(
            COUNTER_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):

            return {
                "financial_year": FINANCIAL_YEAR,
                "last_number": 0,
            }

        return data

    except (
        json.JSONDecodeError,
        OSError,
    ):

        return {
            "financial_year": FINANCIAL_YEAR,
            "last_number": 0,
        }


# ============================================================
# SAVE COUNTER
# ============================================================

def _save_counter(data):
    lock_ctx = (
        FileLock(COUNTER_FILE)
        if FileLock is not None
        else _NullLock()
    )
    with lock_ctx:
        with open(
            COUNTER_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
            )


    # ============================================================
# NEXT QUOTATION NUMBER
# ============================================================

def _counter_block(data, key):
    """Return the {financial_year, last_number} block for a counter key.

    key=None is the legacy top-level quotation counter; any other key is a
    nested block (e.g. "proforma") so each document type numbers on its own.
    """
    if key is None:
        return {
            "financial_year": data.get("financial_year", ""),
            "last_number": data.get("last_number", 0),
        }
    block = data.get(key)
    return block if isinstance(block, dict) else {}


_CLOUD_MAX = {"at": 0.0, "quotes": 0, "proforma": 0}
_CLOUD_MAX_TTL = 60.0


def _cloud_last_serial(series):
    """Highest serial the shared sheet has issued for a Crystal series.

    Cached for a minute so opening the form does not hammer the webhook.
    Fails soft to the cached value (0 if never fetched).
    """
    import time

    try:
        from app.services.paths import get_active_module
        if str(get_active_module()) != "Crystal":
            return 0
    except Exception:
        return 0

    now = time.time()
    if now - _CLOUD_MAX["at"] < _CLOUD_MAX_TTL:
        return int(_CLOUD_MAX.get(series, 0))

    try:
        import requests
        from app.services.cloud_sync import APPS_SCRIPT_URL

        response = requests.get(f"{APPS_SCRIPT_URL}?action=list", timeout=6)
        rows = (response.json() or {}).get("rows", []) if response.ok else []
        fy = re.escape(FINANCIAL_YEAR)
        quotes_re = re.compile(r"^CRY/" + fy + r"/(\d{3})(?:-R\d+)?$")
        prof_re = re.compile(r"^PI/" + fy + r"/(\d{3})(?:-R\d+)?$")
        quotes = proforma = 0
        for row in rows:
            number = str(row.get("Quotation No", "")).strip().upper()
            match = quotes_re.match(number)
            if match:
                quotes = max(quotes, int(match.group(1)))
            match = prof_re.match(number)
            if match:
                proforma = max(proforma, int(match.group(1)))
        _CLOUD_MAX.update({"at": now, "quotes": quotes, "proforma": proforma})
    except Exception:
        pass
    return int(_CLOUD_MAX.get(series, 0))


def _next_serial(key):
    """Increment and persist the counter for ``key`` (None = quotations)."""
    data = _load_counter()
    block = _counter_block(data, key)

    try:
        last_number = int(block.get("last_number", 0) or 0)
    except (TypeError, ValueError):
        last_number = 0

    # New financial year resets that counter only.
    if str(block.get("financial_year", "")) != FINANCIAL_YEAR:
        last_number = 0

    # Numbers must stay unique across PCs; the shared sheet is the register.
    cloud_last = _cloud_last_serial("proforma" if key == "proforma" else "quotes")
    if cloud_last > last_number:
        last_number = cloud_last

    last_number += 1
    new_block = {
        "financial_year": FINANCIAL_YEAR,
        "last_number": last_number,
    }

    if key is None:
        data["financial_year"] = new_block["financial_year"]
        data["last_number"] = new_block["last_number"]
    else:
        data[key] = new_block

    _save_counter(data)
    return last_number


def get_next_quotation_number():

    last_number = _next_serial(None)

    return (
        f"{_get_quotation_prefix()}/"
        f"{FINANCIAL_YEAR}/"
        f"{last_number:03d}"
    )


def get_next_proforma_number():
    """Return the next PI number, e.g. PI/26-27/001."""

    last_number = _next_serial("proforma")

    return (
        f"{PROFORMA_PREFIX}/"
        f"{FINANCIAL_YEAR}/"
        f"{last_number:03d}"
    )


def get_next_document_number(doc_type="quotation"):
    """Allocate a number for the document type: quotation or proforma."""

    if str(doc_type or "").strip().lower().startswith("prof"):
        return get_next_proforma_number()
    return get_next_quotation_number()


# ============================================================
# CURRENT NUMBER
# ============================================================

def get_current_quotation_number():

    data = _load_counter()

    last_number = int(
        data.get(
            "last_number",
            0,
        )
    )

    return (
        f"{_get_quotation_prefix()}/"
        f"{FINANCIAL_YEAR}/"
        f"{last_number:03d}"
    )


# ============================================================
# REVISIONS
# ============================================================

_REVISION_RE = re.compile(r"^(?P<base>.+?)-R(?P<rev>\d+)$", re.IGNORECASE)


def split_revision(quotation_number):
    """Return (base_number, revision_index).

    CRY/26-27/067-R2 → ("CRY/26-27/067", 2)
    CRY/26-27/067    → ("CRY/26-27/067", 0)
    """
    text = str(quotation_number or "").strip()
    match = _REVISION_RE.match(text)
    if not match:
        return text, 0
    return match.group("base"), int(match.group("rev"))


def next_revision_number(quotation_number, existing_numbers=()):
    """Return the next revision number for a quotation.

    Revising CRY/26-27/067-R1 (or CRY/26-27/067) yields CRY/26-27/067-R2
    when R1 is the highest revision found in ``existing_numbers``.
    """
    base, _ = split_revision(quotation_number)
    highest = 0
    for number in existing_numbers or ():
        other_base, rev = split_revision(number)
        if other_base == base and rev > highest:
            highest = rev
    return f"{base}-R{highest + 1}"


# ============================================================
# RESET COUNTER
# ============================================================

def reset_counter():

    data = {
        "financial_year": FINANCIAL_YEAR,
        "last_number": 0,
    }

    _save_counter(
        data
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print(
        "Current:",
        get_current_quotation_number(),
    )

    print(
        "Next:",
        get_next_quotation_number(),
    )