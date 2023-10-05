import zlib
from base64 import b64encode
from enum import Enum
from hashlib import md5
from pathlib import Path
from typing import Union

from binary_reader import BinaryReader

from utils.functions import ReadLeb128, WriteLeb128, calculate_hash, get_attr
from utils.trovesaurus import get_mod_from_hash


class KnownProperties(Enum):
    game_version = "gameVersion"
    author = "author"
    steam_id = "SteamId"
    title = "title"
    notes = "notes"
    preview_path = "previewPath"
    tags = "tags"


class TModProperty:
    def __init__(self, name: KnownProperties, value):
        if name not in KnownProperties:
            raise Exception("Unknown TMod property: " + name)
        self._name = name
        self._value = value

    def __str__(self):
        return f"<TModProperty {self.name}: \"{self.value}\">"

    def __repr__(self):
        return str(self)

    @property
    def name(self):
        return self._name.value

    @property
    def value(self):
        if isinstance(self._value, list):
            return ",".join(self._value)
        return self._value

    @value.setter
    def value(self, value):
        self._value = value


class TModMetadata:
    def __init__(
            self,
            properties: list[TModProperty],
            version=1
    ):
        self.properties = properties
        self.version = version


class TModFile:
    def __init__(self, cwd: Path, name: Union[Path, str], content: Union[Path, bytes] = None):
        self.index = 0
        self.offset = 0
        self.cwd = cwd
        self._name = name
        self._content = content
        self._checksum = None

    def __str__(self):
        return f"<TModFile \"{self.name} ({self.size}\" bytes)>"

    def __repr__(self):
        return str(self)

    @property
    def name(self) -> str:
        return str(self._name)

    @name.setter
    def name(self, value: Union[Path, str]):
        self._name = value

    @property
    def content(self) -> bytes:
        if isinstance(self._content, Path):
            return self._content.read_bytes()
        return self._content

    @content.setter
    def content(self, value: Union[Path, bytes]):
        self._checksum = None
        self._content = value

    @property
    def size(self):
        return len(self.content)

    @property
    def checksum(self):
        if self._checksum is None:
            self._checksum = calculate_hash(self.padded_content)
        return self._checksum

    @property
    def padded_content(self):
        repeats = (4 - len(self.content) % 4)
        padding = b"\x00"
        return self.content + padding * repeats

    @property
    def padded_size(self):
        return len(self.padded_content)

    @property
    def header_format(self) -> bytes:
        data = BinaryReader(b"")
        data.write_int8(len(self.name))
        data.write_str(self.name)
        data.extend(WriteLeb128(self.index))
        data.extend(WriteLeb128(self.offset))
        data.extend(WriteLeb128(self.size))
        data.extend(WriteLeb128(self.checksum))
        return data.buffer()

class TMod:
    def __init__(self, metadata: TModMetadata, files: list[TModFile] = None):
        self.path = None
        self.data = BinaryReader(b"")
        self.metadata = metadata
        self.files = []
        self.files.extend(files or [])
        self._on_trovesaurus = None
        self._trovesaurus = None

    def __str__(self):
        return get_attr(self.metadata.properties, name="title").value

    def __repr__(self):
        return str(self)

    @property
    def hash(self):
        return md5(self.data.buffer()).hexdigest()

    async def trovesaurus(self):
        if self._on_trovesaurus is False:
            return self._trovesaurus
        if self._on_trovesaurus is None:
            self._trovesaurus = await get_mod_from_hash(self.data)
        return self._trovesaurus

    @property
    def raw_image(self):
        previewPath = get_attr(self.metadata.properties, name="previewPath").value
        for file in self.files:
            if file.name == previewPath:
                return file.content
        return open("assets/images/construction.png", "rb").read()

    @property
    def image(self):
        return b64encode(self.raw_image).decode("utf-8")

    def add_file(self, file: TModFile):
        self.files.append(file)

    def remove_file(self, file: TModFile):
        self.files.remove(file)

    def generate_mod(self) -> bytes:
        # Setup Streams
        header_stream = BinaryReader(b"")
        properties_stream = BinaryReader(b"")
        files_list_stream = BinaryReader(b"")
        file_stream = BinaryReader(b"")
        # Write Properties
        for property in self.metadata.properties:
            properties_stream.write_int8(len(property.name))
            properties_stream.write_str(property.name)
            properties_stream.write_int8(len(property.value))
            properties_stream.write_str(property.value)
        # Write Files
        offset = 0
        for file in self.files:
            file.offset = offset
            file_stream.extend(file.padded_content)
            offset += file.padded_size
        # Compress Files
        compressor = zlib.compressobj(level=0, wbits=zlib.MAX_WBITS)
        file_stream = BinaryReader(
            compressor.compress(
                file_stream.buffer()
            ) + compressor.flush(zlib.Z_SYNC_FLUSH)
        )
        # Write Files List
        for file in self.files:
            files_list_stream.extend(file.header_format)
        # Write Header
        header_stream.write_uint64(0)
        header_stream.write_uint16(self.metadata.version)
        header_stream.write_uint16(len(self.metadata.properties))
        header_stream.extend(properties_stream.buffer())
        header_stream.extend(files_list_stream.buffer())
        header_stream.seek(0)
        header_stream.write_uint64(len(header_stream.buffer()))
        # Write Data
        self.data = BinaryReader(header_stream.buffer() + file_stream.buffer())
        return self.data.buffer()

    @classmethod
    def read(cls, path: Path) -> "TMod":
        data = BinaryReader(open(path, 'rb').read())
        header_size = data.read_uint64()
        tmod_version = data.read_uint16()
        tmod_property_count = data.read_uint16()
        properties = []
        for i in range(tmod_property_count):
            name_size = data.read_uint8()
            name = data.read_str(name_size)
            value_size = data.read_uint8()
            value = data.read_str(value_size)
            properties.append(TModProperty(KnownProperties(name), value))
        file_stream = data.buffer()[header_size:]
        decompressor = zlib.decompressobj(wbits=zlib.MAX_WBITS)
        file_stream = BinaryReader(decompressor.decompress(file_stream))
        files = []
        while data.pos() < header_size:
            name_size = data.read_uint8()
            name = data.read_str(name_size)
            index = ReadLeb128(data, data.pos())
            offset = ReadLeb128(data, data.pos())
            size = ReadLeb128(data, data.pos())
            checksum = ReadLeb128(data, data.pos())
            file_stream.seek(offset)
            content = file_stream.read_bytes(size + (4 - size % 4))
            file = TModFile(path.parent, name, content)
            file.index = index
            files.append(file)
        obj = cls(
            metadata=TModMetadata(
                properties=properties,
                version=tmod_version
            ),
            files=files
        )
        obj.data = data
        obj.path = path
        return obj
