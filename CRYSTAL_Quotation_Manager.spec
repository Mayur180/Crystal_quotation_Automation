# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

# Seed data bundled into the EXE. On first launch these files are copied
# to <exe_dir>/data; existing files are never overwritten.
# Deliberately excluded: backups/, _source/, activity logs, sessions —
# runtime state that should not travel inside the binary.
SEED_DATA = [
    ('data/Users.json', 'data'),
    ('data/User_Access.json', 'data'),
    ('data/offer_counter.json', 'data'),
    ('data/VMM', 'data/VMM'),
    ('data/Crystal/catalog.json', 'data/Crystal'),
    ('data/Crystal/customers.json', 'data/Crystal'),
    ('data/Crystal/quotations.json', 'data/Crystal'),
    ('data/Crystal/deleted_quotations.json', 'data/Crystal'),
    ('data/Crystal/quotation_counter.json', 'data/Crystal'),
    ('data/Crystal/company_settings.json', 'data/Crystal'),
    ('data/Crystal/custom_terms.json', 'data/Crystal'),
    ('data/Crystal/leads.json', 'data/Crystal'),
]

datas = [
    ('assets', 'assets'),
    ('ui', 'ui'),
    ('app', 'app'),
] + SEED_DATA
binaries = []

hiddenimports = [
    'bcrypt', 'requests', 'docx', 'docx2pdf', 'pymupdf',
    'PIL', 'PIL.Image', 'PIL.ImageTk',
    'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog',
    'json', 'threading', 'datetime', 'decimal', 'pathlib',
    'win32com', 'win32com.client', 'pythoncom', 'pywintypes',
]

for pkg in ('docx', 'pymupdf', 'docx2pdf', 'certifi'):
    tmp_ret = collect_all(pkg)
    datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CRYSTAL_Quotation_Manager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,            # was True — corrupts onnxruntime/pymupdf/pywin32 DLLs
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/logo/LOGO.ico'],
)
