from hashlib import md5

from aiohttp import ClientSession

from models.trovesaurus.mods import Mod, ModFile


async def get_mod_from_hash(data):
    async with ClientSession() as session:
        hash = md5(data.buffer()).hexdigest()
        async with session.get(
            f"https://trovesaurus.com/client/getmodfilesfromhash.php?hash={hash}"
        ) as response:
            data = await response.json()
            if not data:
                return None
            key = list(data.keys())[0]
            mod_files = [ModFile.parse_obj(mod) for mod in data[key]]
            return mod_files[0]


async def get_mods_list(*fields, limit=0, offset=0) -> list[Mod]:
    url_query = ""
    url_query += "#".join(f"{field[0]}${field[1].value}" for field in fields)
    url_query += f"&limit={limit}" if limit else ""
    url_query += f"&offset={offset}" if offset else ""
    async with ClientSession() as session:
        async with session.get(
            f"https://kiwiapi.aallyn.xyz/v1/mods/list?{url_query}"
        ) as response:
            data = await response.json()
            return [Mod.parse_obj(mod) for mod in data]
