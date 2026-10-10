"""
CRYSTAL — Full code audit.
Runs every check possible without GUI interaction.
"""

import sys
import os
import json
import traceback
from pathlib import Path
from datetime import datetime

# Force UTF-8 output on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


results = []

def check(name, fn):
    """Run a test function. fn returns (bool, str)."""
    try:
        ok, detail = fn()
        status = "PASS" if ok else "FAIL"
        results.append((name, status, detail))
        mark = "OK" if ok else "XX"
        print(f"  [{mark}] {name}" + (f" — {detail}" if detail else ""))
    except Exception as e:
        results.append((name, "FAIL", f"{type(e).__name__}: {e}"))
        print(f"  [XX] {name} — EXCEPTION: {type(e).__name__}: {e}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ============================================================
# SECTION 1 — MODULE IMPORTS
# ============================================================
section("1. Module imports")

MODULES = [
    "app.services.paths",
    "app.services.settings_service",
    "app.services.company_settings_service",
    "app.services.customer_service",
    "app.services.catalog_service",
    "app.services.catalog_admin_service",
    "app.services.quotation_history_service",
    "app.services.quotation_number_service",
    "app.services.activity_log_service",
    "app.services.monthly_report_service",
    "app.services.google_sheet_service",
    "app.services.file_lock",
    "app.services.amount_in_words",
    "app.services.states_service",
    "app.company",
    "quotation_generator",
    "ui.dashboard",
    "ui.quotation_form",
    "ui.quotation_preview",
    "ui.quotation_history",
    "ui.customer_database",
    "ui.product_manager",
    "ui.company_settings",
    "ui.activity_log_window",
    "ui.monthly_report_window",
]

for m in MODULES:
    check(f"import {m}", lambda mod=m: (True, "") if __import__(mod) else (False, ""))


# ============================================================
# SECTION 2 — DATA FILES
# ============================================================
section("2. Data files")

from app.services.paths import get_data_dir, get_output_dir

DATA = get_data_dir()
OUT = get_output_dir()

check("data dir exists", lambda: (DATA.is_dir(), str(DATA)))
check("output dir exists", lambda: (OUT.is_dir(), str(OUT)))

check("catalog.json exists", lambda: ((DATA / "catalog.json").is_file(), ""))
check("company_settings.json exists", lambda: ((DATA / "company_settings.json").is_file(), ""))
check("custom_terms.json exists", lambda: ((DATA / "custom_terms.json").is_file(), ""))
check("customers.json exists", lambda: ((DATA / "customers.json").is_file(), ""))
check("quotations.json exists", lambda: ((DATA / "quotations.json").is_file(), ""))
check("activity_log.jsonl exists", lambda: ((DATA / "activity_log.jsonl").is_file(), ""))


# ============================================================
# SECTION 3 — JSON DATA VALIDITY
# ============================================================
section("3. JSON data validity")

def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

check("catalog.json valid", lambda: (isinstance(_load_json(DATA / "catalog.json"), (dict, list)), ""))
check("company_settings.json valid", lambda: (isinstance(_load_json(DATA / "company_settings.json"), dict), ""))
check("custom_terms.json valid", lambda: (isinstance(_load_json(DATA / "custom_terms.json"), list), ""))
check("customers.json valid", lambda: (isinstance(_load_json(DATA / "customers.json"), list), ""))
check("quotations.json valid", lambda: (isinstance(_load_json(DATA / "quotations.json"), list), ""))


# ============================================================
# SECTION 4 — COMPANY SETTINGS
# ============================================================
section("4. Company settings")

from app.services.company_settings_service import load_settings, save_settings

def test_settings_load():
    s = load_settings()
    if not isinstance(s, dict):
        return False, "not a dict"
    required = ["name", "state", "brand", "email"]
    missing = [k for k in required if not s.get(k)]
    if missing:
        return False, f"missing: {missing}"
    return True, f"name={s['name']}"

check("load_settings works", test_settings_load)


# ============================================================
# SECTION 5 — SETTINGS SERVICE (output folder)
# ============================================================
section("5. Settings service (output folder)")

from app.services.settings_service import get_output_folder, set_output_folder, default_output_folder

def test_get_output_folder():
    p = get_output_folder()
    return p.is_dir(), str(p)

check("get_output_folder returns valid dir", test_get_output_folder)


# ============================================================
# SECTION 6 — CATALOG
# ============================================================
section("6. Catalog")

from app.services.catalog_service import get_product, get_products, get_product_categories

def test_catalog_products():
    prods = get_products()
    return len(prods) >= 16, f"{len(prods)} products"

check("catalog has products", test_catalog_products)

def test_catalog_categories():
    cats = get_product_categories()
    return len(cats) >= 4, f"{len(cats)} categories"

check("catalog has categories", test_catalog_categories)

for model in ["AA-9011M", "AA-9022SA", "AA-9033A", "AA-9043AC", "AA-9053V"]:
    check(f"get_product({model})", lambda m=model: (get_product(m) is not None, ""))


# ============================================================
# SECTION 7 — QUOTATION NUMBER SERVICE
# ============================================================
section("7. Quotation number service")

from app.services.quotation_number_service import get_next_quotation_number, get_current_quotation_number

def test_next_number():
    n = get_next_quotation_number()
    return bool(n) and len(str(n)) > 5, str(n)

check("get_next_quotation_number works", test_next_number)

def test_current_number():
    n = get_current_quotation_number()
    return bool(n), str(n)

check("get_current_quotation_number works", test_current_number)


# ============================================================
# SECTION 8 — CUSTOMER SERVICE
# ============================================================
section("8. Customer service")

from app.services.customer_service import (
    save_customer, list_customers, get_customer, delete_customer,
    find_duplicate, count as cust_count
)

check("list_customers works", lambda: (isinstance(list_customers(), list), f"{len(list_customers())} customers"))


# ============================================================
# SECTION 9 — QUOTATION HISTORY SERVICE
# ============================================================
section("9. Quotation history service")

from app.services.quotation_history_service import (
    list_quotations, get_quotation, count as qh_count,
    update_quotation_status, delete_quotation
)

check("list_quotations works", lambda: (isinstance(list_quotations(), list), f"{len(list_quotations())} records"))
check("list_quotations(limit=5)", lambda: (isinstance(list_quotations(limit=5), list), ""))
check("list_quotations(search='x')", lambda: (isinstance(list_quotations(search="x"), list), ""))
check("list_quotations(status='Sent')", lambda: (isinstance(list_quotations(status="Sent"), list), ""))
check("count works", lambda: (isinstance(qh_count(), int), f"count={qh_count()}"))


# ============================================================
# SECTION 10 — ACTIVITY LOG
# ============================================================
section("10. Activity log")

from app.services.activity_log_service import (
    log_event, list_events, count as al_count, clear_log
)

def test_log():
    before = al_count()
    log_event("audit_test", "AUDIT/001", "full audit test")
    after = al_count()
    return after == before + 1, f"{before} → {after}"

check("log_event works", test_log)
check("list_events works", lambda: (isinstance(list_events(limit=10), list), f"{len(list_events(limit=10))} events"))


# ============================================================
# SECTION 11 — MONTHLY REPORT
# ============================================================
section("11. Monthly report")

from app.services.monthly_report_service import (
    get_monthly_summary, get_year_breakdown, list_years,
    export_csv, export_pdf
)

def test_summary():
    s = get_monthly_summary(2026, 10)
    return isinstance(s, dict) and "count" in s, f"count={s.get('count')}"

check("get_monthly_summary works", test_summary)

def test_breakdown():
    b = get_year_breakdown(2026)
    return len(b) == 12, f"{len(b)} months"

check("get_year_breakdown works", test_breakdown)

def test_years():
    y = list_years()
    return isinstance(y, list) and len(y) > 0, str(y)

check("list_years works", test_years)

def test_csv_export():
    target = OUT / "_audit_test.csv"
    export_csv(2026, 10, str(target))
    ok = target.is_file()
    if ok:
        target.unlink()
    return ok, ""

check("export_csv works", test_csv_export)

def test_pdf_export():
    target = OUT / "_audit_test.pdf"
    export_pdf(2026, 10, str(target))
    ok = target.is_file()
    if ok:
        target.unlink()
    return ok, ""

check("export_pdf works", test_pdf_export)


# ============================================================
# SECTION 12 — GOOGLE SHEET
# ============================================================
section("12. Google Sheet webhook")

from app.services.google_sheet_service import send_to_sheet

def test_sheet_ping():
    return send_to_sheet({
        "action": "quotation",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "user": "AUDIT_USER",
        "quotation_number": f"AUDIT/{datetime.now().strftime('%H%M%S')}",
        "customer": "Audit Customer",
        "company": "Audit Co",
        "phone": "9999000001",
        "email": "audit@test.com",
        "address": "Audit Street",
        "city": "Pune",
        "state": "Maharashtra",
        "pincode": "411026",
        "gstin": "27ABCDE0000F1Z0",
        "model": "AA-9022SA",
        "grand_total": "100",
        "status": "Draft",
    }), "sent"

check("Google Sheet webhook works", test_sheet_ping)


# ============================================================
# SECTION 13 — GENERATOR IMPORTS
# ============================================================
section("13. Generator imports")

def test_generator_import():
    from quotation_generator import generate_quotation
    return callable(generate_quotation), ""

check("generate_quotation importable", test_generator_import)

def test_generator_helpers():
    from quotation_generator import _resolve_product
    p = _resolve_product("AA-9022SA")
    return p is not None, ""

check("_resolve_product works", test_generator_helpers)


# ============================================================
# SECTION 14 — UI IMPORTS + INSTANTIATION (Tk-only)
# ============================================================
section("14. UI instantiation")

import tkinter as tk
root = tk.Tk()
root.withdraw()

def test_dashboard_creation():
    from ui.dashboard import Dashboard
    d = Dashboard()
    exists = d.winfo_exists() == 1
    d.destroy()
    return exists, ""

check("Dashboard creates OK", test_dashboard_creation)

def test_company_settings_creation():
    from ui.company_settings import CompanySettings
    w = CompanySettings(root)
    exists = w.winfo_exists() == 1
    # Check the loaded values
    name_val = w._vars.get("name")
    folder_val = w._vars.get("output_folder")
    name_ok = name_val and name_val.get() == "ARMATECH ASSOCIATES"
    folder_ok = folder_val and folder_val.get()
    w.destroy()
    return exists and name_ok and folder_ok, f"name={name_val.get() if name_val else 'N/A'}"

check("CompanySettings creates + loads", test_company_settings_creation)

def test_quotation_history_creation():
    from ui.quotation_history import QuotationHistory
    w = QuotationHistory(root)
    exists = w.winfo_exists() == 1
    w.destroy()
    return exists, ""

check("QuotationHistory creates OK", test_quotation_history_creation)

def test_activity_log_creation():
    from ui.activity_log_window import ActivityLog
    w = ActivityLog(root)
    exists = w.winfo_exists() == 1
    w.destroy()
    return exists, ""

check("ActivityLog creates OK", test_activity_log_creation)

def test_monthly_report_creation():
    from ui.monthly_report_window import MonthlyReport
    w = MonthlyReport(root)
    exists = w.winfo_exists() == 1
    w.destroy()
    return exists, ""

check("MonthlyReport creates OK", test_monthly_report_creation)

def test_quotation_form_creation():
    from ui.quotation_form import QuotationForm
    w = QuotationForm(root, root)
    exists = w.winfo_exists() == 1
    w.destroy()
    return exists, ""

check("QuotationForm creates OK", test_quotation_form_creation)

def test_customer_database_creation():
    from ui.customer_database import CustomerDatabase
    w = CustomerDatabase(root)
    exists = w.winfo_exists() == 1
    w.destroy()
    return exists, ""

check("CustomerDatabase creates OK", test_customer_database_creation)

def test_product_manager_creation():
    from ui.product_manager import ProductManager
    w = ProductManager(root)
    exists = w.winfo_exists() == 1
    w.destroy()
    return exists, ""

check("ProductManager creates OK", test_product_manager_creation)

root.destroy()


# ============================================================
# SUMMARY
# ============================================================
print()
print("=" * 60)
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
print(f"  {passed} passed   {failed} failed")
print("=" * 60)

if failed:
    print("\nFailed checks:")
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  ✗ {name}: {detail}")
    sys.exit(1)
