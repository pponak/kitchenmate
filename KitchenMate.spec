# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import copy_metadata

datas = [('app.py', '.')]
datas += collect_data_files('streamlit')
datas += copy_metadata('streamlit')


a = Analysis(
    ['window_practice.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'db_storage',
        # Streamlit 动态插入的页面导入，需要显式收集。
        'streamlit.runtime.scriptrunner.magic_funcs',
    ],
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
    name='KitchenMate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KitchenMate',
)
