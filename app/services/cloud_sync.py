import os
import requests
import threading
import time
import json

try:
    from supabase import create_client, Client
except Exception:
    # Supabase is only needed for the VMM module. If the package is missing
    # the Crystal module must still work, so this import is not fatal.
    create_client = None
    Client = None

# Your Supabase Credentials
SUPABASE_URL = "https://ycruccuxvyxkvuitsfjg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InljcnVjY3V4dnl4a3Z1aXRzZmpnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTM2MDc1MjAsImV4cCI6MjEwOTE4MzUyMH0.jDi-f5ZbO-bqoDD9uS0qV-BW9g7ZSJlEQofB9FPwo40"

# Google Apps Script webhook (Google Sheets sync)
APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwhhqEsHfFmh8Iv4ndlSbTcKiuDuDFMaee1k5dsPaXNmZpSked5adzzOCu-N6UxiO83ZQ/exec"

# Supabase client is created lazily — building it at import time used to add
# more than a second to startup even for Crystal, which never uses Supabase.
supabase = None
_SUPABASE_LOCK = threading.Lock()


def get_supabase():
    """Return the shared Supabase client, creating it on first use."""
    global supabase
    if supabase is not None or create_client is None:
        return supabase
    with _SUPABASE_LOCK:
        if supabase is None:
            try:
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e:
                print(f"[cloud] Failed to connect to Supabase: {e}")
                supabase = None
    return supabase


_LAST_FETCH_TIME = 0
_CACHE = {"data": [], "timestamp": 0}

# Short-lived caches: the dashboard, history window and follow-up panel all
# request the same data, and each sheet round-trip takes several seconds.
_QUOTES_CACHE = {"module": None, "data": [], "timestamp": 0.0}
_QUOTES_CACHE_TTL = 20          # seconds
_CUSTOMERS_CACHE = {"module": None, "data": [], "timestamp": 0.0}
_CUSTOMERS_CACHE_TTL = 60


# --- in-flight write tracking ------------------------------------
_PENDING_WRITES = 0
_PENDING_LOCK = threading.Lock()

def _begin_write():
    global _PENDING_WRITES
    with _PENDING_LOCK:
        _PENDING_WRITES += 1

def _end_write():
    global _PENDING_WRITES
    with _PENDING_LOCK:
        _PENDING_WRITES = max(0, _PENDING_WRITES - 1)
        if _PENDING_WRITES == 0:
            invalidate_quotes_cache()
            invalidate_customers_cache()

def has_pending_writes() -> bool:
    with _PENDING_LOCK:
        return _PENDING_WRITES > 0
       # seconds


def invalidate_quotes_cache():
    _QUOTES_CACHE["timestamp"] = 0.0
    _QUOTES_CACHE["data"] = []


def invalidate_customers_cache():
    _CUSTOMERS_CACHE["timestamp"] = 0.0
    _CUSTOMERS_CACHE["data"] = []

_DELETED_FILE = "deleted_quotations.json"


def _deleted_file_path():
    try:
        from app.services import paths as _paths
        return _paths.get_data_dir() / _DELETED_FILE
    except Exception:
        return None


def _load_deleted_quotations() -> set:
    path = _deleted_file_path()
    if path is None or not path.is_file():
        return set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {str(x).strip().upper() for x in data if str(x).strip()}
    except Exception:
        pass
    return set()


def _write_deleted_quotations(numbers: set) -> None:
    path = _deleted_file_path()
    if path is None:
        return
    try:
        path.write_text(
            json.dumps(sorted(numbers), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        pass


def _mark_quotation_deleted(q_no: str) -> None:
    numbers = _load_deleted_quotations()
    numbers.add(str(q_no).strip().upper())
    _write_deleted_quotations(numbers)


def _unmark_quotation_deleted(q_no: str) -> None:
    numbers = _load_deleted_quotations()
    key = str(q_no).strip().upper()
    if key in numbers:
        numbers.discard(key)
        _write_deleted_quotations(numbers)


def is_quotation_deleted(quotation_number: str) -> bool:
    return str(quotation_number or "").strip().upper() in _load_deleted_quotations()


def deleted_quotation_numbers() -> set:
    """All locally tombstoned quotation numbers (upper-cased)."""
    return _load_deleted_quotations()

def _sanitize_json(data):
    """Converts Decimal / datetime / numpy scalars to JSON-safe primitives."""
    from decimal import Decimal
    if isinstance(data, Decimal):
        return str(data)                       # exact precision for money
    if isinstance(data, dict):
        return {str(k): _sanitize_json(v) for k, v in data.items()}
    if isinstance(data, (list, tuple, set)):
        return [_sanitize_json(i) for i in data]
    if hasattr(data, "isoformat"):             # datetime / date / time
        return data.isoformat()
    if hasattr(data, "item") and callable(data.item):   # numpy scalars
        return data.item()
    return data

_SHEET_ERROR_VALUES = {
    "#ERROR!", "#N/A", "#REF!", "#VALUE!", "#DIV/0!", "#NAME?", "#NULL!",
}


def _sheet_text(value) -> str:
    """Convert a sheet cell to text, discarding formula-error markers."""
    if value is None:
        return ""
    s = str(value).strip()
    return "" if s in _SHEET_ERROR_VALUES else s


def _parse_sheet_items(value) -> list:
    """Normalise the material list returned by the Apps Script list action."""
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        try:
            value = json.loads(text)
        except Exception:
            return []
    if not isinstance(value, list):
        return []

    def _num(raw, key, default=0.0):
        try:
            text = (
                str(raw.get(key, default))
                .replace(",", "")
                .replace("₹", "")
                .strip()
            )
            return float(text) if text else default
        except Exception:
            return default

    items = []
    for raw in value:
        if not isinstance(raw, dict):
            continue
        model = str(raw.get("model") or "").strip()
        if not model:
            continue
        items.append({
            "model": model,
            "hsn": str(raw.get("hsn") or "85059000").strip() or "85059000",
            "qty": _num(raw, "qty", 1.0),
            "price": _num(raw, "price"),
            "discount": _num(raw, "discount"),
            "total": _num(raw, "total"),
            "disc_mode": str(raw.get("disc_mode") or "").strip(),
            "raw_discount": _num(raw, "raw_discount"),
        })
    return items


def _parse_sheet_totals(value) -> dict:
    """Parse the totals breakdown stored in the sheet's Totals column."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _get_module(module: str = None) -> str:
    """Safely determines the active module."""
    if module:
        return str(module).upper()
    try:
        from app.services import paths as _paths
        detected = _paths.get_active_module()
        return str(detected).upper() if detected else "VMM"
    except Exception:
        return "VMM"

def fetch_quotations_from_cloud(limit=100, module=None, silent=False, force=False) -> list:
    """Fetch quotations: Supabase First (VMM only), Google Sheets Fallback."""
    active_module = _get_module(module)

    cached = _QUOTES_CACHE["data"]
    if (
        not force
        and _QUOTES_CACHE["module"] == active_module
        and _QUOTES_CACHE["timestamp"]
        and not has_pending_writes()
        and time.time() - _QUOTES_CACHE["timestamp"] < _QUOTES_CACHE_TTL
    ):
        if not silent: print(f"[cloud] ⚡ Cached {active_module} quotations ({len(cached)})")
        return cached if not limit else cached[:limit]

    if not silent: print(f"[cloud] Fetching {active_module} quotations...")
    
    supabase_data = []
    sheet_data = []

    # --- WORKER 1: SUPABASE ---
    def _fetch_supabase():
        sb = get_supabase()
        if not sb: return
        try:
            query = sb.table("quotations").select("*").eq("module", active_module).order("created_at", desc=True)
            response = query.execute()
            for row in response.data:
                record = row.get("data", {}) or {}
                record.update({
                    "id": row.get("id"),
                    "quotation_number": row.get("quotation_number", ""),
                    "grand_total": row.get("grand_total", 0),
                    "status": row.get("status", "Draft"),
                    "module": row.get("module", active_module),
                    "pdf_url": row.get("pdf_url", "")
                })
                supabase_data.append(record)
            if not silent: print(f"[cloud] ✅ Supabase: {len(supabase_data)}")
        except Exception as e:
            if not silent: print(f"[cloud] ❌ Supabase failed: {e}")

    # --- WORKER 2: GOOGLE SHEETS ---
    def _fetch_sheets():
        try:
            # Apps Script cold starts can exceed 15 s; callers run this in the
            # background, so allow a longer timeout instead of losing the data.
            response = requests.get(f"{APPS_SCRIPT_URL}?action=list", timeout=30)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    for row in data.get("rows", []):
                        q_no = str(row.get("Quotation No", ""))
                        if active_module == "VMM" and "VMM" not in q_no.upper(): continue
                        # Crystal owns the CRY (quotation) and PI (proforma) series.
                        if active_module == "CRYSTAL" and not q_no.upper().startswith(("CRY", "PI/")): continue
                        sheet_data.append({
                            "quotation_number": q_no,
                            "date": row.get("Date", ""),
                            "customer_name": row.get("Customer", ""),
                            "customer_company": row.get("Company", ""),
                            "model": row.get("Model", ""),
                            "doc_type": "proforma" if ("prof" in str(row.get("Type", "")).lower() or q_no.upper().startswith("PI/")) else "quotation",
                            "grand_total": row.get("Grand Total", 0),
                            "status": row.get("Status", "Draft"),
                            "items": _parse_sheet_items(row.get("Items")),
                            "totals": _parse_sheet_totals(row.get("Totals")),
                            "module": active_module,
                            "pdf_url": ""
                        })
                    if not silent: print(f"[cloud] ✅ Sheets: {len(sheet_data)}")
        except Exception as e:
            if not silent: print(f"[cloud] ❌ Sheets failed: {e}")

    # --- RUN IN PARALLEL ---
    # Crystal ONLY uses Google Sheets
    if active_module == "CRYSTAL":
        if not silent: print("[cloud] ⚡ Crystal module: Skipping Supabase completely.")
        _fetch_sheets()
    else:
        # VMM uses both
        t1 = threading.Thread(target=_fetch_supabase)
        t2 = threading.Thread(target=_fetch_sheets)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

    # --- MERGE ---
    merged_dict = {}
    for r in supabase_data:
        merged_dict[r["quotation_number"]] = r
    for r in sheet_data:
        q_no = r["quotation_number"]
        if q_no not in merged_dict:
            merged_dict[q_no] = r
        else:
            # Smart repair: take highest value
            try:
                sb_val = float(str(merged_dict[q_no].get("grand_total", 0)).replace(",", "").replace("₹", "").strip() or 0)
                sh_val = float(str(r.get("grand_total", 0)).replace(",", "").replace("₹", "").strip() or 0)
                if sh_val > sb_val:
                    merged_dict[q_no]["grand_total"] = sh_val
            except Exception:
                pass

    final_list = list(merged_dict.values())

    # Hide quotations the user deleted locally. Crystal's sheet source is not
    # immediately writable, so a local tombstone keeps the app consistent.
    if active_module == "CRYSTAL":
        deleted = _load_deleted_quotations()
        if deleted:
            final_list = [
                r for r in final_list
                if str(r.get("quotation_number", "")).strip().upper() not in deleted
            ]

    final_list.sort(key=lambda x: str(x.get("quotation_number", "")), reverse=True)

    _QUOTES_CACHE["module"] = active_module
    _QUOTES_CACHE["data"] = list(final_list)
    _QUOTES_CACHE["timestamp"] = time.time()

    if limit: final_list = final_list[:limit]
    if not silent: print(f"[cloud] ✅ Total Merged: {len(final_list)}")
    return final_list


def upload_quotation_to_cloud(quotation_data: dict, module: str = None) -> bool:
    """Save to Supabase (VMM only) and Google Sheets (Always)."""
    _begin_write()
    try:
        return _upload_quotation_body(quotation_data, module)
    finally:
        _end_write()


def _upload_quotation_body(quotation_data: dict, module: str = None) -> bool:
    active_module = _get_module(module)
    q_no = str(quotation_data.get("quotation_number", ""))

    # A (re)generated quotation is active again.
    if active_module == "CRYSTAL" and q_no:
        _unmark_quotation_deleted(q_no)
    
    raw_total = quotation_data.get("totals", {}).get("grand_total", 0)
    try: grand_total = float(raw_total) if raw_total else 0.0
    except: grand_total = 0.0

    # --- WRITE TO SUPABASE ---
    sb = get_supabase()
    if sb and active_module == "VMM":
        try:
            payload = {
                "quotation_number": q_no,
                "customer_name": str(quotation_data.get("customer_name", "")),
                "model": str(quotation_data.get("model", "")),
                "grand_total": grand_total,
                "data": _sanitize_json(quotation_data), 
                "pdf_url": str(quotation_data.get("pdf_url", "") or quotation_data.get("pdf_path", "")),
                "module": active_module,
                "status": quotation_data.get("status", "Draft")
            }
            sb.table("quotations").insert(payload).execute()
            print(f"[cloud] ✅ {q_no} saved to SUPABASE.")
        except Exception as e:
            print(f"[cloud] ❌ SUPABASE insert failed: {e}")

    # --- WRITE TO GOOGLE SHEETS ---
    try:
        # Bulletproof mapping: handles customer_name, name, or customer
        c_name = quotation_data.get("customer_name") or quotation_data.get("name") or quotation_data.get("customer") or ""
        c_comp = quotation_data.get("customer_company") or quotation_data.get("company") or ""
        c_phone = quotation_data.get("customer_phone") or quotation_data.get("phone") or ""
        c_email = quotation_data.get("customer_email") or quotation_data.get("email") or ""
        c_addr = quotation_data.get("customer_address") or quotation_data.get("address") or ""
        c_city = quotation_data.get("customer_city") or quotation_data.get("city") or ""
        c_state = quotation_data.get("customer_state") or quotation_data.get("state") or ""
        c_pin = quotation_data.get("customer_pincode") or quotation_data.get("pincode") or ""
        c_gst = quotation_data.get("customer_gstin") or quotation_data.get("gstin") or ""
        
        sheet_payload = {
            "action": "quotation",
            "quotation_number": q_no,
            "customer": c_name,
            "company": c_comp,
            "phone": c_phone,
            "email": c_email,
            "address": c_addr,
            "city": c_city,
            "state": c_state,
            "pincode": c_pin,
            "gstin": c_gst,
            "model": quotation_data.get("model", ""),
            "doc_type": quotation_data.get("doc_type", "quotation"),
            "grand_total": grand_total,
            "status": quotation_data.get("status", "Draft"),
            "date": quotation_data.get("date", ""),
            "user": quotation_data.get("user", ""),
            "items": _sanitize_json(quotation_data.get("items") or []),
        }
        res = requests.post(APPS_SCRIPT_URL, json=sheet_payload, timeout=15)
        if res.status_code == 200:
            print(f"[cloud] ✅ {q_no} saved to GOOGLE SHEETS.")
    except Exception as e:
        print(f"[cloud] ❌ GOOGLE SHEETS insert failed: {e}")

    invalidate_quotes_cache()
    return True

# --- OTHER HELPER FUNCTIONS ---
def upload_file_to_cloud(file_path: str, file_name: str) -> str:
    sb = get_supabase()
    if not sb or not os.path.exists(file_path):
        return ""
    try:
        with open(file_path, "rb") as f:
            sb.storage.from_("quotations").upload(path=file_name, file=f, file_options={"content-type": "application/pdf"})
        return sb.storage.from_("quotations").get_public_url(file_name)
    except Exception:
        return ""

def update_quotation_status_in_cloud(quotation_number: str, new_status: str) -> bool:
    invalidate_quotes_cache()

    if _get_module() == "CRYSTAL":
        try:
            res = requests.post(
                APPS_SCRIPT_URL,
                json={
                    "action": "update_status",
                    "quotation_number": quotation_number,
                    "status": new_status,
                },
                timeout=15,
            )
            if res.status_code == 200:
                try:
                    body = res.json()
                except Exception:
                    body = {}
                if isinstance(body, dict) and body.get("status") == "error":
                    print(
                        "[cloud] Sheets status update returned: "
                        f"{body.get('message', 'error')} "
                        "(redeploy tools/apps_script_cloud_sync.gs to enable it)"
                    )
                    return False
                return True
        except Exception as e:
            print(f"[cloud] Sheets status update failed: {e}")
        return False

    sb = get_supabase()
    if not sb: return False
    try:
        sb.table("quotations").update({"status": new_status}).eq("quotation_number", quotation_number).execute()
        return True
    except Exception:
        return False

def _delete_sheet_row(q_no: str) -> None:
    """Remove the sheet row in the background (best effort)."""
    try:
        res = requests.post(
            APPS_SCRIPT_URL,
            json={"action": "delete_quotation", "quotation_number": q_no},
            timeout=20,
        )
        if res.status_code == 200:
            try:
                body = res.json()
            except Exception:
                body = {}
            if isinstance(body, dict) and body.get("status") == "error":
                print(
                    "[cloud] Sheets delete returned: "
                    f"{body.get('message', 'error')} "
                    "(redeploy tools/apps_script_cloud_sync.gs to enable row deletion)"
                )
            else:
                print(f"[cloud] {q_no} deleted from GOOGLE SHEETS.")
    except Exception as e:
        print(f"[cloud] Sheets delete failed: {e}")


def delete_quotation_from_cloud(quotation_number: str) -> bool:
    q_no = str(quotation_number or "").strip()
    if not q_no:
        return False

    # Crystal: delete the Google Sheets row via Apps Script and remember the
    # deletion locally so it stays hidden even before the script is redeployed.
    if _get_module() == "CRYSTAL":
        _mark_quotation_deleted(q_no)
        invalidate_quotes_cache()
        threading.Thread(target=_delete_sheet_row, args=(q_no,), daemon=True).start()
        return True

    if not get_supabase():
        return False
    try:
        get_supabase().table("quotations").delete().eq("quotation_number", q_no).execute()
        invalidate_quotes_cache()
        return True
    except Exception:
        return False


def upload_customer_to_cloud(customer_data: dict, module: str = None) -> bool:
    """Save a customer to Google Sheets (and Supabase if VMM)."""
    _begin_write()
    try:
        return _upload_customer_body(customer_data, module)
    finally:
        _end_write()


def _upload_customer_body(customer_data: dict, module: str = None) -> bool:
    active_module = _get_module(module)
    
    # We only save to Google Sheets for now (since Crystal doesn't use Supabase)
    try:
        payload = {
            "action": "customer",
            "name": customer_data.get("name", ""),
            "company": customer_data.get("company", ""),
            "phone": customer_data.get("phone", ""),
            "email": customer_data.get("email", ""),
            "address": customer_data.get("address", ""),
            "city": customer_data.get("city", ""),
            "state": customer_data.get("state", ""),
            "pincode": customer_data.get("pincode", ""),
            "gstin": customer_data.get("gstin", "")
        }
        res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=15)
        if res.status_code == 200:
            print(f"[cloud] ✅ Customer {payload['name']} saved to GOOGLE SHEETS.")
            invalidate_customers_cache()
            return True
    except Exception as e:
        print(f"[cloud] ❌ GOOGLE SHEETS customer save failed: {e}")
        
    # Also save to Supabase if it's VMM
    sb = get_supabase()
    if sb and active_module == "VMM":
        try:
            sb.table("customers").insert(_sanitize_json(customer_data)).execute()
            print(f"[cloud] ✅ Customer {customer_data.get('name')} saved to SUPABASE.")
            invalidate_customers_cache()
            return True
        except Exception as e:
            print(f"[cloud] ❌ SUPABASE customer save failed: {e}")
            
    return False

def upload_customers_bulk_to_cloud(customers, chunk_size=200, progress=None):
    """Upload many customers through the sheet's bulk endpoint.

    The Apps Script handles de-duplication (phone, email, name+company)
    and only fills blank cells on existing rows. Chunks keep each web
    request short enough for the script execution limit.
    """
    records = [c for c in (customers or []) if isinstance(c, dict)]
    totals = {"added": 0, "updated": 0, "skipped": 0}
    if not records:
        return {"supported": True, **totals}

    chunk_size = max(1, int(chunk_size))
    _begin_write()
    try:
        for start in range(0, len(records), chunk_size):
            chunk = records[start:start + chunk_size]
            payload = {
                "action": "customers_bulk",
                "user": os.environ.get("USERNAME") or "user",
                "customers": chunk,
            }
            try:
                res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=90)
                data = res.json() if res.status_code == 200 else {}
            except Exception as e:
                print(f"[cloud] Customer bulk upload failed: {e}")
                return {"supported": True, "error": str(e), **totals}

            if isinstance(data, dict) and data.get("status") == "error":
                message = str(data.get("message") or "")
                if "Unknown action" in message:
                    print("[cloud] Sheet script has no customers_bulk action "
                          "(redeploy apps_script_cloud_sync.gs)")
                    return {"supported": False, "error": message, **totals}
                return {"supported": True, "error": message, **totals}

            for key in totals:
                try:
                    totals[key] += int(data.get(key) or 0)
                except (TypeError, ValueError):
                    pass
            if progress:
                try:
                    progress(min(start + len(chunk), len(records)))
                except Exception:
                    pass
        invalidate_customers_cache()
    finally:
        _end_write()

    return {"supported": True, **totals}


def fetch_customers_from_cloud(module=None, force=False) -> list:
    """Fetch customers from Supabase (VMM) or Google Sheets (Crystal)."""
    active_module = _get_module(module)

    if (
        not force
        and _CUSTOMERS_CACHE["module"] == active_module
        and _CUSTOMERS_CACHE["timestamp"]
        and not has_pending_writes()
        and time.time() - _CUSTOMERS_CACHE["timestamp"] < _CUSTOMERS_CACHE_TTL
    ):
        return list(_CUSTOMERS_CACHE["data"])

    # --- GOOGLE SHEETS (Crystal) ---
    if active_module == "CRYSTAL":
        try:
            res = requests.get(
                APPS_SCRIPT_URL,
                params={"action": "get_customers"},
                timeout=25,
            )
            if res.status_code != 200:
                print(f"[cloud] Sheets customers HTTP {res.status_code}")
                return []

            data = res.json()
            if isinstance(data, dict) and data.get("status") == "error":
                print(f"[cloud] Sheets customers error: {data.get('message', 'unknown')}")
                return []

            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict):
                rows = data.get("customers")
                if rows is None:
                    rows = data.get("rows") or []
            else:
                rows = []

            customers = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                rec = {
                    "id":         _sheet_text(row.get("id") or row.get("ID")),
                    "name":       _sheet_text(row.get("name") or row.get("Name")),
                    "company":    _sheet_text(row.get("company") or row.get("Company")),
                    "phone":      _sheet_text(row.get("phone") or row.get("Phone")),
                    "email":      _sheet_text(row.get("email") or row.get("Email")),
                    "address":    _sheet_text(row.get("address") or row.get("Address")),
                    "city":       _sheet_text(row.get("city") or row.get("City")),
                    "state":      _sheet_text(row.get("state") or row.get("State")),
                    "pincode":    _sheet_text(row.get("pincode") or row.get("Pincode")),
                    "gstin":      _sheet_text(row.get("gstin") or row.get("GSTIN")).upper(),
                    "created_at": _sheet_text(row.get("created_at") or row.get("Created") or row.get("created")),
                    "updated_at": _sheet_text(row.get("updated_at") or row.get("Updated") or row.get("updated")),
                }
                if rec["name"] or rec["company"]:
                    customers.append(rec)

            if customers:
                print(f"[cloud] Sheets customers: {len(customers)}")
            else:
                print("[cloud] Sheets customers: endpoint returned no rows "
                      "(missing action=get_customers in Apps Script?)")
            _CUSTOMERS_CACHE["module"] = active_module
            _CUSTOMERS_CACHE["data"] = list(customers)
            _CUSTOMERS_CACHE["timestamp"] = time.time()
            return customers
        except Exception as e:
            print(f"[cloud] Sheets customers failed: {e}")
            return []

    # --- SUPABASE (VMM) ---
    sb = get_supabase()
    if sb and active_module == "VMM":
        try:
            query = sb.table("customers").select("*").eq("module", active_module).order("created_at", desc=True)
            response = query.execute()
            _CUSTOMERS_CACHE["module"] = active_module
            _CUSTOMERS_CACHE["data"] = list(response.data or [])
            _CUSTOMERS_CACHE["timestamp"] = time.time()
            return response.data
        except Exception:
            return []
    return []
