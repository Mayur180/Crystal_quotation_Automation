"""
Add 'Enter phone/email' prompt dialogs when missing.
"""

import shutil
import py_compile
from pathlib import Path


UI = Path("ui/quotation_history.py")
shutil.copy2(UI, UI.with_suffix(".py.PROMPT_BACKUP"))
print(f"[backup] {UI.name}")

s = UI.read_text(encoding="utf-8")


# ============================================================
# 1. Add _prompt_for_phone and _prompt_for_email methods
# ============================================================

NEW_METHODS = '''    def _prompt_for_phone(self, record):
        """Show a dialog asking for a phone number.

        Returns the entered phone (str) or None if cancelled.
        Also optionally saves to the customer DB.
        """
        dlg = tk.Toplevel(self)
        dlg.title("WhatsApp")
        dlg.geometry("420x260")
        dlg.configure(bg=self.BG)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(
            dlg, text="No phone number found.",
            bg=self.BG, fg=self.TEXT,
            font=("Arial", 11, "bold"),
        ).pack(padx=20, pady=(20, 8))

        tk.Label(
            dlg, text="Enter phone number:",
            bg=self.BG, fg=self.MUTED,
            font=("Arial", 9, "bold"), anchor="w",
        ).pack(fill="x", padx=20)

        phone_var = tk.StringVar()
        entry = tk.Entry(
            dlg, textvariable=phone_var,
            bg="white", fg=self.TEXT, relief="solid", bd=1,
            font=("Arial", 11), insertbackground=self.RED,
        )
        entry.pack(fill="x", padx=20, ipady=6, pady=(4, 12))
        entry.focus_set()

        save_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            dlg, text="Save to customer database",
            variable=save_var,
            bg=self.BG, activebackground=self.BG,
            selectcolor="white", fg=self.TEXT,
            font=("Arial", 9),
        ).pack(anchor="w", padx=20)

        result = {"value": None}

        def _ok():
            v = phone_var.get().strip()
            digits = "".join(c for c in v if c.isdigit())
            if not digits:
                messagebox.showwarning(
                    "WhatsApp", "Please enter a valid phone number.",
                    parent=dlg,
                )
                return
            result["value"] = digits
            if save_var.get():
                self._save_phone_to_customer(record, digits)
            dlg.destroy()

        def _cancel():
            result["value"] = None
            dlg.destroy()

        btns = tk.Frame(dlg, bg=self.BG)
        btns.pack(fill="x", padx=20, pady=(16, 20))

        tk.Button(
            btns, text="Cancel", command=_cancel,
            bg="white", fg=self.TEXT,
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right")

        tk.Button(
            btns, text="Send WhatsApp", command=_ok,
            bg=self.RED, fg="white",
            activebackground=self.RED, activeforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right", padx=(0, 8))

        dlg.bind("<Return>", lambda _e: _ok())
        dlg.bind("<Escape>", lambda _e: _cancel())

        self.wait_window(dlg)
        return result["value"]

    def _prompt_for_email(self, record):
        """Show a dialog asking for an email address.

        Returns the entered email (str) or None if cancelled.
        """
        dlg = tk.Toplevel(self)
        dlg.title("Email")
        dlg.geometry("440x260")
        dlg.configure(bg=self.BG)
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        tk.Label(
            dlg, text="No email address found.",
            bg=self.BG, fg=self.TEXT,
            font=("Arial", 11, "bold"),
        ).pack(padx=20, pady=(20, 8))

        tk.Label(
            dlg, text="Enter email address:",
            bg=self.BG, fg=self.MUTED,
            font=("Arial", 9, "bold"), anchor="w",
        ).pack(fill="x", padx=20)

        email_var = tk.StringVar()
        entry = tk.Entry(
            dlg, textvariable=email_var,
            bg="white", fg=self.TEXT, relief="solid", bd=1,
            font=("Arial", 11), insertbackground=self.RED,
        )
        entry.pack(fill="x", padx=20, ipady=6, pady=(4, 12))
        entry.focus_set()

        save_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            dlg, text="Save to customer database",
            variable=save_var,
            bg=self.BG, activebackground=self.BG,
            selectcolor="white", fg=self.TEXT,
            font=("Arial", 9),
        ).pack(anchor="w", padx=20)

        result = {"value": None}

        def _ok():
            v = email_var.get().strip()
            if "@" not in v:
                messagebox.showwarning(
                    "Email", "Please enter a valid email address.",
                    parent=dlg,
                )
                return
            result["value"] = v
            if save_var.get():
                self._save_email_to_customer(record, v)
            dlg.destroy()

        def _cancel():
            result["value"] = None
            dlg.destroy()

        btns = tk.Frame(dlg, bg=self.BG)
        btns.pack(fill="x", padx=20, pady=(16, 20))

        tk.Button(
            btns, text="Cancel", command=_cancel,
            bg="white", fg=self.TEXT,
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right")

        tk.Button(
            btns, text="Send Email", command=_ok,
            bg=self.RED, fg="white",
            activebackground=self.RED, activeforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right", padx=(0, 8))

        dlg.bind("<Return>", lambda _e: _ok())
        dlg.bind("<Escape>", lambda _e: _cancel())

        self.wait_window(dlg)
        return result["value"]

    def _save_phone_to_customer(self, record, phone):
        """Update the customer DB with this phone."""
        try:
            from app.services.customer_service import (
                find_duplicate, save_customer, list_customers,
            )
            name = (record.get("customer_name") or "").strip()
            company = (record.get("customer_company") or "").strip()

            # Try to find the customer
            existing = find_duplicate(name, company, "", "")
            if not existing:
                # Looser search — match by name only
                for c in list_customers():
                    if (c.get("name") or "").strip().lower() == name.lower():
                        existing = c
                        break

            if existing:
                existing["phone"] = phone
                save_customer(existing, existing.get("id"))
            else:
                # Create new customer
                save_customer({
                    "name": name,
                    "company": company,
                    "phone": phone,
                })
        except Exception:
            pass

    def _save_email_to_customer(self, record, email):
        """Update the customer DB with this email."""
        try:
            from app.services.customer_service import (
                find_duplicate, save_customer, list_customers,
            )
            name = (record.get("customer_name") or "").strip()
            company = (record.get("customer_company") or "").strip()

            existing = find_duplicate(name, company, "", "")
            if not existing:
                for c in list_customers():
                    if (c.get("name") or "").strip().lower() == name.lower():
                        existing = c
                        break

            if existing:
                existing["email"] = email
                save_customer(existing, existing.get("id"))
            else:
                save_customer({
                    "name": name,
                    "company": company,
                    "email": email,
                })
        except Exception:
            pass

'''

marker = "    def _send_whatsapp(self):"
if "_prompt_for_phone" not in s and marker in s:
    s = s.replace(marker, NEW_METHODS + marker, 1)
    print("[ok] prompt methods added")
elif "_prompt_for_phone" in s:
    print("[skip] already added")
else:
    print("[warn] _send_whatsapp anchor not found")


# ============================================================
# 2. Update _send_whatsapp to use the prompt when phone missing
# ============================================================

old_wa = '''        digits = "".join(ch for ch in raw_phone if ch.isdigit())
        if not digits:
            messagebox.showwarning(
                "WhatsApp",
                "No phone number saved for this customer.\\n\\n"
                "(Also checked the customer database — no match found.)",
                parent=self,
            )
            return'''

new_wa = '''        digits = "".join(ch for ch in raw_phone if ch.isdigit())
        if not digits:
            # Ask user for a phone number
            entered = self._prompt_for_phone(record)
            if not entered:
                return
            raw_phone = entered
            digits = entered

            # Update local record so subsequent operations see it
            record["customer_phone"] = entered'''

if old_wa in s:
    s = s.replace(old_wa, new_wa, 1)
    print("[ok] WhatsApp updated to prompt")
elif "_prompt_for_phone(record)" in s:
    print("[skip] WhatsApp already prompts")
else:
    print("[warn] WhatsApp anchor not found")


# ============================================================
# 3. Update _send_email to prompt when email missing
# ============================================================

old_em = '''        if not to_addr or "@" not in to_addr:
            messagebox.showwarning(
                "Email",
                "No email address saved for this customer.\\n\\n"
                "(Also checked the customer database — no match found.)",
                parent=self,
            )
            return'''

new_em = '''        if not to_addr or "@" not in to_addr:
            entered = self._prompt_for_email(record)
            if not entered:
                return
            to_addr = entered
            record["customer_email"] = entered'''

if old_em in s:
    s = s.replace(old_em, new_em, 1)
    print("[ok] Email updated to prompt")
elif "_prompt_for_email(record)" in s:
    print("[skip] Email already prompts")
else:
    print("[warn] Email anchor not found")


UI.write_text(s, encoding="utf-8")

print()
print("=" * 60)
print("Compile check")
print("=" * 60)
try:
    py_compile.compile(str(UI), doraise=True)
    print("[ok] ui/quotation_history.py compiles")
    print()
    print("Done. Test now.")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(UI.with_suffix(".py.PROMPT_BACKUP"), UI)
    print("[restore] reverted")
