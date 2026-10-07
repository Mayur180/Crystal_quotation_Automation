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


# ============================================================
# MAIN WINDOW
# ============================================================

class BackupExport(tk.Toplevel):

    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    LIGHT_MUTED = "#9BA1AA"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_DARK = "#980000"
    RED_LIGHT = "#FFF3F3"
    SOFT = "#F8F9FA"
    GREEN = "#16804B"
    GREEN_LIGHT = "#ECF8F1"

    def __init__(self, parent):

        super().__init__(parent)

        self.title("CRYSTAL | Backup / Export")
        self.geometry("1040x700")
        self.minsize(900, 580)
        self.configure(bg=self.BG)

        self.transient(parent)
        self.grab_set()

        self.current_tab = "backup"
        self.selected_backup = None

        self._configure_style()
        self._build_interface()
        self._switch_tab("backup")

        # ---- Escape closes the window ----
        try:
            from ui.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(self, on_escape=self.destroy)
        except Exception:
            pass

    # --------------------------------------------------------

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("BE.Treeview",
                        background="white", fieldbackground="white",
                        foreground=self.TEXT, borderwidth=1,
                        relief="solid", rowheight=28, font=("Arial", 9))
        style.configure("BE.Treeview.Heading",
                        background=self.SOFT, foreground=self.TEXT,
                        font=("Arial", 9, "bold"), relief="flat")
        style.map("BE.Treeview",
                  background=[("selected", self.RED_LIGHT)],
                  foreground=[("selected", self.TEXT)])

    # --------------------------------------------------------

    def _build_interface(self):

        # Header
        header = tk.Frame(self, bg=self.CARD, height=78)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=self.CARD)
        brand.pack(side="left", padx=28)

        tk.Label(brand, text="CRYSTAL", bg=self.CARD, fg=self.RED,
                 font=("Arial", 22, "bold")).pack(side="left", pady=22)
        tk.Label(brand, text="  /  Backup / Export",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 11)).pack(side="left", pady=26)

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")

        # Tabs
        tab_bar = tk.Frame(self, bg=self.CARD, height=52)
        tab_bar.pack(fill="x")
        tab_bar.pack_propagate(False)

        inner = tk.Frame(tab_bar, bg=self.CARD)
        inner.pack(padx=28, pady=8)

        self.tab_buttons = {}
        for key, label in [("backup", "Backup"),
                            ("export", "Export"),
                            ("backups", "Manage Backups")]:
            btn = tk.Button(inner, text=label,
                            command=lambda k=key: self._switch_tab(k),
                            bg=self.SOFT, fg=self.TEXT,
                            activebackground="#ECEEF1",
                            activeforeground=self.TEXT,
                            relief="solid", bd=1, highlightthickness=0,
                            font=("Arial", 9, "bold"),
                            cursor="hand2", padx=14, pady=6)
            btn.pack(side="left", padx=(0, 6))
            self.tab_buttons[key] = btn

        tk.Frame(self, bg=self.BORDER, height=1).pack(fill="x")

        # Body
        self.body = tk.Frame(self, bg=self.BG)
        self.body.pack(fill="both", expand=True, padx=28, pady=18)

        # Footer
        footer = tk.Frame(self, bg=self.CARD, height=66,
                          highlightbackground=self.BORDER,
                          highlightthickness=1)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        tk.Button(footer, text="Close", command=self.destroy,
                  bg="white", fg=self.TEXT,
                  activebackground="#F3F4F6",
                  activeforeground=self.TEXT,
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9), cursor="hand2",
                  width=14, height=2).pack(side="right", padx=22, pady=14)

    # --------------------------------------------------------

    def _switch_tab(self, key):

        self.current_tab = key
        self.selected_backup = None

        for widget in self.body.winfo_children():
            widget.destroy()

        for k, btn in self.tab_buttons.items():
            if k == key:
                btn.configure(bg=self.RED, fg="white",
                              activebackground=self.RED_DARK,
                              activeforeground="white")
            else:
                btn.configure(bg=self.SOFT, fg=self.TEXT,
                              activebackground="#ECEEF1",
                              activeforeground=self.TEXT)

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
        self._card_title(card, "Create a Backup")

        tk.Label(card,
                 text=("Create a zip snapshot of all application data:\n"
                       "catalog, customers, quotations, terms, company "
                       "settings, offer counter, and logo.\n\n"
                       "Backups are stored in:\n"
                       "output/backups/"),
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 10),
                 anchor="w", justify="left").pack(anchor="w", pady=(0, 14))

        row = tk.Frame(card, bg=self.CARD)
        row.pack(fill="x", pady=(0, 8))

        tk.Label(row, text="Label (optional)",
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 9, "bold")).pack(anchor="w")

        self.label_var = tk.StringVar()
        tk.Entry(row, textvariable=self.label_var,
                 bg="white", fg=self.TEXT,
                 relief="solid", bd=1,
                 font=("Arial", 10),
                 insertbackground=self.RED).pack(fill="x", ipady=6, pady=(4, 0))

        tk.Button(card, text="Create Backup Now",
                  command=self._do_create_backup,
                  bg=self.RED, fg="white",
                  activebackground=self.RED_DARK,
                  activeforeground="white",
                  relief="flat", bd=0, highlightthickness=0,
                  font=("Arial", 10, "bold"),
                  cursor="hand2",
                  padx=18, pady=8).pack(anchor="w", pady=(14, 0))

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
        self._card_title(card, "Export Data")

        tk.Label(card,
                 text=("Choose what to export. Files are saved to:\n"
                       "output/exports/"),
                 bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 10),
                 anchor="w", justify="left").pack(anchor="w", pady=(0, 16))

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

        row = tk.Frame(parent, bg=self.SOFT,
                       highlightbackground=self.BORDER,
                       highlightthickness=1)
        row.pack(fill="x", pady=4)

        text = tk.Frame(row, bg=self.SOFT)
        text.pack(side="left", fill="x", expand=True, padx=14, pady=10)

        tk.Label(text, text=title, bg=self.SOFT, fg=self.TEXT,
                 font=("Arial", 10, "bold"), anchor="w").pack(anchor="w")

        tk.Label(text, text=subtitle, bg=self.SOFT, fg=self.MUTED,
                 font=("Arial", 9), anchor="w").pack(anchor="w", pady=(2, 0))

        tk.Button(row, text="Export",
                  command=command,
                  bg=self.CARD, fg=self.TEXT,
                  activebackground="#F3F4F6",
                  activeforeground=self.TEXT,
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9, "bold"),
                  cursor="hand2",
                  padx=14, pady=6).pack(side="right", padx=12, pady=10)

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

        cols = ("timestamp", "filename", "size")
        tree = ttk.Treeview(self.body, columns=cols, show="headings",
                            style="BE.Treeview", height=16)

        for c, w in [("timestamp", 220), ("filename", 380), ("size", 120)]:
            tree.heading(c, text=c.title())
            tree.column(c, width=w, anchor="w",
                        stretch=(c == "filename"))

        for ts, path in backups:
            try:
                size_kb = f"{path.stat().st_size / 1024:.1f} KB"
            except Exception:
                size_kb = "—"
            tree.insert("", "end", iid=str(path),
                        values=(ts, path.name, size_kb))

        vsb = ttk.Scrollbar(self.body, orient="vertical",
                            command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        tree.bind("<<TreeviewSelect>>", self._on_backup_select)
        tree.bind("<Double-1>", lambda e: self._do_restore_backup())

        # Actions below
        actions = tk.Frame(self.body, bg=self.BG)
        actions.pack(side="bottom", fill="x", pady=(10, 0))

        tk.Button(actions, text="Open Folder",
                  command=self._open_backup_folder,
                  bg="white", fg=self.TEXT,
                  activebackground="#F3F4F6",
                  activeforeground=self.TEXT,
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9, "bold"),
                  cursor="hand2",
                  padx=14, pady=6).pack(side="left")

        tk.Button(actions, text="Restore Selected",
                  command=self._do_restore_backup,
                  bg=self.RED, fg="white",
                  activebackground=self.RED_DARK,
                  activeforeground="white",
                  relief="flat", bd=0, highlightthickness=0,
                  font=("Arial", 9, "bold"),
                  cursor="hand2",
                  padx=14, pady=6).pack(side="left", padx=(8, 0))

        tk.Button(actions, text="Delete Selected",
                  command=self._do_delete_backup,
                  bg="white", fg=self.RED,
                  activebackground=self.RED_LIGHT,
                  activeforeground=self.RED,
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9, "bold"),
                  cursor="hand2",
                  padx=14, pady=6).pack(side="left", padx=(8, 0))

        self.backup_tree = tree

        # ---- Keyboard shortcuts on the backup tree ----
        try:
            from ui.ui_helpers import install_table_shortcuts
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
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=self.CARD)
        inner.pack(fill="both", expand=True, padx=24, pady=22)
        return inner

    def _card_title(self, parent, title):
        tk.Label(parent, text=title.upper(),
                 bg=self.CARD, fg=self.RED,
                 font=("Arial", 8, "bold")).pack(anchor="w", pady=(0, 10))


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    BackupExport(root)
    root.mainloop()