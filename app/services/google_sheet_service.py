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
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbzhtawFNa_Wlo644joUFEJvRJV9LiiMXu7En_sOzWH2fK6rvVG_XEIqiTE6OgNMnyQ/exec"


def send_to_sheet(data):
    """POST a dict to the webhook. Returns True on success, False on failure.

    Never raises — logs errors to stdout only.
    """
    if not WEBHOOK_URL or "PASTE" in WEBHOOK_URL:
        print("[google-sheet] webhook URL not configured")
        return False

    try:
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
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
                return True
            else:
                print(f"[google-sheet] HTTP {resp.status}: {body[:200]}")
                return False
    except urllib.error.HTTPError as e:
        print(f"[google-sheet] HTTP error {e.code}: {e.reason}")
        return False
    except urllib.error.URLError as e:
        print(f"[google-sheet] URL error: {e.reason}")
        return False
    except Exception as e:
        print(f"[google-sheet] unexpected error: {type(e).__name__}: {e}")
        return False


def fetch_leads_from_sheet():
    """Fetch leads from the Google Sheet via the Apps Script webhook."""
    import requests
    import json
    
    # The Apps Script URL (same as WEBHOOK_URL but with action=get_leads)
    # We need to send a GET request to the webhook to fetch data
    try:
        # We assume WEBHOOK_URL is defined at the top of this file
        # We send a GET request with action=get_leads
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
    except Exception as e:
        print(f"[fetch_leads] Error: {e}")
    
    return []
