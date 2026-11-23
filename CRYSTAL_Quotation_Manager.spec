# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('assets', 'assets'),
    ('data', 'data'),    # SEED — copied to exe_dir/data on first launch
    ('ui', 'ui'),
    ('app', 'app'),
]
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