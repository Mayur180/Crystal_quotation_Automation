# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# CUSTOMER DATABASE — Modal window
#
# File:
#   ui/customer_database.py
# ============================================================

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:
    from app.services.customer_service import (
        list_customers,
        get_customer,
        save_customer,
        delete_customer,
        count as customer_count,
    )
except Exception:
    list_customers = None
    get_customer = None
    save_customer = None
    delete_customer = None
    customer_count = None


# ============================================================
# EDIT DIALOG
# ============================================================

class CustomerEditDialog(tk.Toplevel):

    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_DARK = "#980000"
    RED_LIGHT = "#FFF3F3"
    SOFT = "#F8F9FA"

    def __init__(self, parent, customer=None):
        super().__init__(parent)

        self.result = None

        self.title("Edit Customer" if customer else "New Customer")
        self.geometry("620x780")
        self.minsize(500, 480)
        self.configure(bg=self.BG)

        self.transient(parent)
        self.grab_set()

        self.customer = customer or {}
        self.customer_id = self.customer.get("id")

        self.vars = {}
        self._build_interface()

        self.protocol("WM_DELETE_WINDOW", self._cancel)

        # ---- Keyboard shortcuts ----
        try:
            from ui.ui_helpers import install_modal_shortcuts
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
                 text=("Edit Customer" if self.customer_id else "New Customer"),
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 15, "bold")).pack(anchor="w", padx=24,
                                                  pady=(18, 0))

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")

        # Scrollable container
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(fill="both", expand=True)

        scroll_canvas = tk.Canvas(outer, bg=self.BG, highlightthickness=0, bd=0)
        scroll_bar = tk.Scrollbar(outer, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scroll_bar.set)

        scroll_canvas.pack(side="left", fill="both", expand=True)
        scroll_bar.pack(side="right", fill="y")

        body = tk.Frame(scroll_canvas, bg=self.BG)
        body_window = scroll_canvas.create_window((0, 0), window=body, anchor="nw")

        def _on_body_config(event=None):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))
        body.bind("<Configure>", _on_body_config)

        def _on_canvas_config(event):
            scroll_canvas.itemconfigure(body_window, width=event.width)
        scroll_canvas.bind("<Configure>", _on_canvas_config)

        # Wheel is routed through the shared ScrollManager.
        try:
            from ui.scroll_manager import ScrollManager
            ScrollManager.register(scroll_canvas, "vertical")
            self._scroll_canvas_for_cleanup = scroll_canvas
        except Exception:
            pass

        def _cleanup_wheel(event=None):
            if event is not None and event.widget is not self:
                return
            try:
                from ui.scroll_manager import ScrollManager
                canvas = getattr(self, "_scroll_canvas_for_cleanup", None)
                if canvas is not None:
                    ScrollManager.unregister(canvas)
            except Exception:
                pass

        # Clean up when the dialog is destroyed
        try:
            self.bind("<Destroy>", _cleanup_wheel, add="+")
        except Exception:
            pass

        body_inner = tk.Frame(body, bg=self.BG)
        body_inner.pack(fill="both", expand=True, padx=22, pady=18)

        card = tk.Frame(body_inner, bg=self.CARD,
                        highlightbackground=self.BORDER,
                        highlightthickness=1)
        card.pack(fill="both", expand=True)

        inner = tk.Frame(card, bg=self.CARD)
        inner.pack(fill="both", expand=True, padx=20, pady=18)

        fields = [
            ("Name",             "name",             False),
            ("Company",          "company",          False),
            ("Contact Person",   "contact_person",   False),
            ("Phone",            "phone",            False),
            ("Email",            "email",            False),
            ("GSTIN",            "gstin",            False),
            ("Address",          "address",          True),
            ("City",             "city",             False),
            ("State",            "state",            False),
            ("Pincode",          "pincode",          False),
            ("Country",          "country",          False),
        ]

        for label, key, multiline in fields:
            box = tk.Frame(inner, bg=self.CARD)
            box.pack(fill="x", pady=5)

            tk.Label(box, text=label, bg=self.CARD, fg=self.TEXT,
                     font=("Arial", 9, "bold"), width=16,
                     anchor="w").pack(side="left", anchor="n")

            self.vars[key] = tk.StringVar(value=self.customer.get(key, "") or "")

            if multiline:
                w = tk.Text(box, height=3, bg="white", fg=self.TEXT,
                            relief="solid", bd=1, font=("Arial", 10),
                            insertbackground=self.RED, wrap="word")
                w.pack(side="left", fill="x", expand=True, ipady=4)
                w.insert("1.0", self.vars[key].get())
                self.vars[key + "_widget"] = w
            else:
                e = tk.Entry(box, textvariable=self.vars[key],
                             bg="white", fg=self.TEXT,
                             relief="solid", bd=1,
                             font=("Arial", 10),
                             insertbackground=self.RED)
                e.pack(side="left", fill="x", expand=True, ipady=6)

        footer = tk.Frame(self, bg="white", height=64,
                          highlightbackground=self.BORDER,
                          highlightthickness=1)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        tk.Button(footer, text="Cancel", command=self._cancel,
                  bg="white", fg=self.TEXT,
                  activebackground="#F3F4F6", activeforeground=self.TEXT,
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9), cursor="hand2",
                  width=14, height=2).pack(side="right", padx=(8, 22), pady=13)

        tk.Button(footer, text="Save Customer", command=self._save,
                  bg=self.RED, fg="white",
                  activebackground=self.RED_DARK, activeforeground="white",
                  relief="flat", bd=0, highlightthickness=0,
                  font=("Arial", 10, "bold"), cursor="hand2",
                  width=18, height=2).pack(side="right", pady=13)

    def _collect(self):
        data = {}
        for key, var in self.vars.items():
            if key.endswith("_widget"):
                continue
            if isinstance(var, tk.StringVar):
                data[key] = var.get().strip()

        w = self.vars.get("address_widget")
        if w is not None:
            data["address"] = w.get("1.0", "end").strip()

        return data

    def _save(self):
        if save_customer is None:
            messagebox.showerror("Unavailable",
                                 "Customer service not loaded.",
                                 parent=self)
            return

        data = self._collect()

        if not data.get("name") and not data.get("company"):
            messagebox.showerror("Required",
                                 "Please enter at least a Name or a Company.",
                                 parent=self)
            return

        record, created = save_customer(data, customer_id=self.customer_id)

        if record is None:
            messagebox.showerror("Save failed", str(created), parent=self)
            return

        self.result = (record, created)
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


# ============================================================
# MAIN DATABASE WINDOW
# ============================================================

class CustomerDatabase(tk.Toplevel):

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
    SOFT = "#F8F9FA"

    def __init__(self, parent):
        super().__init__(parent)

        self.title("CRYSTAL | Customer Database")
        self.geometry("1100x720")
        self.minsize(940, 600)
        self.configure(bg=self.BG)

        self.transient(parent)
        self.grab_set()

        self.search_var = tk.StringVar()
        self.selected_id = None

        self._configure_style()
        self._build_interface()
        self._reload()

        # ---- Keyboard shortcuts ----
        try:
            from ui.ui_helpers import (
                install_table_shortcuts,
                install_modal_shortcuts,
            )
            install_table_shortcuts(
                self.tree,
                on_enter=lambda _id: self._edit(),
                on_delete=lambda _id: self._delete(),
            )
            install_modal_shortcuts(self, on_escape=self.destroy)
        except Exception:
            pass

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("Customer.Treeview",
                        background="white", fieldbackground="white",
                        foreground=self.TEXT, borderwidth=1,
                        relief="solid", rowheight=30, font=("Arial", 9))
        style.configure("Customer.Treeview.Heading",
                        background=self.SOFT, foreground=self.TEXT,
                        font=("Arial", 9, "bold"), relief="flat")
        style.map("Customer.Treeview",
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
        tk.Label(brand, text="  /  Customer Database",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 11)).pack(side="left", pady=26)

        right = tk.Frame(header, bg=self.CARD)
        right.pack(side="right", padx=28)

        self.count_label = tk.Label(right, text="", bg=self.CARD,
                                    fg=self.MUTED, font=("Arial", 9))
        self.count_label.pack(anchor="e", pady=26)

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")

        # Search
        bar = tk.Frame(self, bg=self.BG)
        bar.pack(fill="x", padx=28, pady=(18, 8))

        tk.Label(bar, text="Search", bg=self.BG, fg=self.MUTED,
                 font=("Arial", 8, "bold")).pack(side="left", padx=(0, 8))

        entry = tk.Entry(bar, textvariable=self.search_var,
                         bg="white", fg=self.TEXT,
                         relief="solid", bd=1,
                         font=("Arial", 10), insertbackground=self.RED)
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        entry.bind("<KeyRelease>", lambda e: self._reload())

        # Table
        card = tk.Frame(self, bg=self.CARD,
                        highlightbackground=self.BORDER,
                        highlightthickness=1)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 12))

        cols = ("name", "company", "phone", "email", "last_used")
        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                 style="Customer.Treeview", height=14)

        headings = {
            "name": "Name",
            "company": "Company",
            "phone": "Phone",
            "email": "Email",
            "last_used": "Last Used",
        }
        widths = {
            "name": 180, "company": 220, "phone": 130,
            "email": 220, "last_used": 130,
        }

        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w",
                             stretch=(c in ("company", "email")))

        vsb = ttk.Scrollbar(card, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True, padx=14, pady=14)
        vsb.pack(side="right", fill="y", pady=14)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda e: self._edit())

        # Ctrl+N → new quotation for selected customer
        try:
            self.bind("<Control-n>", lambda _e: self._open_quotation_for_selected())
        except Exception:
            pass

        # Right-click menu
        self._ctx_menu = tk.Menu(self, tearoff=0)
        self._ctx_menu.add_command(
            label="New Quotation",
            command=self._open_quotation_for_selected,
        )
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(
            label="Edit",
            command=self._edit,
        )
        self._ctx_menu.add_command(
            label="Delete",
            command=self._delete,
        )

        def _show_ctx(event):
            row = self.tree.identify_row(event.y)
            if not row:
                return
            self.tree.selection_set(row)
            try:
                self._on_select()
            except Exception:
                pass
            self._ctx_menu.tk_popup(event.x_root, event.y_root)

        self.tree.bind("<Button-3>", _show_ctx)

        # Set focus so keyboard nav works right away
        try:
            self.tree.focus_set()
        except Exception:
            pass

        # Action bar
        bar = tk.Frame(self, bg=self.CARD, height=70,
                       highlightbackground=self.BORDER,
                       highlightthickness=1)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=self.CARD)
        left.pack(side="left", padx=22)

        self._btn(left, "+  New Customer", self._new, primary=True).pack(
            side="left", pady=14)
        self._btn(left, "Edit", self._edit).pack(side="left",
                                                  padx=(8, 0), pady=14)
        self._btn(left, "Delete", self._delete, danger=True).pack(
            side="left", padx=(8, 0), pady=14)

        right = tk.Frame(bar, bg=self.CARD)
        right.pack(side="right", padx=22)

        self._btn(right, "New Quotation", self._open_quotation_for_selected).pack(side="right", padx=(0, 8), pady=14)
        self._btn(right, "Close", self.destroy).pack(side="right", pady=14)

    def _btn(self, parent, text, command, *, primary=False, danger=False):
        if primary:
            bg = self.RED
            fg = "white"
            active_bg = self.RED_DARK
            relief = "flat"
            bd = 0
        else:
            bg = "white"
            fg = self.RED if danger else self.TEXT
            active_bg = self.RED_LIGHT if danger else "#F3F4F6"
            relief = "solid"
            bd = 1

        return tk.Button(parent, text=text, command=command,
                         bg=bg, fg=fg,
                         activebackground=active_bg, activeforeground=fg,
                         relief=relief, bd=bd, highlightthickness=0,
                         font=("Arial", 9, "bold"), cursor="hand2",
                         padx=14, pady=6)

    def _reload(self):
        if list_customers is None:
            self.count_label.configure(text="Service unavailable")
            return

        try:
            records = list_customers(search=self.search_var.get().strip() or None)
        except Exception:
            records = []

        for row in self.tree.get_children():
            self.tree.delete(row)

        for r in records:
            last = (r.get("last_used") or "")[:16].replace("T", " ")
            self.tree.insert("", "end",
                             iid=r.get("id", ""),
                             values=(
                                 r.get("name", ""),
                                 r.get("company", ""),
                                 r.get("phone", ""),
                                 r.get("email", ""),
                                 last or "—",
                             ))

        self.count_label.configure(text=f"{len(records)} customer(s)")

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        self.selected_id = sel[0] if sel else None

    def _new(self):
        dialog = CustomerEditDialog(self, customer=None)
        self.wait_window(dialog)
        if dialog.result:
            self._reload()

    def _open_quotation_for_selected(self):
        """Open a New Quotation form pre-filled from the selected customer."""
        if not self.selected_id:
            messagebox.showinfo(
                "New Quotation",
                "Select a customer first.",
                parent=self,
            )
            return

        customer = None
        try:
            from app.services.customer_service import get_customer
            customer = get_customer(self.selected_id)
        except Exception:
            customer = None

        if not customer:
            messagebox.showerror(
                "New Quotation",
                "Could not load the selected customer.",
                parent=self,
            )
            return

        try:
            from ui.quotation_form import QuotationForm
        except Exception as e:
            messagebox.showerror(
                "New Quotation",
                f"Could not open Quotation form:\\n{e}",
                parent=self,
            )
            return

        try:
            QuotationForm(self.master, self, prefill=customer)
        except Exception as e:
            messagebox.showerror(
                "New Quotation",
                f"Could not open Quotation form:\\n{e}",
                parent=self,
            )

    def _edit(self):
        if not self.selected_id:
            messagebox.showinfo("No selection",
                                "Select a customer first.",
                                parent=self)
            return

        customer = get_customer(self.selected_id) if get_customer else None
        if not customer:
            messagebox.showerror("Not found",
                                 "This customer could not be loaded.",
                                 parent=self)
            return

        dialog = CustomerEditDialog(self, customer=customer)
        self.wait_window(dialog)
        if dialog.result:
            self._reload()

    def _delete(self):
        if not self.selected_id:
            messagebox.showinfo("No selection",
                                "Select a customer first.",
                                parent=self)
            return

        customer = get_customer(self.selected_id) if get_customer else None
        label = (customer or {}).get("name") or (customer or {}).get("company") or "?"

        ok = messagebox.askyesno(
            "Delete customer",
            f"Delete this customer?\n\n{label}",
            parent=self,
        )
        if not ok:
            return

        if delete_customer and delete_customer(self.selected_id):
            self.selected_id = None
            self._reload()
        else:
            messagebox.showerror("Delete failed",
                                 "The customer could not be deleted.",
                                 parent=self)


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    CustomerDatabase(root)
    root.mainloop()