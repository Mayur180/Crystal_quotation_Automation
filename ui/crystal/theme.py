"""CRYSTAL — Design System V2 (polished)."""

# ─── Surfaces ───
BG           = "#EEF1F5"      # slightly cooler background
BG_2         = "#E4E8EE"      # subtle gradient end
SURFACE      = "#FFFFFF"
SURFACE_ALT  = "#F7F9FC"
SURFACE_HOVER= "#F0F3F8"
BORDER       = "#DFE3E9"
BORDER_HARD  = "#C8CDD5"
SHADOW       = "#D6DAE1"      # fake shadow line
SHADOW_SOFT  = "#E8EBF0"

# ─── Text ───
TEXT         = "#0B1220"
TEXT_BODY    = "#414D60"
TEXT_MUTED   = "#7B8598"
TEXT_FAINT   = "#A6AEBC"
TEXT_INVERT  = "#FFFFFF"

# ─── Accent (Crystal Red) ───
ACCENT       = "#CC1032"
ACCENT_DARK  = "#A20D28"
ACCENT_DEEP  = "#7A091E"
ACCENT_SOFT  = "#FDECF0"
ACCENT_TINT  = "#FFF5F7"

# ─── Status ───
SUCCESS      = "#0EA55E"
SUCCESS_BG   = "#E8F8EF"
WARNING      = "#D97706"
WARNING_BG   = "#FFF6E5"
DANGER       = "#DC2626"
DANGER_BG    = "#FEECEC"
INFO         = "#2563EB"
INFO_BG      = "#EBF2FF"
NEUTRAL_BG   = "#F1F3F7"

# ─── Nav ───
NAV_BG        = "#FFFFFF"
NAV_TEXT      = "#414D60"
NAV_HOVER_BG  = "#F4F6FA"
NAV_ACTIVE_BG = ACCENT_SOFT
NAV_ACTIVE_FG = ACCENT

# ─── Typography (Segoe UI Variable on Win11, falls back gracefully) ───
FONT_FAMILY   = "Segoe UI Variable Display"
FONT_FAMILY_B = "Segoe UI Variable Text"
FONT_FAMILY_E = "Segoe UI Emoji"

FONT_DISPLAY  = (FONT_FAMILY, 28, "bold")
FONT_H1       = (FONT_FAMILY, 20, "bold")
FONT_H2       = (FONT_FAMILY, 15, "bold")
FONT_H3       = (FONT_FAMILY, 12, "bold")
FONT_KPI      = (FONT_FAMILY, 24, "bold")
FONT_BODY     = (FONT_FAMILY_B, 11)
FONT_BODY_B   = (FONT_FAMILY_B, 11, "bold")
FONT_SMALL    = (FONT_FAMILY_B, 10)
FONT_TINY     = (FONT_FAMILY_B, 9)
FONT_LABEL    = (FONT_FAMILY_B, 9, "bold")
FONT_EMOJI    = (FONT_FAMILY_E, 13)
FONT_EMOJI_LG = (FONT_FAMILY_E, 18)
FONT_ICON     = ("Segoe UI Symbol", 12)

# ─── Spacing ───
SP_XS, SP_SM, SP_MD, SP_LG, SP_XL, SP_2XL, SP_3XL = 4, 8, 16, 24, 32, 48, 64

# ─── Sizes ───
TOPBAR_HEIGHT = 60
SIDEBAR_WIDTH = 232
CARD_PADX     = 22
CARD_PADY     = 20
BUTTON_HEIGHT = 38
INPUT_HEIGHT  = 36
RADIUS        = 8

# ─── Shadow spec (fake with nested frames) ───
SHADOW_LAYERS = [
    # (offset_x, offset_y, color)
    (2, 2, SHADOW_SOFT),
    (1, 1, SHADOW),
]


# Focus ring
FOCUS = "#2563EB"    # subtle blue focus
