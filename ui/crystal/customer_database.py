# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# CUSTOMER DATABASE — Modal window
#
# File:
#   ui/customer_database.py
# ============================================================

import os
import sys
import queue
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from ui.crystal import theme as T
from ui.crystal import widgets as W


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


def _friendly_ts(value):
    text = str(value or "").strip()
    if not text:
        return "—"
    try:
        from datetime import datetime
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text[:19], fmt).strftime("%d-%m-%Y %H:%M")
            except ValueError:
                continue
    except Exception:
        pass
    return text[:16].replace("T", " ")


# ============================================================
# EDIT DIALOG
# ============================================================

class CustomerEditDialog(tk.Toplevel):

    BG = T.BG
    CARD = T.SURFACE
    TEXT = T.TEXT
    MUTED = T.TEXT_MUTED
    BORDER = T.BORDER
    RED = T.ACCENT
    RED_DARK = T.ACCENT_DARK
    RED_LIGHT = T.ACCENT_SOFT
    SOFT = T.SURFACE_ALT

    def __init__(self, parent, customer=None):
        super().__init__(parent)

        self.result = None

        self.title("Edit Customer" if customer else "New Customer")
        self.withdraw()
        self.minsize(500, 480)
        self.configure(bg=T.SURFACE)
        W.set_window_icon(self)

        self.transient(parent)
        W.apply_ttk_theme(self)

        self.customer = customer or {}
        self.customer_id = self.customer.get("id")

        self.vars = {}
        self._build_interface()

        self.protocol("WM_DELETE_WINDOW", self._cancel)

        W.fit_toplevel(self, 620, min_height=780)
        self.deiconify()
        self.grab_set()

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
        header = tk.Frame(self, bg=T.SURFACE)
        header.pack(fill="x", padx=24, pady=(18, 0))

        tk.Label(header,
                 text=("Edit customer" if self.customer_id else "New customer"),
                 bg=T.SURFACE, fg=T.TEXT,
                 font=T.FONT_H2).pack(anchor="w")
        tk.Label(header,
                 text="Billing and contact details used on quotations.",
                 bg=T.SURFACE, fg=T.TEXT_MUTED,
                 font=T.FONT_SMALL).pack(anchor="w", pady=(2, 0))
        tk.Frame(self, bg=T.ACCENT, height=2).pack(fill="x", padx=24, pady=(12, 0))

        footer = tk.Frame(self, bg=T.SURFACE,
                          highlightbackground=T.BORDER,
                          highlightthickness=1)
        footer.pack(side="bottom", fill="x")

        W.GhostButton(
            footer, "Cancel", self._cancel, padx=16, pady=7,
        ).pack(side="right", padx=(8, 22), pady=13)
        W.PrimaryButton(
            footer, "Save customer", self._save, padx=18, pady=7,
        ).pack(side="right", pady=13)

        # Scrollable container
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(fill="both", expand=True)

        scroll_canvas = tk.Canvas(outer, bg=self.BG, highlightthickness=0, bd=0)
        scroll_bar = ttk.Scrollbar(outer, orient="vertical",
                                   command=scroll_canvas.yview)
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
            from ui.common.scroll_manager import ScrollManager
            ScrollManager.register(scroll_canvas, "vertical")
            self._scroll_canvas_for_cleanup = scroll_canvas
        except Exception:
            pass

        def _cleanup_wheel(event=None):
            if event is not None and event.widget is not self:
                return
            try:
                from ui.common.scroll_manager import ScrollManager
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
            ("Contact person",   "contact_person",   False),
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

            tk.Label(box, text=label, bg=T.SURFACE, fg=T.TEXT_BODY,
                     font=T.FONT_LABEL, width=16,
                     anchor="w").pack(side="left", anchor="n", pady=(8, 0))

            self.vars[key] = tk.StringVar(value=self.customer.get(key, "") or "")

            if multiline:
                wrap = tk.Frame(box, bg=T.BORDER_HARD)
                wrap.pack(side="left", fill="x", expand=True)
                inner_wrap = tk.Frame(wrap, bg=T.SURFACE)
                inner_wrap.pack(fill="both", expand=True, padx=1, pady=1)
                w = tk.Text(inner_wrap, height=3, bg=T.SURFACE, fg=T.TEXT,
                            bd=0, highlightthickness=0, font=T.FONT_BODY,
                            insertbackground=T.TEXT, wrap="word")
                w.pack(side="left", fill="both", expand=True,
                       padx=8, pady=6)
                w.insert("1.0", self.vars[key].get())
                self.vars[key + "_widget"] = w
            else:
                W.SearchEntry(
                    box, textvariable=self.vars[key],
                    placeholder="", show_icon=False,
                ).pack(side="left", fill="x", expand=True)

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

    BG = T.BG
    CARD = T.SURFACE
    TEXT = T.TEXT
    MUTED = T.TEXT_MUTED
    LIGHT_MUTED = T.TEXT_FAINT
    BORDER = T.BORDER
    RED = T.ACCENT
    RED_DARK = T.ACCENT_DARK
    RED_LIGHT = T.ACCENT_SOFT
    GREEN = T.SUCCESS
    SOFT = T.SURFACE_ALT

    def __init__(self, parent):
        super().__init__(parent)

        self.title("CRYSTAL | Customer Database")
        self.geometry("1180x720")
        self.minsize(1000, 600)
        self.configure(bg=self.BG)
        W.set_window_icon(self)

        self.transient(parent)
        self.grab_set()

        self.search_var = tk.StringVar()
        self.selected_id = None
        self._import_queue = queue.Queue()

        W.apply_ttk_theme(self)
        self._build_interface()
        self._reload()

        # ---- Keyboard shortcuts ----
        try:
            from ui.common.ui_helpers import (
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

    def _build_interface(self):
        header = W.PageHeader(
            self, title="Customer Database",
            subtitle="Customer and company records",
            meta="Loading…", padx=28,
        )
        header.pack(fill="x")
        self.count_label = header.meta_label

        toolbar = tk.Frame(self, bg=self.BG)
        toolbar.pack(fill="x", padx=28, pady=(14, 10))

        actions = tk.Frame(toolbar, bg=T.BG)
        actions.pack(side="right")
        W.PrimaryButton(
            actions, "New quotation",
            self._open_quotation_for_selected, padx=14, pady=7,
        ).pack(side="right")
        W.GhostButton(
            actions, "New proforma invoice",
            lambda: self._open_quotation_for_selected("proforma"),
            padx=12, pady=7,
        ).pack(side="right", padx=(0, 8))

        search = W.SearchEntry(
            toolbar, textvariable=self.search_var, width=30,
            placeholder="Search name, company, phone or email…",
            bg=self.CARD,
        )
        search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        search.entry.bind("<KeyRelease>", lambda e: self._reload(), add="+")

        self._build_footer()

        # Table
        card = tk.Frame(self, bg=self.CARD,
                        highlightbackground=self.BORDER,
                        highlightthickness=1)
        card.pack(fill="both", expand=True, padx=28, pady=(0, 12))

        cols = ("name", "company", "phone", "email", "last_used")
        self.tree = ttk.Treeview(card, columns=cols, show="headings",
                                 height=10)

        headings = {
            "name": "Name",
            "company": "Company",
            "phone": "Phone",
            "email": "Email",
            "last_used": "Last used",
        }
        widths = {
            "name": 220, "company": 260, "phone": 130,
            "email": 240, "last_used": 150,
        }

        for c in cols:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="w",
                             stretch=(c in ("company", "email")))

        self.tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        self.tree.tag_configure("oddrow", background=T.SURFACE)

        vsb = ttk.Scrollbar(card, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self.tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        self._empty = W.EmptyState(
            card, icon="👥", title="No customers found",
            hint="Adjust the search, or add a new customer.",
        )

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
        self._ctx_menu.add_command(
            label="New Proforma Invoice",
            command=lambda: self._open_quotation_for_selected("proforma"),
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

    def _build_footer(self):
        bar = tk.Frame(self, bg=self.CARD,
                       highlightbackground=self.BORDER,
                       highlightthickness=1)
        bar.pack(side="bottom", fill="x")

        left = tk.Frame(bar, bg=self.CARD)
        left.pack(side="left", padx=22, pady=15)

        W.PrimaryButton(
            left, "New customer", self._new, icon="+", padx=14, pady=7,
        ).pack(side="left")
        W.GhostButton(
            left, "Edit", self._edit, padx=12, pady=7,
        ).pack(side="left", padx=(8, 0))
        W.GhostButton(
            left, "View history", self._view_history, padx=12, pady=7,
        ).pack(side="left", padx=(8, 0))
        W.GhostButton(
            left, "Import Excel…", self._import_excel, padx=12, pady=7,
        ).pack(side="left", padx=(8, 0))
        W.DangerButton(
            left, "Delete", self._delete, padx=12, pady=7,
        ).pack(side="left", padx=(8, 0))

        right = tk.Frame(bar, bg=self.CARD)
        right.pack(side="right", padx=22, pady=15)
        W.GhostButton(
            right, "Close", self.destroy, padx=18, pady=7,
        ).pack(side="right")

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

        for idx, r in enumerate(records):
            self.tree.insert("", "end",
                             iid=r.get("id", ""),
                             values=(
                                 r.get("name", ""),
                                 r.get("company", ""),
                                 r.get("phone", ""),
                                 r.get("email", ""),
                                 _friendly_ts(r.get("last_used")),
                             ),
                             tags=("evenrow" if idx % 2 else "oddrow",))

        count = len(records)
        if self.count_label is not None:
            self.count_label.configure(
                text=f"{count:,} customer{'s' if count != 1 else ''}"
            )
        try:
            if count:
                self._empty.place_forget()
            else:
                self._empty.place(relx=0.5, rely=0.5, anchor="center")
                self._empty.lift()
        except Exception:
            pass

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        self.selected_id = sel[0] if sel else None

    def _new(self):
        dialog = CustomerEditDialog(self, customer=None)
        self.wait_window(dialog)
        if dialog.result:
            self._reload()

    def _import_excel(self):
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            parent=self,
            title="Import customers from Excel",
            filetypes=[("Excel workbook", "*.xlsx"), ("All files", "*.*")],
        )
        if not path:
            return

        busy = tk.Toplevel(self)
        busy.title("Importing customers")
        busy.geometry("440x160")
        busy.configure(bg=self.CARD)
        busy.transient(self)
        busy.grab_set()

        tk.Label(busy, text="Importing customers…", bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 12, "bold")).pack(pady=(22, 6))
        status = tk.Label(busy, text="Reading workbook and saving records…",
                          bg=self.CARD, fg=self.MUTED, font=("Arial", 9))
        status.pack()

        bar = ttk.Progressbar(busy, mode="indeterminate", length=340)
        bar.pack(pady=16)
        bar.start(12)

        def worker():
            try:
                from app.services.customer_import_service import (
                    import_customers_from_excel,
                )
                result = import_customers_from_excel(path, upload_cloud=True)
            except Exception as e:
                result = {"error": str(e)}
            self._import_queue.put(result)

        threading.Thread(target=worker, daemon=True).start()

        def poll():
            try:
                result = self._import_queue.get_nowait()
            except queue.Empty:
                self.after(120, poll)
                return

            try:
                bar.stop()
                busy.destroy()
            except Exception:
                pass

            if "error" in result:
                messagebox.showerror("Import failed", result["error"], parent=self)
                return

            self._reload()
            local = result.get("local") or {}
            cloud = result.get("cloud") or {}

            if cloud.get("error"):
                cloud_line = f"Google Sheet: failed ({cloud['error']})"
            elif cloud.get("supported") is False:
                cloud_line = ("Google Sheet: saved locally only — redeploy the "
                              "Apps Script to enable bulk upload.")
            else:
                cloud_line = (
                    f"Google Sheet: +{cloud.get('added', 0):,} new, "
                    f"{cloud.get('updated', 0):,} updated"
                )

            messagebox.showinfo(
                "Customers imported",
                "\n".join([
                    f"Rows found: {result.get('parsed', 0):,}",
                    f"New customers: {local.get('added', 0):,}",
                    f"Enriched: {local.get('updated', 0):,}",
                    f"Duplicates skipped: {local.get('skipped', 0):,}",
                    f"Total in database: {local.get('total', 0):,}",
                    "",
                    cloud_line,
                ]),
                parent=self,
            )

        poll()

    def _open_quotation_for_selected(self, doc_type="quotation"):
        """Open a New Quotation or Proforma form pre-filled from the selected customer."""
        doc_label = "Proforma Invoice" if str(doc_type).lower().startswith("prof") else "Quotation"
        if not self.selected_id:
            messagebox.showinfo(
                f"New {doc_label}",
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
                f"New {doc_label}",
                "Could not load the selected customer.",
                parent=self,
            )
            return

        try:
            from ui.crystal.quotation_form import QuotationForm
        except Exception as e:
            messagebox.showerror(
                f"New {doc_label}",
                f"Could not open Quotation form:\\n{e}",
                parent=self,
            )
            return

        try:
            QuotationForm(self.master, self, prefill=customer, doc_type=doc_type)
        except Exception as e:
            messagebox.showerror(
                f"New {doc_label}",
                f"Could not open Quotation form:\\n{e}",
                parent=self,
            )

    def _view_history(self):
        """Show the quotation history for the selected customer."""
        print("[history] _view_history called")
        import tkinter as tk
        from tkinter import ttk, messagebox
        
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("History", "Please select a customer first.", parent=self)
            return
        
        # Get the selected customer name
        values = self.tree.item(sel[0], "values")
        customer_name = str(values[0]).strip() if values else ""
        
        if not customer_name:
            messagebox.showerror("History", "Could not read customer name.", parent=self)
            return
        
        # Load quotations
        try:
            from app.services.quotation_history_service import list_quotations
            quotations = list_quotations() or []
        except Exception as e:
            messagebox.showerror("History", f"Could not load quotations: {e}", parent=self)
            return
        
        # Filter by customer name (case-insensitive)
        search_key = customer_name.strip().lower()
        customer_quotations = [
            q for q in quotations
            if str(q.get("customer_name", "")).strip().lower() == search_key
        ]
        
        # Calculate totals
        total_count = len(customer_quotations)
        total_value = 0.0
        for q in customer_quotations:
            try:
                total_value += float(str(q.get("grand_total", 0)).replace(",", "").replace("₹", "").strip() or 0)
            except Exception:
                pass
        
        # --- Build the popup ---
        popup = tk.Toplevel(self)
        popup.title(f"History: {customer_name}")
        popup.geometry("850x550")
        popup.configure(bg=self.BG)
        popup.transient(self)
        popup.grab_set()
        
        # Header
        tk.Label(popup, text=f"📋 History for {customer_name}", bg=self.BG, fg=self.TEXT,
                 font=("Arial", 16, "bold")).pack(pady=15)
        
        # Summary Stats
        stats_frame = tk.Frame(popup, bg=self.CARD, highlightbackground=self.BORDER, highlightthickness=1)
        stats_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(stats_frame, text=f"Total Quotations: {total_count}", bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 12, "bold")).pack(side="left", padx=20, pady=15)
        tk.Label(stats_frame, text=f"Total Business Value: ₹{total_value:,.2f}", bg=self.CARD, fg=self.RED,
                 font=("Arial", 12, "bold")).pack(side="right", padx=20, pady=15)
        
        # Quotation Table
        table_frame = tk.Frame(popup, bg=self.BG)
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        cols = ("number", "date", "model", "amount", "status")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)
        
        headings = {"number": "Quotation No.", "date": "Date", "model": "Model", "amount": "Amount", "status": "Status"}
        widths = {"number": 180, "date": 120, "model": 200, "amount": 150, "status": 100}
        
        for c in cols:
            tree.heading(c, text=headings[c])
            tree.column(c, width=widths[c], anchor="w")
        
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        
        if not customer_quotations:
            tree.insert("", "end", values=("No quotations found for this customer.", "", "", "", ""))
        else:
            for q in customer_quotations:
                try:
                    amount = f"₹{float(q.get('grand_total', 0)):,.2f}"
                except Exception:
                    amount = f"₹{q.get('grand_total', 0)}"
                tree.insert("", "end", values=(
                    q.get("quotation_number", "—"),
                    q.get("date", "—"),
                    q.get("model", "—"),
                    amount,
                    q.get("status", "—"),
                ))
        
        # Close button
        tk.Button(popup, text="Close", command=popup.destroy, bg=self.BG, fg=self.TEXT,
                  relief="flat", padx=20, pady=8).pack(pady=10)
        
        # Force popup to front
        popup.lift()
        popup.focus_force()
        popup.attributes('-topmost', True)
        popup.after(100, lambda: popup.attributes('-topmost', False))
        print(f"[history] Popup opened for {customer_name} with {total_count} quotations.")

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