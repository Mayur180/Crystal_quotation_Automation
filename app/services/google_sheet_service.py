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
WEBHOOK_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbw4cUZ52MY4BcvMtgDWMRjSsZbjATZbDsYGacHYo5mlBl9E8Awtqz4SooRoetmqviV9aQ"
    "/exec"
)


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
