"""
Fallback: when a quotation record lacks phone/email,
look up the customer in the customer database by name.
"""

import shutil
import py_compile
from pathlib import Path


UI = Path("ui/quotation_history.py")
shutil.copy2(UI, UI.with_suffix(".py.FALLBACK_BACKUP"))
print(f"[backup] {UI.name}")

s = UI.read_text(encoding="utf-8")


# ============================================================
# 1. WhatsApp: add fallback phone lookup
# ============================================================

old_wa = '''        # ---- phone cleanup ----
        raw_phone = str(record.get("customer_phone") or "").strip()
        digits = "".join(ch for ch in raw_phone if ch.isdigit())
        if not digits:
            messagebox.showwarning(
                "WhatsApp",
                "No phone number saved for this customer.",
                parent=self,
            )
            return'''

new_wa = '''        # ---- phone cleanup ----
        raw_phone = str(record.get("customer_phone") or "").strip()

        # Fallback: if no phone, look up the customer in the DB
        if not raw_phone:
            try:
                from app.services.customer_service import find_duplicate
                cust = find_duplicate(
                    record.get("customer_name", ""),
                    record.get("customer_company", ""),
                    "",
                    record.get("customer_email", ""),
                )
                if cust:
                    raw_phone = str(cust.get("phone") or "").strip()
            except Exception:
                pass

        digits = "".join(ch for ch in raw_phone if ch.isdigit())
        if not digits:
            messagebox.showwarning(
                "WhatsApp",
                "No phone number saved for this customer.\\n\\n"
                "(Also checked the customer database — no match found.)",
                parent=self,
            )
            return'''

if old_wa in s and "_customer DB fallback" not in s:
    s = s.replace(old_wa, new_wa, 1)
    print("[ok] WhatsApp: fallback added")
elif "Fallback: if no phone" in s:
    print("[skip] WhatsApp: already patched")
else:
    print("[warn] WhatsApp anchor not found")


# ============================================================
# 2. Email: add fallback email lookup
# ============================================================

old_em = '''        to_addr = str(record.get("customer_email") or "").strip()
        if not to_addr or "@" not in to_addr:
            messagebox.showwarning(
                "Email",
                "No email address saved for this customer.",
                parent=self,
            )
            return'''

new_em = '''        to_addr = str(record.get("customer_email") or "").strip()

        # Fallback: if no email, look up the customer in the DB
        if not to_addr or "@" not in to_addr:
            try:
                from app.services.customer_service import find_duplicate
                cust = find_duplicate(
                    record.get("customer_name", ""),
                    record.get("customer_company", ""),
                    record.get("customer_phone", ""),
                    "",
                )
                if cust:
                    to_addr = str(cust.get("email") or "").strip()
            except Exception:
                pass

        if not to_addr or "@" not in to_addr:
            messagebox.showwarning(
                "Email",
                "No email address saved for this customer.\\n\\n"
                "(Also checked the customer database — no match found.)",
                parent=self,
            )
            return'''

if old_em in s and "Fallback: if no email" not in s:
    s = s.replace(old_em, new_em, 1)
    print("[ok] Email: fallback added")
elif "Fallback: if no email" in s:
    print("[skip] Email: already patched")
else:
    print("[warn] Email anchor not found")


UI.write_text(s, encoding="utf-8")

print()
print("=" * 60)
print("Compile check")
print("=" * 60)
try:
    py_compile.compile(str(UI), doraise=True)
    print("[ok] ui/quotation_history.py compiles")
    print()
    print("Done. Now test on an OLD record with no phone/email.")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(UI.with_suffix(".py.FALLBACK_BACKUP"), UI)
    print("[restore] reverted")
