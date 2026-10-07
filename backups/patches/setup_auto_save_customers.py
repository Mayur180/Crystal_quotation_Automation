"""
Auto-save new customers when a quotation is generated.

Hooks into _generate_quotation() to check if the customer
exists in the DB, and creates one if not.
"""

import shutil
import py_compile
from pathlib import Path


FORM = Path("ui/quotation_form.py")
shutil.copy2(FORM, FORM.with_suffix(".py.AUTOSAVE_CUSTOMERS_BACKUP"))
print(f"[backup] {FORM.name}")

s = FORM.read_text(encoding="utf-8")


# ============================================================
# 1. Add helper method _auto_save_customer()
# ============================================================

METHOD = '''    def _auto_save_customer(self, data):
        """Save the current quotation's customer to the customer database
        if they don't already exist.

        Called before generating a quotation.
        """
        try:
            from app.services.customer_service import (
                save_customer,
                find_duplicate,
                touch_last_used,
            )
        except Exception:
            return  # service not available

        name = (data.get("customer_name") or "").strip()
        company = (data.get("company") or "").strip()
        phone = (data.get("phone") or "").strip()
        email = (data.get("email") or "").strip()

        # Need at least a name or company to save
        if not name and not company:
            return

        # Check if this customer already exists
        try:
            existing = find_duplicate(name, company, phone, email)
        except Exception:
            existing = None

        if existing:
            # Update last_used timestamp
            try:
                cid = existing.get("id")
                if cid:
                    touch_last_used(cid)
            except Exception:
                pass
            return

        # Save new customer
        try:
            payload = {
                "name": name,
                "company": company,
                "phone": phone,
                "email": email,
                "address": (data.get("address") or "").strip(),
                "city": (data.get("city") or "").strip(),
                "state": (data.get("state") or "").strip(),
                "pincode": (data.get("pincode") or "").strip(),
                "gstin": (data.get("gstin") or "").strip(),
            }
            save_customer(payload)
        except Exception:
            pass  # don't break quotation on customer save failure

'''

marker = "    def _generate_quotation(self):"
if "_auto_save_customer" not in s and marker in s:
    s = s.replace(marker, METHOD + marker, 1)
    print("[ok] _auto_save_customer method added")
elif "_auto_save_customer" in s:
    print("[skip] method already exists")
else:
    print("[warn] _generate_quotation anchor not found")


# ============================================================
# 2. Hook into _generate_quotation()
# ============================================================

# Find the line in _generate_quotation where `data = self.get_form_data()`
# and insert our call right after it.
old = '''        data = self.get_form_data()

        if generate_quotation is None:'''

new = '''        data = self.get_form_data()

        # ---- auto-save new customers before generating ----
        self._auto_save_customer(data)

        if generate_quotation is None:'''

if old in s and "self._auto_save_customer(data)" not in s:
    s = s.replace(old, new, 1)
    print("[ok] hooked into _generate_quotation")
elif "self._auto_save_customer(data)" in s:
    print("[skip] already hooked")
else:
    print("[warn] anchor in _generate_quotation not found")


# ============================================================
# 3. Also hook into _open_preview() so it saves before preview too
# ============================================================

old = '''    def _open_preview(self):
        """
        Compute the current quotation data and open the six-page preview.
        Does NOT increment the offer counter — generation does that later.
        """

        # ---- 1. Validate everything (same checks as generate) ----
        if not self._validate_customer():
            self._load_step(1)
            return
        if not self._validate_product():
            self._load_step(2)
            return
        if not self._validate_pricing():
            self._load_step(4)
            return

        # ---- 2. Build data ----
        data = self.get_form_data()'''

new = '''    def _open_preview(self):
        """
        Compute the current quotation data and open the six-page preview.
        Does NOT increment the offer counter — generation does that later.
        """

        # ---- 1. Validate everything (same checks as generate) ----
        if not self._validate_customer():
            self._load_step(1)
            return
        if not self._validate_product():
            self._load_step(2)
            return
        if not self._validate_pricing():
            self._load_step(4)
            return

        # ---- 2. Build data ----
        data = self.get_form_data()

        # ---- auto-save new customers ----
        self._auto_save_customer(data)'''

if old in s and "self._auto_save_customer(data)" not in s.split("def _open_preview")[1][:600]:
    s = s.replace(old, new, 1)
    print("[ok] also hooked into _open_preview")
else:
    if "self._auto_save_customer(data)" in s:
        print("[skip] preview hook already present or no match")
    else:
        print("[warn] preview anchor not found")

FORM.write_text(s, encoding="utf-8")

print()
print("=" * 60)
print("Compile check")
print("=" * 60)
try:
    py_compile.compile(str(FORM), doraise=True)
    print("[ok] ui/quotation_form.py compiles")
    print()
    print("=" * 60)
    print("Auto-save new customers installed.")
    print("=" * 60)
    print()
    print("Test:")
    print("  1. python main.py -> Ctrl+N")
    print("  2. Enter NEW customer name + company")
    print("  3. Complete the quotation and finalize")
    print("  4. Check: from app.services.customer_service import list_customers")
    print("     -> should now include the new customer")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(FORM.with_suffix(".py.AUTOSAVE_CUSTOMERS_BACKUP"), FORM)
    print("[restore] reverted")
