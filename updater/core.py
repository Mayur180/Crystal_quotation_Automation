"""Core logic for the CRYSTAL software update (GUI-free).

The updater replaces exactly one file inside an existing installation:
CRYSTAL_Quotation_Manager.exe. Everything under <install>/data -- customers,
quotations, products, settings, backups -- is never deleted or rewritten.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes
from datetime import datetime
from pathlib import Path

APP_EXE_NAME = "CRYSTAL_Quotation_Manager.exe"
DATA_DIR_NAME = "data"
MARKER_REL = Path(DATA_DIR_NAME) / "version.json"
LOG_REL = Path(DATA_DIR_NAME) / "logs" / "update.log"
BACKUP_REL = Path(DATA_DIR_NAME) / "backups" / "updates"
UPDATER_ID = "CRYSTAL_Update_v5"

DEFAULT_VERSION = "5.0"
DEFAULT_VERSION_NAME = "Version 5"

CREATE_NO_WINDOW = 0x08000000

_SKIP_DIRS = {
    "windows", "$recycle.bin", "system volume information", "appdata",
    "programdata", "node_modules", ".git", "__pycache__", ".venv", "venv",
    "site-packages", "temp", "tmp", "dist", "build", "payload",
    "_source", "backups", "output",
}


class UpdateError(Exception):
    """A failure the updater can explain to the user."""


class AppRunningError(UpdateError):
    def __init__(self, message, pids=()):
        super().__init__(message)
        self.pids = list(pids)


# ─────────────────────────────────────────────────────────────
# small helpers
# ─────────────────────────────────────────────────────────────

def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def sha256_file(path: Path, chunk: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path, default):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default
    return data if isinstance(data, type(default)) else default


def _write_json_atomic(path: Path, data: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def app_exe(install_dir: Path) -> Path:
    return Path(install_dir) / APP_EXE_NAME


def is_installation(path: Path) -> bool:
    try:
        return app_exe(path).is_file()
    except OSError:
        return False


def read_installed_version(install_dir: Path) -> tuple[str, dict]:
    """Return (display_version, marker). Pre-v5 installs have no marker."""
    marker = _read_json(Path(install_dir) / MARKER_REL, {})
    version = str(marker.get("version") or "").strip()
    if version:
        return version, marker
    return "pre-v5", marker


def append_update_log(install_dir: Path, line: str) -> None:
    try:
        path = Path(install_dir) / LOG_REL
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(f"[{stamp}] {line}\n")
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────
# payload
# ─────────────────────────────────────────────────────────────

def load_payload(payload_dir: Path) -> tuple[Path | None, dict]:
    payload_dir = Path(payload_dir)
    manifest = _read_json(payload_dir / "manifest.json", {})
    name = str(manifest.get("app_exe") or APP_EXE_NAME)
    path = payload_dir / name
    return (path if path.is_file() else None), manifest


# ─────────────────────────────────────────────────────────────
# install discovery
# ─────────────────────────────────────────────────────────────

def _drive_roots() -> list[tuple[Path, int]]:
    roots: list[Path] = []
    try:
        drives = os.listdrives()
    except Exception:
        drives = []
    for drive in drives:
        try:
            kind = ctypes.windll.kernel32.GetDriveTypeW(drive)
        except Exception:
            continue
        if kind == 2:          # removable drives are scanned deepest
            roots.append((Path(drive), 3))
        elif kind == 3:        # fixed drives, shallow only
            roots.append((Path(drive), 2))
    return roots


def find_installations(extra_roots=None, budget_seconds: float = 2.5,
                       max_results: int = 8) -> list[Path]:
    """Look for folders that contain CRYSTAL_Quotation_Manager.exe.

    Bounded scan: caller-supplied places, user folders, Programs and drive
    roots, with a time budget so a USB stick update stays quick.
    """
    here = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) \
        else Path(__file__).resolve().parent
    home = Path.home()
    remembered = load_settings().get("install_dir")

    roots: list[tuple[Path, int]] = []
    if remembered:
        roots.append((Path(remembered), 0))
    roots += [
        (here, 1),
        (here.parent, 1),
        (Path.cwd(), 2),
        (home, 2),
        (home / "Desktop", 2),
        (home / "OneDrive" / "Desktop", 2),
        (home / "Downloads", 2),
        (home / "OneDrive" / "Downloads", 2),
        (home / "Documents", 2),
        (Path(os.environ.get("LOCALAPPDATA", home)) / "Programs", 2),
        (Path(os.environ.get("PROGRAMFILES", "C:/Program Files")), 2),
        (Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)")), 2),
        (Path("C:/CRYSTAL"), 2),
        (Path("D:/CRYSTAL"), 2),
    ]
    roots += _drive_roots()
    if extra_roots:
        roots += [(Path(p), 3) for p in extra_roots]

    meipass = None
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        try:
            meipass = Path(sys._MEIPASS).resolve()
        except OSError:
            meipass = None

    deadline = time.monotonic() + max(0.5, budget_seconds)
    found: dict[str, Path] = {}
    seen: set[str] = set()

    def _blocked(path: Path) -> bool:
        low = path.name.lower()
        if low in _SKIP_DIRS or low.startswith("_mei"):
            return True
        if meipass is not None:
            try:
                path.resolve().relative_to(meipass)
                return True
            except (ValueError, OSError):
                pass
        return False

    def _scan(folder: Path, depth: int) -> None:
        if time.monotonic() > deadline or len(found) >= max_results:
            return
        try:
            key = os.path.normcase(str(folder.resolve()))
        except OSError:
            return
        if key in seen or _blocked(folder):
            return
        seen.add(key)
        try:
            entries = list(os.scandir(folder))
        except OSError:
            return
        for entry in entries:
            if time.monotonic() > deadline or len(found) >= max_results:
                return
            try:
                if entry.is_file(follow_symlinks=False):
                    if entry.name.lower() == APP_EXE_NAME.lower():
                        parent = Path(entry.path).parent.resolve()
                        found.setdefault(os.path.normcase(str(parent)), parent)
                elif depth > 0 and entry.is_dir(follow_symlinks=False):
                    _scan(Path(entry.path), depth - 1)
            except OSError:
                continue

    for root, depth in roots:
        if time.monotonic() > deadline or len(found) >= max_results:
            break
        try:
            if root.is_dir():
                _scan(root, depth)
        except OSError:
            continue

    def _score(path: Path) -> tuple:
        marker = path / MARKER_REL
        data = path / DATA_DIR_NAME
        return (
            1 if marker.is_file() else 0,
            1 if data.is_dir() else 0,
            "crystal" in str(path).lower(),
            path.stat().st_mtime if path.exists() else 0,
        )

    return sorted(found.values(), key=_score, reverse=True)


# ─────────────────────────────────────────────────────────────
# running process handling
# ─────────────────────────────────────────────────────────────

if os.name == "nt":
    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class _PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_void_p),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]

    _k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    _k32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    _k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    _k32.OpenProcess.restype = wintypes.HANDLE
    _k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _k32.CloseHandle.argtypes = [wintypes.HANDLE]
    _k32.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    _k32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    _k32.CreateFileW.restype = wintypes.HANDLE
    _k32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]


def _same_path(a: str, b: str) -> bool:
    try:
        return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))
    except Exception:
        return False


def running_pids(exe_path: Path) -> list[int]:
    """PIDs currently running the given executable."""
    if os.name != "nt":
        return []
    target = str(Path(exe_path).resolve())
    snap = _k32.CreateToolhelp32Snapshot(0x2, 0)
    if snap == wintypes.HANDLE(-1).value or not snap:
        return []
    pids: list[int] = []
    entry = _PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(entry)
    buf = ctypes.create_unicode_buffer(2048)
    size = wintypes.DWORD(len(buf))
    try:
        ok = _k32.Process32FirstW(snap, ctypes.byref(entry))
        while ok:
            pid = int(entry.th32ProcessID)
            if pid != os.getpid():
                handle = _k32.OpenProcess(0x1000, False, pid)
                if handle:
                    try:
                        size.value = len(buf)
                        if _k32.QueryFullProcessImageNameW(
                                handle, 0, buf, ctypes.byref(size)):
                            if _same_path(buf.value, target):
                                pids.append(pid)
                    finally:
                        _k32.CloseHandle(handle)
            ok = _k32.Process32NextW(snap, ctypes.byref(entry))
    finally:
        _k32.CloseHandle(snap)
    return pids


def _pid_alive(pid: int) -> bool:
    if os.name != "nt":
        return False
    handle = _k32.OpenProcess(0x00100000, False, pid)   # SYNCHRONIZE
    if not handle:
        return False
    try:
        return _k32.WaitForSingleObject(handle, 0) != 0  # not signalled = alive
    finally:
        _k32.CloseHandle(handle)


def request_close(pids, wait_seconds: float = 12.0) -> list[int]:
    """Ask the app windows to close, then wait. Returns PIDs still alive."""
    pids = [int(p) for p in pids]
    for pid in pids:
        try:
            subprocess.run(["taskkill", "/PID", str(pid)],
                           creationflags=CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=False)
        except Exception:
            pass
    deadline = time.monotonic() + max(2.0, wait_seconds)
    while time.monotonic() < deadline:
        remaining = [pid for pid in pids if _pid_alive(pid)]
        if not remaining:
            return []
        time.sleep(0.35)
    return [pid for pid in pids if _pid_alive(pid)]


# ─────────────────────────────────────────────────────────────
# backup + install
# ─────────────────────────────────────────────────────────────

def _assert_replaceable(target: Path, attempts: int = 8) -> None:
    if not target.is_file():
        raise UpdateError(f"The app file was not found:\n{target}")
    if os.name != "nt":
        return
    # Opening with zero share mode fails while the app is running. Retry
    # briefly: Windows can keep the handle for a moment after the app exits.
    for attempt in range(max(1, attempts)):
        handle = _k32.CreateFileW(
            str(target), 0x80000000, 0, None, 3, 0x80, None)
        if handle and handle != wintypes.HANDLE(-1).value:
            _k32.CloseHandle(handle)
            return
        if attempt + 1 < attempts:
            time.sleep(0.25)
    pids = running_pids(target)
    raise AppRunningError(
        "CRYSTAL is still open, so the app file is locked.\n"
        "Close CRYSTAL, then click Install Update again.", pids)


def backup_exe(install_dir: Path, previous_version: str) -> Path:
    source = app_exe(install_dir)
    dest_dir = Path(install_dir) / BACKUP_REL
    dest_dir.mkdir(parents=True, exist_ok=True)
    tag = "pre_v5" if previous_version in ("", "pre-v5") else \
        f"v{previous_version.replace('.', '_')}"
    dest = dest_dir / f"{now_stamp()}_{Path(APP_EXE_NAME).stem}_{tag}.exe"
    shutil.copy2(source, dest)
    return dest


def _write_marker(install_dir: Path, version: str, version_name: str,
                  previous_version: str, backup: Path) -> None:
    path = Path(install_dir) / MARKER_REL
    data = _read_json(path, {})
    now = now_iso()
    data.update({
        "version": version,
        "version_name": version_name,
        "previous_version": previous_version,
        "updated_at": now,
        "updated_by": UPDATER_ID,
        "backup_exe": str(backup),
        "app_exe": str(app_exe(install_dir)),
        "install_dir": str(Path(install_dir).resolve()),
    })
    data.setdefault("installed_at", now)
    _write_json_atomic(path, data)


def install_update(install_dir: Path, payload: Path, *,
                   expected_sha256: str | None = None,
                   version: str = DEFAULT_VERSION,
                   version_name: str = DEFAULT_VERSION_NAME,
                   log=None) -> dict:
    """Install the payload over an existing app file. Returns a result dict."""
    install_dir = Path(install_dir)
    payload = Path(payload)
    target = app_exe(install_dir)

    def say(message: str) -> None:
        append_update_log(install_dir, message)
        if log:
            try:
                log(message)
            except Exception:
                pass

    if not is_installation(install_dir):
        raise UpdateError(
            "This folder does not contain CRYSTAL_Quotation_Manager.exe.\n"
            "Choose the folder where CRYSTAL is installed.")
    if not payload.is_file():
        raise UpdateError("The update package is missing or incomplete.")

    payload_size = payload.stat().st_size
    if payload_size < 1024 * 1024:
        raise UpdateError("The update package looks incomplete (file too small).")

    say(f"Checking update package ({payload_size / 1048576:.1f} MB)...")
    if expected_sha256:
        actual = sha256_file(payload)
        if actual.lower() != expected_sha256.lower():
            raise UpdateError(
                "The update package failed its integrity check.\n"
                "Copy CRYSTAL_Update_v5.exe again and retry.")
        say("Package checksum verified.")

    try:
        free = shutil.disk_usage(install_dir).free
    except OSError:
        free = None
    needed = payload_size + target.stat().st_size + 32 * 1024 * 1024
    if free is not None and free < needed:
        raise UpdateError("Not enough free disk space for this update.")

    pids = running_pids(target)
    _assert_replaceable(target)
    if pids:
        raise AppRunningError("CRYSTAL is still open. Close it and try again.", pids)

    previous_version, _ = read_installed_version(install_dir)
    say(f"Installed version: {previous_version}")
    backup = backup_exe(install_dir, previous_version)
    say(f"Backup saved: {backup}")

    tmp = install_dir / (APP_EXE_NAME + ".v5.new")
    try:
        say("Installing Version 5...")
        try:
            shutil.copy2(payload, tmp)
        except OSError as exc:
            raise AppRunningError(
                "The app file could not be replaced. Close CRYSTAL and retry.",
                running_pids(target)) from exc
        if expected_sha256 and sha256_file(tmp).lower() != expected_sha256.lower():
            raise UpdateError("The copied update file did not verify correctly.")
        try:
            os.chmod(target, os.stat(target).st_mode | 0o200)
        except OSError:
            pass
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass

    try:
        _write_marker(install_dir, version, version_name, previous_version, backup)
        say("Version marker written.")
    except Exception as exc:
        say(f"Warning: the version record could not be written ({exc}).")
    say(f"Update complete. CRYSTAL {version_name} is installed.")

    return {
        "install_dir": install_dir,
        "version": version,
        "version_name": version_name,
        "previous_version": previous_version,
        "backup": backup,
        "target": target,
    }


def launch_app(install_dir: Path) -> None:
    target = app_exe(install_dir)
    subprocess.Popen([str(target)], cwd=str(install_dir), close_fds=True)


# ─────────────────────────────────────────────────────────────
# updater settings (remember last install folder)
# ─────────────────────────────────────────────────────────────

def settings_file() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "CRYSTAL" / "updater.json"


def load_settings() -> dict:
    return _read_json(settings_file(), {})


def save_settings(**values) -> None:
    try:
        data = load_settings()
        data.update({k: str(v) for k, v in values.items() if v})
        _write_json_atomic(settings_file(), data)
    except Exception:
        pass
