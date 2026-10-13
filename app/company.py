"""
CRYSTAL / ARMATECH ASSOCIATES
Company Configuration
"""

import sys
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

def _resolve_base_dir() -> Path:
    """
    Locate the base directory that contains 'assets/'.

    Script mode:
        Walk up until we find an 'assets' folder.
    Frozen .exe mode:
        1. Prefer <exe_dir>/assets (portable layout, if user copied assets there)
        2. Fall back to sys._MEIPASS/assets (PyInstaller bundle, default)
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        external = exe_dir / "assets"
        if external.is_dir():
            return exe_dir
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(meipass)
        return exe_dir

    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        if (candidate / "assets").is_dir():
            return candidate
    return Path(__file__).resolve().parents[1]


BASE_DIR = _resolve_base_dir()

# ------------------------------------------------------------------
# OUTPUT FOLDER
# The user's chosen folder is read from settings_service.
# Fallback: Downloads/CrystalQuotation
#
# Structure inside chosen folder:
#     <DD-MM-YYYY>/word/*.docx
#     <DD-MM-YYYY>/pdf/*.pdf
# ------------------------------------------------------------------

from datetime import date as _date


def _resolve_output_dir() -> Path:
    """Read the user's chosen output folder from settings."""
    try:
        from app.services.settings_service import get_output_folder
        return get_output_folder()
    except Exception:
        return Path.home() / "Downloads" / "CrystalQuotation"


# Kept for backward compatibility
DOWNLOADS_DIR = Path.home() / "Downloads"

# The actual folder used for all output
OUTPUT_DIR = _resolve_output_dir()

# Legacy alias (some code still references this)
QUOTATION_OUTPUT_DIR = OUTPUT_DIR / "quotations"


def get_today_folder() -> Path:
    """Return today's folder (DD-MM-YYYY) inside OUTPUT_DIR."""
    return OUTPUT_DIR / _date.today().strftime("%d-%m-%Y")


def get_word_dir() -> Path:
    """Return today's 'word' folder, creating it if needed."""
    d = get_today_folder() / "word"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_pdf_dir() -> Path:
    """Return today's 'pdf' folder, creating it if needed."""
    d = get_today_folder() / "pdf"
    d.mkdir(parents=True, exist_ok=True)
    return d


# Create the base output folder and today's word folder
# so the app is ready to save immediately.
try:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


LOGO_DIR = BASE_DIR / "assets" / "logo"
DATA_DIR = BASE_DIR / "data"


# ============================================================
# COMPANY INFORMATION
# ============================================================

COMPANY = {
    "name": "ARMATECH ASSOCIATES",
    "address": "W-174A, 'S' Block, M.I.D.C., Bhosari Industrial Estate, PUNE - 411 026. (INDIA)",
    "phone": "+91 7020991684 / +91 9699820070",
    "email": "armatech@gmail.com",
    "website": "armatechassociates.com",

    "state": "Maharashtra",
    "state_code": "27",
}


# ============================================================
# QUOTATION SETTINGS
# ============================================================

QUOTATION = {

    "prefix": "AA/VMM",

    "financial_year": "26-27",

    "validity_days": 60,

    "packing_percent": 3.5,

    "cgst_percent": 9,

    "sgst_percent": 9,

    "payment_terms": (
        "50% advance along with purchase order & 50% Balance against Proforma invoice"
    ),

    "warranty": (
        "One year against manufacturing defects"
    ),

    "delivery": (
        "Within 4–6 weeks from confirmed order"
    ),

    "freight": "To pay basis",

    "installation": (
        "Free by engineers"
    ),
}


# ============================================================
# LOGO
# ============================================================

LOGO_PATH = LOGO_DIR / "armatech_logo.png"


# ============================================================
# BACKWARD-COMPATIBLE SETTINGS
# ============================================================

QUOTATION_PREFIX = QUOTATION["prefix"]

FINANCIAL_YEAR = QUOTATION["financial_year"]

DEFAULT_VALIDITY_DAYS = QUOTATION["validity_days"]

DEFAULT_PACKING_PERCENT = QUOTATION["packing_percent"]

DEFAULT_CGST_PERCENT = QUOTATION["cgst_percent"]

DEFAULT_SGST_PERCENT = QUOTATION["sgst_percent"]

DEFAULT_PAYMENT_TERMS = QUOTATION["payment_terms"]

DEFAULT_WARRANTY = QUOTATION["warranty"]

DEFAULT_DELIVERY = QUOTATION["delivery"]

DEFAULT_FREIGHT = QUOTATION["freight"]

DEFAULT_INSTALLATION = QUOTATION["installation"]

# ============================================================
# LOADED FROM data/company_settings.json
# (auto-appended by apply_company_patch.py)
# ============================================================
# This block is safe: if the file is missing or corrupted, the
# hardcoded defaults above are used unchanged.

try:
    from app.services.company_settings_service import (
        load_settings as _load_company_settings,
        logo_full_path as _company_logo_full_path,
    )

    _saved = _load_company_settings()

    # Company block
    # Company block
    for _key in ("name", "state", "state_code", "brand", "address", "phone",
             "email", "website", "tagline"):
        if _saved.get(_key):
            COMPANY[_key] = _saved[_key]

    # Quotation defaults
    for _key in ("prefix", "financial_year", "validity_days",
                 "packing_percent", "cgst_percent", "sgst_percent",
                 "payment_terms", "warranty", "delivery",
                 "freight", "installation"):
        if _key in _saved and _saved[_key] not in (None, ""):
            QUOTATION[_key] = _saved[_key]

    # Logo — honour the saved logo path if the file exists
    _lp = _company_logo_full_path(_saved)
    if _lp is not None:
        LOGO_PATH = _lp

    # Keep the backward-compatible aliases in sync
    QUOTATION_PREFIX = QUOTATION["prefix"]
    FINANCIAL_YEAR = QUOTATION["financial_year"]
    DEFAULT_VALIDITY_DAYS = QUOTATION["validity_days"]
    DEFAULT_PACKING_PERCENT = QUOTATION["packing_percent"]
    DEFAULT_CGST_PERCENT = QUOTATION["cgst_percent"]
    DEFAULT_SGST_PERCENT = QUOTATION["sgst_percent"]
    DEFAULT_PAYMENT_TERMS = QUOTATION["payment_terms"]
    DEFAULT_WARRANTY = QUOTATION["warranty"]
    DEFAULT_DELIVERY = QUOTATION["delivery"]
    DEFAULT_FREIGHT = QUOTATION["freight"]
    DEFAULT_INSTALLATION = QUOTATION["installation"]

except Exception:
    # Silent — hardcoded defaults above remain in effect
    pass
