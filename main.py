"""
CRYSTAL / ARMATECH ASSOCIATES
Main entry point — v4 multi-module launcher.

Flow:
  Login → (Launcher if multi-module) → Dashboard

CRITICAL SAFETY (v3 lessons learned):
  - Only ONE tk.Tk() instance exists at any moment.
  - Between phases, the old Tk is destroyed AND released.
  - gc.collect() runs between phases to release Tcl resources.
  - This prevents the multi-root crash that plagued v3.
"""

import sys
import gc
from pathlib import Path


# ============================================================
# PATH SETUP (frozen EXE + script)
# ============================================================

def _setup_paths():
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))
    return base


# ============================================================
# GUI PHASE RUNNERS
# Each phase creates its own Tk, runs, and returns a result.
# The Tk is destroyed before returning.
# ============================================================

def _phase_login():
    """Show login. Returns UserSession on success, None on cancel."""
    import tkinter as tk
    from ui.login_window import LoginWindow

    result = {"session": None}
    root = tk.Tk()
    root.title("CRYSTAL v4 — Login")
    root.geometry("700x600")
    root.configure(bg="#F4F6F8")
    _center_window(root, 700, 600)

    def on_success(session):
        result["session"] = session
        root.quit()

    def on_cancel():
        result["session"] = None
        root.quit()

    LoginWindow(root, on_success=on_success, on_cancel=on_cancel)

    root.protocol("WM_DELETE_WINDOW", on_cancel)
    root.mainloop()

    # Fully release Tk
    try:
        root.destroy()
    except Exception:
        pass
    del root
    gc.collect()

    return result["session"]


def _phase_launcher(session):
    """Show module selector. Returns module name, or None if logout."""
    import tkinter as tk
    from ui.launcher_window import LauncherWindow

    result = {"module": None, "action": "cancel"}
    root = tk.Tk()
    root.title("CRYSTAL v4 — Choose Module")
    root.geometry("900x650")
    root.configure(bg="#F4F6F8")
    _center_window(root, 900, 650)

    def on_select(module_name):
        result["module"] = module_name
        result["action"] = "select"
        root.quit()

    def on_logout():
        result["action"] = "logout"
        root.quit()

    LauncherWindow(root, session=session,
                   on_select=on_select, on_logout=on_logout)

    root.protocol("WM_DELETE_WINDOW", on_logout)
    root.mainloop()

    # Fully release Tk
    try:
        root.destroy()
    except Exception:
        pass
    del root
    gc.collect()

    return result


def _phase_dashboard(session):
    """Launch the actual dashboard. This is the final, main Tk."""
    from app.services import paths
    from ui.dashboard import Dashboard

    # Set the active module BEFORE creating the dashboard
    paths.set_active_module(session.active_module)

    # Dashboard creates its own tk.Tk() internally (class inherits tk.Tk)
    app = Dashboard()

    # Center + show
    try:
        app.update_idletasks()
        sw = app.winfo_screenwidth()
        sh = app.winfo_screenheight()
        w, h = 1280, 820
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        app.geometry(f"{w}x{h}+{x}+{y}")
        app.deiconify()
        app.lift()
        app.focus_force()
    except Exception:
        pass

    app.mainloop()


# ============================================================
# HELPERS
# ============================================================

def _center_window(root, w, h):
    root.update_idletasks()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 2)
    root.geometry(f"{w}x{h}+{x}+{y}")


# ============================================================
# MAIN ENTRY
# ============================================================

def main():
    _setup_paths()

    try:
        from app.services import paths
        paths.seed_data_on_first_run()
    except Exception:
        pass

    # ---- PHASE 1: LOGIN ----
    session = _phase_login()
    if session is None:
        print("Login cancelled. Exiting.")
        return

    print(f"✅ Logged in as {session.username} "
          f"(modules: {session.modules})")

    # ---- PHASE 2: LAUNCHER (only if multi-module) ----
    if session.is_multi_module():
        result = _phase_launcher(session)
        if result["action"] == "logout":
            # Restart the whole flow
            return main()
        if result["module"] is None:
            print("No module selected. Exiting.")
            return
        session.active_module = result["module"]
    else:
        # Single module — auto-select
        session.active_module = session.modules[0]

    print(f"🚀 Launching module: {session.active_module}")

    # ---- PHASE 3: DASHBOARD ----
    _phase_dashboard(session)


if __name__ == "__main__":
    main()
