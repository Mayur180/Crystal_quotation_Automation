from pathlib import Path

p = Path("main.py")
s = p.read_text(encoding="utf-8")

# Replace main()
old_main = '''def main():
    base = _setup_paths()
    print(f"Crystal Quotation Automation")
    print(f"Base directory: {base}")
    print()

    try:
        from ui.dashboard import Dashboard
    except Exception as exc:
        print("ERROR: Could not load dashboard.")
        print(f"{type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        return

    _ensure_first_run_setup()

    app = Dashboard()

    # Force window to appear on-screen
    try:
        app.update_idletasks()
        sw = app.winfo_screenwidth()
        sh = app.winfo_screenheight()
        w = 1280
        h = 820
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        app.geometry(f'{w}x{h}+{x}+{y}')
        app.deiconify()
        app.lift()
        app.attributes('-topmost', True)
        app.after(500, lambda: app.attributes('-topmost', False))
    except Exception as e:
        print(f'[window-fix] {e}')

    app.mainloop()'''

new_main = '''def main():
    base = _setup_paths()
    print(f"Crystal Quotation Automation")
    print(f"Base directory: {base}")
    print()

    try:
        from ui.dashboard import Dashboard
    except Exception as exc:
        print("ERROR: Could not load dashboard.")
        print(f"{type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        return

    # ---- Create the ONE AND ONLY Tk root ----
    app = Dashboard()
    app.withdraw()  # hide until ready

    # Position window on-screen (before showing)
    try:
        app.update_idletasks()
        sw = app.winfo_screenwidth()
        sh = app.winfo_screenheight()
        w = 1280
        h = 820
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        app.geometry(f'{w}x{h}+{x}+{y}')
    except Exception as e:
        print(f'[window-fix] {e}')

    # Show setup wizard as a TOPLEVEL on top of Dashboard (no new Tk root)
    _ensure_first_run_setup(app)

    # Now show the dashboard
    try:
        app.deiconify()
        app.lift()
        app.attributes('-topmost', True)
        app.after(500, lambda: app.attributes('-topmost', False))
        app.focus_force()
    except Exception as e:
        print(f'[window-show] {e}')

    app.mainloop()'''

if old_main in s:
    s = s.replace(old_main, new_main, 1)
    print("[ok] main() patched — single Tk root")
else:
    print("[warn] main() pattern not found")

# Replace _ensure_first_run_setup
old_setup = '''def _ensure_first_run_setup():
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
        pass'''

new_setup = '''def _ensure_first_run_setup(parent):
    """Show the setup wizard if the app has never been configured.

    Uses the existing Dashboard root as parent. Does NOT create a new Tk.
    """
    try:
        from app.services.setup_service import is_configured
        from ui.setup_wizard import run_wizard
    except Exception:
        return

    if is_configured():
        return

    # Pass existing root — wizard uses a Toplevel, not a new Tk
    result = run_wizard(parent)
    if not result:
        pass'''

if old_setup in s:
    s = s.replace(old_setup, new_setup, 1)
    print("[ok] _ensure_first_run_setup patched")
else:
    print("[warn] _ensure_first_run_setup pattern not found")

p.write_text(s, encoding="utf-8")
print()
print("Done.")
