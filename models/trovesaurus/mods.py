from datetime import datetime, UTC
from enum import Enum
from typing import Union, Optional

from pydantic import BaseModel, Field, validator


class ModFileType(Enum):
    TMOD = "tmod"
    ZIP = "zip"
    CONFIG = "config"


class ModFile(BaseModel):
    file_id: int = Field(alias="fileid")
    type: ModFileType = Field(alias="format")
    is_config: bool = Field(alias="extra", default=False)
    version: str
    changes: str
    created_at: Union[int, datetime] = Field(alias="date")
    downloads: int
    size: int = Field(alias="fileid")
    hash: str = Field(default="")

    @validator("created_at")
    def parse_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        return datetime.fromtimestamp(value, UTC)

    @validator("version")
    def parse_version(cls, value, values):
        if values["is_config"]:
            return "config"
        if not value.strip():
            return f"File: [{str(values['file_id'])}]"
        return value


class ModAuthor(BaseModel):
    ID: Optional[int]
    Username: Optional[str]
    Avatar: str
    Role: str

    @property
    def avatar_url(self):
        if self.Avatar.startswith("//"):
            return f"https:{self.Avatar}"
        return self.Avatar.replace("http:", "https:")


class Mod(BaseModel):
    id: int
    name: str
    type: str
    subtype: str
    description: str
    created_at: datetime = Field(alias="date")
    views: int
    replacements: str = Field(alias="replaces")
    downloads: int = Field(alias="totaldownloads")
    thumbnail_url: str = Field(alias="image")
    notes: str
    likes: int
    authors: list[ModAuthor]
    image_url: str = Field(alias="image_full")
    file_objs: list[ModFile] = Field(alias="downloads", default_factory=list)
    installed: bool = False
    installed_file: ModFile = None
    installed_version: str = None
    obsolete: int

    def __contains__(self, item):
        return item in self.hashes

    @property
    def hashes(self):
        return [file.hash for file in self.file_objs]

    @validator("created_at")
    def parse_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        return datetime.fromtimestamp(value, UTC)

    @property
    def url(self):
        return f"https://trovesaurus.com/mod={self.id}"

    @property
    def is_obsolete(self):
        return self.obsolete != 0
