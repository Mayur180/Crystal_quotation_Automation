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
    def __init__(self, parent, on_save):
        super().__init__(parent)
        self.title("Log New Lead")
        self.geometry("420x620")
        self.configure(bg=T.SURFACE)
        self.grab_set()
        self._on_save = on_save
        
        wrap = tk.Frame(self, bg=T.SURFACE); wrap.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Variables
        self.var_cust = tk.StringVar() # Customer Name
        self.var_comp = tk.StringVar() # Company Name
        self.var_phone = tk.StringVar()
        self.var_email = tk.StringVar()
        self.var_qty = tk.StringVar(value="1")
        self.var_src = tk.StringVar(value="WhatsApp")
        
        def _lbl(text):
            tk.Label(wrap, text=text, bg=T.SURFACE, fg=T.TEXT, font=("Arial", 9, "bold")).pack(anchor="w", pady=(8, 2))
            
        _lbl("Customer Name")
        tk.Entry(wrap, textvariable=self.var_cust).pack(fill="x", ipady=4)
        
        _lbl("Company Name")
        tk.Entry(wrap, textvariable=self.var_comp).pack(fill="x", ipady=4)
        
        _lbl("Phone")
        tk.Entry(wrap, textvariable=self.var_phone).pack(fill="x", ipady=4)
        
        _lbl("Email")
        tk.Entry(wrap, textvariable=self.var_email).pack(fill="x", ipady=4)
        
        _lbl("Quantity")
        tk.Entry(wrap, textvariable=self.var_qty).pack(fill="x", ipady=4)
        
        _lbl("Source")
        ttk.Combobox(wrap, textvariable=self.var_src, values=["WhatsApp", "Gmail", "Call", "Other"], state="readonly").pack(fill="x")
        
        _lbl("Notes (What did they ask for?)")
        self.txt_notes = tk.Text(wrap, height=4, font=("Arial", 10))
        self.txt_notes.pack(fill="x")
        
        tk.Button(wrap, text="Save Lead", bg=T.ACCENT, fg="white", font=("Arial", 10, "bold"), relief="flat", command=self._save).pack(fill="x", pady=25)

    def _save(self):
        cust = self.var_cust.get().strip()
        if not cust:
            messagebox.showerror("Error", "Customer Name is required", parent=self)
            return
        
        notes = self.txt_notes.get("1.0", "end").strip()
        
        LS.add_lead(
            customer=cust, 
            company=self.var_comp.get().strip(),
            phone=self.var_phone.get().strip(), 
            email=self.var_email.get().strip(), 
            qty=self.var_qty.get().strip(), 
            source=self.var_src.get(), 
            notes=notes
        )
        self._on_save()
        self.destroy()
