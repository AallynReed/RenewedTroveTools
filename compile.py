import subprocess
import sys
from pathlib import Path

from cx_Freeze import setup, Executable

from models.metadata import Metadata

metadata = Metadata.load_from_file(Path("data/metadata.json"))

python_path = Path(sys.executable).parent.parent
flet_path = python_path.joinpath("Lib", "site-packages", "flet")

if not flet_path.exists():
    print(f"Could not find flet at {flet_path}")
    flet_path = python_path.joinpath("x64", "Lib", "site-packages", "flet")
    if not flet_path.exists():
        print(f"Could not find flet at {flet_path}")
        quit()

editor = r".\resedit.exe"

instructions = [
    ("--set-version-string", "CompanyName", "Sly"),
    ("--set-version-string", "FileDescription", metadata.name),
    ("--set-version-string", "ProductName", metadata.name),
    (
        "--set-version-string",
        "OriginalFilename",
        f"{metadata.tech_name}-{metadata.version}.exe",
    ),
    ("--set-version-string", "LegalCopyright", metadata.copyright),
    ("--set-version-string", "CompanyName", "Sly"),
    ("--set-version-string", "InternalName", metadata.tech_name),
    ("--set-file-version", metadata.version, ""),
    ("--set-product-version", metadata.version, ""),
    ("--set-icon", "assets/x256.ico", ""),
]

for executable in flet_path.rglob("*.exe"):
    for option, key, value in instructions:
        command = [
            editor,
            str(executable),
            option,
            f'"{key}"',
        ]
        if value:
            command.append(f'"{value}"')
        subprocess.run(" ".join(command))
    print(f"Updated {executable} resources.")

build_exe_options = {
    "excludes": [
        "wheel",
        "cx_Freeze",
    ],
    "include_files": [
        ("assets/", "assets/"),
        ("locales/", "locales/"),
        ("data/", "data/"),
        ("update.bat", "update.bat"),
        ("README.md", "README.md"),
        ("LICENSE", "LICENSE"),
        ("trove.dll", "trove.dll"),
    ],
    "optimize": 2,
    "include_msvcr": True,
}

bdist_msi_options = {
    "initial_target_dir": f"[ProgramFiles64Folder]{metadata.tech_name}",
    "target_name": metadata.tech_name,
    "upgrade_code": metadata.app_id,
    "add_to_path": True,
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
    license="MIT",
    license_file="LICENSE",
    keywords="trove,glyph,mods,calculators,utilities,flutter,python",
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
