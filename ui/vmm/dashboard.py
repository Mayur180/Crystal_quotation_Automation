# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# QUOTATION MANAGEMENT SYSTEM
#
# Dashboard — main application window
#
# File:
#   ui/dashboard.py
#
# Purpose:
#   Central entry point. User launches the app here.
#   From here they open:
#     • New Quotation      → QuotationForm
#     • Quotation History  → QuotationHistory
#     • Customers          → CustomerDatabase
#     • Products           → ProductManager
#     • Company Settings   → CompanySettings
#     • Backup / Export    → BackupExport
# ============================================================

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

get_current_user = None



# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# DASHBOARD HELPERS — config-driven tiles (Phase R-A)
# ============================================================

def _safe_summary() -> dict:
    """
    Return live counts for the current module. Never raises.
    Missing services → 0, so the dashboard always renders.
    """
    out = {
        "product_count":   0,
        "accessory_count": 0,
        "customer_count":  0,
        "quotation_count": 0,
    }

    # Products + accessories (catalog service)
    try:
        from app.services.catalog_service import get_catalog_summary
        s = get_catalog_summary() or {}
        out["product_count"]   = int(s.get("product_count", 0))
        out["accessory_count"] = int(s.get("accessory_count", 0))
    except Exception:
        pass

    # Customers
    try:
        from app.services.customer_service import get_customers
        out["customer_count"] = len(get_customers() or [])
    except Exception:
        pass

    # Quotations
    try:
        from app.services.quotation_history_service import load_quotations
        out["quotation_count"] = len(load_quotations() or [])
    except Exception:
        pass

    return out


def _resolve_subtitle(tile: dict, summary: dict) -> str:
    """Fill '{n}' in tile['sub'] with a live count (comma-formatted)."""
    sub = tile.get("sub", "") or ""
    ck  = tile.get("count_key")
    if ck and "{n}" in sub:
        n = int(summary.get(ck, 0))
        sub = sub.replace("{n}", f"{n:,}")
    return sub

# ============================================================
# MAIN WINDOW
# ============================================================

class Dashboard(tk.Tk):

    # --------------------------------------------------------
    # PALETTE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # INIT
    # --------------------------------------------------------

    def __init__(self):

        super().__init__()

        # v4: dynamic title based on active module
        try:
            from app.services import paths as _paths
            _mod = _paths.get_active_module()
        except Exception:
            _mod = "VMM"
        self._active_module = _mod
        self.title(
            f"CRYSTAL | ARMATECH ASSOCIATES — {_mod} Quotation Manager  v4.0"
        )
        # Set Crystal logo as window icon
        try:
            from ui.common.ui_helpers import set_window_icon
            set_window_icon(self)
        except Exception:
            pass

        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.configure(bg=self.BG)

        # First-run: ask user for output folder
        self._check_first_run_output_folder()

        self.recent_tree = None
        self.recent_placeholder = None

        self._configure_style()
        self._build_interface()

        self._reload_recent()

        # ---- Keyboard shortcuts (Phase: keyboard nav) ----
        try:
            from ui.common.ui_helpers import (
                install_table_shortcuts,
                install_modal_shortcuts,
            )
            install_table_shortcuts(
                self.recent_tree,
                on_enter=self._on_recent_double_click,
            )
            install_modal_shortcuts(self, on_escape=self._quit)
        except Exception:
            pass

        # ---- Global app shortcuts ----
        self._install_app_shortcuts()

    # --------------------------------------------------------
    # STYLE
    # --------------------------------------------------------

    def _check_first_run_output_folder(self):
        """On first run, ask the user where to save quotations."""
        try:
            from app.services.settings_service import (
                is_confirmed,
                mark_confirmed,
                set_output_folder,
                default_output_folder,
            )
        except Exception:
            return

        if is_confirmed():
            return

        from tkinter import filedialog, messagebox

        default = str(default_output_folder())

        msg1 = (
            "Welcome to Crystal Quotation!\n\n"
            "Please choose a folder where your quotations will be saved.\n\n"
            "Structure:\n"
            "  <chosen_folder>/<DD-MM-YYYY>/word/*.docx\n"
            "  <chosen_folder>/<DD-MM-YYYY>/pdf/*.pdf\n\n"
            "You can change this later in Company Settings."
        )
        messagebox.showinfo("Crystal Quotation", msg1, parent=self)

        chosen = filedialog.askdirectory(
            title="Choose folder for your quotations",
            initialdir=default,
            parent=self,
        )

        if not chosen:
            chosen = default

        try:
            set_output_folder(chosen)
            mark_confirmed()
            mark_confirmed()
        except Exception:
            pass

    def _configure_style(self):

        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Dashboard.Treeview",
            background="white",
            fieldbackground="white",
            foreground=self.TEXT,
            borderwidth=1,
            relief="solid",
            rowheight=28,
            font=("Arial", 9),
        )

        style.configure(
            "Dashboard.Treeview.Heading",
            background=self.SOFT,
            foreground=self.TEXT,
            font=("Arial", 9, "bold"),
            relief="flat",
        )

        style.map(
            "Dashboard.Treeview",
            background=[("selected", self.RED_LIGHT)],
            foreground=[("selected", self.TEXT)],
        )

    # --------------------------------------------------------
    # INTERFACE
    # --------------------------------------------------------

    def _build_interface(self):

        self._build_header()

        # ---- main shell: sidebar (left) + content (right) ----
        shell = tk.Frame(self, bg=self.BG)
        shell.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = tk.Frame(
            shell, bg=self.CARD, width=220,
            highlightbackground=self.BORDER, highlightthickness=0,
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        # Right border on sidebar
        tk.Frame(shell, bg=self.BORDER, width=1).pack(
            side="left", fill="y"
        )

        # Content
        self._content = tk.Frame(shell, bg=self.BG)
        self._content.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_dashboard_counters()
        self._build_recent_section()
        self._build_footer()

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    def _build_header(self):

        header = tk.Frame(self, bg=self.CARD, height=92)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=self.CARD)
        brand.pack(side="left", padx=34)

        tk.Label(
            brand, text="CRYSTAL", bg=self.CARD, fg=self.RED,
            font=("Arial", 26, "bold"),
        ).pack(side="left", pady=22)

        tk.Label(
            brand, text="  /  Quotation Manager", bg=self.CARD,
            fg=self.MUTED, font=("Arial", 11),
        ).pack(side="left", pady=26)

        # v4: module badge
        # v4 C1: theme-driven badge color
        try:
            from ui.themes import get_badge_colors, get_logo_text, get_tiles
            _mod = getattr(self, "_active_module", "VMM")
            _badge_bg, _badge_fg = get_badge_colors(_mod)
        except Exception:
            _badge_bg = self.RED
            _badge_fg = "white"
        tk.Label(
            brand, text=f" {_mod} ",
            bg=_badge_bg, fg=_badge_fg,
            font=("Arial", 9, "bold"),
        ).pack(side="left", pady=26, padx=(10, 0))

        company = tk.Frame(header, bg=self.CARD)
        company.pack(side="right", padx=34)

        tk.Label(
            company, text="ARMATECH ASSOCIATES", bg=self.CARD,
            fg=self.TEXT, font=("Arial", 12, "bold"),
        ).pack(anchor="e", pady=(18, 1))

        # v4 C1: theme-driven tagline
        try:
            from ui.themes import get_tagline
            _tagline = get_tagline(getattr(self, "_active_module", "VMM"))
        except Exception:
            _tagline = "Precision Measurement Technology"
        tk.Label(
            company, text=_tagline,
            bg=self.CARD, fg=self.MUTED, font=("Arial", 9),
        ).pack(anchor="e")

        _row = tk.Frame(company, bg=self.CARD)
        _row.pack(anchor="e", pady=(2, 0))

        tk.Label(
            _row,
            text=f"Today:  {date.today().strftime('%d %b %Y')}",
            bg=self.CARD, fg=self.LIGHT_MUTED, font=("Arial", 8),
        ).pack(side="left")

        # v4: Logout link
        def _do_logout(self=self):
            from tkinter import messagebox
            if not messagebox.askyesno(
                "Switch Module",
                "Return to login screen?\n\n"
                "You will need to log in again to switch modules."
            ):
                return
            try:
                self.destroy()
            except Exception:
                pass
            try:
                import main as _main
                _main.main()
            except Exception as e:
                from tkinter import messagebox as _mb
                _mb.showerror("Restart Failed", f"Could not restart app:\n{e}")

        tk.Label(
            _row, text="  •  ",
            bg=self.CARD, fg=self.LIGHT_MUTED, font=("Arial", 8),
        ).pack(side="left")

        tk.Label(
            _row, text="Logout",
            bg=self.CARD, fg=self.RED, cursor="hand2",
            font=("Arial", 8, "underline"),
        ).pack(side="left")
        # Bind click on logout label
        _row.winfo_children()[-1].bind("<Button-1>", lambda e: _do_logout())

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    def _mark_active(self, item):
        """Give the given nav item an active look (red left bar + light bg)."""
        try:
            for child in item.winfo_children():
                child.configure(bg=self.RED_LIGHT)
                for sub in child.winfo_children():
                    try:
                        sub.configure(bg=self.RED_LIGHT)
                    except Exception:
                        pass
            item.configure(bg=self.RED_LIGHT)
        except Exception:
            pass

    def _build_sidebar(self):

        # Phase R-A step 5c: import theme helpers right here so this
        # method works even if the top-of-file import was edited away.
        from ui.themes import get_tiles, get_logo_text  # noqa: F401

        # top spacer so first nav item isn't glued to the header
        tk.Frame(self._sidebar, bg=self.CARD, height=14).pack(fill="x")

        # ---- nav items ----
        self._nav_items = []
        self._active_nav = None

        def add_item(icon, label, command, danger=False):
            item = tk.Frame(
                self._sidebar, bg=self.CARD, cursor="hand2",
            )
            item.pack(fill="x", padx=8, pady=1)

            inner = tk.Frame(item, bg=self.CARD)
            inner.pack(fill="x", padx=10, pady=8)

            icon_lbl = tk.Label(
                inner, text=icon, bg=self.CARD,
                fg=self.RED if danger else self.TEXT,
                font=("Segoe UI Emoji", 12), width=2, anchor="w",
            )
            icon_lbl.pack(side="left")

            text_lbl = tk.Label(
                inner, text=label, bg=self.CARD,
                fg=self.RED if danger else self.TEXT,
                font=("Arial", 10), anchor="w",
            )
            text_lbl.pack(side="left", padx=(4, 0))

            widgets = (item, inner, icon_lbl, text_lbl)

            def _click(_e, cmd=command):
                cmd()

            def _enter(_e, w=widgets, d=danger):
                bg = self.RED_LIGHT if d else self.SOFT
                for x in w:
                    x.configure(bg=bg)

            def _leave(_e, w=widgets, d=danger):
                for x in w:
                    x.configure(bg=self.CARD)

            for w in widgets:
                w.bind("<Button-1>", _click)
                w.bind("<Enter>", _enter)
                w.bind("<Leave>", _leave)

            self._nav_items.append(item)
            return item

        self._home_item = add_item("🏠", "Home", lambda: None)

        # ---- config-driven nav (Phase R-A step 5c) ----
        # Dispatch map: action name → bound method. Anything missing
        # from dispatch is silently skipped, so the dashboard never crashes
        # on a tile whose handler hasn't been written yet.
        dispatch = {
            "quotation_form":       getattr(self, "_open_new_quotation",     None),
            "quotation_history":    getattr(self, "_open_history",           None),
            "activity_log":         getattr(self, "_open_activity_log",      None),
            "monthly_report":       getattr(self, "_open_monthly_report",    None),
            "customer_database":    getattr(self, "_open_customer_database", None),
            "product_manager":      getattr(self, "_open_product_manager",   None),
            "accessories_manager":  getattr(self, "_open_accessories_manager", None),
            "quotations_browser":   getattr(self, "_open_quotations_browser", None),
            "company_settings":     getattr(self, "_open_company_settings",  None),
            "backup_export":        getattr(self, "_open_backup_export",     None),
        }

        try:
            active_module = self._active_module
        except AttributeError:
            # Fall back to paths.get_active_module()
            try:
                from app.services.paths import get_active_module
                active_module = get_active_module()
            except Exception:
                active_module = "VMM"

        current_group = None
        separator_emitted = False

        for tile in get_tiles(active_module):
            group = tile.get("group", "primary")

            # Insert separator once, at the primary→secondary boundary
            if current_group == "primary" and group == "secondary" \
                    and not separator_emitted:
                tk.Frame(self._sidebar, bg=self.BORDER, height=1).pack(
                    fill="x", padx=14, pady=(10, 8),
                )
                separator_emitted = True

            current_group = group

            action = tile.get("action", "")
            cmd    = dispatch.get(action)
            if cmd is None:
                # No handler yet — skip cleanly (e.g. accessories_manager
                # before R-B ships)
                continue

            add_item(tile.get("icon", "•"), tile.get("label", action), cmd)

        # mark Home as the active item (red left bar + light bg)
        try:
            self._mark_active(self._home_item)
        except Exception:
            pass

        # ---- spacer + Quit at bottom ----
        spacer = tk.Frame(self._sidebar, bg=self.CARD)
        spacer.pack(fill="both", expand=True)

        tk.Frame(self._sidebar, bg=self.BORDER, height=1).pack(
            fill="x", padx=14, pady=(8, 4),
        )

        # ---- signed-in user label ----
        try:
            user = get_current_user() if get_current_user else None
        except Exception:
            user = None
        if user:
            user_lbl = tk.Label(
                self._sidebar,
                text=f"Signed in as: {user}",
                bg=self.CARD, fg=self.MUTED,
                font=("Arial", 8, "italic"),
                anchor="w",
            )
            user_lbl.pack(fill="x", padx=18, pady=(4, 4))

        add_item("🗑",  "Clear Activity Log", self._clear_activity_log,
                 danger=True)
        add_item("🚪", "Quit",               self._quit, danger=True)

    def _make_tile(self, parent, *, title, subtitle, command, primary=False):

        enabled = command is not None

        if primary:
            bg = self.RED
            fg = "white"
            sub_fg = "#FFE0E0"
            hover = self.RED_DARK
        elif enabled:
            bg = self.CARD
            fg = self.TEXT
            sub_fg = self.MUTED
            hover = self.SOFT
        else:
            bg = self.SOFT
            fg = self.LIGHT_MUTED
            sub_fg = self.LIGHT_MUTED
            hover = self.SOFT

        outer = tk.Frame(
            parent, bg=bg,
            highlightbackground=self.BORDER,
            highlightthickness=0 if primary else 1,
        )
        outer.pack(side="left", fill="both", expand=True, padx=(0, 10))

        inner = tk.Frame(outer, bg=bg, cursor="hand2" if enabled else "arrow")
        inner.pack(fill="both", expand=True, padx=18, pady=16)

        title_lbl = tk.Label(
            inner, text=title, bg=bg, fg=fg,
            font=("Arial", 12, "bold"), anchor="w",
            cursor="hand2" if enabled else "arrow",
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            inner, text=subtitle, bg=bg, fg=sub_fg,
            font=("Arial", 9), anchor="w",
            cursor="hand2" if enabled else "arrow",
        )
        sub_lbl.pack(anchor="w", pady=(2, 0))

        if enabled:

            def on_click(_e):
                command()

            for widget in (outer, inner, title_lbl, sub_lbl):
                widget.bind("<Button-1>", on_click)

            def on_enter(_e):
                for w in (outer, inner):
                    w.configure(bg=hover)

            def on_leave(_e):
                for w in (outer, inner):
                    w.configure(bg=bg)

            for widget in (outer, inner, title_lbl, sub_lbl):
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)

    # --------------------------------------------------------
    # DASHBOARD COUNTERS
    # --------------------------------------------------------

    def _build_dashboard_counters(self):
        """Show live quotation summary counters from quotation history."""
        section = tk.Frame(self._content, bg=self.BG)
        section.pack(fill="x", padx=34, pady=(8, 4))

        tk.Label(
            section,
            text="OVERVIEW",
            bg=self.BG,
            fg=self.MUTED,
            font=("Arial", 8, "bold"),
        ).pack(anchor="w", pady=(0, 8))

        cards = tk.Frame(section, bg=self.BG)
        cards.pack(fill="x")

        self.counter_labels = {}

        counter_defs = [
            ("total", "Total Quotations", "0"),
            ("month", "This Month", "0"),
            ("value", "Total Quotation Value", "₹ 0.00"),
            ("average", "Average Quotation Value", "₹ 0.00"),
        ]

        for index, (key, title, value) in enumerate(counter_defs):
            card = tk.Frame(
                cards,
                bg=self.CARD,
                highlightbackground=self.BORDER,
                highlightthickness=1,
            )
            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=(0 if index == 0 else 6, 6 if index < 3 else 0),
            )

            inner = tk.Frame(card, bg=self.CARD)
            inner.pack(fill="both", expand=True, padx=16, pady=11)

            tk.Label(
                inner,
                text=title,
                bg=self.CARD,
                fg=self.MUTED,
                font=("Arial", 8, "bold"),
            ).pack(anchor="w")

            value_label = tk.Label(
                inner,
                text=value,
                bg=self.CARD,
                fg=self.TEXT if key != "value" else self.RED,
                font=("Arial", 17, "bold"),
            )
            value_label.pack(anchor="w", pady=(4, 0))

            self.counter_labels[key] = value_label

        self._reload_counters()

    def _reload_counters(self):
        """Refresh dashboard counters without changing quotation records."""
        try:
            from app.services.quotation_history_service import list_quotations

            records = list_quotations(limit=100000)
            if records is None:
                records = []
        except Exception:
            records = []

        total_count = len(records)
        month_count = 0
        total_value = 0.0

        current_month = date.today().strftime("%m")
        current_year = date.today().strftime("%Y")

        for record in records:
            try:
                raw_total = record.get("grand_total", 0)
                total_value += float(str(raw_total).replace(",", "").replace("₹", "").strip() or 0)
            except Exception:
                pass

            raw_date = str(record.get("date", "")).strip()

            # History currently stores dates as text. Support the common
            # formats used by the quotation system without changing them.
            parsed_date = None
            for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y"):
                try:
                    from datetime import datetime
                    parsed_date = datetime.strptime(raw_date, fmt)
                    break
                except ValueError:
                    continue

            if parsed_date and (
                parsed_date.strftime("%m") == current_month
                and parsed_date.strftime("%Y") == current_year
            ):
                month_count += 1

        average_value = (
            total_value / total_count
            if total_count
            else 0.0
        )

        if hasattr(self, "counter_labels"):
            self.counter_labels["total"].configure(text=f"{total_count:,}")
            self.counter_labels["month"].configure(text=f"{month_count:,}")
            self.counter_labels["value"].configure(
                text=f"₹ {total_value:,.2f}"
            )
            self.counter_labels["average"].configure(
                text=f"₹ {average_value:,.2f}"
            )

    # --------------------------------------------------------
    # RECENT QUOTATIONS SECTION
    # --------------------------------------------------------

    def _build_recent_section(self):

        section = tk.Frame(self._content, bg=self.BG)
        section.pack(fill="both", expand=True, padx=34, pady=(18, 10))

        title_row = tk.Frame(section, bg=self.BG)
        title_row.pack(fill="x", pady=(0, 8))

        tk.Label(
            title_row, text="RECENT QUOTATIONS", bg=self.BG,
            fg=self.MUTED, font=("Arial", 8, "bold"),
        ).pack(side="left")

        tk.Button(
            title_row, text="↺  Refresh",
            command=self._reload_recent,
            bg=self.BG, fg=self.MUTED,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            padx=8, pady=2,
        ).pack(side="right")

        tk.Label(
            title_row,
            text="Double-click a row to open Word",
            bg=self.BG, fg=self.LIGHT_MUTED,
            font=("Arial", 8, "italic"),
        ).pack(side="right", padx=(0, 12))

        card = tk.Frame(
            section, bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True)

        columns = ("offer_no", "date", "customer", "company", "model", "total")

        self.recent_tree = ttk.Treeview(
            card, columns=columns, show="headings",
            style="Dashboard.Treeview", height=12,
        )

        headings = {
            "offer_no": "Offer No.",
            "date": "Date",
            "customer": "Customer",
            "company": "Company",
            "model": "Model",
            "total": "Grand Total",
        }

        widths = {
            "offer_no": 160,
            "date": 110,
            "customer": 180,
            "company": 220,
            "model": 120,
            "total": 140,
        }

        for col in columns:
            self.recent_tree.heading(col, text=headings[col])
            self.recent_tree.column(
                col, width=widths[col],
                anchor="w" if col != "total" else "e",
                stretch=(col in ("customer", "company")),
            )

        self.recent_tree.pack(fill="both", expand=True, padx=14, pady=14)

        self.recent_tree.bind("<Double-1>", self._on_recent_double_click)

        # Set focus so keyboard nav works right away
        try:
            self.recent_tree.focus_set()
        except Exception:
            pass

        self.recent_placeholder = tk.Label(
            card,
            text="No quotations yet — click “New Quotation” to get started.",
            bg=self.CARD, fg=self.LIGHT_MUTED,
            font=("Arial", 9, "italic"),
        )
        self.recent_placeholder.place(relx=0.5, rely=0.5, anchor="center")

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    def _build_footer(self):

        footer = tk.Frame(
            self, bg=self.CARD, height=44,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        tk.Label(
            footer,
            text="CRYSTAL / ARMATECH ASSOCIATES  ·  Quotation Manager  ·  v4.0",
            bg=self.CARD, fg=self.MUTED, font=("Arial", 8),
        ).pack(side="left", padx=24)

        tk.Button(
            footer, text="Quit", command=self._quit,
            bg="white", fg=self.MUTED,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right", padx=20, pady=6)

    # --------------------------------------------------------
    # RECENT QUOTATIONS — DATA LOADING
    # --------------------------------------------------------

    def _reload_recent(self):

        if self.recent_tree is None:
            return

        for row in self.recent_tree.get_children():
            self.recent_tree.delete(row)

        try:
            from app.services.quotation_history_service import list_quotations
            records = list_quotations(limit=20)
        except Exception:
            records = []

        if records:
            if self.recent_placeholder is not None:
                try:
                    self.recent_placeholder.destroy()
                except Exception:
                    pass
                self.recent_placeholder = None
        else:
            if self.recent_placeholder is None:
                try:
                    card = self.recent_tree.master
                    self.recent_placeholder = tk.Label(
                        card,
                        text="No quotations yet — click “New Quotation” to get started.",
                        bg=self.CARD, fg=self.LIGHT_MUTED,
                        font=("Arial", 9, "italic"),
                    )
                    self.recent_placeholder.place(
                        relx=0.5, rely=0.5, anchor="center"
                    )
                except Exception:
                    pass

        self._reload_counters()

        for r in records:

            total = r.get("grand_total", "0.00")
            try:
                from decimal import Decimal
                total_str = f"₹ {Decimal(str(total)):,.2f}"
            except Exception:
                total_str = "₹ 0.00"

            self.recent_tree.insert(
                "", "end",
                values=(
                    r.get("quotation_number", "—"),
                    r.get("date", "—"),
                    r.get("customer_name", "—"),
                    r.get("customer_company", ""),
                    r.get("model", "—"),
                    total_str,
                ),
            )

    def _on_recent_double_click(self, _event=None):

        sel = self.recent_tree.selection()
        if not sel:
            return

        values = self.recent_tree.item(sel[0], "values")
        if not values:
            return

        offer_no = values[0]

        try:
            from app.services.quotation_history_service import get_quotation
            record = get_quotation(offer_no)
        except Exception:
            record = None

        if not record:
            messagebox.showinfo(
                "Not found",
                f"Quotation {offer_no} could not be found.",
                parent=self,
            )
            return

        docx_path = record.get("docx_path")

        if docx_path and os.path.isfile(docx_path):
            try:
                if sys.platform.startswith("win"):
                    os.startfile(docx_path)   # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    import subprocess
                    subprocess.Popen(["open", docx_path])
                else:
                    import subprocess
                    subprocess.Popen(["xdg-open", docx_path])
            except Exception as exc:
                messagebox.showerror(
                    "Cannot open file",
                    f"{type(exc).__name__}: {exc}",
                    parent=self,
                )
        else:
            messagebox.showinfo(
                "File missing",
                "The Word file for this quotation is no longer on disk.",
                parent=self,
            )

    # --------------------------------------------------------
    # ACTIONS
    # --------------------------------------------------------

    def _open_new_quotation(self):

        try:
            from ui.vmm.quotation_form import QuotationForm
        except Exception as exc:
            messagebox.showerror(
                "Could not open quotation form",
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        QuotationForm(self, self)

        try:
            self.after(500, self._reload_recent)
        except Exception:
            pass

    def _open_backup_export(self):

        try:
            from ui.vmm.backup_export import BackupExport
        except Exception as exc:
            messagebox.showerror(
                "Could not open backup / export",
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        BackupExport(self)

    def _open_product_manager(self):

        try:
            from ui.vmm.product_manager import ProductManager
        except Exception as exc:
            messagebox.showerror(
                "Could not open product manager",
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        ProductManager(self)

    def _open_quotations_browser(self):

        try:
            from ui.vmm.quotations_browser import QuotationsBrowser
        except Exception as exc:
            messagebox.showerror(
                "Could not open quotations browser",
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        QuotationsBrowser(self)

    def _open_customer_database(self):

        try:
            from ui.vmm.customer_database import CustomerDatabase
        except Exception as exc:
            messagebox.showerror(
                "Could not open customer database",
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        CustomerDatabase(self)

    def _open_company_settings(self):

        try:
            from ui.vmm.company_settings import CompanySettings
        except Exception as exc:
            messagebox.showerror(
                "Could not open company settings",
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        CompanySettings(self)

    def _open_history(self):

        try:
            from ui.vmm.quotation_history import QuotationHistory
        except Exception as exc:
            messagebox.showerror(
                "Could not open history",
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        QuotationHistory(self)

        try:
            self.after(500, self._reload_recent)
        except Exception:
            pass

    def _open_activity_log(self):

        try:
            from ui.vmm.activity_log_window import ActivityLog
        except Exception as exc:
            messagebox.showerror(
                "Could not open activity log",
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        ActivityLog(self)

    def _open_monthly_report(self):

        try:
            from ui.vmm.monthly_report_window import MonthlyReport
        except Exception as exc:
            messagebox.showerror(
                "Could not open monthly report",
                f"{type(exc).__name__}: {exc}",
                parent=self,
            )
            return

        MonthlyReport(self)

    def _install_app_shortcuts(self):
        """Bind global keyboard shortcuts to the dashboard root."""

        bindings = [
            ("<Control-n>",       self._open_new_quotation),
            ("<Control-h>",       self._open_history),
            ("<Control-r>",       self._open_monthly_report),
            ("<Control-l>",       self._open_activity_log),
            ("<Control-Shift-C>", self._open_customer_database),
            ("<Control-Shift-P>", self._open_product_manager),
            ("<Control-Shift-S>", self._open_company_settings),
            ("<Control-Shift-B>", self._open_backup_export),
            ("<Control-q>",       self._quit),
        ]

        for seq, fn in bindings:
            try:
                self.bind_all(seq, lambda _e, f=fn: f())
            except Exception:
                pass

    def _clear_activity_log(self):
        """Wipe the activity log after confirmation."""

        try:
            from app.services.activity_log_service import (
                clear_log,
                count as log_count,
            )
        except Exception as exc:
            messagebox.showerror(
                "Clear Activity Log",
                f"Service unavailable:\n{exc}",
                parent=self,
            )
            return

        try:
            n = int(log_count())
        except Exception:
            n = 0

        if n == 0:
            messagebox.showinfo(
                "Clear Activity Log",
                "Activity log is already empty.",
                parent=self,
            )
            return

        confirmed = messagebox.askyesno(
            "Clear Activity Log",
            f"Delete all {n} activity log entries?\n\n"
            "This cannot be undone.",
            parent=self,
        )

        if not confirmed:
            return

        try:
            ok = clear_log()
        except Exception as exc:
            messagebox.showerror(
                "Clear Activity Log",
                f"Could not clear log:\n{exc}",
                parent=self,
            )
            return

        if ok:
            messagebox.showinfo(
                "Clear Activity Log",
                f"Cleared {n} entries.",
                parent=self,
            )
        else:
            messagebox.showerror(
                "Clear Activity Log",
                "Could not clear the activity log.",
                parent=self,
            )

    def _quit(self):

        self.destroy()


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    app = Dashboard()
    app.mainloop()