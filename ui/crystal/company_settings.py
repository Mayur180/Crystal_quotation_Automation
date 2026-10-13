# ============================================================
# CRYSTAL / ARMATECH ASSOCIATES
# COMPANY SETTINGS — Modal editor
#
# File:
#   ui/company_settings.py
# ============================================================

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path


PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


try:
    from app.services.company_settings_service import (
        load_settings,
        save_settings,
        reset_settings,
        logo_full_path,
    )
except Exception:
    load_settings = None
    save_settings = None
    reset_settings = None
    logo_full_path = None


class CompanySettings(tk.Toplevel):

    BG = "#F4F5F7"
    CARD = "#FFFFFF"
    TEXT = "#17191D"
    MUTED = "#747A84"
    LIGHT_MUTED = "#9BA1AA"
    BORDER = "#E1E4E8"
    RED = "#C40000"
    RED_DARK = "#980000"
    RED_LIGHT = "#FFF3F3"
    GREEN = "#16804B"
    SOFT = "#F8F9FA"

    def __init__(self, parent):
        super().__init__(parent)

        self.title("CRYSTAL | Company Settings")
        self.geometry("920x780")
        self.minsize(820, 640)
        self.configure(bg=self.BG)
        self.transient(parent)
        self.grab_set()

        self._vars = {}
        self._build_interface()
        self._load()

        # ---- Keyboard shortcuts ----
        try:
            from ui.common.ui_helpers import install_modal_shortcuts
            install_modal_shortcuts(
                self,
                on_escape=self.destroy,
                on_enter=self._save,
            )
        except Exception:
            pass

    # ========================================================
    # VARIABLES
    # ========================================================

    def _build_interface(self):

        self._build_header()
        self._build_body()
        self._build_footer()

    def _build_header(self):
        header = tk.Frame(self, bg=self.CARD, height=76)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=self.CARD)
        brand.pack(side="left", padx=26)

        tk.Label(brand, text="CRYSTAL", bg=self.CARD, fg=self.RED,
                 font=("Arial", 20, "bold")).pack(side="left", pady=20)

        tk.Label(brand, text="  /  Company Settings",
                 bg=self.CARD, fg=self.MUTED,
                 font=("Arial", 10)).pack(side="left", pady=24)

        tk.Frame(header, bg=self.RED, height=3).pack(side="bottom", fill="x")

    def _build_body(self):
        wrap = tk.Frame(self, bg=self.BG)
        wrap.pack(fill="both", expand=True)

        canvas = tk.Canvas(wrap, bg=self.BG, highlightthickness=0, bd=0)
        sb = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)

        inner = tk.Frame(canvas, bg=self.BG)
        canvas_win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)

        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(canvas_win, width=e.width))

        # ---- General card ----
        card1 = self._card(inner)
        self._section_title(card1, "General")

        self._field(card1, "Company Name", "name")
        self._field(card1, "State", "state")
        self._field(card1, "State Code", "state_code")
        self._field(card1, "Brand", "brand")
        self._field(card1, "Tagline", "tagline")
        self._field(card1, "Address", "address", multiline=True)
        self._field(card1, "Phone", "phone")
        self._field(card1, "Email", "email")
        self._field(card1, "Website", "website")

        # ---- Logo card ----
        card2 = self._card(inner)
        self._section_title(card2, "Logo")

        row = tk.Frame(card2, bg=self.CARD)
        row.pack(fill="x", pady=4)

        tk.Label(row, text="Logo Path", bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 9, "bold"), width=18,
                 anchor="w").pack(side="left")

        self._vars["logo_path"] = tk.StringVar()

        entry = tk.Entry(row, textvariable=self._vars["logo_path"],
                         bg="white", fg=self.TEXT, relief="solid", bd=1,
                         font=("Arial", 10), insertbackground=self.RED)
        entry.pack(side="left", fill="x", expand=True, ipady=6)

        tk.Button(row, text="Browse…", command=self._browse_logo,
                  bg=self.SOFT, fg=self.TEXT,
                  activebackground="#ECEEF1", activeforeground=self.TEXT,
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9), cursor="hand2",
                  padx=12, pady=4).pack(side="left", padx=(8, 0))

        # ---- Quotation defaults ----
        card3 = self._card(inner)
        self._section_title(card3, "Quotation Defaults")

        self._field(card3, "Offer Prefix", "prefix")
        self._field(card3, "Financial Year", "financial_year")
        self._field(card3, "Validity (days)", "validity_days")
        self._field(card3, "Packing (%)", "packing_percent")
        self._field(card3, "CGST (%)", "cgst_percent")
        self._field(card3, "SGST (%)", "sgst_percent")

        # ---- Terms text defaults ----
        card4 = self._card(inner)
        self._section_title(card4, "Default Terms Text")
        self._field(card4, "Payment Terms", "payment_terms")
        self._field(card4, "Warranty", "warranty")
        self._field(card4, "Delivery", "delivery")
        self._field(card4, "Freight", "freight")
        self._field(card4, "Installation", "installation")

        tk.Frame(inner, bg=self.BG, height=20).pack()

        

        # ---- Output Folder card ----
        card_out = self._card(inner)
        self._section_title(card_out, "Output Folder")

        tk.Label(
            card_out,
            text="PDF and Word files are saved under this folder.",
            bg=self.CARD, fg=self.MUTED,
            font=("Arial", 9), anchor="w",
        ).pack(fill="x", pady=(0, 8))

        out_row = tk.Frame(card_out, bg=self.CARD)
        out_row.pack(fill="x", pady=4)

        tk.Label(
            out_row, text="Folder", bg=self.CARD, fg=self.TEXT,
            font=("Arial", 9, "bold"), width=18, anchor="w",
        ).pack(side="left")

        self._vars["output_folder"] = tk.StringVar()

        tk.Entry(
            out_row,
            textvariable=self._vars["output_folder"],
            bg="white", fg=self.TEXT, relief="solid", bd=1,
            font=("Arial", 10), insertbackground=self.RED,
        ).pack(side="left", fill="x", expand=True, ipady=6)

        tk.Button(
            out_row, text="Browse…", command=self._browse_output_folder,
            bg=self.SOFT, fg=self.TEXT,
            activebackground="#ECEEF1", activeforeground=self.TEXT,
            relief="solid", bd=1, highlightthickness=0,
            font=("Arial", 9), cursor="hand2",
            padx=12, pady=4,
        ).pack(side="left", padx=(8, 0))

        tk.Label(
            card_out,
            text="Inside this folder, the app creates:",
            bg=self.CARD, fg=self.MUTED,
            font=("Arial", 9, "italic"), anchor="w",
        ).pack(fill="x", pady=(8, 0))

        tk.Label(
            card_out,
            text="    DD-MM-YYYY/word/Quotation_*.docx\n"
                 "    DD-MM-YYYY/pdf/Quotation_*.pdf",
            bg=self.CARD, fg=self.MUTED,
            font=("Courier New", 9), anchor="w", justify="left",
        ).pack(fill="x")

        tk.Frame(inner, bg=self.BG, height=20).pack()

        # ---- Maintenance / Actions card ----
        card3 = self._card(inner)
        self._section_title(card3, "Actions")

        # ---- Reset counter button ----
        reset_wrap = tk.Frame(card3, bg=self.CARD)
        reset_wrap.pack(fill="x", pady=6)

        tk.Button(
            reset_wrap,
            text="Reset Quotation Counter",
            command=self._reset_counter_button,
            bg=self.RED,
            fg="white",
            activebackground=self.RED_DARK,
            activeforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Arial", 10, "bold"),
            cursor="hand2",
            padx=14,
            pady=8,
        ).pack(side="left")

        tk.Label(
            reset_wrap,
            text="  Sets the next quotation number to 001.",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Arial", 9),
        ).pack(side="left", padx=8)

        # ---- Delete backups button ----
        del_wrap = tk.Frame(card3, bg=self.CARD)
        del_wrap.pack(fill="x", pady=6)

        tk.Button(
            del_wrap,
            text="Delete Backup Files",
            command=self._delete_backup_button,
            bg="white",
            fg=self.TEXT,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="solid",
            bd=1,
            highlightthickness=0,
            font=("Arial", 10),
            cursor="hand2",
            padx=14,
            pady=8,
        ).pack(side="left")

        tk.Label(
            del_wrap,
            text="  Removes old auto-backup copies (keeps your data).",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Arial", 9),
        ).pack(side="left", padx=8)


    def _card(self, parent):
        outer = tk.Frame(parent, bg=self.CARD,
                         highlightbackground=self.BORDER, highlightthickness=1)
        outer.pack(fill="x", padx=24, pady=(16, 0))
        inner = tk.Frame(outer, bg=self.CARD)
        inner.pack(fill="both", expand=True, padx=18, pady=16)
        return inner

    def _section_title(self, parent, text):
        tk.Label(parent, text=text.upper(), bg=self.CARD, fg=self.RED,
                 font=("Arial", 8, "bold")).pack(anchor="w", pady=(0, 8))

    def _field(self, parent, label, key, multiline=False):
        box = tk.Frame(parent, bg=self.CARD)
        box.pack(fill="x", pady=4)

        tk.Label(box, text=label, bg=self.CARD, fg=self.TEXT,
                 font=("Arial", 9, "bold"), width=18,
                 anchor="w").pack(side="left", anchor="n")

        self._vars[key] = tk.StringVar()

        if multiline:
            widget = tk.Text(box, height=3, bg="white", fg=self.TEXT,
                             relief="solid", bd=1, font=("Arial", 10),
                             insertbackground=self.RED, wrap="word")
            widget.pack(side="left", fill="x", expand=True, ipady=4)
            self._vars[key + "_widget"] = widget
        else:
            widget = tk.Entry(box, textvariable=self._vars[key],
                              bg="white", fg=self.TEXT, relief="solid", bd=1,
                              font=("Arial", 10), insertbackground=self.RED)
            widget.pack(side="left", fill="x", expand=True, ipady=6)

    def _build_footer(self):
        footer = tk.Frame(self, bg="white", height=66,
                          highlightbackground=self.BORDER, highlightthickness=1)
        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        tk.Button(footer, text="Reset to Defaults",
                  command=self._reset,
                  bg="white", fg=self.RED,
                  activebackground=self.RED_LIGHT, activeforeground=self.RED,
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9, "bold"), cursor="hand2",
                  width=18, height=2).pack(side="left", padx=(22, 0), pady=14)

        tk.Button(footer, text="Cancel", command=self.destroy,
                  bg="white", fg=self.TEXT,
                  activebackground="#F3F4F6", activeforeground=self.TEXT,
                  relief="solid", bd=1, highlightthickness=0,
                  font=("Arial", 9), cursor="hand2",
                  width=14, height=2).pack(side="right", padx=(8, 22), pady=14)

        tk.Button(footer, text="Save Settings", command=self._save,
                  bg=self.RED, fg="white",
                  activebackground=self.RED_DARK, activeforeground="white",
                  relief="flat", bd=0, highlightthickness=0,
                  font=("Arial", 10, "bold"), cursor="hand2",
                  width=18, height=2).pack(side="right", pady=14)

    # ========================================================
    # DATA LOAD / SAVE
    # ========================================================

    def _load(self):
        # Load output folder from settings_service if available
        try:
            from app.services.settings_service import get_output_folder as _gof
            _folder = str(_gof())
            if "output_folder" not in self._vars:
                self._vars["output_folder"] = tk.StringVar()
            self._vars["output_folder"].set(_folder)
        except Exception:
            pass


        if load_settings is None:
            return
        try:
            settings = load_settings()
        except Exception:
            return

        for key, var in self._vars.items():
            if key.endswith("_widget"):
                continue
            # Skip output_folder — already loaded from settings_service above
            if key == "output_folder":
                continue
            value = settings.get(key, "")
            if isinstance(var, tk.StringVar):
                var.set(str(value) if value is not None else "")

        widget = self._vars.get("address_widget")
        if widget is not None:
            widget.delete("1.0", "end")
            widget.insert("1.0", settings.get("address", ""))

    def _collect(self):
        data = {}
        for key, var in self._vars.items():
            if key.endswith("_widget"):
                continue
            if isinstance(var, tk.StringVar):
                data[key] = var.get().strip()

        widget = self._vars.get("address_widget")
        if widget is not None:
            data["address"] = widget.get("1.0", "end").strip()

        # Numeric coerce
        for num_key in ("validity_days",):
            try:
                data[num_key] = int(data.get(num_key, 60))
            except Exception:
                data[num_key] = 60
        for pct_key in ("packing_percent", "cgst_percent", "sgst_percent"):
            try:
                data[pct_key] = float(data.get(pct_key, 0))
            except Exception:
                data[pct_key] = 0.0

        return data

    def _reset_counter_button(self):
        """Reset the quotation counter to 0 (next quote = 001)."""
        from tkinter import messagebox

        confirm = messagebox.askyesno(
            "Reset Quotation Counter",
            "This will reset the next quotation number to 001.\n\n"
            "Continue?",
            parent=self,
        )

        if not confirm:
            return

        try:
            from app.services.quotation_number_service import (
                reset_counter,
                get_current_quotation_number,
            )
            reset_counter()
            current = get_current_quotation_number()
            messagebox.showinfo(
                "Done",
                f"Counter reset.\n\nCurrent: {current}\n"
                "The next quote will be 001.",
                parent=self,
            )
        except Exception as exc:
            messagebox.showerror(
                "Failed",
                f"Could not reset counter:\n\n{exc}",
                parent=self,
            )

    def _delete_backup_button(self):
        """Delete backup files/folders created by the app."""
        import os
        import shutil
        from tkinter import messagebox
        from pathlib import Path

        # Location 1: project backups/ folder
        project_root = Path(__file__).resolve().parents[1]
        backups_dir = project_root / "backups"

        # Location 2: any *.bak / *.BEFORE_* files
        bak_files = list(project_root.rglob("*.bak")) +                     list(project_root.rglob("*.BEFORE_*")) +                     list(project_root.rglob("*.MILESTONE_*"))

        # Ignore files inside .venv
        bak_files = [f for f in bak_files if ".venv" not in str(f)]

        total_items = 0
        if backups_dir.is_dir():
            total_items += sum(1 for _ in backups_dir.rglob("*") if _.is_file())
        total_items += len(bak_files)

        if total_items == 0:
            messagebox.showinfo(
                "Nothing to Delete",
                "No backup files were found.",
                parent=self,
            )
            return

        confirm = messagebox.askyesno(
            "Delete Backup Files",
            f"Found {total_items} backup file(s).\n\n"
            "Delete them all?\n\n"
            "(Your main data files are NOT affected.)",
            parent=self,
        )

        if not confirm:
            return

        deleted = 0
        errors = 0

        # Delete the backups folder contents
        if backups_dir.is_dir():
            try:
                shutil.rmtree(backups_dir)
                deleted += 1
            except Exception:
                errors += 1

        # Delete individual .bak files
        for f in bak_files:
            try:
                f.unlink()
                deleted += 1
            except Exception:
                errors += 1

        messagebox.showinfo(
            "Backup Cleanup",
            f"Deleted {deleted} item(s).\n"
            f"Errors: {errors}",
            parent=self,
        )

    def _browse_output_folder(self):
        """Let the user pick a new output folder."""
        from tkinter import filedialog
        try:
            current = self._vars.get("output_folder")
            current_val = current.get() if current else ""
        except Exception:
            current_val = ""

        chosen = filedialog.askdirectory(
            title="Choose output folder",
            initialdir=current_val or None,
            parent=self,
        )
        if not chosen:
            return

        try:
            self._vars["output_folder"].set(chosen)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"Could not set folder:\n{e}",
                parent=self,
            )

    def _save(self):
        if save_settings is None:
            messagebox.showerror("Unavailable",
                                 "Company settings service not loaded.",
                                 parent=self)
            return

        data = self._collect()
        ok, err = save_settings(data)

        # Also persist the output folder via settings_service
        if ok:
            try:
                from app.services.settings_service import set_output_folder
                folder_var = self._vars.get("output_folder")
                if folder_var:
                    folder_val = folder_var.get().strip()
                    if folder_val:
                        set_output_folder(folder_val)
            except Exception as e:
                print(f"[output-folder] save failed: {e}")

        if ok:
            messagebox.showinfo("Saved",
                                "Company settings saved successfully.\n\n"
                                "Changes will take effect on the next "
                                "generated quotation.",
                                parent=self)
            self.destroy()
        else:
            messagebox.showerror("Save failed", err, parent=self)

    def _reset(self):
        ok = messagebox.askyesno(
            "Reset settings",
            "This will discard your saved settings and restore the defaults "
            "built into the application.\n\nContinue?",
            parent=self,
        )
        if not ok:
            return

        if reset_settings is None:
            return
        success, err = reset_settings()
        if success:
            self._load()
            messagebox.showinfo("Reset",
                                "Settings have been reset to defaults.",
                                parent=self)
        else:
            messagebox.showerror("Reset failed", err, parent=self)

    def _browse_logo(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Select logo image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        try:
            rel = os.path.relpath(path, PROJECT_ROOT).replace("\\", "/")
        except Exception:
            rel = path

        self._vars["logo_path"].set(rel)


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    CompanySettings(root)
    root.mainloop()