"""
Phase 7 patch: Make dashboard module-aware + add Logout button.
"""
from pathlib import Path

p = Path("ui/dashboard.py")
src = p.read_text(encoding="utf-8")

# ---------- 1. Dynamic title ----------
OLD_TITLE = '''        self.title("CRYSTAL | ARMATECH ASSOCIATES — Quotation Manager  v3.0")'''

NEW_TITLE = '''        # v4: dynamic title based on active module
        try:
            from app.services import paths as _paths
            _mod = _paths.get_active_module()
        except Exception:
            _mod = "VMM"
        self._active_module = _mod
        self.title(
            f"CRYSTAL | ARMATECH ASSOCIATES — {_mod} Quotation Manager  v4.0"
        )'''

if OLD_TITLE in src:
    src = src.replace(OLD_TITLE, NEW_TITLE, 1)
    print("[OK] Title patched")
else:
    print("[SKIP] Title (already patched?)")

# ---------- 2. Add badge next to "CRYSTAL" brand ----------
OLD_BRAND_TAIL = '''        tk.Label(
            brand, text="  /  Quotation Manager", bg=self.CARD,
            fg=self.MUTED, font=("Arial", 11),
        ).pack(side="left", pady=26)'''

NEW_BRAND_TAIL = '''        tk.Label(
            brand, text="  /  Quotation Manager", bg=self.CARD,
            fg=self.MUTED, font=("Arial", 11),
        ).pack(side="left", pady=26)

        # v4: module badge
        _badge_colors = {
            "VMM": "#2C3E50",
            "Crystal": "#C0392B",
        }
        _mod = getattr(self, "_active_module", "VMM")
        _badge_bg = _badge_colors.get(_mod, self.RED)
        tk.Label(
            brand, text=f" {_mod} ",
            bg=_badge_bg, fg="white",
            font=("Arial", 9, "bold"),
        ).pack(side="left", pady=26, padx=(10, 0))'''

if OLD_BRAND_TAIL in src:
    src = src.replace(OLD_BRAND_TAIL, NEW_BRAND_TAIL, 1)
    print("[OK] Module badge added next to brand")
else:
    print("[SKIP] Brand tail (already patched?)")

# ---------- 3. Add logout button near date, in company block ----------
OLD_COMPANY_TAIL = '''        tk.Label(
            company,
            text=f"Today:  {date.today().strftime('%d %b %Y')}",
            bg=self.CARD, fg=self.LIGHT_MUTED, font=("Arial", 8),
        ).pack(anchor="e", pady=(2, 0))'''

NEW_COMPANY_TAIL = '''        _row = tk.Frame(company, bg=self.CARD)
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
                "Return to login screen?\\n\\n"
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
                _mb.showerror("Restart Failed", f"Could not restart app:\\n{e}")

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
        _row.winfo_children()[-1].bind("<Button-1>", lambda e: _do_logout())'''

if OLD_COMPANY_TAIL in src:
    src = src.replace(OLD_COMPANY_TAIL, NEW_COMPANY_TAIL, 1)
    print("[OK] Logout link added to header")
else:
    print("[SKIP] Company tail (already patched?)")

p.write_text(src, encoding="utf-8")
print("\n✅ Patch applied to ui/dashboard.py")
