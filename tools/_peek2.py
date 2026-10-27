import csv
from pathlib import Path

SRC = Path("data/Crystal/_source/Product_Master.clean.csv")
with SRC.open("r", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f))

hdr = [" ".join(h.split()) for h in rows[0]]
I_CODE, I_ITEM, I_PDESC = 1, 2, 29

print(f"cols -> {I_CODE}={hdr[I_CODE]!r}  "
      f"{I_ITEM}={hdr[I_ITEM]!r}  {I_PDESC}={hdr[I_PDESC]!r}\n")

seen = 0
for r in rows[1:]:
    if not r or not r[I_CODE].strip():
        continue
    seen += 1
    print(f"━━━ Row {seen}  code={r[I_CODE]!r} ━━━")
    print(f"  Item        : {r[I_ITEM]!r}")
    print(f"  Print Desc  : {r[I_PDESC]!r}")
    print()
    if seen >= 6:
        break

# Stats on Print Description
total = with_nl = with_size = empty = 0
for r in rows[1:]:
    if not r or not r[I_CODE].strip():
        continue
    total += 1
    pd = r[I_PDESC].strip()
    if not pd:
        empty += 1
    else:
        if "\n" in pd:
            with_nl += 1
        if "SIZE:" in pd.upper():
            with_size += 1

print(f"Print Description — total={total}  empty={empty}  "
      f"with_newline={with_nl}  with_SIZE={with_size}")
