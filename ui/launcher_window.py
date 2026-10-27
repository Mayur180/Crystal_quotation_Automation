"""
CRYSTAL / ARMATECH ASSOCIATES
Launcher Window — v4.

Shows module cards (VMM, Crystal, ...) after login.
Only shows modules the user has access to.

SAFETY: Uses the shared Tk root. Never creates a new one.
"""

import tkinter as tk
from tkinter import messagebox

from app.services.auth_service import UserSession
from app.services import paths


# ---------- THEME ----------
BG_COLOR     = "#F4F6F8"
TEXT_COLOR   = "#2C3E50"
MUTED_COLOR  = "#7F8C8D"
BORDER_COLOR = "#D5DBE1"


# ---------- MODULE METADATA ----------
# Add new modules here — the launcher auto-renders them.
MODULE_CARDS = {
    "VMM": {
        "title": "VMM",
        "subtitle": "Video Measuring Machines",
        "description": "Manual, Semi-Auto, Fully Auto, VMS",
        "color": "#2C3E50",
        "hover": "#34495E",
    },
    "Crystal": {
        "title": "CRYSTAL",
        "subtitle": "Precision Measurement Technology",
        "description": "Coming soon — Crystal product line",
        "color": "#C0392B",
        "hover": "#A93226",
    },
}


class LauncherWindow:
    """
    Workspace selector.
    Callback: on_select(module_name: str)
    """

    def __init__(self, root: tk.Tk, session: UserSession, on_select, on_logout=None):
        self.root = root
        self.session = session
        self.on_select = on_select
        self.on_logout = on_logout

        self.frame = tk.Frame(root, bg=BG_COLOR)
        self.frame.pack(fill="both", expand=True)

        self._build_ui()

    # ============================================================
    # UI
    # ============================================================

    def _build_ui(self):
        # ---- Header ----
        header = tk.Frame(self.frame, bg=BG_COLOR)
        header.pack(fill="x", padx=60, pady=(50, 10))

        tk.Label(header, text=f"Welcome, {self.session.full_name}",
                 font=("Segoe UI", 22, "bold"),
                 fg=TEXT_COLOR, bg=BG_COLOR).pack(anchor="w")

        tk.Label(header,
                 text="Which quotation system would you like to open today?",
                 font=("Segoe UI", 12),
                 fg=MUTED_COLOR, bg=BG_COLOR).pack(anchor="w", pady=(6, 0))

        # ---- Logout button (top right) ----
        top_right = tk.Frame(self.frame, bg=BG_COLOR)
        top_right.place(relx=1.0, rely=0.0, anchor="ne", x=-60, y=50)

        tk.Button(top_right, text="Log Out",
                  font=("Segoe UI", 10),
                  fg=MUTED_COLOR, bg=BG_COLOR,
                  relief="flat", cursor="hand2",
                  command=self._on_logout_click).pack()

        # ---- Cards container ----
        cards_container = tk.Frame(self.frame, bg=BG_COLOR)
        cards_container.pack(expand=True)

        # Which modules does this user actually have access to?
        user_modules = [m for m in self.session.modules if m in MODULE_CARDS]

        if not user_modules:
            tk.Label(cards_container,
                     text="⚠ No modules assigned to this account.",
                     font=("Segoe UI", 14),
                     fg="#E74C3C", bg=BG_COLOR).pack(pady=40)
            return

        # Render one card per accessible module
        for module_name in user_modules:
            self._make_card(cards_container, module_name)

    def _make_card(self, parent, module_name: str):
        meta = MODULE_CARDS[module_name]

        card = tk.Frame(parent, bg=meta["color"],
                        width=260, height=300,
                        cursor="hand2")
        card.pack(side="left", padx=20)
        card.pack_propagate(False)

        # Click handler — bind to card AND all children
        def select(_e=None, name=module_name):
            self._on_module_selected(name)

        card.bind("<Button-1>", select)

        # Inner content
        tk.Label(card, text=meta["title"],
                 font=("Segoe UI", 26, "bold"),
                 fg="white", bg=meta["color"]).pack(pady=(60, 0))

        tk.Label(card, text=meta["subtitle"],
                 font=("Segoe UI", 11),
                 fg="white", bg=meta["color"],
                 wraplength=220).pack(pady=(6, 20))

        tk.Label(card, text=meta["description"],
                 font=("Segoe UI", 9),
                 fg="#ECF0F1", bg=meta["color"],
                 wraplength=220).pack(pady=(0, 20))

        enter_btn = tk.Button(
            card, text="ENTER →",
            font=("Segoe UI", 12, "bold"),
            fg=meta["color"], bg="white",
            activebackground="#ECF0F1",
            relief="flat", cursor="hand2", bd=0,
            command=select,
        )
        enter_btn.pack(ipadx=20, ipady=6)

        # Bind click on all children too
        for child in card.winfo_children():
            child.bind("<Button-1>", select)

        # Hover effect
        def on_enter(_e):
            card.configure(bg=meta["hover"])
            for child in card.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=meta["hover"])

        def on_leave(_e):
            card.configure(bg=meta["color"])
            for child in card.winfo_children():
                if isinstance(child, tk.Label):
                    child.configure(bg=meta["color"])

        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    # ============================================================
    # ACTIONS
    # ============================================================

    def _on_module_selected(self, module_name: str):
        # Set the module in paths so all services route correctly
        paths.set_active_module(module_name)
        self.session.active_module = module_name

        # Destroy our frame before handing off
        self.frame.destroy()

        # Fire the callback
        self.on_select(module_name)

    def _on_logout_click(self):
        if not messagebox.askyesno("Log Out", "Log out and return to login?"):
            return
        self.frame.destroy()
        if self.on_logout:
            self.on_logout()
