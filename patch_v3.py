from pathlib import Path
import shutil

# ---- 1. Dashboard footer + title ----
p = Path("ui/dashboard.py")
shutil.copy2(p, p.with_suffix(".py.V3_BACKUP"))
s = p.read_text(encoding="utf-8")

# Title
old_title = 'self.title("CRYSTAL | ARMATECH ASSOCIATES — Quotation Manager")'
new_title = 'self.title("CRYSTAL | ARMATECH ASSOCIATES — Quotation Manager  v3.0")'
if old_title in s:
    s = s.replace(old_title, new_title, 1)
    print("[ok] dashboard title -> v3.0")
else:
    print("[warn] title not found")

# Footer
old_footer = 'text="CRYSTAL / ARMATECH ASSOCIATES  ·  Quotation Manager  ·  v1.0"'
new_footer = 'text="CRYSTAL / ARMATECH ASSOCIATES  ·  Quotation Manager  ·  v3.0"'
if old_footer in s:
    s = s.replace(old_footer, new_footer, 1)
    print("[ok] dashboard footer -> v3.0")
else:
    print("[warn] footer not found")

p.write_text(s, encoding="utf-8")

# ---- 2. app/config.py: add APP_VERSION ----
cfg = Path("app/config.py")
shutil.copy2(cfg, cfg.with_suffix(".py.V3_BACKUP"))
cs = cfg.read_text(encoding="utf-8")

if "APP_VERSION" not in cs:
    cs = 'APP_VERSION = "3.0"\n\n' + cs
    cfg.write_text(cs, encoding="utf-8")
    print("[ok] APP_VERSION added to app/config.py")
else:
    print("[skip] APP_VERSION already exists")

print()
print("Verify:")
print(f"  title:  {new_title[:80]}")
print(f"  footer: {new_footer[:80]}")
print(f"  config: APP_VERSION = '3.0' added")
