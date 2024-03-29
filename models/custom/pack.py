import zlib
from pathlib import Path

from binary_reader import BinaryReader

from models.trove.mod import TroveMod, Property
from utils.functions import get_attr, read_leb128, write_leb128, calculate_hash, chunks


class TPack:
    properties: list[Property]
    files: list[TroveMod]

    def compile(self):
        pack = BinaryReader(bytearray())
        file_stream = BinaryReader(bytearray())
        pack.write_uint64(0)
        pack.write_uint16(1)
        pack.write_uint16(len(self.properties))
        for prop in self.properties:
            pack.write_bytes(write_leb128(len(prop.name)))
            pack.write_str(prop.name)
            pack.write_bytes(write_leb128(len(prop.value)))
            pack.write_str(prop.value)
        offset = 0
        for file in self.files:
            mod_data = file.mod_path.read_bytes()
            pack.write_int8(len(file.mod_path.name))
            pack.write_str(file.mod_path.name)
            pack.write_bytes(write_leb128(0))
            pack.write_bytes(write_leb128(0))
            pack.write_bytes(write_leb128(offset))
            pack.write_bytes(write_leb128(len(mod_data)))
            pack.write_bytes(write_leb128(calculate_hash(mod_data, len(mod_data))))
            offset += len(mod_data)
            file_stream.write_bytes(mod_data)
        pack.seek(0)
        pack.write_uint64(pack.size())
        # Compress file stream to Trove Standards
        compressor = zlib.compressobj(level=0, strategy=0, wbits=zlib.MAX_WBITS)
        chunked_file_stream = chunks(file_stream.buffer(), 32768)
        file_stream = BinaryReader(bytearray())
        for chunk in chunked_file_stream:
            file_stream.extend(bytearray(compressor.compress(chunk)))
        file_stream.extend(bytearray(compressor.flush(zlib.Z_SYNC_FLUSH)))
        pack.extend(file_stream.buffer())
        return pack.buffer()

    @classmethod
    def parse(cls, path: Path, data):
        tpack = cls()
        pack = BinaryReader(bytearray(data))
        header_size = pack.read_uint64()
        version = pack.read_uint16()
        file_count = pack.read_uint16()
        property_count = pack.read_uint16()
        for _ in range(property_count):
            name_length = read_leb128(pack)
            name = pack.read_str(name_length)
            value_length = read_leb128(pack)
            value = pack.read_str(value_length)
            tpack.add_property(name, value)
        for _ in range(file_count):
            file_name_length = pack.read_int8()
            file_name = pack.read_str(file_name_length)
            index = read_leb128(pack, pack.pos())
            file_offset = read_leb128(pack, pack.pos())
            file_size = read_leb128(pack, pack.pos())
            file_hash = read_leb128(pack, pack.pos())
            tpack.files.append(TroveMod(file_name, file_offset, file_size, file_hash))

    @property
    def author(self):
        return self.get_property("author").value

    @author.setter
    def author(self, value):
        self.add_property("author", value)

    def get_property(self, name):
        return get_attr(self.properties, name=name)

    def add_property(self, name, value):
        if self.get_property(name) is not None:
            self.remove_property(name)
        self.properties.append(Property(name, value))

    def remove_property(self, name):
        self.properties.remove(self.get_property(name))
