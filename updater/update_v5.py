"""CRYSTAL Version 5 — software update window.

Run it next to CRYSTAL or anywhere; it finds the installed app, backs up the
old executable, installs Version 5 in place and leaves the data folder alone.
"""
from __future__ import annotations

import argparse
import ctypes
import os
import queue
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parent.parent
if getattr(sys, "frozen", False):
    ROOT = Path(getattr(sys, "_MEIPASS", ROOT))
elif str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.crystal import theme as T
from ui.crystal import widgets as W
from updater import core


def payload_dir() -> Path:
    env = os.environ.get("CRYSTAL_UPDATE_PAYLOAD")
    if env:
        return Path(env)
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "payload"
    return ROOT / "build" / "update_v5_payload"


def _console(message: str) -> None:
    stream = getattr(sys, "stdout", None)
    if stream is None:
        return
    try:
        print(message, flush=True)
    except Exception:
        pass


def cli(args) -> int:
    pdir = Path(args.payload) if args.payload else payload_dir()
    payload, manifest = core.load_payload(pdir)
    if payload is None:
        _console(f"Update payload not found in {pdir}")
        return 2
    install = Path(args.install_dir) if args.install_dir else None
    if install is None:
        found = core.find_installations()
        if not found:
            _console("No CRYSTAL installation found.")
            return 2
        install = found[0]
    if args.close_running:
        pids = core.running_pids(core.app_exe(install))
        if pids:
            core.request_close(pids)
    try:
        result = core.install_update(
            install, payload,
            expected_sha256=manifest.get("sha256"),
            version=str(manifest.get("version") or core.DEFAULT_VERSION),
            version_name=str(manifest.get("version_name") or core.DEFAULT_VERSION_NAME),
            log=_console,
        )
    except core.UpdateError as exc:
        _console(f"UPDATE FAILED: {exc}")
        return 2
    if not args.no_launch:
        core.launch_app(install)
    _console(f"UPDATE_OK {result['target']}")
    return 0


class UpdateWindow(tk.Tk):
    def __init__(self, *, install_dir=None, payload=None, launch_after=True):
        super().__init__()
        self._payload_dir = Path(payload) if payload else payload_dir()
        self._payload, self._manifest = core.load_payload(self._payload_dir)
        if self._payload is None:
            self._manifest = {}
        self._version = str(self._manifest.get("version") or core.DEFAULT_VERSION)
        self._version_name = str(self._manifest.get("version_name")
                                 or core.DEFAULT_VERSION_NAME)
        self._install_dir = Path(install_dir) if install_dir else None
        self._busy = False
        self._done = False
        self._launch_after = tk.BooleanVar(value=bool(launch_after))
        self._events: queue.Queue = queue.Queue()

        self.title(f"CRYSTAL {self._version_name} — Software Update")
        self.configure(bg=T.BG)
        self.minsize(840, 700)
        W.apply_ttk_theme(self)
        W.set_window_icon(self)

        self._build()
        self._center(900, 780)
        self._log(f"Ready to install {self._version_name}.")
        self._log("The data folder will not be changed.", "muted")
        if self._payload is None:
            self._log("The update package is missing. Copy CRYSTAL_Update_v5.exe again.", "err")
        if self._install_dir:
            self._refresh_install()
        else:
            self._log("Looking for the CRYSTAL installation...", "muted")
            threading.Thread(target=self._detect_async, daemon=True).start()

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self._poll()

    # ─────────────────────────────────────────────────────
    # layout
    # ─────────────────────────────────────────────────────

    def _build(self):
        header = tk.Frame(self, bg=T.SURFACE, height=70)
        header.pack(side="top", fill="x")
        header.pack_propagate(False)
        tk.Frame(header, bg=T.ACCENT, height=3).pack(side="bottom", fill="x")

        hrow = tk.Frame(header, bg=T.SURFACE)
        hrow.pack(fill="both", expand=True, padx=28)
        brand = tk.Frame(hrow, bg=T.SURFACE)
        brand.pack(side="left", pady=10)
        tk.Label(brand, text="CRYSTAL", bg=T.SURFACE, fg=T.ACCENT,
                 font=T.FONT_H1).pack(anchor="w")
        tk.Label(brand, text="SOFTWARE UPDATE", bg=T.SURFACE, fg=T.TEXT_MUTED,
                 font=T.FONT_LABEL).pack(anchor="w", pady=(2, 0))

        chip = tk.Frame(hrow, bg=T.ACCENT_SOFT)
        chip.pack(side="right", pady=20)
        tk.Label(chip, text=f"VERSION {self._version}", bg=T.ACCENT_SOFT,
                 fg=T.ACCENT_DARK, font=T.FONT_LABEL,
                 padx=12, pady=6).pack()

        footer = tk.Frame(self, bg=T.SURFACE, height=62)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)
        tk.Frame(footer, bg=T.BORDER, height=1).pack(side="top", fill="x")
        frow = tk.Frame(footer, bg=T.SURFACE)
        frow.pack(fill="both", expand=True, padx=28, pady=10)

        self._launch_check = tk.Checkbutton(
            frow, text="Launch CRYSTAL after the update",
            variable=self._launch_after, bg=T.SURFACE, activebackground=T.SURFACE,
            fg=T.TEXT_BODY, activeforeground=T.TEXT, selectcolor=T.SURFACE,
            font=T.FONT_SMALL, bd=0, highlightthickness=0, cursor="hand2")
        self._launch_check.pack(side="left")

        self._primary = W.PrimaryButton(frow, f"Install {self._version_name}",
                                        self._primary_action, padx=22, pady=9)
        self._primary.pack(side="right")
        self._cancel = W.GhostButton(frow, "Cancel", self._on_cancel,
                                     padx=18, pady=9)
        self._cancel.pack(side="right", padx=(0, 10))

        body = tk.Frame(self, bg=T.BG)
        body.pack(side="top", fill="both", expand=True, padx=28, pady=(12, 8))

        self._title = tk.Label(body, text=f"Install {self._version_name}",
                               bg=T.BG, fg=T.TEXT, font=T.FONT_H1, anchor="w")
        self._title.pack(fill="x")
        self._subtitle = tk.Label(
            body,
            text="This is an update, not a reinstall. You do not need to delete CRYSTAL.",
            bg=T.BG, fg=T.TEXT_MUTED, font=T.FONT_BODY, anchor="w")
        self._subtitle.pack(fill="x", pady=(2, 8))

        # ── installation card ──
        card = self._card(body)
        inner = card.inner
        row = tk.Frame(inner, bg=T.SURFACE)
        row.pack(fill="x")
        tk.Label(row, text="INSTALLATION", bg=T.SURFACE, fg=T.TEXT_MUTED,
                 font=T.FONT_LABEL).pack(side="left")
        self._change = W.GhostButton(row, "Change", self._choose_install,
                                     font=T.FONT_SMALL, padx=12, pady=4)
        self._change.pack(side="right")

        self._path_label = tk.Label(inner, text="Looking for CRYSTAL...",
                                    bg=T.SURFACE, fg=T.TEXT_BODY, font=T.FONT_SMALL,
                                    anchor="w", justify="left", wraplength=720)
        self._path_label.pack(fill="x", pady=(4, 0))

        tk.Frame(inner, bg=T.BORDER, height=1).pack(fill="x", pady=8)

        versions = tk.Frame(inner, bg=T.SURFACE)
        versions.pack(fill="x")
        cur = tk.Frame(versions, bg=T.SURFACE)
        cur.pack(side="left")
        tk.Label(cur, text="CURRENT VERSION", bg=T.SURFACE, fg=T.TEXT_MUTED,
                 font=T.FONT_LABEL).pack(anchor="w")
        self._current_label = tk.Label(cur, text="—", bg=T.SURFACE, fg=T.TEXT,
                                       font=T.FONT_BODY_B)
        self._current_label.pack(anchor="w", pady=(2, 0))

        new = tk.Frame(versions, bg=T.SURFACE)
        new.pack(side="left", padx=(64, 0))
        tk.Label(new, text="NEW VERSION", bg=T.SURFACE, fg=T.TEXT_MUTED,
                 font=T.FONT_LABEL).pack(anchor="w")
        nrow = tk.Frame(new, bg=T.SURFACE)
        nrow.pack(anchor="w", pady=(2, 0))
        tk.Label(nrow, text=f"{self._version_name}", bg=T.SURFACE, fg=T.ACCENT,
                 font=T.FONT_BODY_B).pack(side="left")
        chip = tk.Frame(nrow, bg=T.ACCENT_SOFT)
        chip.pack(side="left", padx=(8, 0))
        tk.Label(chip, text="UPDATE PACKAGE", bg=T.ACCENT_SOFT, fg=T.ACCENT_DARK,
                 font=T.FONT_TINY, padx=8, pady=2).pack()

        # ── data safety strip ──
        note = tk.Frame(body, bg=T.ACCENT_SOFT)
        note.pack(fill="x", pady=(8, 8))
        tk.Frame(note, bg=T.ACCENT, width=3).pack(side="left", fill="y")
        tk.Label(note, text=(
            "Your data is preserved. Customers, quotations, products, settings and "
            "backups in the data folder are left exactly as they are. The old app "
            "file is backed up automatically."),
            bg=T.ACCENT_SOFT, fg=T.ACCENT_DARK, font=T.FONT_SMALL,
            justify="left", anchor="w", wraplength=720).pack(
            side="left", fill="x", expand=True, padx=12, pady=8)

        # ── steps card ──
        steps_card = self._card(body)
        tk.Label(steps_card.inner, text="WHAT THE UPDATE DOES", bg=T.SURFACE,
                 fg=T.TEXT_MUTED, font=T.FONT_LABEL).pack(anchor="w")
        steps = (
            "Close CRYSTAL if it is open.",
            "Back up the current app file.",
            "Install Version 5 in place.",
            "Leave every other file untouched.",
        )
        grid = tk.Frame(steps_card.inner, bg=T.SURFACE)
        grid.pack(fill="x", pady=(4, 0))
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        for index, text in enumerate(steps):
            row, column = divmod(index, 2)
            cell = tk.Frame(grid, bg=T.SURFACE)
            cell.grid(row=row, column=column, sticky="w", pady=3)
            tk.Label(cell, text=str(index + 1), bg=T.ACCENT_SOFT, fg=T.ACCENT_DARK,
                     font=T.FONT_LABEL, width=2, pady=1).pack(side="left", anchor="n")
            tk.Label(cell, text=text, bg=T.SURFACE, fg=T.TEXT_BODY,
                     font=T.FONT_SMALL, anchor="w", justify="left").pack(
                side="left", padx=(10, 0))

        # ── progress card ──
        prog_card = self._card(body, expand=True)
        prow = tk.Frame(prog_card.inner, bg=T.SURFACE)
        prow.pack(fill="x")
        tk.Label(prow, text="PROGRESS", bg=T.SURFACE, fg=T.TEXT_MUTED,
                 font=T.FONT_LABEL).pack(side="left")
        self._progress = ttk.Progressbar(
            prow, mode="determinate", maximum=100, value=0, length=190,
            style="Crystal.Horizontal.TProgressbar")
        self._progress.pack(side="right")

        self._log_text = tk.Text(
            prog_card.inner, height=4, wrap="word", relief="flat", bd=0,
            bg=T.SURFACE_ALT, fg=T.TEXT_BODY, font=T.FONT_SMALL,
            highlightthickness=1, highlightbackground=T.BORDER,
            padx=10, pady=6, state="disabled", cursor="arrow")
        self._log_text.pack(fill="both", expand=True, pady=(6, 0))
        self._log_text.tag_configure("ok", foreground=T.SUCCESS)
        self._log_text.tag_configure("err", foreground=T.DANGER)
        self._log_text.tag_configure("muted", foreground=T.TEXT_MUTED)

    def _card(self, parent, *, expand=False):
        card = tk.Frame(parent, bg=T.SURFACE,
                        highlightbackground=T.BORDER, highlightthickness=1)
        card.pack(fill="both" if expand else "x", expand=bool(expand), pady=(0, 8))
        inner = tk.Frame(card, bg=T.SURFACE)
        inner.pack(fill="both", expand=True, padx=16, pady=10)
        card.inner = inner
        return card

    def _center(self, width, height):
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        width = min(width, sw - 40)
        height = min(height, sh - 60)
        x = max(0, (sw - width) // 2)
        y = max(0, (sh - height) // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    # ─────────────────────────────────────────────────────
    # state
    # ─────────────────────────────────────────────────────

    def _detect_async(self):
        try:
            found = core.find_installations()
        except Exception:
            found = []
        self._events.put(("found", found))

    def _refresh_install(self):
        valid = bool(self._install_dir and core.is_installation(self._install_dir))
        if valid:
            self._path_label.configure(text=str(self._install_dir))
            version, _ = core.read_installed_version(self._install_dir)
            shown = "Earlier version (pre-v5)" if version == "pre-v5" else version
            self._current_label.configure(text=shown)
            core.save_settings(install_dir=self._install_dir)
        else:
            self._path_label.configure(text="Not selected — click Change and choose the CRYSTAL folder.")
            self._current_label.configure(text="—")
        ready = valid and self._payload is not None and not self._busy and not self._done
        self._primary.set_enabled(ready)

    def _choose_install(self):
        initial = str(self._install_dir) if self._install_dir else str(Path.home())
        chosen = filedialog.askdirectory(
            title="Select the CRYSTAL folder (contains CRYSTAL_Quotation_Manager.exe)",
            initialdir=initial)
        if not chosen:
            return
        folder = Path(chosen)
        if not core.is_installation(folder):
            messagebox.showerror(
                "Not a CRYSTAL folder",
                "That folder does not contain CRYSTAL_Quotation_Manager.exe.\n\n"
                "Open the folder where CRYSTAL is installed and select it.")
            return
        self._install_dir = folder
        self._refresh_install()
        self._log(f"Installation selected: {folder}")

    def _log(self, message, tag=None):
        self._log_text.configure(state="normal")
        self._log_text.insert("end", f"{message}\n", tag or ())
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    # ─────────────────────────────────────────────────────
    # actions
    # ─────────────────────────────────────────────────────

    def _primary_action(self):
        if self._done:
            self._launch()
        else:
            self._install()

    def _install(self):
        if self._busy:
            return
        if not self._install_dir or not core.is_installation(self._install_dir):
            messagebox.showwarning(
                "Choose the CRYSTAL folder",
                "Select the folder that contains CRYSTAL_Quotation_Manager.exe first.")
            return
        if self._payload is None:
            messagebox.showerror("Update package missing",
                                 "Copy CRYSTAL_Update_v5.exe again and retry.")
            return

        pids = core.running_pids(core.app_exe(self._install_dir))
        close_pids = []
        if pids:
            if not messagebox.askyesno(
                    "CRYSTAL is running",
                    "The update needs to close CRYSTAL so the app file can be replaced.\n\n"
                    "Save any open work first.\n\nClose CRYSTAL and continue?",
                    icon="warning"):
                return
            close_pids = pids

        self._set_busy(True)
        self._log("Starting update...")
        threading.Thread(target=self._worker, args=(close_pids,), daemon=True).start()

    def _worker(self, close_pids):
        try:
            if close_pids:
                self._events.put(("log", "Closing CRYSTAL..."))
                remaining = core.request_close(close_pids)
                if remaining:
                    raise core.AppRunningError(
                        "CRYSTAL did not close. Close it manually, then click "
                        "Install update again.")
            result = core.install_update(
                self._install_dir, self._payload,
                expected_sha256=self._manifest.get("sha256"),
                version=self._version,
                version_name=self._version_name,
                log=lambda message: self._events.put(("log", message)))
            self._events.put(("done", result))
        except core.UpdateError as exc:
            self._events.put(("error", str(exc)))
        except Exception as exc:
            self._events.put(("error", f"Unexpected error: {exc}"))

    def _launch(self):
        if not self._install_dir:
            return
        try:
            core.launch_app(self._install_dir)
            self._log(f"{self._version_name} launched.", "ok")
        except Exception as exc:
            messagebox.showerror("Could not launch CRYSTAL", str(exc))

    def _set_busy(self, busy):
        self._busy = busy
        self._primary.set_enabled(not busy)
        self._change.set_enabled(not busy)
        self._cancel.set_enabled(not busy)
        self._launch_check.configure(state="disabled" if busy else "normal")
        if busy:
            self._progress.configure(mode="indeterminate")
            self._progress.start(12)
        else:
            self._progress.stop()
            self._progress.configure(mode="determinate")

    def _poll(self):
        try:
            while True:
                kind, data = self._events.get_nowait()
                if kind == "log":
                    self._log(data)
                elif kind == "found":
                    self._handle_found(data)
                elif kind == "done":
                    self._handle_done(data)
                elif kind == "error":
                    self._handle_error(data)
        except queue.Empty:
            pass
        self.after(120, self._poll)

    def _handle_found(self, found):
        if self._install_dir or not found:
            if not found and not self._install_dir:
                self._log("CRYSTAL was not found automatically. Click Change and "
                          "select its folder.", "err")
                self._refresh_install()
            return
        self._install_dir = found[0]
        self._refresh_install()
        extra = f" ({len(found)} found)" if len(found) > 1 else ""
        self._log(f"Installation found{extra}: {found[0]}")

    def _handle_done(self, result):
        self._set_busy(False)
        self._done = True
        self._progress.configure(value=100)
        self._current_label.configure(text=result["version"])
        self._title.configure(text=f"{self._version_name} installed")
        self._subtitle.configure(
            text="Your data was not changed. The previous app file was backed up.")
        self._primary.set_text("Launch CRYSTAL")
        self._primary.set_enabled(True)
        self._cancel.set_text("Close")
        self._change.set_enabled(False)
        self._launch_check.configure(state="disabled")
        self._log(f"Backup: {result['backup']}", "muted")
        self._log(f"Update complete. {self._version_name} is installed.", "ok")
        if self._launch_after.get():
            self.after(500, self._launch)

    def _handle_error(self, message):
        self._set_busy(False)
        self._progress.configure(value=0)
        self._log(message, "err")
        self._refresh_install()
        messagebox.showerror("Update could not be completed", message)

    def _on_cancel(self):
        if self._busy:
            messagebox.showinfo("Update in progress",
                                "Please wait for the update to finish.")
            return
        self.destroy()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="CRYSTAL Version 5 software update")
    parser.add_argument("--install-dir", help="folder containing CRYSTAL_Quotation_Manager.exe")
    parser.add_argument("--payload", help="folder containing the update payload")
    parser.add_argument("--silent", action="store_true", help="run without the window")
    parser.add_argument("--no-launch", action="store_true", help="do not start CRYSTAL afterwards")
    parser.add_argument("--close-running", action="store_true",
                        help="ask a running CRYSTAL to close (silent mode)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    if os.name == "nt":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass
    if args.silent:
        return cli(args)
    app = UpdateWindow(install_dir=args.install_dir,
                       payload=args.payload,
                       launch_after=not args.no_launch)
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
