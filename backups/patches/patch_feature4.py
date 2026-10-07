"""Feature 4: Quotation Status Tracking."""
import shutil
import py_compile
from pathlib import Path

ROOT = Path.cwd()
SVC = ROOT / "app" / "services" / "quotation_history_service.py"
UI  = ROOT / "ui" / "quotation_history.py"
SVC_BKP = SVC.with_suffix(".py.FEATURE4_BACKUP")
UI_BKP  = UI.with_suffix(".py.FEATURE4_BACKUP")

STATUSES = ("Draft", "Sent", "Accepted", "Rejected", "Expired")

# ============================================================
# SERVICE LAYER
# ============================================================
sv = SVC.read_text(encoding="utf-8")
shutil.copy2(SVC, SVC_BKP)
print("[backup]", SVC_BKP)

# 1a. Insert VALID_STATUSES + update_quotation_status before def get_quotation
marker_svc = "def get_quotation(quotation_number):"
new_svc_code = """VALID_STATUSES = ("Draft", "Sent", "Accepted", "Rejected", "Expired")


def update_quotation_status(quotation_number, status):
    \"\"\"Update the status field of a stored quotation.
    Returns True if a record was updated, False otherwise.
    \"\"\"
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status!r}")
    target = _text(quotation_number)
    if not target:
        return False
    records = _load_raw()
    updated = False
    for r in records:
        if _text(r.get("quotation_number")) == target:
            r["status"] = status
            updated = True
    if not updated:
        return False
    try:
        _save_raw(records)
        return True
    except Exception:
        return False


"""
if "def update_quotation_status" not in sv and marker_svc in sv:
    sv = sv.replace(marker_svc, new_svc_code + marker_svc, 1)
    print("[ok] service: update_quotation_status added")
else:
    print("[WARN] service: marker or function missing")

# 1b. Add status to save_quotation record dict
old_save = "        \"created_at\":       datetime.now().isoformat(timespec=\"seconds\"),"
new_save = "        \"created_at\":       datetime.now().isoformat(timespec=\"seconds\"),\n        \"status\":           \"Draft\","
if "\"status\":" not in sv:
    if old_save in sv:
        sv = sv.replace(old_save, new_save, 1)
        print("[ok] service: save_quotation writes status")
    else:
        print("[WARN] service: save_quotation created_at line not found")
else:
    print("[skip] service: status already in save_quotation")

# 1c. Extend list_quotations signature + add status filter
old_sig = "def list_quotations(limit=None, search=None):"
new_sig = "def list_quotations(limit=None, search=None, status=None):"
if old_sig in sv:
    sv = sv.replace(old_sig, new_sig, 1)
    print("[ok] service: list_quotations signature extended")
else:
    print("[WARN] service: list_quotations signature not found")

# Insert status filter right before "if limit is not None:"
old_lim = "    if limit is not None:"
new_lim = """    if status and status != "All":
        sval = str(status).strip().lower()
        records = [
            r for r in records
            if (r.get(\"status\") or \"Draft\").lower() == sval
        ]

    if limit is not None:
"""
if "if status and status" not in sv and old_lim in sv:
    sv = sv.replace(old_lim, new_lim, 1)
    print("[ok] service: status filter added")
else:
    print("[skip/WARN] service: status filter")

SVC.write_text(sv, encoding="utf-8")

# ============================================================
# UI LAYER
# ============================================================
ui = UI.read_text(encoding="utf-8")
shutil.copy2(UI, UI_BKP)
print("[backup]", UI_BKP)

# 2a. Add status_var to __init__
old_init = "        self.from_date_var = tk.StringVar()\n        self.to_date_var = tk.StringVar()"
new_init = "        self.from_date_var = tk.StringVar()\n        self.to_date_var = tk.StringVar()\n        self.status_var = tk.StringVar(value=\"All\")"
if "self.status_var" not in ui and old_init in ui:
    ui = ui.replace(old_init, new_init, 1)
    print("[ok] ui: status_var added")
else:
    print("[WARN] ui: __init__ marker not found")

# 2b. Add Status combobox to _build_search (before the Clear button)
old_clear_btn = "        tk.Button(\n            bar, text=\"Clear\","
new_clear_btn = """        _label(bar, "Status", pad=(12, 6))
        status_cb = ttk.Combobox(
            bar,
            textvariable=self.status_var,
            values=("All", "Draft", "Sent", "Accepted", "Rejected", "Expired"),
            state="readonly",
            width=10,
            font=("Arial", 9),
        )
        status_cb.pack(side="left", ipady=3)
        status_cb.bind("<<ComboboxSelected>>", lambda _e: self._reload())

        tk.Button(
            bar, text="Clear","""
if "status_cb" not in ui and old_clear_btn in ui:
    ui = ui.replace(old_clear_btn, new_clear_btn, 1)
    print("[ok] ui: Status combobox added")
else:
    print("[WARN] ui: _build_search Clear button marker not found")

# 2c. Add status column to _build_table
old_cols = """        cols = ("offer_no", "date", "customer", "company",
                "model", "total", "files")"""
new_cols = """        cols = ("offer_no", "date", "status", "customer", "company",
                "model", "total", "files")"""
if old_cols in ui and "\"status\"" not in ui.split("cols = (")[1].split(")")[0]:
    ui = ui.replace(old_cols, new_cols, 1)
    print("[ok] ui: cols extended")
else:
    print("[skip/WARN] ui: cols")

# 2d. Add status heading + width
old_h = "            \"date\": \"Date\","
new_h = "            \"date\": \"Date\",\n            \"status\": \"Status\","
if "\"status\": \"Status\"" not in ui and old_h in ui:
    ui = ui.replace(old_h, new_h, 1)
    print("[ok] ui: heading added")
else:
    print("[skip/WARN] ui: heading")

old_w = "            \"date\": 105,"
new_w = "            \"date\": 105,\n            \"status\": 90,"
if "\"status\": 90" not in ui and old_w in ui:
    ui = ui.replace(old_w, new_w, 1)
    print("[ok] ui: width added")
else:
    print("[skip/WARN] ui: width")

# 2e. Insert status into _fill_rows values tuple
old_vals = """                    _text(r.get("quotation_number")),
                    _text(r.get("date")),
                    _text(r.get("customer_name")),"""
new_vals = """                    _text(r.get("quotation_number")),
                    _text(r.get("date")),
                    _text(r.get("status")) or "Draft",
                    _text(r.get("customer_name")),"""
if new_vals not in ui and old_vals in ui:
    ui = ui.replace(old_vals, new_vals, 1)
    print("[ok] ui: _fill_rows status value added")
else:
    print("[skip/WARN] ui: _fill_rows values")

# 2f. Add Set Status button to _build_actions
old_btn = "        self._btn(left, \"Delete\", self._delete, danger=True).pack(side=\"left\", padx=(8, 0), pady=14)"
new_btn = "        self._btn(left, \"Set Status\", self._set_status).pack(side=\"left\", padx=(8, 0), pady=14)\n" + old_btn
if "\"Set Status\"" not in ui and old_btn in ui:
    ui = ui.replace(old_btn, new_btn, 1)
    print("[ok] ui: Set Status button added")
else:
    print("[skip/WARN] ui: Set Status button")

# 2g. Add _set_status method + status filter in _reload, right before _current_record
anchor = "    def _current_record(self):"
new_methods = """    def _set_status(self):
        \"\"\"Open a small dialog to set the status of the selected row.\"\"\"
        number = self.selected_number
        if not number:
            messagebox.showinfo(
                "Set Status",
                "Select a quotation first.",
                parent=self,
            )
            return

        dlg = tk.Toplevel(self)
        dlg.title("Set Status")
        dlg.configure(bg=self.BG)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(
            dlg, text=f"Set status for {number}",
            bg=self.BG, fg=self.TEXT,
            font=("Arial", 10, "bold"),
        ).pack(padx=18, pady=(16, 10))

        current = self.selected_number
        chosen = tk.StringVar(value="Draft")

        rec = self._current_record()
        if rec and rec.get("status"):
            chosen.set(rec["status"])

        for s in ("Draft", "Sent", "Accepted", "Rejected", "Expired"):
            tk.Radiobutton(
                dlg, text=s, variable=chosen, value=s,
                bg=self.BG, fg=self.TEXT,
                activebackground=self.BG,
                selectcolor="white",
                font=("Arial", 10),
                anchor="w",
            ).pack(fill="x", padx=24, pady=2)

        btns = tk.Frame(dlg, bg=self.BG)
        btns.pack(fill="x", padx=18, pady=(14, 16))

        def _apply():
            new_status = chosen.get()
            ok = False
            try:
                from app.services.quotation_history_service import (
                    update_quotation_status,
                )
                ok = update_quotation_status(number, new_status)
            except Exception as e:
                messagebox.showerror(
                    "Set Status",
                    f"Could not update status:\\n{e}",
                    parent=dlg,
                )
                return
            dlg.destroy()
            if ok:
                self._reload()
            else:
                messagebox.showwarning(
                    "Set Status",
                    "Record not found.",
                    parent=self,
                )

        tk.Button(
            btns, text="Cancel", command=dlg.destroy,
            bg="white", fg=self.MUTED,
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right")

        tk.Button(
            btns, text="Apply", command=_apply,
            bg=self.RED, fg="white",
            activebackground=self.RED, activeforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right", padx=(0, 8))

    def _current_record(self):"""
if "_set_status" not in ui and anchor in ui:
    ui = ui.replace(anchor, new_methods, 1)
    print("[ok] ui: _set_status method added")
else:
    print("[skip/WARN] ui: _set_status method")

# 2h. Pass status filter into list_quotations in _reload + local filter
old_call = "            records = list_quotations() or []"
new_call = "            records = list_quotations(status=self.status_var.get()) or []"
if old_call in ui and "status=self.status_var.get()" not in ui:
    ui = ui.replace(old_call, new_call, 1)
    print("[ok] ui: _reload passes status")
else:
    print("[skip/WARN] ui: _reload list_quotations call")

UI.write_text(ui, encoding="utf-8")

# ============================================================
# COMPILE
# ============================================================
for path in (SVC, UI):
    try:
        py_compile.compile(str(path), doraise=True)
        print(f"[check] OK {path}")
    except py_compile.PyCompileError as e:
        print(f"[check] SYNTAX ERROR in {path}: {e}")
        if path == SVC:
            shutil.copy2(SVC_BKP, SVC)
        else:
            shutil.copy2(UI_BKP, UI)
        print(f"[restore] restored {path}")
