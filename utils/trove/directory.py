import re
from io import BytesIO
from pathlib import Path

from models.trove.mod import TMod, ZMod


def get_mods_from_directory(path: Path):
    path = path.joinpath("mods")
    mods = []
    enabled = list(get_zip_mods(path)) + list(get_tmod_mods(path))
    disabled = list(get_disabled_zip_mods(path)) + list(get_disabled_tmod_mods(path))
    mods.extend(enabled)
    mods.extend(disabled)
    return mods, enabled, disabled


def get_zip_mods(path: Path) -> list[ZMod]:
    for file in path.glob("*.zip"):
        file_data = file.read_bytes()
        mod = ZMod.read_bytes(file, BytesIO(file_data))
        yield mod


def get_disabled_zip_mods(path: Path) -> list[ZMod]:
    for file in path.glob("*.zip.disabled"):
        file_data = file.read_bytes()
        mod = ZMod.read_bytes(file, BytesIO(file_data))
        mod.enabled = False
        yield mod


def get_tmod_mods(path: Path) -> list[TMod]:
    for file in path.glob("*.tmod"):
        file_data = file.read_bytes()
        mod = TMod.read_bytes(file, file_data)
        if mod.has_wrong_name:
            mod.fix_name()
        yield mod


def get_disabled_tmod_mods(path: Path) -> list[TMod]:
    for file in path.glob("*.tmod.disabled"):
        file_data = file.read_bytes()
        mod = TMod.read_bytes(file, file_data)
        if mod.has_wrong_name:
            mod.fix_name()
        mod.enabled = False
        yield mod


class Cfg:
    def __init__(self, data: dict):
        self.data = data

    @classmethod
    def from_file(cls, path: Path):
        return cls.from_string(path.read_text())

    @classmethod
    def from_string(cls, data: str):
        lines = data.split("\n")
        cfg = {}
        current = cfg
        for line in lines:
            if not line:
                continue
            separator = re.match(r"^\[(.*)]$", line)
            if separator:
                continue
            key, value = line.split("=")
            value = value.strip()
            if value == "":
                value = None
            elif value == "true":
                value = True
            elif value == "false":
                value = False
            current[key.strip()] = value
        return cls(data=cfg)

    @property
    def disabled_mods(self):
        disabled_mods = self.data.get("DisabledMods", "")
        return disabled_mods.split("|")

