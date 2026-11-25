# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# ACTIVITY LOG WINDOW
#
# Modal window - view the audit trail of user actions.
# ============================================================

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from ui.crystal import theme as T
from ui.crystal import widgets as W


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:
    from app.services.activity_log_service import (
        list_events,
        clear_log,
    )
except Exception:
    list_events = None
    clear_log = None


def _text(v):
    return "" if v is None else str(v).strip()


def _friendly_ts(value):
    text = _text(value)
    if not text:
        return "—"
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.strftime("%d-%m-%Y %H:%M")
    except Exception:
        return text


def _friendly_event(value):
    text = _text(value)
    if not text:
        return "—"
    return text.replace("_", " ").strip().capitalize()


class ActivityLog(tk.Toplevel):

    BG = T.BG
    CARD = T.SURFACE
    TEXT = T.TEXT
    MUTED = T.TEXT_MUTED
    BORDER = T.BORDER
    RED = T.ACCENT
    RED_LIGHT = T.ACCENT_SOFT

    def __init__(self, parent):
        super().__init__(parent)

        self.title("CRYSTAL | Activity Log")
        self.geometry("1000x660")
        self.minsize(860, 540)
        self.configure(bg=self.BG)
        W.set_window_icon(self)

        self.transient(parent)
        self.grab_set()

        self.search_var = tk.StringVar()
        self.event_var = tk.StringVar(value="All")

        W.apply_ttk_theme(self)
        self._build_interface()
        self._reload()

        # Esc closes the window
        try:
            self.bind("<Escape>", lambda _e: self.destroy())
        except Exception:
            pass

    def _build_interface(self):
        header = W.PageHeader(
            self, title="Activity Log",
            subtitle="Audit trail of recent actions",
            meta="—", padx=28,
        )
        header.pack(fill="x")
        self.count_label = header.meta_label

        # ---- filter bar ----
        bar_card = tk.Frame(
            self, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        bar_card.pack(fill="x", padx=28, pady=(14, 10))
        bar = tk.Frame(bar_card, bg=T.SURFACE)
        bar.pack(fill="x", padx=14, pady=10)

        search = W.SearchEntry(
            bar, textvariable=self.search_var,
            placeholder="Search details, quote no. or user…",
        )
        search.pack(side="left", fill="x", expand=True)
        search.entry.bind("<KeyRelease>", lambda _e: self._reload())

        tk.Label(
            bar, text="EVENT", bg=T.SURFACE, fg=T.TEXT_MUTED,
            font=T.FONT_LABEL,
        ).pack(side="left", padx=(12, 6))

        cb = ttk.Combobox(
            bar, textvariable=self.event_var,
            values=("All", "created", "status_changed", "deleted"),
            state="readonly", width=14, font=T.FONT_SMALL,
        )
        cb.pack(side="left", ipady=4)
        cb.bind("<<ComboboxSelected>>", lambda _e: self._reload())

        W.GhostButton(
            bar, "Clear", self._clear_search, padx=12, pady=7,
        ).pack(side="left", padx=(10, 0))

        # ---- action bar (bottom first) ----
        abar = tk.Frame(
            self, bg=T.SURFACE,
            highlightbackground=T.BORDER, highlightthickness=1,
        )
        abar.pack(side="bottom", fill="x")
        W.DangerButton(
            abar, "Clear log", self._clear_log, padx=14, pady=7,
        ).pack(side="left", padx=22, pady=13)
        W.GhostButton(
            abar, "Close", self.destroy, padx=18, pady=7,
        ).pack(side="right", padx=22, pady=13)

        # ---- table ----
        card = tk.Frame(
            self, bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )
        card.pack(fill="both", expand=True, padx=28, pady=(0, 14))

        cols = ("timestamp", "event", "number", "detail", "user")
        self.tree = ttk.Treeview(
            card, columns=cols, show="headings", height=12,
        )

        headings = {
            "timestamp": "Timestamp",
            "event": "Event",
            "number": "Quotation No.",
            "detail": "Detail",
            "user": "User",
        }
        widths = {
            "timestamp": 150,
            "event": 140,
            "number": 180,
            "detail": 380,
            "user": 100,
        }
        anchors = {
            "timestamp": "w",
            "event": "w",
            "number": "w",
            "detail": "w",
            "user": "w",
        }

        for c in cols:
            self.tree.heading(c, text=headings[c], anchor=anchors[c])
            self.tree.column(
                c, width=widths[c], anchor=anchors[c],
                stretch=(c == "detail"),
            )
        self.tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        self.tree.tag_configure("oddrow", background=T.SURFACE)

        vsb = ttk.Scrollbar(card, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True,
                       padx=2, pady=2)
        vsb.pack(side="right", fill="y", padx=(0, 2), pady=2)

        self._empty = W.EmptyState(
            card, icon="🕘", title="No activity yet",
            hint="Actions appear here as quotations are created or changed.",
        )

    def _clear_search(self):
        self.search_var.set("")
        self.event_var.set("All")
        self._reload()

    def _clear_log(self):
        if clear_log is None:
            messagebox.showerror(
                "Activity Log",
                "Service unavailable.", parent=self,
            )
            return
        if not messagebox.askyesno(
            "Clear Activity Log",
            "Delete ALL activity log entries?\nThis cannot be undone.",
            parent=self,
        ):
            return
        if clear_log():
            self._reload()
        else:
            messagebox.showerror(
                "Activity Log",
                "Could not clear the log.", parent=self,
            )

    def _reload(self):
        if list_events is None:
            self._fill_rows([])
            if self.count_label is not None:
                self.count_label.configure(text="Service unavailable")
            return

        search = self.search_var.get().strip()
        event_type = self.event_var.get().strip()

        try:
            records = list_events(
                limit=1000,
                search=search or None,
                event_type=event_type or None,
            ) or []
        except Exception:
            records = []

        self._fill_rows(records)
        if self.count_label is not None:
            self.count_label.configure(text=f"{len(records):,} event(s)")

    def _set_empty(self, visible):
        try:
            if visible:
                self._empty.place(relx=0.5, rely=0.5, anchor="center")
                self._empty.lift()
            else:
                self._empty.place_forget()
        except Exception:
            pass

    def _fill_rows(self, records):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for i, r in enumerate(records):
            self.tree.insert(
                "", "end",
                values=(
                    _friendly_ts(r.get("timestamp")),
                    _friendly_event(r.get("event")),
                    _text(r.get("quotation_number")) or "—",
                    _text(r.get("detail")) or "—",
                    _text(r.get("user")) or "—",
                ),
                tags=("evenrow" if i % 2 == 0 else "oddrow",),
            )
        self._set_empty(not records)
