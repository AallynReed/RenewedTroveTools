import os
from pathlib import Path
from typing import Optional
import vdf


if os.name == "nt":
    import winreg

    Hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
    Nodes = ["WOW6432Node\\"]
    TrovePath = "Microsoft\\Windows\\CurrentVersion\\Uninstall\\"
    TroveKey = "Glyph Trove"
    TroveInstallValue = "InstallLocation"
    SteamPath = "Valve\\"
    SteamKey = "Steam"
    SteamInstallValue = "InstallPath"
    SteamTroveID = "304050"


class TroveGamePath:
    def __init__(self, path: Path, steam: Optional[Path] = None, name: str = None):
        self.path = path
        self.steam = steam
        self._clean_name = None
        self.clean_name = name or self.path.name
        self._is_custom = bool(name)

    def __str__(self):
        return str(self.path)

    def __bool__(self):
        return self.is_valid

    def __repr__(self):
        return f"TroveGamePath({self.path!r}, steam={self.steam})"

    def __eq__(self, other):
        return self.path == other.path

    @property
    def clean_name(self):
        return self._clean_name

    @clean_name.setter
    def clean_name(self, value):
        self._clean_name = value

    @property
    def name(self):
        platform_name = "Steam" if self.is_steam else "Glyph"
        return f"({platform_name}) {self.clean_name}"

    @property
    def is_glyph(self):
        return not self.is_custom and self.steam is None

    @property
    def is_steam(self):
        return not self.is_custom and self.steam is not None

    @property
    def is_custom(self):
        return self._is_custom

    @property
    def icon(self):
        if self.is_glyph:
            return "assets/icons/brands/glyph.png"
        if self.is_steam:
            return "assets/icons/brands/steam.png"
        return "assets/icons/brands/trove.png"

    @property
    def executable(self):
        return self.path.joinpath("Trove.exe")

    @property
    def is_valid(self):
        return self.path.exists() and self.executable.exists()

    @property
    def mods_path(self):
        if not self.is_custom:
            mods_path = self.path.joinpath("mods")
            mods_path.mkdir(exist_ok=True, parents=True)
            return mods_path
        return self.path

    @property
    def workshop_path(self):
        if self.is_steam:
            workshop_path = self.steam.joinpath("steamapps\\workshop\\content\\304050")
            if workshop_path.exists():
                return workshop_path
        return None

    @staticmethod
    def get_from_dir(path: Path, pattern: str, recursive: bool = False):
        tree = path.rglob(pattern) if recursive else path.glob(pattern)
        for mod in tree:
            if mod.is_file():
                yield mod

    @property
    def enabled_tmods(self):
        mods = []
        for mod in self.get_from_dir(self.mods_path, "*.tmod"):
            mods.append(mod)
        if self.workshop_path:
            for mod in self.get_from_dir(self.workshop_path, "*.tmod", True):
                mods.append(mod)
        return mods

    @property
    def disabled_tmods(self):
        mods = []
        for mod in self.get_from_dir(self.mods_path, "*.tmod.disabled"):
            mods.append(mod)
        if self.workshop_path:
            for mod in self.get_from_dir(self.workshop_path, "*.tmod.disabled", True):
                mods.append(mod)
        return mods

    @property
    def enabled_zips(self):
        mods = []
        for mod in self.get_from_dir(self.mods_path, "*.zip"):
            mods.append(mod)
        if self.workshop_path:
            for mod in self.get_from_dir(self.workshop_path, "*.zip", True):
                mods.append(mod)
        return mods

    @property
    def disabled_zips(self):
        mods = []
        for mod in self.get_from_dir(self.mods_path, "*.zip.disabled"):
            mods.append(mod)
        if self.workshop_path:
            for mod in self.get_from_dir(self.workshop_path, "*.zip.disabled", True):
                mods.append(mod)
        return mods


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


def search_steam_registry():
    for hive in Hives:
        for node in Nodes:
            try:
                look_path = "SOFTWARE\\" + node + SteamPath
                registry_key_path = winreg.OpenKeyEx(hive, look_path)
                keys = get_keys(registry_key_path, look_path, SteamKey)
                for Key in keys:
                    yield winreg.OpenKeyEx(hive, Key)
            except WindowsError:
                ...


def get_trove_locations():
    if os.name != "nt":
        return []
    for Key in search_glyph_registry():
        try:
            game_path = Path(winreg.QueryValueEx(Key, TroveInstallValue)[0])
        except WindowsError:
            continue
        game = TroveGamePath(game_path)
        if game.is_valid:
            yield game
    for Key in search_steam_registry():
        try:
            steam_path = Path(winreg.QueryValueEx(Key, SteamInstallValue)[0])
            steam_libraries_path = steam_path.joinpath("steamapps\\libraryfolders.vdf")
            steam_libraries = vdf.load(steam_libraries_path.open("r", encoding="utf-8"))
            for library in steam_libraries["libraryfolders"].values():
                if SteamTroveID in library["apps"].keys():
                    library_path = Path(library["path"])
                    TrovePath = library_path.joinpath(
                        "steamapps\\common\\Trove\\Games\\Trove"
                    )
                    for game_path in TrovePath.iterdir():
                        if game_path.is_dir():
                            game = TroveGamePath(game_path, library_path)
                            if game.is_valid:
                                yield game
        except WindowsError:
            continue
