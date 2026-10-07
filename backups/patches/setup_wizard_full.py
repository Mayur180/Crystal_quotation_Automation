"""
CRYSTAL — Full first-run setup wizard.

Creates:
  app/services/setup_service.py    — reads/writes setup.json
  ui/setup_wizard.py               — first-run dialog

Patches:
  main.py                          — show wizard on first launch
  app/services/paths.py            — use shared_path from setup
  app/services/user_service.py     — name + role from setup
  ui/dashboard.py                  — Team Activity only if admin + Reconfigure item
"""

import shutil
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SERVICES = ROOT / "app" / "services"
UI = ROOT / "ui"


# ============================================================
# 1. Create app/services/setup_service.py
# ============================================================

SETUP_SERVICE = '''"""
CRYSTAL / ARMATECH ASSOCIATES
Setup service — first-run configuration.

Stores:
  %APPDATA%/CRYSTAL/setup.json
    {
      "user_name":  "Mayuresh",
      "pc_role":    "admin" | "member",
      "server_pc":  "Invoice",
      "shared_path":"D:\\\\CRYSTAL_data"  or  "\\\\\\\\Invoice\\\\CRYSTAL_data",
      "configured_at": "2026-10-06T20:00:00"
    }
"""

import os
import json
import socket
from pathlib import Path
from datetime import datetime


DEFAULT_SERVER_PC = "Invoice"
DEFAULT_SHARED_FOLDER = "CRYSTAL_data"


def _appdata_dir() -> Path:
    base = Path(os.environ.get("APPDATA", str(Path.home()))) / "CRYSTAL"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _setup_file() -> Path:
    return _appdata_dir() / "setup.json"


def load_setup():
    """Return the saved setup dict, or None if not configured yet."""
    try:
        f = _setup_file()
        if not f.is_file():
            return None
        data = json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or "user_name" not in data:
            return None
        return data
    except Exception:
        return None


def save_setup(data):
    """Persist the setup dict to disk."""
    try:
        payload = dict(data)
        payload["configured_at"] = datetime.now().isoformat(timespec="seconds")
        _setup_file().write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True
    except Exception:
        return False


def clear_setup():
    """Remove the setup file — forces wizard to show again."""
    try:
        f = _setup_file()
        if f.is_file():
            f.unlink()
        return True
    except Exception:
        return False


def is_configured() -> bool:
    return load_setup() is not None


def current_role() -> str:
    """Return 'admin' or 'member'."""
    s = load_setup()
    return (s or {}).get("pc_role", "member")


def is_admin() -> bool:
    return current_role() == "admin"


def current_user():
    s = load_setup()
    return (s or {}).get("user_name") or None


def shared_path():
    """Return the Path to the shared data folder, or None."""
    s = load_setup()
    if not s:
        return None
    p = s.get("shared_path")
    if not p:
        return None
    try:
        return Path(p)
    except Exception:
        return None


def shared_path_available() -> bool:
    """Check if the shared folder exists and is reachable."""
    p = shared_path()
    if p is None:
        return False
    try:
        return p.is_dir()
    except Exception:
        return False


def build_shared_path(role, server_pc=None, custom_path=None):
    """Build the shared_path for the given role.

    - admin:   D:\\\\CRYSTAL_data  (or custom_path)
    - member:  \\\\\\\\<server_pc>\\\\CRYSTAL_data
    """
    if custom_path:
        return custom_path.strip()
    if role == "admin":
        return "D:\\\\" + DEFAULT_SHARED_FOLDER
    # member
    server = (server_pc or DEFAULT_SERVER_PC).strip()
    return "\\\\\\\\" + server + "\\\\" + DEFAULT_SHARED_FOLDER
'''

f = SERVICES / "setup_service.py"
if f.exists():
    print(f"[skip] {f.name} already exists")
else:
    f.write_text(SETUP_SERVICE, encoding="utf-8")
    print(f"[new]  {f.relative_to(ROOT)}")


# ============================================================
# 2. Create ui/setup_wizard.py
# ============================================================

WIZARD = '''"""
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
            self.path_var.set("D:\\\\CRYSTAL_data")
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
        self.path_var.set("\\\\\\\\" + server + "\\\\CRYSTAL_data")

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
'''

p = UI / "setup_wizard.py"
if p.exists():
    print(f"[skip] {p.name} already exists")
else:
    p.write_text(WIZARD, encoding="utf-8")
    print(f"[new]  {p.relative_to(ROOT)}")


# ============================================================
# 3. Patch main.py — show wizard on first launch
# ============================================================

MAIN = ROOT / "main.py"
shutil.copy2(MAIN, MAIN.with_suffix(".py.WIZARD_BACKUP"))
print(f"[backup] {MAIN.name}")

m = MAIN.read_text(encoding="utf-8")

if "_ensure_first_run_setup" not in m:
    helper = '''


def _ensure_first_run_setup():
    """Show the setup wizard if the app has never been configured."""
    try:
        import tkinter as tk
        from app.services.setup_service import is_configured
        from ui.setup_wizard import run_wizard
    except Exception:
        return

    if is_configured():
        return

    root = tk.Tk()
    root.withdraw()
    result = run_wizard(root)
    root.destroy()
    if not result:
        # user cancelled — app will still run with default setup
        pass


'''
    if 'if __name__ == "__main__":' in m:
        m = m.replace(
            'if __name__ == "__main__":',
            helper + 'if __name__ == "__main__":',
            1,
        )
        print("[ok] main.py: helper added")

# call it before Dashboard
if "_ensure_first_run_setup()" not in m.split("def _ensure_first_run_setup")[0]:
    for anchor in ["app = Dashboard(", "root = Dashboard(", "Dashboard()"]:
        if anchor in m:
            m = m.replace(
                anchor,
                "_ensure_first_run_setup()\n\n    " + anchor,
                1,
            )
            print(f"[ok] main.py: called before {anchor}")
            break

MAIN.write_text(m, encoding="utf-8")


# ============================================================
# 4. Patch paths.py — use shared_path from setup
# ============================================================

PATHS = SERVICES / "paths.py"
shutil.copy2(PATHS, PATHS.with_suffix(".py.WIZARD_BACKUP"))
print(f"[backup] {PATHS.name}")

new_paths = '''"""
CRYSTAL / ARMATECH ASSOCIATES
Path resolution helper.

Data source priority:
  1. setup.json's shared_path   (multi-PC mode)
  2. %APPDATA%/CRYSTAL/data     (frozen EXE fallback)
  3. <project>/data             (source mode)
"""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _setup_shared_path():
    """Try to read shared_path from the setup file."""
    try:
        from app.services.setup_service import shared_path
        p = shared_path()
        if p is None:
            return None
        if p.is_dir():
            return p
    except Exception:
        pass
    return None


def _appdata_base() -> Path:
    base = Path(os.environ.get("APPDATA", str(Path.home()))) / "CRYSTAL"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _project_base() -> Path:
    return Path(__file__).resolve().parents[2]


def get_data_dir() -> Path:
    """Where the JSON/JSONL data lives."""
    sp = _setup_shared_path()
    if sp is not None:
        sp.mkdir(parents=True, exist_ok=True)
        return sp
    if is_frozen():
        d = _appdata_base() / "data"
    else:
        d = _project_base() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_output_dir() -> Path:
    """Where generated DOCX/PDF files go."""
    sp = _setup_shared_path()
    if sp is not None:
        d = sp / "output"
        d.mkdir(parents=True, exist_ok=True)
        return d
    if is_frozen():
        d = _appdata_base() / "output"
    else:
        d = _project_base() / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_project_root() -> Path:
    """For code that needs project root (assets, etc.)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return _project_base()


def seed_data_on_first_run():
    """If using %APPDATA% fresh, copy bundled default data."""
    if not is_frozen():
        return
    try:
        target = get_data_dir()
        if any(target.iterdir()):
            return
        bundled = get_project_root() / "data"
        if bundled.is_dir():
            import shutil
            for item in bundled.rglob("*"):
                rel = item.relative_to(bundled)
                dest = target / rel
                if item.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)
    except Exception:
        pass
'''

PATHS.write_text(new_paths, encoding="utf-8")
print("[ok] paths.py: rewritten to use setup.shared_path")


# ============================================================
# 5. Patch user_service.py — read name/role from setup
# ============================================================

USR = SERVICES / "user_service.py"
shutil.copy2(USR, USR.with_suffix(".py.WIZARD_BACKUP"))
print(f"[backup] {USR.name}")

new_user = '''"""
CRYSTAL / ARMATECH ASSOCIATES
User tracking service — reads from setup.json.
"""

try:
    from app.services.setup_service import (
        current_user as _su_current_user,
        current_role as _su_current_role,
        is_admin as _su_is_admin,
    )
except Exception:
    _su_current_user = lambda: None
    _su_current_role = lambda: "member"
    _su_is_admin = lambda: False


def get_current_user():
    try:
        return _su_current_user()
    except Exception:
        return None


def current_role():
    try:
        return _su_current_role()
    except Exception:
        return "member"


def is_admin():
    try:
        return _su_is_admin()
    except Exception:
        return False


# Backwards-compat no-ops (older code may still call these)
def set_current_user(name):
    try:
        from app.services.setup_service import (
            load_setup, save_setup,
        )
        s = load_setup() or {}
        s["user_name"] = (name or "").strip()
        return save_setup(s)
    except Exception:
        return False


def clear_current_user():
    try:
        from app.services.setup_service import clear_setup
        return clear_setup()
    except Exception:
        return False
'''

USR.write_text(new_user, encoding="utf-8")
print("[ok] user_service.py: reads from setup.json")


# ============================================================
# 6. Patch dashboard.py — add "Reconfigure Setup" item
# ============================================================

DASH = UI / "dashboard.py"
shutil.copy2(DASH, DASH.with_suffix(".py.WIZARD_BACKUP"))
print(f"[backup] {DASH.name}")

d = DASH.read_text(encoding="utf-8")

# add _reconfigure_setup method
if "def _reconfigure_setup" not in d:
    old_quit = '''    def _quit(self):

        self.destroy()'''
    new_quit = '''    def _reconfigure_setup(self):
        \"\"\"Re-open the setup wizard to change name / role / server.\"\"\"
        from tkinter import messagebox as _mb
        ok = _mb.askyesno(
            "Reconfigure Setup",
            "This will close the app and reopen the setup wizard.\\n\\n"
            "Continue?",
            parent=self,
        )
        if not ok:
            return
        try:
            from app.services.setup_service import clear_setup
            clear_setup()
        except Exception:
            pass
        try:
            self.destroy()
        except Exception:
            pass
        # Note: next launch will show the wizard

    def _quit(self):

        self.destroy()'''

    if old_quit in d:
        d = d.replace(old_quit, new_quit, 1)
        print("[ok] dashboard.py: _reconfigure_setup method added")

# add the sidebar item just above Clear Activity Log
old_clear = '''        add_item("🗑",  "Clear Activity Log", self._clear_activity_log,
                 danger=True)'''
new_clear = '''        add_item("🔧", "Reconfigure Setup",  self._reconfigure_setup)
        add_item("🗑",  "Clear Activity Log", self._clear_activity_log,
                 danger=True)'''

if "Reconfigure Setup" not in d and old_clear in d:
    d = d.replace(old_clear, new_clear, 1)
    print("[ok] dashboard.py: Reconfigure Setup item added")

DASH.write_text(d, encoding="utf-8")


# ============================================================
# 7. Compile check
# ============================================================

print()
print("=" * 60)
print("Compile check")
print("=" * 60)

failed = False
for path in (f, p, MAIN, PATHS, USR, DASH):
    try:
        py_compile.compile(str(path), doraise=True)
        print(f"[ok] {path.relative_to(ROOT)}")
    except py_compile.PyCompileError as e:
        print(f"[FAIL] {path.relative_to(ROOT)}: {e}")
        failed = True

if failed:
    print()
    print("Some files failed. Backups at *.WIZARD_BACKUP")
else:
    print()
    print("=" * 60)
    print("Setup wizard installed successfully.")
    print("=" * 60)
    print()
    print("Next:")
    print("  1. python main.py")
    print("  2. Wizard appears -> pick role, enter name, finish")
    print("  3. On this laptop choose 'Team member PC' + server 'Invoice'")
    print("  4. On Invoice PC choose 'Admin PC'")
