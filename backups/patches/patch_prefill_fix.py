import shutil
import py_compile
from pathlib import Path

FORM = Path("ui/quotation_form.py")
shutil.copy2(FORM, FORM.with_suffix(".py.PREFILL_FIX_BACKUP"))
print("[backup]", FORM.with_suffix(".py.PREFILL_FIX_BACKUP"))

s = FORM.read_text(encoding="utf-8")

# The current (broken) order:
old = '''        self._build_interface()

        # apply duplicate prefill (after all widgets exist)
        try:
            self._apply_prefill(getattr(self, "_prefill", {}))
        except Exception:
            pass

        self._load_step(1)'''

# New order: _load_step(1) first, then prefill (which jumps to step 2)
new = '''        self._build_interface()

        # initial render on Customer page
        self._load_step(1)

        # apply duplicate/customer prefill AFTER initial render
        # (this may jump to Step 2)
        try:
            self._apply_prefill(getattr(self, "_prefill", {}))
        except Exception:
            pass'''

if old in s:
    s = s.replace(old, new, 1)
    print("[ok] reordered — prefill now runs after _load_step(1)")
else:
    print("[WARN] anchor not found — file may already be patched")
    # Check if already in correct order
    if s.index("_load_step(1)") < s.index("_apply_prefill(getattr"):
        print("[info] already in correct order")
    else:
        print("[info] still in wrong order — manual edit needed")

FORM.write_text(s, encoding="utf-8")

print()
try:
    py_compile.compile(str(FORM), doraise=True)
    print("[check] FORM OK")
except py_compile.PyCompileError as e:
    print("[check] FAIL:", e)
    shutil.copy2(FORM.with_suffix(".py.PREFILL_FIX_BACKUP"), FORM)
    print("[restore] reverted")
