"""
CRYSTAL — Full deployment audit.
Run:  python audit.py
"""

import os
import sys
import json
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ---- test tracking ----

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results = []

def test(name, fn):
    try:
        ok, msg = fn()
        results.append((name, ok, msg))
    except Exception as e:
        results.append((name, FAIL, f"{type(e).__name__}: {e}"))


# ---- environment ----

def get_appdata():
    return Path(os.environ.get("APPDATA", str(Path.home()))) / "CRYSTAL"


# ---- tests ----

def t_imports():
    mods = [
        "app.services.paths",
        "app.services.setup_service",
        "app.services.user_service",
        "app.services.activity_log_service",
        "app.services.quotation_history_service",
        "app.services.customer_service",
        "app.services.company_settings_service",
        "app.services.monthly_report_service",
        "app.services.quotation_number_service",
        "app.services.catalog_admin_service",
        "app.services.file_lock",
        "ui.dashboard",
        "ui.quotation_history",
        "ui.activity_log_window",
        "ui.monthly_report_window",
        "ui.setup_wizard",
        "ui.team_activity_window",
        "ui.quotation_form",
        "ui.customer_database",
    ]
    for m in mods:
        __import__(m)
    return PASS, f"{len(mods)} modules imported OK"


def t_data_dir():
    from app.services.paths import get_data_dir
    d = get_data_dir()
    if not d.is_dir():
        return FAIL, f"not a dir: {d}"
    return PASS, f"data dir = {d}"


def t_output_dir():
    from app.services.paths import get_output_dir
    d = get_output_dir()
    if not d.is_dir():
        return FAIL, f"not a dir: {d}"
    return PASS, f"output dir = {d}"


def t_setup_file():
    f = get_appdata() / "setup.json"
    if not f.is_file():
        return WARN, f"no setup.json — wizard will run"
    try:
        s = json.loads(f.read_text(encoding="utf-8"))
    except Exception as e:
        return FAIL, f"invalid json: {e}"
    required = ("user_name", "pc_role", "shared_path")
    missing = [k for k in required if k not in s]
    if missing:
        return FAIL, f"missing fields: {missing}"
    return PASS, f"role={s['pc_role']} user={s['user_name']} path={s['shared_path']}"


def t_shared_path():
    from app.services.setup_service import shared_path
    p = shared_path()
    if p is None:
        return WARN, "no shared_path set"
    return PASS, f"shared_path = {p}"


def t_shared_reachable():
    from app.services.setup_service import shared_path, shared_path_available
    p = shared_path()
    if p is None:
        return WARN, "no shared_path configured"
    if shared_path_available():
        return PASS, f"{p} reachable"
    return WARN, f"{p} NOT reachable (app will fall back)"


def t_user():
    from app.services.user_service import get_current_user, is_admin
    u = get_current_user()
    a = is_admin()
    if not u:
        return WARN, "no user set"
    return PASS, f"user={u} admin={a}"


def t_file_lock():
    from app.services.file_lock import FileLock
    from app.services.paths import get_data_dir
    target = get_data_dir() / "_audit_lock_test"
    with FileLock(target):
        lock_path = target.with_suffix(target.suffix + ".lock")
        if not lock_path.exists():
            return FAIL, "lock file not created"
    if lock_path.exists():
        return FAIL, "lock file not released"
    return PASS, "acquire + release OK"


def t_quotation_read():
    from app.services.quotation_history_service import list_quotations
    records = list_quotations()
    if records is None:
        return FAIL, "returned None"
    return PASS, f"{len(records)} records loaded"


def t_quotation_number():
    from app.services.quotation_number_service import get_next_quotation_number
    try:
        n = get_next_quotation_number()
        return PASS, f"next number = {n}"
    except Exception as e:
        return FAIL, str(e)


def t_customer_read():
    from app.services.customer_service import list_customers
    try:
        cs = list_customers()
        if cs is None:
            cs = []
        return PASS, f"{len(cs)} customers"
    except Exception as e:
        return FAIL, str(e)


def t_company_settings():
    from app.services.company_settings_service import load_settings
    try:
        s = load_settings()
        if s is None:
            return WARN, "settings returned None"
        return PASS, f"company = {s.get('company_name', '?')}"
    except Exception as e:
        return FAIL, str(e)


def t_activity_log_read():
    from app.services.activity_log_service import list_events, count
    try:
        n = count()
        evs = list_events(limit=10)
        return PASS, f"{n} events total, {len(evs)} recent"
    except Exception as e:
        return FAIL, str(e)


def t_activity_log_write():
    from app.services.activity_log_service import log_event, count as cnt
    before = cnt()
    ok = log_event("audit_test", "AUDIT/001", "self-test event")
    after = cnt()
    if not ok:
        return FAIL, "log_event returned False"
    if after != before + 1:
        return FAIL, f"count went {before} → {after}"
    return PASS, f"event logged, count now {after}"


def t_activity_summary():
    from app.services.activity_log_service import get_all_users_summary
    try:
        s = get_all_users_summary()
        return PASS, f"{len(s)} users in summary"
    except Exception as e:
        return FAIL, str(e)


def t_monthly_summary():
    from app.services.monthly_report_service import get_monthly_summary
    from datetime import date
    try:
        s = get_monthly_summary(2026, 10)
        return PASS, f"Oct 2026: {s['count']} quotes, ₹{s['total_value']:.2f}"
    except Exception as e:
        return FAIL, str(e)


def t_monthly_breakdown():
    from app.services.monthly_report_service import get_year_breakdown
    try:
        rows = get_year_breakdown(2026)
        return PASS, f"{len(rows)} months returned"
    except Exception as e:
        return FAIL, str(e)


def t_csv_export():
    from app.services.monthly_report_service import export_csv
    from app.services.paths import get_output_dir
    target = get_output_dir() / "_audit_test.csv"
    try:
        export_csv(2026, 10, str(target))
        if not target.is_file():
            return FAIL, "file not created"
        size = target.stat().st_size
        target.unlink()
        return PASS, f"wrote {size} bytes"
    except Exception as e:
        return FAIL, str(e)


def t_pdf_export():
    from app.services.monthly_report_service import export_pdf
    from app.services.paths import get_output_dir
    target = get_output_dir() / "_audit_test.pdf"
    try:
        export_pdf(2026, 10, str(target))
        if not target.is_file():
            return FAIL, "file not created"
        size = target.stat().st_size
        target.unlink()
        return PASS, f"wrote {size} bytes"
    except Exception as e:
        return FAIL, str(e)


def t_wizard_importable():
    from ui.setup_wizard import run_wizard
    return PASS, "wizard importable"


def t_team_window():
    from ui.team_activity_window import TeamActivity
    return PASS, "TeamActivity window class OK"


# ---- run everything ----

def main():
    print("=" * 70)
    print("  CRYSTAL — Deployment Audit")
    print("=" * 70)
    print()

    tests = [
        ("1. All modules import",        t_imports),
        ("2. Data directory resolves",   t_data_dir),
        ("3. Output directory resolves", t_output_dir),
        ("4. Setup file valid",          t_setup_file),
        ("5. Shared path configured",    t_shared_path),
        ("6. Shared path reachable",     t_shared_reachable),
        ("7. Current user / role",       t_user),
        ("8. File lock works",           t_file_lock),
        ("9. Quotation read",            t_quotation_read),
        ("10. Next quotation number",    t_quotation_number),
        ("11. Customer read",            t_customer_read),
        ("12. Company settings read",    t_company_settings),
        ("13. Activity log read",        t_activity_log_read),
        ("14. Activity log write",       t_activity_log_write),
        ("15. Activity user summary",    t_activity_summary),
        ("16. Monthly report summary",   t_monthly_summary),
        ("17. Monthly year breakdown",   t_monthly_breakdown),
        ("18. CSV export",               t_csv_export),
        ("19. PDF export",               t_pdf_export),
        ("20. Setup wizard",             t_wizard_importable),
        ("21. Team Activity window",     t_team_window),
    ]

    for name, fn in tests:
        test(name, fn)

    # ---- print results ----
    n_pass = sum(1 for _, r, _ in results if r == PASS)
    n_warn = sum(1 for _, r, _ in results if r == WARN)
    n_fail = sum(1 for _, r, _ in results if r == FAIL)

    for name, status, msg in results:
        if status == PASS:
            mark = "✅"
        elif status == WARN:
            mark = "⚠️ "
        else:
            mark = "❌"
        print(f"  {mark}  {name:<35} {msg}")

    print()
    print("=" * 70)
    print(f"  ✅ {n_pass} passed   ⚠️  {n_warn} warnings   ❌ {n_fail} failed")
    print("=" * 70)


if __name__ == "__main__":
    main()
