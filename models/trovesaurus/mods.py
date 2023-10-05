import re
from datetime import datetime
from enum import Enum
from re import compile
from typing import Union, Any

from pydantic import BaseModel, Field, validator

paragraph = compile(r"<p>(.*?)<\/p>")
strong = compile(r"<strong>(.*?)<\/strong>")
img = compile(r"<img.*?>")
anchor = compile(r"<a.*?>(.*?)<\/a>")
ul = compile(r"<ul>(.*?)<\/ul>", re.MULTILINE | re.DOTALL)
li = compile(r"<li>(.*?)</li>")
br = compile(r"<br.*?>")


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

    @validator('created_at')
    def parse_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        return datetime.utcfromtimestamp(value)

    @validator('version')
    def parse_version(cls, value, values):
        if values["is_config"]:
            return "config"
        if not value.strip():
            return f"File: [{str(values['file_id'])}]"
        return value

    @property
    def clean_changes(self):
        desc = paragraph.sub(r"\1", self.changes)
        desc = strong.sub(r"\1", desc)
        desc = img.sub(r"", desc)
        desc = anchor.sub(r"\1", desc)
        desc = ul.sub(r"", desc)
        desc = br.sub(r"", desc)
        desc = li.sub("\t\u2022 \\1", desc)
        return (
            desc.replace("&nbsp;", "").replace("&gt;", ">").replace("&lt;", "<").strip()
            or None
        )


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
    user_id: int = Field(alias="userid")
    notes: str
    visible: bool
    likes: int = Field(alias="votes")
    author: str
    image_url: str = Field(alias="image_full")
    file_objs: list[ModFile] = Field(alias="downloads", default_factory=list)

    @validator('created_at')
    def parse_timestamp(cls, value):
        if isinstance(value, datetime):
            return value
        return datetime.utcfromtimestamp(value)

    @validator('visible')
    def parse_visible(cls, value):
        return bool(int(value))

    @property
    def clean_description(self):
        desc = paragraph.sub(r"\1", self.description)
        desc = strong.sub(r"\1", desc)
        desc = img.sub(r"", desc)
        desc = anchor.sub(r"\1", desc)
        desc = ul.sub(r"", desc)
        desc = br.sub(r"", desc)
        desc = li.sub("\t\u2022 \\1", desc)
        return (
            desc.replace("&nbsp;", "").replace("&gt;", ">").replace("&lt;", "<").strip()
            or None
        )

    @property
    def url(self):
        return f"https://trovesaurus.com/mod={self.id}"
