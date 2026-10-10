"""
CRYSTAL / ARMATECH ASSOCIATES
TEAM ACTIVITY WINDOW

Admin-only view: everyone's activity logs across all PCs.
"""

import os
import sys
import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:
    from app.services.activity_log_service import (
        list_events,
        get_all_users_summary,
    )
except Exception:
    list_events = None
    get_all_users_summary = None


def _text(v):
    return "" if v is None else str(v).strip()


class TeamActivity(tk.Toplevel):

    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_LIGHT = "#FFF3F3"
    SOFT = "#F8F9FA"

    def __init__(self, parent):
        super().__init__(parent)

        self.title("CRYSTAL | Team Activity")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(bg=self.BG)

        self.transient(parent)
        self.grab_set()

        self.user_var = tk.StringVar(value="All")
        self.from_var = tk.StringVar(value="")
        self.to_var = tk.StringVar(value="")

        self._configure_style()
        self._build_interface()
        self._reload()

        try:
            self.bind("<Escape>", lambda _e: self.destroy())
        except Exception:
            pass

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Team.Treeview",
            background="white", fieldbackground="white",
            foreground=self.TEXT, rowheight=24,
            borderwidth=0, font=("Arial", 9),
        )
        style.configure(
            "Team.Treeview.Heading",
            background="#F0F1F3", foreground=self.TEXT,
            relief="flat", font=("Arial", 9, "bold"),
        )

    def _build_interface(self):
        # header
        head = tk.Frame(self, bg=self.BG)
        head.pack(fill="x", padx=28, pady=(18, 6))
        tk.Label(
            head, text="Team Activity",
            bg=self.BG, fg=self.TEXT,
            font=("Arial", 16, "bold"),
        ).pack(side="left")
        tk.Label(
            head, text="All users · Audit trail",
            bg=self.BG, fg=self.MUTED,
            font=("Arial", 9),
        ).pack(side="left", padx=(12, 0), pady=(8, 0))

        # filter bar
        filt = tk.Frame(self, bg=self.BG)
        filt.pack(fill="x", padx=28, pady=(6, 10))

        tk.Label(filt, text="User", bg=self.BG, fg=self.MUTED,
                 font=("Arial", 8, "bold")).pack(side="left", padx=(0, 6))
        self.user_cb = ttk.Combobox(
            filt, textvariable=self.user_var, values=["All"],
            state="readonly", width=14, font=("Arial", 9),
        )
        self.user_cb.pack(side="left", ipady=3)
        self.user_cb.bind("<<ComboboxSelected>>", lambda _e: self._reload())

        tk.Label(filt, text="From", bg=self.BG, fg=self.MUTED,
                 font=("Arial", 8, "bold")).pack(side="left", padx=(14, 6))
        tk.Entry(
            filt, textvariable=self.from_var, width=12,
            bg="white", fg=self.TEXT, relief="solid", bd=1,
            font=("Arial", 10), insertbackground=self.RED,
        ).pack(side="left", ipady=4)

        tk.Label(filt, text="To", bg=self.BG, fg=self.MUTED,
                 font=("Arial", 8, "bold")).pack(side="left", padx=(10, 6))
        tk.Entry(
            filt, textvariable=self.to_var, width=12,
            bg="white", fg=self.TEXT, relief="solid", bd=1,
            font=("Arial", 10), insertbackground=self.RED,
        ).pack(side="left", ipady=4)

        tk.Button(
            filt, text="Apply", command=self._reload,
            bg="white", fg=self.TEXT,
            activebackground="#F3F4F6",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=12, pady=4,
        ).pack(side="left", padx=(10, 0))

        tk.Button(
            filt, text="Reset", command=self._reset,
            bg="white", fg=self.MUTED,
            activebackground="#F3F4F6",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            padx=12, pady=4,
        ).pack(side="left", padx=(6, 0))

        # right side buttons
        tk.Button(
            filt, text="Export CSV", command=self._export_csv,
            bg="white", fg=self.TEXT,
            activebackground="#F3F4F6",
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=12, pady=4,
        ).pack(side="right")

        tk.Button(
            filt, text="Refresh", command=self._reload,
            bg="white", fg=self.TEXT,
            activebackground="#F3F4F6",
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=12, pady=4,
        ).pack(side="right", padx=(0, 8))

        # summary card
        sum_card = tk.Frame(
            self, bg=self.CARD,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        sum_card.pack(fill="x", padx=28, pady=(0, 10))

        self.summary_title = tk.Label(
            sum_card, text="Per-User Summary",
            bg=self.CARD, fg=self.TEXT,
            font=("Arial", 11, "bold"), anchor="w",
        )
        self.summary_title.pack(anchor="w", padx=14, pady=(12, 6))

        user_cols = ("user", "events", "last_seen")
        self.user_tree = ttk.Treeview(
            sum_card, columns=user_cols, show="headings",
            style="Team.Treeview", height=4,
        )
        self.user_tree.heading("user", text="User")
        self.user_tree.heading("events", text="Events")
        self.user_tree.heading("last_seen", text="Last Seen")
        self.user_tree.column("user", width=240, anchor="w")
        self.user_tree.column("events", width=100, anchor="e")
        self.user_tree.column("last_seen", width=240, anchor="w")
        self.user_tree.pack(fill="x", padx=14, pady=(0, 14))

        # events card
        ev_card = tk.Frame(
            self, bg=self.CARD,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        ev_card.pack(fill="both", expand=True, padx=28, pady=(0, 12))

        tk.Label(
            ev_card, text="All Events (newest first)",
            bg=self.CARD, fg=self.TEXT,
            font=("Arial", 11, "bold"), anchor="w",
        ).pack(anchor="w", padx=14, pady=(12, 6))

        ev_cols = ("time", "event", "number", "detail", "user")
        self.tree = ttk.Treeview(
            ev_card, columns=ev_cols, show="headings",
            style="Team.Treeview", height=14,
        )
        self.tree.heading("time", text="Time")
        self.tree.heading("event", text="Event")
        self.tree.heading("number", text="Quotation No.")
        self.tree.heading("detail", text="Detail")
        self.tree.heading("user", text="User")
        self.tree.column("time", width=150, anchor="w")
        self.tree.column("event", width=120, anchor="w")
        self.tree.column("number", width=180, anchor="w")
        self.tree.column("detail", width=300, anchor="w", stretch=True)
        self.tree.column("user", width=110, anchor="w")

        vsb = ttk.Scrollbar(ev_card, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True,
                       padx=(14, 0), pady=(0, 14))
        vsb.pack(side="right", fill="y", pady=(0, 14), padx=(0, 14))

        # action bar
        abar = tk.Frame(
            self, bg=self.CARD, height=60,
            highlightbackground=self.BORDER, highlightthickness=1,
        )
        abar.pack(side="bottom", fill="x")
        abar.pack_propagate(False)

        self.count_label = tk.Label(
            abar, text="", bg=self.CARD, fg=self.MUTED,
            font=("Arial", 9),
        )
        self.count_label.pack(side="left", padx=22)

        tk.Button(
            abar, text="Close", command=self.destroy,
            bg="white", fg=self.TEXT,
            activebackground="#F3F4F6",
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9, "bold"), cursor="hand2",
            padx=14, pady=6,
        ).pack(side="right", padx=22, pady=14)

    def _reset(self):
        self.user_var.set("All")
        self.from_var.set("")
        self.to_var.set("")
        self._reload()

    def _parse_date(self, s):
        s = _text(s)
        if not s:
            return None
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                pass
        return None

    def _reload(self):
        if list_events is None:
            return

        # ---- per-user summary ----
        users = []
        try:
            if get_all_users_summary is not None:
                users = get_all_users_summary() or []
        except Exception:
            users = []

        # update combobox values
        names = ["All"] + [u.get("user", "") for u in users if u.get("user")]
        try:
            self.user_cb["values"] = names
        except Exception:
            pass

        # fill user tree
        for row in self.user_tree.get_children():
            self.user_tree.delete(row)
        for u in users:
            self.user_tree.insert(
                "", "end",
                values=(
                    _text(u.get("user")),
                    str(u.get("events", 0)),
                    _text(u.get("last_seen")),
                ),
            )

        # ---- events ----
        user_filter = self.user_var.get()
        if user_filter == "All":
            user_filter = None

        try:
            events = list_events(limit=2000, event_type=None) or []
        except Exception:
            events = []

        from_d = self._parse_date(self.from_var.get())
        to_d = self._parse_date(self.to_var.get())

        filtered = []
        for ev in events:
            if user_filter and _text(ev.get("user")) != user_filter:
                continue
            if from_d or to_d:
                ts = _text(ev.get("timestamp"))[:10]
                try:
                    d = datetime.strptime(ts, "%Y-%m-%d").date()
                except Exception:
                    continue
                if from_d and d < from_d:
                    continue
                if to_d and d > to_d:
                    continue
            filtered.append(ev)

        for row in self.tree.get_children():
            self.tree.delete(row)

        for ev in filtered:
            ts = _text(ev.get("timestamp"))
            # friendly time
            try:
                dt = datetime.fromisoformat(ts)
                time_str = dt.strftime("%d %b %H:%M:%S")
            except Exception:
                time_str = ts

            self.tree.insert(
                "", "end",
                values=(
                    time_str,
                    _text(ev.get("event")),
                    _text(ev.get("quotation_number")),
                    _text(ev.get("detail")),
                    _text(ev.get("user")),
                ),
            )

        self.count_label.configure(
            text=f"{len(filtered)} event(s) · {len(users)} user(s)"
        )

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export Team Activity as CSV",
            defaultextension=".csv",
            initialfile="TeamActivity.csv",
            filetypes=[("CSV file", "*.csv")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(["Timestamp", "Event", "Quotation No.",
                            "Detail", "User"])

                for item in self.tree.get_children():
                    vals = self.tree.item(item, "values")
                    w.writerow(vals)

            messagebox.showinfo(
                "Export CSV",
                f"Saved to:\n{path}",
                parent=self,
            )
        except Exception as e:
            messagebox.showerror(
                "Export CSV",
                f"Could not export:\n{e}",
                parent=self,
            )


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    TeamActivity(root)
    root.mainloop()
