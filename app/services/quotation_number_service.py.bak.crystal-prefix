"""
CRYSTAL / ARMATECH ASSOCIATES
Quotation Number Service
"""

import json
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
QUOTATION_PREFIX = "AA/VMM"
FINANCIAL_YEAR = "26-27"


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

def get_next_quotation_number():

    data = _load_counter()

    stored_year = str(
        data.get(
            "financial_year",
            "",
        )
    )

    last_number = int(
        data.get(
            "last_number",
            0,
        )
    )

    # --------------------------------------------------------
    # New financial year
    # --------------------------------------------------------

    if stored_year != FINANCIAL_YEAR:

        last_number = 0

        data = {
            "financial_year": FINANCIAL_YEAR,
            "last_number": 0,
        }

    # --------------------------------------------------------
    # Increment
    # --------------------------------------------------------

    last_number += 1

    data["financial_year"] = FINANCIAL_YEAR

    data["last_number"] = last_number

    _save_counter(
        data
    )

    # --------------------------------------------------------
    # Format
    # --------------------------------------------------------

    return (
        f"{QUOTATION_PREFIX}/"
        f"{FINANCIAL_YEAR}/"
        f"{last_number:03d}"
    )


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
        f"{QUOTATION_PREFIX}/"
        f"{FINANCIAL_YEAR}/"
        f"{last_number:03d}"
    )


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