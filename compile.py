import subprocess
from pathlib import Path

from cx_Freeze import setup, Executable

from models.metadata import Metadata

metadata = Metadata.load_from_file(Path("data/metadata.json"))

executables = [
    r"venv\Lib\site-packages\flet\bin\flet\flet.exe",
    r"venv\Lib\site-packages\flet\bin\fletd.exe",
]

editor = r".\resedit.exe"

instructions = [
    ("--set-version-string", "CompanyName", "Sly"),
    ("--set-version-string", "FileDescription", metadata.name),
    ("--set-version-string", "ProductName", metadata.name),
    ("--set-version-string", "OriginalFilename", f"{metadata.tech_name}-{metadata.version}.exe"),
    ("--set-version-string", "LegalCopyright", metadata.copyright),
    ("--set-version-string", "CompanyName", "Sly"),
    ("--set-version-string", "InternalName", metadata.tech_name),
    ("--set-file-version", metadata.version, ""),
    ("--set-product-version", metadata.version, ""),
    ("--set-icon", "assets/x256.ico", ""),
]

for executable in executables:
    for option, key, value in instructions:
        command = [
            editor,
            executable,
            option,
            f"\"{key}\"",
        ]
        if value:
            command.append(f"\"{value}\"")
        subprocess.run(" ".join(command))

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
            base="Win32GUI",
            copyright=f"{metadata.author} {metadata.copyright}",
            shortcut_name=metadata.name,
            shortcut_dir="DesktopFolder",
        )
    ],
)
