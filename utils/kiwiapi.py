from datetime import datetime, UTC
from enum import Enum
from typing import Union, Optional

from pydantic import BaseModel, Field, validator
from aiohttp import ClientSession
from urllib.parse import urlencode


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
        return datetime.utcfromtimestamp(value)

    @validator("version")
    def parse_version(cls, value, values):
        if values["is_config"]:
            return "config"
        if not value.strip():
            return f"File: [{str(values['file_id'])}]"
        return value


class ModAuthorRoleColors(Enum):
    null = "#6C757D"
    modder = "#198754"
    artist = "#0D6EFD"
    gold = "#FFC107"
    creator = "#328282"
    streamer = "#800080"
    admin = "#800000"


class ModAuthorRole(Enum):
    null = ""
    modder = "Modder"
    artist = "Artist"
    gold = "Gold"
    creator = "Creator"
    streamer = "Streamer"
    admin = "Admin"


class ModAuthor(BaseModel):
    ID: Optional[int]
    Username: Optional[str]
    Avatar: str
    Role: ModAuthorRole


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


class ModsEndpoint(Enum):
    base: str = "/mods"
    list: str = "/mods/search"
    types: str = "/mods/types"
    sub_types: str = "/mods/sub_types"


class KiwiAPI:
    base_url: str = "https://kiwiapi.slynx.xyz"
    api_version: int = 1
    api_url: str = f"{base_url}/v{api_version}"

    async def get_mods_page_count(
        self,
        page_size: int = 8,
        query: str = None,
        type: str = None,
        sub_type: str = None,
    ):
        params = {"limit": page_size}
        if query is not None:
            params["query"] = query
        if type is not None:
            params["type"] = type
        if sub_type is not None:
            params["sub_type"] = sub_type
        encoded_params = urlencode(params)
        async with ClientSession() as session:
            async with session.get(
                f"{self.api_url}{ModsEndpoint.list.value}?{encoded_params}"
            ) as response:
                count = int(response.headers.get("count"))
                pages = count // page_size + 1
        return pages

    async def get_mods_list_chunk(
        self,
        page_size: int = 8,
        page: int = 0,
        query: str = None,
        type: str = None,
        sub_type: str = None,
        sort_by: list[tuple[str, int]] = None,
    ):
        offset = page_size * page
        params = {"limit": page_size, "offset": offset}
        if query is not None:
            params["query"] = query
        if type is not None:
            params["type"] = type
        if sub_type is not None:
            params["sub_type"] = sub_type
        if sort_by is not None:
            ...
        encoded_params = urlencode(params)
        async with ClientSession() as session:
            async with session.get(
                f"{self.api_url}{ModsEndpoint.list.value}?{encoded_params}"
            ) as response:
                mods = await response.json()
        return [Mod(**mod) for mod in mods]

    async def get_mod_types(self):
        async with ClientSession() as session:
            async with session.get(
                f"{self.api_url}{ModsEndpoint.types.value}"
            ) as response:
                return await response.json()

    async def get_mod_sub_types(self, type: str):
        async with ClientSession() as session:
            async with session.get(
                f"{self.api_url}{ModsEndpoint.sub_types.value}/{type}"
            ) as response:
                return await response.json()
