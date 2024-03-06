import os
from pathlib import Path

if os.name == "nt":
    import winreg

    Hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
    Nodes = ["WOW6432Node\\"]
    TrovePath = "Microsoft\\Windows\\CurrentVersion\\Uninstall\\"
    TroveKey = "Glyph Trove"
    TroveInstallValue = "InstallLocation"


def sanity_check(path):
    trove_executable = path.joinpath("Trove.exe")
    if not trove_executable.exists():
        return False
    return True


def get_keys(key, path, look_for):
    i = 0
    while True:
        try:
            subkey = winreg.EnumKey(key, i)
            if subkey.startswith(look_for):
                yield path + subkey + "\\"
        except WindowsError:
            break
        i += 1


def search_glyph_registry():
    for hive in Hives:
        for node in Nodes:
            try:
                look_path = "SOFTWARE\\" + node + TrovePath
                registry_key_path = winreg.OpenKeyEx(hive, look_path)
                keys = get_keys(registry_key_path, look_path, TroveKey)
                for Key in keys:
                    yield winreg.OpenKeyEx(hive, Key)
            except WindowsError:
                ...


def get_trove_locations():
    if os.name != "nt":
        return []
    for Key in search_glyph_registry():
        try:
            game_path = winreg.QueryValueEx(Key, TroveInstallValue)[0]
        except WindowsError:
            continue
        if sanity_check(Path(game_path)):
            yield Path(game_path)
