"""
Update terms in all 3 locations to match manager's file.
"""

import json
import shutil
import py_compile
from pathlib import Path


ROOT = Path.cwd()

# The 11 terms matching the manager's file
MANAGER_TERMS = [
    ("PRICES",                      "EX WORKS PUNE"),
    ("GST",                         "As applicable at time of delivery"),
    ("PAYMENT",                     "50% advance along with purchase order & 50% Balance against Proforma invoice"),
    ("VALIDITY",                    "30 days"),
    ("WARRANTY",                    "One year against manufacturing defects"),
    ("PACKING",                     "Extra Applicable"),
    ("INSURANCE",                   "Extra if required"),
    ("DISPATCH",                    "By road transport / courier cargo"),
    ("DELIVERY",                    "Within 4-6 weeks from receiving date of confirmed order"),
    ("FREIGHT",                     "To pay basis"),
    ("INSTALLATION & COMMISSIONING","Free of cost by our Engineers"),
]


# ============================================================
# 1. Update data/custom_terms.json
# ============================================================

TERMS = ROOT / "data" / "custom_terms.json"
if TERMS.exists():
    shutil.copy2(TERMS, TERMS.with_suffix(".json.BACKUP"))
    print(f"[backup] {TERMS.name}")

    new_terms = [{"title": t, "value": v} for t, v in MANAGER_TERMS]
    TERMS.write_text(
        json.dumps(new_terms, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"[ok] {TERMS.name} updated with {len(new_terms)} terms")


# ============================================================
# 2. Update STANDARD_TERMS in ui/quotation_form.py
# ============================================================

FORM = ROOT / "ui" / "quotation_form.py"
shutil.copy2(FORM, FORM.with_suffix(".py.TERMS_BACKUP"))
print(f"[backup] {FORM.name}")

s = FORM.read_text(encoding="utf-8")

# Build the new STANDARD_TERMS block
new_block_lines = ["STANDARD_TERMS = ["]
for title, value in MANAGER_TERMS:
    # Escape quotes in the value
    esc = value.replace('"', '\\"')
    new_block_lines.append(f'    ("{title}",')
    new_block_lines.append(f'     "{esc}"),')
new_block_lines.append("]")
new_block = "\n".join(new_block_lines)

# Find the existing STANDARD_TERMS block
import re
pattern = re.compile(
    r'STANDARD_TERMS = \[.*?\]',
    re.DOTALL,
)

match = pattern.search(s)
if match:
    s = s[:match.start()] + new_block + s[match.end():]
    FORM.write_text(s, encoding="utf-8")
    print("[ok] STANDARD_TERMS in quotation_form.py updated")
else:
    print("[warn] STANDARD_TERMS pattern not found")


# ============================================================
# 3. Update app/company.py
# ============================================================

COMPANY = ROOT / "app" / "company.py"
if COMPANY.exists():
    shutil.copy2(COMPANY, COMPANY.with_suffix(".py.TERMS_BACKUP"))
    print(f"[backup] {COMPANY.name}")

    cs = COMPANY.read_text(encoding="utf-8")

    # Match a similar list — usually a list of tuples or dicts
    # Just look for any line with 100% advance and packging
    # We'll do a simpler replacement: replace "100% advance" patterns

    replacements = [
        ('"100% advance with purchase order"',
         '"50% advance along with purchase order & 50% Balance against Proforma invoice"'),
        ('"100% advance along with purchase order"',
         '"50% advance along with purchase order & 50% Balance against Proforma invoice"'),
        ('"3.5% extra"', '"Extra Applicable"'),
    ]

    changed = 0
    for old, new in replacements:
        if old in cs:
            cs = cs.replace(old, new)
            changed += 1

    if changed:
        COMPANY.write_text(cs, encoding="utf-8")
        print(f"[ok] app/company.py: {changed} replacements")
    else:
        print("[skip] app/company.py: no matching patterns")
else:
    print("[skip] app/company.py not found")


# ============================================================
# 4. Compile check
# ============================================================

print()
print("=" * 60)
print("Compile check")
print("=" * 60)

ok = True
for p in [FORM, COMPANY]:
    if not p.exists():
        continue
    try:
        py_compile.compile(str(p), doraise=True)
        print(f"[ok] {p.relative_to(ROOT)}")
    except py_compile.PyCompileError as e:
        print(f"[FAIL] {p.relative_to(ROOT)}: {e}")
        ok = False

if ok:
    print()
    print("Done.")
