"""Phase C2.5: make quotation_form module-aware (tagline + fallback)."""
from pathlib import Path

p = Path("ui/quotation_form.py")
src = p.read_text(encoding="utf-8")

# ---------- CHANGE 1: Theme-driven tagline ----------
OLD_TAGLINE = '''        tk.Label(
            company,
            text="Precision Measurement Technology",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Arial", 9)
        ).pack(
            anchor="e"
        )'''

NEW_TAGLINE = '''        try:
            from ui.themes import get_tagline
            from app.services import paths as _paths
            _form_tagline = get_tagline(_paths.get_active_module())
        except Exception:
            _form_tagline = "Precision Measurement Technology"

        tk.Label(
            company,
            text=_form_tagline,
            bg=self.CARD,
            fg=self.MUTED,
            font=("Arial", 9)
        ).pack(
            anchor="e"
        )'''

if OLD_TAGLINE in src:
    src = src.replace(OLD_TAGLINE, NEW_TAGLINE, 1)
    print("[OK] Tagline made theme-driven")
else:
    print("[SKIP] Tagline block not found")

# ---------- CHANGE 2: Module-aware fallback categories ----------
OLD_FALLBACK = '''FALLBACK_CATEGORIES = [
    "Manual VMM",
    "Semi Automatic VMM",
    "Fully Automatic VMM",
    "Automatic VMM with Cabinet",
    "VMS",
]'''

NEW_FALLBACK = '''def _get_fallback_categories():
    """Return VMM fallback categories ONLY when VMM module is active.
    Crystal module gets NO fallback (user must add real products)."""
    try:
        from app.services import paths as _paths
        if _paths.get_active_module() == "VMM":
            return [
                "Manual VMM",
                "Semi Automatic VMM",
                "Fully Automatic VMM",
                "Automatic VMM with Cabinet",
                "VMS",
            ]
    except Exception:
        pass
    return []


FALLBACK_CATEGORIES = _get_fallback_categories()'''

if OLD_FALLBACK in src:
    src = src.replace(OLD_FALLBACK, NEW_FALLBACK, 1)
    print("[OK] Fallback categories made module-aware")
else:
    print("[SKIP] Fallback categories block not found")

p.write_text(src, encoding="utf-8")
print()
print("✅ quotation_form.py patched")
