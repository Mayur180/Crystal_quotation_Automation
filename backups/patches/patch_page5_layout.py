"""
Page 5 layout — new totals order:
  Machine
  BuyBack Offer (-)
  Accessories
  Packing (if > 0)
  Transportation (if > 0)
  Taxable Value
  GST rows
  Grand Total
"""

import shutil
import py_compile
from pathlib import Path


GEN = Path("quotation_generator.py")
shutil.copy2(GEN, GEN.with_suffix(".py.PAGE5_LAYOUT_BACKUP"))
print(f"[backup] {GEN.name}")

s = GEN.read_text(encoding="utf-8")


# Replace the totals_data builder
old = '''    # Build totals rows dynamically — hide 0-value optional rows
    totals_data = [
        ("Machine + Accessories", totals["subtotal"]),
    ]

    # Packing row — only if > 0
    if totals["packing"] > 0:
        packing_label = (
            f"Packing ({_decimal(packing_value if packing_mode == 'Percentage (%)' else 0):.2f}%)"
            if packing_mode == "Percentage (%)"
            else (
                "Packing (Fixed Amount)"
                if packing_mode == "Amount (₹)"
                else "Packing"
            )
        )
        totals_data.append((packing_label, totals["packing"]))

    # Transportation row — only if > 0
    if totals["transportation"] > 0:
        totals_data.append(("Transportation / Freight", totals["transportation"]))

    # BuyBack row — only if > 0 (shown as negative)
    if totals.get("buyback", Decimal("0")) > 0:
        totals_data.append(("BuyBack Offer for Rs.", -totals["buyback"]))

    # Taxable Value
    totals_data.append(("Taxable Value", totals["taxable"]))

    # GST rows
    totals_data.append((cgst_label, totals["cgst"]))
    totals_data.append((sgst_label, totals["sgst"]))
    totals_data.append((igst_label, totals["igst"]))

    # Grand total
    totals_data.append(("GRAND TOTAL", totals["grand_total"]))'''

new = '''    # Build totals rows dynamically — new layout:
    #   Machine
    #   BuyBack Offer (-)
    #   Accessories
    #   Packing (if > 0)
    #   Transportation (if > 0)
    #   Taxable Value
    #   GST rows
    #   Grand Total
    totals_data = []

    # 1. Machine row
    totals_data.append(("Machine", totals["machine_total"]))

    # 2. BuyBack row — only if > 0
    if totals.get("buyback", Decimal("0")) > 0:
        totals_data.append(("BuyBack Offer", -totals["buyback"]))

    # 3. Accessories row — only if > 0
    if totals.get("accessory_total", Decimal("0")) > 0:
        totals_data.append(("Accessories", totals["accessory_total"]))

    # 4. Packing row — only if > 0
    if totals["packing"] > 0:
        packing_label = (
            f"Packing ({_decimal(packing_value if packing_mode == 'Percentage (%)' else 0):.2f}%)"
            if packing_mode == "Percentage (%)"
            else (
                "Packing (Fixed Amount)"
                if packing_mode == "Amount (₹)"
                else "Packing"
            )
        )
        totals_data.append((packing_label, totals["packing"]))

    # 5. Transportation row — only if > 0
    if totals["transportation"] > 0:
        totals_data.append(("Transportation / Freight", totals["transportation"]))

    # 6. Taxable Value
    totals_data.append(("Taxable Value", totals["taxable"]))

    # 7. GST rows
    totals_data.append((cgst_label, totals["cgst"]))
    totals_data.append((sgst_label, totals["sgst"]))
    totals_data.append((igst_label, totals["igst"]))

    # 8. Grand total
    totals_data.append(("GRAND TOTAL", totals["grand_total"]))'''

if old in s:
    s = s.replace(old, new, 1)
    print("[ok] totals_data rebuilt with new layout")
else:
    print("[warn] totals_data pattern not found")


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
    shutil.copy2(GEN.with_suffix(".py.PAGE5_LAYOUT_BACKUP"), GEN)
    print("[restore] reverted")
