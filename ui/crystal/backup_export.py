# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# BACKUP / EXPORT
#
# Modal window — three tabs: Backup / Export / Backups
#
# File:
#   ui/backup_export.py
# ============================================================

import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from ui.crystal import theme as T
from ui.crystal import widgets as W


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:
    from app.services.backup_service import (
        create_backup,
        list_backups,
        restore_backup,
        delete_backup,
    )
except Exception:
    create_backup = None
    list_backups = None
    restore_backup = None
    delete_backup = None


try:
    from app.services.export_service import (
        export_quotations_csv,
        export_customers_csv,
        export_all_json,
        export_quotation_files_zip,
    )
except Exception:
    export_quotations_csv = None
    export_customers_csv = None
    export_all_json = None
    export_quotation_files_zip = None


# ============================================================
# HELPERS
# ============================================================

def _open_in_explorer(path):
    """Open a file or folder in the OS default application."""
    if not path:
        return False
    p = str(path)
    if not os.path.exists(p):
        return False
    try:
        if sys.platform.startswith("win"):
            if os.path.isfile(p):
                subprocess.Popen(["explorer", "/select,", os.path.normpath(p)])
            else:
                os.startfile(p)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", p])
        else:
            subprocess.Popen(["xdg-open", p])
        return True
    except Exception:
        return False


def _friendly_ts(value):
    text = "" if value is None else str(value).strip()
    if not text:
        return "—"
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d_%H-%M-%S",
                "%Y-%m-%dT%H:%M:%S", "%Y%m%d_%H%M%S",
                "%Y-%m-%d %H-%M-%S"):
        try:
            return datetime.strptime(text, fmt).strftime("%d-%m-%Y %H:%M")
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")) \
            .strftime("%d-%m-%Y %H:%M")
    except Exception:
        return text


# ============================================================
# MAIN WINDOW
# ============================================================

class BackupExport(tk.Toplevel):

    BG = T.BG
    CARD = T.SURFACE
    TEXT = T.TEXT
    MUTED = T.TEXT_MUTED
    LIGHT_MUTED = T.TEXT_FAINT
    BORDER = T.BORDER
    RED = T.ACCENT
    RED_DARK = T.ACCENT_DARK
    RED_LIGHT = T.ACCENT_SOFT
    SOFT = T.SURFACE_ALT
    GREEN = T.SUCCESS
    GREEN_LIGHT = T.SUCCESS_BG

    def __init__(self, parent):

        super().__init__(parent)

        self.title("CRYSTAL | Backup / Export")
        self.geometry("1040x700")
        self.minsize(920, 600)
        self.configure(bg=self.BG)
        W.set_window_icon(self)

        self.transient(parent)
        self.grab_set()

        self.current_tab = "backup"
        self.selected_backup = None

        W.apply_ttk_theme(self)
        self._build_interface()
        self._switch_tab("backup")

        # ---- Escape closes the window ----
        try:
            from ui.common.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(self, on_escape=self.destroy)
        except Exception:
            pass

    # --------------------------------------------------------

    def _build_interface(self):

        header = W.PageHeader(
            self, title="Backup / Export",
            subtitle="Snapshots and data exports",
            padx=28,
        )
        header.pack(fill="x")

        # Footer before the expanding body
        footer = tk.Frame(self, bg=T.SURFACE,
                          highlightbackground=T.BORDER,
                          highlightthickness=1)
        footer.pack(side="bottom", fill="x")
        W.GhostButton(
            footer, "Close", self.destroy, padx=18, pady=7,
        ).pack(side="right", padx=22, pady=13)

        # Tabs
        tab_bar = tk.Frame(self, bg=self.BG)
        tab_bar.pack(fill="x", padx=28, pady=(14, 10))

        self.tab_buttons = {}
        for key, label in [("backup", "Backup"),
                            ("export", "Export"),
                            ("backups", "Manage backups")]:
            btn = tk.Button(
                tab_bar, text=label,
                command=lambda k=key: self._switch_tab(k),
                bg=T.SURFACE_ALT, fg=T.TEXT_BODY,
                activebackground=T.SURFACE_HOVER,
                activeforeground=T.TEXT,
                relief="flat", bd=0, highlightthickness=1,
                highlightbackground=T.BORDER,
                highlightcolor=T.BORDER,
                font=T.FONT_BODY_B, cursor="hand2",
                padx=16, pady=7,
            )
            btn.pack(side="left", padx=(0, 6))
            self.tab_buttons[key] = btn

        # Body
        self.body = tk.Frame(self, bg=self.BG)
        self.body.pack(fill="both", expand=True, padx=28, pady=(0, 4))

    # --------------------------------------------------------

    def _switch_tab(self, key):

        self.current_tab = key
        self.selected_backup = None

        for widget in self.body.winfo_children():
            widget.destroy()

        for k, btn in self.tab_buttons.items():
            if k == key:
                btn.configure(bg=T.ACCENT_SOFT, fg=T.ACCENT,
                              activebackground=T.ACCENT_SOFT,
                              activeforeground=T.ACCENT)
            else:
                btn.configure(bg=T.SURFACE_ALT, fg=T.TEXT_BODY,
                              activebackground=T.SURFACE_HOVER,
                              activeforeground=T.TEXT)

        if key == "backup":
            self._render_backup_tab()
        elif key == "export":
            self._render_export_tab()
        elif key == "backups":
            self._render_backups_tab()

    # --------------------------------------------------------
    # BACKUP TAB
    # --------------------------------------------------------

    def _render_backup_tab(self):

        card = self._card()
        self._card_title(card, "Create a backup")

        tk.Label(card,
                 text=("Create a zip snapshot of all application data: catalog, "
                       "customers, quotations, terms, company settings, offer "
                       "counter and logo."),
                 bg=self.CARD, fg=T.TEXT_BODY,
                 font=T.FONT_SMALL,
                 anchor="w", justify="left", wraplength=760).pack(
            anchor="w", pady=(0, 4))

        tk.Label(card,
                 text="Backups are stored in output/backups/",
                 bg=self.CARD, fg=T.TEXT_MUTED,
                 font=T.FONT_SMALL,
                 anchor="w").pack(anchor="w", pady=(0, 16))

        row = tk.Frame(card, bg=self.CARD)
        row.pack(fill="x", pady=(0, 8))

        tk.Label(row, text="LABEL (OPTIONAL)",
                 bg=self.CARD, fg=T.TEXT_MUTED,
                 font=T.FONT_LABEL).pack(anchor="w", pady=(0, 4))

        self.label_var = tk.StringVar()
        W.SearchEntry(
            row, textvariable=self.label_var,
            placeholder="e.g. before rate revision",
            show_icon=False,
        ).pack(fill="x")

        W.PrimaryButton(
            card, "Create backup now", self._do_create_backup,
            padx=16, pady=8,
        ).pack(anchor="w", pady=(16, 0))

    def _do_create_backup(self):

        if create_backup is None:
            messagebox.showerror("Unavailable",
                                 "Backup service not loaded.",
                                 parent=self)
            return

        label = self.label_var.get().strip()
        path, err = create_backup(label=label)

        if err:
            messagebox.showerror("Backup failed", err, parent=self)
            return

        messagebox.showinfo(
            "Backup Created",
            f"Backup saved to:\n{path}",
            parent=self,
        )
        self.label_var.set("")

    # --------------------------------------------------------
    # EXPORT TAB
    # --------------------------------------------------------

    def _render_export_tab(self):

        card = self._card()
        self._card_title(card, "Export data")

        tk.Label(card,
                 text="Choose what to export. Files are saved to output/exports/",
                 bg=self.CARD, fg=T.TEXT_MUTED,
                 font=T.FONT_SMALL,
                 anchor="w").pack(anchor="w", pady=(0, 14))

        options = [
            ("Quotations as CSV",
             "One row per quotation with customer, model, totals.",
             self._do_export_quotations_csv),
            ("Customers as CSV",
             "One row per saved customer.",
             self._do_export_customers_csv),
            ("All Data as JSON",
             "Full catalog + customers + quotations in one file.",
             self._do_export_all_json),
            ("Quotation Files as ZIP",
             "All generated .docx and .pdf from output/quotations/.",
             self._do_export_quotation_files),
        ]

        for title, subtitle, command in options:
            self._export_row(card, title, subtitle, command)

    def _export_row(self, parent, title, subtitle, command):

        row = tk.Frame(parent, bg=T.SURFACE_ALT,
                       highlightbackground=T.BORDER,
                       highlightthickness=1)
        row.pack(fill="x", pady=4)

        text = tk.Frame(row, bg=T.SURFACE_ALT)
        text.pack(side="left", fill="x", expand=True, padx=14, pady=10)

        tk.Label(text, text=title, bg=T.SURFACE_ALT, fg=T.TEXT,
                 font=T.FONT_BODY_B, anchor="w").pack(anchor="w")

        tk.Label(text, text=subtitle, bg=T.SURFACE_ALT, fg=T.TEXT_MUTED,
                 font=T.FONT_SMALL, anchor="w").pack(anchor="w", pady=(2, 0))

        W.GhostButton(
            row, "Export", command, padx=14, pady=6,
        ).pack(side="right", padx=12, pady=10)

    def _handle_export(self, func, success_label):

        if func is None:
            messagebox.showerror("Unavailable",
                                 "Export service not loaded.",
                                 parent=self)
            return

        path, err = func()
        if err:
            messagebox.showwarning("Export", err, parent=self)
            return

        ok = messagebox.askyesno(
            "Export Complete",
            f"{success_label}\n\n{path}\n\nOpen the folder?",
            parent=self,
        )
        if ok:
            _open_in_explorer(path)

    def _do_export_quotations_csv(self):
        self._handle_export(export_quotations_csv,
                            "Quotations exported as CSV.")

    def _do_export_customers_csv(self):
        self._handle_export(export_customers_csv,
                            "Customers exported as CSV.")

    def _do_export_all_json(self):
        self._handle_export(export_all_json,
                            "All data exported as JSON.")

    def _do_export_quotation_files(self):
        self._handle_export(export_quotation_files_zip,
                            "Quotation files zipped.")

    # --------------------------------------------------------
    # BACKUPS TAB
    # --------------------------------------------------------

    def _render_backups_tab(self):

        backups = list_backups() if list_backups else []

        card = tk.Frame(self.body, bg=T.SURFACE,
                        highlightbackground=T.BORDER,
                        highlightthickness=1)
        card.pack(fill="both", expand=True)

        head = tk.Frame(card, bg=T.SURFACE)
        head.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(
            head, text="Saved backups", bg=T.SURFACE, fg=T.TEXT,
            font=T.FONT_H3, anchor="w",
        ).pack(side="left")
        tk.Label(
            head, text=f"{len(backups):,} backup(s)", bg=T.SURFACE,
            fg=T.TEXT_MUTED, font=T.FONT_SMALL,
        ).pack(side="right")

        actions = tk.Frame(card, bg=T.SURFACE)
        actions.pack(side="bottom", fill="x", padx=14, pady=(6, 12))

        W.GhostButton(
            actions, "Open folder", self._open_backup_folder, padx=13, pady=7,
        ).pack(side="left")
        self.restore_btn = W.PrimaryButton(
            actions, "Restore selected", self._do_restore_backup, padx=13, pady=7,
        )
        self.restore_btn.pack(side="left", padx=(8, 0))
        self.delete_btn = W.DangerButton(
            actions, "Delete selected", self._do_delete_backup, padx=13, pady=7,
        )
        self.delete_btn.pack(side="left", padx=(8, 0))
        self.restore_btn.set_enabled(bool(backups))
        self.delete_btn.set_enabled(bool(backups))

        cols = ("timestamp", "filename", "size")
        tree = ttk.Treeview(card, columns=cols, show="headings", height=12)

        for c, title, width, anchor in (
            ("timestamp", "Created", 170, "w"),
            ("filename", "Backup file", 460, "w"),
            ("size", "Size", 100, "e"),
        ):
            tree.heading(c, text=title, anchor=anchor)
            tree.column(c, width=width, anchor=anchor,
                        stretch=(c == "filename"))
        tree.tag_configure("evenrow", background=T.SURFACE_ALT)
        tree.tag_configure("oddrow", background=T.SURFACE)

        for i, (ts, path) in enumerate(backups):
            try:
                size_kb = f"{path.stat().st_size / 1024:.1f} KB"
            except Exception:
                size_kb = "—"
            tree.insert(
                "", "end", iid=str(path),
                values=(_friendly_ts(ts), path.name, size_kb),
                tags=("evenrow" if i % 2 == 0 else "oddrow",),
            )

        vsb = ttk.Scrollbar(card, orient="vertical",
                            command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y", padx=(0, 2), pady=(0, 2))
        tree.pack(side="left", fill="both", expand=True,
                  padx=2, pady=(0, 2))

        empty = W.EmptyState(
            card, icon="🗄", title="No backups yet",
            hint="Create one from the Backup tab.",
        )
        if not backups:
            empty.place(relx=0.5, rely=0.5, anchor="center")
            empty.lift()

        self.backup_tree = tree

        tree.bind("<<TreeviewSelect>>", self._on_backup_select)
        tree.bind("<Double-1>", lambda e: self._do_restore_backup())

        # ---- Keyboard shortcuts on the backup tree ----
        try:
            from ui.common.ui_helpers import install_table_shortcuts
            install_table_shortcuts(
                tree,
                on_enter=lambda _id: self._do_restore_backup(),
                on_delete=lambda _id: self._do_delete_backup(),
            )
            tree.focus_set()
        except Exception:
            pass

    def _on_backup_select(self, _event=None):
        sel = self.backup_tree.selection()
        self.selected_backup = sel[0] if sel else None
        try:
            self.restore_btn.set_enabled(bool(sel))
            self.delete_btn.set_enabled(bool(sel))
        except Exception:
            pass

    def _do_restore_backup(self):

        if not self.selected_backup:
            messagebox.showinfo("No selection",
                                "Select a backup row first.",
                                parent=self)
            return

        ok = messagebox.askyesno(
            "Restore Backup",
            "Restore this backup?\n\n"
            "The current state will be saved to a new backup first.\n\n"
            "Continue?",
            parent=self,
        )
        if not ok:
            return

        success, err = restore_backup(self.selected_backup)
        if not success:
            messagebox.showerror("Restore failed", str(err), parent=self)
            return

        messagebox.showinfo("Restored",
                            "Backup restored successfully.",
                            parent=self)
        self._switch_tab("backups")

    def _do_delete_backup(self):

        if not self.selected_backup:
            messagebox.showinfo("No selection",
                                "Select a backup row first.",
                                parent=self)
            return

        ok = messagebox.askyesno(
            "Delete Backup",
            "Permanently delete this backup?\n\n"
            f"{self.selected_backup}",
            parent=self,
        )
        if not ok:
            return

        if delete_backup(self.selected_backup):
            self.selected_backup = None
            self._switch_tab("backups")
        else:
            messagebox.showerror("Delete failed",
                                 "Could not delete the backup.",
                                 parent=self)

    def _open_backup_folder(self):
        from app.services.backup_service import BACKUP_DIR
        _open_in_explorer(str(BACKUP_DIR))

    # --------------------------------------------------------
    # SMALL HELPERS
    # --------------------------------------------------------

    def _card(self):
        outer = tk.Frame(self.body, bg=self.CARD,
                         highlightbackground=self.BORDER,
                         highlightthickness=1)
        outer.pack(fill="x")
        inner = tk.Frame(outer, bg=self.CARD)
        inner.pack(fill="both", expand=True, padx=24, pady=22)
        return inner

    def _card_title(self, parent, title):
        tk.Label(parent, text=title.upper(),
                 bg=self.CARD, fg=self.RED,
                 font=T.FONT_LABEL).pack(anchor="w", pady=(0, 8))


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    BackupExport(root)
    root.mainloop()