"""CRYSTAL — Quotations browser (reads from Google Sheet)."""
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


class QuotationsBrowser(tk.Toplevel):
    BG = "#F4F5F7"; CARD = "#FFFFFF"; TEXT = "#17191D"
    MUTED = "#747A84"; BORDER = "#E1E4E8"; SOFT = "#F7F8FA"
    RED = "#C8102E"; RED_DARK = "#A00D25"

    DATE_OPTIONS = [("Last 7 days", 7), ("Last 30 days", 30),
                    ("Last 90 days", 90), ("All time", None)]
    USER_OPTIONS = ["All", "ADMIN", "Invoice"]

    def __init__(self, parent):
        super().__init__(parent)
        self.title("CRYSTAL | Quotations")
        self.configure(bg=self.BG)
        try:
            from ui.common.ui_helpers import set_window_icon
            set_window_icon(self)
        except Exception:
            pass
        self.update_idletasks()
        try:
            sw = self.winfo_screenwidth(); sh = self.winfo_screenheight()
        except Exception:
            sw, sh = 1366, 768
        w = min(1200, max(900, sw - 120))
        h = min(760, max(600, sh - 120))
        x = max(0, (sw - w) // 2); y = max(0, (sh - h) // 2 - 20)
        self.geometry("%dx%d+%d+%d" % (w, h, x, y))
        self.minsize(900, 560)
        self.transient(parent); self.grab_set()
        self._rows = []; self._loading = False
        self._build()
        try:
            from ui.common.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(self, on_escape=self.destroy)
        except Exception:
            self.bind("<Escape>", lambda e: self.destroy())
        self.after(80, self._refresh)

    def _build(self):
        header = tk.Frame(self, bg=self.CARD, height=72)
        header.pack(fill="x"); header.pack_propagate(False)
        brand = tk.Frame(header, bg=self.CARD); brand.pack(side="left", padx=26)
        tk.Label(brand, text="CRYSTAL", bg=self.CARD, fg=self.RED,
                 font=("Arial", 20, "bold")).pack(side="left", pady=20)
        tk.Label(brand, text="  /  Quotations (Sheet)", bg=self.CARD,
                 fg=self.MUTED, font=("Arial", 11)).pack(side="left", pady=24)
        tk.Frame(self, bg=self.RED, height=3).pack(fill="x")

        filters = tk.Frame(self, bg=self.CARD, height=60)
        filters.pack(fill="x"); filters.pack_propagate(False)
        inner = tk.Frame(filters, bg=self.CARD)
        inner.pack(fill="x", padx=26, pady=12)

        tk.Label(inner, text="User:", bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 9)).pack(side="left")
        self.user_var = tk.StringVar(value="All")
        cbu = ttk.Combobox(inner, textvariable=self.user_var,
                           values=self.USER_OPTIONS, state="readonly", width=12)
        cbu.pack(side="left", padx=(6, 18))
        cbu.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        tk.Label(inner, text="Date:", bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 9)).pack(side="left")
        self.date_var = tk.StringVar(value=self.DATE_OPTIONS[1][0])
        cbd = ttk.Combobox(inner, textvariable=self.date_var,
                           values=[o[0] for o in self.DATE_OPTIONS],
                           state="readonly", width=14)
        cbd.pack(side="left", padx=(6, 18))
        cbd.bind("<<ComboboxSelected>>", lambda e: self._refresh())

        tk.Label(inner, text="Search:", bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 9)).pack(side="left")
        self.search_var = tk.StringVar()
        se = tk.Entry(inner, textvariable=self.search_var, width=28,
                      relief="solid", bd=1)
        se.pack(side="left", padx=(6, 18), ipady=3)
        se.bind("<Return>", lambda e: self._refresh())

        self.refresh_btn = tk.Button(
            inner, text="Refresh", command=self._refresh,
            bg=self.RED, fg="white", activebackground=self.RED_DARK,
            activeforeground="white", relief="flat", bd=0,
            highlightthickness=0, font=("Arial", 9, "bold"),
            cursor="hand2", padx=14, pady=6)
        self.refresh_btn.pack(side="left")

        tk.Frame(self, bg=self.BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True, padx=18, pady=12)

        cols = ("date", "user", "quot", "customer", "company",
                "model", "total", "status")
        heads = ("Date", "User", "Quotation No", "Customer",
                 "Company", "Model", "Grand Total", "Status")
        widths = (90, 70, 150, 160, 130, 120, 110, 80)

        st = ttk.Style()
        try: st.theme_use("clam")
        except Exception: pass
        st.configure("QB.Treeview", background=self.CARD,
                     fieldbackground=self.CARD, foreground=self.TEXT,
                     rowheight=26, borderwidth=0)
        st.configure("QB.Treeview.Heading", background=self.SOFT,
                     foreground=self.TEXT, font=("Arial", 9, "bold"))
        st.map("QB.Treeview", background=[("selected", self.RED)],
               foreground=[("selected", "white")])

        wrap = tk.Frame(body, bg=self.BORDER)
        wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings",
                                 style="QB.Treeview", height=18)
        for c, h, w in zip(cols, heads, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="w")
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.tree.bind("<Double-1>", self._on_double)

        status = tk.Frame(self, bg=self.CARD, height=40,
                          highlightbackground=self.BORDER, highlightthickness=1)
        status.pack(side="bottom", fill="x"); status.pack_propagate(False)
        self.status_var = tk.StringVar(value="Ready.")
        tk.Label(status, textvariable=self.status_var, bg=self.CARD,
                 fg=self.MUTED, font=("Arial", 9), anchor="w").pack(
            side="left", padx=18, pady=11)
        tk.Button(status, text="Close", command=self.destroy,
                  bg="white", fg=self.TEXT, activebackground="#F3F4F6",
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9, "bold"), cursor="hand2",
                  padx=14, pady=4).pack(side="right", padx=18, pady=8)

    def _since_days(self):
        for name, days in self.DATE_OPTIONS:
            if name == self.date_var.get():
                return days
        return 30

    def _refresh(self):
        if self._loading: return
        self._loading = True
        self.status_var.set("Fetching from Google Sheet...")
        self.refresh_btn.configure(state="disabled")
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
            try: self.after(0, lambda: self._apply(rows, err))
            except Exception: pass
        threading.Thread(target=worker, daemon=True).start()

    def _apply(self, rows, err):
        self._loading = False
        try: self.refresh_btn.configure(state="normal")
        except Exception: pass
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        if err:
            self.status_var.set("Error: " + err)
            return
        self._rows = rows or []
        for r in self._rows:
            total = r.get("Grand Total")
            try:
                ts = ("\u20b9 %.2f" % float(total)) if total not in (None, "") else ""
            except Exception:
                ts = str(total or "")
            self.tree.insert("", "end", values=(
                r.get("_date") or r.get("Date") or "",
                r.get("User") or "", r.get("Quotation No") or "",
                r.get("Customer") or "", r.get("Company") or "",
                r.get("Model") or "", ts, r.get("Status") or ""))
        self.status_var.set(
            "Last refreshed: %s  \u2022  %d row(s)" % (
                datetime.now().strftime("%H:%M:%S"), len(self._rows)))

    def _on_double(self, _e):
        sel = self.tree.selection()
        if not sel: return
        v = self.tree.item(sel[0], "values")
        if not v: return
        messagebox.showinfo(
            "Quotation detail",
            "Quotation No: %s\nDate:         %s\nUser:         %s\n"
            "Customer:     %s\nCompany:      %s\nModel:        %s\n"
            "Grand Total:  %s\nStatus:       %s" % (
                v[2], v[0], v[1], v[3], v[4], v[5], v[6], v[7]),
            parent=self)
