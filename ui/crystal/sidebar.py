"""CRYSTAL — Sidebar widget (mockup C layout)."""
import tkinter as tk
from ui.crystal import theme as T


def get_nav_items(is_admin=False):
    items = [
        ("dashboard",   "◉",  "Dashboard",        "_go_dashboard"),
        ("quotes",      "📄", "Quotes",           "_go_quotes"),
        ("leads",       "🎯", "Leads",            "_go_leads"),
        ("products",    "📦", "Products",         "_go_products"),
        ("customers",   "👥", "Customers",        "_go_customers"),
        ("reports",     "📊", "Reports",          "_go_reports"),
    ]
    # Only add Users if the logged-in user is an admin
    if is_admin:
        items.append(("users", "👤", "Users", "_go_users"))
    
    items.append(("settings", "⚙", "Settings", "_go_settings"))
    return items


class Sidebar(tk.Frame):
    def __init__(self, parent, *, logo_text="CRYSTAL", active_key="dashboard",
                 on_navigate, on_quit, is_admin=False):
        super().__init__(parent, bg=T.SURFACE, width=T.SIDEBAR_WIDTH)
        self.pack_propagate(False)
        self._collapsed = False

        # right border
        tk.Frame(self, bg=T.BORDER, width=1).pack(side="right", fill="y")

        # ─── Logo ───
        logo_wrap = tk.Frame(self, bg=T.SURFACE)
        logo_wrap.pack(fill="x", padx=20, pady=(22, 26))
        tk.Label(logo_wrap, text=logo_text, bg=T.SURFACE, fg=T.ACCENT,
                 font=(T.FONT_FAMILY, 18, "bold")).pack(anchor="w")

        # ─── Nav items ───
        self._active_key = active_key
        self._items = {}

        nav_wrap = tk.Frame(self, bg=T.SURFACE)
        nav_wrap.pack(fill="x")

        for key, glyph, label, action in get_nav_items(is_admin):
            item = self._make_item(nav_wrap, key, glyph, label,
                                    getattr(on_navigate, "__call__", None) or (lambda k: None))
            self._items[key] = item

        # ─── Spacer ───
        tk.Frame(self, bg=T.SURFACE).pack(fill="both", expand=True)

        # ─── Divider ───
        tk.Frame(self, bg=T.BORDER, height=1).pack(fill="x", padx=16, pady=(8, 4))

        # ─── Logout ───
        self._logout = self._make_item(self, "_logout", "🚪", "Logout",
                                       lambda _k: on_quit(), danger=True)

        # ─── Quit App ───
        self._quit_app = self._make_item(self, "_quit_app", "⏻", "Quit App",
                                         lambda _k: _confirm_quit_app(),
                                         danger=True)

        # mark active
        self.set_active(active_key)

    def _make_item(self, parent, key, glyph, label, callback, danger=False):
        """Build one nav row. Returns a dict with refs so we can restyle it."""
        outer = tk.Frame(parent, bg=T.SURFACE, cursor="hand2")
        outer.pack(fill="x", padx=10, pady=2)

        # active left bar (invisible by default)
        bar = tk.Frame(outer, bg=T.SURFACE, width=3)
        bar.pack(side="left", fill="y")

        inner = tk.Frame(outer, bg=T.SURFACE)
        inner.pack(side="left", fill="both", expand=True, padx=(10, 12), pady=9)

        icon = tk.Label(inner, text=glyph, bg=T.SURFACE,
                        fg=T.ACCENT if danger else T.TEXT_BODY,
                        font=T.FONT_EMOJI, width=2, anchor="w")
        icon.pack(side="left")

        lbl = tk.Label(inner, text=label, bg=T.SURFACE,
                       fg=T.ACCENT if danger else T.NAV_TEXT,
                       font=T.FONT_BODY, anchor="w")
        lbl.pack(side="left", padx=(8, 0))

        refs = {"key": key, "outer": outer, "bar": bar, "inner": inner,
                "icon": icon, "label": lbl, "danger": danger,
                "active": False}

        def on_click(_e=None, k=key, cb=callback):
            cb(k)

        def on_enter(_e=None):
            if not refs["active"]:
                _paint(refs, T.NAV_HOVER_BG, T.TEXT_BODY,
                       T.ACCENT if danger else T.NAV_TEXT)

        def on_leave(_e=None):
            if not refs["active"]:
                _paint(refs, T.SURFACE, T.TEXT_BODY,
                       T.ACCENT if danger else T.NAV_TEXT)

        for w in (outer, inner, icon, lbl):
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

        return refs

    def set_active(self, key):
        for k, refs in self._items.items():
            _set_ref_active(refs, k == key)
        self._active_key = key

    def clear_active(self):
        for refs in self._items.values():
            _set_ref_active(refs, False)

    # ─────────────────────────────────────────────────────
    def toggle(self):
        """Collapse / expand the sidebar in place."""
        if self._collapsed:
            self.grid()
            self._collapsed = False
        else:
            self.grid_remove()
            self._collapsed = True


def _paint(refs, bg, icon_fg, text_fg):
    refs["outer"].configure(bg=bg)
    refs["inner"].configure(bg=bg)
    refs["icon"].configure(bg=bg, fg=icon_fg)
    refs["label"].configure(bg=bg, fg=text_fg)


def _set_ref_active(refs, on):
    refs["active"] = bool(on)
    if on:
        _paint(refs, T.NAV_ACTIVE_BG,
               T.NAV_ACTIVE_FG, T.NAV_ACTIVE_FG)
        refs["bar"].configure(bg=T.ACCENT)
    else:
        _paint(refs, T.SURFACE, T.TEXT_BODY,
               T.ACCENT if refs["danger"] else T.NAV_TEXT)
        refs["bar"].configure(bg=T.SURFACE)
