"""
Page 6 — update default terms to match manager's file.
"""

import shutil
import py_compile
from pathlib import Path


GEN = Path("quotation_generator.py")
shutil.copy2(GEN, GEN.with_suffix(".py.PAGE6_TERMS_BACKUP"))
print(f"[backup] {GEN.name}")

s = GEN.read_text(encoding="utf-8")


old = '''    default_terms = [
        ("1", "PRICES", "EX WORKS PUNE."),
        ("2", "GST", "As applicable at time of delivery."),
        ("3", "PAYMENT", "100% advance along with purchase order."),
        ("4", "WARRANTY", "One year against manufacturing defects."),
        ("5", "PACKING", "3.5% extra."),
        ("6", "INSURANCE", "Extra if required."),
        ("7", "DISPATCH", "By road transport / courier cargo."),
        ("8", "DELIVERY", "Within 4–6 weeks from receiving date of confirmed order."),
        ("9", "VALIDITY", "60 days."),
        ("10", "FREIGHT", "To pay basis."),
        ("11", "INSTALLATION & COMMISSIONING", "Free of cost by our Engineers."),
    ]'''

new = '''    default_terms = [
        ("1", "PRICES", "EX WORKS PUNE."),
        ("2", "GST", "As applicable at time of delivery."),
        ("3", "PAYMENT", "50% advance along with purchase order & 50% Balance against Proforma invoice."),
        ("4", "VALIDITY", "30 days."),
        ("5", "WARRANTY", "One year against manufacturing defects."),
        ("6", "PACKING", "Extra Applicable."),
        ("7", "INSURANCE", "Extra if required."),
        ("8", "DISPATCH", "By road transport / courier cargo."),
        ("9", "DELIVERY", "Within 4-6 weeks from receiving date of confirmed order."),
        ("10", "FREIGHT", "To pay basis."),
        ("11", "INSTALLATION & COMMISSIONING", "Free of cost by our Engineers."),
    ]'''

if old in s:
    s = s.replace(old, new, 1)
    print("[ok] terms updated (11 rows matching manager)")
else:
    print("[warn] default_terms pattern not found")


GEN.write_text(s, encoding="utf-8")

print()
print("=" * 60)
print("Compile check")
print("=" * 60)
try:
    py_compile.compile(str(GEN), doraise=True)
    print("[ok] GENERATOR OK")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(GEN.with_suffix(".py.PAGE6_TERMS_BACKUP"), GEN)
    print("[restore] reverted")
