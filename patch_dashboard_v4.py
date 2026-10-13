"""
Phase 7 patch: Make dashboard module-aware + add Logout button.
Safe, additive changes only. No existing behavior modified.
"""
from pathlib import Path

p = Path("ui/dashboard.py")
src = p.read_text(encoding="utf-8")

# ============================================================
# CHANGE 1: Dynamic title in __init__
# ============================================================

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
    print("[SKIP] Title line not found — may already be patched")

# ============================================================
# CHANGE 2: Add module badge + Logout button to header
# ============================================================

OLD_HEADER_END = '''        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")'''

NEW_HEADER_END = '''        # ---- v4: Module badge + Logout button ----
        actions = tk.Frame(header, bg=self.CARD)
        actions.pack(side="right", padx=(0, 34))

        # Module badge
        badge_colors = {
            "VMM": ("#2C3E50", "#34495E"),
            "Crystal": ("#C0392B", "#A93226"),
        }
        badge_bg, _ = badge_colors.get(
            getattr(self, "_active_module", "VMM"),
            (self.RED, self.RED_DARK),
        )

        badge = tk.Label(
            actions,
            text=f"  {getattr(self, '_active_module', 'VMM')}  ",
            bg=badge_bg, fg="white",
            font=("Arial", 10, "bold"),
            padx=10, pady=4,
        )
        badge.pack(side="left", padx=(0, 12))

        # Logout / Switch Module button
        def _do_logout():
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
            # Restart the v4 flow
            try:
                import main as _main
                _main.main()
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Restart Failed",
                    f"Could not restart app:\\n{e}")

        logout_btn = tk.Button(
            actions, text="Logout",
            bg=self.CARD, fg=self.MUTED,
            activebackground=self.SOFT, activeforeground=self.TEXT,
            relief="flat", bd=0, cursor="hand2",
            font=("Arial", 10),
            command=_do_logout,
        )
        logout_btn.pack(side="left")

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")'''

if OLD_HEADER_END in src:
    src = src.replace(OLD_HEADER_END, NEW_HEADER_END, 1)
    print("[OK] Header patched (badge + logout)")
else:
    print("[SKIP] Header end line not found — may already be patched")

# ============================================================
# Write back
# ============================================================

p.write_text(src, encoding="utf-8")
print("\n✅ Patch applied to ui/dashboard.py")
print("   Backup: ui/dashboard.py.bak_before_v4_polish")
