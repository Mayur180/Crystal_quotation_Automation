"""
Preview — same totals layout change as DOCX.
"""

import shutil
import py_compile
from pathlib import Path


PREV = Path("ui/quotation_preview.py")
shutil.copy2(PREV, PREV.with_suffix(".py.PAGE5_LAYOUT_BACKUP"))
print(f"[backup] {PREV.name}")

s = PREV.read_text(encoding="utf-8")


old = '''        # Build totals rows dynamically
        rows_to_show = []

        # Machine + Accessories
        rows_to_show.append(
            ("Machine + Accessories",
             _money(self.totals.get("subtotal", 0)), False)
        )

        # Packing — only if > 0
        packing_val = _decimal(self.totals.get("packing", 0))
        if packing_val > 0:
            rows_to_show.append(
                ("Packing", _money(packing_val), False)
            )

        # Transportation — only if > 0
        if transport_val > 0:
            rows_to_show.append(
                ("Transportation / Freight", _money(transport_val), False)
            )

        # BuyBack — only if > 0
        buyback_val = _decimal(self.totals.get("buyback", 0))
        if buyback_val > 0:
            rows_to_show.append(
                ("BuyBack Offer for Rs.", _money(-buyback_val), False)
            )

        # Taxable Value
        rows_to_show.append(
            ("Taxable Value", _money(self.totals.get("taxable", 0)), False)
        )

        # GST rows (always show)
        rows_to_show.append(
            (f"CGST ({_decimal(self.form_data.get('cgst_percent', 9)):.2f}%)",
             _money(self.totals.get("cgst", 0)), False)
        )
        rows_to_show.append(
            (f"SGST ({_decimal(self.form_data.get('sgst_percent', 9)):.2f}%)",
             _money(self.totals.get("sgst", 0)), False)
        )

        # Grand total
        rows_to_show.append(
            ("GRAND TOTAL",
             _money(self.totals.get("grand_total", 0)), True)
        )'''

new = '''        # Build totals rows dynamically — new layout:
        #   Machine
        #   BuyBack Offer (-)
        #   Accessories
        #   Packing (if > 0)
        #   Transportation (if > 0)
        #   Taxable Value
        #   GST rows
        #   Grand Total
        rows_to_show = []

        # 1. Machine
        rows_to_show.append(
            ("Machine", _money(self.totals.get("machine_total", 0)), False)
        )

        # 2. BuyBack — only if > 0, shown as negative
        buyback_val = _decimal(self.totals.get("buyback", 0))
        if buyback_val > 0:
            rows_to_show.append(
                ("BuyBack Offer", _money(-buyback_val), False)
            )

        # 3. Accessories — only if > 0
        accessory_val = _decimal(self.totals.get("accessory_total", 0))
        if accessory_val > 0:
            rows_to_show.append(
                ("Accessories", _money(accessory_val), False)
            )

        # 4. Packing — only if > 0
        packing_val = _decimal(self.totals.get("packing", 0))
        if packing_val > 0:
            rows_to_show.append(
                ("Packing", _money(packing_val), False)
            )

        # 5. Transportation — only if > 0
        if transport_val > 0:
            rows_to_show.append(
                ("Transportation / Freight", _money(transport_val), False)
            )

        # 6. Taxable Value
        rows_to_show.append(
            ("Taxable Value", _money(self.totals.get("taxable", 0)), False)
        )

        # 7. GST rows
        rows_to_show.append(
            (f"CGST ({_decimal(self.form_data.get('cgst_percent', 9)):.2f}%)",
             _money(self.totals.get("cgst", 0)), False)
        )
        rows_to_show.append(
            (f"SGST ({_decimal(self.form_data.get('sgst_percent', 9)):.2f}%)",
             _money(self.totals.get("sgst", 0)), False)
        )

        # 8. Grand total
        rows_to_show.append(
            ("GRAND TOTAL",
             _money(self.totals.get("grand_total", 0)), True)
        )'''

if old in s:
    s = s.replace(old, new, 1)
    print("[ok] preview totals_data rebuilt")
else:
    print("[warn] preview pattern not found")


PREV.write_text(s, encoding="utf-8")

print()
print("=" * 60)
print("Compile check")
print("=" * 60)
try:
    py_compile.compile(str(PREV), doraise=True)
    print("[ok] PREVIEW OK")
except py_compile.PyCompileError as e:
    print(f"[FAIL] {e}")
    shutil.copy2(PREV.with_suffix(".py.PAGE5_LAYOUT_BACKUP"), PREV)
    print("[restore] reverted")
