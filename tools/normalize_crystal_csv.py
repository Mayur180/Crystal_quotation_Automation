"""
Crystal Product Master — Normalizer + Deduplicator
Reads:  data/Crystal/_source/Product_Master.csv
Writes: data/Crystal/_source/Product_Master.clean.csv
Logs:   data/Crystal/_source/skipped.log
        data/Crystal/_source/duplicates.log
        data/Crystal/_source/normalize_report.txt
"""
import csv
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

# ─── Paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / "data/Crystal/_source/Product_Master.csv"
OUT  = ROOT / "data/Crystal/_source/Product_Master.clean.csv"
SKIP = ROOT / "data/Crystal/_source/skipped.log"
DUPE = ROOT / "data/Crystal/_source/duplicates.log"
RPT  = ROOT / "data/Crystal/_source/normalize_report.txt"

if not SRC.exists():
    sys.exit(f"ERROR: Source not found: {SRC}")

# ─── Helpers ──────────────────────────────────────────────────────────────
HTML_ENTITIES = {
    "&amp;": "&", "&lt;": "<", "&gt;": ">",
    "&quot;": '"', "&#39;": "'", "&apos;": "'", "&nbsp;": " ",
}
ENTITY_RE = re.compile("|".join(re.escape(k) for k in HTML_ENTITIES))
BR_RE     = re.compile(r"<\s*br\s*/?\s*>", re.IGNORECASE)

NULL_TOKENS = {"", "n.a.", "na", "n/a", "-", "--", "none", "null"}

def clean_text(v: str) -> str:
    """Collapse whitespace, convert <br> to \\n, decode basic entities."""
    if v is None:
        return ""
    v = str(v)
    v = ENTITY_RE.sub(lambda m: HTML_ENTITIES[m.group(0)], v)
    v = BR_RE.sub("\n", v)
    # normalize line-by-line: strip edges, collapse internal runs of spaces
    lines = [" ".join(line.split()) for line in v.splitlines()]
    v = "\n".join(lines).strip()
    return v

def clean_code(v: str) -> str:
    """Item code normalization: strip stray ']', fix AA spacing, collapse WS."""
    v = clean_text(v)
    v = v.lstrip("]").strip()                     # "]AA - 1216" -> "AA - 1216"
    v = re.sub(r"\bA\s+A\s*-\s*", "AA-", v, flags=re.IGNORECASE)  # "A A -" -> "AA-"
    v = re.sub(r"\bAA\s*-\s*", "AA-", v)          # "AA -" / "AA-" -> "AA-"
    v = re.sub(r"\s{2,}", " ", v).strip()
    return v

def is_null(v: str) -> bool:
    return clean_text(v).lower() in NULL_TOKENS

def to_float(v: str) -> float:
    """Handle '1,500.00', '₹1500', '1500.50', '', 'N.A.'"""
    if v is None:
        return 0.0
    s = clean_text(v).replace(",", "").replace("₹", "").strip()
    if s.lower() in NULL_TOKENS:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0

# ─── Load ─────────────────────────────────────────────────────────────────
print(f"Reading {SRC} ...")
with SRC.open("r", encoding="utf-8-sig", newline="") as f:
    raw = list(csv.reader(f))

header = [" ".join(h.split()) for h in raw[0]]
print(f"Header columns: {len(header)}")
print(f"Total records (incl. header): {len(raw)}")

# Resolve key column indices by *name* (robust to reordering)
def col(name):
    n = " ".join(name.split()).lower()
    for i, h in enumerate(header):
        if h.lower() == n:
            return i
    sys.exit(f"ERROR: missing column {name!r}")

I_RECNO = col("Rec No.")
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
I_SIZE  = col("Item Size")
I_PDESC = col("Print Description")

# ─── Process ──────────────────────────────────────────────────────────────
skipped     = []   # (row_num, reason, snippet)
duplicates  = []   # (row_num, dup_of_row, code, name)
clean_rows  = []
seen_keys   = OrderedDict()   # (code_lower, name_lower) -> first_row_num
seen_codes  = Counter()
stats       = Counter()

for row_num, row in enumerate(raw[1:], start=2):   # 2 = human line of first data row
    # Pad ragged rows (defensive — all were 35 in our scan, but be safe)
    if len(row) < len(header):
        row = row + [""] * (len(header) - len(row))

    code_raw = row[I_CODE]
    item_raw = row[I_ITEM]

    code = clean_code(code_raw)
    name = clean_text(item_raw)

    # Rule 1 — Skip blank Item Code
    if not code:
        skipped.append((row_num, "blank_item_code",
                        f"name={name[:60]!r}" if name else "fully_blank_row"))
        stats["skipped_blank_code"] += 1
        continue

    # Rule 2 — Remove exact duplicates (case-insensitive code+name)
    key = (code.lower(), name.lower())
    if key in seen_keys:
        duplicates.append((row_num, seen_keys[key], code, name))
        stats["duplicates"] += 1
        continue
    seen_keys[key] = row_num
    seen_codes[code.lower()] += 1

    # Build normalized row
    out = list(row)                       # keep all 35 columns
    out[I_RECNO] = str(len(clean_rows) + 1)   # renumber 1..N
    out[I_CODE]  = code
    out[I_ITEM]  = name
    out[I_UNITS] = clean_text(row[I_UNITS])
    out[I_HSN]   = clean_text(row[I_HSN])
    out[I_TAX]   = f"{to_float(row[I_TAX]):g}" if row[I_TAX].strip() else "0"
    out[I_CAT]   = "" if is_null(row[I_CAT]) else clean_text(row[I_CAT]).upper()
    out[I_SUB]   = "" if is_null(row[I_SUB]) else clean_text(row[I_SUB])
    out[I_MANF]  = "" if is_null(row[I_MANF]) else clean_text(row[I_MANF]).upper()
    out[I_RATE]  = f"{to_float(row[I_RATE]):.2f}"
    out[I_DISC]  = f"{to_float(row[I_DISC]):.2f}"
    out[I_SIZE]  = "" if is_null(row[I_SIZE]) else clean_text(row[I_SIZE])
    out[I_PDESC] = clean_text(row[I_PDESC])
    clean_rows.append(out)

# ─── Write cleaned CSV ────────────────────────────────────────────────────
with OUT.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    w.writerow(header)
    w.writerows(clean_rows)

# ─── Write logs ───────────────────────────────────────────────────────────
with SKIP.open("w", encoding="utf-8") as f:
    f.write(f"# Skipped rows (blank Item Code): {len(skipped)}\n")
    f.write(f"# Format: csv_line | reason | snippet\n")
    for rn, reason, snippet in skipped:
        f.write(f"{rn} | {reason} | {snippet}\n")

with DUPE.open("w", encoding="utf-8") as f:
    f.write(f"# Duplicate rows removed: {len(duplicates)}\n")
    f.write(f"# Format: dup_line | first_seen_line | code | name\n")
    for rn, first, code, name in duplicates:
        f.write(f"{rn} | {first} | {code} | {name[:100]}\n")

# ─── Report ───────────────────────────────────────────────────────────────
summary = [
    "=" * 70,
    "CRYSTAL PRODUCT MASTER — NORMALIZE REPORT",
    "=" * 70,
    f"Source:           {SRC.name}",
    f"Output:           {OUT.name}",
    f"Header columns:   {len(header)}",
    f"Data rows read:   {len(raw) - 1}",
    f"  → skipped:      {len(skipped)}  (blank Item Code)",
    f"  → duplicates:   {len(duplicates)}",
    f"  → written:      {len(clean_rows)}",
    "",
    "-- Sanity checks on written rows --",
]
cat_vals  = Counter(r[I_CAT]  for r in clean_rows)
manf_vals = Counter(r[I_MANF] for r in clean_rows)
tax_vals  = Counter(r[I_TAX]  for r in clean_rows)
zero_rate = sum(1 for r in clean_rows if float(r[I_RATE]) == 0)
zero_disc = sum(1 for r in clean_rows if float(r[I_DISC]) == 0)

summary.append(f"Category values ({len(cat_vals)}):")
for v, n in cat_vals.most_common(8):
    summary.append(f"    {(v or '<blank>'):20s} {n}")
summary.append(f"Manufacturer values ({len(manf_vals)}):")
for v, n in manf_vals.most_common(12):
    summary.append(f"    {(v or '<blank>'):20s} {n}")
summary.append(f"Tax % values: {dict(tax_vals.most_common(6))}")
summary.append(f"Rate == 0:    {zero_rate}")
summary.append(f"Discount ==0: {zero_disc}")
summary.append("=" * 70)

report_text = "\n".join(summary)
RPT.write_text(report_text, encoding="utf-8")
print()
print(report_text)
