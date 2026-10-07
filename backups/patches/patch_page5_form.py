"""
Form changes for BuyBack:
- Add self.buyback StringVar
- Add BuyBack input in _render_pricing
- Include buyback in get_form_data()
"""

import shutil
import py_compile
from pathlib import Path


FORM = Path("ui/quotation_form.py")
shutil.copy2(FORM, FORM.with_suffix(".py.BUYBACK_FORM_BACKUP"))
print(f"[backup] {FORM.name}")

s = FORM.read_text(encoding="utf-8")


# ============================================================
# 1. Add self.buyback StringVar (after self.transportation)
# ============================================================

old_var = '''        self.transportation = tk.StringVar(value="0")'''
new_var = '''        self.transportation = tk.StringVar(value="0")
        self.buyback = tk.StringVar(value="0")'''

if "self.buyback = tk.StringVar" in s:
    print("[skip] self.buyback already exists")
elif old_var in s:
    s = s.replace(old_var, new_var, 1)
    print("[ok] self.buyback added")
else:
    print("[warn] transportation StringVar not found")


# ============================================================
# 2. Add BuyBack input in _render_pricing
# Find the "Transportation (₹)" entry and add BuyBack after it
# ============================================================

old_entry = '''        self._make_entry(
            settings,
            "Transportation (₹)",
            self.transportation
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(6, 0)
        )'''

new_entry = '''        self._make_entry(
            settings,
            "Transportation (₹)",
            self.transportation
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(6, 0)
        )

        self._make_entry(
            settings,
            "BuyBack Offer (₹)",
            self.buyback
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(6, 0)
        )'''

if "BuyBack Offer (₹)" in s:
    print("[skip] BuyBack entry already exists")
elif old_entry in s:
    s = s.replace(old_entry, new_entry, 1)
    print("[ok] BuyBack input added to _render_pricing")
else:
    print("[warn] Transportation entry not found")


# ============================================================
# 3. Add trace on buyback to trigger recalculate
# ============================================================

old_trace = '''        self.transportation.trace_add(
            "write",
            lambda *_: self._recalculate()
        )'''

new_trace = '''        self.transportation.trace_add(
            "write",
            lambda *_: self._recalculate()
        )

        self.buyback.trace_add(
            "write",
            lambda *_: self._recalculate()
        )'''

if "self.buyback.trace_add" in s:
    print("[skip] buyback trace already exists")
elif old_trace in s:
    s = s.replace(old_trace, new_trace, 1)
    print("[ok] buyback trace added")
else:
    print("[warn] transportation trace not found")


# ============================================================
# 4. Include buyback in get_form_data()
# ============================================================

old_form_data = '''            "transportation":
                float(self._decimal(
                    self.transportation.get()
                )),'''

new_form_data = '''            "transportation":
                float(self._decimal(
                    self.transportation.get()
                )),

            "buyback":
                float(self._decimal(
                    self.buyback.get()
                )),'''

if '"buyback":' in s and 'self.buyback.get()' in s:
    print("[skip] buyback in get_form_data already present")
elif old_form_data in s:
    s = s.replace(old_form_data, new_form_data, 1)
    print("[ok] buyback added to get_form_data")
else:
    print("[warn] transportation in get_form_data not found")


# ============================================================
# 5. Add BuyBack to _recalculate() summary
# ============================================================

old_recalc = '''            transportation = self._decimal(
                self.transportation.get()
            )

            taxable = (
                subtotal
                + packing
                + transportation
            )'''

new_recalc = '''            transportation = self._decimal(
                self.transportation.get()
            )

            buyback = self._decimal(
                self.buyback.get()
            )

            taxable = (
                subtotal
                + packing
                + transportation
                - buyback
            )

            if taxable < Decimal("0"):
                taxable = Decimal("0")'''

if "buyback = self._decimal" in s:
    print("[skip] recalculate already uses buyback")
elif old_recalc in s:
    s = s.replace(old_recalc, new_recalc, 1)
    print("[ok] recalculate includes buyback")
else:
    print("[warn] recalculate pattern not found")


# ============================================================
# 6. Add buyback to form_data dict — used by the preview builder
# ============================================================

# Add buyback into _render_pricing summary values rows
old_rows = '''        rows = [
            ("Machine + Accessories", "subtotal"),
            ("Packing", "packing"),
            ("Transportation", "transportation"),
            ("Taxable Value", "taxable"),
        ]'''

new_rows = '''        rows = [
            ("Machine + Accessories", "subtotal"),
            ("Packing", "packing"),
            ("Transportation", "transportation"),
            ("BuyBack Offer", "buyback"),
            ("Taxable Value", "taxable"),
        ]'''

if '"BuyBack Offer", "buyback"' in s:
    print("[skip] BuyBack row already in _render_pricing summary")
elif old_rows in s:
    s = s.replace(old_rows, new_rows, 1)
    print("[ok] BuyBack row added to pricing summary")
else:
    print("[warn] pricing summary rows not found")


FORM.write_text(s, encoding="utf-8")

print()
print("=" * 60)
print("Compile check")
print("=" * 60)
try:
    py_compile.compile(str(FORM), doraise=True)
    print("[ok] FORM OK")
    print()
    print("Next:")
    print("  1. Add 'buyback' key to self.summary_values in _create_variables")
    print("     (needed for the 'BuyBack Offer' row in the summary)")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(FORM.with_suffix(".py.BUYBACK_FORM_BACKUP"), FORM)
    print("[restore] reverted")
