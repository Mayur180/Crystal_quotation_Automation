"""
Build a portable EXE of the CRYSTAL Quotation app using Nuitka.
Produces a self-contained folder in dist/CRYSTAL_Demo/

Run:  python build_manager_demo.py
"""

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent

ENTRY = "main.py"
APP_NAME = "CRYSTALQuotation"
OUTPUT_SUBDIR = "CRYSTAL_Demo"
ICON = ROOT / "assets" / "logo" / "LOGO.ico"

OUTPUT_DIR = ROOT / "dist" / OUTPUT_SUBDIR
BUILD_TMP = ROOT / "build_demo"


def _check_prereqs():
    problems = []
    if not (ROOT / ENTRY).is_file():
        problems.append(f"entry file missing: {ENTRY}")
    if not ICON.is_file():
        problems.append(f"icon missing: {ICON}")
    if not (ROOT / "assets").is_dir():
        problems.append("assets/ folder missing")
    if not (ROOT / "data").is_dir():
        problems.append("data/ folder missing")

    try:
        subprocess.run(
            [sys.executable, "-m", "nuitka", "--version"],
            check=True, capture_output=True,
        )
    except Exception:
        problems.append("nuitka not installed (run: pip install nuitka)")

    return problems


def _clean():
    for p in (OUTPUT_DIR, BUILD_TMP):
        if p.exists():
            shutil.rmtree(p, ignore_errors=True)
            print(f"[clean] removed {p.relative_to(ROOT)}")


def _human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def _size_of(p):
    try:
        if p.is_dir():
            return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        return p.stat().st_size
    except Exception:
        return 0


def main():
    print("=" * 68)
    print("  CRYSTAL Quotation — Manager Demo Build")
    print("=" * 68)
    print()

    problems = _check_prereqs()
    if problems:
        print("Cannot build:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    print("[ok] prerequisites met")
    print()

    print("Build configuration:")
    print(f"  entry:      {ENTRY}")
    print(f"  output:     dist/{OUTPUT_SUBDIR}/")
    print(f"  icon:       {ICON.relative_to(ROOT)}")
    print(f"  mode:       --standalone (folder, not onefile)")
    print()

    confirm = input("Proceed with build? [y/N] ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    _clean()

    # ============================================================
    # The Nuitka command
    # ============================================================
    args = [
        sys.executable, "-m", "nuitka",

        # ---- standalone folder (not onefile) ----
        "--standalone",

        # ---- no console window (GUI app) ----
        "--windows-console-mode=disable",

        # ---- icon ----
        f"--windows-icon-from-ico={ICON}",

        # ---- Tkinter plugin ----
        "--enable-plugin=tk-inter",

        # ---- include only what we need ----
        "--include-data-dir=assets=assets",
        "--include-data-dir=data=data",

        "--include-package=app",
        "--include-package=ui",

        "--include-module=fpdf",
        "--include-module=docx",
        "--include-module=lxml",
        "--include-module=PIL",

        # ---- skip heavy unused stuff ----
        "--nofollow-import-to=tkinter.test",
        "--nofollow-import-to=test",
        "--nofollow-import-to=tests",
        "--nofollow-import-to=numpy",
        "--nofollow-import-to=pandas",
        "--nofollow-import-to=matplotlib",
        "--nofollow-import-to=scipy",
        "--nofollow-import-to=setuptools",
        "--nofollow-import-to=distutils",
        "--nofollow-import-to=pytest",
        "--nofollow-import-to=unittest",
        "--nofollow-import-to=email",
        "--nofollow-import-to=http",
        "--nofollow-import-to=xmlrpc",
        "--nofollow-import-to=lib2to3",
        "--nofollow-import-to=pydoc",
        "--nofollow-import-to=doctest",
        "--nofollow-import-to=sqlite3.test",
        "--nofollow-import-to=concurrent.futures",
        "--nofollow-import-to=PIL.ImageQt",

        # ---- automatic download of C tooling ----
        "--assume-yes-for-downloads",

        # ---- output ----
        f"--output-dir={OUTPUT_DIR.parent}",
        f"--output-filename={APP_NAME}.exe",

        # ---- verbosity ----
        "--show-progress",
        "--show-memory",

        # ---- entry file ----
        ENTRY,
    ]

    print()
    print("=" * 68)
    print("Running Nuitka:")
    print("=" * 68)
    print(" ".join(args))
    print()
    print("This takes 3–10 minutes on first run.")
    print()

    t0 = time.time()
    try:
        result = subprocess.run(args, cwd=str(ROOT))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)

    elapsed = time.time() - t0
    print()
    print("=" * 68)

    if result.returncode != 0:
        print(f"[FAIL] Nuitka exited with code {result.returncode}")
        sys.exit(result.returncode)

    # Nuitka writes to dist/main.dist/ by default; move to our nice name
    nuitka_dist = ROOT / "dist" / "main.dist"
    if nuitka_dist.exists() and nuitka_dist != OUTPUT_DIR:
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
        shutil.move(str(nuitka_dist), str(OUTPUT_DIR))
        print(f"[ok] moved main.dist -> {OUTPUT_DIR.relative_to(ROOT)}")

    exe = OUTPUT_DIR / f"{APP_NAME}.exe"
    if exe.exists():
        size = _size_of(OUTPUT_DIR)
        print()
        print("=" * 68)
        print("  ✅ BUILD SUCCESSFUL")
        print("=" * 68)
        print(f"  Folder:  {OUTPUT_DIR}")
        print(f"  EXE:     {exe}")
        print(f"  Size:    {_human(size)}")
        print(f"  Time:    {elapsed:.0f}s")
        print()
        print("  To test:")
        print(f"    cd {OUTPUT_DIR}")
        print(f"    ./{APP_NAME}.exe")
        print()
        print("  To distribute:")
        print(f"    Zip {OUTPUT_DIR.name}/ and share.")
        print("=" * 68)
    else:
        print("[WARN] EXE not found at expected path.")
        print(f"       Look under {OUTPUT_DIR.parent}")


if __name__ == "__main__":
    main()
