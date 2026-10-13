"""
CRYSTAL / ARMATECH ASSOCIATES
Module theme + tile definitions — v4 (Phase R-A).

Each module (VMM, Crystal, ...) declares:
  - Branding:   display_name, company_name, tagline, logo_text
  - Colors:     primary, primary_dark, primary_light, badge_bg, badge_fg
  - Layout:     tiles[] — ordered list of dashboard cards

The dashboard renders purely from this config. Adding a module or
changing a tile list never requires touching dashboard.py.
"""

# ============================================================
# THEME + TILE DEFINITIONS
# ============================================================

# Common tile builder — most tiles share the same fields.
def _tile(key, label, sub, action, *, primary=False, count_key=None,
          icon=None, group="primary"):
    return {
        "key":       key,
        "label":     label,
        "sub":       sub,
        "action":    action,
        "primary":   primary,     # styled as the standout CTA
        "count_key": count_key,   # if set, dashboard replaces "{n}" in sub
        "icon":      icon,        # emoji / glyph shown on the sidebar row
        "group":     group,       # "primary" | "secondary" — controls spacing
    }


THEMES = {
    # ────────────────────────────────────────────────────────
    # VMM
    # ────────────────────────────────────────────────────────
    "VMM": {
        "display_name":   "VMM",
        "company_name":   "ARMATECH ASSOCIATES",
        "tagline":        "Precision Measurement Technology",
        "logo_text":      "VMM",

        "primary":        "#C40000",
        "primary_dark":   "#980000",
        "primary_light":  "#FFF3F3",

        "badge_bg":       "#2C3E50",
        "badge_fg":       "#FFFFFF",

        "tiles": [
            _tile("new_quotation", "New Quotation",
                  "Create a fresh quote",
                  "quotation_form", primary=True, icon="📄", group="primary"),
            _tile("history",       "Quotation History",
                  "{n} quotes",
                  "quotation_history", count_key="quotation_count", icon="📋", group="primary"),
            _tile("activity",      "Activity Log",
                  "User actions",
                  "activity_log", icon="📝", group="primary"),
            _tile("report",        "Monthly Report",
                  "Sales summary",
                  "monthly_report", icon="📊", group="primary"),
            _tile("customers",     "Customers",
                  "{n} buyers",
                  "customer_database", count_key="customer_count", icon="👥", group="secondary"),
            _tile("products",      "Products & Prices",
                  "{n} products",
                  "product_manager",  count_key="product_count", icon="📦", group="secondary"),
            _tile("quotations_sheet", "Quotations (Sheet)",
                  "Spreadsheet view",
                  "quotations_browser", icon="📋", group="secondary"),
            _tile("settings",      "Company Settings",
                  "Address, GST, terms",
                  "company_settings", icon="⚙", group="secondary"),
            _tile("backup",        "Backup & Export",
                  "Save or restore",
                  "backup_export", icon="💾", group="secondary"),
        ],
    },

    # ────────────────────────────────────────────────────────
    # Crystal
    # ────────────────────────────────────────────────────────
    "Crystal": {
        "display_name":   "Crystal",
        "company_name":   "ARMATECH ASSOCIATES",
        "tagline":        "A Name With Magnetic Fame",
        "logo_text":      "CRYSTAL",

        "primary":        "#C40000",
        "primary_dark":   "#980000",
        "primary_light":  "#FFF3F3",

        "badge_bg":       "#C0392B",
        "badge_fg":       "#FFFFFF",

        "tiles": [
            _tile("new_quotation", "New Quotation",
                  "Create a fresh quote",
                  "quotation_form", primary=True, icon="📄", group="primary"),
            _tile("history",       "Quotation History",
                  "{n} quotes",
                  "quotation_history", count_key="quotation_count", icon="📋", group="primary"),
            _tile("activity",      "Activity Log",
                  "User actions",
                  "activity_log", icon="📝", group="primary"),
            _tile("report",        "Monthly Report",
                  "Sales summary",
                  "monthly_report", icon="📊", group="primary"),
            _tile("accessories",   "Accessories",
                  "{n} add-ons",
                  "accessories_manager", count_key="accessory_count", icon="🔧", group="secondary"),
            _tile("customers",     "Customers",
                  "{n} buyers",
                  "customer_database", count_key="customer_count", icon="👥", group="secondary"),
            _tile("products",      "Products & Prices",
                  "{n} products",
                  "product_manager",  count_key="product_count", icon="📦", group="secondary"),
            _tile("quotations_sheet", "Quotations (Sheet)",
                  "Spreadsheet view",
                  "quotations_browser", icon="📋", group="secondary"),
            _tile("settings",      "Company Settings",
                  "Address, GST, terms",
                  "company_settings", icon="⚙", group="secondary"),
            _tile("backup",        "Backup & Export",
                  "Save or restore",
                  "backup_export", icon="💾", group="secondary"),
        ],
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


def get_tiles(module_name: str) -> list:
    """Return the ordered tile list for a module."""
    return list(get_theme(module_name).get("tiles", []))


def get_logo_text(module_name: str) -> str:
    return get_theme(module_name).get("logo_text", get_display_name(module_name))
