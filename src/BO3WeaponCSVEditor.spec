datas = [('assets/CSVEdit.ico', 'assets'),
         ('assets/dragdrop.png', 'assets'),
         ('assets/github.png', 'assets')]

excludes = [
    'numpy', 'test', 'unittest', 'pydoc', 'doctest', 'xmlrpc', 'lib2to3',
    'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.Qt3DInput',
    'PySide6.Qt3DLogic', 'PySide6.Qt3DAnimation', 'PySide6.Qt3DExtras',
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets',
    'PySide6.QtWebEngineQuick', 'PySide6.QtWebChannel', 'PySide6.QtWebSockets',
    'PySide6.QtQuick', 'PySide6.QtQuick3D', 'PySide6.QtQuickWidgets',
    'PySide6.QtQml', 'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
    'PySide6.QtCharts', 'PySide6.QtDataVisualization', 'PySide6.QtBluetooth',
    'PySide6.QtNfc', 'PySide6.QtPositioning', 'PySide6.QtLocation',
    'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtSql',
    'PySide6.QtDesigner', 'PySide6.QtHelp', 'PySide6.QtOpenGL',
    'PySide6.QtOpenGLWidgets', 'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
    'PySide6.QtRemoteObjects', 'PySide6.QtScxml', 'PySide6.QtSpatialAudio',
    'PySide6.QtTextToSpeech', 'PySide6.QtUiTools', 'PySide6.QtNetwork',
    'PySide6.QtTest', 'PySide6.QtConcurrent', 'PySide6.QtPrintSupport',
]

DROP = [
    'opengl32sw.dll',
    'qt6quick', 'qt6qml', 'qt6pdf', 'qt6virtualkeyboard', 'qt6network',
    'pyside6/translations/',
    'plugins/qmltooling/', 'plugins/platforminputcontexts/',
    'plugins/sqldrivers/', 'plugins/multimedia/', 'plugins/tls/',
    'plugins/networkinformation/', 'plugins/generic/', 'plugins/position/',
]


def prune(entries):
    kept = []
    for entry in entries:
        name = entry[0].replace('\\', '/').lower()
        if not any(drop in name for drop in DROP):
            kept.append(entry)
    return kept

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=1,
)
a.binaries = prune(a.binaries)
a.datas = prune(a.datas)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BO3WeaponCSVEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/CSVEdit.ico'],
)

COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='BO3WeaponCSVEditor',
)
