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
import threading
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

try:
    from app.services.activity_log_service import log_event
except Exception:
    log_event = None

try:
    from app.services.file_lock import FileLock
except Exception:
    FileLock = None

from app.services.paths import get_data_dir

_LEGACY_DATA_DIR = get_data_dir()

def _safe_log(*args, **kwargs):
    if log_event is None:
        return
    try:
        log_event(*args, **kwargs)
    except Exception:
        pass

# ============================================================
# PATHS
# ============================================================

def _resolve_data_dir() -> Path:
    """Return the folder where JSON data lives."""
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
_CLOUD_CACHE = None
HISTORY_FILE = DATA_DIR / "quotations.json"


def load_local_quotations() -> list:
    try:
        if HISTORY_FILE.is_file():
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def fetch_quotations_merged(force: bool = False, module: str = None, limit: int = None, silent: bool = False, **kwargs) -> list:
    from app.services.cloud_sync import fetch_quotations_from_cloud
    cloud = []
    try:
        cloud = fetch_quotations_from_cloud(force=force, module=module, silent=silent) or []
    except Exception as e:
        print(f"[quotation] cloud fetch failed: {e}")

    local = load_local_quotations()
    merged = {}
    for rec in local:
        q_no = str(rec.get("quotation_number") or "").strip()
        if q_no:
            merged[q_no] = rec
    for rec in cloud:
        q_no = str(rec.get("quotation_number") or "").strip()
        if not q_no:
            continue
        existing = merged.get(q_no)
        if existing is None:
            merged[q_no] = rec
        else:
            for k, v in rec.items():
                if not existing.get(k) and v:
                    existing[k] = v

    result = sorted(
        merged.values(),
        key=lambda x: str(x.get("quotation_number") or ""),
        reverse=True,
    )
    if limit:
        result = result[:int(limit)]
    return result


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

def _json_safe(value):
    """Convert Decimal values into JSON-serializable primitives."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value

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

    # Crystal quotes keep their line items and totals so the dashboard popup
    # can show base prices, discounts and GST-inclusive amounts.
    try:
        from app.services.paths import get_active_module
        if get_active_module() == "Crystal":
            record["items"] = _json_safe(result.get("items") or [])
            record["totals"] = _json_safe(totals)
            record["machine_price"] = _decimal_str(
                result.get("machine_price") or totals.get("subtotal") or 0
            )
            record["machine_qty"] = _text(result.get("machine_qty") or 1)
    except Exception:
        pass

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
        from app.services.cloud_sync import invalidate_quotes_cache
        invalidate_quotes_cache()
    except Exception:
        pass
    try:
        from app.services.google_sheet_service import send_to_sheet
        try:
            import os as _os
            _user = _os.environ.get('USERNAME') or 'user'
        except Exception:
            _user = 'user'

        # Aggressively find customer info from whatever structure the generator used
        cust_name = record.get('customer_name') or record.get('customer') or record.get('name') or result.get('customer_name') or result.get('customer') or result.get('name') or ''
        cust_comp = record.get('customer_company') or record.get('company') or result.get('customer_company') or result.get('company') or ''
        cust_phone = record.get('customer_phone') or record.get('phone') or result.get('customer_phone') or result.get('phone') or ''
        cust_email = record.get('customer_email') or record.get('email') or result.get('customer_email') or result.get('email') or ''
        cust_addr = record.get('customer_address') or record.get('address') or result.get('customer_address') or result.get('address') or ''
        cust_city = record.get('customer_city') or record.get('city') or result.get('customer_city') or result.get('city') or ''
        cust_state = record.get('customer_state') or record.get('state') or result.get('customer_state') or result.get('state') or ''
        cust_pin = record.get('customer_pincode') or record.get('pincode') or result.get('customer_pincode') or result.get('pincode') or ''
        cust_gst = record.get('customer_gstin') or record.get('gstin') or result.get('customer_gstin') or result.get('gstin') or ''

        payload = {
            'action':           'quotation',
            'date':             record.get('date', ''),
            'user':             _user,
            'quotation_number': record.get('quotation_number', ''),
            'customer_name':    cust_name,
            'customer_company': cust_comp,
            'customer_phone':   cust_phone,
            'customer_email':   cust_email,
            'customer_address': cust_addr,
            'customer_city':    cust_city,
            'customer_state':   cust_state,
            'customer_pincode': cust_pin,
            'customer_gstin':   cust_gst,
            'model':            record.get('model', ''),
            'grand_total':      record.get('grand_total', ''),
            'status':           record.get('status', 'Draft'),
            'items':            record.get('items') or [],
        }
        # Auto-sync customer to the Customers tab
        if cust_name or cust_comp:
            try:
                from app.services.customer_service import save_customer
                save_customer({
                    "name": cust_name, "company": cust_comp, "phone": cust_phone,
                    "email": cust_email, "address": cust_addr, "city": cust_city,
                    "state": cust_state, "pincode": cust_pin, "gstin": cust_gst
                })
            except Exception as e:
                print(f"[quotation] customer auto-sync failed: {e}")

        # The sheet round-trip can take many seconds on a slow network; the
        # quotation is already saved locally, so don't block the UI on it.
        threading.Thread(
            target=send_to_sheet, args=(payload,), daemon=True
        ).start()
    except Exception as _e:
        print(f'[google-sheet] hook failed: {_e}')

    return record

def list_quotations(limit=None, search=None, status=None):
    """Return quotation records from the cloud, newest first."""
    from app.services.cloud_sync import fetch_quotations_from_cloud
    from app.services import paths as _paths
    
    try:
        module = _paths.get_active_module()
    except Exception:
        module = "VMM"

    global _CLOUD_CACHE
    if _CLOUD_CACHE is not None and not search and not status:
        return _CLOUD_CACHE
        
    records = fetch_quotations_from_cloud(limit=500, module=module)
    if not search and not status:
        _CLOUD_CACHE = records
    
    if not records:
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

def load_quotations():
    """Alias for list_quotations to keep dashboard stats working."""
    return list_quotations()


def local_quotations():
    """Return the locally stored records (newest first), no network calls."""
    try:
        records = list(reversed(_load_raw()))
    except Exception:
        return []

    try:
        from app.services.paths import get_active_module
        if get_active_module() == "Crystal":
            from app.services.cloud_sync import deleted_quotation_numbers
            deleted = deleted_quotation_numbers()
            if deleted:
                records = [
                    r for r in records
                    if _text(r.get("quotation_number")).upper() not in deleted
                ]
    except Exception:
        pass
    return records

VALID_STATUSES = ("Draft", "Sent", "Accepted", "Rejected", "Expired")


def merge_quotation_records(local_records, cloud_records):
    """Combine local and cloud records into a single list.

    Cloud rows win on non-empty fields (they carry the latest status from
    any PC); local rows fill in anything missing (items, PDF path, drafts
    that were never uploaded). Records are de-duplicated by number.
    """
    merged = {}
    order = []

    def _key(record):
        return _text(record.get("quotation_number")).upper()

    def _add(record, overwrite):
        if not isinstance(record, dict):
            return
        number = _key(record)
        if not number:
            return
        if number not in merged:
            merged[number] = dict(record)
            order.append(number)
            return
        target = merged[number]
        for key, value in record.items():
            if value in (None, "", [], {}):
                continue
            if overwrite or not target.get(key):
                target[key] = value

    for record in local_records or ():
        _add(record, overwrite=False)
    for record in cloud_records or ():
        _add(record, overwrite=True)

    return [merged[number] for number in order]


def update_quotation_status(quotation_number, status):
    """Update the status of a quotation in the Cloud AND Local."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status!r}")
    target = _text(quotation_number)
    if not target:
        return False

    global _CLOUD_CACHE
    _CLOUD_CACHE = None
        
    # 1. Update Cloud
    try:
        from app.services.cloud_sync import update_quotation_status_in_cloud
        update_quotation_status_in_cloud(target, status)
    except Exception as e:
        print(f"[history] Cloud status update failed: {e}")

    # 2. Update Local
    records = _load_raw()
    updated = False
    for r in records:
        if _text(r.get("quotation_number")) == target:
            old_status = r.get("status") or "Draft"
            r["status"] = status
            updated = True
            
    if updated:
        try:
            _save_raw(records)
            _safe_log("status_changed", target, str(old_status) + " -> " + str(status))
        except Exception:
            pass
            
    # Return True so the UI refreshes
    return True

def update_quotation_pdf_path(quotation_number, pdf_path):
    """Update the pdf_path field of a stored quotation."""
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
    """Remove a record by offer number from BOTH Cloud and Local."""
    target = _text(quotation_number)
    if not target:
        return False

    global _CLOUD_CACHE
    _CLOUD_CACHE = None # Clear cache so next fetch gets fresh data
    
    # 1. Delete from Cloud (Supabase + Google Sheets)
    try:
        from app.services.cloud_sync import delete_quotation_from_cloud
        delete_quotation_from_cloud(target)
    except Exception as e:
        print(f'[history] Cloud delete failed: {e}')

    # 2. Delete from local JSON (in case it exists here too)
    records = _load_raw()
    kept = [r for r in records if _text(r.get("quotation_number")) != target]
    
    if len(kept) != len(records):
        try:
            _save_raw(kept)
            _safe_log("deleted", target, "")
        except Exception as e:
            print(f'[history] Local delete failed: {e}')
    
    # Always return True so the UI refreshes and shows the deletion
    return True

def count():
    """Number of stored records."""
    return len(_load_raw())

def get_conversion_stats(module=None, data_dir=None):
    """Return conversion metrics for the specified module (or active module)."""
    try:
        if data_dir is not None:
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

def get_pending_followups(days_old=3, quotations=None):
    """Return quotations that are older than `days_old` days and still Draft/Sent.

    Pass `quotations` when the caller already fetched the cloud list, so the
    same data is not downloaded twice.
    """
    from datetime import datetime, timedelta
    
    if quotations is None:
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
        
        date_str = str(q.get("date", "")).strip()
        try:
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
    
    pending.sort(key=lambda x: x.get("date", ""))
    return pending

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