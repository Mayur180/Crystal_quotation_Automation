"""Cleanup Phase 7 duplicates."""
from pathlib import Path

p = Path("ui/dashboard.py")
src = p.read_text(encoding="utf-8")

# ---- 1. Remove the badge from the top-right actions frame (keep only brand badge) ----
DUPLICATE_BADGE = '''        # ---- v4: Module badge + Logout button ----
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

SIMPLE_END = '''        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")'''

if DUPLICATE_BADGE in src:
    src = src.replace(DUPLICATE_BADGE, SIMPLE_END, 1)
    print("[OK] Removed duplicate badge + logout block")
else:
    print("[SKIP] Duplicate block not found")

# ---- 2. Fix the footer v3.0 -> v4.0 ----
src = src.replace("Quotation Manager   ·   v3.0", "Quotation Manager   ·   v4.0")
src = src.replace("Quotation Manager · v3.0", "Quotation Manager · v4.0")
src = src.replace("Quotation Manager  v3.0", "Quotation Manager  v4.0")
print("[OK] Footer version updated (if found)")

p.write_text(src, encoding="utf-8")
print("\n✅ Cleanup complete")
