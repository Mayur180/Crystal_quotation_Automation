"""
Page 5 — Commercial Quotation
- Add buyback parameter
- Subtract buyback from taxable
- Hide Packing / Transportation rows when 0
- Add BuyBack row when > 0
- Add Optional Accessories note from catalog
"""

import re
import shutil
import py_compile
from pathlib import Path


GEN = Path("quotation_generator.py")
shutil.copy2(GEN, GEN.with_suffix(".py.PAGE5_BUYBACK_BACKUP"))
print(f"[backup] {GEN.name}")

s = GEN.read_text(encoding="utf-8")


# ============================================================
# 1. calculate_totals — add buyback parameter
# ============================================================

old_sig = '''def calculate_totals(machine_price=0, machine_qty=1, accessories=None,
                     transportation=0, packing_percent=Decimal("3.5"),
                     packing_mode="Percentage (%)",
                     packing_value=None,
                     cgst_percent=Decimal("9"), sgst_percent=Decimal("9"),
                     gst_type="CGST + SGST",
                     gst_rate=None,
                     igst_percent=None):'''

new_sig = '''def calculate_totals(machine_price=0, machine_qty=1, accessories=None,
                     transportation=0, packing_percent=Decimal("3.5"),
                     packing_mode="Percentage (%)",
                     packing_value=None,
                     cgst_percent=Decimal("9"), sgst_percent=Decimal("9"),
                     gst_type="CGST + SGST",
                     gst_rate=None,
                     igst_percent=None,
                     buyback=0):'''

if old_sig in s:
    s = s.replace(old_sig, new_sig, 1)
    print("[ok] calculate_totals signature updated")
else:
    print("[warn] calculate_totals signature not found")


# ============================================================
# 2. Subtract buyback from taxable
# ============================================================

old_taxable = '''    subtotal = machine_total + accessory_total

    # Packing
    mode_str = str(packing_mode or "").strip().lower()
    if mode_str in ("amount (₹)", "amount", "fixed", "fixed amount", "flat"):
        packing = _decimal(
            packing_value if packing_value is not None else packing_percent
        )
    elif mode_str in ("no packing", "none"):
        packing = Decimal("0")
    else:
        packing = subtotal * packing_percent / Decimal("100")

    taxable = subtotal + packing + transportation'''

new_taxable = '''    subtotal = machine_total + accessory_total

    # BuyBack — subtracted from machine portion
    buyback_dec = _decimal(buyback)

    # Packing
    mode_str = str(packing_mode or "").strip().lower()
    if mode_str in ("amount (₹)", "amount", "fixed", "fixed amount", "flat"):
        packing = _decimal(
            packing_value if packing_value is not None else packing_percent
        )
    elif mode_str in ("no packing", "none"):
        packing = Decimal("0")
    else:
        packing = subtotal * packing_percent / Decimal("100")

    # Taxable = Machine + Accessories + Packing + Transportation − BuyBack
    taxable = subtotal + packing + transportation - buyback_dec
    if taxable < Decimal("0"):
        taxable = Decimal("0")'''

if old_taxable in s:
    s = s.replace(old_taxable, new_taxable, 1)
    print("[ok] taxable calc updated with buyback")
else:
    print("[warn] taxable calc pattern not found")


# ============================================================
# 3. Add buyback to returned dict
# ============================================================

old_ret = '''    return {
        "machine_total": machine_total,
        "accessory_total": accessory_total,
        "subtotal": subtotal,
        "packing": packing,
        "transportation": transportation,
        "taxable": taxable,'''

new_ret = '''    return {
        "machine_total": machine_total,
        "accessory_total": accessory_total,
        "subtotal": subtotal,
        "packing": packing,
        "transportation": transportation,
        "buyback": buyback_dec,
        "taxable": taxable,'''

if old_ret in s:
    s = s.replace(old_ret, new_ret, 1)
    print("[ok] return dict includes buyback")
else:
    print("[warn] return dict pattern not found")


# ============================================================
# 4. _page5 — add buyback param
# ============================================================

old_p5 = '''def _page5(
    doc,
    model,
    product,
    machine_price,
    machine_qty,
    accessories,
    transportation,
    packing_percent,
    packing_mode="Percentage (%)",
    packing_value=None,
    cgst_percent=Decimal("9"),
    sgst_percent=Decimal("9"),
    gst_type="CGST + SGST",
    gst_rate=None,
    igst_percent=Decimal("0"),
):'''

new_p5 = '''def _page5(
    doc,
    model,
    product,
    machine_price,
    machine_qty,
    accessories,
    transportation,
    packing_percent,
    packing_mode="Percentage (%)",
    packing_value=None,
    cgst_percent=Decimal("9"),
    sgst_percent=Decimal("9"),
    gst_type="CGST + SGST",
    gst_rate=None,
    igst_percent=Decimal("0"),
    buyback=0,
):'''

if old_p5 in s:
    s = s.replace(old_p5, new_p5, 1)
    print("[ok] _page5 signature updated")
else:
    print("[warn] _page5 signature not found")


# ============================================================
# 5. _page5 — pass buyback to calculate_totals
# ============================================================

old_call = '''    totals = calculate_totals(
        machine_price=machine_price,
        machine_qty=machine_qty,
        accessories=accessories,
        transportation=transportation,
        packing_percent=packing_percent,
        packing_mode=packing_mode,
        packing_value=packing_value,
        cgst_percent=cgst_percent,
        sgst_percent=sgst_percent,
        gst_type=gst_type,
        gst_rate=gst_rate,
        igst_percent=igst_percent,
    )'''

new_call = '''    totals = calculate_totals(
        machine_price=machine_price,
        machine_qty=machine_qty,
        accessories=accessories,
        transportation=transportation,
        packing_percent=packing_percent,
        packing_mode=packing_mode,
        packing_value=packing_value,
        cgst_percent=cgst_percent,
        sgst_percent=sgst_percent,
        gst_type=gst_type,
        gst_rate=gst_rate,
        igst_percent=igst_percent,
        buyback=buyback,
    )'''

if old_call in s:
    s = s.replace(old_call, new_call, 1)
    print("[ok] _page5 call includes buyback")
else:
    print("[warn] _page5 call pattern not found")


# ============================================================
# 6. totals_data — make Packing/Transportation/BuyBack conditional
# ============================================================

old_totals_data = '''    totals_data = [
        (
            "Machine + Accessories",
            totals["subtotal"],
        ),
        (
            (
                f"Packing ({_decimal(packing_value if packing_mode == 'Percentage (%)' else 0):.2f}%)"
                if packing_mode == "Percentage (%)"
                else (
                    "Packing (Fixed Amount)"
                    if packing_mode == "Amount (₹)"
                    else "Packing"
                )
            ),
            totals["packing"],
        ),
        (
            "Transportation / Freight",
            totals["transportation"],
        ),
        (
            "Taxable Value",
            totals["taxable"],
        ),
        (
            cgst_label,
            totals["cgst"],
        ),
        (
            sgst_label,
            totals["sgst"],
        ),
        (
            igst_label,
            totals["igst"],
        ),
        (
            "GRAND TOTAL",
            totals["grand_total"],
        ),
    ]'''

new_totals_data = '''    # Build totals rows dynamically — hide 0-value optional rows
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

if old_totals_data in s:
    s = s.replace(old_totals_data, new_totals_data, 1)
    print("[ok] totals_data now dynamic")
else:
    print("[warn] totals_data pattern not found")


# ============================================================
# 7. Dynamic totals_table row count + grand total index
# ============================================================

old_table = '''    totals_table = doc.add_table(
        rows=8,
        cols=2,
    )'''

# We'll create it after we know how many rows. Move it AFTER totals_data.
# But since totals_data is defined later, we need to restructure.
# Easiest: keep table creation but move it after totals_data.
# For now, replace rows=8 with rows=len(totals_data) — but that runs before
# totals_data. So we need to swap order.

# Find and remove the early table creation
if old_table in s:
    s = s.replace(old_table, '''    totals_table = doc.add_table(
        rows=1,
        cols=2,
    )''', 1)
    print("[ok] totals_table created with placeholder rows")
else:
    print("[warn] totals_table pattern not found")


# ============================================================
# 8. Update grand total detection + fill table dynamically
# ============================================================

old_loop = '''    for index, (
        label,
        value,
    ) in enumerate(
        totals_data
    ):
        is_grand_total = index == 7'''

new_loop = '''    # Resize table to match totals_data
    totals_table._tbl.remove(totals_table.rows[0]._tr)
    for _ in range(len(totals_data)):
        totals_table.add_row()

    for index, (
        label,
        value,
    ) in enumerate(
        totals_data
    ):
        is_grand_total = (index == len(totals_data) - 1)'''

if old_loop in s:
    s = s.replace(old_loop, new_loop, 1)
    print("[ok] dynamic row count + grand total detection")
else:
    print("[warn] loop pattern not found")


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
    shutil.copy2(GEN.with_suffix(".py.PAGE5_BUYBACK_BACKUP"), GEN)
    print("[restore] reverted")
