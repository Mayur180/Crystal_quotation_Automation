"""Persistent offline queue for Google Sheet pushes.

Crystal screens save every document and customer to local JSON first.
When a sheet push fails (no internet, sheet down, script not deployed)
the payload is stored in data/pending_sync.json and retried later, so a
reboot or a long offline stretch never loses a sync.
"""

import json
import os
import threading
import time
from datetime import datetime

from app.services.paths import get_data_root


_QUEUE_FILENAME = "pending_sync.json"
_MAX_ENTRIES = 500
_MAX_SCRIPT_ERRORS = 10       # drop an entry only after this many script-side errors

_LOCK = threading.RLock()
_PROCESS_LOCK = threading.Lock()
_last_flush = 0.0


def _queue_file():
    return get_data_root() / _QUEUE_FILENAME


def _load():
    try:
        path = _queue_file()
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(entries):
    try:
        path = _queue_file()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(tmp, path)
    except Exception as e:
        print(f"[sync-queue] could not save queue: {e}")


def _dedupe_key(action, payload):
    payload = payload if isinstance(payload, dict) else {}
    if action in ("quotation", "update_status", "delete_quotation"):
        return str(payload.get("quotation_number") or "").strip().upper()
    if action == "customer":
        return "|".join(
            str(payload.get(k) or "").strip().lower()
            for k in ("name", "company", "phone", "email")
        )
    return ""


def enqueue(action, payload, module="Crystal"):
    """Store one failed push. Returns True when persisted."""
    action = str(action or "").strip()
    if not action or not isinstance(payload, dict):
        return False

    entry = {
        "action": action,
        "module": module,
        "payload": payload,
        "key": _dedupe_key(action, payload),
        "queued_at": datetime.now().isoformat(timespec="seconds"),
        "attempts": 0,
    }

    with _LOCK:
        entries = _load()
        key = entry["key"]
        if key:
            # One pending entry per document/customer; newest payload wins.
            entries = [
                e for e in entries
                if not (e.get("action") == action
                        and str(e.get("key") or "") == key)
            ]
        if action == "delete_quotation" and key:
            # A delete supersedes a not-yet-created quotation/status.
            entries = [
                e for e in entries
                if not (e.get("action") in ("quotation", "update_status")
                        and str(e.get("key") or "") == key)
            ]
        entries.append(entry)
        if len(entries) > _MAX_ENTRIES:
            entries = entries[-_MAX_ENTRIES:]
        _save(entries)

    print(f"[sync-queue] queued {action} - {len(entries)} pending")
    return True


def pending_count():
    with _LOCK:
        return len(_load())


def has_pending():
    return pending_count() > 0


def _post_entry(entry):
    """POST one queued payload. Returns (state, message).

    state: "ok" | "network" | "error"
    """
    import requests

    from app.services.google_sheet_service import WEBHOOK_URL

    payload = entry.get("payload") or {}
    try:
        res = requests.post(WEBHOOK_URL, json=payload, timeout=25)
    except Exception as e:
        return "network", f"{type(e).__name__}: {e}"

    if res.status_code != 200:
        return "network", f"HTTP {res.status_code}"

    try:
        body = res.json()
    except Exception:
        body = None

    if isinstance(body, dict) and body.get("status") == "error":
        return "error", str(body.get("message") or "sheet error")

    return "ok", ""


def process_queue(max_items=100):
    """Flush pending pushes, oldest first. Safe to call from any thread."""
    global _last_flush
    if not _PROCESS_LOCK.acquire(blocking=False):
        return {"processed": 0, "remaining": pending_count(), "busy": True}

    processed = 0
    remaining = []
    try:
        with _LOCK:
            entries = _load()
        if not entries:
            _last_flush = time.time()
            return {"processed": 0, "remaining": 0, "busy": False}

        _last_flush = time.time()
        remaining = []

        for idx, entry in enumerate(entries):
            if processed >= max_items:
                remaining.extend(entries[idx:])
                break

            state, message = _post_entry(entry)

            if state == "ok":
                processed += 1
                continue

            if state == "network":
                # Still offline — keep this entry and everything after it.
                remaining.extend(entries[idx:])
                break

            # Script rejected this entry (e.g. sheet not redeployed yet).
            entry["attempts"] = int(entry.get("attempts") or 0) + 1
            entry["last_error"] = message[:200]
            if entry["attempts"] < _MAX_SCRIPT_ERRORS:
                remaining.append(entry)
            else:
                print(f"[sync-queue] dropping {entry.get('action')} "
                      f"({entry.get('key')}): {message}")

        with _LOCK:
            _save(remaining)
    finally:
        _PROCESS_LOCK.release()

    if processed:
        print(f"[sync-queue] flushed {processed} pending push(es), "
              f"{len(remaining)} left")
    return {"processed": processed, "remaining": len(remaining), "busy": False}


def flush_async(min_interval=90):
    """Retry the queue in the background, at most once per interval."""
    if time.time() - _last_flush < min_interval:
        return
    if not has_pending():
        return
    threading.Thread(target=process_queue, daemon=True).start()
