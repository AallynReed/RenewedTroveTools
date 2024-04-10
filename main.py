import asyncio
import json
import os
import re
import sys
from datetime import datetime
from json import load
from pathlib import Path
from urllib.parse import urlparse

import requests
from aiohttp import ClientSession
from flet import app_async, WEB_BROWSER, FLET_APP, Theme, Row, Text, Icon

from models import Metadata, Preferences
from models.interface import CustomAppBar
from models.interface.controls import Snackbar, Modal
from utils import tasks
from utils.localization import LocalizationManager
from utils.logger import Logger
from utils.path import BasePath
from utils.protocol import set_protocol
from utils.routing import Routing
from utils.trove.server_time import ServerTime
from views import all_views


class App:
    def __init__(self, web=False):
        self.web = web

    def run(self, port: int = 0):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            app_async(
                target=self.start,
                assets_dir="assets",
                view=WEB_BROWSER if self.web else FLET_APP,
                port=port,
            )
        )

    async def start(self, page):
        self.page = page
        self.page.RTT = self
        if page.web:
            await self.start_web(page)
        else:
            await self.start_app(page)

    async def start_app(self, _):
        set_protocol()
        self.setup_folders()
        await self.load_configurations()
        await self.load_constants()
        await self.setup_protocol_socket()
        self.setup_logging()
        self.setup_localization()
        await self.setup_page()
        await self.gather_views()
        await self.process_login()

    async def start_web(self, _):
        self.setup_folders()
        await self.load_configurations()
        await self.load_constants()
        self.setup_logging(True)
        self.setup_localization()
        await self.setup_page()
        await self.gather_views()
        await self.post_login(route=self.page.route)

    def setup_folders(self):
        self.compiled = getattr(sys, "frozen", False)
        self.app_path = BasePath
        self.page.metadata = Metadata.load_from_file(
            self.app_path.joinpath("data/metadata.json")
        )
        if not self.page.web:
            try:
                APPDATA = Path(os.environ.get("APPDATA"))
            except TypeError:
                # Patch for Linux support
                APPDATA = Path(os.getenv("HOME") + "/.steam/Steam/steamapps/common")
            self.app_data = APPDATA.joinpath("Trove/sly.dev").joinpath(
                self.page.metadata.tech_name
            )
            self.logs_folder = self.app_data.joinpath("logs")
            self.logs_folder.mkdir(parents=True, exist_ok=True)
            self.app_data.mkdir(parents=True, exist_ok=True)

    async def load_configurations(self):
        self.page.user_data = None
        self.page.trove_time = ServerTime()
        if self.page.web:
            self.page.preferences = await Preferences.load_from_web(self.page)
        else:
            self.page.preferences = Preferences.load_from_json(
                self.app_data.joinpath("preferences.json"), self.page
            )
            self.page.theme_mode = self.page.preferences.theme
            self.page.theme = Theme(
                color_scheme_seed=str(self.page.preferences.accent_color)
            )

    async def load_constants(self):
        async with ClientSession() as session:
            async with session.get(
                "https://kiwiapi.slynx.xyz/v1/stats/files"
            ) as response:
                if response.status != 200:
                    data_path = Path("data")
                    files = [
                        str(x.relative_to(data_path))
                        for x in data_path.rglob("*")
                        if x.is_file()
                    ]
                    self.page.data_files = {
                        path.replace("\\", "/"): load(
                            open(data_path.joinpath(path), encoding="utf-8")
                        )
                        for path in files
                    }
                    return
                files = await response.json()
                self.page.data_files = {
                    path: await (
                        await session.get(
                            f"https://kiwiapi.slynx.xyz/v1/stats/file/{path}"
                        )
                    ).json()
                    for path in files
                }

    async def setup_protocol_socket(self):
        for port in range(13010, 13020):
            try:
                self.page.protocol_socket = await asyncio.start_server(
                    self.protocol_handler, "127.0.0.1", port
                )
                asyncio.create_task(self.page.protocol_socket.serve_forever())
                break
            except OSError:
                continue

    async def protocol_handler(self, reader, _):
        raw_data = await reader.read(2048)
        data = json.loads(raw_data.decode())
        if data:
            uri = urlparse(data[0])
            if uri.scheme == "rtt":
                params = {
                    k: v
                    for kv in uri.query.split("&")
                    for k, v in re.findall(r"^(.*?)=(.*?)$", kv)
                }
                await self.page.go_async(uri.path, **params)

    def setup_logging(self, web=False):
        self.page.logger = Logger("Trove Builds Core")
        if not web:
            for file in self.logs_folder.glob("*.log"):
                file.unlink()

    def setup_localization(self):
        LocalizationManager(self.page).update_all_translations()
        self.page.logger.info("Updated localization strings")

    async def setup_page(self):
        self.page.title = self.page.metadata.name
        self.page.window_min_width = 1630
        self.page.window_min_height = 950
        width = self.page.preferences.window_size[0]
        height = self.page.preferences.window_size[1]
        if width < self.page.window_min_width:
            width = self.page.window_min_width
        if height < self.page.window_min_height:
            height = self.page.window_min_height
        self.page.preferences.window_size = (width, height)
        self.page.preferences.save()
        self.page.window_width = width
        self.page.window_height = height
        self.page.window_maximized = self.page.preferences.fullscreen
        self.page.snack_bar = Snackbar(page=self.page)
        self.page.clock = Text(str(self.page.trove_time))
        self.page.on_error = self.renderer_error_logger
        self.page.on_window_event = self.window_event
        self.page.dialog = Modal(page=self.page)

    async def window_event(self, e):
        if e.data == "maximize":
            self.page.preferences.fullscreen = True
        elif e.data == "unmaximize":
            self.page.preferences.fullscreen = False
        elif e.data == "resized":
            width = self.page.window_width
            height = self.page.window_height
            self.page.preferences.window_size = (width, height)
        self.page.preferences.save()

    async def renderer_error_logger(self, e):
        self.page.logger.error(e.data)

    async def process_login(self):
        token = await self.page.client_storage.get_async("rnt-token")
        self.page.user_data = await self.login(token)
        await self.post_login()

    async def login(self, token):
        if token is None:
            return None
        response = requests.get(
            "https://kiwiapi.slynx.xyz/v1/user/discord/get?pass_key=" + token
        )
        if response.status_code == 200:
            await self.page.client_storage.set_async("rnt-token", token)
            return response.json()
        return None

    async def display_login_screen(self, _):
        await self.page.go_async("/login")

    async def button_hover(self, e):
        if e.data == "true":
            e.control.ink = True
        else:
            e.control.ink = False
        await e.control.update_async()

    async def execute_login_discord(self, e):
        await self.page.launch_url_async(
            "https://kiwiapi.slynx.xyz/v1/user/discord/login"
        )

    async def execute_login_trovesaurus(self, e):
        await self.page.launch_url_async("https://trovesaurus.com/profile")

    async def execute_logout(self, e):
        await self.page.client_storage.remove_async("rnt-token")
        await self.stop_tasks()
        await self.process_login()

    async def post_login(self, route=None):
        await self.setup_appbar()
        await self.start_tasks()

        data = sys.argv[1:]
        if data:
            uri = urlparse(data[0])
            if uri.scheme == "rtt":
                params = {
                    k: v
                    for kv in uri.query.split("&")
                    for k, v in re.findall(r"^(.*?)=(.*?)$", kv)
                }
            else:
                params = {}
            await self.page.go_async(uri.path, **params)
        else:
            await self.page.go_async(route or "/mods_manager")

    async def setup_appbar(self):
        if self.page.appbar:
            if self.page.appbar.check_updates.is_running():
                self.page.appbar.check_updates.cancel()
        self.page.appbar = CustomAppBar(
            page=self.page,
            title=Text(self.page.metadata.app_name),
            leading=Row(controls=[Icon("Star"), self.page.clock]),
        )

    async def close_dialog(self, e=None):
        await self.page.dialog.hide()

    async def gather_views(self):
        self.page.all_views = []
        self.page.all_views.extend(all_views(self.page.web))
        Routing(self.page, self.page.all_views)

    async def start_tasks(self):
        if self.update_clock.is_running():
            self.update_clock.cancel()
        try:
            self.update_clock.start()
        except RuntimeError:
            ...

    async def stop_tasks(self):
        if self.update_clock.is_running():
            self.update_clock.cancel()

    @tasks.loop(seconds=60)
    async def update_clock(self):
        self.page.clock.value = str(self.page.trove_time)
        try:
            await self.page.clock.update_async()
        except Exception:
            ...

    @update_clock.before_loop
    async def sync_clock(self):
        now = datetime.now()
        await asyncio.sleep(60 - now.second)


if __name__ == "__main__":
    APP = App()
    APP.run()
