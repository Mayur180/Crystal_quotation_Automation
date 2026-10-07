"""Re-apply auto-save-customer feature."""

import shutil
import py_compile
from pathlib import Path


FORM = Path("ui/quotation_form.py")
shutil.copy2(FORM, FORM.with_suffix(".py.AUTOSAVE_REDO_BACKUP"))
print(f"[backup] {FORM.name}")

s = FORM.read_text(encoding="utf-8")


# ============================================================
# 1. Insert _auto_save_customer method before _generate_quotation
# ============================================================

METHOD = '''    def _auto_save_customer(self, data):
        """Save the current quotation's customer to the customer database
        if they don't already exist. Called before generating a quotation.
        """
        try:
            from app.services.customer_service import (
                save_customer,
                find_duplicate,
                touch_last_used,
            )
        except Exception:
            return

        name = (data.get("customer_name") or "").strip()
        company = (data.get("company") or "").strip()
        phone = (data.get("phone") or "").strip()
        email = (data.get("email") or "").strip()

        if not name and not company:
            return

        try:
            existing = find_duplicate(name, company, phone, email)
        except Exception:
            existing = None

        if existing:
            try:
                cid = existing.get("id")
                if cid:
                    touch_last_used(cid)
            except Exception:
                pass
            return

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
            pass

'''

marker = "    def _generate_quotation(self):"
if "_auto_save_customer" not in s and marker in s:
    s = s.replace(marker, METHOD + marker, 1)
    print("[ok] _auto_save_customer method added")
elif "_auto_save_customer" in s:
    print("[skip] method already present")
else:
    print("[warn] _generate_quotation anchor not found")


# ============================================================
# 2. Call it inside _generate_quotation after `data = self.get_form_data()`
# ============================================================

old = """        data = self.get_form_data()

        if generate_quotation is None:"""

new = """        data = self.get_form_data()

        # ---- auto-save new customers before generating ----
        self._auto_save_customer(data)

        if generate_quotation is None:"""

if old in s and "self._auto_save_customer(data)" not in s:
    s = s.replace(old, new, 1)
    print("[ok] hooked into _generate_quotation")
elif "self._auto_save_customer(data)" in s:
    print("[skip] already hooked")
else:
    print("[warn] anchor in _generate_quotation not found")


# ============================================================
# 3. Also hook into _open_preview
# ============================================================

old = '''        # ---- 2. Build data ----
        data = self.get_form_data()'''

new = '''        # ---- 2. Build data ----
        data = self.get_form_data()

        # ---- auto-save new customers ----
        self._auto_save_customer(data)'''

if old in s and s.count("self._auto_save_customer(data)") < 2:
    s = s.replace(old, new, 1)
    print("[ok] also hooked into _open_preview")
else:
    print("[skip] preview hook (already present or not found)")


FORM.write_text(s, encoding="utf-8")

print()
print("=" * 60)
print("Compile check")
print("=" * 60)
try:
    py_compile.compile(str(FORM), doraise=True)
    print("[ok] FORM OK")
    print()
    print("Features now present:")
    print("  - _maybe_update_catalog:", s.count("_maybe_update_catalog"))
    print("  - _auto_save_customer:  ", s.count("_auto_save_customer"))
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(FORM.with_suffix(".py.AUTOSAVE_REDO_BACKUP"), FORM)
    print("[restore] reverted")
