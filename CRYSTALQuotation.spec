# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('assets', 'assets'), ('data', 'data')]
binaries = []
hiddenimports = ['fpdf', 'docx', 'docx2pdf', 'win32com', 'win32com.client', 'pythoncom', 'pywintypes']
tmp_ret = collect_all('fpdf')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('docx')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=['.'],
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
    [],
    exclude_binaries=True,
    name='CRYSTALQuotation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/logo/LOGO.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CRYSTALQuotation',
)


# CRYSTAL: copy data next to exe
# Runs after PyInstaller finishes so dist/CRYSTALQuotation/data/ exists
# on first launch (seed_data_on_first_run only fills missing files).
import shutil, os as _os
_project_root_dir = _os.path.dirname(_os.path.abspath(SPEC))
for _folder in ("data", "assets"):
    _src_dir = _os.path.join(_project_root_dir, _folder)
    _dst_dir = _os.path.join(DISTPATH, "CRYSTALQuotation", _folder)
    if not _os.path.isdir(_src_dir):
        continue
    _os.makedirs(_dst_dir, exist_ok=True)
    for _root, _dirs, _files in _os.walk(_src_dir):
        for _f in _files:
            _src = _os.path.join(_root, _f)
            _rel = _os.path.relpath(_src, _src_dir)
            _dst = _os.path.join(_dst_dir, _rel)
            _os.makedirs(_os.path.dirname(_dst), exist_ok=True)
            if not _os.path.exists(_dst):
                shutil.copy2(_src, _dst)
