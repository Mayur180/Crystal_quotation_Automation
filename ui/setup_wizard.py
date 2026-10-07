"""
CRYSTAL / ARMATECH ASSOCIATES
First-run setup wizard.
"""

import tkinter as tk
from tkinter import ttk, messagebox


try:
    from app.services.setup_service import (
        load_setup,
        save_setup,
        build_shared_path,
        DEFAULT_SERVER_PC,
    )
except Exception:
    load_setup = None
    save_setup = None
    build_shared_path = None
    DEFAULT_SERVER_PC = "Invoice"


class SetupWizard(tk.Toplevel):

    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    BORDER = "#E1E4E8"
    RED = "#C40000"

    def __init__(self, parent=None):
        super().__init__(parent)

        self.title("CRYSTAL Setup")
        self.geometry("560x460")
        self.minsize(520, 420)
        self.configure(bg=self.BG)
        self.resizable(False, False)

        try:
            self.transient(parent)
            self.grab_set()
        except Exception:
            pass

        self.result = None

        existing = load_setup() if load_setup else None

        self.name_var = tk.StringVar(
            value=(existing or {}).get("user_name", "")
        )
        self.role_var = tk.StringVar(
            value=(existing or {}).get("pc_role", "member")
        )
        self.server_var = tk.StringVar(
            value=(existing or {}).get("server_pc", DEFAULT_SERVER_PC)
        )
        self.path_var = tk.StringVar(
            value=(existing or {}).get("shared_path", "")
        )

        self._build()

        try:
            self.bind("<Escape>", lambda _e: self._cancel())
            self.protocol("WM_DELETE_WINDOW", self._cancel)
        except Exception:
            pass

        # center on screen
        self.update_idletasks()
        w, h = 560, 460
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        tk.Label(
            self, text="Welcome to CRYSTAL",
            bg=self.BG, fg=self.TEXT,
            font=("Arial", 18, "bold"),
        ).pack(pady=(24, 4))

        tk.Label(
            self, text="Let's set up this PC in one step.",
            bg=self.BG, fg=self.MUTED,
            font=("Arial", 10),
        ).pack(pady=(0, 18))

        card = tk.Frame(self, bg=self.CARD,
                        highlightbackground=self.BORDER,
                        highlightthickness=1)
        card.pack(fill="both", expand=True, padx=24, pady=(0, 12))

        inner = tk.Frame(card, bg=self.CARD)
        inner.pack(fill="both", expand=True, padx=22, pady=18)

        # name
        tk.Label(inner, text="Your name", bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 8, "bold"), anchor="w").pack(fill="x")
        tk.Entry(inner, textvariable=self.name_var,
                 bg="white", fg=self.TEXT, relief="solid", bd=1,
                 font=("Arial", 11), insertbackground=self.RED,
                 ).pack(fill="x", ipady=6, pady=(2, 14))

        # role
        tk.Label(inner, text="This PC is", bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 8, "bold"), anchor="w").pack(fill="x")
        role_box = tk.Frame(inner, bg=self.CARD)
        role_box.pack(fill="x", pady=(2, 14))

        tk.Radiobutton(
            role_box, text="Admin PC (holds shared folder)",
            variable=self.role_var, value="admin",
            command=self._on_role_change,
            bg=self.CARD, fg=self.TEXT, selectcolor="white",
            activebackground=self.CARD,
            font=("Arial", 10), anchor="w",
        ).pack(fill="x")
        tk.Radiobutton(
            role_box, text="Team member PC (connects to admin PC)",
            variable=self.role_var, value="member",
            command=self._on_role_change,
            bg=self.CARD, fg=self.TEXT, selectcolor="white",
            activebackground=self.CARD,
            font=("Arial", 10), anchor="w",
        ).pack(fill="x")

        # server PC (only shown for member)
        self.server_frame = tk.Frame(inner, bg=self.CARD)
        self.server_frame.pack(fill="x", pady=(0, 14))
        tk.Label(self.server_frame, text="Server PC name",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 8, "bold"), anchor="w").pack(fill="x")
        tk.Entry(self.server_frame, textvariable=self.server_var,
                 bg="white", fg=self.TEXT, relief="solid", bd=1,
                 font=("Arial", 11), insertbackground=self.RED,
                 ).pack(fill="x", ipady=6, pady=(2, 0))

        # shared path (editable, auto-filled)
        tk.Label(inner, text="Shared folder path",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 8, "bold"), anchor="w").pack(fill="x")
        tk.Entry(inner, textvariable=self.path_var,
                 bg="#F8F9FA", fg=self.TEXT, relief="solid", bd=1,
                 font=("Arial", 10), insertbackground=self.RED,
                 ).pack(fill="x", ipady=5, pady=(2, 4))

        self.hint_lbl = tk.Label(
            inner, text="", bg=self.CARD, fg=self.MUTED,
            font=("Arial", 8, "italic"), anchor="w",
        )
        self.hint_lbl.pack(fill="x")

        # buttons
        btns = tk.Frame(self, bg=self.BG)
        btns.pack(fill="x", padx=24, pady=(0, 18))

        tk.Button(
            btns, text="Cancel", command=self._cancel,
            bg="white", fg=self.MUTED,
            activebackground="#F3F4F6",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 10), cursor="hand2",
            padx=18, pady=8,
        ).pack(side="right")

        tk.Button(
            btns, text="Finish Setup", command=self._finish,
            bg=self.RED, fg="white",
            activebackground=self.RED, activeforeground="white",
            relief="flat", bd=0, highlightthickness=0,
            font=("Arial", 10, "bold"), cursor="hand2",
            padx=18, pady=8,
        ).pack(side="right", padx=(0, 10))

        self._on_role_change()

    def _on_role_change(self):
        role = self.role_var.get()
        if role == "admin":
            self.server_frame.pack_forget()
            self.path_var.set("D:\\CRYSTAL_data")
            self.hint_lbl.configure(
                text="This PC holds the shared data folder.",
            )
        else:
            # show server frame again (pack if hidden)
            try:
                self.server_frame.pack(fill="x", pady=(0, 14))
            except Exception:
                pass
            self._refresh_member_path()
            self.hint_lbl.configure(
                text="Connects to the admin PC over the network.",
            )

    def _refresh_member_path(self):
        server = (self.server_var.get() or DEFAULT_SERVER_PC).strip()
        self.path_var.set("\\\\" + server + "\\CRYSTAL_data")

    def _finish(self):
        name = (self.name_var.get() or "").strip()
        if not name:
            messagebox.showwarning(
                "Missing name", "Please enter your name.",
                parent=self,
            )
            return

        role = self.role_var.get()
        server = (self.server_var.get() or "").strip()

        if role == "member" and not server:
            messagebox.showwarning(
                "Missing server PC",
                "Please enter the admin PC's name.",
                parent=self,
            )
            return

        path = (self.path_var.get() or "").strip()
        if not path:
            path = build_shared_path(role, server) if build_shared_path else ""

        payload = {
            "user_name": name,
            "pc_role": role,
            "server_pc": server,
            "shared_path": path,
        }
        if save_setup and save_setup(payload):
            self.result = payload
            self.destroy()
        else:
            messagebox.showerror(
                "Could not save",
                "Failed to write setup file.",
                parent=self,
            )

    def _cancel(self):
        self.result = None
        self.destroy()


def run_wizard(parent=None):
    """Show the wizard. Returns the saved config dict or None if cancelled."""
    try:
        w = SetupWizard(parent)
        w.wait_window()
        return w.result
    except Exception:
        return None


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    print(run_wizard(root))
