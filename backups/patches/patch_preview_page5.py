"""
Preview window — page 5 sync with manager's format.
- Title: Standard Quotation -> Commercial Quotation
- Subtitle: updated
- Table headers: match DOCX
- Transportation row: hide when 0
- BuyBack row: add when > 0
- Optional Accessories note: add from catalog
"""

import shutil
import py_compile
from pathlib import Path


PREV = Path("ui/quotation_preview.py")
shutil.copy2(PREV, PREV.with_suffix(".py.PAGE5_PREVIEW_BACKUP"))
print(f"[backup] {PREV.name}")

s = PREV.read_text(encoding="utf-8")


# ============================================================
# 1. Fix title + subtitle
# ============================================================

old_title = '''        self._page_title(card, 5, "Standard Quotation",
                         "Commercial pricing and taxes.")'''

new_title = '''        self._page_title(card, 5, "Commercial Quotation",
                         "Final pricing and tax calculation for the selected configuration.")'''

if old_title in s:
    s = s.replace(old_title, new_title, 1)
    print("[ok] title + subtitle updated")
else:
    print("[warn] title pattern not found")


# ============================================================
# 2. Fix table headers
# ============================================================

old_headers = '''        for text, width in [
            ("Sr.", 4), ("Product / Accessory", 26),
            ("Description", 32), ("Qty.", 5),
            ("Unit Price", 14), ("Total", 14),
        ]:'''

new_headers = '''        for text, width in [
            ("Sr.", 4), ("Product / Accessory", 24),
            ("Model / Code", 22), ("Qty.", 5),
            ("Unit Price", 14), ("Amount", 14),
        ]:'''

if old_headers in s:
    s = s.replace(old_headers, new_headers, 1)
    print("[ok] table headers updated")
else:
    print("[warn] headers pattern not found")


# ============================================================
# 3. Add Model/Code column data to Row 1 (machine)
# ============================================================

old_row1 = '''        desc = (f"Model: {_text(self.form_data.get('model'))}\\n"
                f"Measuring Range: "
                f"{_text(self.product.get('measuring_range'))}")

        for text, width in [
            ("1", 4),
            (self.product.get("product_name", "CRYSTAL VMM"), 26),
            (desc, 32),
            (f"{machine_qty:g}", 5),
            (_money(machine_price), 14),
            (_money(machine_total), 14),
        ]:'''

new_row1 = '''        for text, width in [
            ("1", 4),
            (self.product.get("product_name", "CRYSTAL VMM"), 24),
            (_text(self.form_data.get("model")), 22),
            (f"{machine_qty:g}", 5),
            (_money(machine_price), 14),
            (_money(machine_total), 14),
        ]:'''

if old_row1 in s:
    s = s.replace(old_row1, new_row1, 1)
    print("[ok] row 1 now shows model/code in dedicated column")
else:
    print("[warn] row 1 pattern not found")


# ============================================================
# 4. Row 2 — additional items: use accessory name, hide if 0
# ============================================================

old_row2 = '''        # Row 2 — Additional Items (if accessories)
        if accessories:
            row = tk.Frame(table, bg=self.SOFT)
            row.pack(fill="x")
            for text, width in [
                ("2", 4), ("Additional Items", 26), ("", 32),
                ("-", 5), ("", 14), (_money(accessory_total), 14),
            ]:
                tk.Label(row, text=_text(text), bg=self.SOFT, fg=self.TEXT,
                         font=("Arial", 9), anchor="w",
                         width=width, padx=6, pady=7).pack(side="left")'''

new_row2 = '''        # Row 2 — Additional Items (if accessories > 0)
        if accessories and accessory_total > 0:
            row = tk.Frame(table, bg=self.SOFT)
            row.pack(fill="x")
            for text, width in [
                ("2", 4), ("Additional Items", 24), ("", 22),
                ("-", 5), ("", 14), (_money(accessory_total), 14),
            ]:
                tk.Label(row, text=_text(text), bg=self.SOFT, fg=self.TEXT,
                         font=("Arial", 9), anchor="w",
                         width=width, padx=6, pady=7).pack(side="left")'''

if old_row2 in s:
    s = s.replace(old_row2, new_row2, 1)
    print("[ok] row 2 updated")
else:
    print("[warn] row 2 pattern not found")


# ============================================================
# 5. Row 3 — Transportation: hide when 0, shift row number to 3 only if shown
# ============================================================

old_row3 = '''        # Row 3 — Transportation
        row = tk.Frame(table, bg=self.CARD)
        row.pack(fill="x")
        for text, width in [
            ("3", 4), ("Transportation Cost", 26), ("", 32),
            ("-", 5), ("", 14),
            (_money(self.totals.get("transportation", 0)), 14),
        ]:
            tk.Label(row, text=_text(text), bg=self.CARD, fg=self.TEXT,
                     font=("Arial", 9), anchor="w",
                     width=width, padx=6, pady=7).pack(side="left")'''

new_row3 = '''        # Row 3 — Transportation (only if > 0)
        transport_val = _decimal(self.totals.get("transportation", 0))
        if transport_val > 0:
            row = tk.Frame(table, bg=self.CARD)
            row.pack(fill="x")
            for text, width in [
                ("3", 4), ("Transportation Cost", 24), ("", 22),
                ("-", 5), ("", 14), (_money(transport_val), 14),
            ]:
                tk.Label(row, text=_text(text), bg=self.CARD, fg=self.TEXT,
                         font=("Arial", 9), anchor="w",
                         width=width, padx=6, pady=7).pack(side="left")'''

if old_row3 in s:
    s = s.replace(old_row3, new_row3, 1)
    print("[ok] transportation row now conditional")
else:
    print("[warn] row 3 pattern not found")


# ============================================================
# 6. Totals block — add Packing, BuyBack + hide zero rows
# ============================================================

old_totals = '''        for label, value, is_grand in [
            ("Taxable Value / Base Price",
             _money(self.totals.get("taxable", 0)), False),
            (f"CGST ({_decimal(self.form_data.get('cgst_percent', 9)):.2f}%)",
             _money(self.totals.get("cgst", 0)), False),
            (f"SGST ({_decimal(self.form_data.get('sgst_percent', 9)):.2f}%)",
             _money(self.totals.get("sgst", 0)), False),
            ("GRAND TOTAL",
             _money(self.totals.get("grand_total", 0)), True),
        ]:'''

new_totals = '''        # Build totals rows dynamically
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
        )

        for label, value, is_grand in rows_to_show:'''

if old_totals in s:
    s = s.replace(old_totals, new_totals, 1)
    print("[ok] totals rows now dynamic (with Packing + BuyBack)")
else:
    print("[warn] totals pattern not found")


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
    shutil.copy2(PREV.with_suffix(".py.PAGE5_PREVIEW_BACKUP"), PREV)
    print("[restore] reverted")
