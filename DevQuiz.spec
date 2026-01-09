# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

ROOT = Path.cwd().resolve()

datas = [
    (str(ROOT / "assets"), "assets"),
]

env_file = ROOT / ".env"
if env_file.exists():
    datas.append((str(env_file), "_internal"))

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DevQuiz",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="DevQuiz",
)


