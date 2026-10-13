import csv, sys
from pathlib import Path

SRC = Path("data/Crystal/_source/Product_Master.csv")

if not SRC.exists():
    sys.exit(f"ERROR: {SRC} not found")

with SRC.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.reader(f)
    rows = list(reader)

print(f"Total physical CSV records: {len(rows)}")
print(f"Header column count: {len(rows[0])}")
print()

print("=== RAW HEADER (repr, showing newlines) ===")
for i, h in enumerate(rows[0]):
    print(f"  [{i:2d}] {h!r}")
print()

print("=== NORMALIZED HEADER ===")
norm = [" ".join(h.split()) for h in rows[0]]
for i, h in enumerate(norm):
    print(f"  [{i:2d}] {h}")
print()

# Find key column indices by normalized name
def idx(name):
    n = " ".join(name.split()).lower()
    for i, h in enumerate(norm):
        if h.lower() == n:
            return i
    return None

keys = ["Rec No.", "Item Code", "Item", "Units", "Hsn Code", "Tax %",
        "Item Category", "Sub Category", "Manf Name",
        "Sales Rate", "Sales Discount", "Item Size", "Print Description"]
print("=== KEY COLUMN INDICES ===")
for k in keys:
    print(f"  {k:20s} -> {idx(k)}")
print()

print("=== FIRST 2 DATA ROWS (repr, first 15 cols) ===")
for r_i, row in enumerate(rows[1:3], start=1):
    print(f"--- Row {r_i} (len={len(row)}) ---")
    for c_i, cell in enumerate(row[:15]):
        print(f"  [{c_i:2d}] {cell[:120]!r}")
    print()

# Sanity: check for rows with wrong column count
from collections import Counter
counts = Counter(len(r) for r in rows[1:])
print(f"=== ROW LENGTH DISTRIBUTION (data rows) ===")
for length, n in sorted(counts.items(), reverse=True):
    print(f"  {length:3d} cols: {n:5d} rows")
