"""
CRYSTAL / ARMATECH ASSOCIATES
Quotation Management System — Entry point.

Works both as a Python script and as a frozen .exe.
"""

import os
import sys
from pathlib import Path


# ============================================================
# PROJECT ROOT — works for script and frozen .exe
# ============================================================

def get_project_root():
    """Return the project root, working in both script and frozen modes."""
    if getattr(sys, "frozen", False):
        # Frozen .exe — use the folder containing the .exe
        return Path(sys.executable).parent
    else:
        # Normal Python — use the folder containing run.py
        return Path(__file__).resolve().parent


PROJECT_ROOT = get_project_root()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# MAIN
# ============================================================

def main():
    print("CRYSTAL Quotation Automation")
    print(f"Project root: {PROJECT_ROOT}")
    print("Starting quotation system...")
    print()

    try:
        from ui.dashboard import Dashboard
    except Exception as exc:
        print("ERROR: Could not load dashboard.")
        print("-" * 40)
        print(f"{type(exc).__name__}: {exc}")
        print("-" * 40)
        raise

    app = Dashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
