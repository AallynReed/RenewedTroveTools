import winreg
from pathlib import Path


Hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
Nodes = ["WOW6432Node\\"]
TrovePath = "Microsoft\\Windows\\CurrentVersion\\Uninstall\\"
TroveKey = "Glyph Trove"
TroveInstallValue = "InstallLocation"


def SanityCheck(Path):
    ModsFolder = Path.joinpath("mods")
    if not ModsFolder.exists():
        return False
    return True


def GetKeys(key, path, look_for):
    i = 0
    while True:
        try:
            subkey = winreg.EnumKey(key, i)
            if subkey.startswith(look_for):
                yield path + subkey + "\\"
        except WindowsError:
            break
        i += 1


def SearchGlyphRegistry():
    for Hive in Hives:
        for Node in Nodes:
            try:
                LookPath = "SOFTWARE\\" + Node + TrovePath
                RegistryKeyPath = winreg.OpenKeyEx(Hive, LookPath)
                Keys = GetKeys(RegistryKeyPath, LookPath, TroveKey)
                for Key in Keys:
                    yield winreg.OpenKeyEx(Hive, Key)
            except WindowsError:
                ...


def GetTroveLocations():
    for Key in SearchGlyphRegistry():
        try:
            GamePath = winreg.QueryValueEx(Key, TroveInstallValue)[
                0]  # Extracts path out of value in Glyph keys
        except WindowsError:
            continue
        if SanityCheck(Path(GamePath)):
            yield [Path(GamePath).name.lower(), Path(GamePath)]