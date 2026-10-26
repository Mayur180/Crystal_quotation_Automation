"""CRYSTAL — Leads Manager UI."""
import tkinter as tk
from tkinter import ttk, messagebox
from app.services import lead_service as LS
from ui.crystal import theme as T

class LeadsManager(tk.Toplevel):
    def __init__(self, parent, on_convert=None):
        super().__init__(parent)
        self.title("Customer Leads")
        self.geometry("1100x650")
        self.configure(bg=T.BG)
        self.transient(parent)
        self.grab_set()
        self._on_convert = on_convert
        
        self._build()
        self._refresh()

    def _build(self):
        hdr = tk.Frame(self, bg=T.SURFACE); hdr.pack(fill="x")
        tk.Label(hdr, text="Customer Leads", bg=T.SURFACE, fg=T.TEXT, font=("Arial", 18, "bold")).pack(side="left", padx=24, pady=20)
        tk.Button(hdr, text="+ Log New Lead", bg=T.ACCENT, fg="white", font=("Arial", 11, "bold"), relief="flat", padx=15, pady=8, cursor="hand2", command=self._open_add_dialog).pack(side="right", padx=24)

        # Table Frame
        table_frame = tk.Frame(self, bg=T.BG)
        table_frame.pack(fill="both", expand=True, padx=24, pady=10)

        columns = ("date", "customer", "phone", "email", "qty", "source", "notes", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        # Configure columns
        widths = {"date": 100, "customer": 150, "phone": 120, "email": 180, "qty": 60, "source": 100, "notes": 250, "status": 100}
        for col in columns:
            self.tree.heading(col, text=col.title())
            self.tree.column(col, width=widths[col], anchor="w")
            
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Bottom Action Bar
        bar = tk.Frame(self, bg=T.SURFACE)
        bar.pack(fill="x", side="bottom")
        tk.Frame(bar, bg=T.BORDER, height=1).pack(fill="x")

        btn_wrap = tk.Frame(bar, bg=T.SURFACE)
        btn_wrap.pack(fill="x", padx=24, pady=15)

        tk.Button(btn_wrap, text="🗑 Delete", bg="#D32F2F", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=15, pady=8, command=self._delete_lead).pack(side="left")
        tk.Button(btn_wrap, text="Mark as Sent", bg=T.BG, fg=T.TEXT, font=("Arial", 10, "bold"), relief="flat", padx=15, pady=8, command=self._mark_sent).pack(side="left", padx=10)
        
        # Add the Restore button
        tk.Button(btn_wrap, text="☁ Restore from Sheet", bg="#0277BD", fg="white", font=("Arial", 10, "bold"), relief="flat", padx=15, pady=8, command=self._restore_from_sheet).pack(side="left", padx=10)
        
        tk.Button(btn_wrap, text="Convert to Quotation →", bg=T.ACCENT, fg="white", font=("Arial", 11, "bold"), relief="flat", padx=20, pady=8, command=self._convert).pack(side="right")

    def _refresh(self):
        # Clear table and show loading
        self.tree.delete(*self.tree.get_children())
        self.tree.insert("", "end", iid="loading", values=("Loading...", "", "", "", "", "", "", ""))
        
        import threading
        
        def fetch_data():
            try:
                leads = LS.load_leads()
                # Schedule UI update on main thread
                self.after(0, lambda: self._update_table(leads))
            except Exception as e:
                self.after(0, lambda: self._update_table([], str(e)))

        threading.Thread(target=fetch_data, daemon=True).start()

    def _update_table(self, leads, error=None):
        self.tree.delete(*self.tree.get_children())
        if error:
            self.tree.insert("", "end", values=(f"Error: {error}", "", "", "", "", "", "", ""))
            return
            
        for lead in leads:
            lead_id = lead.get("leadid") or lead.get("id") or ""
            
            # Handle both "qty" and "quantity" keys
            qty = lead.get("qty") or lead.get("quantity") or ""
            
            self.tree.insert("", "end", iid=lead_id, values=(
                lead.get("date", ""), lead.get("customer", ""), lead.get("phone", ""),
                lead.get("email", ""), qty, lead.get("source", ""),
                lead.get("notes", ""), lead.get("status", "")
            ))

    def _mark_sent(self):
        sel = self.tree.selection()
        if not sel: return
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
        if not sel: return
        if messagebox.askyesno("Delete", "Are you sure you want to permanently delete this lead?", parent=self):
            if LS.delete_lead(sel[0]):
                self._refresh()

    def _convert(self):
        sel = self.tree.selection()
        if not sel: return
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
        self.geometry("600x700")
        self.configure(bg="#F4F6F8")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._on_save = on_save
        
        # Center the window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"+{x}+{y}")

        self._build()

    def _build(self):
        # Header
        header = tk.Frame(self, bg="#FFFFFF", height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="Log New Lead", bg="#FFFFFF", fg="#2C3E50", font=("Arial", 18, "bold")).pack(side="left", padx=24, pady=20)
        tk.Frame(self, bg="#E0E0E0", height=1).pack(fill="x")

        # Main content area
        content = tk.Frame(self, bg="#F4F6F8")
        content.pack(fill="both", expand=True, padx=30, pady=20)
        content.grid_columnconfigure(1, weight=1)

        # Helper function to create a field row
        def add_field(row_idx, label_text, var, widget_type="entry", values=None):
            tk.Label(content, text=label_text, bg="#F4F6F8", fg="#2C3E50", font=("Arial", 10, "bold"), anchor="w").grid(row=row_idx, column=0, sticky="w", padx=(0, 15), pady=(10, 2))
            
            if widget_type == "entry":
                widget = tk.Entry(content, textvariable=var, font=("Arial", 11), relief="solid", bd=1)
            elif widget_type == "combobox":
                widget = ttk.Combobox(content, textvariable=var, values=values, state="readonly", font=("Arial", 11))
            
            widget.grid(row=row_idx, column=1, sticky="ew", pady=(10, 2))
            return widget

        # Variables
        self._customer_var = tk.StringVar()
        self._company_var = tk.StringVar()
        self._phone_var = tk.StringVar()
        self._email_var = tk.StringVar()
        self._qty_var = tk.StringVar(value="1")
        self._source_var = tk.StringVar(value="Other")
        self._notes_var = tk.StringVar()

        # Fields
        add_field(0, "Customer Name *", self._customer_var)
        add_field(1, "Company Name", self._company_var)
        add_field(2, "Phone", self._phone_var)
        add_field(3, "Email", self._email_var)
        add_field(4, "Quantity", self._qty_var)
        add_field(5, "Source", self._source_var, widget_type="combobox", values=["Gmail", "WhatsApp", "Call", "Website", "Other"])

        # Notes (larger text area)
        tk.Label(content, text="Notes (What did they ask for?)", bg="#F4F6F8", fg="#2C3E50", font=("Arial", 10, "bold"), anchor="w").grid(row=6, column=0, sticky="nw", padx=(0, 15), pady=(10, 2))
        notes_frame = tk.Frame(content, bg="#F4F6F8")
        notes_frame.grid(row=6, column=1, sticky="ew", pady=(10, 2))
        
        self._notes_text = tk.Text(notes_frame, height=5, font=("Arial", 11), relief="solid", bd=1)
        self._notes_text.pack(fill="x")
        
        # Notes scrollbar
        notes_scroll = ttk.Scrollbar(notes_frame, orient="vertical", command=self._notes_text.yview)
        self._notes_text.configure(yscrollcommand=notes_scroll.set)
        notes_scroll.pack(side="right", fill="y")

        # Bottom Action Bar
        btn_bar = tk.Frame(self, bg="#FFFFFF", height=60)
        btn_bar.pack(fill="x", side="bottom")
        btn_bar.pack_propagate(False)
        tk.Frame(self, bg="#E0E0E0", height=1).pack(fill="x", side="bottom")

        tk.Button(btn_bar, text="Save Lead", bg="#C40000", fg="white", font=("Arial", 11, "bold"), relief="flat", cursor="hand2", padx=20, pady=5, command=self._save).pack(side="right", padx=24, pady=10)
        tk.Button(btn_bar, text="Cancel", bg="#E0E0E0", fg="#333", font=("Arial", 11), relief="flat", cursor="hand2", padx=20, pady=5, command=self.destroy).pack(side="right", padx=(0, 10), pady=10)

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
