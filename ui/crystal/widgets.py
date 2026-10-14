"""CRYSTAL — Widget Library V2 (polished)."""
import tkinter as tk
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
        tk.Label(body, text=value, bg=T.SURFACE,
                 fg=accent_color or T.TEXT,
                 font=T.FONT_KPI, anchor="w").pack(anchor="w")

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

        self.var = tk.StringVar()
        self.entry = tk.Entry(wrap, textvariable=self.var,
                              bg=T.SURFACE, fg=T.TEXT,
                              font=T.FONT_BODY, bd=0,
                              highlightthickness=0, show=show)
        self.entry.pack(fill="both", expand=True, padx=10, pady=8)

        self.entry.bind("<FocusIn>",  lambda e: wrap.configure(bg=T.ACCENT))
        self.entry.bind("<FocusOut>", lambda e: wrap.configure(bg=T.BORDER_HARD))

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
