"""
Full end-to-end automated test for CRYSTAL.
Run: python test_end_to_end.py
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


results = []

def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    icon = "✓" if condition else "✗"
    print(f"  [{icon}] {name}" + (f" — {detail}" if detail else ""))


# ============================================================
# SECTION 1 — Imports
# ============================================================
print("\n=== 1. Imports ===")

try:
    from app.services.quotation_history_service import (
        save_quotation, list_quotations, get_quotation,
        delete_quotation, update_quotation_status, count
    )
    check("quotation_history_service", True)
except Exception as e:
    check("quotation_history_service", False, str(e))

try:
    from app.services.customer_service import (
        save_customer, list_customers, get_customer, delete_customer
    )
    check("customer_service", True)
except Exception as e:
    check("customer_service", False, str(e))

try:
    from app.services.google_sheet_service import send_to_sheet
    check("google_sheet_service", True)
except Exception as e:
    check("google_sheet_service", False, str(e))

try:
    from app.services.activity_log_service import list_events, log_event
    check("activity_log_service", True)
except Exception as e:
    check("activity_log_service", False, str(e))

try:
    from app.services.monthly_report_service import get_monthly_summary
    check("monthly_report_service", True)
except Exception as e:
    check("monthly_report_service", False, str(e))

try:
    from app.services.catalog_service import get_product
    check("catalog_service", True)
except Exception as e:
    check("catalog_service", False, str(e))


# ============================================================
# SECTION 2 — Google Sheet webhook
# ============================================================
print("\n=== 2. Google Sheet webhook ===")

test_q = {
    "action":           "quotation",
    "date":             datetime.now().strftime("%Y-%m-%d"),
    "user":             "TEST_USER",
    "quotation_number": f"AUTO_TEST/{datetime.now().strftime('%H%M%S')}",
    "customer":         "Auto Test Customer",
    "company":          "Auto Test Co",
    "phone":            "9999000000",
    "email":            "auto@test.com",
    "address":          "Auto Street 123",
    "city":             "Pune",
    "state":            "Maharashtra",
    "pincode":          "411026",
    "gstin":            "27ABCDE0000F1Z0",
    "model":            "AA-9022SA",
    "grand_total":      "500000",
    "status":           "Draft",
}

ok = send_to_sheet(test_q)
check("Send quotation to Sheet", ok)

test_c = {
    "action":   "customer",
    "user":     "TEST_USER",
    "name":     "Auto Test Customer",
    "company":  "Auto Test Co",
    "phone":    "9999000000",
    "email":    "auto@test.com",
    "address":  "Auto Street 123",
    "city":     "Pune",
    "state":    "Maharashtra",
    "pincode":  "411026",
    "gstin":    "27ABCDE0000F1Z0",
}

ok = send_to_sheet(test_c)
check("Send customer to Sheet", ok)


# ============================================================
# SECTION 3 — Quotation save + Google Sheet hook
# ============================================================
print("\n=== 3. Quotation save ===")

before_count = count()

test_number = f"AUTO/E2E/{datetime.now().strftime('%H%M%S')}"

result = save_quotation({
    "quotation_number": test_number,
    "quotation_date":   datetime.now().strftime("%Y-%m-%d"),
    "customer_name":    "E2E Test",
    "customer_company": "E2E Co",
    "customer_phone":   "9876500000",
    "customer_email":   "e2e@test.com",
    "customer_address": "123 E2E Street",
    "customer_city":    "Pune",
    "customer_state":   "Maharashtra",
    "customer_pincode": "411026",
    "customer_gstin":   "27ABCDE1111F1Z1",
    "contact_person":   "Mr. E2E",
    "model":            "AA-9022SA",
    "totals":           {"grand_total": 550000},
    "docx_path":        "D:/test/fake.docx",
    "pdf_path":         None,
})

check("save_quotation returned dict", isinstance(result, dict))

after_count = count()
check("Record count increased", after_count == before_count + 1, f"{before_count} → {after_count}")

# Verify the saved record has full customer fields
rec = get_quotation(test_number)
if rec:
    check("customer_phone saved", rec.get("customer_phone") == "9876500000")
    check("customer_email saved", rec.get("customer_email") == "e2e@test.com")
    check("customer_address saved", rec.get("customer_address") == "123 E2E Street")
    check("customer_city saved", rec.get("customer_city") == "Pune")
    check("customer_state saved", rec.get("customer_state") == "Maharashtra")
    check("customer_pincode saved", rec.get("customer_pincode") == "411026")
    check("customer_gstin saved", rec.get("customer_gstin") == "27ABCDE1111F1Z1")
    check("contact_person saved", rec.get("contact_person") == "Mr. E2E")
    check("status defaults to Draft", rec.get("status") == "Draft")
else:
    check("get_quotation returns record", False, "not found")


# ============================================================
# SECTION 4 — Update status + list + filter
# ============================================================
print("\n=== 4. Status + list ===")

ok = update_quotation_status(test_number, "Sent")
check("update_quotation_status", ok)

rec = get_quotation(test_number)
check("status changed to Sent", rec and rec.get("status") == "Sent")

# Filter by status
sent_list = list_quotations(status="Sent")
check("list_quotations(status='Sent') works", len(sent_list) > 0)

# Filter by search
search_list = list_quotations(search="E2E")
check("list_quotations(search='E2E') works", len(search_list) > 0)


# ============================================================
# SECTION 5 — Customer service
# ============================================================
print("\n=== 5. Customer ===")

import uuid
cust_name = f"E2E Customer {uuid.uuid4().hex[:6]}"
saved = save_customer({
    "name":    cust_name,
    "company": "E2E Co",
    "phone":   f"9800{uuid.uuid4().int % 100000:05d}",
    "email":   f"{uuid.uuid4().hex[:6]}@test.com",
})
# save_customer returns (record, created_bool) tuple
check("save_customer returned tuple", isinstance(saved, tuple) and len(saved) == 2)
check("save_customer returned record", isinstance(saved[0], dict) and saved[0].get("name") == cust_name)

customers = list_customers()
found = any(c.get("name") == cust_name for c in customers)
check("customer in list", found)


# ============================================================
# SECTION 6 — Activity log
# ============================================================
print("\n=== 6. Activity log ===")

ev_before = len(list_events(limit=1000))
log_event("e2e_test", test_number, "automated test event")
ev_after = len(list_events(limit=1000))
check("event logged", ev_after == ev_before + 1)


# ============================================================
# SECTION 7 — Reports
# ============================================================
print("\n=== 7. Monthly report ===")

today = datetime.now()
summary = get_monthly_summary(today.year, today.month)
check("get_monthly_summary works", isinstance(summary, dict))
check("summary has count", "count" in summary)

from app.services.monthly_report_service import get_year_breakdown, export_csv, export_pdf
breakdown = get_year_breakdown(today.year)
check("get_year_breakdown works", len(breakdown) == 12)

from app.services.paths import get_output_dir
tmp_csv = get_output_dir() / "_e2e_test.csv"
tmp_pdf = get_output_dir() / "_e2e_test.pdf"

try:
    export_csv(today.year, today.month, str(tmp_csv))
    check("export_csv works", tmp_csv.is_file())
    tmp_csv.unlink()
except Exception as e:
    check("export_csv works", False, str(e))

try:
    export_pdf(today.year, today.month, str(tmp_pdf))
    check("export_pdf works", tmp_pdf.is_file())
    tmp_pdf.unlink()
except Exception as e:
    check("export_pdf works", False, str(e))


# ============================================================
# SECTION 8 — Catalog
# ============================================================
print("\n=== 8. Catalog ===")

for model in ["AA-9011M", "AA-9022SA", "AA-9053V"]:
    p = get_product(model)
    check(f"catalog: {model}", p is not None and p.get("model") == model)


# ============================================================
# SECTION 9 — Cleanup
# ============================================================
print("\n=== 9. Cleanup ===")

# Delete the test quotation
ok = delete_quotation(test_number)
check("delete_quotation works", ok)

rec = get_quotation(test_number)
check("deleted record not found", rec is None)


# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
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
else:
    print("\nAll tests passed!")
