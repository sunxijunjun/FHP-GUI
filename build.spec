# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_submodules

hidden_imports = collect_submodules('reportlab.graphics.barcode')

tkinterweb_datas, tkinterweb_binaries, tkinterweb_zips = collect_all('tkinterweb')

a = Analysis(
    ['D:\\GitHub\\FHP-GUI\\gui\\main.py'],  
    pathex=[],
    binaries=tkinterweb_binaries,  
    datas=[
        ('D:\\GitHub\\FHP-GUI\\gui\\data', 'data'),  
        *tkinterweb_datas,  
    ],
    hiddenimports=hidden_imports + ['tkinterweb'], 
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data,
           cipher=None)  # Add cipher if needed

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='main',  
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Collect step
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main' 
)