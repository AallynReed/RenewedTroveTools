from aiohttp import ClientSession
from json import load
from pathlib import Path

files_cache = {}


async def fetch_files():
    session = ClientSession()
    response = await session.get("https://kiwiapi.slynx.xyz/v1/stats/files")
    files_cache.clear()
    if response.status != 200:
        data_path = Path("data")
        files_data = [
            str(x.relative_to(data_path)) for x in data_path.rglob("*") if x.is_file()
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
    files_cache.update(
        {
            path: await (
                await session.get(f"https://kiwiapi.slynx.xyz/v1/stats/file/{path}")
            ).json()
            for path in files_data
        }
    )
    await session.close()
    return files_cache
