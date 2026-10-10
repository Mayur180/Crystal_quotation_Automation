"""
Crystal Quotation Automation — Windows Launcher
"""

import sys
from pathlib import Path


def _setup_paths():
    """Set up sys.path for frozen and script modes."""
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent

    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

    return base


def main():
    base = _setup_paths()

    try:
        from ui.dashboard import Dashboard
    except Exception:
        import traceback
        traceback.print_exc()
        return

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
        app.geometry(f"{w}x{h}+{x}+{y}")
        app.deiconify()
        app.lift()
        app.attributes("-topmost", True)
        app.after(500, lambda: app.attributes("-topmost", False))
        app.focus_force()
    except Exception:
        pass

    app.mainloop()


if __name__ == "__main__":
    main()
