"""
Fix quotation_number_service to use get_data_dir().
"""

import shutil
import py_compile
from pathlib import Path


SVC = Path("app/services/quotation_number_service.py")
shutil.copy2(SVC, SVC.with_suffix(".py.QNUMBER_DIR_BACKUP"))
print(f"[backup] {SVC.name}")

s = SVC.read_text(encoding="utf-8")

# Show what we're working with
print("\n=== current _resolve_data_dir (quotation_number_service) ===")
idx = s.find("def _resolve_data_dir")
if idx >= 0:
    print(s[idx:idx + 800])
    print("=" * 60)
