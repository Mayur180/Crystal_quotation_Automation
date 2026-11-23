# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# QUOTATION HISTORY
#
# Modal window — browse, search, open and delete past quotations.
#
# File:
#   ui/quotation_history.py
# ============================================================

import os
import queue
import sys
import subprocess
import threading
import tkinter as tk
from urllib.parse import quote as _url_quote
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation
from datetime import datetime


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# SERVICE IMPORT
# ============================================================

try:
    from app.services.quotation_history_service import (
        list_quotations,
        local_quotations,
        get_quotation,
        delete_quotation,
        merge_quotation_records,
    )
except Exception:
    list_quotations = None
    local_quotations = None
    get_quotation = None
    delete_quotation = None
    merge_quotation_records = None


# ============================================================
# HELPERS
# ============================================================

def _text(value, default="—"):
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def _money(value):
    try:
        d = Decimal(str(value))
        return f"₹ {d:,.2f}"
    except (InvalidOperation, ValueError, TypeError):
        return "₹ 0.00"


def _open_path(path):
    if not path:
        return False
    if not os.path.isfile(path):
        return False
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)   # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False


def _reveal_in_folder(path):
    if not path or not os.path.isfile(path):
        return False
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(path)])
        return True
    except Exception:
        return False


def _parse_date(value):
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def _record_matches_search(record, search):
    if not search:
        return True
    needle = str(search).strip().lower()
    fields = (
        record.get("quotation_number"),
        record.get("date"),
        record.get("customer_name"),
        record.get("customer_company"),
        record.get("model"),
        record.get("product"),
        record.get("customer_phone"),
        record.get("customer_email"),
    )
    return any(needle in str(v or "").lower() for v in fields)


# ============================================================
# MAIN WINDOW
# ============================================================

class QuotationHistory(tk.Toplevel):

    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    LIGHT_MUTED = "#9BA1AA"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_DARK = "#980000"
    RED_LIGHT = "#FFF3F3"
    GREEN = "#16804B"
    GREEN_LIGHT = "#ECF8F1"
    SOFT = "#F8F9FA"

    def __init__(self, parent):

        super().__init__(parent)

        self.title("CRYSTAL | Quotation History")
        self.geometry("1180x740")
        self.minsize(1000, 620)
        self.configure(bg=self.BG)

        self.transient(parent)
        self.grab_set()

        self.search_var = tk.StringVar()
        self.from_date_var = tk.StringVar()
        self.to_date_var = tk.StringVar()
        self.status_var = tk.StringVar(value="All")
        self.selected_number = None
        self._all_records = []
        self._fetching = False
        self._filter_job = None
        self._fetch_queue = queue.Queue()

        self._configure_style()
        self._build_interface()
        self._reload()
        self.after(150, self._poll_fetch_queue)

        # ---- Keyboard shortcuts ----
        try:
            from ui.common.ui_helpers import (
                install_table_shortcuts,
                install_modal_shortcuts,
            )
            install_table_shortcuts(
                self.tree,
                on_enter=lambda _id: self._open_docx(),
                on_delete=lambda _id: self._delete(),
            )
            install_modal_shortcuts(self, on_escape=self.destroy)
        except Exception:
            pass

    # --------------------------------------------------------

    def _configure_style(self):

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "History.Treeview",
            background="white",
            fieldbackground="white",
            foreground=self.TEXT,
            borderwidth=1,
            relief="solid",
            rowheight=30,
            font=("Arial", 9),
        )

        style.configure(
            "History.Treeview.Heading",
            background=self.SOFT,
            foreground=self.TEXT,
            font=("Arial", 9, "bold"),
            relief="flat",
        )

        style.map(
            "History.Treeview",
            background=[("selected", self.RED_LIGHT)],
            foreground=[("selected", self.TEXT)],
        )

    # --------------------------------------------------------

    def _build_interface(self):

        self._build_header()
        self._build_search()
        self._build_table()
        self._build_actions()

    # --------------------------------------------------------

    def _build_header(self):

        header = tk.Frame(self, bg=self.CARD, height=78)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=self.CARD)
        brand.pack(side="left", padx=28)

        tk.Label(
            brand, text="CRYSTAL",
            bg=self.CARD, fg=self.RED,
            font=("Arial", 22, "bold"),
        ).pack(side="left", pady=22)

        tk.Label(
            brand, text="  /  Quotation History",
            bg=self.CARD, fg=self.MUTED,
            font=("Arial", 11),
        ).pack(side="left", pady=26)

        right = tk.Frame(header, bg=self.CARD)
        right.pack(side="right", padx=28)

        self.count_label = tk.Label(
            right, text="",
            bg=self.CARD, fg=self.MUTED,
            font=("Arial", 9),
        )
        self.count_label.pack(anchor="e", pady=26)

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")

    # --------------------------------------------------------

    def _build_search(self):

        bar = tk.Frame(self, bg=self.BG)
        bar.pack(fill="x", padx=28, pady=(18, 8))

        def _label(parent, text, pad=(0, 8)):
            tk.Label(
                parent, text=text,
                bg=self.BG, fg=self.MUTED,
                font=("Arial", 8, "bold"),
            ).pack(side="left", padx=pad)

        def _entry(parent, var, width=None, expand=False):
            e = tk.Entry(
                parent,
                textvariable=var,
                bg="white", fg=self.TEXT,
                relief="solid", bd=1,
                font=("Arial", 10),
                insertbackground=self.RED,
            )
            if width:
                e.configure(width=width)
            if expand:
                e.pack(side="left", fill="x", expand=True, ipady=6)
            else:
                e.pack(side="left", ipady=6)
            e.bind("<KeyRelease>", lambda _e: self._schedule_filter())
            return e

        _label(bar, "Search")
        _entry(bar, self.search_var, expand=True)

        _label(bar, "From", pad=(12, 6))
        _entry(bar, self.from_date_var, width=12)

        _label(bar, "To", pad=(12, 6))
        _entry(bar, self.to_date_var, width=12)

        _label(bar, "Status", pad=(12, 6))
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
            bar, text="Clear",
            command=self._clear_search,
            bg="white", fg=self.MUTED,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="flat", bd=0,
            highlightthickness=0,
            font=("Arial", 9),
            cursor="hand2", padx=12, pady=4,
        ).pack(side="left", padx=(8, 0))

    def _clear_search(self):
        self.search_var.set("")
        self.from_date_var.set("")
        self.to_date_var.set("")
        self._reload()

    # --------------------------------------------------------

    def _build_table(self):

        card = tk.Frame(
            self, bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=28, pady=(0, 12))

        cols = ("offer_no", "date", "status", "customer", "company",
                "model", "total", "files")

        self.tree = ttk.Treeview(
            card, columns=cols, show="headings",
            style="History.Treeview", height=14,
        )

        # ---- Status row colors (tagged per-row in _fill_rows) ----
        STATUS_STYLES = {
            "Sent":     ("#EAF2FB", "#0D4A8F"),
            "Accepted": ("#E7F6EC", "#0F6B3A"),
            "Rejected": ("#FDECEC", "#A01616"),
            "Expired":  ("#F0F1F3", "#6B7280"),
        }
        for _status_name, (_bg, _fg) in STATUS_STYLES.items():
            self.tree.tag_configure(
                f"status_{_status_name}",
                background=_bg,
                foreground=_fg,
            )

        # ---- Extra keyboard shortcuts ----
        # S on tree → set status; Ctrl+D → duplicate; Esc → close
        self.tree.bind("<KeyPress-s>", lambda _e: self._set_status())
        self.tree.bind("<KeyPress-S>", lambda _e: self._set_status())
        self.tree.bind("<Control-d>", lambda _e: self._duplicate())
        self.bind("<Control-d>", lambda _e: self._duplicate())
        self.bind("<Escape>", lambda _e: self.destroy())

        # ---- Right-click context menu ----
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(
            label="Open Word", command=self._open_docx,
        )
        self._ctx_menu.add_command(
            label="View material / items", command=self._show_items,
        )
        self._ctx_menu.add_command(
            label="Revise quotation", command=self._revise,
        )
        self._ctx_menu.add_command(
            label="Duplicate quotation", command=self._duplicate,
        )
        self._ctx_menu.add_command(
            label="Send WhatsApp", command=self._send_whatsapp,
        )
        self._ctx_menu.add_command(
            label="Send Email", command=self._send_email,
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
            if row:
                self.tree.selection_set(row)
                try:
                    self._on_select()
                except Exception:
                    pass
                self._ctx_menu.tk_popup(event.x_root, event.y_root)

        self.tree.bind("<Button-3>", _show_ctx)

        # W → send WhatsApp
        self.tree.bind("<KeyPress-w>", lambda _e: self._send_whatsapp())
        self.tree.bind("<KeyPress-W>", lambda _e: self._send_whatsapp())

        # E → send email
        self.tree.bind("<KeyPress-e>", lambda _e: self._send_email())
        self.tree.bind("<KeyPress-E>", lambda _e: self._send_email())

        headings = {
            "offer_no": "Offer No.",
            "date": "Date",
            "status": "Status",
            "customer": "Customer",
            "company": "Company",
            "model": "Model",
            "total": "Grand Total",
            "files": "Files",
        }
        widths = {
            "offer_no": 150,
            "date": 105,
            "status": 90,
            "customer": 170,
            "company": 200,
            "model": 110,
            "total": 130,
            "files": 90,
        }

        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(
                c,
                width=widths[c],
                anchor="e" if c == "total" else "w",
                stretch=(c in ("customer", "company")),
            )

        vsb = ttk.Scrollbar(card, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True,
                       padx=14, pady=14)
        vsb.pack(side="right", fill="y", pady=14)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._open_docx())

        # Set focus so keyboard nav works right away
        try:
            self.tree.focus_set()
        except Exception:
            pass

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if sel:
            self.selected_number = self.tree.item(sel[0], "values")[0]
        else:
            self.selected_number = None

    # --------------------------------------------------------

    def _build_actions(self):
        # Force enable delete for now
        self._force_delete = True

        bar = tk.Frame(self, bg=self.CARD, height=70,
                       highlightbackground=self.BORDER,
                       highlightthickness=1)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=self.CARD)
        left.pack(side="left", padx=22)

        self._btn(left, "Open Word", self._open_docx).pack(side="left", pady=14)
        self._btn(left, "Open PDF", self._open_pdf).pack(side="left", padx=(8, 0), pady=14)
        self._btn(left, "Show in folder", self._reveal).pack(side="left", padx=(8, 0), pady=14)
        self._btn(left, "Set Status", self._set_status).pack(side="left", padx=(8, 0), pady=14)
        self._btn(left, "Send WhatsApp", self._send_whatsapp).pack(side="left", padx=(8, 0), pady=14)
        self._btn(left, "Send Email", self._send_email).pack(side="left", padx=(8, 0), pady=14)
        self._btn(left, "Delete", self._delete, danger=True).pack(side="left", padx=(8, 0), pady=14)

        right = tk.Frame(bar, bg=self.CARD)
        right.pack(side="right", padx=22)

        self._btn(right, "Close", self.destroy).pack(side="right", pady=14)

    def _btn(self, parent, text, command, *, danger=False):

        bg = "white"
        fg = self.RED if danger else self.TEXT
        active_bg = self.RED_LIGHT if danger else "#F3F4F6"

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg, fg=fg,
            activebackground=active_bg,
            activeforeground=fg,
            relief="solid", bd=1,
            highlightthickness=0,
            font=("Arial", 9, "bold"),
            cursor="hand2",
            padx=14, pady=6,
        )

    # --------------------------------------------------------

    def _schedule_filter(self):
        """Debounce keystrokes — filtering is local, no cloud round-trip."""
        if self._filter_job is not None:
            try:
                self.after_cancel(self._filter_job)
            except Exception:
                pass
        self._filter_job = self.after(250, self._reload)

    def _reload(self):
        """Refilter the loaded records; fetch from the cloud only when needed."""
        self._filter_job = None

        if list_quotations is None:
            self._fill_rows([])
            self.count_label.configure(text="Service unavailable")
            return

        if not self._all_records:
            self.count_label.configure(text="Loading…")
            self._fill_rows([])
            self._start_fetch()
            return

        self._apply_filters()

    def _start_fetch(self):
        """Download quotation records in the background, then refresh the table."""
        if self._fetching:
            return
        self._fetching = True

        def worker():
            records = None
            try:
                from app.services.cloud_sync import fetch_quotations_from_cloud
                from app.services.paths import get_active_module
                cloud_records = fetch_quotations_from_cloud(
                    limit=10000, module=get_active_module(), silent=True
                )
                records = [
                    r for r in (cloud_records or [])
                    if str(r.get("quotation_number", "")).upper().startswith("CRY")
                ]
            except Exception as e:
                print(f"[History] Cloud load failed: {e}")
            self._fetch_queue.put(records)

        threading.Thread(target=worker, daemon=True).start()

    def _poll_fetch_queue(self):
        """Main-thread pump for results coming from the fetch worker."""
        try:
            while True:
                records = self._fetch_queue.get_nowait()
                self._fetching = False
                local_records = []
                if local_quotations is not None:
                    try:
                        local_records = [
                            r for r in local_quotations()
                            if str(r.get("quotation_number", "")).upper().startswith("CRY")
                        ]
                    except Exception:
                        local_records = []
                if records is not None:
                    if merge_quotation_records is not None:
                        self._all_records = merge_quotation_records(local_records, records)
                    else:
                        self._all_records = records
                if not self._all_records and local_records:
                    # Cloud unreachable or sheet empty — show saved records.
                    self._all_records = local_records
                self._apply_filters()
        except queue.Empty:
            pass
        except Exception:
            pass
        try:
            self.after(250, self._poll_fetch_queue)
        except Exception:
            pass

    def _apply_filters(self):
        search = self.search_var.get().strip()
        from_text = self.from_date_var.get().strip()
        to_text = self.to_date_var.get().strip()

        from_date = _parse_date(from_text)
        to_date = _parse_date(to_text)

        filtered = []
        for r in self._all_records:
            if not _record_matches_search(r, search):
                continue
            if from_date or to_date:
                rec_date = _parse_date(r.get("date"))
                if rec_date is None:
                    continue
                if from_date and rec_date < from_date:
                    continue
                if to_date and rec_date > to_date:
                    continue
            filtered.append(r)

        self._fill_rows(filtered)

        self.count_label.configure(
            text=f"{len(filtered)} quotation(s)"
        )

    def _fill_rows(self, records):

        for row in self.tree.get_children():
            self.tree.delete(row)

        for r in records:

            files = []
            if r.get("docx_path"):
                files.append("DOCX")
            if r.get("pdf_path"):
                files.append("PDF")
            files_str = " · ".join(files) if files else "—"

            status = _text(r.get("status")) or "Draft"
            tag = f"status_{status}" if status in (
                "Sent", "Accepted", "Rejected", "Expired"
            ) else ""

            self.tree.insert(
                "", "end",
                values=(
                    _text(r.get("quotation_number")),
                    _text(r.get("date")),
                    status,
                    _text(r.get("customer_name")),
                    _text(r.get("customer_company")),
                    _text(r.get("model")),
                    _money(r.get("grand_total")),
                    files_str,
                ),
                tags=(tag,) if tag else (),
            )

    # --------------------------------------------------------
    # ACTIONS
    # --------------------------------------------------------

    def _set_status(self):
        """Open a small dialog to set the status of the selected row."""
        number = self.selected_number
        if not number:
            messagebox.showinfo(
                "Set Status",
                "Select a quotation first.",
                parent=self,
            )
            return

        rec = self._current_record()
        current = "Draft"
        if rec and rec.get("status"):
            current = rec["status"]

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
        ).pack(padx=20, pady=(16, 10))

        chosen = tk.StringVar(value=current)

        for s_name in ("Draft", "Sent", "Accepted", "Rejected", "Expired"):
            tk.Radiobutton(
                dlg, text=s_name, variable=chosen, value=s_name,
                bg=self.BG, fg=self.TEXT,
                activebackground=self.BG,
                selectcolor="white",
                font=("Arial", 10),
                anchor="w",
            ).pack(fill="x", padx=30, pady=2)

        btns = tk.Frame(dlg, bg=self.BG)
        btns.pack(fill="x", padx=20, pady=(14, 16))

        def _apply():
            new_status = chosen.get()
            try:
                from app.services.quotation_history_service import (
                    update_quotation_status,
                )
                ok = update_quotation_status(number, new_status)
            except Exception as e:
                messagebox.showerror(
                    "Set Status",
                    f"Could not update status:\n{e}",
                    parent=dlg,
                )
                return
            dlg.destroy()
            if ok:
                # Reflect the new status immediately, then confirm with the cloud.
                for r in self._all_records:
                    if _text(r.get("quotation_number")) == _text(number):
                        r["status"] = new_status
                self._apply_filters()
                self._start_fetch()
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

    def _record_with_items(self, record):
        """Merge the locally stored line items into a (cloud) record."""
        if not record:
            return record
        if record.get("items"):
            return record
        number = _text(record.get("quotation_number"))
        try:
            local = get_quotation(number) if get_quotation else None
        except Exception:
            local = None
        if not local:
            return record
        merged = dict(record)
        for key, value in local.items():
            if value and not merged.get(key):
                merged[key] = value
        return merged

    def _show_items(self):
        """Show the materials (models, quantities, prices) of the selected quote."""
        record = self._current_record()
        if not record:
            messagebox.showinfo("Items", "Select a quotation first.", parent=self)
            return

        record = self._record_with_items(record)
        number = _text(record.get("quotation_number"))
        items = [it for it in (record.get("items") or []) if isinstance(it, dict)]

        def _qty(value):
            try:
                q = float(value)
                return str(int(q)) if q.is_integer() else f"{q:g}"
            except Exception:
                return _text(value)

        def _discount_text(it):
            if it.get("disc_mode") == "Percentage (%)":
                try:
                    return f"{float(it.get('raw_discount') or 0):g}%"
                except Exception:
                    return _text(it.get("raw_discount"))
            return _money(it.get("discount"))

        popup = tk.Toplevel(self)
        popup.title(f"Material — {number}")
        popup.geometry("780x430")
        popup.configure(bg=self.BG)
        popup.transient(self)

        tk.Label(
            popup,
            text=f"{number}  ·  {_text(record.get('customer_name'))}",
            bg=self.BG, fg=self.TEXT, font=("Arial", 12, "bold"),
        ).pack(anchor="w", padx=20, pady=(16, 8))

        try:
            from app.services.quotation_number_service import split_revision
            _base, _rev = split_revision(number)
        except Exception:
            _base, _rev = number, 0
        if _rev:
            tk.Label(
                popup, text=f"Revision R{_rev} of {_base}",
                bg=self.BG, fg=self.MUTED, font=("Arial", 9, "italic"),
            ).pack(anchor="w", padx=20)

        if not items:
            tk.Label(
                popup,
                text=(
                    "No material details are stored for this quotation.\n\n"
                    "Open it on the PC that created it, or wait until the "
                    "quotation is re-saved with the updated cloud sync."
                ),
                bg=self.BG, fg=self.MUTED, font=("Arial", 10),
                justify="left",
            ).pack(anchor="w", padx=20, pady=16)
            tk.Button(popup, text="Close", command=popup.destroy).pack(pady=10)
            return

        table = tk.Frame(popup, bg=self.BG)
        table.pack(fill="both", expand=True, padx=20, pady=(10, 0))

        cols = ("model", "hsn", "qty", "price", "discount", "total")
        tree = ttk.Treeview(table, columns=cols, show="headings", height=9)
        for col, title, width, anchor in (
            ("model", "Model", 240, "w"),
            ("hsn", "HSN", 90, "w"),
            ("qty", "Qty", 60, "center"),
            ("price", "Price", 110, "e"),
            ("discount", "Discount", 110, "e"),
            ("total", "Total", 120, "e"),
        ):
            tree.heading(col, text=title)
            tree.column(col, width=width, anchor=anchor)

        vsb = ttk.Scrollbar(table, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        for it in items:
            tree.insert("", "end", values=(
                _text(it.get("model")),
                _text(it.get("hsn")),
                _qty(it.get("qty")),
                _money(it.get("price")),
                _discount_text(it),
                _money(it.get("total")),
            ))

        tk.Label(
            popup, text=f"Grand Total: {_money(record.get('grand_total'))}",
            bg=self.BG, fg=self.TEXT, font=("Arial", 11, "bold"),
        ).pack(anchor="e", padx=20, pady=(8, 4))
        tk.Button(popup, text="Close", command=popup.destroy).pack(pady=(0, 12))

    def _revise(self):
        """Open a linked revision (…-R1) of the selected quotation."""
        record = self._current_record()
        if not record:
            messagebox.showinfo("Revise", "Select a quotation first.", parent=self)
            return

        record = self._record_with_items(record)
        number = _text(record.get("quotation_number"))

        try:
            from app.services.quotation_number_service import next_revision_number
            numbers = [
                r.get("quotation_number", "") for r in self._all_records
            ]
            if local_quotations:
                numbers += [
                    r.get("quotation_number", "") for r in local_quotations()
                ]
            revision_number = next_revision_number(number, numbers)
        except Exception as e:
            messagebox.showerror(
                "Revise", f"Could not build revision number:\n{e}", parent=self
            )
            return

        try:
            from ui.crystal.quotation_form import QuotationForm
            QuotationForm(
                self.master, self, prefill=record,
                revision_number=revision_number,
            )
        except Exception as e:
            messagebox.showerror(
                "Revise", f"Could not open Quotation form:\n{e}", parent=self
            )

    def _duplicate(self):
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
            from ui.crystal.quotation_form import QuotationForm
        except Exception as e:
            messagebox.showerror(
                "Duplicate",
                f"Could not open Quotation form:\n{e}",
                parent=self,
            )
            return

        try:
            # QuotationForm signature: (app=None, parent=None, prefill=None)
            QuotationForm(self.master, self, prefill=record)
        except Exception as e:
            messagebox.showerror(
                "Duplicate",
                f"Could not open Quotation form:\n{e}",
                parent=self,
            )

    def _prompt_for_phone(self, record):
        """Show a dialog asking for a phone number.

        Returns the entered phone (str) or None if cancelled.
        Also optionally saves to the customer DB.
        """
        dlg = tk.Toplevel(self)
        dlg.title("WhatsApp")
        dlg.geometry("420x260")
        dlg.configure(bg=self.BG)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(
            dlg, text="No phone number found.",
            bg=self.BG, fg=self.TEXT,
            font=("Arial", 11, "bold"),
        ).pack(padx=20, pady=(20, 8))

        tk.Label(
            dlg, text="Enter phone number:",
            bg=self.BG, fg=self.MUTED,
            font=("Arial", 9, "bold"), anchor="w",
        ).pack(fill="x", padx=20)

        phone_var = tk.StringVar()
        entry = tk.Entry(
            dlg, textvariable=phone_var,
            bg="white", fg=self.TEXT, relief="solid", bd=1,
            font=("Arial", 11), insertbackground=self.RED,
        )
        entry.pack(fill="x", padx=20, ipady=6, pady=(4, 12))
        entry.focus_set()

        save_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            dlg, text="Save to customer database",
            variable=save_var,
            bg=self.BG, activebackground=self.BG,
            selectcolor="white", fg=self.TEXT,
            font=("Arial", 9),
        ).pack(anchor="w", padx=20)

        result = {"value": None}

        def _ok():
            v = phone_var.get().strip()
            digits = "".join(c for c in v if c.isdigit())
            if not digits:
                messagebox.showwarning(
                    "WhatsApp", "Please enter a valid phone number.",
                    parent=dlg,
                )
                return
            result["value"] = digits
            if save_var.get():
                self._save_phone_to_customer(record, digits)
            dlg.destroy()

        def _cancel():
            result["value"] = None
            dlg.destroy()

        btns = tk.Frame(dlg, bg=self.BG)
        btns.pack(fill="x", padx=20, pady=(16, 20))

        tk.Button(
            btns, text="Cancel", command=_cancel,
            bg="white", fg=self.TEXT,
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right")

        tk.Button(
            btns, text="Send WhatsApp", command=_ok,
            bg=self.RED, fg="white",
            activebackground=self.RED, activeforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right", padx=(0, 8))

        dlg.bind("<Return>", lambda _e: _ok())
        dlg.bind("<Escape>", lambda _e: _cancel())

        self.wait_window(dlg)
        return result["value"]

    def _prompt_for_email(self, record):
        """Show a dialog asking for an email address.

        Returns the entered email (str) or None if cancelled.
        """
        dlg = tk.Toplevel(self)
        dlg.title("Email")
        dlg.geometry("440x260")
        dlg.configure(bg=self.BG)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(
            dlg, text="No email address found.",
            bg=self.BG, fg=self.TEXT,
            font=("Arial", 11, "bold"),
        ).pack(padx=20, pady=(20, 8))

        tk.Label(
            dlg, text="Enter email address:",
            bg=self.BG, fg=self.MUTED,
            font=("Arial", 9, "bold"), anchor="w",
        ).pack(fill="x", padx=20)

        email_var = tk.StringVar()
        entry = tk.Entry(
            dlg, textvariable=email_var,
            bg="white", fg=self.TEXT, relief="solid", bd=1,
            font=("Arial", 11), insertbackground=self.RED,
        )
        entry.pack(fill="x", padx=20, ipady=6, pady=(4, 12))
        entry.focus_set()

        save_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            dlg, text="Save to customer database",
            variable=save_var,
            bg=self.BG, activebackground=self.BG,
            selectcolor="white", fg=self.TEXT,
            font=("Arial", 9),
        ).pack(anchor="w", padx=20)

        result = {"value": None}

        def _ok():
            v = email_var.get().strip()
            if "@" not in v:
                messagebox.showwarning(
                    "Email", "Please enter a valid email address.",
                    parent=dlg,
                )
                return
            result["value"] = v
            if save_var.get():
                self._save_email_to_customer(record, v)
            dlg.destroy()

        def _cancel():
            result["value"] = None
            dlg.destroy()

        btns = tk.Frame(dlg, bg=self.BG)
        btns.pack(fill="x", padx=20, pady=(16, 20))

        tk.Button(
            btns, text="Cancel", command=_cancel,
            bg="white", fg=self.TEXT,
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right")

        tk.Button(
            btns, text="Send Email", command=_ok,
            bg=self.RED, fg="white",
            activebackground=self.RED, activeforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right", padx=(0, 8))

        dlg.bind("<Return>", lambda _e: _ok())
        dlg.bind("<Escape>", lambda _e: _cancel())

        self.wait_window(dlg)
        return result["value"]

    def _save_phone_to_customer(self, record, phone):
        """Update the customer DB with this phone."""
        try:
            from app.services.customer_service import (
                find_duplicate, save_customer, list_customers,
            )
            name = (record.get("customer_name") or "").strip()
            company = (record.get("customer_company") or "").strip()

            # Try to find the customer
            existing = find_duplicate(name, company, "", "")
            if not existing:
                # Looser search — match by name only
                for c in list_customers():
                    if (c.get("name") or "").strip().lower() == name.lower():
                        existing = c
                        break

            if existing:
                existing["phone"] = phone
                save_customer(existing, existing.get("id"))
            else:
                # Create new customer
                save_customer({
                    "name": name,
                    "company": company,
                    "phone": phone,
                })
        except Exception:
            pass

    def _save_email_to_customer(self, record, email):
        """Update the customer DB with this email."""
        try:
            from app.services.customer_service import (
                find_duplicate, save_customer, list_customers,
            )
            name = (record.get("customer_name") or "").strip()
            company = (record.get("customer_company") or "").strip()

            existing = find_duplicate(name, company, "", "")
            if not existing:
                for c in list_customers():
                    if (c.get("name") or "").strip().lower() == name.lower():
                        existing = c
                        break

            if existing:
                existing["email"] = email
                save_customer(existing, existing.get("id"))
            else:
                save_customer({
                    "name": name,
                    "company": company,
                    "email": email,
                })
        except Exception:
            pass

    def _send_whatsapp(self):
        """Open WhatsApp Web with a pre-filled message for the selected
        quotation. Also opens Explorer with the PDF selected (if any)."""
        record = self._current_record()
        if not record:
            messagebox.showinfo(
                "WhatsApp",
                "Select a quotation first.",
                parent=self,
            )
            return

        # ---- phone cleanup ----
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
            # Ask user for a phone number
            entered = self._prompt_for_phone(record)
            if not entered:
                return
            raw_phone = entered
            digits = entered

            # Update local record so subsequent operations see it
            record["customer_phone"] = entered
        if digits.startswith("91") and len(digits) >= 12:
            full_phone = digits
        else:
            full_phone = "91" + digits.lstrip("0")

        # ---- build message ----
        cust_name = (record.get("customer_name") or "").strip() or "Customer"
        number    = (record.get("quotation_number") or "").strip()
        model     = (record.get("model") or "").strip()

        try:
            from decimal import Decimal
            amount = f"\u20b9 {Decimal(str(record.get('grand_total', 0))):,.2f}"
        except Exception:
            amount = "\u20b9 0.00"

        message_lines = [
            f"Dear {cust_name},",
            "",
            "Please find attached our quotation:",
            "",
            f"Offer No:  {number}",
            f"Model:     {model}",
            f"Amount:    {amount}",
            "",
            "Kindly review and let us know.",
            "",
            "Regards,",
            "Armatech Associates",
        ]
        message = "\n".join(message_lines)

        try:
            url = f"https://wa.me/{full_phone}?text={_url_quote(message)}"
        except Exception as e:
            messagebox.showerror(
                "WhatsApp",
                f"Could not build WhatsApp link:\n{e}",
                parent=self,
            )
            return

        # ---- open WhatsApp Web ----
        try:
            import webbrowser
            webbrowser.open_new_tab(url)
        except Exception as e:
            messagebox.showerror(
                "WhatsApp",
                f"Could not open WhatsApp Web:\n{e}",
                parent=self,
            )
            return

        # ---- reveal the PDF in Explorer ----
        pdf_path = record.get("pdf_path")
        docx_path = record.get("docx_path")
        target = pdf_path if pdf_path and os.path.isfile(pdf_path) else (
            docx_path if docx_path and os.path.isfile(docx_path) else None
        )
        if target:
            try:
                if sys.platform.startswith("win"):
                    subprocess.Popen(["explorer", "/select,", target])
            except Exception:
                pass
        else:
            messagebox.showinfo(
                "WhatsApp",
                "WhatsApp Web opened.\n\n"
                "No PDF/DOCX file found on disk for this quotation — "
                "attach manually if needed.",
                parent=self,
            )

    def _send_email(self):
        """Open Gmail compose in the browser with a pre-filled message,
        and reveal the PDF in Explorer so the user can attach it."""
        record = self._current_record()
        if not record:
            messagebox.showinfo(
                "Email",
                "Select a quotation first.",
                parent=self,
            )
            return

        to_addr = str(record.get("customer_email") or "").strip()

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
            entered = self._prompt_for_email(record)
            if not entered:
                return
            to_addr = entered
            record["customer_email"] = entered

        cust_name = (record.get("customer_name") or "").strip() or "Customer"
        number    = (record.get("quotation_number") or "").strip()
        model     = (record.get("model") or "").strip()

        try:
            from decimal import Decimal
            amount = f"\u20b9 {Decimal(str(record.get('grand_total', 0))):,.2f}"
        except Exception:
            amount = "\u20b9 0.00"

        subject = f"Quotation {number} \u2014 {model}"

        body_lines = [
            f"Dear {cust_name},",
            "",
            "Please find attached our quotation.",
            "",
            f"Offer No:  {number}",
            f"Model:     {model}",
            f"Amount:    {amount}",
            "",
            "Kindly review and let us know if you have any questions.",
            "",
            "Regards,",
            "Armatech Associates",
            "+91 70209 91684",
        ]
        body = "\n".join(body_lines)

        # Gmail compose URL
        try:
            url = (
                "https://mail.google.com/mail/?view=cm&fs=1"
                f"&to={_url_quote(to_addr)}"
                f"&su={_url_quote(subject)}"
                f"&body={_url_quote(body)}"
            )
        except Exception as e:
            messagebox.showerror(
                "Email",
                f"Could not build email link:\n{e}",
                parent=self,
            )
            return

        try:
            import webbrowser
            webbrowser.open_new_tab(url)
        except Exception as e:
            messagebox.showerror(
                "Email",
                f"Could not open Gmail:\n{e}",
                parent=self,
            )
            return

        # Reveal PDF in Explorer for manual attach
        pdf_path = record.get("pdf_path")
        if pdf_path and os.path.isfile(pdf_path):
            try:
                if sys.platform.startswith("win"):
                    subprocess.Popen(["explorer", "/select,", pdf_path])
            except Exception:
                pass
        else:
            # No PDF — offer to open DOCX as fallback
            docx_path = record.get("docx_path")
            if docx_path and os.path.isfile(docx_path):
                try:
                    if sys.platform.startswith("win"):
                        subprocess.Popen(["explorer", "/select,", docx_path])
                except Exception:
                    pass
            else:
                messagebox.showinfo(
                    "Email",
                    "Gmail compose opened.\n\n"
                    "No PDF file found on disk for this quotation.",
                    parent=self,
                )

    def _current_record(self):
        if not self.selected_number:
            return None
        rec = get_quotation(self.selected_number) if get_quotation else None
        if rec:
            return rec
        # Records created on another PC exist only in the cloud list.
        for r in self._all_records:
            if str(r.get("quotation_number", "")).strip() == str(self.selected_number).strip():
                return r
        return None

    def _open_docx(self):
        rec = self._current_record()
        if not rec:
            messagebox.showinfo("No selection",
                                "Please select a quotation first.",
                                parent=self)
            return
        path = rec.get("docx_path")
        if not _open_path(path):
            messagebox.showerror(
                "File not found",
                (
                    f"Word file is missing:\n{path}\n\n"
                    "It is stored on the PC that created this quotation.\n"
                    "Right-click the row and choose "
                    "'View material / items' to see its contents."
                ),
                parent=self,
            )

    def _open_pdf(self):
        rec = self._current_record()
        if not rec:
            messagebox.showinfo("No selection",
                                "Please select a quotation first.",
                                parent=self)
            return

        path = rec.get("pdf_path")

        # ---- case 1: PDF exists ----
        if path and os.path.isfile(path):
            if not _open_path(path):
                messagebox.showerror(
                    "File not found",
                    f"PDF file is missing:\n{path}",
                    parent=self,
                )
            return

        # ---- case 2: no PDF -> ask ----
        ok = messagebox.askyesno(
            "PDF not created",
            "PDF is not created for this quotation.\n\n"
            "Do you want to create it now?",
            parent=self,
        )
        if not ok:
            return

        self._create_pdf_from_docx(rec)

    def _create_pdf_from_docx(self, record):
        """Convert the DOCX for this quotation into a PDF and open it."""
        docx_path = record.get("docx_path") or ""

        if not docx_path or not os.path.isfile(docx_path):
            messagebox.showerror(
                "Cannot create PDF",
                "The DOCX file for this quotation is missing.\n\n"
                "Without a DOCX we cannot generate a PDF.",
                parent=self,
            )
            return

        pdf_path = os.path.splitext(docx_path)[0] + ".pdf"

        # Already exists? just open it
        if os.path.isfile(pdf_path):
            try:
                from app.services.quotation_history_service import (
                    update_quotation_pdf_path,
                )
                update_quotation_pdf_path(
                    record.get("quotation_number"), pdf_path
                )
            except Exception:
                pass
            _open_path(pdf_path)
            self._reload()
            return

        # Show progress
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            self._do_convert(docx_path, pdf_path)
        finally:
            try:
                self.config(cursor="")
            except Exception:
                pass

        if not os.path.isfile(pdf_path):
            messagebox.showerror(
                "PDF creation failed",
                "PDF could not be created.\n\n"
                "Check that Microsoft Word is available and the "
                "DOCX file is not locked.",
                parent=self,
            )
            return

        # Save new path back to history
        try:
            from app.services.quotation_history_service import (
                update_quotation_pdf_path,
            )
            update_quotation_pdf_path(
                record.get("quotation_number"), pdf_path
            )
        except Exception:
            pass

        # Open it and refresh the table (Files column updates)
        _open_path(pdf_path)
        try:
            self._reload()
        except Exception:
            pass

    def _do_convert(self, docx_path, pdf_path):
        """Run docx2pdf, fall back to win32com if needed."""
        # Try docx2pdf first (simplest API)
        try:
            from docx2pdf import convert
            convert(docx_path, pdf_path)
            if os.path.isfile(pdf_path):
                return
        except Exception:
            pass

        # Fallback: direct win32com Word automation
        try:
            import win32com.client
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0

            doc = word.Documents.Open(os.path.abspath(docx_path))

            # FileFormat=17 is wdFormatPDF
            doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)

            doc.Close(SaveChanges=False)
            word.Quit()
        except Exception as e:
            messagebox.showerror(
                "PDF conversion error",
                f"docx2pdf and Word automation both failed.\n\n{e}",
                parent=self,
            )

    def _reveal(self):
        rec = self._current_record()
        if not rec:
            messagebox.showinfo("No selection",
                                "Please select a quotation first.",
                                parent=self)
            return
        path = rec.get("docx_path") or rec.get("pdf_path")
        if not path or not _reveal_in_folder(path):
            messagebox.showerror(
                "Cannot reveal",
                "The file could not be located.",
                parent=self,
            )

    def _delete(self):
        rec = self._current_record()
        if not rec:
            messagebox.showinfo("No selection",
                                "Please select a quotation first.",
                                parent=self)
            return

        ok = messagebox.askyesno(
            "Delete quotation",
            "Remove this entry from history?\n\n"
            f"{rec.get('quotation_number')}\n"
            f"{rec.get('customer_name')}",
            parent=self,
        )
        if not ok:
            return

        number = self.selected_number
        if delete_quotation and delete_quotation(number):
            self.selected_number = None
            # Drop the row locally right away, then re-sync in the background.
            self._all_records = [
                r for r in self._all_records
                if _text(r.get("quotation_number")) != _text(number)
            ]
            self._apply_filters()
            self._start_fetch()


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()
    root.withdraw()
    QuotationHistory(root)
    root.mainloop()