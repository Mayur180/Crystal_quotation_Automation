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

        # Global Search Bar
        search_frame = tk.Frame(bar, bg=T.SURFACE)
        search_frame.pack(side="left", padx=15)
        
        tk.Label(search_frame, text="🔍", bg=T.SURFACE, fg=T.TEXT_MUTED,
                 font=("Arial", 12)).pack(side="left", padx=(0, 5))
        
        self._search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self._search_var,
            font=("Arial", 10),
            width=30,
            relief="solid",
            bd=1
        )
        search_entry.pack(side="left", pady=15)
        search_entry.bind("<Return>", lambda e: self._do_global_search())

        right = tk.Frame(bar, bg=T.SURFACE)
        right.pack(side="right", fill="y", padx=(0, 20))
        
        # Refresh Button
        tk.Button(
            right, 
            text="🔄 Refresh", 
            bg=T.BG, fg=T.TEXT, 
            font=("Arial", 9, "bold"), 
            relief="flat", 
            cursor="hand2",
            command=self._refresh_dashboard
        ).pack(side="right", padx=(0, 10), pady=15)

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
            ("📈", f"{summary['conversion_rate']:.1f}%", "Conversion %", "#27AE60"),
            ("⏰", f"{summary.get('pending_followups', 0)}", "Follow-ups", "#E67E22"),
        ]
        for i, (icon, val, label, accent) in enumerate(kpis):
            card_wrap = tk.Frame(kpi_row, bg=T.SURFACE, highlightbackground=T.BORDER, highlightthickness=1)
            card_wrap.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 8, 0))
            
            # Make Follow-ups card clickable
            if label == "Follow-ups":
                card_wrap.configure(cursor="hand2")
                for w in (card_wrap,):
                    w.bind("<Button-1>", lambda e: self._show_pending_followups())
                # Bind children too
                def bind_children(parent, cmd):
                    for child in parent.winfo_children():
                        child.bind("<Button-1>", lambda e: cmd())
                        bind_children(child, cmd)
            
            icon_lbl = tk.Label(card_wrap, text=icon, bg=T.SURFACE, fg=T.TEXT_BODY, font=("Arial", 24))
            icon_lbl.pack(side="left", padx=(12, 6), pady=20)
            
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
                row = tk.Frame(left, bg=T.SURFACE, highlightbackground=T.BORDER, highlightthickness=1, cursor="hand2")
                row.pack(fill="x", pady=2)
                
                lbl_num = tk.Label(row, text=r["number"], bg=T.SURFACE, fg=T.TEXT, font=T.FONT_BODY_B)
                lbl_num.pack(side="left", padx=10, pady=6)
                
                lbl_cust = tk.Label(row, text=r["customer"] or "—", bg=T.SURFACE, fg=T.TEXT_BODY, font=T.FONT_BODY)
                lbl_cust.pack(side="left", padx=10)
                
                # Make the row clickable
                for w in (row, lbl_num, lbl_cust):
                    w.bind("<Button-1>", lambda e, num=r["number"]: self._show_quotation_items(num))

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

        # Calculate conversion rate (Accepted / Total * 100)
        accepted_count = 0
        try:
            q_file = crystal_data_dir / "quotations.json"
            if q_file.exists():
                q_data = json.loads(q_file.read_text(encoding="utf-8"))
                if isinstance(q_data, list):
                    qs_all = q_data
                elif isinstance(q_data, dict):
                    qs_all = q_data.get("quotations", [])
                else:
                    qs_all = []
                accepted_count = sum(1 for q in qs_all if str(q.get("status", "")).strip().lower() == "accepted")
        except Exception:
            pass
        
        conversion_rate = (accepted_count / q_count * 100) if q_count > 0 else 0.0

        # Count pending follow-ups (3+ days old, not accepted/rejected)
        pending_followups = 0
        try:
            from app.services.quotation_history_service import get_pending_followups
            pending_followups = len(get_pending_followups(days_old=3))
        except Exception:
            pass
        
        return {
            "products": p_count,
            "customers": c_count,
            "quotes": q_count,
            "accepted": accepted_count,
            "conversion_rate": conversion_rate,
            "pending_followups": pending_followups,
            "recent": recent,
        }


    def _show_quotation_items(self, quotation_number):
        """Show a popup with the items of the selected quotation."""
        import tkinter as tk
        from tkinter import ttk
        import json
        from app.services.paths import get_data_dir
        
        # Fetch the quotation details
        try:
            base_data_dir = get_data_dir()
            crystal_data_dir = base_data_dir.parent / "Crystal"
            if not crystal_data_dir.exists():
                crystal_data_dir = base_data_dir
                
            q_file = crystal_data_dir / "quotations.json"
            if not q_file.exists():
                return
                
            q_data = json.loads(q_file.read_text(encoding="utf-8"))
            
            # Handle list or dict format
            if isinstance(q_data, list):
                qs = q_data
            elif isinstance(q_data, dict):
                qs = q_data.get("quotations", [])
            else:
                qs = []
                
            quotation = next((q for q in qs if q.get("quotation_number") == quotation_number), None)
            
            if not quotation:
                return
                
        except Exception as e:
            print(f"Error fetching quotation: {e}")
            return

        # Create popup window
        popup = tk.Toplevel(self)
        popup.title(f"Quotation {quotation_number}")
        popup.geometry("700x400")
        popup.configure(bg=T.BG)
        popup.transient(self)
        popup.grab_set()
        
        # Header
        header = tk.Frame(popup, bg=T.SURFACE)
        header.pack(fill="x")
        tk.Label(header, text=f"Quotation: {quotation_number}", bg=T.SURFACE, fg=T.TEXT, font=("Arial", 14, "bold")).pack(side="left", padx=20, pady=15)
        tk.Label(header, text=f"Customer: {quotation.get('customer_name', '—')}", bg=T.SURFACE, fg=T.TEXT_BODY, font=("Arial", 9)).pack(side="right", padx=20, pady=15)
        
        tk.Frame(popup, bg=T.BORDER, height=1).pack(fill="x")
        
        # Items Table
        table_frame = tk.Frame(popup, bg=T.BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        cols = ("model", "qty", "price", "total")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        tree.heading("model", text="Model")
        tree.heading("qty", text="Qty")
        tree.heading("price", text="Price")
        tree.heading("total", text="Total")
        
        tree.column("model", width=250)
        tree.column("qty", width=60, anchor="center")
        tree.column("price", width=100, anchor="e")
        tree.column("total", width=100, anchor="e")
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        # Populate items
        items = quotation.get("items", [])
        if not items and quotation.get("model"):
            items = [{"model": quotation.get("model"), "qty": quotation.get("machine_qty", 1), "price": quotation.get("machine_price", 0), "total": quotation.get("grand_total", 0)}]
            
        for item in items:
            tree.insert("", "end", values=(
                item.get("model", ""),
                item.get("qty", ""),
                f"₹{float(item.get('price', 0)):,.2f}",
                f"₹{float(item.get('total', 0)):,.2f}"
            ))
            
        # Bottom Info
        footer = tk.Frame(popup, bg=T.SURFACE)
        footer.pack(fill="x", side="bottom")
        tk.Frame(footer, bg=T.BORDER, height=1).pack(fill="x")
        tk.Label(footer, text=f"Grand Total: ₹{float(quotation.get('grand_total', 0)):,.2f}", bg=T.SURFACE, fg=T.ACCENT, font=("Arial", 12, "bold")).pack(side="right", padx=20, pady=15)
        tk.Button(footer, text="Close", bg=T.BG, fg=T.TEXT, relief="flat", command=popup.destroy).pack(side="left", padx=20, pady=15)


    def _refresh_dashboard(self):
        """Reload the dashboard data without closing the app."""
        # Clear existing widgets in the body
        for widget in self._body.winfo_children():
            widget.destroy()
        # Rebuild
        self._build_body()

    def _show_pending_followups(self):
        """Show a popup listing quotations that need follow-up."""
        import tkinter as tk
        from tkinter import ttk
        from app.services.quotation_history_service import get_pending_followups
        
        pending = get_pending_followups(days_old=3)
        
        popup = tk.Toplevel(self)
        popup.title("Pending Follow-ups")
        popup.geometry("750x450")
        popup.configure(bg=T.BG)
        popup.transient(self)
        popup.grab_set()
        
        tk.Label(popup, text="⏰ Quotations Needing Follow-up (3+ days old)",
                 bg=T.BG, fg=T.TEXT, font=("Arial", 14, "bold")).pack(pady=15)
        
        if not pending:
            tk.Label(popup, text="✅ No pending follow-ups! All quotations are up to date.",
                     bg=T.BG, fg="#27AE60", font=("Arial", 11)).pack(pady=50)
            tk.Button(popup, text="Close", command=popup.destroy, bg=T.BG, relief="flat").pack(pady=10)
            return
        
        # Table
        frame = tk.Frame(popup, bg=T.BG)
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        cols = ("quotation", "customer", "date", "total")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=12)
        tree.heading("quotation", text="Quotation No.")
        tree.heading("customer", text="Customer")
        tree.heading("date", text="Date")
        tree.heading("total", text="Grand Total")
        tree.column("quotation", width=180)
        tree.column("customer", width=250)
        tree.column("date", width=120)
        tree.column("total", width=150, anchor="e")
        
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        for q in pending:
            try:
                total_str = f"₹{float(q['grand_total']):,.2f}"
            except Exception:
                total_str = f"₹{q['grand_total']}"
            tree.insert("", "end", values=(
                q["quotation_number"],
                q["customer_name"],
                q["date"],
                total_str,
            ))
        
        # Bottom buttons
        btn_frame = tk.Frame(popup, bg=T.BG)
        btn_frame.pack(fill="x", pady=10)
        
        def open_selected():
            sel = tree.selection()
            if not sel:
                return
            values = tree.item(sel[0], "values")
            quot_no = values[0]
            popup.destroy()
            # Open Quotation History and select this quotation
            try:
                from ui.crystal.quotation_history import QuotationHistory
                QuotationHistory(self)
            except Exception as e:
                print(f"Could not open history: {e}")
        
        tk.Button(btn_frame, text="Open Quotation History", command=open_selected,
                  bg=T.ACCENT, fg="white", font=("Arial", 10, "bold"), relief="flat",
                  padx=15, pady=6).pack(side="right", padx=10)
        tk.Button(btn_frame, text="Close", command=popup.destroy,
                  bg=T.BG, fg=T.TEXT, relief="flat").pack(side="right", padx=10)

    def _do_global_search(self):
        """Execute a global search and show results in a popup."""
        import tkinter as tk
        from tkinter import ttk
        from app.services.search_service import global_search
        
        query = self._search_var.get().strip()
        if len(query) < 2:
            from tkinter import messagebox
            messagebox.showinfo("Search", "Please enter at least 2 characters.", parent=self)
            return
        
        results = global_search(query)
        
        popup = tk.Toplevel(self)
        popup.title(f"Search Results: {query}")
        popup.geometry("800x500")
        popup.configure(bg="#F4F6F8")
        popup.transient(self)
        popup.grab_set()
        
        tk.Label(popup, text=f"🔍 Results for \"{query}\" ({len(results)} found)",
                 bg="#F4F6F8", fg="#2C3E50", font=("Arial", 14, "bold")).pack(pady=15)
        
        if not results:
            tk.Label(popup, text="No results found.", bg="#F4F6F8", fg="#7F8C8D",
                     font=("Arial", 11)).pack(pady=50)
            tk.Button(popup, text="Close", command=popup.destroy, bg="#F4F6F8", relief="flat").pack(pady=10)
            return
        
        # Treeview
        frame = tk.Frame(popup, bg="#F4F6F8")
        frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        cols = ("type", "title", "subtitle")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        tree.heading("type", text="Type")
        tree.heading("title", text="Name / Number")
        tree.heading("subtitle", text="Details")
        tree.column("type", width=100)
        tree.column("title", width=250)
        tree.column("subtitle", width=380)
        
        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        for r in results:
            tree.insert("", "end", values=(r["type"], r["title"], r["subtitle"]))
        
        tk.Button(popup, text="Close", command=popup.destroy, bg="#F4F6F8", relief="flat").pack(pady=10)

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
