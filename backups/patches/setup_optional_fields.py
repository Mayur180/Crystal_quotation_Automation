"""
Make Company (Step 1) and Model (Step 2) the only required fields.
Everything else becomes optional.

Pricing: allow empty / ₹0 with a warning.
"""

import re
import shutil
import py_compile
from pathlib import Path


FORM = Path("ui/quotation_form.py")
shutil.copy2(FORM, FORM.with_suffix(".py.OPTIONAL_FIELDS_BACKUP"))
print(f"[backup] {FORM.name}")

s = FORM.read_text(encoding="utf-8")

# ============================================================
# 1. Replace _validate_customer — require only `company`
# ============================================================

new_validate_customer = '''    def _validate_customer(self):
        """Only COMPANY is required. Everything else is optional."""
        company = (self.company.get() or "").strip()
        if not company:
            messagebox.showerror(
                "Company required",
                "Please enter the company name.",
                parent=self,
            )
            return False
        return True

'''

# match from "def _validate_customer" up to the next "def " at 4-space indent
pat = re.compile(
    r'    def _validate_customer\(self\):.*?(?=\n    def )',
    re.DOTALL,
)
if pat.search(s):
    s = pat.sub(new_validate_customer, s, count=1)
    print("[ok] _validate_customer: only company required")
else:
    print("[warn] _validate_customer not found")


# ============================================================
# 2. Replace _validate_product — require only `model`
# ============================================================

new_validate_product = '''    def _validate_product(self):
        """Only MODEL is required. Category is optional."""
        model = (self.model.get() or "").strip()
        if not model:
            messagebox.showerror(
                "Product required",
                "Please select a model.",
                parent=self,
            )
            return False
        return True

'''

pat = re.compile(
    r'    def _validate_product\(self\):.*?(?=\n    def )',
    re.DOTALL,
)
if pat.search(s):
    s = pat.sub(new_validate_product, s, count=1)
    print("[ok] _validate_product: only model required")
else:
    print("[warn] _validate_product not found")


# ============================================================
# 3. Replace _validate_pricing — allow empty, warn but continue
# ============================================================

new_validate_pricing = '''    def _validate_pricing(self):
        """Pricing is optional.

        - Empty machine price -> warn but continue (grand total = 0)
        - Empty quantity -> default to 1 silently
        - GST type stays strict (must be one of three)
        """
        price = self._number(self.machine_price.get())
        qty = self._number(self.machine_qty.get())

        # default quantity to 1 if empty
        if qty <= 0:
            try:
                self.machine_qty.set("1")
            except Exception:
                pass

        # if price is empty or zero, warn but let the user continue
        if price <= 0:
            ok = messagebox.askyesno(
                "Price is empty",
                "Machine price is empty or zero.\\n\\n"
                "Continue anyway? (grand total will be \\u20b9 0)",
                parent=self,
            )
            if not ok:
                return False

        # GST type must be one of the three known values
        if self.gst_type.get() not in (
            "CGST + SGST", "IGST", "No GST",
        ):
            messagebox.showerror(
                "Invalid GST type",
                "Please select CGST + SGST, IGST, or No GST.",
                parent=self,
            )
            return False

        return True

'''

pat = re.compile(
    r'    def _validate_pricing\(self\):.*?(?=\n    # ==|\n    def |\Z)',
    re.DOTALL,
)
if pat.search(s):
    s = pat.sub(new_validate_pricing + "\n\n", s, count=1)
    print("[ok] _validate_pricing: allows empty, warns but continues")
else:
    print("[warn] _validate_pricing not found")


# ============================================================
# 4. Remove the * from "Customer name  *"
# ============================================================

old = 'text="Customer name  *"'
new = 'text="Customer name"'
if old in s:
    s = s.replace(old, new, 1)
    print("[ok] label: Customer name * removed")
else:
    print("[warn] Customer name label not found")


# ============================================================
# 5. Remove the * from "State  *"
# ============================================================

old = 'text="State  *"'
new = 'text="State"'
if old in s:
    s = s.replace(old, new, 1)
    print("[ok] label: State * removed")
else:
    print("[warn] State label not found")


# ============================================================
# 6. Save + compile
# ============================================================

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
    print("Optional fields setup complete.")
    print("=" * 60)
    print()
    print("Test:")
    print("  1. python main.py")
    print("  2. Ctrl+N -> New Quotation")
    print("  3. Try 'Continue' with EMPTY form -> only Company error")
    print("  4. Fill Company + skip to Product -> only Model error")
    print("  5. Skip Pricing -> warning dialog, click Yes to continue")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(FORM.with_suffix(".py.OPTIONAL_FIELDS_BACKUP"), FORM)
    print("[restore] reverted")
