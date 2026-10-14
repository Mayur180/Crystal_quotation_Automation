"""CRYSTAL — Dashboard (mockup C: sidebar + content)."""
import os
import sys
import tkinter as tk

# project root on path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ui.crystal import theme as T
from ui.crystal import widgets as W
from ui.crystal.sidebar import Sidebar


class Dashboard(tk.Tk):
    def __init__(self, *, username="Admin", module="Crystal", on_logout=None):
        super().__init__()
        self.title(f"CRYSTAL | ARMATECH ASSOCIATES — Quotation Manager v4.0")
        self.geometry("1280x800")
        self.configure(bg=T.BG)
        self.minsize(1100, 700)

        self._username = username
        self._module = module
        self._on_logout = on_logout

        self._build()

    # ═════════════════════════════════════════════════════════
    # LAYOUT
    # ═════════════════════════════════════════════════════════

    def _build(self):
        # Root grid: sidebar | content column
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._sidebar = Sidebar(
            self,
            logo_text="CRYSTAL",
            active_key="dashboard",
            on_navigate=self._on_nav,
            on_quit=self._quit,
        )
        self._sidebar.grid(row=0, column=0, sticky="ns")

        # Content column: topbar + body
        content = tk.Frame(self, bg=T.BG)
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)

        # topbar
        topbar = self._make_topbar(content)
        topbar.grid(row=0, column=0, sticky="ew")

        # scrollable body
        body_wrap = tk.Frame(content, bg=T.BG)
        body_wrap.grid(row=1, column=0, sticky="nsew")

        self._canvas = tk.Canvas(body_wrap, bg=T.BG, highlightthickness=0)
        vscroll = tk.Scrollbar(body_wrap, orient="vertical",
                                command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._body = tk.Frame(self._canvas, bg=T.BG)
        self._canvas.create_window((0, 0), window=self._body, anchor="nw")
        self._body.bind(
            "<Configure>",
            lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.bind(
            "<Configure>",
            lambda e: self._canvas.itemconfigure(
                self._canvas.find_all()[0], width=e.width
            ),
        )

        self._build_body()

    def _make_topbar(self, parent):
        bar = tk.Frame(parent, bg=T.SURFACE, height=T.TOPBAR_HEIGHT)
        bar.pack_propagate(False)

        # bottom accents
        tk.Frame(bar, bg=T.ACCENT, height=3).pack(side="bottom", fill="x")
        tk.Frame(bar, bg=T.BORDER, height=1).pack(side="bottom", fill="x")

        left = tk.Frame(bar, bg=T.SURFACE)
        left.pack(side="left", fill="y", padx=(20, 0))

        W.IconButton(left, "☰", self._sidebar.toggle).pack(side="left", pady=12)
        tk.Label(left, text="Dashboard", bg=T.SURFACE, fg=T.TEXT,
                 font=T.FONT_H2).pack(side="left", padx=(12, 0))

        right = tk.Frame(bar, bg=T.SURFACE)
        right.pack(side="right", fill="y", padx=(0, 20))

        W.IconButton(right, "🔔", lambda: None).pack(side="right", pady=12)

        chip = tk.Frame(right, bg=T.SURFACE_ALT, cursor="hand2")
        chip.pack(side="right", padx=(0, 8))
        tk.Label(chip, text="👤", bg=T.SURFACE_ALT, fg=T.TEXT_BODY,
                 font=T.FONT_EMOJI).pack(side="left", padx=(10, 6), pady=8)
        tk.Label(chip, text=self._username, bg=T.SURFACE_ALT, fg=T.TEXT,
                 font=T.FONT_BODY_B).pack(side="left", padx=(0, 12), pady=8)
        if self._on_logout:
            chip.bind("<Button-1>", lambda e: self._on_logout())

        return bar

    # ═════════════════════════════════════════════════════════
    # BODY CONTENT
    # ═════════════════════════════════════════════════════════

    def _build_body(self):
        pad = 28

        # ─── KPI row ───
        kpi_row = tk.Frame(self._body, bg=T.BG)
        kpi_row.pack(fill="x", padx=pad, pady=(pad, 0))

        summary = self._load_summary()
        kpis = [
            ("3,323", "Products",     T.ACCENT),
            ("0",     "Quotes",       None),
        ]
        for i, (val, label, accent) in enumerate(kpis):
            card = W.StatCard(kpi_row, value=val, label=label,
                              accent_color=accent)
            card.pack(side="left", fill="both", expand=True,
                      padx=(0 if i == 0 else 16, 0))

        # ─── Two-column row ───
        two_col = tk.Frame(self._body, bg=T.BG)
        two_col.pack(fill="both", expand=True, padx=pad, pady=(24, pad))

        # left: Quick Actions
        left = tk.Frame(two_col, bg=T.BG)
        left.pack(side="left", fill="both", expand=True)

        self._section_label(left, "Quick Actions", "Primary workflow shortcuts")

        actions = [
            ("＋", "New Quotation",      "Create a fresh quote",   True,  self._new_quotation),
            ("📦", "Manage Products",    "3,323 products",         False, self._open_products),
            ("👥", "Customers",          "Buyer database",         False, self._open_customers),
        ]
        for icon, label, sub, primary, cmd in actions:
            row = W.ActionRow(left, icon=icon, label=label,
                              sublabel=sub, command=cmd, primary=primary)
            row.pack(fill="x", pady=6)

        # right: Recent Activity
        right = tk.Frame(two_col, bg=T.BG, width=380)
        right.pack(side="right", fill="both", padx=(24, 0))
        right.pack_propagate(False)

        self._section_label(right, "Recent Activity", "Latest actions")

        activity_card = W.Card(right)
        activity_card.pack(fill="both", expand=True, pady=(8, 0))

        empty = tk.Frame(activity_card.body, bg=T.SURFACE)
        empty.pack(fill="both", expand=True, pady=40)

        tk.Label(empty, text="📭", bg=T.SURFACE, fg=T.TEXT_FAINT,
                 font=(T.FONT_FAMILY_E, 30)).pack()
        tk.Label(empty, text="No activity yet",
                 bg=T.SURFACE, fg=T.TEXT_BODY,
                 font=T.FONT_BODY_B).pack(pady=(10, 2))
        tk.Label(empty, text="Quotes you create will appear here.",
                 bg=T.SURFACE, fg=T.TEXT_MUTED,
                 font=T.FONT_SMALL).pack()

    def _section_label(self, parent, title, subtitle=None):
        tk.Label(parent, text=title, bg=T.BG, fg=T.TEXT,
                 font=T.FONT_H2, anchor="w").pack(anchor="w")
        if subtitle:
            tk.Label(parent, text=subtitle, bg=T.BG, fg=T.TEXT_MUTED,
                     font=T.FONT_SMALL, anchor="w").pack(anchor="w", pady=(2, 6))

    # ═════════════════════════════════════════════════════════
    # DATA
    # ═════════════════════════════════════════════════════════

    def _load_summary(self):
        try:
            from app.services.catalog_service import get_catalog_summary
            return get_catalog_summary() or {}
        except Exception:
            return {}

    # ═════════════════════════════════════════════════════════
    # NAVIGATION HOOKS
    # ═════════════════════════════════════════════════════════

    def _on_nav(self, key):
        """Dispatch sidebar clicks to the correct screen."""
        handlers = {
            "dashboard":   self._go_home,
            "quotes":      self._open_history,
            "products":    self._open_products,
            "customers":   self._open_customers,
            "reports":     self._open_reports,
            "settings":    self._open_settings,
        }
        handler = handlers.get(key)
        if handler:
            self._sidebar.set_active(key)
            handler()

    # ═════════════════════════════════════════════════════
    # NAV HANDLERS
    # ═════════════════════════════════════════════════════

    def _go_home(self):
        """Return focus to the dashboard (no-op since we're already here)."""
        self._sidebar.set_active("dashboard")
        self.lift()
        self.focus_force()

    def _open_products(self):
        try:
            from ui.crystal.product_manager import ProductManager
            ProductManager(self)
        except Exception as e:
            W.Toast.show(self, f"Could not open Products: {e}", kind="error")

    def _open_customers(self):
        try:
            from ui.crystal.customer_database import CustomerDatabase
            CustomerDatabase(self)
        except Exception as e:
            W.Toast.show(self, f"Could not open Customers: {e}", kind="error")

    def _open_history(self):
        try:
            from ui.crystal.quotation_history import QuotationHistory
            QuotationHistory(self)
        except Exception as e:
            W.Toast.show(self, f"Could not open History: {e}", kind="error")

    def _open_reports(self):
        try:
            from ui.crystal.monthly_report_window import MonthlyReport
            MonthlyReport(self)
        except Exception as e:
            W.Toast.show(self, f"Could not open Reports: {e}", kind="error")

    def _open_settings(self):
        try:
            from ui.crystal.company_settings import CompanySettings
            CompanySettings(self)
        except Exception as e:
            W.Toast.show(self, f"Could not open Settings: {e}", kind="error")

    def _new_quotation(self):
        try:
            from ui.crystal.quotation_form import QuotationForm
            QuotationForm(app=self, parent=self)
        except Exception as e:
            W.Toast.show(self, f"Could not open Quotation Form: {e}", kind="error")

    def _quit(self):
        if self._on_logout:
            self._on_logout()
        self.destroy()


# ═════════════════════════════════════════════════════════════
# STANDALONE PREVIEW
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    Dashboard().mainloop()
