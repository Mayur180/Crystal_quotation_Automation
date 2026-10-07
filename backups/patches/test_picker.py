"""Standalone test of the customer picker dialog."""
import tkinter as tk
from app.services.customer_service import list_customers

records = list_customers()
print(f"Loaded {len(records)} customers")

root = tk.Tk()
root.title("Picker test")
root.geometry("620x480")

tk.Label(root, text="SELECT A SAVED CUSTOMER",
         font=("Arial", 8, "bold")).pack(anchor="w", padx=22, pady=(18, 6))

listbox = tk.Listbox(root, font=("Arial", 10))
listbox.pack(fill="both", expand=True, padx=22, pady=(0, 12))

def customer_value(record, *keys):
    for key in keys:
        value = record.get(key, "")
        if value not in (None, ""):
            return str(value)
    return ""

for r in records:
    label = (
        f"{customer_value(r, 'name', 'contact_person')}  —  "
        f"{customer_value(r, 'company', 'company_name')}  —  "
        f"{customer_value(r, 'phone')}"
    )
    listbox.insert("end", label)

# Live feedback on selection
def show_selection(_e=None):
    sel = listbox.curselection()
    if sel:
        idx = sel[0]
        print(f"[clicked] row {idx}: {records[idx].get('name')}")

listbox.bind("<<ListboxSelect>>", show_selection)

btn_row = tk.Frame(root)
btn_row.pack(side="bottom", fill="x")

def apply_selection():
    sel = listbox.curselection()
    print(f"[Use Selected] selection = {sel}")
    if not sel:
        print("  → nothing selected (you must click a row first)")
        return
    record = records[sel[0]]
    print(f"  → would set:")
    print(f"      name:    {customer_value(record, 'name')}")
    print(f"      company: {customer_value(record, 'company')}")
    print(f"      phone:   {customer_value(record, 'phone')}")
    root.destroy()

tk.Button(btn_row, text="Cancel", command=root.destroy,
          width=14).pack(side="right", padx=(8, 22), pady=14)
tk.Button(btn_row, text="Use Selected", command=apply_selection,
          bg="#C40000", fg="white", width=18).pack(side="right", pady=14)

root.mainloop()
