"""Build the CRYSTAL Version 5 update package.

Outputs (in dist/):
    CRYSTAL_Quotation_Manager.exe     full app, Version 5
    CRYSTAL_Update_v5.exe             single-file updater (payload embedded)
    CRYSTAL_Update_v5.zip             updater + readme, ready to copy to a PC
    CRYSTAL_Update_v5_READ_ME.txt

The updater only replaces CRYSTAL_Quotation_Manager.exe in an existing
installation; <install>/data is never touched.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import APP_VERSION, APP_VERSION_NAME  # noqa: E402

APP_EXE_NAME = "CRYSTAL_Quotation_Manager.exe"
UPDATER_NAME = "CRYSTAL_Update_v5"
DIST = ROOT / "dist"
APP_EXE = DIST / APP_EXE_NAME
PAYLOAD_DIR = ROOT / "build" / "update_v5_payload"
READ_ME = DIST / f"{UPDATER_NAME}_READ_ME.txt"

READ_ME_TEXT = """CRYSTAL Quotation Manager - Version 5 update
============================================

This is an UPDATE, not a full reinstall. Your customers, quotations,
products, settings and backups are kept exactly as they are.


BEFORE YOU START
- Close CRYSTAL on the PC.
- Copy CRYSTAL_Update_v5.exe to the PC (pen drive, shared folder, e-mail).
- You do not need to delete the old CRYSTAL folder or its data.


HOW TO UPDATE
1. Double-click CRYSTAL_Update_v5.exe.
2. The window shows the CRYSTAL folder it found.
   If it says "Not selected", click Change and choose the folder that
   contains CRYSTAL_Quotation_Manager.exe.
3. Click "Install Version 5".
4. Wait for "Version 5 installed", then click "Launch CRYSTAL".
   (If CRYSTAL was open, the updater asks before closing it.)


WHAT CHANGES
- Only CRYSTAL_Quotation_Manager.exe is replaced.
- The old app file is saved in:
      <CRYSTAL folder>\\data\\backups\\updates\\
- The version is recorded in:
      <CRYSTAL folder>\\data\\version.json
- A log of the update is written to:
      <CRYSTAL folder>\\data\\logs\\update.log
- Nothing inside the data folder is deleted or rewritten.


IF SOMETHING GOES WRONG
- Open <CRYSTAL folder>\\data\\backups\\updates and find the newest
  CRYSTAL_Quotation_Manager_*.exe backup.
- Close CRYSTAL.
- Copy that backup file into the CRYSTAL folder and rename it to
  CRYSTAL_Quotation_Manager.exe (replace the existing file).
- Start CRYSTAL again.

Windows may show "Windows protected your PC" because the app is not
code-signed. Click "More info" then "Run anyway" - the same as the main
CRYSTAL app.


Version 5.0 - ARMATECH ASSOCIATES
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run(args) -> None:
    print("+ " + " ".join(str(a) for a in args), flush=True)
    subprocess.run([str(a) for a in args], cwd=str(ROOT), check=True)


def build_app() -> None:
    print("\n[1/3] Building CRYSTAL_Quotation_Manager.exe (Version 5)...", flush=True)
    run([sys.executable, "-m", "PyInstaller", "--noconfirm",
         "CRYSTAL_Quotation_Manager.spec"])
    if not APP_EXE.is_file():
        raise SystemExit(f"App build failed: {APP_EXE} was not created.")


def prepare_payload(manifest: dict) -> None:
    print("\n[2/3] Preparing update payload...", flush=True)
    if PAYLOAD_DIR.exists():
        shutil.rmtree(PAYLOAD_DIR)
    PAYLOAD_DIR.mkdir(parents=True)
    payload_exe = PAYLOAD_DIR / APP_EXE_NAME
    shutil.copy2(APP_EXE, payload_exe)
    manifest.update({
        "app_exe": APP_EXE_NAME,
        "size": payload_exe.stat().st_size,
        "sha256": sha256(payload_exe),
    })
    (PAYLOAD_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    (DIST / f"{UPDATER_NAME}_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")


def build_updater() -> Path:
    print("\n[3/3] Building CRYSTAL_Update_v5.exe...", flush=True)
    distpath = ROOT / "build" / "update_v5_dist"
    workpath = ROOT / "build" / "update_v5_work"
    specpath = ROOT / "build" / "update_v5_spec"
    for folder in (distpath, workpath, specpath):
        shutil.rmtree(folder, ignore_errors=True)
    args = [
        str(ROOT / "updater" / "update_v5.py"),
        f"--name={UPDATER_NAME}",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        f"--distpath={distpath}",
        f"--workpath={workpath}",
        f"--specpath={specpath}",
        f"--paths={ROOT}",
        f"--add-data={PAYLOAD_DIR}{os.pathsep}payload",
        f"--add-data={ROOT / 'assets'}{os.pathsep}assets",
        f"--icon={ROOT / 'assets' / 'logo' / 'LOGO.ico'}",
        f"--version-file={ROOT / 'updater' / 'version_v5.txt'}",
        "--exclude-module=docx",
        "--exclude-module=docx2pdf",
        "--exclude-module=pymupdf",
        "--exclude-module=win32com",
        "--exclude-module=bcrypt",
        "--exclude-module=requests",
        "--exclude-module=PIL",
    ]
    run([sys.executable, "-m", "PyInstaller", *args])
    built = distpath / f"{UPDATER_NAME}.exe"
    if not built.is_file():
        raise SystemExit(f"Updater build failed: {built} was not created.")
    out = DIST / f"{UPDATER_NAME}.exe"
    shutil.copy2(built, out)
    return out


def write_package(updater: Path, make_zip: bool) -> None:
    READ_ME.write_text(READ_ME_TEXT, encoding="utf-8")
    if not make_zip:
        return
    archive = DIST / f"{UPDATER_NAME}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(updater, updater.name)
        zf.write(READ_ME, READ_ME.name)
    print(f"ZIP: {archive} ({archive.stat().st_size / 1048576:.1f} MB)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Version 5 update")
    parser.add_argument("--skip-app", action="store_true",
                        help="reuse the existing dist app EXE")
    parser.add_argument("--no-zip", action="store_true")
    args = parser.parse_args()

    if APP_VERSION.split(".")[0] != "5":
        raise SystemExit(f"app/config.py says version {APP_VERSION}; this package is Version 5.")

    DIST.mkdir(parents=True, exist_ok=True)
    if not args.skip_app:
        build_app()
    elif not APP_EXE.is_file():
        raise SystemExit("No app EXE to package. Run without --skip-app first.")

    manifest = {
        "version": APP_VERSION,
        "version_name": APP_VERSION_NAME,
        "updater": f"{UPDATER_NAME}.exe",
        "built_at": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
    prepare_payload(manifest)

    updater = build_updater()
    final_manifest = json.loads((DIST / f"{UPDATER_NAME}_manifest.json").read_text(encoding="utf-8"))
    updater_sha = sha256(updater)
    write_package(updater, make_zip=not args.no_zip)

    print("\nDone.")
    print(f"  App:      {APP_EXE}  ({APP_EXE.stat().st_size / 1048576:.1f} MB)")
    print(f"  Updater:  {updater}  ({updater.stat().st_size / 1048576:.1f} MB)")
    print(f"  Payload:  sha256 {final_manifest['sha256']}")
    print(f"  Updater:  sha256 {updater_sha}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
