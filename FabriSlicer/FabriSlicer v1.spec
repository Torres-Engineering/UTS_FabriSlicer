# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\MainMP600\\uni\\2026\\capstone\\data\\FabriSlicer\\src\\fabrigui.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\MainMP600\\uni\\2026\\capstone\\data\\FabriSlicer\\icon', 'icon'), ('D:\\MainMP600\\uni\\2026\\capstone\\data\\FabriSlicer\\..\\gcode_gen\\profiles\\default.uam', '.')],
    hiddenimports=[],
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
    name='FabriSlicer v1',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['D:\\MainMP600\\uni\\2026\\capstone\\data\\FabriSlicer\\icon\\slicer_icon.ico'],
)
