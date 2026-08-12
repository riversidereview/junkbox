# -*- mode: python ; coding: utf-8 -*-

exclude_patterns = [
    'opencv_videoio_ffmpeg',
    'opengl32sw',
    'Qt6Quick',
    'Qt6Qml',
    'Qt6Pdf',
    'Qt6OpenGL',
    'Qt6Network',
    'Qt6Svg',
    'Qt6VirtualKeyboard',
    'Qt6ShaderTools',
    'tcl',
    'tk',
    'PIL',
    '_avif',
    'sqlite3',
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('app.ico', '.')],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'keyboard',
        'mss',
        'pygetwindow',
        'cv2',
        'numpy',
        'pyautogui',
        'urllib',
        'urllib.parse',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        '_tkinter',
        'unittest',
        'pydoc',
        'PySide6.QtNetwork',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtPdf',
        'PySide6.Qt3D',
        'PySide6.QtSql',
        'PySide6.QtTest',
        'PySide6.QtXml',
        'PySide6.QtSvg',
        'PySide6.QtOpenGL',
        'PySide6.QtMultimedia',
        'PIL',
        'matplotlib',
        'scipy',
        'sqlite3',
    ],
    noarchive=False,
    optimize=1,
)

# 过滤真正不需要的大型非核心 DLL
filtered_binaries = []
for b in a.binaries:
    name, path, type_ = b[0], b[1], b[2]
    should_skip = False
    for pat in exclude_patterns:
        if pat.lower() in name.lower() or pat.lower() in path.lower():
            should_skip = True
            break
    if not should_skip:
        filtered_binaries.append(b)

a.binaries = filtered_binaries

pyz = PYZ(a.pure, optimize=1)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='D2R_Gem_Crafter',
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
    icon=['app.ico'],
)
