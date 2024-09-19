from __future__ import annotations

import asyncio
import base64
import io
import zipfile
import zlib
from hashlib import md5
from io import BytesIO
from pathlib import Path
from typing import Optional

from aiohttp import ClientSession
from binary_reader import BinaryReader
from pydantic import BaseModel
from toml import dumps
import re
import os

from utils.functions import read_leb128, write_leb128, calculate_hash, chunks, get_attr
from utils.logger import Logger
from ..trovesaurus.mods import Mod
from utils.trove.registry import TroveGamePath


ModParserLogger = Logger("Mod Parser")


class NoFilesError(Exception): ...


class PropertyMalformedError(Exception): ...


class MissingPropertyError(Exception): ...


class Property(BaseModel):
    name: str
    value: str

    def __str__(self):
        return self.value

    def __repr__(self):
        return f'<Property {self.name}: "{self.value}">'

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)


class TroveModFile:
    index: int = 0
    offset: int = 0

    def __init__(self, trove_path: Path, data: bytes):
        self.trove_path = trove_path.as_posix().lower()
        self._content = BinaryReader(bytearray(data))
        self._checksum = None

    def __str__(self):
        return f'<TroveModFile "{self.trove_path} ({self.size}" bytes)>'

    def __repr__(self):
        return str(self)

    @property
    def content(self) -> BinaryReader:
        return self._content

    @content.setter
    def content(self, value: BinaryReader):
        self._content = value

    @property
    def data(self) -> bytes:
        return self.content.buffer()

    @data.setter
    def data(self, value: bytes):
        self.content = BinaryReader(bytearray(value))

    @property
    def size(self):
        return self.content.size()

    @property
    def checksum(self):
        if self._checksum is None:
            self._checksum = calculate_hash(
                bytes(self.content.buffer()), len(self.content.buffer())
            )
        return self._checksum

    @property
    def padded_data(self) -> bytes:
        data = self.data
        if len(data) % 4 != 0:
            data += b"\x00" * (4 - (len(data) % 4))
        return data

    @property
    def header_format(self) -> bytes:
        data = BinaryReader(bytearray())
        data.write_int8(len(str(self.trove_path)))
        data.write_str(str(self.trove_path))
        data.extend(write_leb128(self.index))
        data.extend(write_leb128(self.offset if self.content.buffer() else 0))
        data.extend(write_leb128(self.size))
        data.extend(write_leb128(self.checksum))
        return data.buffer()


class TroveMod:
    mod_path: Path
    version: int = 1
    properties: list[Property]
    _content_files: list[str]
    files: list[TroveModFile]
    _zip_hash: str = None
    _tmod_hash: str = None
    _zip_content: bytes = None
    _tmod_content: bytes = None
    enabled: bool = True
    name_conflicts: list[TroveMod]
    file_conflicts: list[TroveMod]
    _trovesaurus_data: Optional[Mod] = None

    def __init__(self):
        self.properties = []
        self._content_files = []
        self.files = []
        self.name_conflicts = []
        self.file_conflicts = []

    def __str__(self):
        return f'<TroveMod "{self.name}">'

    def __repr__(self):
        return str(self)

    @property
    def content_files(self):
        if not self._content_files:
            self._content_files = [
                f.trove_path for f in self.files if f.trove_path != self.preview_path
            ]
        return self._content_files

    @content_files.setter
    def content_files(self, value: list[TroveModFile]):
        self._content_files = value

    @property
    def cwd(self):
        return self.mod_path.parent

    @property
    def has_wrong_name(self):
        stem = str(self.mod_path).split(".tmod")[0]
        return stem != self.name

    @property
    def is_ui_mod(self):
        return False

    @property
    def is_rtt_mod(self):
        return self.get_property_value("modLoader") == "RTT"

    def toggle(self):
        self.enabled = not self.enabled
        extension = ".tmod" if isinstance(self, TMod) else ".zip"
        if self.enabled:
            new_name = self.mod_path.name.split(f"{extension}.disabled")[0] + extension
            new_path = self.cwd.joinpath(new_name)
        else:
            new_name = self.mod_path.name.split(extension)[0] + f"{extension}.disabled"
            new_path = self.cwd.joinpath(new_name)
        if new_path.exists():
            raise FileExistsError()
        self.mod_path.rename(new_path)
        self.mod_path = new_path

    def fix_name(self):
        extension = ".tmod" if self.enabled else ".tmod.disabled"
        new_mod_path = self.mod_path.with_name(self.name + extension)
        if new_mod_path.exists():
            return
        try:
            self.mod_path.rename(new_mod_path)
            self.mod_path = new_mod_path
        except PermissionError:
            ModParserLogger.error(
                f"Failed to rename mod {self.name} at {self.mod_path} (Likely another program is using it)"
            )

    def check_conflicts(self, mods: list[TroveMod], force=False):
        if force:
            self.conflicts.clear()
        for mod in mods:
            if mod == self:
                continue
            if mod.name == self.name:
                self.name_conflicts.append(mod)
            if mod in self.file_conflicts:
                continue
            self_files = set(self.content_files)
            mod_files = set(mod.content_files)
            if self_files & mod_files:
                self.file_conflicts.append(mod)
                if self not in mod.file_conflicts:
                    mod.file_conflicts.append(self)
        self.file_conflicts = list(set(self.file_conflicts))

    @property
    def conflicts(self):
        return self.name_conflicts + self.file_conflicts

    @property
    def has_conflicts(self):
        return bool(self.conflicts)

    @property
    def metadata(self) -> str:
        metadata = dict()
        metadata["name"] = self.name
        metadata["properties"] = {}
        needed_props = ["author", "title"]
        for prop in needed_props:
            if prop not in [p.name for p in self.properties]:
                raise MissingPropertyError(f'Property "{prop}" is missing')
        for prop in self.properties:
            if prop.name in needed_props and not prop.value:
                raise PropertyMalformedError(f'Property "{prop.name}" has no value')
            metadata["properties"][prop.name] = prop.value
        metadata["files"] = [str(f.trove_path) for f in self.files]
        return dumps(metadata)

    @property
    def name(self):
        return self.get_property_value("title")

    @name.setter
    def name(self, value: str):
        self.add_property("title", value)

    @property
    def author(self):
        return self.get_property_value("author")

    @author.setter
    def author(self, value: str):
        self.add_property("author", value)

    @property
    def steam_id(self):
        return self.get_property_value("SteamId")

    @steam_id.setter
    def steam_id(self, value: str):
        self.add_property("SteamId", value)

    @property
    def game_version(self):
        return self.get_property_value("gameVersion")

    @game_version.setter
    def game_version(self, value: str):
        self.add_property("gameVersion", value)

    @property
    def notes(self):
        return self.get_property_value("notes")

    @notes.setter
    def notes(self, value: str):
        self.add_property("notes", value)

    @property
    def preview_path(self):
        preview_path = self.get_property_value("previewPath")
        if preview_path:
            return preview_path.lower()
        return preview_path

    @preview_path.setter
    def preview_path(self, value: Path):
        self.add_property("previewPath", value.as_posix())

    @property
    def image(self):
        for file in self.files:
            if file.trove_path == self.preview_path:
                return base64.b64encode(file.data).decode("utf-8")
        return base64.b64encode(
            open("assets/images/no_preview.png", "rb").read()
        ).decode("utf-8")

    @property
    def tags(self):
        tags = self.get_property_value("tags")
        if tags:
            return tags.split(",")
        return []

    def add_tag(self, tag: str):
        tags = self.tags
        tags.append(tag)
        tags_string = ",".join(tags)
        self.add_property("tags", tags_string)

    def remove_tag(self, tag: str):
        tags = self.tags
        tags.remove(tag)
        tags_string = ",".join(tags)
        self.add_property("tags", tags_string)

    def add_property(self, name: str, value: str):
        self.remove_property(name)
        self.properties.append(Property(name=name, value=value))

    def remove_property(self, name: str):
        prop = get_attr(self.properties, name=name)
        if prop is not None:
            self.properties.remove(prop)

    def get_property(self, name: str):
        return get_attr(self.properties, name=name)

    def get_property_value(self, name: str):
        prop = self.get_property(name)
        if prop:
            return prop.value
        return None

    def reorder_files(self):
        offset = 0
        for file in self.files:
            file.index = 0
            file.offset = offset
            offset += len(file.padded_data)

    def reset_cache(self):
        self.zip_content = None
        self.zip_hash = None
        self.tmod_content = None
        self.tmod_hash = None

    def add_file(self, file: TroveModFile):
        self.files.append(file)
        self.reset_cache()
        self.reorder_files()

    def remove_file(self, file: TroveModFile):
        self.files.remove(file)
        self.reset_cache()
        self.reorder_files()

    def pre_compile(self):
        self.reorder_files()
        metadata = self.metadata
        return metadata

    def compile_zip_mod(self) -> bytes:
        if self.zip_content:
            return self.zip_content
        if not self.files:
            raise NoFilesError("No files to compile")
        metadata = self.pre_compile()
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as f:
            for file in self.files:
                f.writestr(str(file.trove_path), file.data)
            f.writestr(str("metadata.toml"), bytes(metadata, "utf-8"))
        return data.getvalue()

    def compile_tmod(self) -> bytes:
        if self._tmod_content:
            return self.tmod_content
        if not self.files:
            raise NoFilesError("No files to compile")
        self.reorder_files()
        tmod = BinaryReader(bytearray())
        header_stream = BinaryReader(bytearray())
        properties_stream = BinaryReader(bytearray())
        files_list_stream = BinaryReader(bytearray())
        file_stream = BinaryReader(bytearray())
        self.add_property("modLoader", "RTT")
        for prop in self.properties:
            properties_stream.write_bytes(write_leb128(len(prop.name)))
            properties_stream.write_str(prop.name)
            properties_stream.write_bytes(write_leb128(len(prop.value)))
            properties_stream.write_str(prop.value)
        for file in self.files:
            file_stream.extend(bytearray(file.padded_data))
        compressor = zlib.compressobj(level=0, strategy=0, wbits=zlib.MAX_WBITS)
        chunked_file_stream = chunks(file_stream.buffer(), 32768)
        file_stream = BinaryReader(bytearray())
        for chunk in chunked_file_stream:
            file_stream.extend(bytearray(compressor.compress(chunk)))
        file_stream.extend(bytearray(compressor.flush(zlib.Z_SYNC_FLUSH)))
        for i, file in enumerate(self.files, 1):
            files_list_stream.extend(bytearray(file.header_format))
        header_stream.write_uint64(0)
        header_stream.write_uint16(self.version)
        header_stream.write_uint16(len(self.properties))
        header_stream.extend(properties_stream.buffer())
        header_stream.extend(files_list_stream.buffer())
        header_stream.seek(0)
        header_stream.write_uint64(len(header_stream.buffer()))
        tmod.extend(header_stream.buffer() + file_stream.buffer())
        return tmod.buffer()

    @property
    def zip_content(self):
        if self._zip_content is None:
            self.zip_content = self.compile_zip_mod()
        return self._zip_content

    @zip_content.setter
    def zip_content(self, value: bytes):
        self._zip_content = value

    @property
    def tmod_content(self):
        if self._tmod_content is None:
            self.tmod_content = self.compile_tmod()
        return self._tmod_content

    @tmod_content.setter
    def tmod_content(self, value: bytes):
        self._tmod_content = value

    @property
    def hash(self):
        return ""

    @property
    def zip_hash(self):
        if self._zip_hash is None:
            self.zip_hash = md5(self.compile_zip_mod()).hexdigest()
        return self._zip_hash

    @zip_hash.setter
    def zip_hash(self, value: str):
        self._zip_hash = value

    @property
    def tmod_hash(self):
        if self._tmod_hash is None:
            self.tmod_hash = md5(self.compile_tmod()).hexdigest()
        return self._tmod_hash

    @tmod_hash.setter
    def tmod_hash(self, value: str):
        self._tmod_hash = value

    @property
    def trovesaurus_data(self) -> Mod:
        return self._trovesaurus_data

    @trovesaurus_data.setter
    def trovesaurus_data(self, value: Mod):
        self._trovesaurus_data = value

    @property
    def has_update(self):
        if self.trovesaurus_data is not None:
            files = [f for f in self.trovesaurus_data.file_objs if not f.is_config]
            files.sort(key=lambda f: -f.file_id)
            if files:
                return files[0].hash != self.trovesaurus_data.installed_file.hash
        return False

    async def update(self):
        if self.trovesaurus_data is not None:
            files = [f for f in self.trovesaurus_data.file_objs if not f.is_config]
            files.sort(key=lambda f: -f.file_id)
            if files:
                file = files[0]
                url = f"https://trovesaurus.com/client/downloadfile.php?fileid={file.file_id}"
                async with ClientSession() as session:
                    async with session.get(url) as response:
                        data = await response.read()
                        self.mod_path.write_bytes(data)

    def ensure_config(self):
        pass


class TMod(TroveMod):
    def __str__(self):
        return f'<TMod "{self.name}">'

    @property
    def hash(self):
        return self.tmod_hash

    @classmethod
    def read_bytes(cls, path: Path, data: bytes, partial=False):
        mod = cls()
        mod.tmod_content = data
        mod.mod_path = path
        mod.files = []
        data = BinaryReader(bytearray(data))
        header_size = data.read_uint64()
        mod.version = data.read_uint16()
        properties_count = data.read_uint16()
        mod.properties = []
        for i in range(properties_count):
            name_size = read_leb128(data, data.pos())
            name = data.read_str(name_size)
            value_size = read_leb128(data, data.pos())
            value = data.read_str(value_size)
            mod.properties.append(Property(name=name, value=value))
        if not partial:
            file_stream = data.buffer()[header_size:]
            decompressor = zlib.decompressobj(wbits=zlib.MAX_WBITS)
            try:
                file_stream = BinaryReader(
                    bytearray(decompressor.decompress(file_stream))
                )
            except:
                ModParserLogger.debug(
                    "Failed to decompile mod, trying manual decompression: " + str(path)
                )
                file_stream = BinaryReader(
                    bytearray(mod.manual_decompression(file_stream))
                )
        while data.pos() < header_size:
            name_size = data.read_uint8()
            name = data.read_str(name_size)
            index = read_leb128(data, data.pos())
            offset = read_leb128(data, data.pos())
            size = read_leb128(data, data.pos())
            checksum = read_leb128(data, data.pos())
            if not partial:
                file_stream.seek(offset)
                content = file_stream.read_bytes(size)
                file = TroveModFile(Path(name), content)
                file.index = index
                file.old_checksum = checksum
                mod.files.append(file)
        return mod

    @staticmethod
    def manual_decompression(data: bytes):
        data = BinaryReader(bytearray(data[7:-5]))
        data_chunks = data.size() // (32768 + 5)
        output = BinaryReader(bytearray())
        for i in range(data_chunks):
            output.extend(bytearray(data.read_bytes(32768)))
            data.read_bytes(5)
        output.extend(bytearray(data.read_bytes(data.size() - data.pos())))
        return output.buffer()

    @staticmethod
    def manual_compression(data: bytes):
        output = BinaryReader(bytearray())
        output.write_bytes(b"\x78\x01\x00\x00\x80\xFF\x7F")
        data_chunks = chunks(data, 32768)
        for data_chunk in data_chunks:
            output.write_bytes(data_chunk)
            if len(data_chunk) == 32768:
                output.write_bytes(b"\x00\x00\x80\xFF\x7F")
        output.write_bytes(b"\x00\x00\x00\xFF\xFF")
        return output.buffer()

    @property
    def is_ui_mod(self):
        for file in self.files:
            if file.trove_path.endswith(".swf"):
                return True

    def ensure_config(self):
        if os.name != "nt":
            return
        mods_cfgs_path = Path(os.getenv("APPDATA")).joinpath("Trove", "ModCfgs")
        mods_cfgs_path.mkdir(parents=True, exist_ok=True)
        config_file = mods_cfgs_path.joinpath(f"{self.name}.cfg")
        swf_files = [
            file.trove_path.split("/")[-1]
            for file in self.files
            if file.trove_path.endswith(".swf")
        ]
        if not config_file.exists():
            configs = []
            for file in swf_files:
                file_name = file
                configs.append(f"[{file_name}]")
            config_file.write_text("\n".join(configs))
        else:
            regex = re.compile(r"^\[(.*?\.swf)]$", re.MULTILINE)
            current = config_file.read_text(encoding="utf-8")
            configs = regex.findall(current)
            missing = []
            for file in swf_files:
                if file not in configs:
                    missing.append(file)
            if missing:
                missing_text = "\n\n".join([f"[{file}]" for file in missing])
                current += "\n\n" + missing_text
                config_file.write_text(current, encoding="utf-8")


class ZMod(TroveMod):
    def __str__(self):
        return f'<ZMod "{self.name}">'

    @property
    def hash(self):
        return self.zip_hash

    @classmethod
    def read_bytes(cls, path: Path, data: io.BytesIO):
        mod = cls()
        mod.zip_content = data.read()
        mod.mod_path = path
        mod.files = []
        with zipfile.ZipFile(data) as f:
            for file_name in f.namelist():
                if file_name.endswith("/"):
                    continue
                mod.files.append(TroveModFile(Path(file_name), f.read(file_name)))
        mod.name = path.stem
        return mod


class TroveModList:
    enabled: list[TroveMod]
    disabled: list[TroveMod]
    _mods: list[TroveMod]

    def __init__(self, path: TroveGamePath, **kwargs):
        self._mods = []
        self.trove_path = path
        self._populate(**kwargs)

    def __str__(self):
        return f'<TroveModList "{self.trove_path.name}" count={self.count}>'

    def __repr__(self):
        return str(self)

    def __iter__(self):
        return iter(self.mods)

    def __len__(self):
        return self.count

    async def cloud_check(self):
        async with ClientSession() as session:
            try:
                async with session.get(
                    f"https://kiwiapi.aallyn.xyz/v1/profile/cloud_mods",
                    json={"hashes": self.all_hashes},
                    timeout=2,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        uploads = []
                        for hash, entry in data.items():
                            for mod in self:
                                if mod.hash == hash:
                                    if entry is None:
                                        if isinstance(mod, TMod):
                                            authors = [
                                                {
                                                    "ID": None,
                                                    "Username": author,
                                                    "Avatar": None,
                                                    "Role": None,
                                                }
                                                for author in mod.author.split(",")
                                            ]
                                            uploads.append(
                                                {
                                                    "hash": mod.hash,
                                                    "name": mod.name,
                                                    "format": "tmod",
                                                    "authors": authors,
                                                    "description": None,
                                                    "data": base64.b64encode(
                                                        mod.tmod_content
                                                    ).decode("utf-8"),
                                                }
                                            )
                                        else:
                                            ...
                                            # uploads.append(
                                            #     {
                                            #         "hash": mod.hash,
                                            #         "name": mod.name,
                                            #         "format": "zip",
                                            #         "authors": [],
                                            #         "description": None,
                                            #         "data": base64.b64encode(
                                            #             mod.zip_content
                                            #         ).decode("utf-8"),
                                            #     }
                                            # )
                        if uploads:
                            await session.post(
                                f"https://kiwiapi.aallyn.xyz/v1/profile/upload_cloud_mods",
                                json={"mods": uploads},
                            )
            except asyncio.TimeoutError:
                ...

    async def update_trovesaurus_data(self):
        async with ClientSession() as session:
            try:
                response = await session.get(
                    f"https://kiwiapi.aallyn.xyz/v1/mods/hashes",
                    json={"hashes": self.all_hashes},
                    timeout=10,
                )
                if response.status == 200:
                    data = await response.json()
                    for mod in self:
                        for k, v in data.items():
                            if mod.hash == k and v is not None:
                                mod.trovesaurus_data = Mod.parse_obj(v)
                                mod.trovesaurus_data.installed = True
                                for file in mod.trovesaurus_data.file_objs:
                                    if file.hash == mod.hash:
                                        mod.trovesaurus_data.installed_file = file
                                        mod.trovesaurus_data.installed_version = (
                                            file.version
                                        )
                                        break
                                break
            except asyncio.TimeoutError:
                ...

    @property
    def all_hashes(self):
        return [mod.hash for mod in self.mods]

    @property
    def name(self):
        return self.trove_path.name

    @property
    def mods(self):
        return self._mods

    @property
    def enabled(self):
        return [mod for mod in self.mods if mod.enabled]

    @property
    def disabled(self):
        return [mod for mod in self.mods if not mod.enabled]

    def sort_by_name(self):
        self._mods.sort(key=lambda mod: mod.name)

    @property
    def mods_with_conflicts(self):
        return [mod for mod in self.mods if mod.has_conflicts]

    @property
    def count(self):
        return len(self.mods)

    def refresh(self):
        self._populate(True)

    def _calculate_conflicts(self, force=False):
        for mod in self.mods:
            mod.check_conflicts(self.mods, force)

    def _ensure_mod_configs(self):
        for mod in self.mods:
            if mod.is_ui_mod:
                mod.ensure_config()

    def _populate(self, force=False, fix_names=True, fix_configs=True, partial=False):
        self._mods.clear()
        self._ensure_correct_extensions()
        self._populate_tmod_enabled(fix_names, partial)
        self._populate_tmod_disabled(fix_names, partial)
        self._populate_zip_enabled()
        self._populate_zip_disabled()
        self.sort_by_name()
        self._calculate_conflicts(force)
        if fix_configs:
            self._ensure_mod_configs()

    def _ensure_correct_extensions(self):
        for file in self.trove_path.enabled_tmods:
            if zipfile.is_zipfile(file):
                file.rename(file.with_suffix(".zip"))
        for file in self.trove_path.disabled_tmods:
            if zipfile.is_zipfile(file):
                file.rename(file.with_suffix("").with_suffix(".zip.disabled"))
        for file in self.trove_path.enabled_zips:
            if not zipfile.is_zipfile(file):
                file.rename(file.with_suffix(".tmod"))
        for file in self.trove_path.disabled_zips:
            if not zipfile.is_zipfile(file):
                file.rename(file.with_suffix("").with_suffix(".tmod.disabled"))

    def _populate_tmod_enabled(self, fix_names=True, partial=False):
        for file in self.trove_path.enabled_tmods:
            with open(file, "rb") as f:
                if partial:
                    file_data = f.read(8)
                    header_size = int.from_bytes(file_data, "little")
                    f.seek(0)
                    file_data = f.read(header_size)
                else:
                    file_data = f.read()
                mod = TMod.read_bytes(file, file_data, partial)
                if mod.has_wrong_name and fix_names:
                    mod.fix_name()
                self._mods.append(mod)

    def _populate_tmod_disabled(self, fix_names=True, partial=False):
        for file in self.trove_path.disabled_tmods:
            with open(file, "rb") as f:
                if partial:
                    file_data = f.read(8)
                    header_size = int.from_bytes(file_data, "little")
                    f.seek(0)
                    file_data = f.read(header_size)
                else:
                    file_data = f.read()
                mod = TMod.read_bytes(file, file_data, partial)
                mod.enabled = False
                if mod.has_wrong_name and fix_names:
                    mod.fix_name()
                self._mods.append(mod)

    def _populate_zip_enabled(self):
        for file in self.trove_path.enabled_zips:
            file_data = file.read_bytes()
            mod = ZMod.read_bytes(file, BytesIO(file_data))
            self._mods.append(mod)

    def _populate_zip_disabled(self):
        for file in self.trove_path.disabled_zips:
            file_data = file.read_bytes()
            mod = ZMod.read_bytes(file, BytesIO(file_data))
            mod.enabled = False
            self._mods.append(mod)
