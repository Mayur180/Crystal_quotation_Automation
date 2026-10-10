"""
Clean reset of CRYSTAL application data.

Keeps:
    - data/catalog.json (product catalog)
    - data/company_settings.json (company info)
    - data/custom_terms.json (terms)
    - data/products/ (product images if any)
    - data/backups/ (catalog backups)

Deletes:
    - data/quotations.json (all quotations)
    - data/quotation_history.jsonl (legacy)
    - data/customers.json
    - data/activity_log.jsonl
    - data/quotation_counter.json (resets to 0)
    - output/quotations/* (all generated DOCX/PDF)
    - output/backups/*
    - %APPDATA%/CrystalQuotation/setup.json (multi-user leftover)
    - %APPDATA%/CrystalQuotation/data/ (leftover)
"""

import json
import os
import shutil
from pathlib import Path


ROOT = Path.cwd()
DATA = ROOT / "data"
OUTPUT = ROOT / "output"
APPDATA_CRYSTAL = Path(os.environ.get("APPDATA", "")) / "CrystalQuotation"


def _print(msg):
    print(msg)


def preview():
    print("=" * 68)
    print("  CRYSTAL — Data Reset")
    print("=" * 68)
    print()
    print("WILL KEEP:")
    print("  ✓ data/catalog.json")
    print("  ✓ data/company_settings.json")
    print("  ✓ data/custom_terms.json")
    print("  ✓ data/products/")
    print("  ✓ data/backups/")
    print("  ✓ all code, assets, config")
    print()
    print("WILL RESET (content cleared, file kept or recreated):")
    for name in [
        "data/quotations.json",
        "data/quotation_history.jsonl",
        "data/customers.json",
        "data/activity_log.jsonl",
        "data/quotation_counter.json",
    ]:
        p = ROOT / name
        if p.is_file():
            size = p.stat().st_size
            print(f"  ✗ {name}  ({size} bytes → empty)")
    print()
    print("WILL DELETE (entire folder contents):")
    for name in ["output/quotations", "output/backups"]:
        p = ROOT / name
        if p.is_dir():
            count = len(list(p.iterdir()))
            print(f"  ✗ {name}/  ({count} items)")
    print()
    print("WILL DELETE (app data folder — leftover from multi-user):")
    for p in [APPDATA_CRYSTAL / "setup.json", APPDATA_CRYSTAL / "data"]:
        if p.exists():
            print(f"  ✗ {p}")
    print()


def do_reset():
    # 1. Backup the current data folder first
    backup = ROOT / f"data_RESET_BACKUP_{__import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copytree(DATA, backup)
    print(f"[backup] data -> {backup.name}")

    # 2. Reset data files
    resets = {
        DATA / "quotations.json":        [],
        DATA / "customers.json":         [],
        DATA / "quotation_counter.json": {"financial_year": "26-27", "last_number": 0},
    }
    for path, empty_content in resets.items():
        path.write_text(json.dumps(empty_content, indent=2), encoding="utf-8")
        print(f"[reset] {path.relative_to(ROOT)}")

    # Empty the JSONL files (just clear them)
    for name in ["quotation_history.jsonl", "activity_log.jsonl"]:
        p = DATA / name
        p.write_text("", encoding="utf-8")
        print(f"[reset] {p.relative_to(ROOT)} (emptied)")

    # 3. Clear output folders (keep the folders themselves)
    for folder in [OUTPUT / "quotations", OUTPUT / "backups"]:
        if folder.is_dir():
            for item in folder.iterdir():
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink()
            print(f"[clear] {folder.relative_to(ROOT)}/")

    # 4. Delete multi-user leftovers
    for p in [APPDATA_CRYSTAL / "setup.json", APPDATA_CRYSTAL / "data"]:
        if p.exists():
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink()
            print(f"[removed] {p}")

    print()
    print("[done] Data reset complete.")
    print()
    print("Next:")
    print("  1. python main.py       (verify app opens with 0 records)")
    print("  2. Rebuild the EXE if needed")


if __name__ == "__main__":
    preview()
    answer = input("Proceed with reset? Type 'yes' to confirm: ").strip().lower()
    if answer != "yes":
        print("Cancelled.")
    else:
        print()
        do_reset()
