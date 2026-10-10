"""
Extend quotation flow with full customer data + send to Google Sheet.
"""
import shutil
import py_compile
from pathlib import Path


ROOT = Path.cwd()


# ============================================================
# 1. quotation_generator.py — extend result dict
# ============================================================

GEN = ROOT / "quotation_generator.py"
shutil.copy2(GEN, GEN.with_suffix(".py.FULL_CUSTOMER_BACKUP"))
print(f"[backup] {GEN.name}")

s = GEN.read_text(encoding="utf-8")

old_result = '''    result = {
        "path": str(
            output_path
        ),

        "docx_path": str(
            output_path
        ),

        "pdf_path": (
            str(pdf_path)
            if pdf_path
            else None
        ),

        "quotation_number": quotation_number,

        "quotation_date": quotation_date,

        "model": model,

        "customer_name": customer_name,

        "customer_company": customer_company,

        "totals": totals,
    }'''

new_result = '''    result = {
        "path": str(output_path),
        "docx_path": str(output_path),
        "pdf_path": (str(pdf_path) if pdf_path else None),
        "quotation_number": quotation_number,
        "quotation_date": quotation_date,
        "model": model,

        # ---- customer summary ----
        "customer_name":    customer_name,
        "customer_company": customer_company,

        # ---- full customer block ----
        "customer_phone":   (customer_phone or phone or ""),
        "customer_email":   (customer_email or email or ""),
        "customer_address": (customer_address or address or ""),
        "customer_city":    (kwargs.get("city") or ""),
        "customer_state":   (kwargs.get("state") or ""),
        "customer_pincode": (kwargs.get("pincode") or ""),
        "customer_gstin":   (kwargs.get("gstin") or ""),
        "contact_person":   (kwargs.get("contact_person") or ""),

        "totals": totals,
    }'''

if old_result in s:
    s = s.replace(old_result, new_result, 1)
    GEN.write_text(s, encoding="utf-8")
    print("[ok] generator: result dict extended with customer fields")
else:
    print("[warn] generator: result dict pattern not found")


# ============================================================
# 2. quotation_history_service.py — extend save_quotation
# ============================================================

SVC = ROOT / "app" / "services" / "quotation_history_service.py"
shutil.copy2(SVC, SVC.with_suffix(".py.FULL_CUSTOMER_BACKUP"))
print(f"[backup] {SVC.name}")

s = SVC.read_text(encoding="utf-8")

# Extend record dict
old_record = '''    record = {
        "quotation_number": _text(result.get("quotation_number")),
        "date":             _text(result.get("quotation_date")),
        "customer_name":    _text(result.get("customer_name")),
        "customer_company": _text(result.get("customer_company")),
        "model":            _text(result.get("model")),
        "grand_total":      _decimal_str(grand),
        "docx_path":        _text(result.get("docx_path") or result.get("path")),
        "pdf_path":         _text(result.get("pdf_path")),
        "created_at":       datetime.now().isoformat(timespec="seconds"),
        "status":           "Draft",
    }'''

new_record = '''    record = {
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
    }'''

if old_record in s:
    s = s.replace(old_record, new_record, 1)
    print("[ok] service: record extended")
else:
    print("[warn] service: record pattern not found")

# Extend Google Sheet payload
old_payload = '''        send_to_sheet({
            'date':             record.get('date', ''),
            'user':             _user,
            'quotation_number': record.get('quotation_number', ''),
            'customer':         record.get('customer_name', ''),
            'company':          record.get('customer_company', ''),
            'model':            record.get('model', ''),
            'grand_total':      record.get('grand_total', ''),
            'status':           record.get('status', 'Draft'),
        })'''

new_payload = '''        send_to_sheet({
            'action':           'quotation',
            'date':             record.get('date', ''),
            'user':             _user,
            'quotation_number': record.get('quotation_number', ''),
            'customer':         record.get('customer_name', ''),
            'company':          record.get('customer_company', ''),
            'phone':            record.get('customer_phone', ''),
            'email':            record.get('customer_email', ''),
            'address':          record.get('customer_address', ''),
            'city':             record.get('customer_city', ''),
            'state':            record.get('customer_state', ''),
            'pincode':          record.get('customer_pincode', ''),
            'gstin':            record.get('customer_gstin', ''),
            'model':            record.get('model', ''),
            'grand_total':      record.get('grand_total', ''),
            'status':           record.get('status', 'Draft'),
        })'''

if old_payload in s:
    s = s.replace(old_payload, new_payload, 1)
    print("[ok] service: sheet payload extended")
else:
    print("[warn] service: sheet payload pattern not found")

SVC.write_text(s, encoding="utf-8")


# ============================================================
# 3. customer_service.py — send on customer save
# ============================================================

CUST = ROOT / "app" / "services" / "customer_service.py"
shutil.copy2(CUST, CUST.with_suffix(".py.FULL_CUSTOMER_BACKUP"))
print(f"[backup] {CUST.name}")

s = CUST.read_text(encoding="utf-8")

# Find the end of save_customer — add webhook before "return"
# Look for the pattern where save_customer returns the record
marker = "def save_customer(data, customer_id=None):"
if marker in s:
    # find the "return record" inside save_customer
    idx = s.index(marker)
    # find next "def " after marker
    next_def = s.find("\ndef ", idx + 10)
    if next_def < 0:
        next_def = len(s)
    function_body = s[idx:next_def]

    # Look for the last "return " before next_def
    return_idx = function_body.rfind("    return ")
    if return_idx > 0:
        indent = "    "
        hook = (
            "\n" + indent + "# ---- Send to Google Sheet (fire and forget) ----\n"
            + indent + "try:\n"
            + indent + "    from app.services.google_sheet_service import send_to_sheet\n"
            + indent + "    import os as _os\n"
            + indent + "    _user = _os.environ.get('USERNAME') or 'user'\n"
            + indent + "    send_to_sheet({\n"
            + indent + "        'action':  'customer',\n"
            + indent + "        'user':    _user,\n"
            + indent + "        'name':    _text(_result.get('name', '')) if isinstance(_result, dict) else _text(data.get('name', '')),\n"
            + indent + "        'company': _text(_result.get('company', '')) if isinstance(_result, dict) else _text(data.get('company', '')),\n"
            + indent + "        'phone':   _text(_result.get('phone', '')) if isinstance(_result, dict) else _text(data.get('phone', '')),\n"
            + indent + "        'email':   _text(_result.get('email', '')) if isinstance(_result, dict) else _text(data.get('email', '')),\n"
            + indent + "        'address': _text(_result.get('address', '')) if isinstance(_result, dict) else _text(data.get('address', '')),\n"
            + indent + "        'city':    '',\n"
            + indent + "        'state':   '',\n"
            + indent + "        'pincode': '',\n"
            + indent + "        'gstin':   '',\n"
            + indent + "    })\n"
            + indent + "except Exception:\n"
            + indent + "    pass\n"
        )

        # Insert hook before the return, but we need to use `return_result` — the value being returned
        # Simpler: just append the hook right before the return
        # But we need a variable holding the return value

        # Actually: easier approach — modify the return statement to store first
        return_stmt = function_body[return_idx:function_body.find("\n", return_idx)]
        # e.g. "    return record"
        # Extract the value name
        parts = return_stmt.split("return", 1)
        if len(parts) == 2:
            value_name = parts[1].strip()
            new_return = (
                indent + "_result = " + value_name + "\n"
                + hook
                + indent + "return _result"
            )
            function_body_new = function_body[:return_idx] + new_return + function_body[function_body.find("\n", return_idx):]
            s = s[:idx] + function_body_new + s[next_def:]
            print("[ok] customer: hook added before return")
        else:
            print("[warn] customer: could not parse return statement")
    else:
        print("[warn] customer: no return found in save_customer")
else:
    print("[warn] customer: save_customer not found")

CUST.write_text(s, encoding="utf-8")


# ============================================================
# 4. Compile check
# ============================================================

print()
print("=" * 60)
print("Compile check")
print("=" * 60)

for p in [GEN, SVC, CUST]:
    try:
        py_compile.compile(str(p), doraise=True)
        print(f"[ok] {p.relative_to(ROOT)}")
    except py_compile.PyCompileError as e:
        print(f"[FAIL] {p.relative_to(ROOT)}: {e}")

print()
print("Done. Test:")
print("  1. python main.py")
print("  2. Create a new quotation with full customer data")
print("  3. Check Google Sheet for the new row")
print("  4. Save a new customer, check Customers tab")
