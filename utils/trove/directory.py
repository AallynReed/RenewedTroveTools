import re
from pathlib import Path


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
    def last_version(self):
        return int(self.data.get("LastModVersion", 0)) or None

    @property
    def disabled_mods(self):
        disabled_mods = self.data.get("DisabledMods", "")
        return [
            re.findall("^Trove-(.*?)-(\w+)$", mod)[0]
            for mod in disabled_mods.split("|")
            if mod != ""
        ]
