"""
CRYSTAL — Setup %APPDATA% paths + (optionally) build EXE
=========================================================

Run:  python setup_appdata_build.py

This script:
  1. Creates app/services/paths.py
  2. Patches app/services/*.py to use get_data_dir()
  3. Backs up each patched file
  4. Compile-checks
  5. Optionally builds the EXE with Nuitka (--onefile)

Safe: every file is backed up before modification.
"""

import shutil
import subprocess
import sys
import py_compile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SERVICES = ROOT / "app" / "services"
PATHS_PY = SERVICES / "paths.py"

# ============================================================
# The shared helper file
# ============================================================

PATHS_PY_CONTENT = '''"""
CRYSTAL / ARMATECH ASSOCIATES
Path resolution helper.

When running as a script  → uses <project>/data/
When running as a frozen EXE → uses %APPDATA%/CRYSTAL/data/
"""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def _base_dir() -> Path:
    if is_frozen():
        base = Path(os.environ.get("APPDATA", str(Path.home()))) / "CRYSTAL"
    else:
        base = Path(__file__).resolve().parents[2]
    base.mkdir(parents=True, exist_ok=True)
    return base


def get_data_dir() -> Path:
    """Return the data folder (project/data or %APPDATA%/CRYSTAL/data)."""
    d = _base_dir() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_output_dir() -> Path:
    """Return the output folder (project/output or %APPDATA%/CRYSTAL/output)."""
    d = _base_dir() / "output"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_project_root() -> Path:
    """For code that still needs the project root (assets, etc.)."""
    if is_frozen():
        # When frozen, assets are bundled next to the EXE.
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def seed_data_on_first_run():
    """Copy bundled default data into %APPDATA%/CRYSTAL/data/ the first time
    the EXE is launched, if the folder is empty."""
    if not is_frozen():
        return
    try:
        target = get_data_dir()
        # if already populated, skip
        if any(target.iterdir()):
            return
        # find bundled data folder (next to EXE)
        bundled = get_project_root() / "data"
        if bundled.is_dir():
            for item in bundled.rglob("*"):
                rel = item.relative_to(bundled)
                dest = target / rel
                if item.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)
            print(f"[seed] copied default data to {target}")
    except Exception as e:
        print(f"[seed] skipped: {e}")
'''

# ============================================================
# Per-service patch rules
# ============================================================

PATCHES = [
    {
        "file": "quotation_history_service.py",
        "find": [
            'PROJECT_ROOT = Path(__file__).resolve().parents[2]',
            '_LEGACY_DATA_DIR = PROJECT_ROOT / "data"',
        ],
        "replace": [
            'from app.services.paths import get_data_dir',
            '_LEGACY_DATA_DIR = get_data_dir()',
        ],
    },
    {
        "file": "activity_log_service.py",
        "find": [
            'PROJECT_ROOT = os.path.abspath(\n    os.path.join(os.path.dirname(__file__), "..", "..")\n)',
            'LOG_PATH = os.path.join(PROJECT_ROOT, "data", "activity_log.jsonl")',
        ],
        "replace": [
            'from app.services.paths import get_data_dir',
            'LOG_PATH = str(get_data_dir() / "activity_log.jsonl")',
        ],
    },
    {
        "file": "customer_service.py",
        "find": [
            'PROJECT_ROOT = Path(__file__).resolve().parents[2]',
            'DATA_DIR = PROJECT_ROOT / "data"',
        ],
        "replace": [
            'from app.services.paths import get_data_dir',
            'DATA_DIR = get_data_dir()',
        ],
    },
    {
        "file": "company_settings_service.py",
        "find": [
            'PROJECT_ROOT = Path(__file__).resolve().parents[2]',
            'DATA_DIR = PROJECT_ROOT / "data"',
        ],
        "replace": [
            'from app.services.paths import get_data_dir, get_project_root',
            'DATA_DIR = get_data_dir()',
            'PROJECT_ROOT = get_project_root()',
        ],
    },
    {
        "file": "monthly_report_service.py",
        "find": [
            'PROJECT_ROOT = os.path.abspath(\n    os.path.join(os.path.dirname(__file__), "..", "..")\n)',
        ],
        "replace": [
            'from app.services.paths import get_data_dir, get_project_root',
            'PROJECT_ROOT = get_project_root()',
        ],
    },
    {
        "file": "quotation_number_service.py",
        "find": [
            'BASE_DIR = Path(__file__).resolve().parent.parent.parent',
            '_LEGACY_DATA_DIR = BASE_DIR / "data"',
        ],
        "replace": [
            'from app.services.paths import get_data_dir',
            '_LEGACY_DATA_DIR = get_data_dir()',
        ],
    },
    {
        "file": "catalog_admin_service.py",
        "find": [
            'PROJECT_ROOT = Path(__file__).resolve().parents[2]',
            'DATA_DIR = PROJECT_ROOT / "data"',
        ],
        "replace": [
            'from app.services.paths import get_data_dir',
            'DATA_DIR = get_data_dir()',
        ],
    },
]


# ============================================================
# helpers
# ============================================================

def _backup(p: Path, suffix=".APPDATA_BACKUP"):
    b = p.with_suffix(p.suffix + suffix)
    if not b.exists():
        shutil.copy2(p, b)
        print(f"[backup] {p.name} → {b.name}")


def _apply_patches():
    for rule in PATCHES:
        f = SERVICES / rule["file"]
        if not f.is_file():
            print(f"[skip] {rule['file']} not found")
            continue
        _backup(f)
        s = f.read_text(encoding="utf-8")
        changed = False
        for old, new in zip(rule["find"], rule["replace"]):
            if old in s:
                s = s.replace(old, new, 1)
                changed = True
            elif new.strip().split("\n")[0] in s:
                pass  # already patched
            else:
                print(f"[warn] pattern not found in {f.name}:")
                print(f"       {old[:80]!r}")
        if changed:
            f.write_text(s, encoding="utf-8")
            print(f"[ok] patched: {f.name}")
        else:
            print(f"[skip] {f.name} — no changes made")


# ============================================================
# main
# ============================================================

def main():
    print("=" * 68)
    print("  CRYSTAL — Setup %APPDATA% Paths + Build EXE")
    print("=" * 68)
    print()
    print("This will:")
    print("  1. Create  app/services/paths.py")
    print("  2. Patch   7 service files to use %APPDATA%/CRYSTAL/data/")
    print("  3. Back up each file to *.APPDATA_BACKUP")
    print("  4. Compile-check everything")
    print("  5. Optionally build the EXE with Nuitka")
    print()

    ans = input("Proceed? [y/N] ").strip().lower()
    if ans != "y":
        print("Cancelled.")
        return

    # ---- 1. create paths.py ----
    if PATHS_PY.exists():
        print(f"[skip] {PATHS_PY.name} already exists")
    else:
        PATHS_PY.write_text(PATHS_PY_CONTENT, encoding="utf-8")
        print(f"[new]  {PATHS_PY.relative_to(ROOT)}")

    # ---- 2. patch services ----
    print()
    _apply_patches()

    # ---- 3. compile everything ----
    print()
    print("=" * 68)
    print("  Compile check")
    print("=" * 68)
    failed = []
    for f in SERVICES.glob("*.py"):
        try:
            py_compile.compile(str(f), doraise=True)
        except py_compile.PyCompileError as e:
            print(f"[FAIL] {f.name}: {e}")
            failed.append(f)
    if failed:
        print()
        print(f"*** {len(failed)} file(s) failed to compile.")
        print("    Backups are at *.APPDATA_BACKUP — restore manually if needed.")
        return
    print("[check] all services compile OK")

    # ---- 4. ask about EXE build ----
    print()
    ans = input("Build the EXE now with Nuitka? [y/N] ").strip().lower()
    if ans != "y":
        print("Skipped EXE build. You can build later with:")
        print("  python setup_appdata_build.py  (and answer 'y' here)")
        return

    # ---- 5. build the EXE ----
    print()
    build_exe()


def build_exe():
    icon = ROOT / "assets" / "logo" / "LOGO.ico"
    if not icon.is_file():
        print(f"[FAIL] icon not found: {icon}")
        return

    out_dir = ROOT / "dist"
    exe_name = "CRYSTALQuotation.exe"

    args = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--assume-yes-for-downloads",
        "--windows-console-mode=disable",
        f"--windows-icon-from-ico={icon}",
        "--enable-plugin=tk-inter",
        "--include-data-dir=assets=assets",
        "--include-data-dir=data=data",
        "--include-package=app",
        "--include-package=ui",
        "--include-module=fpdf",
        "--include-module=docx",
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
        f"--output-dir={out_dir}",
        f"--output-filename={exe_name}",
        "main.py",
    ]

    print()
    print("=" * 68)
    print("  Running Nuitka")
    print("=" * 68)
    print(" ".join(args))
    print()

    try:
        result = subprocess.run(args, cwd=str(ROOT))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return

    if result.returncode == 0:
        exe = out_dir / exe_name
        if exe.exists():
            size_mb = exe.stat().st_size / (1024 * 1024)
            print()
            print("=" * 68)
            print("  ✅ BUILD SUCCESSFUL")
            print("=" * 68)
            print(f"  EXE:  {exe}")
            print(f"  Size: {size_mb:.1f} MB")
            print()
            print("  Send this file to your manager.")
            print("=" * 68)
        else:
            print("[WARN] Nuitka finished but EXE not found.")
    else:
        print(f"[FAIL] Nuitka exited with code {result.returncode}")


if __name__ == "__main__":
    main()
