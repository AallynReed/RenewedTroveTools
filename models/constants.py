from aiohttp import ClientSession
from json import load, loads
from pathlib import Path
from base64 import b64decode

files_cache = {}


async def fetch_files(local_data=False, local_locales=False):
    async with ClientSession() as session:
        # Load data files
        files_cache.clear()
        if not local_data:
            response = await session.get("https://kiwiapi.slynx.xyz/v1/stats/get_data")
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
            else:
                files_data = await response.json()
                for path, data in files_data.items():
                    files_cache[path] = loads(b64decode(data).decode("utf-8"))
        else:
            data_path = Path("data")
            for x in data_path.rglob("*.json"):
                if x.is_file():
                    file_name = str(x.relative_to(data_path).as_posix())
                    files_cache[file_name] = loads(x.read_text(encoding="utf-8"))
        # Load localization files
        if not local_locales:
            response = await session.get("https://kiwiapi.slynx.xyz/v1/misc/locales")
            if response.status != 200:
                locales_path = Path("locales")
                files_data = [
                    str(x.relative_to(locales_path))
                    for x in locales_path.rglob("*")
                    if x.is_file()
                ]
                files_cache.update(
                    {
                        path.replace("\\", "/"): locales_path.joinpath(path).read_text(
                            encoding="utf-8"
                        )
                        for path in files_data
                    }
                )
            else:
                files_data = await response.json()
                for path, data in files_data.items():
                    files_cache[path] = b64decode(data).decode("utf-8")
        else:
            locales_path = Path("locales")
            for x in locales_path.rglob("*.loc"):
                if x.is_file():
                    file_name = str(x.relative_to(locales_path).as_posix())
                    files_cache[file_name] = x.read_text(encoding="utf-8")
        return files_cache
