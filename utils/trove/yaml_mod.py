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
    version: Optional[str]
    changes: Optional[str]

    def __init__(self):
        self.title = None
        self.authors_string = None
        self.description = None
        self.preview = (None, None)
        self.config = (None, None)
        self.mod_files = []
        self.type = None
        self.sub_type = None
        self._version = None
        self._changes = None

    def sanity_check(self):
        if self.title is None:
            raise ValueError("Title is required")
        if len(self.authors) == 0:
            raise ValueError("Authors are required")
        if self.description is None:
            raise ValueError("Description is required")
        if self.preview[0] is not None and not self.preview[0].exists():
            raise FileNotFoundError(self.preview[0])
        if self.config[0] is not None and not self.config[0].exists():
            raise FileNotFoundError(self.config[0])
        for f in self.mod_files:
            if not f[0].exists():
                self.remove_file(f[0])
                raise FileNotFoundError(f[0])
        for f in self.mod_files:
            if f[0] == self.preview[0]:
                raise ValueError("Preview file cannot be a mod file")
            if f[0] == self.config[0]:
                raise ValueError("Config file cannot be a mod file")
        return True

    @staticmethod
    def validate_title(title):
        return bool(re.match(r"^[\w',\s\-()\[\]]+$", title))

    @property
    def authors(self):
        return self.authors_string.split(",") if self.authors_string else []

    @authors.setter
    def authors(self, authors):
        self.authors_string = authors

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, version):
        self._version = version

    @property
    def changes(self):
        return self._changes

    @changes.setter
    def changes(self, changes):
        self._changes = changes

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
            "version": self.version,
            "changes": self.changes,
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
        mod_yaml.version = data.get("version")
        mod_yaml.changes = data.get("changes")
        return mod_yaml

    @classmethod
    def from_yaml(cls, path):
        with open(path, "r") as f:
            data = yaml.safe_load(f)
            cls.from_dict(data)

    def to_yaml(self, path):
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f)
