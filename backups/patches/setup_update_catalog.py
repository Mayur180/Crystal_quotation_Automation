"""
Add 'Also update catalog price' checkbox to Step 4 (Pricing).
"""

import shutil
import py_compile
from pathlib import Path


FORM = Path("ui/quotation_form.py")
shutil.copy2(FORM, FORM.with_suffix(".py.UPDATE_CATALOG_BACKUP"))
print(f"[backup] {FORM.name}")

s = FORM.read_text(encoding="utf-8")


# ============================================================
# 1. Add self.update_catalog BooleanVar
# ============================================================

old = '        self.machine_price = tk.StringVar()'
new = '        self.machine_price = tk.StringVar()\n        self.update_catalog = tk.BooleanVar(value=False)'

if 'self.update_catalog = tk.BooleanVar' in s:
    print("[skip] update_catalog already exists")
elif old in s:
    s = s.replace(old, new, 1)
    print("[ok] self.update_catalog added")
else:
    print("[warn] machine_price declaration not found")


# ============================================================
# 2. Add checkbox after the price + qty fields
# ============================================================

old = '''        self.machine_price.trace_add(
            "write",
            lambda *_: self._recalculate()
        )

        self.machine_qty.trace_add(
            "write",
            lambda *_: self._recalculate()
        )

        self.status_text.set(
            "Select a model and enter its price."
        )'''

new = '''        self.machine_price.trace_add(
            "write",
            lambda *_: self._recalculate()
        )

        self.machine_qty.trace_add(
            "write",
            lambda *_: self._recalculate()
        )

        # ---- 'Also update catalog' checkbox ----
        update_box = tk.Frame(card, bg=self.CARD)
        update_box.pack(fill="x", pady=(14, 0))

        tk.Checkbutton(
            update_box,
            text="Also update catalog price for this model",
            variable=self.update_catalog,
            bg=self.CARD,
            activebackground=self.CARD,
            selectcolor="white",
            fg=self.TEXT,
            font=("Arial", 10),
        ).pack(anchor="w")

        tk.Label(
            update_box,
            text=(
                "Unchecked: only this quotation uses the new price.  "
                "Checked: all future quotations for this model will use it."
            ),
            bg=self.CARD,
            fg=self.MUTED,
            font=("Arial", 8, "italic"),
            anchor="w",
        ).pack(anchor="w", padx=(24, 0), pady=(0, 4))

        self.status_text.set(
            "Select a model and enter its price."
        )'''

if 'Also update catalog price' in s:
    print("[skip] checkbox already present")
elif old in s:
    s = s.replace(old, new, 1)
    print("[ok] checkbox added to Step 4")
else:
    print("[warn] pricing section anchor not found")


# ============================================================
# 3. Add _maybe_update_catalog() method before _generate_quotation
# ============================================================

METHOD = '''    def _maybe_update_catalog(self):
        """If the user checked 'Also update catalog', update the
        catalog price for the selected model after confirmation.

        Returns True to continue with quotation generation,
        False to abort (user cancelled the confirmation dialog).
        """
        try:
            wants_update = bool(self.update_catalog.get())
        except Exception:
            wants_update = False

        if not wants_update:
            return True

        model = (self.model.get() or "").strip()
        if not model:
            return True

        try:
            new_price = float(self._decimal(self.machine_price.get()))
        except Exception:
            new_price = 0.0

        if new_price <= 0:
            messagebox.showwarning(
                "Cannot update catalog",
                "Catalog price must be greater than zero.",
                parent=self,
            )
            return True  # let quotation continue without catalog update

        # Show old price in confirmation
        old_price = None
        try:
            from app.services.catalog_service import get_product
            p = get_product(model)
            if p:
                old_price = p.get("price")
        except Exception:
            pass

        if old_price is not None:
            msg = (
                f"Update catalog price for {model}?\\n\\n"
                f"   Old: \\u20b9 {float(old_price):,.2f}\\n"
                f"   New: \\u20b9 {new_price:,.2f}\\n\\n"
                f"This affects all future quotations for this model."
            )
        else:
            msg = (
                f"Update catalog price for {model} to "
                f"\\u20b9 {new_price:,.2f}?\\n\\n"
                f"This affects all future quotations for this model."
            )

        ok = messagebox.askyesno(
            "Update catalog price",
            msg,
            parent=self,
        )
        if not ok:
            return False

        # Perform the update
        try:
            from app.services.catalog_admin_service import update_product
            update_product(model, {"price": new_price})
            messagebox.showinfo(
                "Catalog updated",
                f"Catalog price for {model} is now \\u20b9 {new_price:,.2f}.",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror(
                "Catalog update failed",
                f"Could not update catalog:\\n{e}",
                parent=self,
            )

        return True

'''

marker = "    def _generate_quotation(self):"
if "_maybe_update_catalog" not in s and marker in s:
    s = s.replace(marker, METHOD + marker, 1)
    print("[ok] _maybe_update_catalog method added")
else:
    if "_maybe_update_catalog" in s:
        print("[skip] method already exists")
    else:
        print("[warn] _generate_quotation anchor not found")


# ============================================================
# 4. Hook into _generate_quotation()
# ============================================================

old = '''    def _generate_quotation(self):

        if not self._validate_customer():'''

new = '''    def _generate_quotation(self):

        # Ask about catalog update BEFORE validation
        if not self._maybe_update_catalog():
            return

        if not self._validate_customer():'''

if "_maybe_update_catalog()" not in s.split("def _generate_quotation")[1][:200] if "def _generate_quotation" in s else True:
    if old in s:
        s = s.replace(old, new, 1)
        print("[ok] _generate_quotation hooked")
    else:
        print("[warn] _generate_quotation body anchor not found")

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
    print("Update catalog feature complete.")
    print("=" * 60)
    print()
    print("Test:")
    print("  1. python main.py -> Ctrl+N")
    print("  2. Fill Company + pick a model")
    print("  3. On Pricing step, change price to something obvious")
    print("  4. Check 'Also update catalog price for this model'")
    print("  5. Generate quotation")
    print("  6. Confirm dialog -> Yes")
    print("  7. Verify: python -c from catalog_service import get_product...")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(FORM.with_suffix(".py.UPDATE_CATALOG_BACKUP"), FORM)
    print("[restore] reverted")
