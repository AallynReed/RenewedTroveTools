import yaml
from typing import Optional
from pathlib import Path
import re


class ModYaml:
    title: Optional[str]
    authors_string: Optional[str]
    description: Optional[str]
    preview: tuple[Optional[Path], Optional[str]]
    config: tuple[Optional[Path], Optional[str]]
    mod_files: list[tuple[Path, str]]
    type: Optional[str]
    sub_type: Optional[str]

    def __init__(self):
        self.title = None
        self.authors_string = None
        self.description = None
        self.preview = (None, None)
        self.config = (None, None)
        self.mod_files = []
        self.type = None
        self.sub_type = None

    def sanity_check(self):
        if self.title is None:
            return False
        if len(self.authors) == 0:
            return False
        if self.description is None:
            return False
        if not self.preview[0].exists():
            return False
        if not self.config[0].exists():
            return False
        for f in self.mod_files:
            if not f[0].exists():
                return False
        return True

    @staticmethod
    def validate_title(title):
        return bool(re.match(r"^[\w,\s\-()\[\]]+$", title))

    @property
    def authors(self):
        return self.authors_string.split(",") if self.authors_string else []

    @authors.setter
    def authors(self, authors):
        self.authors_string = authors

    def add_file(self, override, true_override):
        ovr = (override, true_override)
        if ovr not in self.mod_files:
            self.mod_files.append(ovr)

    def remove_file(self, override):
        self.mod_files = [f for f in self.mod_files if f[0] != override]

    def get_file(self, override):
        for f in self.mod_files:
            if f[0] == override:
                return f
        return None

    def to_dict(self):
        return {
            "title": self.title,
            "authors": self.authors,
            "description": self.description,
            "preview": (str(self.preview[0]), self.preview[1]),
            "config": (str(self.config[0]), self.config[1]),
            "mod_files": [(str(f[0]), f[1]) for f in self.mod_files],
        }

    @classmethod
    def from_dict(cls, data):
        mod_yaml = cls()
        mod_yaml.title = data.get("title")
        mod_yaml.authors_string = ", ".join(data.get("authors", []))
        mod_yaml.description = data.get("description")
        preview = data.get("preview", (None, None))
        mod_yaml.preview = (
            (Path(preview[0]), preview[1]) if preview != (None, None) else (None, None)
        )
        config = data.get("config", (None, None))
        mod_yaml.config = (
            (Path(config[0]), config[1]) if config != (None, None) else (None, None)
        )
        mod_yaml.mod_files = [(Path(f[0]), f[1]) for f in data.get("mod_files", [])]
        return mod_yaml

    @classmethod
    def from_yaml(cls, path):
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            cls.from_dict(data)

    def to_yaml(self, path):
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f)
