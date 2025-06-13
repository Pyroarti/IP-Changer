from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT, MERGE
from pathlib import Path
import glob


spec_hooks = []
hidden_imports = []


app_name = "RB IP changer"
main_script = "src\main_gui.py"
icon_file = "UI\icon.ico"

log_files = [(f, ".") for f in glob.glob("logs/*")]
data_files = [(f, ".") for f in glob.glob("data/*")]


data_files = [
    ("UI/About_pic.jpg", "UI/"),
    ("logs", "logs/"),
    ("data", "data/"),
    (r"C:\Programmering\Programmering\Github\IP-Changer\.env\Lib\site-packages\customtkinter", "customtkinter/")
] + log_files + data_files





a = Analysis(
    [main_script],
    pathex=[str(Path(SPEC).parent.resolve())],
    binaries=[],
    datas=data_files,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    hiddenimports=hidden_imports,
    cipher=None,
    noarchive=False
)


pyz = PYZ(a.pure, a.zipped_data)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name="output_folder",
)

