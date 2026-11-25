"""CRYSTAL — Widget Library V2 (polished)."""
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from ui.crystal import theme as T


# ═══════════════════════════════════════════════════════════
# SHADOW HELPER — fake depth with nested frames
# ═══════════════════════════════════════════════════════════

class ShadowedFrame(tk.Frame):
    """A frame that looks like it has a drop shadow."""
    def __init__(self, parent, *, bg=T.SURFACE, radius=1, **kw):
        super().__init__(parent, bg=T.BG, **kw)
        # Soft outer layer
        tk.Frame(self, bg=T.SHADOW_SOFT, height=1).pack(fill="x", side="bottom")
        tk.Frame(self, bg=T.SHADOW_SOFT, width=1).pack(fill="y", side="right")
        # Inner content
        self.inner = tk.Frame(self, bg=bg)
        self.inner.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1))


# ═══════════════════════════════════════════════════════════
# CARD — polished surface with optional accent bar + hover lift
# ═══════════════════════════════════════════════════════════

class Card(tk.Frame):
    def __init__(self, parent, *, title=None, subtitle=None,
                 padx=T.CARD_PADX, pady=T.CARD_PADY,
                 accent_bar=None, hover_lift=False, **kw):
        super().__init__(parent, bg=T.SHADOW_SOFT, **kw)

        # inner white surface, 1px inset to create shadow border
        self._inner = tk.Frame(self, bg=T.SURFACE)
        self._inner.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1))

        # optional accent left bar
        if accent_bar:
            bar = tk.Frame(self._inner, bg=accent_bar, width=4)
            bar.pack(side="left", fill="y")

        content_wrap = tk.Frame(self._inner, bg=T.SURFACE)
        content_wrap.pack(side="left", fill="both", expand=True)

        if title:
            hdr = tk.Frame(content_wrap, bg=T.SURFACE)
            hdr.pack(fill="x", padx=padx, pady=(pady, 6))
            tk.Label(hdr, text=title, bg=T.SURFACE,
                     fg=T.TEXT, font=T.FONT_H2).pack(anchor="w")
            if subtitle:
                tk.Label(hdr, text=subtitle, bg=T.SURFACE,
                         fg=T.TEXT_MUTED, font=T.FONT_SMALL).pack(anchor="w", pady=(2, 0))

        self.body = tk.Frame(content_wrap, bg=T.SURFACE)
        self.body.pack(fill="both", expand=True,
                       padx=padx, pady=(6 if title else pady, pady))


class Divider(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=T.BORDER, height=1, **kw)


# ═══════════════════════════════════════════════════════════
# BUTTONS — polished
# ═══════════════════════════════════════════════════════════

class _BaseButton(tk.Frame):
    def __init__(self, parent, text, command, *,
                 bg, fg, hover_bg, press_bg=None,
                 border=None, font=T.FONT_BODY_B,
                 padx=18, pady=10, icon=None, **kw):
        super().__init__(parent, bg=bg, cursor="hand2", **kw)
        if border:
            self.configure(highlightbackground=border,
                           highlightcolor=border,
                           highlightthickness=1)
        self._bg        = bg
        self._fg        = fg
        self._hover_bg  = hover_bg
        self._press_bg  = press_bg or hover_bg
        self._command   = command
        self._enabled   = True

        row = tk.Frame(self, bg=bg)
        row.pack(padx=padx, pady=pady)

        if icon:
            self._icon = tk.Label(row, text=icon, bg=bg, fg=fg,
                                  font=T.FONT_EMOJI)
            self._icon.pack(side="left", padx=(0, 8))
        else:
            self._icon = None

        self._label = tk.Label(row, text=text, bg=bg, fg=fg, font=font)
        self._label.pack(side="left")

        self._row = row
        ws = (self, row, self._label)
        if self._icon:
            ws = ws + (self._icon,)
        for w in ws:
            w.bind("<Button-1>",  self._on_press)
            w.bind("<ButtonRelease-1>", self._on_release)
            w.bind("<Enter>",     self._enter)
            w.bind("<Leave>",     self._leave)

    def _on_press(self, _e=None):
        if self._enabled:
            self._paint(self._press_bg)

    def _on_release(self, _e=None):
        if self._enabled:
            self._paint(self._hover_bg)
            if self._command:
                self._command()

    def _enter(self, _e=None):
        if self._enabled:
            self._paint(self._hover_bg)

    def _leave(self, _e=None):
        if self._enabled:
            self._paint(self._bg)

    def _paint(self, color):
        self.configure(bg=color)
        self._row.configure(bg=color)
        self._label.configure(bg=color)
        if self._icon:
            self._icon.configure(bg=color)

    def set_enabled(self, enabled):
        self._enabled = bool(enabled)
        self.configure(cursor="hand2" if enabled else "arrow")
        self._paint(self._bg if enabled else T.NEUTRAL_BG)
        self._label.configure(fg=self._fg if enabled else T.TEXT_MUTED)
        if self._icon:
            self._icon.configure(fg=self._fg if enabled else T.TEXT_MUTED)

    def set_text(self, text):
        self._label.configure(text=text)


class PrimaryButton(_BaseButton):
    def __init__(self, parent, text, command, *, icon=None, **kw):
        super().__init__(parent, text, command,
                         bg=T.ACCENT, fg=T.TEXT_INVERT,
                         hover_bg=T.ACCENT_DARK, press_bg=T.ACCENT_DEEP,
                         icon=icon, **kw)


class GhostButton(_BaseButton):
    def __init__(self, parent, text, command, *, icon=None, **kw):
        super().__init__(parent, text, command,
                         bg=T.SURFACE, fg=T.TEXT_BODY,
                         hover_bg=T.SURFACE_HOVER, press_bg=T.SURFACE_ALT,
                         border=T.BORDER_HARD,
                         icon=icon, **kw)


class DangerButton(_BaseButton):
    def __init__(self, parent, text, command, *, icon=None, **kw):
        super().__init__(parent, text, command,
                         bg=T.DANGER_BG, fg=T.DANGER,
                         hover_bg="#FCDCDC", press_bg="#F8C8C8",
                         border="#F0B8B8",
                         icon=icon, **kw)


class IconButton(tk.Label):
    def __init__(self, parent, glyph, command, *, size=36):
        super().__init__(parent, text=glyph, bg=T.SURFACE, fg=T.TEXT_BODY,
                         font=T.FONT_ICON, cursor="hand2",
                         width=2, height=1)
        self.bind("<Button-1>", lambda e: command())
        self.bind("<Enter>", lambda e: self.configure(bg=T.SURFACE_HOVER,
                                                      fg=T.ACCENT))
        self.bind("<Leave>", lambda e: self.configure(bg=T.SURFACE,
                                                      fg=T.TEXT_BODY))


# ═══════════════════════════════════════════════════════════
# STAT CARD — polished KPI tile with accent bar + delta
# ═══════════════════════════════════════════════════════════

class StatCard(tk.Frame):
    def __init__(self, parent, *, value, label, sublabel=None,
                 delta=None, delta_kind="neutral", accent_color=None, **kw):
        super().__init__(parent, bg=T.SHADOW_SOFT, **kw)

        # white inner
        inner = tk.Frame(self, bg=T.SURFACE)
        inner.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1))

        # accent bar on left
        bar_color = accent_color or T.BORDER
        tk.Frame(inner, bg=bar_color, width=4).pack(side="left", fill="y")

        body = tk.Frame(inner, bg=T.SURFACE)
        body.pack(side="left", fill="both", expand=True, padx=20, pady=18)

        # Big value
        self.value_label = tk.Label(body, text=value, bg=T.SURFACE,
                 fg=accent_color or T.TEXT,
                 font=T.FONT_KPI, anchor="w")
        self.value_label.pack(anchor="w")

        # Label
        tk.Label(body, text=label, bg=T.SURFACE,
                 fg=T.TEXT_BODY, font=T.FONT_BODY_B,
                 anchor="w").pack(anchor="w", pady=(6, 0))

        # Delta or sublabel
        if delta:
            delta_colors = {
                "up":   (T.SUCCESS_BG, T.SUCCESS, "↑"),
                "down": (T.DANGER_BG,  T.DANGER,  "↓"),
                "neutral": (T.NEUTRAL_BG, T.TEXT_MUTED, "•"),
            }
            bg, fg, arrow = delta_colors.get(delta_kind, delta_colors["neutral"])
            chip = tk.Frame(body, bg=bg)
            chip.pack(anchor="w", pady=(8, 0))
            tk.Label(chip, text=f"{arrow}  {delta}", bg=bg, fg=fg,
                     font=T.FONT_TINY, padx=8, pady=2).pack()
        elif sublabel:
            tk.Label(body, text=sublabel, bg=T.SURFACE,
                     fg=T.TEXT_MUTED, font=T.FONT_SMALL,
                     anchor="w").pack(anchor="w", pady=(6, 0))


# ═══════════════════════════════════════════════════════════
# ACTION ROW — polished quick action with icon circle
# ═══════════════════════════════════════════════════════════

class ActionRow(tk.Frame):
    def __init__(self, parent, *, icon, label, sublabel=None,
                 command, primary=False):
        outer_bg = T.ACCENT if primary else T.SURFACE
        hover_bg = T.ACCENT_DARK if primary else T.SURFACE_HOVER
        fg       = T.TEXT_INVERT if primary else T.TEXT
        sub_fg   = "#FFD9DE" if primary else T.TEXT_MUTED
        icon_bg  = "#FFFFFF" if primary else T.ACCENT_SOFT
        icon_fg  = T.ACCENT if primary else T.ACCENT

        super().__init__(parent, bg=T.SHADOW_SOFT, cursor="hand2")
        inner = tk.Frame(self, bg=outer_bg)
        inner.pack(fill="both", expand=True, padx=(0, 1), pady=(0, 1))

        row = tk.Frame(inner, bg=outer_bg)
        row.pack(fill="x", padx=16, pady=14)

        # Icon circle
        icon_chip = tk.Frame(row, bg=icon_bg, width=38, height=38)
        icon_chip.pack(side="left", padx=(0, 14))
        icon_chip.pack_propagate(False)
        icon_lbl = tk.Label(icon_chip, text=icon, bg=icon_bg, fg=icon_fg,
                            font=T.FONT_EMOJI_LG)
        icon_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Text column
        text_col = tk.Frame(row, bg=outer_bg)
        text_col.pack(side="left", fill="x", expand=True)
        title_lbl = tk.Label(text_col, text=label, bg=outer_bg, fg=fg,
                             font=T.FONT_BODY_B, anchor="w")
        title_lbl.pack(anchor="w")
        sub_lbl = None
        if sublabel:
            sub_lbl = tk.Label(text_col, text=sublabel, bg=outer_bg, fg=sub_fg,
                               font=T.FONT_SMALL, anchor="w")
            sub_lbl.pack(anchor="w", pady=(3, 0))

        # Arrow on right
        arrow = tk.Label(row, text="›", bg=outer_bg, fg=fg,
                         font=(T.FONT_FAMILY, 16, "bold"))
        arrow.pack(side="right", padx=(8, 0))

        # Hover region — includes ALL widgets except icon chip (which has fixed bg)
        hovers = [inner, row, text_col, title_lbl, arrow]
        if sub_lbl:
            hovers.append(sub_lbl)

        def click(_e=None):  command()
        def enter(_e=None):
            for w in hovers: w.configure(bg=hover_bg)
        def leave(_e=None):
            for w in hovers: w.configure(bg=outer_bg)

        for w in hovers:
            w.bind("<Button-1>", click)
            w.bind("<Enter>", enter)
            w.bind("<Leave>", leave)


# ═══════════════════════════════════════════════════════════
# FORM FIELDS
# ═══════════════════════════════════════════════════════════

class Field(tk.Frame):
    def __init__(self, parent, *, label, required=False, show=None):
        super().__init__(parent, bg=T.SURFACE)
        lbl_text = f"{label} *" if required else label
        tk.Label(self, text=lbl_text, bg=T.SURFACE, fg=T.TEXT_BODY,
                 font=T.FONT_LABEL, anchor="w").pack(anchor="w", pady=(0, 6))

        wrap = tk.Frame(self, bg=T.BORDER_HARD, height=T.INPUT_HEIGHT)
        wrap.pack(fill="x")
        wrap.pack_propagate(False)

        # Inner frame to hold the entry with a thin 1px padding,
        # so focus highlight is a clean 1px ring.
        inner = tk.Frame(wrap, bg=T.SURFACE)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        self.var = tk.StringVar()
        self.entry = tk.Entry(inner, textvariable=self.var,
                              bg=T.SURFACE, fg=T.TEXT,
                              font=T.FONT_BODY, bd=0,
                              highlightthickness=0,
                              insertbackground=T.TEXT,
                              show=show)
        self.entry.pack(fill="both", expand=True, padx=10, pady=8)

        # Subtle 1px focus ring — blue, not red
        def _focus_in(_e):
            try:
                wrap.configure(bg=T.FOCUS)
            except Exception:
                wrap.configure(bg=T.ACCENT)

        def _focus_out(_e):
            wrap.configure(bg=T.BORDER_HARD)

        self.entry.bind("<FocusIn>",  _focus_in)
        self.entry.bind("<FocusOut>", _focus_out)

    def get(self):  return self.var.get()
    def set(self, v): self.var.set(v or "")


class Combo(tk.Frame):
    def __init__(self, parent, *, label, values=None, required=False,
                 editable=False):
        super().__init__(parent, bg=T.SURFACE)
        lbl_text = f"{label} *" if required else label
        tk.Label(self, text=lbl_text, bg=T.SURFACE, fg=T.TEXT_BODY,
                 font=T.FONT_LABEL, anchor="w").pack(anchor="w", pady=(0, 6))

        self.var = tk.StringVar()
        self.combo = ttk.Combobox(self, textvariable=self.var,
                                   values=values or [],
                                   state="normal" if editable else "readonly",
                                   font=T.FONT_BODY)
        self.combo.pack(fill="x", ipady=4)

    def get(self):  return self.var.get()
    def set(self, v): self.var.set(v or "")
    def set_values(self, vs): self.combo["values"] = vs


# ═══════════════════════════════════════════════════════════
# TOPBAR
# ═══════════════════════════════════════════════════════════

class TopBar(tk.Frame):
    def __init__(self, parent, *, logo_text="CRYSTAL", nav_label="Dashboard",
                 user_label="Admin", on_logout=None, on_menu=None):
        super().__init__(parent, bg=T.SURFACE, height=T.TOPBAR_HEIGHT)
        self.pack_propagate(False)

        tk.Frame(self, bg=T.BORDER, height=1).pack(side="bottom", fill="x")
        tk.Frame(self, bg=T.ACCENT, height=3).pack(side="bottom", fill="x")

        left = tk.Frame(self, bg=T.SURFACE)
        left.pack(side="left", fill="y", padx=(T.SP_LG, 0))

        if on_menu:
            IconButton(left, "☰", on_menu).pack(side="left", pady=T.SP_SM)

        tk.Label(left, text=logo_text, bg=T.SURFACE, fg=T.ACCENT,
                 font=(T.FONT_FAMILY, 17, "bold")).pack(side="left", padx=(T.SP_MD, 0))

        tk.Label(left, text="│", bg=T.SURFACE, fg=T.BORDER_HARD,
                 font=T.FONT_BODY).pack(side="left", padx=T.SP_SM)

        tk.Label(left, text=nav_label, bg=T.SURFACE, fg=T.TEXT_BODY,
                 font=T.FONT_BODY).pack(side="left")

        right = tk.Frame(self, bg=T.SURFACE)
        right.pack(side="right", fill="y", padx=(0, T.SP_LG))

        IconButton(right, "🔔", lambda: None).pack(side="right", padx=(T.SP_XS, 0))

        chip = tk.Frame(right, bg=T.SURFACE_ALT, cursor="hand2")
        chip.pack(side="right", padx=(0, T.SP_SM))
        tk.Label(chip, text="👤", bg=T.SURFACE_ALT, fg=T.TEXT_BODY,
                 font=T.FONT_EMOJI).pack(side="left", padx=(10, 6), pady=7)
        tk.Label(chip, text=user_label, bg=T.SURFACE_ALT, fg=T.TEXT,
                 font=T.FONT_BODY_B).pack(side="left", padx=(0, 12), pady=7)

        if on_logout:
            chip.bind("<Button-1>", lambda e: on_logout())


# ═══════════════════════════════════════════════════════════
# TTK THEME — one look for every table / combo / scrollbar
# ═══════════════════════════════════════════════════════════

def set_window_icon(window):
    """Give any Toplevel the CRYSTAL app icon (no-op if missing)."""
    try:
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))
        ico = base / "assets" / "logo" / "LOGO.ico"
        if ico.is_file():
            window.iconbitmap(default=str(ico))
    except Exception:
        pass


def fit_toplevel(win, width=None, *, min_height=0, margin=80):
    """Size a dialog to its requested content, keeping it fully on screen."""
    win.update_idletasks()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    w = int(width or win.winfo_reqwidth())
    w = max(320, min(w, sw - 40))
    h = max(int(min_height), win.winfo_reqheight())
    h = min(h, sh - margin)
    x = max(10, (sw - w) // 2)
    y = max(10, (sh - h) // 2 - 20)
    win.geometry(f"{w}x{h}+{x}+{y}")
    return w, h


def apply_ttk_theme(root):
    """Apply the CRYSTAL table theme. Safe to call on every window."""
    st = ttk.Style(root)
    try:
        st.theme_use("clam")
    except tk.TclError:
        return

    st.layout("Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
    st.configure(
        "Treeview",
        background=T.SURFACE, fieldbackground=T.SURFACE,
        foreground=T.TEXT, font=T.FONT_SMALL,
        rowheight=32, borderwidth=0, relief="flat",
    )
    st.map(
        "Treeview",
        background=[("selected", T.ACCENT_SOFT)],
        foreground=[("selected", T.TEXT)],
    )
    st.configure(
        "Treeview.Heading",
        background=T.SURFACE_ALT, foreground=T.TEXT_BODY,
        font=T.FONT_LABEL, relief="flat",
        borderwidth=0, padding=(10, 9),
    )
    st.map("Treeview.Heading", background=[("active", T.SURFACE_HOVER)])

    st.configure(
        "TCombobox",
        fieldbackground=T.SURFACE, background=T.SURFACE,
        foreground=T.TEXT, arrowcolor=T.TEXT_MUTED,
        bordercolor=T.BORDER_HARD, lightcolor=T.BORDER_HARD,
        darkcolor=T.BORDER_HARD, padding=5,
    )
    st.map(
        "TCombobox",
        fieldbackground=[("readonly", T.SURFACE)],
        bordercolor=[("focus", T.FOCUS)],
        selectbackground=[("readonly", T.SURFACE)],
        selectforeground=[("readonly", T.TEXT)],
    )
    for orient in ("Vertical", "Horizontal"):
        st.configure(
            f"{orient}.TScrollbar",
            width=12, arrowsize=0, gripcount=0,
            background=T.BORDER_HARD, troughcolor=T.SURFACE_ALT,
            bordercolor=T.SURFACE, lightcolor=T.BORDER_HARD,
            darkcolor=T.BORDER_HARD, arrowcolor=T.TEXT_MUTED,
            relief="flat", borderwidth=0,
        )
        st.map(
            f"{orient}.TScrollbar",
            background=[
                ("pressed", T.TEXT_FAINT),
                ("active", T.TEXT_MUTED),
                ("disabled", T.BORDER),
            ],
            arrowcolor=[("disabled", T.BORDER)],
        )
    st.configure(
        "Crystal.Horizontal.TProgressbar",
        troughcolor=T.SURFACE_ALT, background=T.ACCENT,
        bordercolor=T.BORDER, lightcolor=T.ACCENT, darkcolor=T.ACCENT,
        thickness=6,
    )


# ═══════════════════════════════════════════════════════════
# SEARCH BOX — placeholder + focus ring, no chunky border
# ═══════════════════════════════════════════════════════════

class SearchEntry(tk.Frame):
    def __init__(self, parent, *, textvariable=None, width=34,
                 placeholder="Search…", on_submit=None, bg=T.SURFACE,
                 show_icon=True):
        super().__init__(parent, bg=T.BORDER_HARD)

        self._bg = bg
        self._placeholder = placeholder
        self._showing_placeholder = False

        inner = tk.Frame(self, bg=bg)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        if show_icon:
            tk.Label(inner, text="🔍", bg=bg, fg=T.TEXT_FAINT,
                     font=T.FONT_TINY).pack(side="left", padx=(10, 2))

        self.var = textvariable if textvariable is not None else tk.StringVar()
        self.entry = tk.Entry(
            inner, textvariable=self.var, width=width,
            bg=bg, fg=T.TEXT, font=T.FONT_BODY, bd=0,
            highlightthickness=0, insertbackground=T.TEXT,
        )
        self.entry.pack(side="left", fill="both", expand=True,
                        padx=(0 if show_icon else 10, 10), ipady=8)

        self._hint = None
        if placeholder:
            self._hint = tk.Label(self.entry, text=placeholder, bg=bg,
                                  fg=T.TEXT_FAINT, font=T.FONT_BODY,
                                  cursor="xterm")
            self._hint.bind("<Button-1>", lambda e: self.entry.focus_set())

        def _hide(_e=None):
            if self._hint is not None:
                self._hint.place_forget()

        def _maybe_show(*_a):
            if self._hint is not None and not self.var.get():
                self._hint.place(x=1, rely=0.5, anchor="w")

        self.entry.bind("<FocusIn>", self._focus_in)
        self.entry.bind("<FocusOut>", self._focus_out)
        self.entry.bind("<KeyRelease>", _maybe_show)
        self._hide_hint = _hide
        self._maybe_show = _maybe_show
        if on_submit:
            self.entry.bind("<Return>", lambda e: on_submit())
        try:
            self.var.trace_add(
                "write",
                lambda *_: _hide() if self.var.get() else None,
            )
        except Exception:
            pass
        _maybe_show()

    def _focus_in(self, _e=None):
        self.configure(bg=T.FOCUS)
        self._hide_hint()

    def _focus_out(self, _e=None):
        self.configure(bg=T.BORDER_HARD)
        self._maybe_show()

    def get(self):
        return self.var.get()

    def clear(self):
        self.entry.delete(0, "end")
        self._maybe_show()
        self.configure(bg=T.BORDER_HARD)


# ═══════════════════════════════════════════════════════════
# PAGE HEADER — brand + breadcrumb + right-side meta
# ═══════════════════════════════════════════════════════════

class PageHeader(tk.Frame):
    def __init__(self, parent, *, title, subtitle=None, meta=None,
                 padx=24, bg=T.BG):
        super().__init__(parent, bg=bg)

        row = tk.Frame(self, bg=bg)
        row.pack(fill="x", padx=padx, pady=(18, 0))

        tk.Label(row, text="CRYSTAL", bg=bg, fg=T.ACCENT,
                 font=(T.FONT_FAMILY, 15, "bold")).pack(side="left")
        tk.Label(row, text="  /  ", bg=bg, fg=T.TEXT_FAINT,
                 font=T.FONT_BODY).pack(side="left")
        tk.Label(row, text=title, bg=bg, fg=T.TEXT,
                 font=T.FONT_H2).pack(side="left")
        self.meta_label = None
        if meta:
            self.meta_label = tk.Label(row, text=meta, bg=bg, fg=T.TEXT_MUTED,
                                       font=T.FONT_SMALL)
            self.meta_label.pack(side="right")
        if subtitle:
            tk.Label(row, text=subtitle, bg=bg, fg=T.TEXT_MUTED,
                     font=T.FONT_SMALL).pack(side="left", padx=(12, 0), pady=(2, 0))

        tk.Frame(self, bg=T.ACCENT, height=2).pack(
            fill="x", padx=padx, pady=(14, 0))


# ═══════════════════════════════════════════════════════════
# EMPTY STATE — for tables with no rows
# ═══════════════════════════════════════════════════════════

class EmptyState(tk.Frame):
    def __init__(self, parent, *, title="Nothing here yet",
                 hint=None, icon="🗂", bg=T.SURFACE):
        super().__init__(parent, bg=bg)
        tk.Label(self, text=icon, bg=bg, fg=T.TEXT_FAINT,
                 font=("Segoe UI Emoji", 24)).pack(pady=(0, 8))
        self._title = tk.Label(self, text=title, bg=bg, fg=T.TEXT_BODY,
                               font=T.FONT_BODY_B)
        self._title.pack()
        self._hint = tk.Label(self, text=hint or "", bg=bg, fg=T.TEXT_MUTED,
                              font=T.FONT_SMALL)
        if hint:
            self._hint.pack(pady=(4, 0))

    def set_text(self, title, hint=None):
        self._title.configure(text=title)
        self._hint.configure(text=hint or "")
        if hint:
            self._hint.pack(pady=(4, 0))
        else:
            self._hint.pack_forget()


# ═══════════════════════════════════════════════════════════
# TOAST
# ═══════════════════════════════════════════════════════════

class Toast(tk.Toplevel):
    _active = None

    @classmethod
    def show(cls, parent, message, *, kind="info", duration=2600):
        if cls._active is not None:
            try: cls._active.destroy()
            except Exception: pass

        colors = {
            "info":    (T.INFO_BG,    T.INFO,    "ℹ"),
            "success": (T.SUCCESS_BG, T.SUCCESS, "✓"),
            "warning": (T.WARNING_BG, T.WARNING, "⚠"),
            "error":   (T.DANGER_BG,  T.DANGER,  "✕"),
        }
        bg, fg, glyph = colors.get(kind, colors["info"])

        win = tk.Toplevel(parent)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        cls._active = win

        frame = tk.Frame(win, bg=bg, highlightbackground=fg,
                         highlightthickness=1)
        frame.pack(fill="both", expand=True)

        inner = tk.Frame(frame, bg=bg)
        inner.pack(padx=16, pady=12)

        tk.Label(inner, text=glyph, bg=bg, fg=fg,
                 font=T.FONT_EMOJI_LG).pack(side="left", padx=(0, 10))
        tk.Label(inner, text=message, bg=bg, fg=fg,
                 font=T.FONT_BODY_B).pack(side="left")

        win.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width()
        ph = parent.winfo_rooty() + parent.winfo_height()
        ww, wh = win.winfo_width(), win.winfo_height()
        win.geometry(f"+{pw - ww - 24}+{ph - wh - 24}")

        win.after(duration, lambda: cls._dismiss(win))

    @classmethod
    def _dismiss(cls, win):
        try: win.destroy()
        except Exception: pass
        if cls._active is win:
            cls._active = None
