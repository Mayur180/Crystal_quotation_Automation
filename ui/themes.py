"""
CRYSTAL / ARMATECH ASSOCIATES
Module theme definitions — v4.

Each module (VMM, Crystal, ...) has its own:
  - Accent colors (button highlights, borders)
  - Badge colors (the small module tag in the header)
  - Company tagline (shown in the header)
  - Display name

The dashboard reads these based on the active module.
"""

# ============================================================
# THEME DEFINITIONS
# ============================================================

THEMES = {
    "VMM": {
        "display_name":   "VMM",
        "company_name":   "ARMATECH ASSOCIATES",
        "tagline":        "Precision Measurement Technology",

        # Accent colors (used for buttons, highlights, borders)
        "primary":        "#C40000",
        "primary_dark":   "#980000",
        "primary_light":  "#FFF3F3",

        # Module badge in header (the pill-shaped tag)
        "badge_bg":       "#2C3E50",   # dark blue
        "badge_fg":       "#FFFFFF",
    },

    "Crystal": {
        "display_name":   "Crystal",
        "company_name":   "ARMATECH ASSOCIATES",
        "tagline":        "A Name With Magnetic Fame",

        # Accent colors — same red as VMM (Armatech brand)
        "primary":        "#C40000",
        "primary_dark":   "#980000",
        "primary_light":  "#FFF3F3",

        # Module badge in header
        "badge_bg":       "#C0392B",   # crystal red
        "badge_fg":       "#FFFFFF",
    },
}


# ============================================================
# PUBLIC API
# ============================================================

def get_theme(module_name: str) -> dict:
    """Return theme dict for a module. Falls back to VMM if unknown."""
    return THEMES.get(module_name, THEMES["VMM"])


def get_tagline(module_name: str) -> str:
    return get_theme(module_name).get("tagline", "")


def get_display_name(module_name: str) -> str:
    return get_theme(module_name).get("display_name", module_name)


def get_company_name(module_name: str) -> str:
    return get_theme(module_name).get("company_name", "ARMATECH ASSOCIATES")


def get_badge_colors(module_name: str) -> tuple:
    """Return (bg, fg) for the module badge."""
    t = get_theme(module_name)
    return (t.get("badge_bg", "#2C3E50"), t.get("badge_fg", "#FFFFFF"))
