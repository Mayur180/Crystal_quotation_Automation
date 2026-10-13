"""
Phase C1 patch: Use ui/themes.py for module-aware tagline + badge.
Safe, additive-only changes.
"""
from pathlib import Path

p = Path("ui/dashboard.py")
src = p.read_text(encoding="utf-8")
changes = []

# ---------- CHANGE 1: Hardcoded tagline ----------
OLD_TAGLINE = '''        tk.Label(
            company, text="Precision Measurement Technology",
            bg=self.CARD, fg=self.MUTED, font=("Arial", 9),
        ).pack(anchor="e")'''

NEW_TAGLINE = '''        # v4 C1: theme-driven tagline
        try:
            from ui.themes import get_tagline
            _tagline = get_tagline(getattr(self, "_active_module", "VMM"))
        except Exception:
            _tagline = "Precision Measurement Technology"
        tk.Label(
            company, text=_tagline,
            bg=self.CARD, fg=self.MUTED, font=("Arial", 9),
        ).pack(anchor="e")'''

if OLD_TAGLINE in src:
    src = src.replace(OLD_TAGLINE, NEW_TAGLINE, 1)
    changes.append("tagline")
else:
    print("[SKIP] tagline — string not found (may be already patched)")

# ---------- CHANGE 2: Hardcoded badge color dict ----------
OLD_BADGE_DICT = '''        _badge_colors = {
            "VMM": "#2C3E50",
            "Crystal": "#C0392B",
        }
        _mod = getattr(self, "_active_module", "VMM")
        _badge_bg = _badge_colors.get(_mod, self.RED)'''

NEW_BADGE_DICT = '''        # v4 C1: theme-driven badge color
        try:
            from ui.themes import get_badge_colors
            _mod = getattr(self, "_active_module", "VMM")
            _badge_bg, _badge_fg = get_badge_colors(_mod)
        except Exception:
            _badge_bg = self.RED
            _badge_fg = "white"'''

if OLD_BADGE_DICT in src:
    src = src.replace(OLD_BADGE_DICT, NEW_BADGE_DICT, 1)
    changes.append("badge_bg")
else:
    print("[SKIP] badge dict — string not found (may be already patched)")

# ---------- CHANGE 3: Badge label fg color ----------
OLD_BADGE_FG = '''        tk.Label(
            brand, text=f" {_mod} ",
            bg=_badge_bg, fg="white",
            font=("Arial", 9, "bold"),
        ).pack(side="left", pady=26, padx=(10, 0))'''

NEW_BADGE_FG = '''        tk.Label(
            brand, text=f" {_mod} ",
            bg=_badge_bg, fg=_badge_fg,
            font=("Arial", 9, "bold"),
        ).pack(side="left", pady=26, padx=(10, 0))'''

if OLD_BADGE_FG in src:
    src = src.replace(OLD_BADGE_FG, NEW_BADGE_FG, 1)
    changes.append("badge_fg")
else:
    print("[SKIP] badge fg — string not found (may be already patched)")

# Write back
p.write_text(src, encoding="utf-8")

print()
print(f"✅ Patch applied — {len(changes)} changes:")
for c in changes:
    print(f"   • {c}")
print(f"\n   Backup: ui/dashboard.py.bak_before_c1")
