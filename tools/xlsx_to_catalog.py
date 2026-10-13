"""
Crystal Catalog Converter
Reads:  data/Crystal/_source/Product_Master.clean.csv
Writes: data/Crystal/catalog.json  (schema v4)
"""
import csv
import json
import sys
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────
ROOT  = Path(__file__).resolve().parent.parent
SRC   = ROOT / "data/Crystal/_source/Product_Master.clean.csv"
DEST  = ROOT / "data/Crystal/catalog.json"

if not SRC.exists():
    sys.exit(
        f"ERROR: clean CSV not found: {SRC}\n"
        f"Run:  python tools/normalize_crystal_csv.py  first."
    )

# ─── Helpers ──────────────────────────────────────────────────────────────
def to_float(v: str) -> float:
    if v is None:
        return 0.0
    s = str(v).replace(",", "").replace("₹", "").strip()
    if not s or s.lower() in {"n.a.", "na", "n/a", "-", "--"}:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0

def to_int(v: str) -> int:
    return int(to_float(v))

def s(v) -> str:
    return "" if v is None else str(v).strip()

# ─── Load ─────────────────────────────────────────────────────────────────
print(f"Reading {SRC} ...")
with SRC.open("r", encoding="utf-8-sig", newline="") as f:
    raw = list(csv.reader(f))

if not raw:
    sys.exit("ERROR: clean CSV is empty.")

header = [" ".join(h.split()) for h in raw[0]]

# Resolve indices by header name (robust to reorder)
def col(name: str) -> int:
    n = " ".join(name.split()).lower()
    for i, h in enumerate(header):
        if h.lower() == n:
            return i
    sys.exit(f"ERROR: required column missing: {name!r}\nHeader: {header}")

I_CODE  = col("Item Code")
I_ITEM  = col("Item")
I_UNITS = col("Units")
I_HSN   = col("Hsn Code")
I_TAX   = col("Tax %")
I_CAT   = col("Item Category")
I_SUB   = col("Sub Category")
I_MANF  = col("Manf Name")
I_RATE  = col("Sales Rate")
I_DISC  = col("Sales Discount")
I_PDESC = col("Print Description")

# ─── Build catalog ────────────────────────────────────────────────────────
catalog = []
skipped = 0
for row_num, row in enumerate(raw[1:], start=2):
    if len(row) < len(header):
        row = row + [""] * (len(header) - len(row))

    model = s(row[I_CODE])
    if not model:                       # safety — clean.csv shouldn't have any
        skipped += 1
        continue

    catalog.append({
        "model":            model,
        "name":             s(row[I_ITEM]),
        "category":         s(row[I_CAT]),
        "sub_category":     s(row[I_SUB]),
        "manufacturer":     s(row[I_MANF]),
        "description":      s(row[I_PDESC]),
        "hsn":              s(row[I_HSN]),
        "unit":             s(row[I_UNITS]),
        "rate":             round(to_float(row[I_RATE]), 2),
        "tax_percent":      round(to_float(row[I_TAX]),  2),
        "default_discount": round(to_float(row[I_DISC]), 2),
        "accessories":      [],
    })

# ─── Write catalog.json ───────────────────────────────────────────────────
DEST.parent.mkdir(parents=True, exist_ok=True)
with DEST.open("w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

# ─── Summary ──────────────────────────────────────────────────────────────
size_kb = DEST.stat().st_size / 1024
print()
print("=" * 62)
print("CRYSTAL CATALOG BUILD — SUMMARY")
print("=" * 62)
print(f"Source rows read :  {len(raw) - 1}")
print(f"Products written :  {len(catalog)}")
print(f"Skipped (blank)  :  {skipped}")
print(f"Output file      :  {DEST}")
print(f"Output size      :  {size_kb:,.1f} KB")
print("=" * 62)
print()
print("Sample — first product:")
print(json.dumps(catalog[0], indent=2, ensure_ascii=False))
print()
print("Sample — a non-CRYSTAL branded row:")
for p in catalog:
    if "KRISTEEL" in p["name"].upper():
        print(json.dumps(p, indent=2, ensure_ascii=False))
        break
