# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# PRODUCT / PRICE MANAGER
#
# Modal window — two tabs (Products / Accessories).
#
# File:
#   ui/product_manager.py
# ============================================================

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, InvalidOperation


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:
    from app.services.catalog_admin_service import (
        load_catalog,
        update_product,
        update_accessory,
        bulk_adjust_product_prices,
        list_backups,
        restore_backup,
    )
except Exception:
    load_catalog = None
    update_product = None
    update_accessory = None
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
# ACCESSORY EDIT DIALOG
# ============================================================

class AccessoryEditDialog(tk.Toplevel):

    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_DARK = "#980000"
    SOFT = "#F8F9FA"

    FIELDS = [
        ("code", "Code", True),
        ("name", "Name", False),
        ("category", "Category", False),
        ("price", "Price (INR)", False),
        ("default_quantity", "Default Quantity", False),
        ("unit", "Unit", False),
        ("status", "Status (active/inactive)", False),
        ("description", "Description", False),
    ]

    def __init__(self, parent, accessory):
        super().__init__(parent)

        self.result = None
        self.accessory = accessory or {}
        self.original_code = self.accessory.get("code", "")

        self.title(f"Edit Accessory — {self.original_code}")
        self.geometry("640x600")
        self.minsize(560, 480)
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
                 text=f"Edit Accessory — {self.original_code}",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 14, "bold")).pack(anchor="w", padx=22,
                                                  pady=(18, 0))

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")

        card = tk.Frame(self, bg=self.CARD,
                        highlightbackground=self.BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=18, pady=14)

        body = tk.Frame(card, bg=self.CARD)
        body.pack(fill="both", expand=True, padx=18, pady=16)

        for key, label, readonly in self.FIELDS:

            box = tk.Frame(body, bg=self.CARD)
            box.pack(fill="x", pady=5)

            tk.Label(box, text=label, bg=self.CARD, fg=self.TEXT,
                     font=("Arial", 9, "bold"), width=20,
                     anchor="w").pack(side="left")

            value = self.accessory.get(key, "")
            self.vars[key] = tk.StringVar(value=str(value) if value is not None else "")

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

        tk.Button(footer, text="Save Accessory", command=self._save,
                  bg=self.RED, fg="white",
                  activebackground=self.RED_DARK, activeforeground="white",
                  relief="flat", bd=0, highlightthickness=0,
                  font=("Arial", 10, "bold"), cursor="hand2",
                  width=18, height=2).pack(side="right", pady=14)

    def _save(self):

        if update_accessory is None:
            messagebox.showerror("Unavailable",
                                 "Catalog admin service not loaded.",
                                 parent=self)
            return

        data = {}
        for key, _label, readonly in self.FIELDS:
            if readonly:
                continue
            var = self.vars.get(key)
            if isinstance(var, tk.StringVar):
                data[key] = var.get().strip()

        # Coerce numeric fields
        for num_key in ("price",):
            try:
                data[num_key] = int(Decimal(str(data.get(num_key, 0))))
            except Exception:
                pass

        try:
            data["default_quantity"] = int(Decimal(
                str(data.get("default_quantity", 1))))
        except Exception:
            data["default_quantity"] = 1

        ok, err = update_accessory(self.original_code, data)

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

    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    LIGHT_MUTED = "#9BA1AA"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_DARK = "#980000"
    RED_LIGHT = "#FFF3F3"
    SOFT = "#F8F9FA"
    GREEN = "#16804B"

    def __init__(self, parent):
        super().__init__(parent)

        self.title("CRYSTAL | Products & Prices")
        self.geometry("1180x760")
        self.minsize(1000, 640)
        self.configure(bg=self.BG)

        self.transient(parent)
        self.grab_set()

        self.current_tab = "products"
        self.selected_key = None

        self._configure_style()
        self._build_interface()
        self.after(50, self._reload)

        # ---- Escape closes the window ----
        try:
            from ui.common.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(self, on_escape=self.destroy)
        except Exception:
            pass

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("PM.Treeview",
                        background="white", fieldbackground="white",
                        foreground=self.TEXT, borderwidth=1,
                        relief="solid", rowheight=28, font=("Arial", 9))
        style.configure("PM.Treeview.Heading",
                        background=self.SOFT, foreground=self.TEXT,
                        font=("Arial", 9, "bold"), relief="flat")
        style.map("PM.Treeview",
                  background=[("selected", self.RED_LIGHT)],
                  foreground=[("selected", self.TEXT)])

    def _build_interface(self):

        # Header
        header = tk.Frame(self, bg=self.CARD, height=78)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=self.CARD)
        brand.pack(side="left", padx=28)

        tk.Label(brand, text="CRYSTAL", bg=self.CARD, fg=self.RED,
                 font=("Arial", 22, "bold")).pack(side="left", pady=22)
        tk.Label(brand, text="  /  Products & Prices",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 11)).pack(side="left", pady=26)

        right = tk.Frame(header, bg=self.CARD)
        right.pack(side="right", padx=28)

        self.count_label = tk.Label(right, text="", bg=self.CARD,
                                    fg=self.MUTED, font=("Arial", 9))
        self.count_label.pack(anchor="e", pady=26)

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")

        # Tabs
        tab_bar = tk.Frame(self, bg=self.CARD, height=52)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        inner = tk.Frame(tab_bar, bg=self.CARD)
        inner.pack(padx=28, pady=8)

        self.tab_buttons = {}
        for key, label in [("products", "Products"),
                            ("accessories", "Accessories"),
                            ("backups", "Backups")]:
            btn = tk.Button(inner, text=label,
                            command=lambda k=key: self._switch_tab(k),
                            bg=self.SOFT, fg=self.TEXT,
                            activebackground="#ECEEF1",
                            activeforeground=self.TEXT,
                            relief="solid", bd=1, highlightthickness=0,
                            font=("Arial", 9, "bold"),
                            cursor="hand2", padx=14, pady=6)
            btn.pack(side="left", padx=(0, 6))
            self.tab_buttons[key] = btn

        tk.Frame(self, bg=self.BORDER, height=1).pack(fill="x")

        # Bottom action bar
        bar = tk.Frame(self, bg=self.CARD, height=70,
                       highlightbackground=self.BORDER,
                       highlightthickness=1)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=self.CARD)
        left.pack(side="left", padx=22)

        self.edit_btn = self._btn(left, "Edit Selected", self._edit_selected,
                                   primary=True)
        self.edit_btn.pack(side="left", pady=14)

        self.bulk_btn = self._btn(left, "Bulk Adjust…", self._bulk_adjust)
        self.bulk_btn.pack(side="left", padx=(8, 0), pady=14)

        self._btn(left, "Reload", self._reload).pack(
            side="left", padx=(8, 0), pady=14)

        right_side = tk.Frame(bar, bg=self.CARD)
        right_side.pack(side="right", padx=22)

        self._btn(right_side, "Close", self.destroy).pack(
            side="right", pady=14)

        # Content area
        self.body = tk.Frame(self, bg=self.BG)
        self.body.pack(fill="both", expand=True, padx=28, pady=14)


    def _btn(self, parent, text, command, primary=False, danger=False):
        if primary:
            bg, fg = self.RED, "white"
            active_bg = self.RED_DARK
            relief, bd = "flat", 0
        else:
            bg, fg = "white", (self.RED if danger else self.TEXT)
            active_bg = self.RED_LIGHT if danger else "#F3F4F6"
            relief, bd = "solid", 1

        return tk.Button(parent, text=text, command=command,
                         bg=bg, fg=fg,
                         activebackground=active_bg, activeforeground=fg,
                         relief=relief, bd=bd, highlightthickness=0,
                         font=("Arial", 9, "bold"), cursor="hand2",
                         padx=14, pady=6)

    def _switch_tab(self, key):
        self.current_tab = key
        self.selected_key = None
        self._reload()

    def _reload(self):

        for widget in self.body.winfo_children():
            widget.destroy()

        for key, btn in self.tab_buttons.items():
            if key == self.current_tab:
                btn.configure(bg=self.RED, fg="white",
                              activebackground=self.RED_DARK,
                              activeforeground="white")
            else:
                btn.configure(bg=self.SOFT, fg=self.TEXT,
                              activebackground="#ECEEF1",
                              activeforeground=self.TEXT)

        # Toggle enabled/disabled buttons per tab
        if self.current_tab == "backups":
            self.edit_btn.configure(state="disabled", fg=self.LIGHT_MUTED)
            self.bulk_btn.configure(state="disabled", fg=self.LIGHT_MUTED)
        else:
            self.edit_btn.configure(state="normal", fg="white")
            self.bulk_btn.configure(state="normal", fg=self.TEXT)

        if self.current_tab == "products":
            self._render_products()
        elif self.current_tab == "accessories":
            self._render_accessories()
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

    def _render_products(self):

        try:
            catalog = load_catalog() or {}
            products = catalog.get("products", []) or []
        except Exception as e:
            import traceback
            traceback.print_exc()
            products = []

        cols = ("model", "category", "name", "price", "status")
        tree = ttk.Treeview(self.body, columns=cols, show="headings",
                            style="PM.Treeview", height=16)

        headings = {
            "model": "Model",
            "category": "Category",
            "name": "Product Name",
            "price": "Price",
            "status": "Status",
        }
        widths = {
            "model": 120, "category": 200, "name": 260,
            "price": 130, "status": 100,
        }

        for c in cols:
            tree.heading(c, text=headings[c])
            tree.column(c, width=widths[c], anchor="w",
                        stretch=(c in ("category", "name")))

        for p in products:
            try:
                model_val = p.get("model", "")
                tree.insert("", "end", iid=model_val,
                            values=(
                                p.get("model", ""),
                                p.get("category", ""),
                                p.get("product_name", ""),
                                _money(p.get("price", 0)),
                                p.get("status", ""),
                            ))
            except Exception as e:
                import traceback
                traceback.print_exc()

        vsb = ttk.Scrollbar(self.body, orient="vertical",
                            command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tree.bind("<<TreeviewSelect>>", self._on_select)
        tree.bind("<Double-1>", lambda e: self._edit_selected())

        self.tree = tree
        actual_rows = len(tree.get_children())
        
        # Check tree visibility
        tree.update_idletasks()
        
        # Show first row
        children = tree.get_children()
        if children:
            first = children[0]
            vals = tree.item(first, 'values')
        
        self.count_label.configure(text=f"{len(products)} product(s)")

        # Keyboard shortcuts
        self._install_tree_shortcuts(tree, self._edit_selected)

    # --------------------------------------------------------
    # ACCESSORIES
    # --------------------------------------------------------

    def _render_accessories(self):

        catalog = load_catalog() or {}
        accessories = catalog.get("accessories", []) or []

        cols = ("code", "name", "category", "price", "qty", "status")
        tree = ttk.Treeview(self.body, columns=cols, show="headings",
                            style="PM.Treeview", height=16)

        headings = {
            "code": "Code",
            "name": "Name",
            "category": "Category",
            "price": "Price",
            "qty": "Default Qty",
            "status": "Status",
        }
        widths = {
            "code": 140, "name": 220, "category": 120,
            "price": 110, "qty": 100, "status": 100,
        }

        for c in cols:
            tree.heading(c, text=headings[c])
            tree.column(c, width=widths[c], anchor="w",
                        stretch=(c in ("name",)))

        for a in accessories:
            tree.insert("", "end", iid=a.get("code", ""),
                        values=(
                            a.get("code", ""),
                            a.get("name", ""),
                            a.get("category", ""),
                            _money(a.get("price", 0)),
                            a.get("default_quantity", 1),
                            a.get("status", ""),
                        ))

        vsb = ttk.Scrollbar(self.body, orient="vertical",
                            command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tree.bind("<<TreeviewSelect>>", self._on_select)
        tree.bind("<Double-1>", lambda e: self._edit_selected())

        self.tree = tree
        self.count_label.configure(text=f"{len(accessories)} accessory item(s)")

        # Keyboard shortcuts
        self._install_tree_shortcuts(tree, self._edit_selected)

    # --------------------------------------------------------
    # BACKUPS
    # --------------------------------------------------------

    def _render_backups(self):

        backups = list_backups() if list_backups else []

        cols = ("timestamp", "filename")
        tree = ttk.Treeview(self.body, columns=cols, show="headings",
                            style="PM.Treeview", height=16)

        for c in cols:
            tree.heading(c, text=c.title())
            tree.column(c, width=280, anchor="w",
                        stretch=(c == "filename"))

        for ts, path in backups:
            tree.insert("", "end", iid=str(path),
                        values=(ts, path.name))

        vsb = ttk.Scrollbar(self.body, orient="vertical",
                            command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tree.bind("<<TreeviewSelect>>", self._on_select)
        tree.bind("<Double-1>", lambda e: self._restore_selected())

        # Restore button
        restore_btn = self._btn(self.body, "Restore Selected Backup",
                                 self._restore_selected, primary=True)
        restore_btn.pack(side="bottom", anchor="w", pady=(10, 0))

        self.tree = tree
        self.count_label.configure(text=f"{len(backups)} backup file(s)")

        # Keyboard shortcuts
        self._install_tree_shortcuts(tree, self._restore_selected)

    # --------------------------------------------------------
    # SELECT / EDIT
    # --------------------------------------------------------

    def _on_select(self, _event=None):
        sel = self.tree.selection() if hasattr(self, "tree") else ()
        self.selected_key = sel[0] if sel else None

    def _edit_selected(self):

        if not self.selected_key:
            messagebox.showinfo("No selection",
                                "Please select a row first.",
                                parent=self)
            return

        if self.current_tab == "products":
            catalog = load_catalog() or {}
            product = None
            for p in catalog.get("products", []):
                if p.get("model") == self.selected_key:
                    product = p
                    break
            if product is None:
                messagebox.showerror("Not found",
                                     "Product not found in catalog.",
                                     parent=self)
                return
            dialog = ProductEditDialog(self, product)
            self.wait_window(dialog)
            if dialog.result is not None:
                self._reload()

        elif self.current_tab == "accessories":
            catalog = load_catalog() or {}
            accessory = None
            for a in catalog.get("accessories", []):
                if a.get("code") == self.selected_key:
                    accessory = a
                    break
            if accessory is None:
                messagebox.showerror("Not found",
                                     "Accessory not found in catalog.",
                                     parent=self)
                return
            dialog = AccessoryEditDialog(self, accessory)
            self.wait_window(dialog)
            if dialog.result is not None:
                self._reload()

    # --------------------------------------------------------
    # BULK ADJUST
    # --------------------------------------------------------

    def _bulk_adjust(self):

        if bulk_adjust_product_prices is None:
            messagebox.showerror("Unavailable",
                                 "Catalog admin service not loaded.",
                                 parent=self)
            return

        dialog = tk.Toplevel(self)
        dialog.title("Bulk Price Adjust")
        dialog.geometry("440x320")
        dialog.configure(bg=self.BG)
        dialog.transient(self)
        dialog.grab_set()

        card = tk.Frame(dialog, bg=self.CARD,
                        highlightbackground=self.BORDER,
                        highlightthickness=1)
        card.pack(fill="both", expand=True, padx=18, pady=18)

        inner = tk.Frame(card, bg=self.CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        tk.Label(inner, text="Apply to Category",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 4))

        catalog = load_catalog() or {}
        categories = sorted({p.get("category", "")
                             for p in catalog.get("products", [])})

        category_var = tk.StringVar(value="ALL")
        combo = ttk.Combobox(inner, textvariable=category_var,
                             values=["ALL"] + categories,
                             state="readonly",
                             style="Crystal.TCombobox")
        combo.pack(fill="x", pady=(0, 14))

        tk.Label(inner, text="Adjustment (%)",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 9, "bold")).pack(anchor="w", pady=(0, 4))

        pct_var = tk.StringVar(value="5")
        tk.Entry(inner, textvariable=pct_var, bg="white", fg=self.TEXT,
                 relief="solid", bd=1, font=("Arial", 10),
                 insertbackground=self.RED).pack(fill="x", ipady=6)

        tk.Label(inner,
                 text="Use positive to increase, negative to decrease.",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 8, "italic")).pack(anchor="w", pady=(4, 0))

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

        btn_row = tk.Frame(card, bg=self.CARD)
        btn_row.pack(side="bottom", fill="x", padx=20, pady=(0, 18))

        tk.Button(btn_row, text="Cancel", command=dialog.destroy,
                  bg="white", fg=self.TEXT,
                  activebackground="#F3F4F6", activeforeground=self.TEXT,
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9), cursor="hand2",
                  width=12, height=2).pack(side="right", padx=(8, 0))

        tk.Button(btn_row, text="Apply", command=apply_bulk,
                  bg=self.RED, fg="white",
                  activebackground=self.RED_DARK, activeforeground="white",
                  relief="flat", bd=0, highlightthickness=0,
                  font=("Arial", 10, "bold"), cursor="hand2",
                  width=14, height=2).pack(side="right")

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