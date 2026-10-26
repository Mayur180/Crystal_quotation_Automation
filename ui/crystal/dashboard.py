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
        self._is_admin = False
        try:
            from app.services.user_service import is_admin
            self._is_admin = is_admin(username)
        except Exception:
            pass

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
            is_admin=self._is_admin
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
        summary = self._load_summary()

        # ─── KPI row ───
        kpi_row = tk.Frame(self._body, bg=T.BG)
        kpi_row.pack(fill="x", padx=pad, pady=(pad, 0))

        # Added icons to match VMM style
        kpis = [
            ("📦", f"{summary['products']:,}", "Products",     T.ACCENT),
            ("👥", f"{summary['customers']:,}", "Customers",   None),
            ("📄", f"{summary['quotes']:,}",   "Quotations",  None),
        ]
        for i, (icon, val, label, accent) in enumerate(kpis):
            card_wrap = tk.Frame(kpi_row, bg=T.SURFACE, highlightbackground=T.BORDER, highlightthickness=1)
            card_wrap.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 16, 0))
            
            icon_lbl = tk.Label(card_wrap, text=icon, bg=T.SURFACE, fg=T.TEXT_BODY, font=("Arial", 24))
            icon_lbl.pack(side="left", padx=(20, 10), pady=20)
            
            card = W.StatCard(card_wrap, value=val, label=label, accent_color=accent)
            card.pack(side="left", fill="both", expand=True, pady=10, padx=(0, 20))

        # ─── Two-column row ───
        two_col = tk.Frame(self._body, bg=T.BG)
        two_col.pack(fill="both", expand=True, padx=pad, pady=(24, pad))

        # Left: Recent Activity
        left = tk.Frame(two_col, bg=T.BG)
        left.pack(side="left", fill="both", expand=True)
        
        tk.Label(left, text="Recent Quotations", bg=T.BG, fg=T.TEXT,
                 font=T.FONT_H2).pack(anchor="w")
        tk.Label(left, text="Your last 5 generated quotes", bg=T.BG, fg=T.TEXT_BODY,
                 font=T.FONT_BODY).pack(anchor="w", pady=(2, 12))
        
        if not summary["recent"]:
            # Empty State Fix
            empty_box = tk.Frame(left, bg=T.SURFACE, highlightbackground=T.BORDER, highlightthickness=1)
            empty_box.pack(fill="both", expand=True)
            
            tk.Label(empty_box, text="📄", bg=T.SURFACE, fg=T.BORDER, font=("Arial", 48)).pack(pady=(40, 10))
            tk.Label(empty_box, text="No quotations yet", bg=T.SURFACE, fg=T.TEXT, font=T.FONT_H2).pack()
            tk.Label(empty_box, text="Create your first quote to see it here.", bg=T.SURFACE, fg=T.TEXT_BODY, font=T.FONT_BODY).pack(pady=(5, 20))
            
            btn = tk.Button(empty_box, text="+ Create New Quotation", bg=T.ACCENT, fg="white", 
                            font=T.FONT_BODY_B, relief="flat", cursor="hand2", command=self._new_quotation)
            btn.pack(pady=10, ipadx=10, ipady=5)
        else:
            for r in summary["recent"]:
                row = tk.Frame(left, bg=T.SURFACE, highlightbackground=T.BORDER, highlightthickness=1)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=r["number"], bg=T.SURFACE, fg=T.TEXT, font=T.FONT_BODY_B).pack(side="left", padx=10, pady=6)
                tk.Label(row, text=r["customer"] or "—", bg=T.SURFACE, fg=T.TEXT_BODY, font=T.FONT_BODY).pack(side="left", padx=10)
                try:
                    amt = f"₹{float(r['total']):,.0f}"
                except Exception:
                    amt = "₹0"
                tk.Label(row, text=amt, bg=T.SURFACE, fg=T.ACCENT, font=T.FONT_BODY_B).pack(side="right", padx=10)

        # Right: Quick Actions
        right = tk.Frame(two_col, bg=T.BG)
        right.pack(side="right", fill="both", expand=True, padx=(24, 0))
        
        tk.Label(right, text="Quick Actions", bg=T.BG, fg=T.TEXT,
                 font=T.FONT_H2).pack(anchor="w")
        tk.Label(right, text="Primary workflow shortcuts", bg=T.BG,
                 fg=T.TEXT_BODY, font=T.FONT_BODY).pack(anchor="w", pady=(2, 12))
        
        actions = [
            ("+", "New Quotation", "Create a fresh quote", self._new_quotation),
            ("📦", "Manage Products", f"{summary['products']:,} products", self._open_products),
            ("👥", "Customers", "Buyer database", self._open_customers),
        ]
        for icon, title, subtitle, cmd in actions:
            card = tk.Frame(right, bg=T.SURFACE, cursor="hand2", highlightbackground=T.BORDER, highlightthickness=1)
            card.pack(fill="x", pady=6)
            
            tk.Label(card, text=icon, bg=T.SURFACE, fg=T.ACCENT, font=("Arial", 18)).pack(side="left", padx=16, pady=12)
            box = tk.Frame(card, bg=T.SURFACE)
            box.pack(side="left", fill="x", expand=True)
            tk.Label(box, text=title, bg=T.SURFACE, fg=T.TEXT, font=T.FONT_BODY_B).pack(anchor="w")
            tk.Label(box, text=subtitle, bg=T.SURFACE, fg=T.TEXT_BODY, font=T.FONT_BODY).pack(anchor="w")
            
            for w in (card, box, *box.winfo_children()):
                w.bind("<Button-1>", lambda e, c=cmd: c())

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
        import json
        from app.services.paths import get_data_dir
        import os
        
        # Force the path to the Crystal data folder (not VMM)
        base_data_dir = get_data_dir()
        crystal_data_dir = base_data_dir.parent / "Crystal"
        
        # If Crystal folder doesn't exist, fall back to base
        if not crystal_data_dir.exists():
            crystal_data_dir = base_data_dir
        
        # --- products count from catalog ---
        p_count = 0
        try:
            cat_file = crystal_data_dir / "catalog.json"
            if cat_file.exists():
                cat = json.loads(cat_file.read_text(encoding="utf-8"))
                p_count = len(cat.get("products", []))
        except Exception:
            pass

        # --- customers count ---
        c_count = 0
        try:
            c_file = crystal_data_dir / "customers.json"
            if c_file.exists():
                c_data = json.loads(c_file.read_text(encoding="utf-8"))
                if isinstance(c_data, list):
                    c_count = len(c_data)
                else:
                    c_count = len(c_data.get("customers", []))
        except Exception:
            pass

        # --- quotes count + recent activity ---
        q_count = 0
        recent = []
        try:
            q_file = crystal_data_dir / "quotations.json"
            if q_file.exists():
                q_data = json.loads(q_file.read_text(encoding="utf-8"))
                # Handle both list and dict formats
                if isinstance(q_data, list):
                    qs = q_data
                elif isinstance(q_data, dict):
                    qs = q_data.get("quotations", [])
                else:
                    qs = []
                q_count = len(qs)
                # Sort newest first, take last 5
                qs_sorted = sorted(qs, key=lambda x: x.get("date", ""), reverse=True)[:5]
                for q in qs_sorted:
                    recent.append({
                        "number": q.get("quotation_number", ""),
                        "customer": q.get("customer_name", ""),
                        "total": q.get("grand_total", 0),
                        "date": q.get("date", ""),
                    })
        except Exception:
            pass

        return {
            "products": p_count,
            "customers": c_count,
            "quotes": q_count,
            "recent": recent,
        }

    def _on_nav(self, key):
        """Dispatch sidebar clicks to the correct screen."""
        handlers = {
            "dashboard":   self._go_home,
            "quotes":      self._open_history,
            "products":    self._open_products,
            "customers":   self._open_customers,
            "reports":     self._open_reports,
            "leads":       self._open_leads,
            "users":       self._open_user_manager,
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

    def _open_leads(self):
        try:
            from ui.crystal.leads_manager import LeadsManager
            LeadsManager(self, on_convert=self._convert_lead)
        except Exception as e:
            W.Toast.show(self, f"Could not open Leads: {e}", kind="error")

    def _convert_lead(self, lead):
        try:
            from ui.crystal.quotation_form import QuotationForm
            # Open the quotation form, passing the lead data to pre-fill it
            QuotationForm(app=self, parent=self, prefill=lead)
        except Exception as e:
            W.Toast.show(self, f"Could not open Quotation: {e}", kind="error")

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

    def _open_user_manager(self):
        try:
            from ui.crystal.user_manager import UserManager
            UserManager(self, current_username=self._username)
        except Exception as e:
            W.Toast.show(self, f"Could not open User Management: {e}", kind="error")

    def _quit(self):
        if self._on_logout:
            self._on_logout()
        self.destroy()


# ═════════════════════════════════════════════════════════════
# STANDALONE PREVIEW
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    Dashboard().mainloop()
