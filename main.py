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
    
    # Check for saved session (auto-login)
    try:
        import json
        from app.services.paths import get_data_root
        session_file = get_data_root() / "session.json"
        if session_file.exists():
            session_data = json.loads(session_file.read_text(encoding='utf-8'))
            # Reconstruct the UserSession from saved data
            from app.services.auth_service import UserSession
            saved_session = UserSession(
                user_id=session_data.get("user_id", ""),
                username=session_data.get("username", ""),
                full_name=session_data.get("full_name", ""),
                modules=session_data.get("modules", []),
            )
            # Verify the user still exists and is active
            from app.services.user_service import find_user_by_username
            user = find_user_by_username(saved_session.username)
            if user and user.get("is_active", True):
                print(f"[auto-login] Welcome back, {saved_session.username}!")
                return saved_session
            else:
                # User no longer exists or is inactive — delete the session
                session_file.unlink()
                print("[auto-login] Session invalid, please log in again.")
    except Exception as e:
        print(f"[auto-login] Could not auto-login: {e}")

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
    """Show module selector. Returns dict with action: select/logout/exit."""
    import tkinter as tk
    from ui.launcher_window import LauncherWindow

    result = {"module": None, "action": "exit"}
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

    def on_close():
        result["action"] = "exit"
        root.quit()

    LauncherWindow(root, session=session,
                   on_select=on_select, on_logout=on_logout)

    root.protocol("WM_DELETE_WINDOW", on_close)
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
    """Launch the actual dashboard. This is the final, main Tk.

    Returns "logout" if the user clicked Logout, otherwise None.
    """
    from app.services import paths
    # Route to the correct module dashboard
    from app.services.paths import get_active_module

    logged_out = {"value": False}

    # Determine the correct module based on the user's assigned modules
    user_modules = getattr(session, "modules", []) or []
    
    # If the user has both modules, use the active module (last used), default to VMM if not set
    # If the user has only one, force that one.
    if "VMM" in user_modules and "Crystal" in user_modules:
        active = get_active_module()
        if active not in ("VMM", "Crystal"):
            active = "VMM"
    elif "Crystal" in user_modules:
        active = "Crystal"
    elif "VMM" in user_modules:
        active = "VMM"
    else:
        active = "VMM"  # fallback
        
    try:
        from app.services.paths import set_active_module
        set_active_module(active)
    except Exception:
        pass

    if get_active_module() == "Crystal":
        from ui.crystal.dashboard import Dashboard as CrystalDashboard
        from tkinter import messagebox

        def _do_logout():
            if not messagebox.askyesno(
                "Log Out",
                "Log out and return to login?",
            ):
                return
            # Clear the saved session on logout
            try:
                import json
                from app.services.paths import get_data_root
                session_file = get_data_root() / "session.json"
                if session_file.exists():
                    session_file.unlink()
            except Exception:
                pass
            logged_out["value"] = True
            app.quit()

        app = CrystalDashboard(
            username=getattr(session, "username", "Admin"),
            module="Crystal",
            on_logout=_do_logout,
        )
        app.mainloop()

        # Release Tk before next phase
        try:
            app.destroy()
        except Exception:
            pass
        import gc; gc.collect()

        return "logout" if logged_out["value"] else None

    else:
        from ui.vmm.dashboard import Dashboard

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

    # ---- SYNC USERS FROM GOOGLE SHEETS ----
    try:
        from app.services.user_service import fetch_users_from_sheet
        fetch_users_from_sheet()
    except Exception as e:
        print(f"[startup] Could not sync users: {e}")

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
        print(f"[DEBUG] Launcher returned: action={result['action']}, module={result['module']}")
        if result["action"] == "exit":
            print("[DEBUG] Exiting application.")
            return
        if result["action"] == "logout":
            print("[DEBUG] Logout detected — clearing session and restarting...")
            # Delete session file so auto-login doesn't fire
            try:
                from app.services.paths import get_data_root
                session_file = get_data_root() / "session.json"
                if session_file.exists():
                    session_file.unlink()
                    print("[DEBUG] Session file deleted.")
            except Exception as e:
                print(f"[DEBUG] Could not delete session: {e}")
            return main()
        if result["module"] is None:
            print("[DEBUG] No module selected. Exiting.")
            return
        session.active_module = result["module"]
    else:
        # Single module — auto-select
        session.active_module = session.modules[0]

    print(f"🚀 Launching module: {session.active_module}")

    # ---- PHASE 3: DASHBOARD ----
    result = _phase_dashboard(session)
    if result == "logout":
        return main()


if __name__ == "__main__":
    main()
