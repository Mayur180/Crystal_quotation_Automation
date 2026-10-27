"""
CRYSTAL / ARMATECH ASSOCIATES
Quotation History Service

Persists and retrieves past quotations.

File:
    app/services/quotation_history_service.py

Storage:
    data/quotations.json — append-only list.
"""

import json
import os
from datetime import datetime

try:
    from app.services.activity_log_service import log_event
except Exception:
    log_event = None


def _safe_log(*args, **kwargs):
    if log_event is None:
        return
    try:
        log_event(*args, **kwargs)
    except Exception:
        pass

from decimal import Decimal, InvalidOperation
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
    """Return the folder where JSON data lives.

    Uses app.services.paths.get_data_dir(), which respects:
      1. setup.json's shared_path  (multi-user / shared folder)
      2. %APPDATA%/CRYSTAL/data    (frozen EXE)
      3. <project>/data            (dev)
    """
    try:
        from app.services.paths import get_data_dir
        d = get_data_dir()
        d.mkdir(parents=True, exist_ok=True)
        return d
    except Exception:
        pass

    # Fallback to legacy behavior
    _LEGACY_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return _LEGACY_DATA_DIR


DATA_DIR = _resolve_data_dir()
HISTORY_FILE = DATA_DIR / "quotations.json"


# ============================================================
# HELPERS
# ============================================================

def _text(value, default=""):
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _decimal_str(value):
    """Return a canonical decimal string for JSON storage."""
    try:
        return str(Decimal(str(value)).quantize(Decimal("0.01")))
    except (InvalidOperation, ValueError, TypeError):
        return "0.00"


def _ensure_data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_raw():
    """Return the full list from disk, or [] on any error."""
    try:
        if HISTORY_FILE.is_file():
            with open(HISTORY_FILE, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _save_raw(records):
    """Write the list back to disk atomically (with lock)."""
    _ensure_data_dir()

    lock_ctx = (
        FileLock(HISTORY_FILE)
        if FileLock is not None
        else _NullLock()
    )

    with lock_ctx:
        tmp = HISTORY_FILE.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(records, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, HISTORY_FILE)


class _NullLock:
    """Used if FileLock isn't available — no locking."""
    def __enter__(self):
        return self
    def __exit__(self, *args):
        pass


# ============================================================
# PUBLIC API
# ============================================================

def save_quotation(result):
    """
    Save a quotation record from the generator's return dict.
    """

    if not isinstance(result, dict):
        return None

    totals = result.get("totals") or {}
    grand = totals.get("grand_total", 0)

    record = {
        "quotation_number": _text(result.get("quotation_number")),
        "date":             _text(result.get("quotation_date")),
        "customer_name":    _text(result.get("customer_name")),
        "customer_company": _text(result.get("customer_company")),
        "customer_phone":   _text(result.get("customer_phone")),
        "customer_email":   _text(result.get("customer_email")),
        "customer_address": _text(result.get("customer_address")),
        "customer_city":    _text(result.get("customer_city")),
        "customer_state":   _text(result.get("customer_state")),
        "customer_pincode": _text(result.get("customer_pincode")),
        "customer_gstin":   _text(result.get("customer_gstin")),
        "contact_person":   _text(result.get("contact_person")),
        "model":            _text(result.get("model")),
        "grand_total":      _decimal_str(grand),
        "docx_path":        _text(result.get("docx_path") or result.get("path")),
        "pdf_path":         _text(result.get("pdf_path")),
        "created_at":       datetime.now().isoformat(timespec="seconds"),
        "status":           "Draft",
    }

    records = _load_raw()

    # Idempotent — replace if same offer number already exists
    records = [
        r for r in records
        if _text(r.get("quotation_number")) != record["quotation_number"]
    ]

    records.append(record)

    _safe_log("created", record["quotation_number"], "")

    try:
        _save_raw(records)
    except Exception:
        return record

    # ---- Send to Google Sheet (fire and forget) ----
    try:
        from app.services.google_sheet_service import send_to_sheet
        # Get current user (falls back to Windows username)
        try:
            import os as _os
            _user = _os.environ.get('USERNAME') or 'user'
        except Exception:
            _user = 'user'

        send_to_sheet({
            'action':           'quotation',
            'date':             record.get('date', ''),
            'user':             _user,
            'quotation_number': record.get('quotation_number', ''),
            'customer':         record.get('customer_name', ''),
            'company':          record.get('customer_company', ''),
            'phone':            record.get('customer_phone', ''),
            'email':            record.get('customer_email', ''),
            'address':          record.get('customer_address', ''),
            'city':             record.get('customer_city', ''),
            'state':            record.get('customer_state', ''),
            'pincode':          record.get('customer_pincode', ''),
            'gstin':            record.get('customer_gstin', ''),
            'model':            record.get('model', ''),
            'grand_total':      record.get('grand_total', ''),
            'status':           record.get('status', 'Draft'),
        })
    except Exception as _e:
        print(f'[google-sheet] hook failed: {_e}')

    return record


def list_quotations(limit=None, search=None, status=None):
    """
    Return quotation records, newest first.
    search: substring match against number / customer / company / model.
    """

    records = _load_raw()
    records = list(reversed(records))

    if search:
        needle = str(search).strip().lower()
        if needle:
            def matches(r):
                haystack = " ".join([
                    _text(r.get("quotation_number")),
                    _text(r.get("customer_name")),
                    _text(r.get("customer_company")),
                    _text(r.get("model")),
                ]).lower()
                return needle in haystack
            records = [r for r in records if matches(r)]

    if status and status != "All":
        sval = str(status).strip().lower()
        records = [
            r for r in records
            if (r.get("status") or "Draft").lower() == sval
        ]

    if limit is not None:

        records = records[: int(limit)]

    return records


VALID_STATUSES = ("Draft", "Sent", "Accepted", "Rejected", "Expired")


def update_quotation_status(quotation_number, status):
    """Update the status field of a stored quotation.
    Returns True if a record was updated, False otherwise.
    """
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status!r}")
    target = _text(quotation_number)
    if not target:
        return False
    records = _load_raw()
    updated = False
    for r in records:
        if _text(r.get("quotation_number")) == target:
            old_status = r.get("status") or "Draft"
            r["status"] = status
            updated = True
    if not updated:
        return False
    try:
        _save_raw(records)
        _safe_log("status_changed", target,
                  str(old_status) + " -> " + str(status))
        return True
    except Exception:
        return False


def update_quotation_pdf_path(quotation_number, pdf_path):
    """Update the pdf_path field of a stored quotation.

    Returns True if a record was updated, False otherwise.
    """
    target = _text(quotation_number)
    if not target:
        return False

    records = _load_raw()
    updated = False
    for r in records:
        if _text(r.get("quotation_number")) == target:
            r["pdf_path"] = _text(pdf_path)
            updated = True

    if not updated:
        return False

    try:
        _save_raw(records)
        return True
    except Exception:
        return False

def get_quotation(quotation_number):
    """Return a single record by offer number, or None."""
    target = _text(quotation_number)
    if not target:
        return None
    for r in _load_raw():
        if _text(r.get("quotation_number")) == target:
            return r
    return None


def delete_quotation(quotation_number):
    """Remove a record by offer number. Returns True if removed."""
    target = _text(quotation_number)
    if not target:
        return False

    records = _load_raw()
    kept = [r for r in records
            if _text(r.get("quotation_number")) != target]

    if len(kept) == len(records):
        return False

    try:
        _save_raw(kept)
        _safe_log("deleted", target, "")
        return True
    except Exception:
        return False


def count():
    """Number of stored records."""
    return len(_load_raw())


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("QUOTATION HISTORY SERVICE")
    print("=" * 60)
    print(f"File: {HISTORY_FILE}")
    print(f"Records: {count()}")

    for r in list_quotations(limit=10):
        print(f"  {r.get('quotation_number'):<24} "
              f"{r.get('date'):<12} "
              f"{r.get('customer_name'):<20} "
              f"{r.get('model'):<12} "
              f"₹ {r.get('grand_total')}")

    print("=" * 60)

def get_conversion_stats(module=None, data_dir=None):
    """Return conversion metrics for the specified module (or active module).
    
    Args:
        module: "Crystal", "VMM", or None (uses active module)
        data_dir: Optional Path to read quotations.json from directly (for testing)
    
    Returns:
        dict with keys: total, accepted, rejected, pending, conversion_rate
    """
    try:
        if data_dir is not None:
            # Direct path (used for testing)
            from pathlib import Path
            q_file = Path(data_dir) / "quotations.json"
            if q_file.exists():
                data = json.loads(q_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    quotations = data
                elif isinstance(data, dict):
                    quotations = data.get("quotations", [])
                else:
                    quotations = []
            else:
                quotations = []
        elif module:
            # Explicitly read from the specified module's folder
            base = _LEGACY_DATA_DIR.parent
            module_dir = base / module
            if not module_dir.exists():
                module_dir = _LEGACY_DATA_DIR
            q_file = module_dir / "quotations.json"
            if q_file.exists():
                data = json.loads(q_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    quotations = data
                elif isinstance(data, dict):
                    quotations = data.get("quotations", [])
                else:
                    quotations = []
            else:
                quotations = []
        else:
            quotations = load_quotations() or []
    except Exception:
        quotations = []

    total = len(quotations)
    accepted = 0
    rejected = 0
    pending = 0

    for q in quotations:
        status = str(q.get("status", "")).strip().lower()
        if status == "accepted":
            accepted += 1
        elif status == "rejected":
            rejected += 1
        else:
            pending += 1

    conversion_rate = (accepted / total * 100) if total > 0 else 0.0

    return {
        "total": total,
        "accepted": accepted,
        "rejected": rejected,
        "pending": pending,
        "conversion_rate": conversion_rate,
    }



def get_pending_followups(days_old=3):
    """Return quotations that are older than `days_old` days and still Draft/Sent.
    
    Returns list of dicts with quotation_number, customer_name, date, grand_total, status.
    """
    from datetime import datetime, timedelta
    
    try:
        quotations = load_quotations() or []
    except Exception:
        quotations = []
    
    cutoff = datetime.now() - timedelta(days=days_old)
    pending = []
    
    for q in quotations:
        status = str(q.get("status", "")).strip().lower()
        if status not in ("draft", "sent", ""):
            continue
        
        # Parse date
        date_str = str(q.get("date", "")).strip()
        try:
            # Try common formats
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
                try:
                    q_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            else:
                continue
            
            if q_date < cutoff:
                pending.append({
                    "quotation_number": q.get("quotation_number", ""),
                    "customer_name": q.get("customer_name", "—"),
                    "date": date_str,
                    "grand_total": q.get("grand_total", 0),
                    "status": q.get("status", "Draft"),
                })
        except Exception:
            continue
    
    # Sort by oldest first
    pending.sort(key=lambda x: x.get("date", ""))
    return pending
