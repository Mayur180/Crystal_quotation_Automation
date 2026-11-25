# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# MONTHLY REPORT WINDOW
# ============================================================

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date

from ui.crystal import theme as T
from ui.crystal import widgets as W


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

    BG = T.BG
    CARD = T.SURFACE
    TEXT = T.TEXT
    MUTED = T.TEXT_MUTED
    BORDER = T.BORDER
    RED = T.ACCENT
    RED_LIGHT = T.ACCENT_SOFT
    SOFT = T.SURFACE_ALT

    def __init__(self, parent):
        super().__init__(parent)

        self.title("CRYSTAL | Monthly Report")
        self.geometry("1180x740")
        self.minsize(1000, 640)
        self.configure(bg=self.BG)
        W.set_window_icon(self)

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

        W.apply_ttk_theme(self)
        self._build_interface()
        self._reload()

        # Esc closes the window
        try:
            self.bind("<Escape>", lambda _e: self.destroy())
        except Exception:
            pass

    # --------------------------------------------------------
    # UI BUILD
    # --------------------------------------------------------

    def _build_interface(self):
        header = W.PageHeader(
            self, title="Monthly Report",
            subtitle="Business summary and yearly totals",
            meta="—", padx=28,
        )
        header.pack(fill="x")
        self.period_meta = header.meta_label

        # ---- filter bar ----
        filt = tk.Frame(
            self, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        filt.pack(fill="x", padx=28, pady=(14, 10))
        row = tk.Frame(filt, bg=T.SURFACE)
        row.pack(fill="x", padx=14, pady=10)

        def _label(text, pad=(0, 5)):
            tk.Label(row, text=text.upper(), bg=T.SURFACE,
                     fg=T.TEXT_MUTED, font=T.FONT_LABEL).pack(
                side="left", padx=pad)

        _label("Year")
        year_cb = ttk.Combobox(
            row, textvariable=self.year_var, values=self.years,
            state="readonly", width=6, font=T.FONT_SMALL,
        )
        year_cb.pack(side="left", ipady=4)
        year_cb.bind("<<ComboboxSelected>>", lambda _e: self._reload())

        _label("Month", (10, 5))
        month_cb = ttk.Combobox(
            row, textvariable=self.month_var, values=list(MONTH_NAMES),
            state="readonly", width=10, font=T.FONT_SMALL,
        )
        month_cb.pack(side="left", ipady=4)
        month_cb.bind("<<ComboboxSelected>>", lambda _e: self._reload())

        _label("From", (10, 5))
        W.SearchEntry(
            row, textvariable=self.from_var, width=11,
            placeholder="dd-mm-yyyy", show_icon=False,
        ).pack(side="left")

        _label("To", (8, 5))
        W.SearchEntry(
            row, textvariable=self.to_var, width=11,
            placeholder="dd-mm-yyyy", show_icon=False,
        ).pack(side="left")

        W.PrimaryButton(
            row, "Apply", self._reload, padx=12, pady=7,
        ).pack(side="left", padx=(10, 0))
        W.GhostButton(
            row, "Reset", self._reset, padx=11, pady=7,
        ).pack(side="left", padx=(6, 0))

        # ---- action bar (bottom first) ----
        abar = tk.Frame(
            self, bg=T.SURFACE, height=64,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        abar.pack(side="bottom", fill="x")
        abar.pack_propagate(False)
        W.GhostButton(
            abar, "Close", self.destroy, padx=18, pady=7,
        ).pack(side="right", padx=22, pady=13)
        W.GhostButton(
            abar, "Export CSV", self._export_csv, padx=14, pady=7,
        ).pack(side="right", padx=(0, 10), pady=13)
        W.GhostButton(
            abar, "Export PDF", self._export_pdf, padx=14, pady=7,
        ).pack(side="right", pady=13)

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
            bg=self.CARD, fg=T.TEXT,
            font=T.FONT_H3, anchor="w",
        )
        self.summary_title.pack(anchor="w", padx=18, pady=(12, 2))

        grid = tk.Frame(sum_card, bg=self.CARD)
        grid.pack(fill="x", padx=18, pady=(0, 14))
        for col in range(4):
            grid.columnconfigure(col, weight=1, uniform="stat")

        self.lbl_count = self._stat_cell(grid, "Total quotations", "0", 0, 0)
        self.lbl_total = self._stat_cell(grid, "Total value", "₹ 0.00", 0, 1)
        self.lbl_avg = self._stat_cell(grid, "Average value", "₹ 0.00", 0, 2)
        self.lbl_max = self._stat_cell(grid, "Highest value", "₹ 0.00", 0, 3)

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
            cust_card, text="Top customers",
            bg=self.CARD, fg=T.TEXT,
            font=T.FONT_H3, anchor="w",
        ).pack(anchor="w", padx=16, pady=(12, 6))
        self.cust_tree = self._make_mini_tree(cust_card, ("Customer", "Qty", "Total"))
        self.cust_note = self._empty_note(
            cust_card, "No customer activity in this period.")

        model_card = tk.Frame(
            cols, bg=self.CARD,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        model_card.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        tk.Label(
            model_card, text="Top models",
            bg=self.CARD, fg=T.TEXT,
            font=T.FONT_H3, anchor="w",
        ).pack(anchor="w", padx=16, pady=(12, 6))
        self.model_tree = self._make_mini_tree(model_card, ("Model", "Qty", "Total"))
        self.model_note = self._empty_note(
            model_card, "No model activity in this period.")

        # 12-month breakdown card
        year_card = tk.Frame(
            body, bg=self.CARD,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        year_card.pack(fill="both", expand=True)

        self.year_title = tk.Label(
            year_card, text="12-Month breakdown",
            bg=self.CARD, fg=T.TEXT,
            font=T.FONT_H3, anchor="w",
        )
        self.year_title.pack(anchor="w", padx=16, pady=(12, 6))

        year_cols = ("month", "count", "value")
        self.year_tree = ttk.Treeview(
            year_card, columns=year_cols, show="headings", height=3,
        )
        self.year_tree.heading("month", text="Month", anchor="w")
        self.year_tree.heading("count", text="Quotations", anchor="e")
        self.year_tree.heading("value", text="Total value", anchor="e")
        self.year_tree.column("month", width=220, anchor="w", stretch=True)
        self.year_tree.column("count", width=120, anchor="e")
        self.year_tree.column("value", width=160, anchor="e")
        self.year_tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        self.year_tree.tag_configure("oddrow", background=T.SURFACE)

        vsb = ttk.Scrollbar(year_card, orient="vertical",
                            command=self.year_tree.yview)
        self.year_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 2), pady=(0, 2))
        self.year_tree.pack(side="left", fill="both", expand=True,
                            padx=2, pady=(0, 2))

    def _stat_cell(self, parent, label, value, row, col):
        cell = tk.Frame(parent, bg=self.CARD)
        cell.grid(row=row, column=col, sticky="w", padx=(0, 24), pady=(4, 10))
        tk.Label(
            cell, text=label.upper(), bg=self.CARD, fg=self.MUTED,
            font=T.FONT_LABEL, anchor="w",
        ).pack(anchor="w")
        val_lbl = tk.Label(
            cell, text=value, bg=self.CARD, fg=T.TEXT,
            font=T.FONT_H1, anchor="w",
        )
        val_lbl.pack(anchor="w")
        return val_lbl

    def _empty_note(self, parent, text):
        return tk.Label(
            parent, text=text, bg=self.CARD, fg=T.TEXT_FAINT,
            font=T.FONT_SMALL,
        )

    def _toggle_note(self, note, visible):
        try:
            if visible:
                note.place(relx=0.5, rely=0.66, anchor="center")
                note.lift()
            else:
                note.place_forget()
        except Exception:
            pass

    def _make_mini_tree(self, parent, headings):
        cols = ("c1", "c2", "c3")
        tree = ttk.Treeview(
            parent, columns=cols, show="headings", height=3,
        )
        tree.heading("c1", text=headings[0], anchor="w")
        tree.heading("c2", text=headings[1], anchor="e")
        tree.heading("c3", text=headings[2], anchor="e")
        tree.column("c1", width=200, anchor="w", stretch=True)
        tree.column("c2", width=50, anchor="e")
        tree.column("c3", width=110, anchor="e")
        tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        tree.tag_configure("oddrow", background=T.SURFACE)
        tree.pack(fill="x", padx=14, pady=(0, 14))
        return tree

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
        try:
            if self.period_meta is not None:
                self.period_meta.configure(text=period_label)
        except Exception:
            pass
        self.lbl_count.configure(text=str(summary["count"]))
        self.lbl_total.configure(text=_money(summary["total_value"]))
        self.lbl_avg.configure(text=_money(summary["average_value"]))
        self.lbl_max.configure(text=_money(summary["max_value"]))

        # top customers / models
        for t in self.cust_tree.get_children():
            self.cust_tree.delete(t)
        for i, c in enumerate(summary["top_customers"]):
            self.cust_tree.insert(
                "", "end",
                values=(c["name"], str(c["count"]), _money(c["value"])),
                tags=("evenrow" if i % 2 == 0 else "oddrow",),
            )

        for t in self.model_tree.get_children():
            self.model_tree.delete(t)
        for i, mm in enumerate(summary["top_models"]):
            self.model_tree.insert(
                "", "end",
                values=(mm["name"], str(mm["count"]), _money(mm["value"])),
                tags=("evenrow" if i % 2 == 0 else "oddrow",),
            )

        self._toggle_note(self.cust_note, not summary["top_customers"])
        self._toggle_note(self.model_note, not summary["top_models"])

        # 12-month breakdown
        try:
            breakdown = get_year_breakdown(y)
        except Exception:
            breakdown = []

        self.year_title.configure(text=f"12-Month breakdown — {y}")
        for t in self.year_tree.get_children():
            self.year_tree.delete(t)

        total_count = 0
        total_value = 0.0
        for i, row in enumerate(breakdown):
            total_count += row["count"]
            total_value += row["total_value"]
            self.year_tree.insert(
                "", "end",
                values=(
                    f"{row['month_name']} {y}",
                    str(row["count"]),
                    _money(row["total_value"]),
                ),
                tags=("evenrow" if i % 2 == 0 else "oddrow",),
            )
        self.year_tree.insert(
            "", "end",
            values=("TOTAL", str(total_count), _money(total_value)),
            tags=("total",),
        )
        try:
            self.year_tree.tag_configure(
                "total", font=T.FONT_BODY_B, background=T.SURFACE_ALT)
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
