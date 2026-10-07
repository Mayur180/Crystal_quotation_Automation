import shutil
import py_compile
from pathlib import Path

CUST = Path("ui/customer_database.py")
shutil.copy2(CUST, CUST.with_suffix(".py.NEWQUOTE_BACKUP"))
print("[backup]", CUST.with_suffix(".py.NEWQUOTE_BACKUP"))

s = CUST.read_text(encoding="utf-8")

# ---- 1. Add right-click menu + Ctrl+N binding after the Double-1 bind ----
old = '''        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._edit())'''

new = '''        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._edit())

        # Ctrl+N → new quotation for selected customer
        try:
            self.bind("<Control-n>", lambda _e: self._open_quotation_for_selected())
        except Exception:
            pass

        # Right-click menu
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(
            label="New Quotation",
            command=self._open_quotation_for_selected,
        )
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(
            label="Edit",
            command=self._edit,
        )
        self._ctx_menu.add_command(
            label="Delete",
            command=self._delete,
        )

        def _show_ctx(event):
            row = self.tree.identify_row(event.y)
            if not row:
                return
            self.tree.selection_set(row)
            try:
                self._on_select()
            except Exception:
                pass
            self._ctx_menu.tk_popup(event.x_root, event.y_root)

        self.tree.bind("<Button-3>", _show_ctx)'''

if "_open_quotation_for_selected" not in s and old in s:
    s = s.replace(old, new, 1)
    print("[ok] right-click menu + Ctrl+N added")
else:
    print("[skip/warn] right-click binding")

# ---- 2. Add the _open_quotation_for_selected method before _edit ----
METHOD = '''    def _open_quotation_for_selected(self):
        """Open a New Quotation form pre-filled from the selected customer."""
        if not self.selected_id:
            from tkinter import messagebox as _mb
            _mb.showinfo(
                "New Quotation",
                "Select a customer first.",
                parent=self,
            )
            return

        try:
            from app.services.customer_service import get_customer
        except Exception:
            try:
                from app.services.customer_service import get_customer
            except Exception:
                get_customer = None

        customer = None
        try:
            if get_customer is not None:
                customer = get_customer(self.selected_id)
        except Exception:
            customer = None

        if not customer:
            from tkinter import messagebox as _mb
            _mb.showerror(
                "New Quotation",
                "Could not load the selected customer.",
                parent=self,
            )
            return

        try:
            from ui.quotation_form import QuotationForm
        except Exception as e:
            from tkinter import messagebox as _mb
            _mb.showerror(
                "New Quotation",
                f"Could not open Quotation form:\\n{e}",
                parent=self,
            )
            return

        try:
            QuotationForm(self.master, self, prefill=customer)
        except Exception as e:
            from tkinter import messagebox as _mb
            _mb.showerror(
                "New Quotation",
                f"Could not open Quotation form:\\n{e}",
                parent=self,
            )

'''
marker = "    def _edit(self):"
if "_open_quotation_for_selected" not in s and marker in s:
    s = s.replace(marker, METHOD + marker, 1)
    print("[ok] _open_quotation_for_selected method added")
else:
    print("[skip/warn] _edit anchor")

# ---- 3. Add a New Quotation button to the bottom action bar ----
# Find the action bar construction. Look for a pattern where _btn or tk.Button
# is used for "Close" or similar, and insert our button before it.
# We'll search for common patterns.
insert_done = False
for candidate in (
    'self._btn(right, "Close", self.destroy)',
    'self._btn(right, "Close", self.close)',
    'self._btn(right, "Close"',
    'tk.Button(right, text="Close"',
):
    if candidate in s:
        # Insert a sibling BEFORE the Close button
        idx = s.index(candidate)
        # Find the line start
        line_start = s.rfind("\n", 0, idx) + 1
        # Compose new button line(s) — match indentation
        indent = s[line_start:idx]
        new_btn = (
            indent + 'self._btn(right, "New Quotation", ' +
            'self._open_quotation_for_selected).pack(side="right", padx=(0, 8), pady=14)\n'
        )
        s = s[:line_start] + new_btn + s[line_start:]
        insert_done = True
        print("[ok] New Quotation button inserted in bottom bar")
        break

if not insert_done:
    print("[skip/warn] could not find Close button — button not added")
    print("       You can still use right-click or Ctrl+N")

CUST.write_text(s, encoding="utf-8")

print()
try:
    py_compile.compile(str(CUST), doraise=True)
    print("[check] CUST OK")
except py_compile.PyCompileError as e:
    print("[check] FAIL:", e)
    shutil.copy2(CUST.with_suffix(".py.NEWQUOTE_BACKUP"), CUST)
    print("[restore] reverted")
