"""
CRYSTAL / ARMATECH ASSOCIATES
Build script — packages the app into a single Windows EXE with Nuitka.

Run:  python build_exe.py

Review the printed Nuitka command first. Then confirm to proceed.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ------------------------------------------------------------
# CONFIG — tweak these if needed
# ------------------------------------------------------------

ENTRY_FILE = "main.py"
OUTPUT_NAME = "CrystalQuotation.exe"
ICON_PATH = ROOT / "assets" / "logo" / "LOGO.ico"
OUTPUT_DIR = ROOT / "dist"
DIST_FOLDER = ROOT / "main.dist"         # Nuitka's standalone folder
ONEFILE_TMP = ROOT / "main.onefile-build"  # Nuitka's onefile temp
BUILD_DIR = ROOT / "main.build"           # Nuitka's build cache

# Nuitka flags for a clean one-file, no-console, icon-bearing EXE
NUITKA_ARGS = [
    sys.executable, "-m", "nuitka",

    # Core build type
    "--standalone",
    "--onefile",

    # Windows behaviour
    "--windows-console-mode=disable",
    f"--windows-icon-from-ico={ICON_PATH}",

    # Bundled assets + data
    "--include-data-dir=assets=assets",
    "--include-data-dir=data=data",

    # App packages
    "--include-package=app",
    "--include-package=ui",

    # Third-party runtime deps actually used
    "--include-module=fpdf",
    "--include-module=docx",

    # Tkinter plugin (needed for GUI apps)
    "--enable-plugin=tk-inter",

    # Stop Nuitka from wandering into huge unused libs
    "--nofollow-import-to=tkinter.test",
    "--nofollow-import-to=test",
    "--nofollow-import-to=tests",
    "--nofollow-import-to=numpy",
    "--nofollow-import-to=pandas",
    "--nofollow-import-to=matplotlib",
    "--nofollow-import-to=scipy",
    "--nofollow-import-to=pytest",
    "--nofollow-import-to=PIL.ImageQt",
    "--nofollow-import-to=setuptools",
    "--nofollow-import-to=distutils",

    # Auto-accept downloads (Nuitka may fetch a C compiler helper)
    "--assume-yes-for-downloads",

    # Output
    f"--output-dir={OUTPUT_DIR}",
    f"--output-filename={OUTPUT_NAME}",

    # Quiet-ish output
    "--show-progress",
    "--show-memory",

    # Entry file (must be last)
    ENTRY_FILE,
]


def _clean_previous():
    """Remove leftover build folders so the build starts fresh."""
    for p in (OUTPUT_DIR, DIST_FOLDER, ONEFILE_TMP, BUILD_DIR):
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
            print(f"[clean] removed {p.name}/")
    # Also remove old exe directly under root if present
    stray = ROOT / OUTPUT_NAME
    if stray.exists():
        stray.unlink()
        print(f"[clean] removed {stray.name}")


def _check_inputs():
    """Verify required files exist before we start."""
    problems = []
    if not (ROOT / ENTRY_FILE).exists():
        problems.append(f"entry file not found: {ENTRY_FILE}")
    if not ICON_PATH.exists():
        problems.append(f"icon not found: {ICON_PATH}")
    if not (ROOT / "assets").is_dir():
        problems.append("assets/ folder missing")
    if not (ROOT / "data").is_dir():
        problems.append("data/ folder missing")
    return problems


def _print_command():
    print("=" * 68)
    print("Nuitka command to be run:")
    print("=" * 68)
    print(" ".join(NUITKA_ARGS))
    print("=" * 68)


def main():
    print(f"Project root: {ROOT}\n")

    problems = _check_inputs()
    if problems:
        print("Cannot build:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    print("All inputs present.\n")

    answer = input("Proceed with build?  [y/N] ").strip().lower()
    if answer != "y":
        print("Cancelled.")
        return

    _clean_previous()

    _print_command()
    print("Starting Nuitka build (this can take 2-10 minutes)...\n")

    try:
        result = subprocess.run(NUITKA_ARGS, cwd=str(ROOT))
    except KeyboardInterrupt:
        print("\nBuild interrupted by user.")
        sys.exit(130)

    print("\n" + "=" * 68)
    if result.returncode == 0:
        exe = OUTPUT_DIR / OUTPUT_NAME
        if exe.exists():
            size_mb = exe.stat().st_size / (1024 * 1024)
            print(f"[ok] build succeeded")
            print(f"     output: {exe}")
            print(f"     size:   {size_mb:.1f} MB")
        else:
            print("[warn] Nuitka finished but EXE not found where expected.")
            print(f"       look under {OUTPUT_DIR}")
    else:
        print(f"[fail] Nuitka exited with code {result.returncode}")
        print("       Scroll up to see the error.")
    print("=" * 68)


if __name__ == "__main__":
    main()
