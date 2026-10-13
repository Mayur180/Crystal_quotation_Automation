"""CRYSTAL — Read quotations from the Google Sheet (GET / list)."""

import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import date, timedelta


def _base_url():
    try:
        from app.services.google_sheet_service import WEBHOOK_URL
        return WEBHOOK_URL
    except Exception:
        return ""


def _iso_date(value):
    if not value:
        return ""
    s = str(value).strip()
    if not s:
        return ""
    if "T" in s:
        return s.split("T", 1)[0]
    return s[:10]


def fetch_quotations(user=None, since_days=None, search=None):
    url = _base_url()
    if not url:
        return [], "Webhook URL not configured"

    params = ["action=list"]
    if user and user != "All":
        params.append("user=" + urllib.parse.quote(str(user)))
    if since_days is not None:
        since = (date.today() - timedelta(days=int(since_days))).isoformat()
        params.append("since=" + since)

    full_url = url + "?" + "&".join(params)

    try:
        req = urllib.request.Request(
            full_url,
            headers={"User-Agent": "CRYSTAL-Quotation/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")

        data = json.loads(body)
        if not isinstance(data, dict) or data.get("status") != "ok":
            return [], "Sheet returned: " + str(data.get("message", "unknown"))

        rows = data.get("rows", []) or []
        norm = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            r = dict(r)
            r["_date"] = _iso_date(r.get("Date"))
            norm.append(r)

        if search:
            needle = str(search).strip().lower()
            if needle:
                def match(r):
                    for k in ("Quotation No", "Customer", "Company",
                              "Model", "Phone", "Email"):
                        if needle in str(r.get(k, "")).lower():
                            return True
                    return False
                norm = [r for r in norm if match(r)]

        def sort_key(r):
            return (r.get("_date") or "", str(r.get("Quotation No") or ""))
        norm.sort(key=sort_key, reverse=True)

        return norm, None

    except urllib.error.HTTPError as e:
        return [], "HTTP %s: %s" % (e.code, e.reason)
    except urllib.error.URLError as e:
        return [], "Network error: %s" % e.reason
    except Exception as e:
        return [], "%s: %s" % (type(e).__name__, e)
