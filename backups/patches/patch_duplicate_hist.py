import shutil
import py_compile
from pathlib import Path

HIST = Path("ui/quotation_history.py")
shutil.copy2(HIST, HIST.with_suffix(".py.DUPLICATE_BACKUP"))
print("[backup]", HIST.with_suffix(".py.DUPLICATE_BACKUP"))

s = HIST.read_text(encoding="utf-8")

# --- 1. Add Ctrl+D + right-click menu right after the Escape binding ---
old = '        self.bind("<Escape>", lambda _e: self.destroy())'
new = '''        self.bind("<Escape>", lambda _e: self.destroy())

        # Ctrl+D on tree or window → duplicate
        self.tree.bind("<Control-d>", lambda _e: self._duplicate())
        self.bind("<Control-d>", lambda _e: self._duplicate())

        # Right-click context menu
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(
            label="Open Word", command=self._open_docx,
        )
        self._ctx_menu.add_command(
            label="Duplicate quotation", command=self._duplicate,
        )
        self._ctx_menu.add_command(
            label="Set status...", command=self._set_status,
        )
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(
            label="Delete", command=self._delete,
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

if "<Control-d>" not in s and old in s:
    s = s.replace(old, new, 1)
    print("[ok] Ctrl+D + right-click menu added")
elif "<Control-d>" in s:
    print("[skip] already patched")
else:
    print("[WARN] Escape binding not found")

# --- 2. Add _duplicate method before _current_record ---
METHOD = '''    def _duplicate(self):
        """Open a new Quotation form pre-filled from the selected record."""
        record = self._current_record()
        if not record:
            messagebox.showinfo(
                "Duplicate",
                "Select a quotation first.",
                parent=self,
            )
            return

        try:
            from ui.quotation_form import QuotationForm
        except Exception as e:
            messagebox.showerror(
                "Duplicate",
                f"Could not open Quotation form:\\n{e}",
                parent=self,
            )
            return

        try:
            QuotationForm(self.master, self, prefill=record)
        except Exception as e:
            messagebox.showerror(
                "Duplicate",
                f"Could not open Quotation form:\\n{e}",
                parent=self,
            )

'''
marker = "    def _current_record(self):"
if "def _duplicate" not in s and marker in s:
    s = s.replace(marker, METHOD + marker, 1)
    print("[ok] _duplicate method added")
elif "def _duplicate" in s:
    print("[skip] _duplicate already exists")
else:
    print("[WARN] _current_record marker not found")

HIST.write_text(s, encoding="utf-8")

# --- compile ---
print()
try:
    py_compile.compile(str(HIST), doraise=True)
    print("[check] HIST OK")
except py_compile.PyCompileError as e:
    print("[check] FAIL:", e)
    shutil.copy2(HIST.with_suffix(".py.DUPLICATE_BACKUP"), HIST)
    print("[restore] reverted")
