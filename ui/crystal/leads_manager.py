"""CRYSTAL — Leads Manager UI."""
import tkinter as tk
from tkinter import ttk, messagebox
from app.services import lead_service as LS
from ui.crystal import theme as T
from ui.crystal import widgets as W

class LeadsManager(tk.Toplevel):
    def __init__(self, parent, on_convert=None):
        super().__init__(parent)
        self.title("Customer Leads")
        self.geometry("1100x660")
        self.minsize(980, 560)
        self.configure(bg=T.BG)
        W.set_window_icon(self)
        self.transient(parent)
        self.grab_set()
        self._on_convert = on_convert

        W.apply_ttk_theme(self)
        self._build()
        self._refresh()

    def _build(self):
        header = W.PageHeader(
            self, title="Customer Leads",
            subtitle="Enquiries from calls, WhatsApp and email",
            meta="Loading…", padx=28,
        )
        header.pack(fill="x")
        self.count_label = header.meta_label

        toolbar = tk.Frame(self, bg=T.BG)
        toolbar.pack(fill="x", padx=28, pady=(14, 10))
        W.PrimaryButton(
            toolbar, "Log new lead", self._open_add_dialog,
            icon="+", padx=14, pady=7,
        ).pack(side="right")

        self._build_footer()

        card = tk.Frame(
            self, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=28, pady=(0, 12))

        columns = ("date", "customer", "phone", "email",
                   "qty", "source", "notes", "status")
        self.tree = ttk.Treeview(
            card, columns=columns, show="headings",
            selectmode="browse", height=10,
        )

        headings = {
            "date": "Date", "customer": "Customer", "phone": "Phone",
            "email": "Email", "qty": "Qty", "source": "Source",
            "notes": "Notes", "status": "Status",
        }
        widths = {
            "date": 100, "customer": 150, "phone": 115, "email": 185,
            "qty": 55, "source": 90, "notes": 240, "status": 90,
        }
        for col in columns:
            self.tree.heading(col, text=headings[col],
                              anchor="e" if col == "qty" else "w")
            self.tree.column(
                col, width=widths[col], minwidth=50,
                anchor="e" if col == "qty" else "w",
                stretch=(col == "notes"),
            )

        # Zebra striping keeps wide rows readable
        self.tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        self.tree.tag_configure("oddrow", background=T.SURFACE)

        vsb = ttk.Scrollbar(card, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 2), pady=2)
        self.tree.pack(side="left", fill="both", expand=True, padx=2, pady=2)

        self._empty = W.EmptyState(
            card, icon="📋", title="Loading leads…",
            hint="Fetching leads from the Google Sheet.",
        )

        self.tree.bind("<Double-1>", lambda _e: self._convert())

    def _build_footer(self):
        bar = tk.Frame(
            self, bg=T.SURFACE, height=68,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=T.SURFACE)
        left.pack(side="left", padx=22, pady=15)

        W.DangerButton(
            left, "Delete", self._delete_lead, padx=12, pady=7,
        ).pack(side="left")
        W.GhostButton(
            left, "Mark as sent", self._mark_sent, padx=12, pady=7,
        ).pack(side="left", padx=(8, 0))
        W.GhostButton(
            left, "Restore from sheet", self._restore_from_sheet,
            padx=12, pady=7,
        ).pack(side="left", padx=(8, 0))

        right = tk.Frame(bar, bg=T.SURFACE)
        right.pack(side="right", padx=22, pady=15)
        W.PrimaryButton(
            right, "Convert to quotation", self._convert,
            padx=16, pady=7,
        ).pack(side="right")

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        self._show_empty(True, "Loading leads…",
                         "Fetching leads from the Google Sheet.")

        import threading

        def fetch_data():
            try:
                leads = LS.load_leads()
                self.after(0, lambda: self._update_table(leads))
            except Exception as e:
                self.after(0, lambda: self._update_table([], str(e)))

        threading.Thread(target=fetch_data, daemon=True).start()

    def _show_empty(self, visible, title=None, hint=None):
        try:
            if visible:
                if title:
                    self._empty.set_text(title, hint)
                self._empty.place(relx=0.5, rely=0.5, anchor="center")
                self._empty.lift()
            else:
                self._empty.place_forget()
        except Exception:
            pass

    def _update_table(self, leads, error=None):
        self.tree.delete(*self.tree.get_children())

        if error:
            if self.count_label is not None:
                self.count_label.configure(text="Could not load leads")
            self._show_empty(
                True, "Could not load leads",
                "Check the connection, then use Restore from sheet.",
            )
            return

        for idx, lead in enumerate(leads):
            lead_id = lead.get("leadid") or lead.get("id") or ""
            if not lead_id or lead_id in self.tree.get_children():
                lead_id = f"row_{idx}_{lead_id}"

            qty = lead.get("qty") or lead.get("quantity") or ""

            self.tree.insert("", "end", iid=lead_id, values=(
                lead.get("date", ""), lead.get("customer", ""), lead.get("phone", ""),
                lead.get("email", ""), qty, lead.get("source", ""),
                lead.get("notes", ""), lead.get("status", "")
            ), tags=("evenrow" if idx % 2 else "oddrow",))

        count = len(leads)
        if self.count_label is not None:
            self.count_label.configure(
                text=f"{count:,} lead{'s' if count != 1 else ''}"
            )
        self._show_empty(
            not leads, "No leads yet",
            "Use Log new lead to capture an enquiry.",
        )

    def _mark_sent(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Leads", "Select a lead first.", parent=self)
            return
        try:
            if LS.mark_lead_sent(sel[0]):
                self._refresh()
                messagebox.showinfo("Success", "Lead marked as Sent.", parent=self)
            else:
                messagebox.showerror("Error", "Lead not found.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark sent: {e}", parent=self)


    def _restore_from_sheet(self):
        """Fetch the latest leads from Google Sheet and refresh the table."""
        from tkinter import messagebox
        import threading
        
        def do_restore():
            success = LS.restore_leads_from_sheet()
            if success:
                self.after(0, lambda: (self._refresh(), messagebox.showinfo("Restored", "Leads restored from Google Sheet.", parent=self)))
            else:
                self.after(0, lambda: messagebox.showerror("Error", "Could not fetch leads from Google Sheet.", parent=self))
                
        threading.Thread(target=do_restore, daemon=True).start()

    def _delete_lead(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Leads", "Select a lead first.", parent=self)
            return
        if messagebox.askyesno("Delete", "Are you sure you want to permanently delete this lead?", parent=self):
            if LS.delete_lead(sel[0]):
                self._refresh()

    def _convert(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Leads", "Select a lead first.", parent=self)
            return
        lead = next((l for l in LS.load_leads() if (l.get("leadid") or l.get("id")) == sel[0]), None)
        if lead and self._on_convert:
            self.destroy()
            self._on_convert(lead)

    def _open_add_dialog(self):
        LeadDialog(self, on_save=self._refresh)

class LeadDialog(tk.Toplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.title("Log New Lead")
        self.geometry("620x640")
        self.configure(bg=T.SURFACE)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        W.set_window_icon(self)
        self._on_save = on_save

        # Center the window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (620 // 2)
        y = (self.winfo_screenheight() // 2) - (640 // 2)
        self.geometry(f"+{x}+{y}")

        W.apply_ttk_theme(self)
        self._build()

    def _build(self):
        head = tk.Frame(self, bg=T.SURFACE)
        head.pack(fill="x", padx=24, pady=(18, 0))
        tk.Label(head, text="Log new lead", bg=T.SURFACE, fg=T.TEXT,
                 font=T.FONT_H2).pack(anchor="w")
        tk.Label(head, text="Capture an enquiry so it is not lost.",
                 bg=T.SURFACE, fg=T.TEXT_MUTED,
                 font=T.FONT_SMALL).pack(anchor="w", pady=(2, 0))
        tk.Frame(self, bg=T.ACCENT, height=2).pack(fill="x", padx=24, pady=(12, 0))

        self._build_footer()

        content = tk.Frame(self, bg=T.BG)
        content.pack(fill="both", expand=True, padx=24, pady=14)

        card = tk.Frame(
            content, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        card.pack(fill="both", expand=True)
        card.grid_columnconfigure(1, weight=1)

        self._customer_var = tk.StringVar()
        self._company_var = tk.StringVar()
        self._phone_var = tk.StringVar()
        self._email_var = tk.StringVar()
        self._qty_var = tk.StringVar(value="1")
        self._source_var = tk.StringVar(value="Other")
        self._notes_var = tk.StringVar()

        def add_field(row_idx, label_text, var, widget_type="entry", values=None):
            tk.Label(
                card, text=label_text, bg=T.SURFACE, fg=T.TEXT_BODY,
                font=T.FONT_LABEL, anchor="w",
            ).grid(row=row_idx, column=0, sticky="w", padx=(20, 14), pady=(11, 0))

            if widget_type == "entry":
                widget = W.SearchEntry(
                    card, textvariable=var, placeholder="", show_icon=False,
                )
            else:
                widget = ttk.Combobox(
                    card, textvariable=var, values=values,
                    state="readonly", font=T.FONT_BODY,
                )
            widget.grid(row=row_idx, column=1, sticky="ew",
                        padx=(0, 20), pady=(11, 0))
            return widget

        customer_entry = add_field(0, "Customer name *", self._customer_var)
        add_field(1, "Company", self._company_var)
        add_field(2, "Phone", self._phone_var)
        add_field(3, "Email", self._email_var)
        add_field(4, "Quantity", self._qty_var)
        add_field(5, "Source", self._source_var, widget_type="combobox",
                  values=["Gmail", "WhatsApp", "Call", "Website", "Other"])

        tk.Label(
            card, text="Notes", bg=T.SURFACE, fg=T.TEXT_BODY,
            font=T.FONT_LABEL, anchor="w",
        ).grid(row=6, column=0, sticky="nw", padx=(20, 14), pady=(11, 0))

        notes_wrap = tk.Frame(card, bg=T.BORDER_HARD)
        notes_wrap.grid(row=6, column=1, sticky="ew",
                        padx=(0, 20), pady=(11, 16))
        notes_inner = tk.Frame(notes_wrap, bg=T.SURFACE)
        notes_inner.pack(fill="both", expand=True, padx=1, pady=1)
        self._notes_text = tk.Text(
            notes_inner, height=5, font=T.FONT_BODY,
            bg=T.SURFACE, fg=T.TEXT, bd=0, highlightthickness=0,
            insertbackground=T.TEXT, wrap="word",
        )
        self._notes_text.pack(side="left", fill="both", expand=True,
                              padx=8, pady=6)
        notes_scroll = ttk.Scrollbar(notes_inner, orient="vertical",
                                     command=self._notes_text.yview)
        self._notes_text.configure(yscrollcommand=notes_scroll.set)
        notes_scroll.pack(side="right", fill="y")

        customer_entry.entry.focus_set()

    def _build_footer(self):
        bar = tk.Frame(self, bg=T.SURFACE, height=64,
                       highlightbackground=T.BORDER, highlightthickness=1)
        bar.pack(side="bottom", fill="x")
        bar.pack_propagate(False)

        W.GhostButton(
            bar, "Cancel", self.destroy, padx=16, pady=7,
        ).pack(side="right", padx=(8, 22), pady=13)
        W.PrimaryButton(
            bar, "Save lead", self._save, padx=18, pady=7,
        ).pack(side="right", pady=13)

    def _save(self):
        from tkinter import messagebox
        customer = self._customer_var.get().strip()
        if not customer:
            messagebox.showwarning("Required", "Please enter a customer name.", parent=self)
            return

        from app.services import lead_service as LS
        try:
            LS.add_lead(
                customer=customer,
                company=self._company_var.get().strip(),
                phone=self._phone_var.get().strip(),
                email=self._email_var.get().strip(),
                qty=self._qty_var.get().strip() or "1",
                source=self._source_var.get(),
                notes=self._notes_text.get("1.0", "end").strip()
            )
            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save lead: {e}", parent=self)
