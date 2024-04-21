from aiohttp import ClientSession
from json import load, loads
from pathlib import Path
from base64 import b64decode

files_cache = {}


async def fetch_files():
    async with ClientSession() as session:
        response = await session.get("https://kiwiapi.slynx.xyz/v1/stats/get_data")
        files_cache.clear()
        if response.status != 200:
            data_path = Path("data")
            files_data = [
                str(x.relative_to(data_path))
                for x in data_path.rglob("*")
                if x.is_file()
            ]
            files_cache.update(
                {
                    path.replace("\\", "/"): load(
                        open(data_path.joinpath(path), encoding="utf-8")
                    )
                    for path in files_data
                }
            )
            return
        files_data = await response.json()
        for path, data in files_data.items():
            files_cache[path] = loads(b64decode(data).decode("utf-8"))
        return files_cache
