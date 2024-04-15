from datetime import datetime, UTC
from enum import Enum
from typing import Union, Optional
from urllib.parse import urlencode

from aiohttp import ClientSession
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
    def image_thumbnail_url(self):
        return self.image_url.replace("_l.", "_t.")


class ImageSize(Enum):
    MINI = 24
    TINY = 32
    SMALL = 64
    MEDIUM = 128
    LARGE = 256
    HUGE = 512
    MAX = 1024


class ModsEndpoint(Enum):
    base: str = "/mods"
    list: str = "/mods/search"
    types: str = "/mods/types"
    sub_types: str = "/mods/sub_types"
    image_resize: str = "/image/resize"
    mastery: str = "/stats/mastery"
    profiles: str = "/profile"
    twitch_streams: str = "/misc/twitch_streams"


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
        sort_by: list[tuple[str, str]] = None,
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
            sort_by_string = ",".join([f"{field}:{order}" for field, order in sort_by])
            params["sort_by"] = sort_by_string
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

    def get_resized_image_url(self, url: str, size: ImageSize):
        return (
            self.api_url
            + ModsEndpoint.image_resize.value
            + f"?url={url}&size={size.name}"
        )

    async def get_mastery(self):
        async with ClientSession() as session:
            async with session.get(
                f"{self.api_url}{ModsEndpoint.mastery.value}"
            ) as response:
                return await response.json()

    async def update_mastery(self, user_token: str, mastery_data: dict):
        async with ClientSession() as session:
            await session.put(
                f"{self.api_url}{ModsEndpoint.mastery.value}",
                headers={"Authorization": user_token},
                json={"mastery_data": mastery_data},
            )

    async def create_profile(self, user_token: str, name: str, description: str):
        async with ClientSession() as session:
            await session.post(
                f"{self.api_url}{ModsEndpoint.profiles.value}/create",
                headers={"Authorization": user_token},
                json={"name": name, "description": description},
            )

    async def update_profile(self, user_token: str, profile_id: str, **kwargs):
        async with ClientSession() as session:
            await session.put(
                f"{self.api_url}{ModsEndpoint.profiles.value}/update/{profile_id}",
                headers={"Authorization": user_token},
                json=kwargs,
            )

    async def list_profiles(self, user_token: str):
        async with ClientSession() as session:
            async with session.get(
                f"{self.api_url}{ModsEndpoint.profiles.value}/list_profiles",
                headers={"Authorization": user_token},
            ) as response:
                return await response.json()

    async def share_profile(self, user_token: str, profile_id: str):
        async with ClientSession() as session:
            await session.post(
                f"{self.api_url}{ModsEndpoint.profiles.value}/share/{profile_id}",
                headers={"Authorization": user_token},
            )

    async def private_profile(self, user_token: str, profile_id: str):
        async with ClientSession() as session:
            await session.post(
                f"{self.api_url}{ModsEndpoint.profiles.value}/unshare/{profile_id}",
                headers={"Authorization": user_token},
            )

    async def delete_profile(self, user_token: str, profile_id: str):
        async with ClientSession() as session:
            await session.delete(
                f"{self.api_url}{ModsEndpoint.profiles.value}/delete/{profile_id}",
                headers={"Authorization": user_token},
            )

    async def add_mods_to_profile(
        self, user_token: str, profile_id: str, mod_hashes: list[str]
    ):
        async with ClientSession() as session:
            await session.post(
                f"{self.api_url}{ModsEndpoint.profiles.value}/mod_hashes/{profile_id}",
                headers={"Authorization": user_token},
                json={"hashes": mod_hashes},
            )

    async def remove_mods_from_profile(
        self, user_token: str, profile_id: str, mod_hashes: list[str]
    ):
        async with ClientSession() as session:
            await session.delete(
                f"{self.api_url}{ModsEndpoint.profiles.value}/mod_hashes/{profile_id}",
                headers={"Authorization": user_token},
                json={"hashes": mod_hashes},
            )

    async def get_twitch_streams(self):
        async with ClientSession() as session:
            async with session.get(
                f"{self.api_url}{ModsEndpoint.twitch_streams.value}"
            ) as response:
                return await response.json()
