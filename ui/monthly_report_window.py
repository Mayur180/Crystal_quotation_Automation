# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# MONTHLY REPORT WINDOW
# ============================================================

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:
    from app.services.monthly_report_service import (
        get_monthly_summary,
        get_year_breakdown,
        list_years,
        export_csv,
        export_pdf,
        MONTH_NAMES,
    )
except Exception:
    get_monthly_summary = None
    get_year_breakdown = None
    list_years = None
    export_csv = None
    export_pdf = None
    MONTH_NAMES = (
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    )


def _money(v):
    try:
        return f"₹ {float(v):,.2f}"
    except Exception:
        return "₹ 0.00"


def _text(v):
    return "" if v is None else str(v).strip()


class MonthlyReport(tk.Toplevel):

    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_LIGHT = "#FFF3F3"
    SOFT = "#F8F9FA"

    def __init__(self, parent):
        super().__init__(parent)

        self.title("CRYSTAL | Monthly Report")
        self.geometry("1100x720")
        self.minsize(950, 620)
        self.configure(bg=self.BG)

        self.transient(parent)
        self.grab_set()

        today = date.today()
        years = []
        if list_years is not None:
            try:
                years = list_years() or []
            except Exception:
                years = []
        if today.year not in years:
            years.append(today.year)
        years = sorted(set(years))

        self.year_var = tk.StringVar(value=str(today.year))
        self.month_var = tk.StringVar(value=MONTH_NAMES[today.month - 1])
        self.from_var = tk.StringVar(value="")
        self.to_var = tk.StringVar(value="")
        self.years = years

        self._configure_style()
        self._build_interface()
        self._reload()

        # Esc closes the window
        try:
            self.bind("<Escape>", lambda _e: self.destroy())
        except Exception:
            pass

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "MR.Treeview",
            background="white", fieldbackground="white",
            foreground=self.TEXT, rowheight=24,
            borderwidth=0, font=("Arial", 9),
        )
        style.configure(
            "MR.Treeview.Heading",
            background="#F0F1F3", foreground=self.TEXT,
            relief="flat", font=("Arial", 9, "bold"),
        )

    # --------------------------------------------------------
    # UI BUILD
    # --------------------------------------------------------

    def _build_interface(self):
        head = tk.Frame(self, bg=self.BG)
        head.pack(fill="x", padx=28, pady=(18, 6))
        tk.Label(
            head, text="Monthly Report",
            bg=self.BG, fg=self.TEXT,
            font=("Arial", 16, "bold"),
        ).pack(side="left")
        tk.Label(
            head, text="Business summary & yearly totals",
            bg=self.BG, fg=self.MUTED,
            font=("Arial", 9),
        ).pack(side="left", padx=(12, 0), pady=(8, 0))

        # ---- filter bar ----
        filt = tk.Frame(self, bg=self.BG)
        filt.pack(fill="x", padx=28, pady=(6, 10))

        tk.Label(filt, text="Year", bg=self.BG, fg=self.MUTED,
                 font=("Arial", 8, "bold")).pack(side="left", padx=(0, 6))
        year_cb = ttk.Combobox(
            filt, textvariable=self.year_var, values=self.years,
            state="readonly", width=8, font=("Arial", 9),
        )
        year_cb.pack(side="left", ipady=3)
        year_cb.bind("<<ComboboxSelected>>", lambda _e: self._reload())

        tk.Label(filt, text="Month", bg=self.BG, fg=self.MUTED,
                 font=("Arial", 8, "bold")).pack(side="left", padx=(14, 6))
        month_cb = ttk.Combobox(
            filt, textvariable=self.month_var, values=list(MONTH_NAMES),
            state="readonly", width=12, font=("Arial", 9),
        )
        month_cb.pack(side="left", ipady=3)
        month_cb.bind("<<ComboboxSelected>>", lambda _e: self._reload())

        tk.Label(filt, text="From", bg=self.BG, fg=self.MUTED,
                 font=("Arial", 8, "bold")).pack(side="left", padx=(14, 6))
        tk.Entry(
            filt, textvariable=self.from_var, width=12,
            bg="white", fg=self.TEXT, relief="solid", bd=1,
            font=("Arial", 10), insertbackground=self.RED,
        ).pack(side="left", ipady=4)

        tk.Label(filt, text="To", bg=self.BG, fg=self.MUTED,
                 font=("Arial", 8, "bold")).pack(side="left", padx=(10, 6))
        tk.Entry(
            filt, textvariable=self.to_var, width=12,
            bg="white", fg=self.TEXT, relief="solid", bd=1,
            font=("Arial", 10), insertbackground=self.RED,
        ).pack(side="left", ipady=4)

        tk.Button(
            filt, text="Apply", command=self._reload,
            bg="white", fg=self.TEXT,
            activebackground="#F3F4F6",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=12, pady=4,
        ).pack(side="left", padx=(10, 0))

        tk.Button(
            filt, text="Reset", command=self._reset,
            bg="white", fg=self.MUTED,
            activebackground="#F3F4F6",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            padx=12, pady=4,
        ).pack(side="left", padx=(6, 0))

        # ---- export buttons (moved up so always visible) ----
        tk.Button(
            filt, text="Export CSV", command=self._export_csv,
            bg="white", fg=self.TEXT,
            activebackground="#F3F4F6",
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=12, pady=4,
        ).pack(side="right")

        tk.Button(
            filt, text="Export PDF", command=self._export_pdf,
            bg="white", fg=self.TEXT,
            activebackground="#F3F4F6",
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=12, pady=4,
        ).pack(side="right", padx=(0, 8))

        # ---- scrollable body ----
        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True, padx=28, pady=(0, 10))

        # summary card
        sum_card = tk.Frame(
            body, bg=self.CARD,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        sum_card.pack(fill="x", pady=(0, 10))

        self.summary_title = tk.Label(
            sum_card, text="Summary",
            bg=self.CARD, fg=self.TEXT,
            font=("Arial", 11, "bold"), anchor="w",
        )
        self.summary_title.pack(anchor="w", padx=16, pady=(12, 6))

        grid = tk.Frame(sum_card, bg=self.CARD)
        grid.pack(fill="x", padx=16, pady=(0, 14))

        self.lbl_count = self._stat_cell(grid, "Total quotations", "0", 0, 0)
        self.lbl_total = self._stat_cell(grid, "Total value", "Rs. 0.00", 0, 1)
        self.lbl_avg = self._stat_cell(grid, "Average value", "Rs. 0.00", 1, 0)
        self.lbl_max = self._stat_cell(grid, "Highest value", "Rs. 0.00", 1, 1)

        # two-column: top customers + top models
        cols = tk.Frame(body, bg=self.BG)
        cols.pack(fill="x", pady=(0, 10))
        cols.columnconfigure(0, weight=1, uniform="col")
        cols.columnconfigure(1, weight=1, uniform="col")

        cust_card = tk.Frame(
            cols, bg=self.CARD,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        cust_card.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        tk.Label(
            cust_card, text="Top Customers",
            bg=self.CARD, fg=self.TEXT,
            font=("Arial", 11, "bold"), anchor="w",
        ).pack(anchor="w", padx=14, pady=(12, 6))
        self.cust_tree = self._make_mini_tree(cust_card, ("Customer", "Q", "Total"))

        model_card = tk.Frame(
            cols, bg=self.CARD,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        model_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        tk.Label(
            model_card, text="Top Models",
            bg=self.CARD, fg=self.TEXT,
            font=("Arial", 11, "bold"), anchor="w",
        ).pack(anchor="w", padx=14, pady=(12, 6))
        self.model_tree = self._make_mini_tree(model_card, ("Model", "Q", "Total"))

        # 12-month breakdown card
        year_card = tk.Frame(
            body, bg=self.CARD,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        year_card.pack(fill="both", expand=True)

        self.year_title = tk.Label(
            year_card, text="12-Month Breakdown",
            bg=self.CARD, fg=self.TEXT,
            font=("Arial", 11, "bold"), anchor="w",
        )
        self.year_title.pack(anchor="w", padx=14, pady=(12, 6))

        year_cols = ("month", "count", "value")
        self.year_tree = ttk.Treeview(
            year_card, columns=year_cols, show="headings",
            style="MR.Treeview", height=8,
        )
        self.year_tree.heading("month", text="Month")
        self.year_tree.heading("count", text="Quotations")
        self.year_tree.heading("value", text="Total value")
        self.year_tree.column("month", width=200, anchor="w")
        self.year_tree.column("count", width=120, anchor="e")
        self.year_tree.column("value", width=200, anchor="e")

        vsb = ttk.Scrollbar(year_card, orient="vertical",
                            command=self.year_tree.yview)
        self.year_tree.configure(yscrollcommand=vsb.set)
        self.year_tree.pack(side="left", fill="both", expand=True,
                            padx=(14, 0), pady=(0, 14))
        vsb.pack(side="right", fill="y", pady=(0, 14), padx=(0, 14))

        # ---- action bar ----
        abar = tk.Frame(
            self, bg=self.CARD, height=60,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        abar.pack(side="bottom", fill="x")
        abar.pack_propagate(False)

        right = tk.Frame(abar, bg=self.CARD)
        right.pack(side="right", padx=22)
        self._btn(right, "Close", self.destroy).pack(side="right", pady=14)

    def _stat_cell(self, parent, label, value, row, col):
        cell = tk.Frame(parent, bg=self.CARD)
        cell.grid(row=row, column=col, sticky="w", padx=(0, 40), pady=(0, 8))
        tk.Label(
            cell, text=label, bg=self.CARD, fg=self.MUTED,
            font=("Arial", 8, "bold"), anchor="w",
        ).pack(anchor="w")
        val_lbl = tk.Label(
            cell, text=value, bg=self.CARD, fg=self.TEXT,
            font=("Arial", 14, "bold"), anchor="w",
        )
        val_lbl.pack(anchor="w")
        return val_lbl

    def _make_mini_tree(self, parent, headings):
        cols = ("c1", "c2", "c3")
        tree = ttk.Treeview(
            parent, columns=cols, show="headings",
            style="MR.Treeview", height=5,
        )
        tree.heading("c1", text=headings[0])
        tree.heading("c2", text=headings[1])
        tree.heading("c3", text=headings[2])
        tree.column("c1", width=220, anchor="w")
        tree.column("c2", width=50, anchor="e")
        tree.column("c3", width=120, anchor="e")
        tree.pack(fill="x", padx=14, pady=(0, 14))
        return tree

    def _btn(self, parent, text, command, *, danger=False):
        return tk.Button(
            parent, text=text, command=command,
            bg="white", fg=self.RED if danger else self.TEXT,
            activebackground=self.RED_LIGHT if danger else "#F3F4F6",
            activeforeground=self.RED if danger else self.TEXT,
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=14, pady=6,
        )

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    def _current_year_month(self):
        try:
            y = int(self.year_var.get())
        except Exception:
            y = date.today().year
        try:
            m_name = self.month_var.get()
            m = list(MONTH_NAMES).index(m_name) + 1
        except Exception:
            m = date.today().month
        return y, m

    def _parse_optional(self, text):
        text = _text(text)
        if not text:
            return None
        from datetime import datetime
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                pass
        return None

    def _reset(self):
        today = date.today()
        self.year_var.set(str(today.year))
        self.month_var.set(MONTH_NAMES[today.month - 1])
        self.from_var.set("")
        self.to_var.set("")
        self._reload()

    def _reload(self):
        if get_monthly_summary is None or get_year_breakdown is None:
            messagebox.showerror(
                "Monthly Report",
                "Report service unavailable.",
                parent=self,
            )
            return

        y, m = self._current_year_month()
        from_d = self._parse_optional(self.from_var.get())
        to_d = self._parse_optional(self.to_var.get())

        if from_d or to_d:
            period_label = "Custom range"
        else:
            period_label = f"{MONTH_NAMES[m - 1]} {y}"

        try:
            summary = get_monthly_summary(
                y, m, from_date=from_d, to_date=to_d,
            )
        except Exception as e:
            messagebox.showerror(
                "Monthly Report",
                f"Could not compute summary:\n{e}",
                parent=self,
            )
            return

        # update summary card
        self.summary_title.configure(text=f"Summary — {period_label}")
        self.lbl_count.configure(text=str(summary["count"]))
        self.lbl_total.configure(text=_money(summary["total_value"]))
        self.lbl_avg.configure(text=_money(summary["average_value"]))
        self.lbl_max.configure(text=_money(summary["max_value"]))

        # top customers / models
        for t in self.cust_tree.get_children():
            self.cust_tree.delete(t)
        for c in summary["top_customers"]:
            self.cust_tree.insert(
                "", "end",
                values=(c["name"], str(c["count"]), _money(c["value"])),
            )

        for t in self.model_tree.get_children():
            self.model_tree.delete(t)
        for mm in summary["top_models"]:
            self.model_tree.insert(
                "", "end",
                values=(mm["name"], str(mm["count"]), _money(mm["value"])),
            )

        # 12-month breakdown
        try:
            breakdown = get_year_breakdown(y)
        except Exception:
            breakdown = []

        self.year_title.configure(text=f"12-Month Breakdown — {y}")
        for t in self.year_tree.get_children():
            self.year_tree.delete(t)

        total_count = 0
        total_value = 0.0
        for row in breakdown:
            total_count += row["count"]
            total_value += row["total_value"]
            self.year_tree.insert(
                "", "end",
                values=(
                    f"{row['month_name']} {y}",
                    str(row["count"]),
                    _money(row["total_value"]),
                ),
            )
        self.year_tree.insert(
            "", "end",
            values=("TOTAL", str(total_count), _money(total_value)),
            tags=("total",),
        )
        try:
            self.year_tree.tag_configure("total", font=("Arial", 9, "bold"))
        except Exception:
            pass

    # --------------------------------------------------------
    # EXPORT
    # --------------------------------------------------------

    def _default_filename(self, ext):
        y, m = self._current_year_month()
        return f"MonthlyReport_{MONTH_NAMES[m-1]}_{y}.{ext}"

    def _export_csv(self):
        if export_csv is None:
            return
        y, m = self._current_year_month()
        from_d = self._parse_optional(self.from_var.get())
        to_d = self._parse_optional(self.to_var.get())

        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Monthly Report as CSV",
            defaultextension=".csv",
            initialfile=self._default_filename("csv"),
            filetypes=[("CSV file", "*.csv")],
        )
        if not path:
            return
        try:
            export_csv(y, m, path, from_date=from_d, to_date=to_d)
        except Exception as e:
            messagebox.showerror(
                "Export CSV",
                f"Could not export:\n{e}",
                parent=self,
            )
            return
        messagebox.showinfo(
            "Export CSV",
            f"Saved to:\n{path}",
            parent=self,
        )

    def _export_pdf(self):
        if export_pdf is None:
            return
        y, m = self._current_year_month()
        from_d = self._parse_optional(self.from_var.get())
        to_d = self._parse_optional(self.to_var.get())

        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Monthly Report as PDF",
            defaultextension=".pdf",
            initialfile=self._default_filename("pdf"),
            filetypes=[("PDF file", "*.pdf")],
        )
        if not path:
            return
        try:
            export_pdf(y, m, path, from_date=from_d, to_date=to_d)
        except Exception as e:
            messagebox.showerror(
                "Export PDF",
                f"Could not export:\n{e}",
                parent=self,
            )
            return
        messagebox.showinfo(
            "Export PDF",
            f"Saved to:\n{path}",
            parent=self,
        )
