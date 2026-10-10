"""
Add 'Output Folder' field to Company Settings.
"""
import shutil
import py_compile
from pathlib import Path

UI = Path("ui/company_settings.py")
shutil.copy2(UI, UI.with_suffix(".py.OUTPUT_FOLDER_BACKUP"))
print(f"[backup] {UI.name}")

s = UI.read_text(encoding="utf-8")


# ============================================================
# 1. Insert new card before "Maintenance / Actions" card
# ============================================================

old = '''        tk.Frame(inner, bg=self.BG, height=20).pack()

        # ---- Maintenance / Actions card ----
        card3 = self._card(inner)
        self._section_title(card3, "Actions")'''

new = '''        tk.Frame(inner, bg=self.BG, height=20).pack()

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
            text="    DD-MM-YYYY/word/Quotation_*.docx\\n"
                 "    DD-MM-YYYY/pdf/Quotation_*.pdf",
            bg=self.CARD, fg=self.MUTED,
            font=("Courier New", 9), anchor="w", justify="left",
        ).pack(fill="x")

        tk.Frame(inner, bg=self.BG, height=20).pack()

        # ---- Maintenance / Actions card ----
        card3 = self._card(inner)
        self._section_title(card3, "Actions")'''

if old in s:
    s = s.replace(old, new, 1)
    print("[ok] Output Folder card added")
else:
    print("[warn] pattern not found — showing context")
    idx = s.find("Maintenance / Actions")
    if idx > 0:
        print(repr(s[idx-200:idx+100]))


# ============================================================
# 2. Add _browse_output_folder method (after _browse_logo)
# ============================================================

old_method = '''    def _browse_logo(self):'''
new_method = '''    def _browse_output_folder(self):
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
                f"Could not set folder:\\n{e}",
                parent=self,
            )

    def _browse_logo(self):'''

if "_browse_output_folder" not in s and old_method in s:
    s = s.replace(old_method, new_method, 1)
    print("[ok] _browse_output_folder method added")
else:
    print("[skip/warn] _browse method")


# ============================================================
# 3. Ensure _load pulls output_folder from settings_service
# ============================================================

old_load = '''    def _load(self):'''
if old_load in s:
    # Add a hook at the start of _load
    insert = '''    def _load(self):
        # Load output folder from settings_service if available
        try:
            from app.services.settings_service import get_output_folder as _gof
            _folder = str(_gof())
            if "output_folder" not in self._vars:
                self._vars["output_folder"] = tk.StringVar()
            self._vars["output_folder"].set(_folder)
        except Exception:
            pass

'''
    # Only replace the first occurrence
    idx = s.find(old_load)
    if idx >= 0 and "settings_service import get_output_folder as _gof" not in s:
        s = s[:idx] + insert + s[idx + len(old_load):]
        print("[ok] _load reads output folder from settings")


# ============================================================
# 4. Save: after company settings saved, also save output folder
# ============================================================

old_save = '''        data = self._collect()
        ok, err = save_settings(data)

        if ok:
            messagebox.showinfo("Saved",'''

new_save = '''        data = self._collect()
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
            messagebox.showinfo("Saved",'''

if old_save in s and 'from app.services.settings_service import set_output_folder' not in s:
    s = s.replace(old_save, new_save, 1)
    print("[ok] _save persists output folder")


UI.write_text(s, encoding="utf-8")

print()
print("=" * 60)
print("Compile check")
print("=" * 60)
try:
    py_compile.compile(str(UI), doraise=True)
    print("[ok] COMPANY SETTINGS OK")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(UI.with_suffix(".py.OUTPUT_FOLDER_BACKUP"), UI)
    print("[restore] reverted")
