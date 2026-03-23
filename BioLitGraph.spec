# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hiddenimports = (
    ['app', 'certifi']
    + collect_submodules('src')
    + collect_submodules('src.clients')
    + collect_submodules('waitress')
)

datas = (
    collect_data_files('certifi')
    + [
        ('templates', 'templates'),
        ('static', 'static'),
        ('data', 'data'),
        ('assets', 'assets'),
    ]
)

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
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
    name='BioLitGraph',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon='assets/icons/biolitgraph_icon.ico',
)
