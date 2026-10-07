"""
CRYSTAL / ARMATECH ASSOCIATES
Export Service

CSV / JSON / ZIP export of quotations.

File:
    app/services/export_service.py
"""

import csv
import json
import zipfile
from datetime import datetime
from pathlib import Path


# ============================================================
# PATHS
# ============================================================

from app.services.paths import get_data_dir, get_output_dir, get_project_root
PROJECT_ROOT = get_project_root()
DATA_DIR = get_data_dir()
OUTPUT_DIR = get_output_dir()
EXPORT_DIR = OUTPUT_DIR / "exports"

HISTORY_FILE = DATA_DIR / "quotations.json"
CUSTOMERS_FILE = DATA_DIR / "customers.json"

OUTPUT_QUOTATIONS = OUTPUT_DIR / "quotations"


# ============================================================
# HELPERS
# ============================================================

def _ensure_dir():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _load_json(path):
    try:
        if path.is_file():
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


# ============================================================
# QUOTATIONS CSV
# ============================================================

def export_quotations_csv():
    """
    Export all quotations as a CSV file.
    Returns (path_str, error_or_empty).
    """

    _ensure_dir()

    records = _load_json(HISTORY_FILE)

    if not records:
        return "", "no quotations to export"

    path = EXPORT_DIR / f"quotations_{_timestamp()}.csv"

    columns = [
        "quotation_number",
        "date",
        "customer_name",
        "customer_company",
        "model",
        "grand_total",
        "docx_path",
        "pdf_path",
        "created_at",
    ]

    try:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns)
            writer.writeheader()
            for r in records:
                row = {k: r.get(k, "") for k in columns}
                writer.writerow(row)

        return str(path), ""

    except Exception as exc:
        return "", f"{type(exc).__name__}: {exc}"


# ============================================================
# CUSTOMERS CSV
# ============================================================

def export_customers_csv():
    """Export all customers as CSV. Returns (path_str, err)."""

    _ensure_dir()
    records = _load_json(CUSTOMERS_FILE)

    if not records:
        return "", "no customers to export"

    path = EXPORT_DIR / f"customers_{_timestamp()}.csv"

    columns = [
        "id", "name", "company", "phone", "email",
        "address", "created_at", "last_used",
    ]

    try:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=columns)
            writer.writeheader()
            for r in records:
                row = {k: r.get(k, "") for k in columns}
                writer.writerow(row)

        return str(path), ""

    except Exception as exc:
        return "", f"{type(exc).__name__}: {exc}"


# ============================================================
# ALL DATA AS JSON
# ============================================================

def export_all_json():
    """
    Export catalog + customers + quotations as a single JSON archive.
    Returns (path_str, err).
    """

    _ensure_dir()

    payload = {
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "catalog":     _load_json(DATA_DIR / "catalog.json"),
        "customers":   _load_json(CUSTOMERS_FILE),
        "quotations":  _load_json(HISTORY_FILE),
    }

    # Catalog is a dict, not a list; load it separately
    try:
        with open(DATA_DIR / "catalog.json", "r", encoding="utf-8") as fh:
            payload["catalog"] = json.load(fh)
    except Exception:
        payload["catalog"] = {}

    path = EXPORT_DIR / f"all_data_{_timestamp()}.json"

    try:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)
        return str(path), ""
    except Exception as exc:
        return "", f"{type(exc).__name__}: {exc}"


# ============================================================
# DOCX / PDF ARCHIVE
# ============================================================

def export_quotation_files_zip():
    """
    Zip all generated Word/PDF files under output/quotations/.
    Returns (path_str, err).
    """

    _ensure_dir()

    if not OUTPUT_QUOTATIONS.is_dir():
        return "", "no quotation files to export"

    files = [
        f for f in OUTPUT_QUOTATIONS.glob("*")
        if f.is_file() and f.suffix.lower() in (".docx", ".pdf")
    ]

    if not files:
        return "", "no docx/pdf files found"

    path = EXPORT_DIR / f"quotation_files_{_timestamp()}.zip"

    try:
        with zipfile.ZipFile(path, "w",
                             compression=zipfile.ZIP_DEFLATED) as zf:
            for f in files:
                zf.write(f, arcname=f.name)
        return str(path), ""
    except Exception as exc:
        return "", f"{type(exc).__name__}: {exc}"


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("EXPORT SERVICE")
    print("=" * 60)
    print(f"Export dir: {EXPORT_DIR}")
    print("=" * 60)