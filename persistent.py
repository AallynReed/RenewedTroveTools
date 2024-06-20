from utils import tasks
import asyncio
import aiofiles
from watchdog.events import FileSystemEventHandler
import re
from aiohttp import ClientSession
import psutil
from utils.trove.registry import get_trove_locations
from pathlib import Path


class AsyncFileEventHandler(FileSystemEventHandler):
    def __init__(self, page, loop):
        self.page = page
        self.loop = loop
        self.swf_file_regex = re.compile(r"\[(.*?\.swf)]")
        self.swf_files = {
            "zonebanner.swf": [
                (
                    self.process_biomes,
                    re.compile(
                        r"biome = (.*)",
                        re.MULTILINE,
                    ),
                )
            ]
        }

    def check_process_and_get_path(self, process_name):
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if proc.info["name"] == process_name:
                    process_path = Path(proc.info["exe"])
                    for trove_location in get_trove_locations():
                        if process_path.is_relative_to(trove_location.path):
                            return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return False

    def on_modified(self, event):
        if not self.page.user_data or not self.check_process_and_get_path("Trove.exe"):
            return
        if not event.is_directory and event.src_path.endswith(".cfg"):
            asyncio.run_coroutine_threadsafe(self.process(event.src_path), self.loop)

    async def process(self, file_path):
        async with aiofiles.open(file_path, "r") as f:
            content = await f.read()
            swf_file = None
            for line in content.splitlines():
                match = self.swf_file_regex.search(line)
                if match:
                    swf_file = match.group(1)
                if swf_file is None:
                    continue
                regexes = self.swf_files.get(swf_file)
                if regexes is None:
                    continue
                for function, regex in regexes:
                    result = regex.search(content)
                    if result:
                        await function(result.group(1))

    async def process_biomes(self, biome):
        async with ClientSession() as session:
            data = {
                "biome": biome,
            }
            headers = {"Authorization": self.page.user_data["internal_token"]}
            await session.post(
                "https://kiwiapi.aallyn.xyz/v1/misc/d15_biomes",
                json=data,
                headers=headers,
            )
