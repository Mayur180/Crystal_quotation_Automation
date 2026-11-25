"""
CRYSTAL / ARMATECH ASSOCIATES
Google Sheet integration via Apps Script webhook.

Sends quotation data to a Google Sheet whenever a quotation is saved.
Never raises — if Sheets is unreachable, the app continues normally.
"""

import json
import urllib.request
import urllib.error


# ---- Paste your Apps Script Web App URL here ----
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwhhqEsHfFmh8Iv4ndlSbTcKiuDuDFMaee1k5dsPaXNmZpSked5adzzOCu-N6UxiO83ZQ/exec"


# The sheet handler reads customer/company/phone/... but Crystal callers
# send customer_name/customer_company/... — mirror them before posting.
_CUSTOMER_ALIASES = (
    ("customer", "customer_name"),
    ("company", "customer_company"),
    ("phone", "customer_phone"),
    ("email", "customer_email"),
    ("address", "customer_address"),
    ("city", "customer_city"),
    ("state", "customer_state"),
    ("pincode", "customer_pincode"),
    ("gstin", "customer_gstin"),
)


def _with_customer_keys(data):
    if not isinstance(data, dict):
        return data
    if not any(key in data for key in ("customer_name", "customer_company")):
        return data
    out = dict(data)
    for target, source in _CUSTOMER_ALIASES:
        if not out.get(target) and out.get(source):
            out[target] = out[source]
    return out


def _enqueue_failed(data):
    """Keep a failed push so the sync queue can retry it later."""
    try:
        action = str((data or {}).get("action") or "").strip()
        if not action or action == "login":
            # Login events are timestamped audit rows — replaying them late
            # would only confuse the sheet.
            return
        from app.services.sync_queue import enqueue
        enqueue(action, data, module="Crystal")
    except Exception as e:
        print(f"[google-sheet] could not queue payload: {e}")


def send_to_sheet(data):
    """POST a dict to the webhook. Returns True on success, False on failure.

    Never raises — logs errors to stdout only. Failures are queued in
    data/pending_sync.json so an offline PC syncs once it reconnects.
    """
    if not WEBHOOK_URL or "PASTE" in WEBHOOK_URL:
        print("[google-sheet] webhook URL not configured")
        return False

    payload_data = _with_customer_keys(data)

    try:
        payload = json.dumps(payload_data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "CRYSTAL-Quotation/1.0",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            if resp.status == 200:
                print(f"[google-sheet] sent OK: {data.get('quotation_number')}")
                try:
                    from app.services.sync_queue import flush_async
                    flush_async()
                except Exception:
                    pass
                return True
            else:
                print(f"[google-sheet] HTTP {resp.status}: {body[:200]}")
    except urllib.error.HTTPError as e:
        print(f"[google-sheet] HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        print(f"[google-sheet] URL error: {e.reason}")
    except Exception as e:
        print(f"[google-sheet] unexpected error: {type(e).__name__}: {e}")

    _enqueue_failed(payload_data)
    return False


def fetch_leads_from_sheet():
    """Fetch leads from the Google Sheet via the Apps Script webhook.
    
    Returns:
        list: The list of leads (can be empty if the sheet is empty)
        None: If the connection failed (so the caller knows NOT to overwrite local data)
    """
    import requests
    
    try:
        response = requests.get(
            WEBHOOK_URL,
            params={"action": "get_leads"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "leads" in data:
                return data["leads"]
            elif isinstance(data, dict) and data.get("status") == "ok":
                # Success but no "leads" key — means empty sheet
                return []
        print(f"[fetch_leads] HTTP {response.status_code}: {response.text[:200]}")
        return None
    except Exception as e:
        print(f"[fetch_leads] Error: {e}")
        return None
