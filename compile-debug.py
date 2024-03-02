import subprocess
from pathlib import Path

from cx_Freeze import setup, Executable

from models.metadata import Metadata

flet_exe = Path(
    r"C:\hostedtoolcache\windows\Python\3.11.8\x64\Lib\site-packages\flet\bin\flet\flet.exe"
)

subprocess.run(
    r'.\resedit.exe --update-resource-ico "{0}" IDI_ICON1 "assets/favicon.ico"'.format(
        flet_exe
    )
)

metadata = Metadata.load_from_file(Path("data/metadata.json"))

build_exe_options = {
    "excludes": [
        "wheel",
        "cx_Freeze",
    ],
    "include_files": [
        ("assets/", "assets/"),
        ("locales/", "locales/"),
        ("data/", "data/"),
        ("README.md", "README.md"),
        ("LICENSE", "LICENSE"),
    ],
    "optimize": 2,
    "include_msvcr": True,
}

bdist_msi_options = {
    "target_name": metadata.tech_name,
    "upgrade_code": metadata.app_id,
    "add_to_path": False,
    "install_icon": str(metadata.icon),
    "all_users": True,
}

options = {"build_exe": build_exe_options, "bdist_msi": bdist_msi_options}

setup(
    name=metadata.name,
    version=metadata.version,
    author=metadata.author,
    url=f"https://github.com/Sly0511/{metadata.tech_name}",
    description=metadata.description,
    options=options,
    executables=[
        Executable(
            "app.py",
            target_name=f"{metadata.tech_name}.exe",
            icon=str(metadata.icon),
            base=None,
            copyright=f"{metadata.author} {metadata.copyright}",
            shortcut_name=metadata.name,
            shortcut_dir="DesktopFolder",
        )
    ],
)
