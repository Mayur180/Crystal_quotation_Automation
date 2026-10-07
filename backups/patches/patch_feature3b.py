"""Feature 3b: wire date filter into search bar + _reload + _clear_search."""
import shutil
import py_compile
from pathlib import Path

TARGET = Path("ui/quotation_history.py")
BACKUP = Path("ui/quotation_history_FEATURE3B_BACKUP.py")

s = TARGET.read_text(encoding="utf-8")
shutil.copy2(TARGET, BACKUP)
print("[backup]", BACKUP)

# ----------------------------------------------------------------
# 1. Replace _build_search
# ----------------------------------------------------------------
old_build = """    def _build_search(self):

        bar = tk.Frame(self, bg=self.BG)
        bar.pack(fill="x", padx=28, pady=(18, 8))

        tk.Label(
            bar, text="Search",
            bg=self.BG, fg=self.MUTED,
            font=("Arial", 8, "bold"),
        ).pack(side="left", padx=(0, 8))

        entry = tk.Entry(
            bar,
            textvariable=self.search_var,
            bg="white", fg=self.TEXT,
            relief="solid", bd=1,
            font=("Arial", 10),
            insertbackground=self.RED,
        )
        entry.pack(side="left", fill="x", expand=True, ipady=6)
        entry.bind("<KeyRelease>", lambda e: self._reload())

        tk.Button(
            bar, text="Clear",
            command=self._clear_search,
            bg="white", fg=self.MUTED,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="flat", bd=0,
            highlightthickness=0,
            font=("Arial", 9),
            cursor="hand2", padx=12, pady=4,
        ).pack(side="left", padx=(8, 0))
"""

new_build = """    def _build_search(self):

        bar = tk.Frame(self, bg=self.BG)
        bar.pack(fill="x", padx=28, pady=(18, 8))

        def _label(parent, text, pad=(0, 8)):
            tk.Label(
                parent, text=text,
                bg=self.BG, fg=self.MUTED,
                font=("Arial", 8, "bold"),
            ).pack(side="left", padx=pad)

        def _entry(parent, var, width=None, expand=False):
            e = tk.Entry(
                parent,
                textvariable=var,
                bg="white", fg=self.TEXT,
                relief="solid", bd=1,
                font=("Arial", 10),
                insertbackground=self.RED,
            )
            if width:
                e.configure(width=width)
            if expand:
                e.pack(side="left", fill="x", expand=True, ipady=6)
            else:
                e.pack(side="left", ipady=6)
            e.bind("<KeyRelease>", lambda _e: self._reload())
            return e

        _label(bar, "Search")
        _entry(bar, self.search_var, expand=True)

        _label(bar, "From", pad=(12, 6))
        _entry(bar, self.from_date_var, width=12)

        _label(bar, "To", pad=(12, 6))
        _entry(bar, self.to_date_var, width=12)

        tk.Button(
            bar, text="Clear",
            command=self._clear_search,
            bg="white", fg=self.MUTED,
            activebackground="#F3F4F6",
            activeforeground=self.TEXT,
            relief="flat", bd=0,
            highlightthickness=0,
            font=("Arial", 9),
            cursor="hand2", padx=12, pady=4,
        ).pack(side="left", padx=(8, 0))
"""

if old_build in s:
    s = s.replace(old_build, new_build, 1)
    print("[ok] _build_search replaced")
else:
    print("[WARN] _build_search pattern not found")

# ----------------------------------------------------------------
# 2. Replace _clear_search
# ----------------------------------------------------------------
old_clear = """    def _clear_search(self):
        self.search_var.set("")
        self._reload()
"""

new_clear = """    def _clear_search(self):
        self.search_var.set("")
        self.from_date_var.set("")
        self.to_date_var.set("")
        self._reload()
"""

if old_clear in s:
    s = s.replace(old_clear, new_clear, 1)
    print("[ok] _clear_search replaced")
else:
    print("[WARN] _clear_search pattern not found")

# ----------------------------------------------------------------
# 3. Replace _reload
# ----------------------------------------------------------------
old_reload = """    def _reload(self):

        if list_quotations is None:
            self._fill_rows([])
            self.count_label.configure(text="Service unavailable")
            return

        search = self.search_var.get().strip()

        try:
            records = list_quotations(search=search or None)
        except Exception:
            records = []

        self._fill_rows(records)

        self.count_label.configure(
            text=f"{len(records)} quotation(s)"
        )
"""

new_reload = """    def _reload(self):

        if list_quotations is None:
            self._fill_rows([])
            self.count_label.configure(text="Service unavailable")
            return

        search = self.search_var.get().strip()
        from_text = self.from_date_var.get().strip()
        to_text = self.to_date_var.get().strip()

        try:
            records = list_quotations() or []
        except TypeError:
            try:
                records = list_quotations(search=None) or []
            except Exception:
                records = []
        except Exception:
            records = []

        self._all_records = records

        from_date = _parse_date(from_text)
        to_date = _parse_date(to_text)

        filtered = []
        for r in records:
            if not _record_matches_search(r, search):
                continue
            if from_date or to_date:
                rec_date = _parse_date(r.get("date"))
                if rec_date is None:
                    continue
                if from_date and rec_date < from_date:
                    continue
                if to_date and rec_date > to_date:
                    continue
            filtered.append(r)

        self._fill_rows(filtered)

        self.count_label.configure(
            text=f"{len(filtered)} quotation(s)"
        )
"""

if old_reload in s:
    s = s.replace(old_reload, new_reload, 1)
    print("[ok] _reload replaced")
else:
    print("[WARN] _reload pattern not found")

TARGET.write_text(s, encoding="utf-8")

try:
    py_compile.compile(str(TARGET), doraise=True)
    print("[check] syntax OK")
except py_compile.PyCompileError as e:
    print("[check] SYNTAX ERROR:", e)
    shutil.copy2(BACKUP, TARGET)
    print("[restore] restored from backup")
