import shutil
import py_compile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SERVICES = ROOT / "app" / "services"


def backup(p):
    b = p.with_suffix(p.suffix + ".AUDITFIX_BACKUP")
    if not b.exists():
        shutil.copy2(p, b)
        print(f"[backup] {p.name}")


# ============================================================
# 1. Fix company_settings_service.py — add PROJECT_ROOT assignment
# ============================================================

f = SERVICES / "company_settings_service.py"
backup(f)
s = f.read_text(encoding="utf-8")

old = '''from app.services.paths import get_data_dir, get_project_root
DATA_DIR = get_data_dir()
SETTINGS_FILE = DATA_DIR / "company_settings.json"
LOGO_DIR = PROJECT_ROOT / "assets" / "logo"'''

new = '''from app.services.paths import get_data_dir, get_project_root
DATA_DIR = get_data_dir()
PROJECT_ROOT = get_project_root()
SETTINGS_FILE = DATA_DIR / "company_settings.json"
LOGO_DIR = PROJECT_ROOT / "assets" / "logo"'''

if old in s:
    s = s.replace(old, new, 1)
    f.write_text(s, encoding="utf-8")
    print("[ok] company_settings_service.py: PROJECT_ROOT defined")
else:
    print("[warn] company_settings_service.py: pattern not found")


# ============================================================
# 2. Fix backup_service.py — use get_data_dir() / get_output_dir()
# ============================================================

f = SERVICES / "backup_service.py"
backup(f)
s = f.read_text(encoding="utf-8")

old = '''PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"'''

new = '''from app.services.paths import get_data_dir, get_output_dir, get_project_root
PROJECT_ROOT = get_project_root()
DATA_DIR = get_data_dir()
OUTPUT_DIR = get_output_dir()'''

if old in s:
    s = s.replace(old, new, 1)
    f.write_text(s, encoding="utf-8")
    print("[ok] backup_service.py: uses paths helpers")
else:
    print("[warn] backup_service.py: pattern not found")


# ============================================================
# 3. Fix export_service.py — same pattern
# ============================================================

f = SERVICES / "export_service.py"
backup(f)
s = f.read_text(encoding="utf-8")

old = '''PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"'''

new = '''from app.services.paths import get_data_dir, get_output_dir, get_project_root
PROJECT_ROOT = get_project_root()
DATA_DIR = get_data_dir()
OUTPUT_DIR = get_output_dir()'''

if old in s:
    s = s.replace(old, new, 1)
    f.write_text(s, encoding="utf-8")
    print("[ok] export_service.py: uses paths helpers")
else:
    print("[warn] export_service.py: pattern not found")


# ============================================================
# 4. Fix catalog_service.py — check line 17 pattern
# ============================================================

f = SERVICES / "catalog_service.py"
backup(f)
s = f.read_text(encoding="utf-8")

old = 'PROJECT_ROOT = Path(__file__).resolve().parents[2]'
new = 'from app.services.paths import get_project_root\nPROJECT_ROOT = get_project_root()'

if 'from app.services.paths import get_project_root' not in s and old in s:
    s = s.replace(old, new, 1)
    f.write_text(s, encoding="utf-8")
    print("[ok] catalog_service.py: uses get_project_root()")
else:
    print("[skip] catalog_service.py")


# ============================================================
# 5. Update audit.py to use correct function names
# ============================================================

f = ROOT / "audit.py"
if f.is_file():
    s = f.read_text(encoding="utf-8")

    s = s.replace(
        "from app.services.quotation_number_service import get_next_number",
        "from app.services.quotation_number_service import get_next_quotation_number",
    )
    s = s.replace(
        "n = get_next_number()",
        "n = get_next_quotation_number()",
    )
    s = s.replace(
        "from app.services.customer_service import get_customers",
        "from app.services.customer_service import list_customers",
    )
    s = s.replace(
        "cs = get_customers()",
        "cs = list_customers()",
    )
    f.write_text(s, encoding="utf-8")
    print("[ok] audit.py: function names corrected")


# ============================================================
# 6. Compile check
# ============================================================

print()
print("=" * 60)
print("Compile check")
print("=" * 60)

failed = False
for f in SERVICES.glob("*.py"):
    try:
        py_compile.compile(str(f), doraise=True)
    except py_compile.PyCompileError as e:
        print(f"[FAIL] {f.name}: {e}")
        failed = True

if failed:
    print()
    print("Some services failed to compile — restore backups if needed.")
else:
    print("[ok] all services compile")
    print()
    print("Now run:")
    print("  python audit.py")
