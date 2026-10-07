import shutil
import py_compile
from pathlib import Path

FORM = Path("ui/quotation_form.py")
shutil.copy2(FORM, FORM.with_suffix(".py.PREFILL_BACKUP"))
print("[backup]", FORM.with_suffix(".py.PREFILL_BACKUP"))

s = FORM.read_text(encoding="utf-8")

# --- 1. Add prefill param to __init__ signature ---
old = "    def __init__(self, app=None, parent=None):"
new = "    def __init__(self, app=None, parent=None, prefill=None):"
if old in s:
    s = s.replace(old, new, 1)
    print("[ok] prefill param added")
elif "prefill=None" in s:
    print("[skip] prefill param already present")
else:
    print("[WARN] signature not found")

# --- 2. Store self._prefill right after self.current_step = 1 ---
old = "        self.current_step = 1"
new = "        self.current_step = 1\n        self._prefill = prefill or {}"
if "self._prefill =" not in s and old in s:
    s = s.replace(old, new, 1)
    print("[ok] _prefill stored")
elif "self._prefill =" in s:
    print("[skip] _prefill already stored")
else:
    print("[WARN] current_step marker not found")

FORM.write_text(s, encoding="utf-8")

# --- compile ---
print()
try:
    py_compile.compile(str(FORM), doraise=True)
    print("[check] FORM OK")
except py_compile.PyCompileError as e:
    print("[check] FAIL:", e)
    shutil.copy2(FORM.with_suffix(".py.PREFILL_BACKUP"), FORM)
    print("[restore] reverted")
