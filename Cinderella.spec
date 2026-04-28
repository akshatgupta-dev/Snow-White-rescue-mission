# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_ui.py'],
    pathex=[],
    binaries=[],
    datas=[('src\\assets\\lightsaber_cursor.xbm', 'src\\assets'), ('src\\assets\\lightsaber_cursor_mask.xbm', 'src\\assets'), ('src\\assets\\cinderella_cursor.xbm', 'src\\assets'), ('src\\assets\\cinderella_cursor_mask.xbm', 'src\\assets'), ('src\\assets\\pumpkin_cursor.xbm', 'src\\assets'), ('src\\assets\\pumpkin_cursor_mask.xbm', 'src\\assets'), ('src\\assets\\wand_cursor.xbm', 'src\\assets'), ('src\\assets\\wand_cursor_mask.xbm', 'src\\assets'), ('src\\assets\\Vietnamese_Jedi_with_Red_Lightsaber.mp4', 'src\\assets'), ('src\\assets\\image.png', 'src\\assets')],
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
    name='Cinderella',
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
)
