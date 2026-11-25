# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# PRODUCT / PRICE MANAGER
#
# Modal window — Products catalog.
#
# File:
#   ui/product_manager.py
# ============================================================

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from decimal import Decimal, InvalidOperation

from ui.crystal import theme as T
from ui.crystal import widgets as W


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:
    from app.services.catalog_admin_service import (
        load_catalog,
        update_product,
        bulk_adjust_product_prices,
        list_backups,
        restore_backup,
    )
except Exception:
    load_catalog = None
    update_product = None
    bulk_adjust_product_prices = None
    list_backups = None
    restore_backup = None


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
        return f"₹ {Decimal(str(value)):,.0f}"
    except (InvalidOperation, ValueError, TypeError):
        return "₹ 0"


def _short_name(value, limit=64):
    text = str(value or "").strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def _friendly_ts(value):
    text = str(value or "").strip()
    for fmt, size in (("%Y-%m-%dT%H:%M:%S", 19),
                      ("%Y-%m-%d %H:%M:%S", 19),
                      ("%Y-%m-%dT%H:%M:%S.%f", 26)):
        try:
            return datetime.strptime(text[:size], fmt).strftime("%d-%m-%Y %H:%M")
        except ValueError:
            continue
    return text or "—"


# ============================================================
# PRODUCT EDIT DIALOG
# ============================================================

class ProductEditDialog(tk.Toplevel):

    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_DARK = "#980000"
    SOFT = "#F8F9FA"

    FIELDS = [
        ("model", "Model", False, True),
        ("category", "Category", False, True),
        ("product_name", "Product Name", False, False),
        ("status", "Status (active/inactive)", False, False),
        ("price", "Price (INR)", False, False),
        ("measuring_range", "Measuring Range", False, False),
        ("dimension", "Dimension", False, False),
        ("accuracy", "Accuracy", False, False),
        ("repeatability", "Repeatability", False, False),
        ("weight", "Weight", False, False),
        ("ccd", "CCD", False, False),
        ("lens", "Lens", False, False),
        ("magnification", "Magnification", False, False),
        ("fov", "FOV", False, False),
        ("working_distance", "Working Distance", False, False),
        ("linear_scale_resolution", "Linear Scale Resolution", False, False),
        ("driving_system", "Driving System", True, False),
        ("controller", "Controller", False, False),
        ("guidance_mode", "Guidance Mode", True, False),
        ("software", "Software", True, False),
        ("illumination", "Illumination", True, False),
    ]

    def __init__(self, parent, product):
        super().__init__(parent)

        self.result = None
        self.product = product or {}
        self.original_model = self.product.get("model", "")

        self.title(f"Edit Product — {self.original_model}")
        self.geometry("720x740")
        self.minsize(640, 600)
        self.configure(bg=self.BG)
        self.transient(parent)
        self.grab_set()

        self.vars = {}
        self._build_interface()

        self.protocol("WM_DELETE_WINDOW", self._cancel)

        # ---- Keyboard shortcuts ----
        try:
            from ui.common.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(
                self,
                on_escape=self._cancel,
                on_enter=self._save,
            )
        except Exception:
            pass

    def _build_interface(self):

        header = tk.Frame(self, bg=self.CARD, height=68)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header,
                 text=f"Edit Product — {self.original_model}",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 14, "bold")).pack(anchor="w", padx=22,
                                                  pady=(18, 0))

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")

        wrap = tk.Frame(self, bg=self.BG)
        wrap.pack(fill="both", expand=True)

        canvas = tk.Canvas(wrap, bg=self.BG, highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.BG)
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(win, width=e.width))

        card = tk.Frame(inner, bg=self.CARD,
                        highlightbackground=self.BORDER, highlightthickness=1)
        card.pack(fill="x", padx=18, pady=14)

        body = tk.Frame(card, bg=self.CARD)
        body.pack(fill="both", expand=True, padx=18, pady=16)

        for key, label, multiline, readonly in self.FIELDS:

            box = tk.Frame(body, bg=self.CARD)
            box.pack(fill="x", pady=4)

            tk.Label(box, text=label, bg=self.CARD, fg=self.TEXT,
                     font=("Arial", 9, "bold"), width=22,
                     anchor="w").pack(side="left", anchor="n")

            value = self.product.get(key, "")
            self.vars[key] = tk.StringVar(value=str(value) if value is not None else "")

            if multiline:
                w = tk.Text(box, height=3, bg="white", fg=self.TEXT,
                            relief="solid", bd=1, font=("Arial", 10),
                            insertbackground=self.RED, wrap="word")
                w.pack(side="left", fill="x", expand=True, ipady=4)
                w.insert("1.0", self.vars[key].get())
                self.vars[key + "_widget"] = w
                if readonly:
                    w.configure(state="disabled")
            else:
                e = tk.Entry(box, textvariable=self.vars[key],
                             bg="white", fg=self.TEXT,
                             relief="solid", bd=1,
                             font=("Arial", 10),
                             insertbackground=self.RED)
                e.pack(side="left", fill="x", expand=True, ipady=6)
                if readonly:
                    e.configure(state="readonly",
                                readonlybackground=self.SOFT)

        footer = tk.Frame(self, bg="white", height=66,
                          highlightbackground=self.BORDER,
                          highlightthickness=1)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        tk.Button(footer, text="Cancel", command=self._cancel,
                  bg="white", fg=self.TEXT,
                  activebackground="#F3F4F6", activeforeground=self.TEXT,
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9), cursor="hand2",
                  width=14, height=2).pack(side="right", padx=(8, 22), pady=14)

        tk.Button(footer, text="Save Product", command=self._save,
                  bg=self.RED, fg="white",
                  activebackground=self.RED_DARK, activeforeground="white",
                  relief="flat", bd=0, highlightthickness=0,
                  font=("Arial", 10, "bold"), cursor="hand2",
                  width=18, height=2).pack(side="right", pady=14)

    def _collect(self):

        data = {}
        for key, _label, multiline, readonly in self.FIELDS:

            if readonly:
                continue

            if multiline:
                w = self.vars.get(key + "_widget")
                if w is not None:
                    data[key] = w.get("1.0", "end").strip()
            else:
                var = self.vars.get(key)
                if isinstance(var, tk.StringVar):
                    data[key] = var.get().strip()

        # Coerce price to int if possible
        if "price" in data:
            try:
                data["price"] = int(Decimal(str(data["price"])))
            except Exception:
                pass

        return data

    def _save(self):

        if update_product is None:
            messagebox.showerror("Unavailable",
                                 "Catalog admin service not loaded.",
                                 parent=self)
            return

        data = self._collect()
        if not data:
            self._cancel()
            return

        ok, err = update_product(self.original_model, data)

        if not ok:
            messagebox.showerror("Save failed", str(err), parent=self)
            return

        self.result = data
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()



# ============================================================
# MAIN WINDOW
# ============================================================

class ProductManager(tk.Toplevel):

    BG = T.BG
    CARD = T.SURFACE
    TEXT = T.TEXT
    MUTED = T.TEXT_MUTED
    LIGHT_MUTED = T.TEXT_FAINT
    BORDER = T.BORDER
    RED = T.ACCENT
    RED_DARK = T.ACCENT_DARK
    RED_LIGHT = T.ACCENT_SOFT
    SOFT = T.SURFACE_ALT
    GREEN = T.SUCCESS

    def __init__(self, parent):
        super().__init__(parent)

        self.title("CRYSTAL | Products")
        self.geometry("1180x700")
        self.minsize(1000, 600)
        self.configure(bg=self.BG)
        W.set_window_icon(self)

        self.transient(parent)
        self.grab_set()

        self.current_tab = "products"
        self.selected_key = None

        W.apply_ttk_theme(self)
        self._build_interface()
        self.after(50, self._reload)

        # ---- Escape closes the window ----
        try:
            from ui.common.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(self, on_escape=self.destroy)
        except Exception:
            pass

    def _build_interface(self):

        header = W.PageHeader(
            self, title="Products & Prices",
            subtitle="Catalog models, categories and prices",
            meta="Loading…", padx=28,
        )
        header.pack(fill="x")
        self.count_label = header.meta_label

        toolbar = tk.Frame(self, bg=self.BG)
        toolbar.pack(fill="x", padx=28, pady=(14, 10))

        tabs = tk.Frame(
            toolbar, bg=self.CARD,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        tabs.pack(side="left")

        self.tab_buttons = {}
        for key, label in [("products", "Products"),
                           ("backups", "Backups")]:
            btn = tk.Button(
                tabs, text=label,
                command=lambda k=key: self._switch_tab(k),
                bg=self.SOFT, fg=T.TEXT_BODY,
                activebackground=T.SURFACE_HOVER,
                activeforeground=self.TEXT,
                relief="flat", bd=0, highlightthickness=0,
                font=T.FONT_LABEL, cursor="hand2", padx=18, pady=8,
            )
            btn.pack(side="left")
            self.tab_buttons[key] = btn

        self._search_var = tk.StringVar()
        search = W.SearchEntry(
            toolbar, textvariable=self._search_var, width=30,
            placeholder="Search model, category or name…", bg=self.CARD,
        )
        search.pack(side="right")
        search.entry.bind("<KeyRelease>",
                          lambda e: self._filter_products(), add="+")

        self._build_footer()

        self.body = tk.Frame(self, bg=self.BG)
        self.body.pack(fill="both", expand=True, padx=28, pady=(0, 12))

    def _build_footer(self):
        bar = tk.Frame(self, bg=self.CARD, height=68,
                       highlightbackground=self.BORDER,
                       highlightthickness=1)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=self.CARD)
        left.pack(side="left", padx=22, pady=15)

        W.PrimaryButton(
            left, "Add product", self._add_new_product,
            icon="+", padx=14, pady=7,
        ).pack(side="left")
        self.edit_btn = W.GhostButton(
            left, "Edit selected", self._edit_selected, padx=12, pady=7,
        )
        self.edit_btn.pack(side="left", padx=(8, 0))
        self.bulk_btn = W.GhostButton(
            left, "Bulk adjust…", self._bulk_adjust, padx=12, pady=7,
        )
        self.bulk_btn.pack(side="left", padx=(8, 0))
        W.GhostButton(
            left, "Reload", self._reload, padx=12, pady=7,
        ).pack(side="left", padx=(8, 0))

        right_side = tk.Frame(bar, bg=self.CARD)
        right_side.pack(side="right", padx=22, pady=15)
        W.GhostButton(
            right_side, "Close", self.destroy, padx=18, pady=7,
        ).pack(side="right")

    def _set_count(self, count, noun="product"):
        if self.count_label is not None:
            self.count_label.configure(
                text=f"{count:,} {noun}{'s' if count != 1 else ''}"
            )

    def _switch_tab(self, key):
        self.current_tab = key
        self.selected_key = None
        self._reload()

    def _filter_products(self):
        """Filter the product table based on the search query."""
        if self.current_tab != "products":
            return
        query = self._search_var.get().strip().lower()
        
        # Clear the table
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # If _all_products doesn't exist, load the catalog now
        if not hasattr(self, '_all_products') or not self._all_products:
            try:
                from app.services.catalog_service import load_catalog
                catalog = load_catalog() or {}
                self._all_products = catalog.get("products", [])
            except Exception as e:
                print(f"[products] Could not load catalog: {e}")
                self._all_products = []
        
        count = 0
        for p in self._all_products:
            model = str(p.get("model", "")).lower()
            name = str(p.get("name") or p.get("product_name") or "").lower()
            category = str(p.get("category", "")).lower()

            if not query or query in model or query in name or query in category:
                self.tree.insert("", "end", values=(
                    p.get("model", ""),
                    p.get("category", ""),
                    _short_name(p.get("name") or p.get("product_name", "")),
                    _money(p.get("price", 0)),
                    p.get("status") or "Active",
                ), tags=("evenrow" if count % 2 else "oddrow",))
                count += 1

        self._set_count(count)
        if getattr(self, "_empty", None) is not None:
            try:
                if count:
                    self._empty.place_forget()
                else:
                    self._empty.place(relx=0.5, rely=0.5, anchor="center")
                    self._empty.lift()
            except Exception:
                pass

    def _reload(self):
        # Load all products into memory for fast filtering
        try:
            from app.services.catalog_service import load_catalog
            catalog = load_catalog() or {}
            self._all_products = catalog.get("products", [])
        except Exception as e:
            print(f"[products] Could not load catalog: {e}")
            self._all_products = []
        

        for widget in self.body.winfo_children():
            widget.destroy()

        for key, btn in self.tab_buttons.items():
            if key == self.current_tab:
                btn.configure(bg=T.ACCENT_SOFT, fg=T.ACCENT)
            else:
                btn.configure(bg=self.SOFT, fg=T.TEXT_BODY)

        # Edit / bulk actions only apply to the catalog tab
        on_products = self.current_tab == "products"
        self.edit_btn.set_enabled(on_products)
        self.bulk_btn.set_enabled(on_products)

        if self.current_tab == "products":
            self._render_products()
        elif self.current_tab == "backups":
            self._render_backups()

    # --------------------------------------------------------
    # SHORTCUT INSTALLER (per tab)
    # --------------------------------------------------------

    def _install_tree_shortcuts(self, tree, on_enter):
        """Wire keyboard nav on the given tree, once per tab."""
        try:
            from ui.common.ui_helpers import install_table_shortcuts
            install_table_shortcuts(tree, on_enter=on_enter)
            tree.focus_set()
        except Exception:
            pass

    # --------------------------------------------------------
    # PRODUCTS
    # --------------------------------------------------------

    def _table_card(self):
        card = tk.Frame(
            self.body, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        card.pack(fill="both", expand=True)
        return card

    def _fill_products(self, tree, products):
        for idx, p in enumerate(products):
            tree.insert("", "end", iid=f"row_{idx}", values=(
                p.get("model", ""),
                p.get("category", ""),
                _short_name(p.get("name") or p.get("product_name", "")),
                _money(p.get("price", 0)),
                p.get("status") or "Active",
            ), tags=("evenrow" if idx % 2 else "oddrow",))

    def _render_products(self):

        products = self._all_products

        card = self._table_card()

        cols = ("model", "category", "name", "price", "status")
        tree = ttk.Treeview(card, columns=cols, show="headings", height=12)

        headings = {
            "model": "Model",
            "category": "Category",
            "name": "Product Name",
            "price": "Price",
            "status": "Status",
        }
        widths = {
            "model": 130, "category": 190, "name": 300,
            "price": 120, "status": 100,
        }

        for c in cols:
            tree.heading(c, text=headings[c],
                         anchor="e" if c == "price" else "w")
            tree.column(
                c, width=widths[c],
                anchor="e" if c == "price" else "w",
                stretch=(c == "name"),
            )

        tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        tree.tag_configure("oddrow", background=T.SURFACE)

        self._fill_products(tree, products)

        vsb = ttk.Scrollbar(card, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 2), pady=2)
        tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        tree.bind("<<TreeviewSelect>>", self._on_select)
        tree.bind("<Double-1>", lambda e: self._edit_selected())

        self.tree = tree
        self._set_count(len(products))

        self._empty = W.EmptyState(
            card, icon="📦", title="No products found",
            hint="Try a different search, or add a new product.",
        )
        if not products:
            self._empty.place(relx=0.5, rely=0.5, anchor="center")

        # Keyboard shortcuts
        self._install_tree_shortcuts(tree, self._edit_selected)

    # --------------------------------------------------------
    # ACCESSORIES
    # --------------------------------------------------------

    def _render_backups(self):

        self._empty = None
        backups = list_backups() if list_backups else []

        card = self._table_card()

        tool = tk.Frame(card, bg=T.SURFACE)
        tool.pack(fill="x", padx=14, pady=(12, 8))
        tk.Label(
            tool, text="Restoring replaces the current catalog with the selected backup.",
            bg=T.SURFACE, fg=T.TEXT_MUTED, font=T.FONT_SMALL,
        ).pack(side="left")
        W.PrimaryButton(
            tool, "Restore selected", self._restore_selected,
            padx=14, pady=7,
        ).pack(side="right")

        tk.Frame(card, bg=T.BORDER, height=1).pack(fill="x")

        tree_wrap = tk.Frame(card, bg=T.SURFACE)
        tree_wrap.pack(fill="both", expand=True)

        cols = ("timestamp", "filename")
        tree = ttk.Treeview(tree_wrap, columns=cols, show="headings", height=12)

        for c, title, width in (("timestamp", "Created", 180),
                                ("filename", "Backup file", 420)):
            tree.heading(c, text=title)
            tree.column(c, width=width, anchor="w",
                        stretch=(c == "filename"))

        tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        tree.tag_configure("oddrow", background=T.SURFACE)

        for idx, (ts, path) in enumerate(backups):
            tree.insert("", "end", iid=str(path),
                        values=(_friendly_ts(ts), path.name),
                        tags=("evenrow" if idx % 2 else "oddrow",))

        vsb = ttk.Scrollbar(tree_wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 2), pady=2)
        tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        tree.bind("<<TreeviewSelect>>", self._on_select)
        tree.bind("<Double-1>", lambda e: self._restore_selected())

        self.tree = tree
        self._set_count(len(backups), "backup file")

        if not backups:
            W.EmptyState(
                tree_wrap, icon="🗄", title="No backups yet",
                hint="A backup is created automatically before catalog changes.",
            ).place(relx=0.5, rely=0.5, anchor="center")

        # Keyboard shortcuts
        self._install_tree_shortcuts(tree, self._restore_selected)

    # --------------------------------------------------------
    # SELECT / EDIT
    # --------------------------------------------------------

    def _on_select(self, _event=None):
        sel = self.tree.selection() if hasattr(self, "tree") else ()
        self.selected_key = sel[0] if sel else None

    def _add_new_product(self):
        """Open the Add New Product form (uses the same 2-column layout as Edit)."""
        self._open_product_form(mode="add")


    def _open_product_form(self, mode="add", product=None):
        """Open a compact 2-column popup form to add or edit a product."""
        import tkinter as tk
        from tkinter import messagebox
        
        dialog = tk.Toplevel(self)
        dialog.title("Add New Product" if mode == "add" else f"Edit Product: {product.get('model', '')}")
        dialog.configure(bg=T.SURFACE)
        dialog.transient(self)
        dialog.withdraw()
        W.set_window_icon(dialog)
        W.apply_ttk_theme(dialog)

        head = tk.Frame(dialog, bg=T.SURFACE)
        head.pack(fill="x", padx=22, pady=(18, 0))
        tk.Label(
            head,
            text="Add new product" if mode == "add"
            else f"Edit product · {product.get('model', '')}",
            bg=T.SURFACE, fg=T.TEXT, font=T.FONT_H2,
        ).pack(anchor="w")
        tk.Label(
            head, text="Catalog details used on quotations and proforma invoices.",
            bg=T.SURFACE, fg=T.TEXT_MUTED, font=T.FONT_SMALL,
        ).pack(anchor="w", pady=(2, 0))
        tk.Frame(dialog, bg=T.ACCENT, height=2).pack(fill="x", padx=22, pady=(12, 0))

        # Reserve the footer before the expanding card so DPI-scaled text
        # can never squeeze the Save/Cancel buttons.
        btn_frame = tk.Frame(dialog, bg=T.SURFACE)
        btn_frame.pack(side="bottom", fill="x", padx=22, pady=(10, 14))
        tk.Frame(dialog, bg=T.BORDER, height=1).pack(side="bottom", fill="x")

        main_frame = tk.Frame(dialog, bg=T.BG)
        main_frame.pack(fill="both", expand=True, padx=22, pady=(14, 8))

        card = tk.Frame(
            main_frame, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        card.pack(fill="both", expand=True)

        fields = {}
        field_list = [
            ("Model", "model"), ("Category", "category"),
            ("Product name", "name"), ("Price (₹)", "price"),
            ("HSN/SAC code", "hsn"), ("Unit", "unit"), ("Tax %", "tax_percent"),
        ]

        for i, (label_text, key) in enumerate(field_list):
            col_offset = 0 if i < 4 else 2
            row = (i % 4)

            tk.Label(
                card, text=label_text, bg=T.SURFACE, fg=T.TEXT_BODY,
                font=T.FONT_LABEL, anchor="w",
            ).grid(row=row, column=col_offset, sticky="w",
                   padx=(20, 10), pady=(12, 0))

            var = tk.StringVar()
            fields[key] = var
            if product:
                if key == "name":
                    var.set(str(product.get("name") or product.get("product_name") or ""))
                elif key == "tax_percent":
                    var.set(str(product.get("tax_percent") or product.get("tax") or "18"))
                else:
                    val = product.get(key, "")
                    if val is not None:
                        var.set(str(val))

            entry = W.SearchEntry(
                card, textvariable=var, placeholder="", show_icon=False,
            )
            entry.grid(row=row, column=col_offset + 1, sticky="ew",
                       padx=(0, 20), pady=(12, 0))
            if mode == "edit" and key == "model":
                entry.entry.configure(state="disabled",
                                      disabledbackground=T.SURFACE_ALT)

        tk.Label(
            card, text="Description", bg=T.SURFACE, fg=T.TEXT_BODY,
            font=T.FONT_LABEL, anchor="w",
        ).grid(row=5, column=0, sticky="nw", padx=(20, 10), pady=(12, 0))

        notes_wrap = tk.Frame(card, bg=T.BORDER_HARD)
        notes_wrap.grid(row=5, column=1, columnspan=3, sticky="ew",
                        padx=(0, 20), pady=(12, 14))
        notes_inner = tk.Frame(notes_wrap, bg=T.SURFACE)
        notes_inner.pack(fill="both", expand=True, padx=1, pady=1)
        text_widget = tk.Text(
            notes_inner, height=4, font=T.FONT_BODY,
            bg=T.SURFACE, fg=T.TEXT, bd=0, highlightthickness=0,
            insertbackground=T.TEXT, wrap="word",
        )
        text_widget.pack(side="left", fill="both", expand=True, padx=8, pady=6)
        if product:
            text_widget.insert("1.0", str(product.get("description") or ""))
        fields["description_widget"] = text_widget

        card.grid_columnconfigure(1, weight=1)
        card.grid_columnconfigure(3, weight=1)

        def save():
            model = fields["model"].get().strip()
            if not model:
                messagebox.showerror("Error", "Model is required.", parent=dialog)
                return
            try:
                price = float(fields["price"].get().strip() or "0")
            except ValueError:
                messagebox.showerror("Error", "Price must be a number.", parent=dialog)
                return
            product_data = {
                "model": model,
                "category": fields["category"].get().strip() or "Uncategorized",
                "name": fields["name"].get().strip(),
                "product_name": fields["name"].get().strip(),
                "description": fields["description_widget"].get("1.0", "end").strip(),
                "price": price,
                "hsn": fields["hsn"].get().strip() or "85059000",
                "unit": fields["unit"].get().strip() or "NOS",
                "tax_percent": fields["tax_percent"].get().strip() or "18",
                "status": "Active",
            }
            try:
                if mode == "add":
                    from app.services.catalog_admin_service import add_product
                    add_product(product_data)
                    messagebox.showinfo("Success", f"Product '{model}' added.", parent=dialog)
                else:
                    from app.services.catalog_admin_service import update_product
                    update_product(model, product_data)
                    messagebox.showinfo("Success", f"Product '{model}' updated.", parent=dialog)
                dialog.destroy()
                self._reload()
            except Exception as e:
                messagebox.showerror("Error", f"Could not save: {e}", parent=dialog)
        
        W.GhostButton(
            btn_frame, "Cancel", dialog.destroy, padx=18, pady=7,
        ).pack(side="right")
        W.PrimaryButton(
            btn_frame, "Save product", save, padx=18, pady=7,
        ).pack(side="right", padx=(0, 8))

        # Fit the window to its requested content instead of a fixed height.
        dialog.update_idletasks()
        width = min(680, dialog.winfo_screenwidth() - 40)
        height = dialog.winfo_reqheight()
        height = min(max(480, height),
                     dialog.winfo_screenheight() - 80)
        self.update_idletasks()
        x = self.winfo_rootx() + (self.winfo_width() - width) // 2
        y = self.winfo_rooty() + max(0, (self.winfo_height() - height) // 3)
        x = max(10, min(x, dialog.winfo_screenwidth() - width - 10))
        y = max(10, min(y, dialog.winfo_screenheight() - height - 40))
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.minsize(width, height)
        dialog.deiconify()
        dialog.grab_set()


    def _edit_selected(self):
        """Open the form pre-filled with the selected product."""
        if not self.selected_key:
            messagebox.showinfo("No selection", "Please select a row first.", parent=self)
            return

        if self.current_tab == "products":
            # Get the selected row
            sel = self.tree.selection()
            if not sel:
                messagebox.showinfo("No selection", "Please select a row first.", parent=self)
                return
            
            # Get the MODEL from the first column (values[0]), not the iid
            values = self.tree.item(sel[0], "values")
            model_name = str(values[0]).strip() if values else ""
            
            if not model_name:
                messagebox.showerror("Error", "Could not read model name.", parent=self)
                return
            
            # Find the product in the catalog
            catalog = load_catalog() or {}
            product = None
            search_key = model_name.strip().lower()
            
            for p in catalog.get("products", []):
                if str(p.get("model", "")).strip().lower() == search_key:
                    product = p
                    break
            
            if product is None:
                messagebox.showerror(
                    "Not found",
                    f"Product '{model_name}' not found in catalog.\n\n"
                    f"Try clicking 'Reload' first.",
                    parent=self
                )
                return
            
            # Use our new simple form instead of the old ProductEditDialog
            self._open_product_form(mode="edit", product=product)


    def _bulk_adjust(self):

        if bulk_adjust_product_prices is None:
            messagebox.showerror("Unavailable",
                                 "Catalog admin service not loaded.",
                                 parent=self)
            return

        dialog = tk.Toplevel(self)
        dialog.title("Bulk Price Adjust")
        dialog.geometry("460x360")
        dialog.configure(bg=T.SURFACE)
        dialog.transient(self)
        dialog.grab_set()
        W.set_window_icon(dialog)
        W.apply_ttk_theme(dialog)

        inner = tk.Frame(dialog, bg=T.SURFACE)
        inner.pack(fill="both", expand=True, padx=24, pady=18)

        tk.Label(
            inner, text="Bulk price adjust",
            bg=T.SURFACE, fg=T.TEXT, font=T.FONT_H2,
        ).pack(anchor="w")
        tk.Label(
            inner, text="Apply one percentage change to a category or the whole catalog.",
            bg=T.SURFACE, fg=T.TEXT_MUTED, font=T.FONT_SMALL,
        ).pack(anchor="w", pady=(2, 14))

        tk.Label(inner, text="CATEGORY",
                 bg=T.SURFACE, fg=T.TEXT_BODY,
                 font=T.FONT_LABEL).pack(anchor="w", pady=(0, 4))

        catalog = load_catalog() or {}
        categories = sorted({p.get("category", "")
                             for p in catalog.get("products", [])})

        category_var = tk.StringVar(value="ALL")
        combo = ttk.Combobox(inner, textvariable=category_var,
                             values=["ALL"] + categories,
                             state="readonly", font=T.FONT_BODY)
        combo.pack(fill="x", ipady=4, pady=(0, 14))

        tk.Label(inner, text="ADJUSTMENT (%)",
                 bg=T.SURFACE, fg=T.TEXT_BODY,
                 font=T.FONT_LABEL).pack(anchor="w", pady=(0, 4))

        pct_var = tk.StringVar(value="5")
        pct_entry = W.SearchEntry(
            inner, textvariable=pct_var, placeholder="", show_icon=False,
        )
        pct_entry.pack(fill="x")

        tk.Label(inner,
                 text="Positive increases prices; negative decreases them.",
                 bg=T.SURFACE, fg=T.TEXT_MUTED,
                 font=T.FONT_TINY).pack(anchor="w", pady=(6, 0))

        def apply_bulk():
            cat = category_var.get()
            cat = None if cat == "ALL" else cat
            try:
                pct = float(pct_var.get())
            except Exception:
                messagebox.showerror("Invalid", "Enter a number.", parent=dialog)
                return

            ok, result = bulk_adjust_product_prices(cat, pct)
            if not ok:
                messagebox.showerror("Failed", str(result), parent=dialog)
                return

            messagebox.showinfo("Done",
                                f"Adjusted {result} product(s).",
                                parent=dialog)
            dialog.destroy()
            self._reload()

        btn_row = tk.Frame(inner, bg=T.SURFACE)
        btn_row.pack(side="bottom", fill="x", pady=(18, 0))

        W.GhostButton(
            btn_row, "Cancel", dialog.destroy, padx=18, pady=7,
        ).pack(side="right")
        W.PrimaryButton(
            btn_row, "Apply", apply_bulk, padx=18, pady=7,
        ).pack(side="right", padx=(0, 8))

        # Escape closes the bulk dialog
        try:
            from ui.common.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(dialog, on_escape=dialog.destroy)
        except Exception:
            pass

    # --------------------------------------------------------
    # RESTORE
    # --------------------------------------------------------

    def _restore_selected(self):

        if not self.selected_key:
            messagebox.showinfo("No selection",
                                "Select a backup row first.",
                                parent=self)
            return

        ok = messagebox.askyesno(
            "Restore backup",
            "This will replace the current catalog with the selected backup.\n\n"
            "The current catalog will be backed up first.\n\nContinue?",
            parent=self,
        )
        if not ok:
            return

        success, err = restore_backup(self.selected_key)
        if not success:
            messagebox.showerror("Restore failed", str(err), parent=self)
            return

        messagebox.showinfo("Restored",
                            "Catalog restored successfully.",
                            parent=self)
        self._reload()


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    ProductManager(root)
    root.mainloop()