
def get_latest_quotation_number():
    try:
        from app.services.paths import get_data_dir
        counter_file = get_data_dir() / "quotation_counter.json"
        if counter_file.is_file():
            data = json.loads(counter_file.read_text(encoding="utf-8"))
            return data.get("last_number", 0)
    except Exception:
        pass
    return 0

"""CRYSTAL — Dashboard (mockup C: sidebar + content)."""
import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox

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

        # Summary is loaded in the background so the window appears instantly.
        self._summary_cache = None
        self._summary_loading = False
        self._kpi_cards = {}
        self._recent_box = None
        self._products_sub_lbl = None
        self._customers_synced = False
        self._async_queue = queue.Queue()

        self._build()
        
        # Start auto-refresh after UI is built
        self.after(100, self._auto_refresh)
        self.after(150, self._poll_async_queue)
        self.after(200, self._sync_customers_async)

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
        summary = self._summary_cache or self._quick_summary()

        # ─── KPI row ───
        kpi_row = tk.Frame(self._body, bg=T.BG)
        kpi_row.pack(fill="x", padx=pad, pady=(pad, 0))

        self._kpi_cards = {}
        kpis = [
            ("📦", "products", summary.get("products"), "Products",     T.ACCENT),
            ("👥", "customers", summary.get("customers"), "Customers",   None),
            ("📄", "quotes", get_latest_quotation_number() or summary.get("quotes"), "Quotations",  None),
            ("📈", "conversion_rate", summary.get("conversion_rate"), "Conversion %", "#27AE60"),
            ("⏰", "pending_followups", summary.get("pending_followups"), "Follow-ups", "#E67E22"),
        ]
        for i, (icon, key, val, label, accent) in enumerate(kpis):
            card_wrap = tk.Frame(kpi_row, bg=T.SURFACE, highlightbackground=T.BORDER, highlightthickness=1)
            card_wrap.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 8, 0))
            
            if label == "Follow-ups":
                card_wrap.configure(cursor="hand2")
                for w in (card_wrap,):
                    w.bind("<Button-1>", lambda e: self._show_pending_followups())
                def bind_children(parent, cmd):
                    for child in parent.winfo_children():
                        child.bind("<Button-1>", lambda e: cmd())
                        bind_children(child, cmd)
            
            icon_lbl = tk.Label(card_wrap, text=icon, bg=T.SURFACE, fg=T.TEXT_BODY, font=("Arial", 24))
            icon_lbl.pack(side="left", padx=(12, 6), pady=20)
            
            card = W.StatCard(card_wrap, value=self._kpi_text(key, val), label=label, accent_color=accent)
            card.pack(side="left", fill="both", expand=True, pady=10, padx=(0, 20))
            self._kpi_cards[key] = card

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
        
        self._recent_box = tk.Frame(left, bg=T.BG)
        self._recent_box.pack(fill="both", expand=True)
        self._render_recent(self._recent_box, summary.get("recent"))

        # Right: Quick Actions
        right = tk.Frame(two_col, bg=T.BG)
        right.pack(side="right", fill="both", expand=True, padx=(24, 0))
        
        tk.Label(right, text="Quick Actions", bg=T.BG, fg=T.TEXT,
                 font=T.FONT_H2).pack(anchor="w")
        tk.Label(right, text="Primary workflow shortcuts", bg=T.BG,
                 fg=T.TEXT_BODY, font=T.FONT_BODY).pack(anchor="w", pady=(2, 12))
        
        actions = [
            ("+", "New Quotation", "Create a fresh quote", self._new_quotation),
            ("📦", "Manage Products", self._products_subtext(summary.get("products")), self._open_products),
            ("👥", "Customers", "Buyer database", self._open_customers),
        ]
        self._products_sub_lbl = None
        for icon, title, subtitle, cmd in actions:
            card = tk.Frame(right, bg=T.SURFACE, cursor="hand2", highlightbackground=T.BORDER, highlightthickness=1)
            card.pack(fill="x", pady=6)
            
            tk.Label(card, text=icon, bg=T.SURFACE, fg=T.ACCENT, font=("Arial", 18)).pack(side="left", padx=16, pady=12)
            box = tk.Frame(card, bg=T.SURFACE)
            box.pack(side="left", fill="x", expand=True)
            tk.Label(box, text=title, bg=T.SURFACE, fg=T.TEXT, font=T.FONT_BODY_B).pack(anchor="w")
            sub_lbl = tk.Label(box, text=subtitle, bg=T.SURFACE, fg=T.TEXT_BODY, font=T.FONT_BODY)
            sub_lbl.pack(anchor="w")
            if title == "Manage Products":
                self._products_sub_lbl = sub_lbl
            
            for w in (card, box, *box.winfo_children()):
                w.bind("<Button-1>", lambda e, c=cmd: c())

        if self._summary_cache is None:
            self._start_summary_load()

    # ═════════════════════════════════════════════════════════
    # DATA
    # ═════════════════════════════════════════════════════════

    # ─── catalog count cache (catalog.json is 2 MB and never changes) ───
    _catalog_cache = {"path": None, "mtime": None, "count": 0}

    def _crystal_data_dir(self):
        from app.services.paths import get_data_dir
        base_data_dir = get_data_dir()
        crystal_data_dir = base_data_dir.parent / "Crystal"
        return crystal_data_dir if crystal_data_dir.exists() else base_data_dir

    def _catalog_count(self):
        import json
        cat_file = self._crystal_data_dir() / "catalog.json"
        try:
            mtime = cat_file.stat().st_mtime
        except OSError:
            return 0
        cache = self._catalog_cache
        if cache["path"] == str(cat_file) and cache["mtime"] == mtime:
            return cache["count"]
        try:
            cat = json.loads(cat_file.read_text(encoding="utf-8"))
            count = len(cat.get("products", []))
        except Exception:
            count = 0
        cache.update(path=str(cat_file), mtime=mtime, count=count)
        return count

    def _local_customer_count(self):
        import json
        c_file = self._crystal_data_dir() / "customers.json"
        try:
            if c_file.exists():
                c_data = json.loads(c_file.read_text(encoding="utf-8"))
                if isinstance(c_data, list):
                    return len(c_data)
                return len(c_data.get("customers", []))
        except Exception:
            pass
        return 0

    def _quick_summary(self):
        """Instant summary from local files; cloud figures show as pending."""
        return {
            "products": self._catalog_count(),
            "customers": self._local_customer_count(),
            "quotes": None,
            "conversion_rate": None,
            "pending_followups": None,
            "recent": None,
        }

    def _kpi_text(self, key, value):
        if value is None:
            return "…"
        try:
            if key == "conversion_rate":
                return f"{float(value):.1f}%"
            return f"{int(value):,}"
        except (TypeError, ValueError):
            return str(value)

    def _products_subtext(self, count):
        return "…" if count is None else f"{count:,} products"

    def _start_summary_load(self, force=False):
        """Fetch dashboard figures on a worker thread, then update the tiles."""
        if self._summary_loading:
            return
        self._summary_loading = True

        def worker():
            try:
                summary = self._load_summary(force=force)
            except Exception as e:
                print(f"[Dashboard] Summary load failed: {e}")
                summary = None
            self._async_queue.put(("summary", summary))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_async_queue(self):
        """Main-thread pump for results coming from worker threads."""
        try:
            while True:
                kind, payload = self._async_queue.get_nowait()
                if kind == "summary":
                    self._summary_loading = False
                    if payload is not None:
                        self._summary_cache = payload
                        self._apply_summary(payload)
                elif kind == "customers":
                    self._apply_customer_count(payload)
        except queue.Empty:
            pass
        except Exception:
            pass
        try:
            self.after(250, self._poll_async_queue)
        except Exception:
            pass

    def _apply_customer_count(self, count):
        if not count:
            return
        card = self._kpi_cards.get("customers")
        if card is not None:
            try:
                card.value_label.configure(text=self._kpi_text("customers", count))
            except Exception:
                pass
        if self._summary_cache is not None:
            self._summary_cache["customers"] = count

    def _apply_summary(self, summary):
        for key, card in self._kpi_cards.items():
            try:
                card.value_label.configure(text=self._kpi_text(key, summary.get(key)))
            except Exception:
                pass
        if self._products_sub_lbl is not None:
            try:
                self._products_sub_lbl.configure(
                    text=self._products_subtext(summary.get("products"))
                )
            except Exception:
                pass
        if self._recent_box is not None:
            try:
                self._render_recent(self._recent_box, summary.get("recent"))
            except Exception:
                pass

    def _render_recent(self, box, recent):
        for child in box.winfo_children():
            child.destroy()

        if recent is None:
            tk.Label(box, text="Loading…", bg=T.BG, fg=T.TEXT_MUTED,
                     font=T.FONT_BODY).pack(anchor="w", pady=10)
            return

        if not recent:
            empty_box = tk.Frame(box, bg=T.SURFACE, highlightbackground=T.BORDER, highlightthickness=1)
            empty_box.pack(fill="both", expand=True)

            tk.Label(empty_box, text="📄", bg=T.SURFACE, fg=T.BORDER, font=("Arial", 48)).pack(pady=(40, 10))
            tk.Label(empty_box, text="No quotations yet", bg=T.SURFACE, fg=T.TEXT, font=T.FONT_H2).pack()
            tk.Label(empty_box, text="Create your first quote to see it here.", bg=T.SURFACE, fg=T.TEXT_BODY, font=T.FONT_BODY).pack(pady=(5, 20))

            btn = tk.Button(empty_box, text="+ Create New Quotation", bg=T.ACCENT, fg="white",
                            font=T.FONT_BODY_B, relief="flat", cursor="hand2", command=self._new_quotation)
            btn.pack(pady=10, ipadx=10, ipady=5)
            return

        for r in recent:
            row = tk.Frame(box, bg=T.SURFACE, highlightbackground=T.BORDER, highlightthickness=1, cursor="hand2")
            row.pack(fill="x", pady=2)

            lbl_num = tk.Label(row, text=r["number"], bg=T.SURFACE, fg=T.TEXT, font=T.FONT_BODY_B)
            lbl_num.pack(side="left", padx=10, pady=6)

            lbl_cust = tk.Label(row, text=r["customer"] or "—", bg=T.SURFACE, fg=T.TEXT_BODY, font=T.FONT_BODY)
            lbl_cust.pack(side="left", padx=10)

            # Make the row clickable (left and right click)
            for w in (row, lbl_num, lbl_cust):
                w.bind("<Button-1>", lambda e, num=r["number"]: self._show_quotation_items(num))
                w.bind("<Button-3>", lambda e, num=r["number"]: self._show_context_menu(e, num))

    def _sync_customers_async(self):
        """Merge sheet customers into the local cache once, off the UI thread."""
        if self._customers_synced:
            return
        self._customers_synced = True

        def worker():
            try:
                from app.services.customer_service import sync_from_cloud
                from app.services.paths import get_active_module
                count = sync_from_cloud(module=get_active_module())
            except Exception as e:
                print(f"[Dashboard] Customer sync failed: {e}")
                return
            self._async_queue.put(("customers", count))

        threading.Thread(target=worker, daemon=True).start()

    def _load_summary(self, force=False):
        """Load summary figures (runs on a worker thread)."""
        from app.services.paths import get_active_module

        # --- 1. CLOUD QUOTATIONS (cached for a few seconds by cloud_sync) ---
        cloud_quotes = []
        try:
            from app.services.quotation_history_service import fetch_quotations_merged
            cloud_quotes = fetch_quotations_merged(
                limit=10000, module=get_active_module(), silent=True, force=force
            ) or []
        except Exception as e:
            print(f"[Dashboard] Cloud load failed: {e}")

        # --- FILTER: ONLY CRYSTAL QUOTES (CRY prefix) ---
        cloud_quotes = [
            q for q in cloud_quotes
            if str(q.get("quotation_number", "")).upper().startswith("CRY")
        ]

        # Merge with the locally saved records so quotations that exist
        # only on this PC (or have not been uploaded yet) stay visible.
        try:
            from app.services.quotation_history_service import (
                local_quotations,
                merge_quotation_records,
            )
            local_quotes = [
                q for q in local_quotations()
                if str(q.get("quotation_number", "")).upper().startswith("CRY")
            ]
            cloud_quotes = merge_quotation_records(local_quotes, cloud_quotes)
        except Exception as e:
            print(f"[Dashboard] Local merge failed: {e}")

        # --- 3. CALCULATE COUNTS ---
        q_count = len(cloud_quotes)
        accepted_count = sum(1 for q in cloud_quotes if str(q.get("status", "")).strip().lower() == "accepted")
        conversion_rate = (accepted_count / q_count * 100) if q_count > 0 else 0.0

        # --- 4. RECENT QUOTATIONS (LAST 5) ---
        recent = []
        try:
            # Sort by date and take last 5
            sorted_quotes = sorted(cloud_quotes, key=lambda x: str(x.get("date", "")), reverse=True)[:5]
            for q in sorted_quotes:
                recent.append({
                    "number": q.get("quotation_number", ""),
                    "customer": q.get("customer_name", ""),
                    "total": q.get("grand_total", 0),
                    "date": q.get("date", ""),
                })
        except Exception:
            pass

        # --- 5. PRODUCTS (cached local parse) & CUSTOMERS (local cache) ---
        p_count = self._catalog_count()
        c_count = self._local_customer_count()

        # --- 6. PENDING FOLLOW-UPS (reuse the quotes we already fetched) ---
        pending_followups = 0
        try:
            from app.services.quotation_history_service import get_pending_followups
            pending_followups = len(get_pending_followups(days_old=3, quotations=cloud_quotes))
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

        def _num(value):
            try:
                return float(str(value).replace(",", "").replace("₹", "").strip() or 0)
            except Exception:
                return 0.0

        # --- LOAD RECORD: local history first, then cloud ---
        try:
            from app.services.cloud_sync import is_quotation_deleted
            if is_quotation_deleted(quotation_number):
                messagebox.showinfo(
                    "Quotation removed",
                    f"{quotation_number} was deleted and is no longer available.",
                    parent=self,
                )
                return
        except Exception:
            pass

        quotation = None
        try:
            from app.services.quotation_history_service import get_quotation
            quotation = get_quotation(quotation_number)
        except Exception as e:
            print(f"Error fetching quotation: {e}")

        if not quotation:
            try:
                from app.services.quotation_history_service import fetch_quotations_merged
                from app.services.paths import get_active_module
                for rec in fetch_quotations_merged(
                    limit=10000, module=get_active_module(), silent=True
                ):
                    if str(rec.get("quotation_number", "")) == str(quotation_number):
                        quotation = rec
                        break
            except Exception as e:
                print(f"Error fetching quotation from cloud: {e}")

        if not quotation:
            messagebox.showinfo(
                "Quotation removed",
                f"{quotation_number} is no longer available.",
                parent=self,
            )
            return

        # --- BUILD LINE ITEMS (base price + discount) ---
        totals = quotation.get("totals") or {}
        grand_total = _num(quotation.get("grand_total")) or _num(totals.get("grand_total"))

        line_items = []
        for it in (quotation.get("items") or []):
            if not isinstance(it, dict):
                continue
            qty = _num(it.get("qty")) or 1.0
            price = _num(it.get("price"))
            discount = _num(it.get("discount"))
            raw_total = it.get("total")
            amount = (
                _num(raw_total) if raw_total not in (None, "")
                else price * qty - discount
            )
            line_items.append({
                "model": str(it.get("model") or ""),
                "qty": qty,
                "price": price,
                "discount": discount,
                "amount": amount,
                "disc_mode": it.get("disc_mode") or "",
                "raw_discount": _num(it.get("raw_discount")),
            })

        if not line_items:
            line_items = self._items_from_generated_docx(quotation)

        if not line_items:
            # Legacy record with no item data: show the GST-exclusive base.
            qty = _num(quotation.get("machine_qty")) or 1.0
            gst_rate = _num(totals.get("gst_rate")) or 18.0
            taxable = grand_total / (1 + gst_rate / 100.0) if grand_total else 0.0
            line_items = [{
                "model": str(quotation.get("model") or ""),
                "qty": qty,
                "price": taxable / qty if qty else 0.0,
                "discount": 0.0,
                "amount": taxable,
            }]

        # Spread packing/transport/GST over the lines so the Total column is
        # GST-inclusive and adds up to the grand total.
        base_total = sum(i["amount"] for i in line_items)
        overhead = max(grand_total - base_total, 0.0)

        popup = tk.Toplevel(self)
        popup.title(f"Quotation {quotation_number}")
        popup.geometry("760x420")
        popup.configure(bg=T.BG)
        popup.transient(self)
        popup.grab_set()

        header = tk.Frame(popup, bg=T.SURFACE)
        header.pack(fill="x")
        tk.Label(header, text=f"Quotation: {quotation_number}", bg=T.SURFACE, fg=T.TEXT, font=("Arial", 14, "bold")).pack(side="left", padx=20, pady=15)
        try:
            from app.services.quotation_number_service import split_revision
            _base, _rev = split_revision(quotation_number)
        except Exception:
            _base, _rev = quotation_number, 0
        if _rev:
            tk.Label(header, text=f"Revision R{_rev} of {_base}", bg=T.SURFACE, fg=T.TEXT_MUTED, font=("Arial", 9, "italic")).pack(side="left", padx=6, pady=15)
        tk.Label(header, text=f"Customer: {quotation.get('customer_name', '—')}", bg=T.SURFACE, fg=T.TEXT_BODY, font=("Arial", 9)).pack(side="right", padx=20, pady=15)

        tk.Frame(popup, bg=T.BORDER, height=1).pack(fill="x")

        table_frame = tk.Frame(popup, bg=T.BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=20)

        cols = ("model", "qty", "price", "discount", "total")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings")
        tree.heading("model", text="Model")
        tree.heading("qty", text="Qty")
        tree.heading("price", text="Price")
        tree.heading("discount", text="Discount")
        tree.heading("total", text="Total (incl. GST)")

        tree.column("model", width=240)
        tree.column("qty", width=55, anchor="center")
        tree.column("price", width=105, anchor="e")
        tree.column("discount", width=100, anchor="e")
        tree.column("total", width=130, anchor="e")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)

        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def _qty_text(qty):
            return int(qty) if float(qty).is_integer() else f"{qty:g}"

        def _discount_text(it):
            if it.get("disc_mode") == "Percentage (%)":
                return f"{it.get('raw_discount') or 0:g}%"
            return f"₹{it['discount']:,.2f}"

        total_discount = 0.0
        for it in line_items:
            share = (it["amount"] / base_total) if base_total else 0.0
            total_with_gst = it["amount"] + overhead * share
            total_discount += it["discount"]
            tree.insert("", "end", values=(
                it["model"],
                _qty_text(it["qty"]),
                f"₹{it['price']:,.2f}",
                _discount_text(it),
                f"₹{total_with_gst:,.2f}",
            ))

        footer = tk.Frame(popup, bg=T.SURFACE)
        footer.pack(fill="x", side="bottom")
        tk.Frame(footer, bg=T.BORDER, height=1).pack(fill="x")

        tk.Label(footer, text=f"Discount: ₹{total_discount:,.2f}", bg=T.SURFACE, fg="#E67E22", font=("Arial", 11, "bold")).pack(side="left", padx=20, pady=15)

        tk.Label(footer, text=f"Grand Total: ₹{grand_total:,.2f}", bg=T.SURFACE, fg=T.ACCENT, font=("Arial", 12, "bold")).pack(side="right", padx=20, pady=15)
        tk.Button(
            footer, text="Revise", bg=T.ACCENT, fg="white", relief="flat",
            command=lambda: (popup.destroy(), self._revise_quotation(quotation_number)),
        ).pack(side="left", padx=10, pady=15)
        tk.Button(footer, text="Close", bg=T.BG, fg=T.TEXT, relief="flat", command=popup.destroy).pack(side="left", padx=20, pady=15)

    def _items_from_generated_docx(self, quotation):
        """Recover line items from the generated .docx for legacy records."""
        import re
        import zipfile

        path = quotation.get("docx_path") or quotation.get("path") or ""
        if not path or not os.path.isfile(path):
            return []

        try:
            with zipfile.ZipFile(path) as z:
                xml = z.read("word/document.xml").decode("utf-8", "ignore")
            tokens = [
                re.sub(r"&amp;", "&", t).strip()
                for t in re.findall(r"<w:t(?: [^>]*)?>(.*?)</w:t>", xml)
            ]
            tokens = [t for t in tokens if t]
            start = tokens.index("Amount") + 1
            end = tokens.index("Sub Total", start)
        except Exception:
            return []

        hsn_positions = [
            i for i, tok in enumerate(tokens[start:end], start)
            if re.fullmatch(r"\d{6,8}", tok)
        ]
        if not hsn_positions:
            return []

        def _num_token(tok):
            try:
                return float(tok.replace(",", ""))
            except Exception:
                return 0.0

        items = []
        desc_start = start
        for idx, h in enumerate(hsn_positions):
            segment_end = hsn_positions[idx + 1] if idx + 1 < len(hsn_positions) else end
            segment = tokens[h + 1:segment_end]

            model = str(quotation.get("model") or "")
            match = re.search(r"Model:\s*(.+)", " ".join(tokens[desc_start:h]))
            if match:
                model = match.group(1).strip()

            qty = _num_token(segment[1]) if len(segment) > 1 else 1.0
            qty = qty or 1.0

            unit_at = None
            for j, tok in enumerate(segment[2:], 2):
                if re.fullmatch(r"[A-Za-z./-]{1,10}", tok):
                    unit_at = j
                    break

            money = []
            if unit_at is not None:
                for j, tok in enumerate(segment[unit_at + 1:], unit_at + 1):
                    if re.fullmatch(r"[\d,]+\.\d{2}", tok):
                        money.append((j, _num_token(tok)))
            if len(money) < 2:
                return []

            price = money[0][1]
            amount = money[-1][1]
            discount = 0.0
            disc_mode = ""
            raw_discount = 0.0
            if len(money) >= 3 and 0 <= money[1][1] <= 100:
                raw_discount = money[1][1]
                disc_mode = "Percentage (%)"
                discount = price * qty * raw_discount / 100.0

            items.append({
                "model": model,
                "qty": qty,
                "price": price,
                "discount": discount,
                "amount": amount,
                "disc_mode": disc_mode,
                "raw_discount": raw_discount,
            })
            desc_start = h + 1 + money[-1][0] + 1

        return items

    def _refresh_dashboard(self):
        """Reload the dashboard figures without blocking the UI."""
        self._start_summary_load(force=True)

    def _auto_refresh(self):
        """Refresh the figures every 60 seconds (background, no UI freeze)."""
        try:
            self._start_summary_load(force=False)
        except Exception:
            pass
        try:
            self.after(60000, self._auto_refresh)
        except Exception:
            pass

    # ═════════════════════════════════════════════════════════
    # RIGHT CLICK & REVISE
    # ═════════════════════════════════════════════════════════

    def _show_context_menu(self, event, q_no):
        """Right-click menu for Crystal Dashboard."""
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✎ Revise Quotation", command=lambda: self._revise_quotation(q_no))
        menu.add_separator()
        menu.add_command(label="Mark as Sent", command=lambda: self._update_quote_status(q_no, "Sent"))
        menu.add_command(label="Mark as Accepted", command=lambda: self._update_quote_status(q_no, "Accepted"))
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _revise_quotation(self, q_no):
        """Open the form pre-filled from a saved quotation, linked as a revision."""
        try:
            from app.services.quotation_history_service import (
                get_quotation,
                local_quotations,
            )
            from app.services.quotation_number_service import next_revision_number

            record = get_quotation(q_no)

            all_records = []
            try:
                from app.services.quotation_history_service import fetch_quotations_merged
                from app.services.paths import get_active_module
                all_records = fetch_quotations_merged(
                    limit=10000, module=get_active_module(), silent=True
                ) or []
            except Exception as e:
                print(f"[revise] cloud fetch failed: {e}")

            if not record:
                record = next(
                    (
                        r for r in all_records
                        if str(r.get("quotation_number", "")) == str(q_no)
                    ),
                    None,
                )

            if not record:
                messagebox.showerror("Error", f"Could not find data for {q_no}", parent=self)
                return

            # Local records carry the cart lines; fill anything the cloud copy lacks.
            local = get_quotation(q_no)
            if local and local is not record:
                for key, value in local.items():
                    if value and not record.get(key):
                        record[key] = value

            # Legacy records predate stored line items — recover them from
            # the generated Word file when it is available.
            if not record.get("items"):
                try:
                    record["items"] = self._items_from_generated_docx(record)
                except Exception:
                    record["items"] = []

            numbers = [r.get("quotation_number", "") for r in all_records]
            numbers += [r.get("quotation_number", "") for r in local_quotations()]
            revision_number = next_revision_number(q_no, numbers)

            from ui.crystal.quotation_form import QuotationForm
            QuotationForm(self, self, prefill=record, revision_number=revision_number)

        except Exception as e:
            messagebox.showerror("Error", f"Could not open revise form: {e}", parent=self)

    def _update_quote_status(self, q_no, new_status):
        """Update status in Supabase and Google Sheets."""
        try:
            from app.services.cloud_sync import update_quotation_status_in_cloud

            ok = update_quotation_status_in_cloud(q_no, new_status)

            if hasattr(self, '_refresh_dashboard'):
                self._refresh_dashboard()

            if ok:
                messagebox.showinfo("Status Updated", f"Quotation {q_no} is now {new_status}.", parent=self)
            else:
                messagebox.showwarning(
                    "Status Not Saved",
                    f"{q_no} was updated locally, but the cloud row could not be changed.\n"
                    "Redeploy tools/apps_script_cloud_sync.gs to enable it.",
                    parent=self,
                )

        except Exception as e:
            messagebox.showerror("Error", f"Could not update status: {e}", parent=self)

    # ═════════════════════════════════════════════════════════
    # FOLLOW-UPS & SEARCH
    # ═════════════════════════════════════════════════════════

    def _show_pending_followups(self):
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
        
        btn_frame = tk.Frame(popup, bg=T.BG)
        btn_frame.pack(fill="x", pady=10)
        
        def open_selected():
            sel = tree.selection()
            if not sel:
                return
            values = tree.item(sel[0], "values")
            quot_no = values[0]
            popup.destroy()
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

    # ═════════════════════════════════════════════════════
    # NAV HANDLERS
    # ═════════════════════════════════════════════════════

    def _on_nav(self, key):
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

    def _go_home(self):
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