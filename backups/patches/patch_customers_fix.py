import shutil
import py_compile
from pathlib import Path

CUST = Path("ui/customer_database.py")
shutil.copy2(CUST, CUST.with_suffix(".py.NEWQUOTE_FIX_BACKUP"))
print("[backup]", CUST.with_suffix(".py.NEWQUOTE_FIX_BACKUP"))

s = CUST.read_text(encoding="utf-8")

# ---- 1. Remove duplicate button lines (keep ONE) ----
btn_line = '        self._btn(right, "New Quotation", self._open_quotation_for_selected).pack(side="right", padx=(0, 8), pady=14)\n'
count = s.count(btn_line)
if count > 1:
    # Keep first occurrence, drop the rest
    first = s.find(btn_line)
    after_first = first + len(btn_line)
    rest = s[after_first:].replace(btn_line, "", count - 1)
    s = s[:after_first] + rest
    print(f"[ok] removed {count - 1} duplicate button(s), kept 1")
elif count == 1:
    print("[skip] only one button — fine")
else:
    print("[warn] button line not found")

# ---- 2. Add the missing _open_quotation_for_selected method ----
METHOD = '''    def _open_quotation_for_selected(self):
        """Open a New Quotation form pre-filled from the selected customer."""
        if not self.selected_id:
            messagebox.showinfo(
                "New Quotation",
                "Select a customer first.",
                parent=self,
            )
            return

        customer = None
        try:
            from app.services.customer_service import get_customer
            customer = get_customer(self.selected_id)
        except Exception:
            customer = None

        if not customer:
            messagebox.showerror(
                "New Quotation",
                "Could not load the selected customer.",
                parent=self,
            )
            return

        try:
            from ui.quotation_form import QuotationForm
        except Exception as e:
            messagebox.showerror(
                "New Quotation",
                f"Could not open Quotation form:\\\\n{e}",
                parent=self,
            )
            return

        try:
            QuotationForm(self.master, self, prefill=customer)
        except Exception as e:
            messagebox.showerror(
                "New Quotation",
                f"Could not open Quotation form:\\\\n{e}",
                parent=self,
            )

'''
marker = "    def _edit(self):"
if "_open_quotation_for_selected(self)" not in s and marker in s:
    s = s.replace(marker, METHOD + marker, 1)
    print("[ok] _open_quotation_for_selected method added")
else:
    if "_open_quotation_for_selected(self)" in s:
        print("[skip] method already exists")
    else:
        print("[WARN] _edit anchor not found")

# ---- 3. Ensure messagebox is imported ----
if "from tkinter import ttk, messagebox" not in s and "import messagebox" not in s:
    old = "from tkinter import ttk"
    new = "from tkinter import ttk, messagebox"
    if old in s:
        s = s.replace(old, new, 1)
        print("[ok] added messagebox import")
else:
    print("[skip] messagebox already imported")

CUST.write_text(s, encoding="utf-8")

print()
try:
    py_compile.compile(str(CUST), doraise=True)
    print("[check] CUST OK")
except py_compile.PyCompileError as e:
    print("[check] FAIL:", e)
    shutil.copy2(CUST.with_suffix(".py.NEWQUOTE_FIX_BACKUP"), CUST)
    print("[restore] reverted")
