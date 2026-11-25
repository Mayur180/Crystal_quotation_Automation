"""CRYSTAL — Quotations browser (reads from Google Sheet)."""
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from ui.crystal import theme as T
from ui.crystal import widgets as W

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class QuotationsBrowser(tk.Toplevel):
    BG = T.BG
    CARD = T.SURFACE
    TEXT = T.TEXT
    MUTED = T.TEXT_MUTED
    BORDER = T.BORDER
    SOFT = T.SURFACE_ALT
    RED = T.ACCENT
    RED_DARK = T.ACCENT_DARK

    DATE_OPTIONS = [("Last 7 days", 7), ("Last 30 days", 30),
                    ("Last 90 days", 90), ("All time", None)]
    USER_OPTIONS = ["All", "ADMIN", "Invoice"]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("CRYSTAL | Cloud Quotations")
        self.configure(bg=self.BG)
        W.set_window_icon(self)
        self.geometry("1180x720")
        self.minsize(1000, 600)
        self.transient(parent)
        self.grab_set()
        self._rows = []
        self._loading = False
        W.apply_ttk_theme(self)
        self._build()
        try:
            from ui.common.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(self, on_escape=self.destroy)
        except Exception:
            self.bind("<Escape>", lambda e: self.destroy())
        self.after(80, self._refresh)

    def _build(self):
        header = W.PageHeader(
            self, title="Cloud Quotations",
            subtitle="Quotations stored in the Google Sheet",
            meta="—", padx=28,
        )
        header.pack(fill="x")
        self.count_label = header.meta_label

        # ---- filters ----
        filt = tk.Frame(
            self, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        filt.pack(fill="x", padx=28, pady=(14, 10))
        row = tk.Frame(filt, bg=T.SURFACE)
        row.pack(fill="x", padx=14, pady=10)

        self.refresh_btn = W.PrimaryButton(
            row, "Refresh", self._refresh, padx=14, pady=7,
        )
        self.refresh_btn.pack(side="right")

        def _label(text, pad=(0, 6)):
            tk.Label(row, text=text.upper(), bg=T.SURFACE,
                     fg=T.TEXT_MUTED, font=T.FONT_LABEL).pack(
                side="left", padx=pad)

        _label("User")
        self.user_var = tk.StringVar(value="All")
        cbu = ttk.Combobox(
            row, textvariable=self.user_var, values=self.USER_OPTIONS,
            state="readonly", width=10, font=T.FONT_SMALL,
        )
        cbu.pack(side="left", ipady=4)
        cbu.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        _label("Date", (12, 6))
        self.date_var = tk.StringVar(value=self.DATE_OPTIONS[1][0])
        cbd = ttk.Combobox(
            row, textvariable=self.date_var,
            values=[o[0] for o in self.DATE_OPTIONS],
            state="readonly", width=13, font=T.FONT_SMALL,
        )
        cbd.pack(side="left", ipady=4)
        cbd.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        _label("Search", (12, 6))
        self.search_var = tk.StringVar()
        se = W.SearchEntry(
            row, textvariable=self.search_var,
            placeholder="Quote no., customer, model…",
        )
        se.pack(side="left", fill="x", expand=True)
        se.entry.bind("<Return>", lambda e: self._refresh())

        # ---- footer (bottom first) ----
        foot = tk.Frame(
            self, bg=T.SURFACE, height=64,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        foot.pack(side="bottom", fill="x")
        foot.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(
            foot, textvariable=self.status_var, bg=T.SURFACE,
            fg=T.TEXT_MUTED, font=T.FONT_SMALL, anchor="w",
        ).pack(side="left", padx=22, pady=18)
        W.GhostButton(
            foot, "Close", self.destroy, padx=18, pady=7,
        ).pack(side="right", padx=22, pady=13)

        # ---- table ----
        card = tk.Frame(
            self, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=28, pady=(0, 14))

        cols = ("date", "user", "quot", "customer", "company",
                "model", "total", "status")
        heads = {
            "date": "Date", "user": "User", "quot": "Quotation No.",
            "customer": "Customer", "company": "Company",
            "model": "Model", "total": "Grand Total", "status": "Status",
        }
        widths = {
            "date": 100, "user": 80, "quot": 160, "customer": 210,
            "company": 210, "model": 140, "total": 120, "status": 90,
        }
        anchors = {"total": "e", "status": "center"}

        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                 height=12)
        for c in cols:
            self.tree.heading(c, text=heads[c],
                              anchor=anchors.get(c, "w"))
            self.tree.column(c, width=widths[c],
                             anchor=anchors.get(c, "w"),
                             stretch=(c in ("customer", "company")))
        self.tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        self.tree.tag_configure("oddrow", background=T.SURFACE)

        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 2), pady=(0, 2))
        self.tree.pack(side="left", fill="both", expand=True,
                       padx=2, pady=(0, 2))
        self.tree.bind("<Double-1>", self._on_double)

        self._empty = W.EmptyState(
            card, icon="☁", title="No quotations",
            hint="Adjust the filters, or refresh from the Sheet.",
        )

    def _set_empty(self, visible, title=None, hint=None):
        try:
            if visible:
                if title:
                    self._empty.set_text(title, hint)
                self._empty.place(relx=0.5, rely=0.5, anchor="center")
                self._empty.lift()
            else:
                self._empty.place_forget()
        except Exception:
            pass

    def _since_days(self):
        for name, days in self.DATE_OPTIONS:
            if name == self.date_var.get():
                return days
        return 30

    def _refresh(self):
        if self._loading:
            return
        self._loading = True
        self.status_var.set("Fetching from Google Sheet…")
        self._set_empty(
            True, "Fetching quotations…",
            "Reading the latest rows from the Google Sheet.")
        try:
            self.refresh_btn.set_enabled(False)
        except Exception:
            pass
        user = self.user_var.get()
        since = self._since_days()
        search = self.search_var.get()

        def worker():
            try:
                from app.services.google_sheet_reader import fetch_quotations
                rows, err = fetch_quotations(user=user, since_days=since,
                                             search=search)
            except Exception as e:
                rows, err = [], "%s: %s" % (type(e).__name__, e)
            try:
                self.after(0, lambda: self._apply(rows, err))
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def _apply(self, rows, err):
        self._loading = False
        try:
            self.refresh_btn.set_enabled(True)
        except Exception:
            pass
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        if err:
            self.status_var.set("Error: " + err)
            if self.count_label is not None:
                self.count_label.configure(text="—")
            self._set_empty(
                True, "Could not load quotations",
                "Check your connection, then press Refresh.")
            return

        self._rows = rows or []
        for i, r in enumerate(self._rows):
            total = r.get("Grand Total")
            try:
                ts = ("\u20b9 %.2f" % float(total)) if total not in (None, "") else "—"
            except Exception:
                ts = str(total or "—")
            self.tree.insert(
                "", "end",
                values=(
                    r.get("_date") or r.get("Date") or "—",
                    r.get("User") or "—",
                    r.get("Quotation No") or "—",
                    r.get("Customer") or "—",
                    r.get("Company") or "—",
                    r.get("Model") or "—",
                    ts,
                    r.get("Status") or "—",
                ),
                tags=("evenrow" if i % 2 == 0 else "oddrow",),
            )
        if self.count_label is not None:
            self.count_label.configure(text=f"{len(self._rows):,} row(s)")
        self.status_var.set(
            "Last refreshed: %s  \u2022  %d row(s)" % (
                datetime.now().strftime("%H:%M:%S"), len(self._rows)))
        self._set_empty(not self._rows)

    def _on_double(self, _e):
        sel = self.tree.selection()
        if not sel:
            return
        v = self.tree.item(sel[0], "values")
        if not v:
            return
        messagebox.showinfo(
            "Quotation detail",
            "Quotation No: %s\nDate:         %s\nUser:         %s\n"
            "Customer:     %s\nCompany:      %s\nModel:        %s\n"
            "Grand Total:  %s\nStatus:       %s" % (
                v[2], v[0], v[1], v[3], v[4], v[5], v[6], v[7]),
            parent=self)
