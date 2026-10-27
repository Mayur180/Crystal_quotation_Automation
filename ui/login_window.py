"""
CRYSTAL / ARMATECH ASSOCIATES
Login Window — v4 multi-module launcher.

IMPORTANT (from v3 lessons learned):
  - NEVER create a new tk.Tk() root here.
  - We build inside a Frame that lives in the shared root.
  - On success, we destroy our Frame and call on_success(session).
  - On failure, we stay on screen and show an error.
"""

import tkinter as tk
from tkinter import ttk

from app.services.auth_service import (
    verify_credentials,
    describe_login_failure,
    UserSession,
)


# ---------- THEME ----------
BG_COLOR       = "#F4F6F8"
CARD_COLOR     = "#FFFFFF"
ACCENT_COLOR   = "#C0392B"   # Crystal red
TEXT_COLOR     = "#2C3E50"
MUTED_COLOR    = "#7F8C8D"
ERROR_COLOR    = "#E74C3C"
BORDER_COLOR   = "#D5DBE1"


class LoginWindow:
    """
    A self-contained login screen.

    Usage:
        LoginWindow(root, on_success=my_callback, on_cancel=my_cancel)
        # my_callback(session: UserSession) is called on success.
    """

    def __init__(self, root: tk.Tk, on_success, on_cancel=None):
        self.root = root
        self.on_success = on_success
        self.on_cancel = on_cancel

        # The container frame — this is what we destroy on success
        self.frame = tk.Frame(root, bg=BG_COLOR)
        self.frame.pack(fill="both", expand=True)

        self._build_ui()

        # Focus username field immediately
        self.root.after(100, lambda: self.username_entry.focus_set())

    # ============================================================
    # UI CONSTRUCTION
    # ============================================================

    def _build_ui(self):
        # Center card
        card = tk.Frame(self.frame, bg=CARD_COLOR,
                        highlightbackground=BORDER_COLOR,
                        highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center",
                   width=420, height=440)

        # ---- Logo / Title ----
        tk.Label(card, text="CRYSTAL",
                 font=("Segoe UI", 28, "bold"),
                 fg=ACCENT_COLOR, bg=CARD_COLOR).pack(pady=(40, 0))

        tk.Label(card, text="ARM ATECH ASSOCIATES",
                 font=("Segoe UI", 11, "bold"),
                 fg=TEXT_COLOR, bg=CARD_COLOR).pack(pady=(0, 4))

        tk.Label(card, text="Quotation Manager  •  v4.0",
                 font=("Segoe UI", 9),
                 fg=MUTED_COLOR, bg=CARD_COLOR).pack(pady=(0, 30))

        # ---- Username ----
        tk.Label(card, text="Username",
                 font=("Segoe UI", 10),
                 fg=TEXT_COLOR, bg=CARD_COLOR,
                 anchor="w").pack(fill="x", padx=50, pady=(0, 2))

        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(
            card, textvariable=self.username_var,
            font=("Segoe UI", 12), relief="solid", bd=1,
        )
        self.username_entry.pack(fill="x", padx=50, ipady=6)

        # ---- Password ----
        tk.Label(card, text="Password",
                 font=("Segoe UI", 10),
                 fg=TEXT_COLOR, bg=CARD_COLOR,
                 anchor="w").pack(fill="x", padx=50, pady=(14, 2))

        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            card, textvariable=self.password_var,
            font=("Segoe UI", 12), relief="solid", bd=1,
            show="•",
        )
        self.password_entry.pack(fill="x", padx=50, ipady=6)

        # ---- Error label (hidden by default) ----
        self.error_label = tk.Label(
            card, text="",
            font=("Segoe UI", 9),
            fg=ERROR_COLOR, bg=CARD_COLOR,
            wraplength=320,
        )
        self.error_label.pack(pady=(10, 0))

        # ---- Login button ----
        # ---- Remember Me checkbox ----
        self.remember_var = tk.BooleanVar(value=False)
        remember_frame = tk.Frame(card, bg=CARD_COLOR)
        remember_frame.pack(fill="x", padx=50, pady=(5, 0))
        
        tk.Checkbutton(
            remember_frame,
            text="Remember me on this PC",
            variable=self.remember_var,
            bg=CARD_COLOR, fg=TEXT_COLOR,
            activebackground=CARD_COLOR,
            selectcolor="white",
            font=("Segoe UI", 9),
            anchor="w",
        ).pack(side="left")

        self.login_btn = tk.Button(
            card, text="LOGIN",
            font=("Segoe UI", 12, "bold"),
            fg="white", bg=ACCENT_COLOR,
            activebackground="#A93226",
            activeforeground="white",
            relief="flat", cursor="hand2",
            command=self._on_login_click,
        )
        self.login_btn.pack(fill="x", padx=50, pady=(20, 10), ipady=8)

        # ---- Cancel / Quit ----
        tk.Button(
            card, text="Quit",
            font=("Segoe UI", 9),
            fg=MUTED_COLOR, bg=CARD_COLOR,
            relief="flat", cursor="hand2",
            command=self._on_cancel_click,
        ).pack(pady=(0, 20))

        # ---- Bind Enter key ----
        self.root.bind("<Return>", lambda e: self._on_login_click())
        self.root.bind("<Escape>", lambda e: self._on_cancel_click())

    # ============================================================
    # ACTIONS
    # ============================================================

    def _on_login_click(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()

        self.error_label.config(text="")

        session = verify_credentials(username, password)

        if session is None:
            msg = describe_login_failure(username, password)
            self.error_label.config(text=msg)
            self.password_var.set("")
            self.password_entry.focus_set()
            return

        # Success — hand off to callback
        self._cleanup_bindings()
        self.frame.destroy()
        # Save session if "Remember Me" is checked
        if self.remember_var.get():
            try:
                import json
                from app.services.paths import get_data_root
                session_file = get_data_root() / "session.json"
                session_data = {
                    "user_id": session.user_id,
                    "username": session.username,
                    "full_name": session.full_name,
                    "modules": session.modules,
                }
                with open(session_file, 'w', encoding='utf-8') as f:
                    json.dump(session_data, f, indent=2)
                print(f"[session] Saved session for {session.username}")
            except Exception as e:
                print(f"[session] Could not save session: {e}")
        else:
            # Clear any existing session if "Remember Me" is unchecked
            try:
                from app.services.paths import get_data_root
                session_file = get_data_root() / "session.json"
                if session_file.exists():
                    session_file.unlink()
            except Exception:
                pass

        self.on_success(session)

    def _on_cancel_click(self):
        self._cleanup_bindings()
        if self.on_cancel:
            self.on_cancel()
        else:
            self.root.quit()

    def _cleanup_bindings(self):
        """Remove global key bindings we added, so the next screen starts clean."""
        try:
            self.root.unbind("<Return>")
            self.root.unbind("<Escape>")
        except Exception:
            pass
