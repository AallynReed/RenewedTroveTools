from json import load
from pathlib import Path

from pydantic import BaseModel


class Metadata(BaseModel):
    dev: bool
    author: str
    name: str
    tech_name: str
    short_name: str
    version: str
    description: str
    icon: Path
    copyright: str
    app_id: str

    @classmethod
    def load_from_file(cls, path: Path):
        return cls.parse_obj(load(open(path)))

    @property
    def app_name(self):
        return f"{self.name} - v{self.version}"
