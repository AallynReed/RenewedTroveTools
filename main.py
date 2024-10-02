from utils.logger import Logger, log
import logging
from models import Metadata, Preferences
from utils.path import BasePath

metadata = Metadata.load_from_file(BasePath.joinpath("data/metadata.json"))
level = logging.DEBUG if metadata.dev else logging.INFO
Logger("Core", level=level)
Logger("Routing", level=level)
Logger("Traffic", level=level)
Logger("Network", level=level)
Logger("Tasks", level=level)
Logger("TMod Parser", level=level)
Logger("Testing", level=level)

#####

import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import shutil

if os.name == "nt":
    import win32gui
    import win32con
    import pystray
    import win11toast
from PIL import Image
import threading

import requests
from flet import app_async, AppView, Theme, Row, Text, Icon
from models.constants import fetch_files
from models.interface import CustomAppBar
from models.interface.controls import Snackbar, Modal
from utils import tasks

from utils.protocol import set_protocol
from utils.routing import Routing
from utils.trove.server_time import ServerTime
from views import all_views
from utils.kiwiapi import KiwiAPI
from utils import locale
from utils.trove.registry import add_to_startup, remove_from_startup
from persistent import AsyncFileEventHandler
from watchdog.observers import Observer
from tasks import events


if getattr(sys, "frozen", False):
    os.chdir(Path(sys.executable).parent)

MINIMIZED = "--minimized" in sys.argv
if MINIMIZED:
    sys.argv.remove("--minimized")


class App:
    def __init__(self, web=False):
        self.web = web

    def run(self, port: int = 0):
        self.loop = asyncio.get_event_loop()
        tray_thread = threading.Thread(
            target=self.run_tray_icon, args=(self.loop,), daemon=True
        )
        tray_thread.start()
        self.loop.run_until_complete(
            app_async(
                target=self.start,
                assets_dir="assets",
                view=AppView.WEB_BROWSER if self.web else AppView.FLET_APP,
                port=port,
            )
        )

    async def start(self, page):
        self.page = page
        self.page.send_notification = self.send_notification
        self.page.RTT = self
        if page.web:
            await self.start_web()
        else:
            await self.start_app()

    async def start_app(self):
        set_protocol()
        self.setup_folders()
        await self.load_configurations()
        await self.load_constants()
        await self.setup_protocol_socket()
        self.setup_localization()
        await self.setup_page()
        await self.gather_views()
        await self.handshake_api()
        await self.process_login()
        if os.name == "nt":
            events.event_receiver.start(self.page)
            if MINIMIZED:
                await asyncio.sleep(2)
                await self.hide_window()

    async def start_web(self):
        self.setup_folders()
        await self.load_configurations()
        await self.load_constants()
        self.setup_localization()
        await self.setup_page()
        await self.gather_views()
        await self.process_login()

    async def monitor_directory(self, path, loop):
        event_handler = AsyncFileEventHandler(self.page, loop)
        observer = Observer()
        observer.schedule(event_handler, path, recursive=False)
        observer.start()
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

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
            # Rebrand old folder
            old_dir = APPDATA.joinpath("Sly")
            try:
                if old_dir.exists() and old_dir.is_dir():
                    old_dir.rename(old_dir.parent.joinpath("Aallyn"))
            except FileExistsError:
                shutil.rmtree(old_dir)
            old_dir = APPDATA.joinpath("Trove/sly.dev")
            try:
                if old_dir.exists() and old_dir.is_dir():
                    old_dir.rename(old_dir.parent.joinpath("aallyn"))
            except FileExistsError:
                shutil.rmtree(old_dir)
            self.app_data = APPDATA.joinpath("Trove/aallyn").joinpath(
                self.page.metadata.tech_name
            )
            self.logs_folder = self.app_data.joinpath("logs")
            self.logs_folder.mkdir(parents=True, exist_ok=True)
            self.app_data.mkdir(parents=True, exist_ok=True)
            # Watch CFG edits
            asyncio.create_task(
                self.monitor_directory(APPDATA.joinpath("Trove/ModCfgs"), self.loop)
            )

    async def load_configurations(self):
        self.page.user_data = None
        self.page.trove_time = ServerTime(self.page)
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
        await fetch_files()

    async def setup_protocol_socket(self):
        opened = False
        for port in range(13010, 13020):
            try:
                self.page.protocol_socket = await asyncio.start_server(
                    self.protocol_handler, "127.0.0.1", port
                )
                asyncio.create_task(self.page.protocol_socket.serve_forever())
                opened = True
                log("Network").info("Started protocol socket at %s" % port)
                break
            except OSError:
                continue
        if not opened:
            await self.page.window_close_async()

    async def protocol_handler(self, reader, _):
        raw_data = await reader.read(2048)
        data = json.loads(raw_data.decode())
        log("Network").debug("Received data from protocol socket: %s" % data)
        if data:
            uri = urlparse(data[0])
            if uri.scheme == "rtt":
                params = {
                    k: v
                    for kv in uri.query.split("&")
                    for k, v in re.findall(r"^(.*?)=(.*?)$", kv)
                }
                await self.page.go_async(uri.path, **params)

    def setup_localization(self):
        locale.ENGINE.load_locale_translations()
        locale.ENGINE.locale = self.page.preferences.locale
        log("Core").info("Updated localization strings")

    async def setup_page(self):
        self.page.fonts = {"Open Sans": "/fonts/Google Sans.ttf"}
        self.page.theme = Theme(font_family="Product Sans")
        self.page.title = self.page.metadata.name
        self.page.window_prevent_close = True
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
        self.page.api = KiwiAPI()

    async def window_event(self, e):
        if e.data == "maximize":
            self.page.preferences.fullscreen = True
        elif e.data == "unmaximize":
            self.page.preferences.fullscreen = False
        elif e.data == "resized":
            width = self.page.window_width
            height = self.page.window_height
            self.page.preferences.window_size = (width, height)
        elif e.data == "close":
            await self.hide_window()
        self.page.preferences.save()

    async def renderer_error_logger(self, e):
        log("Core").error(e.data)

    async def process_login(self, logout=False):
        token = await self.page.client_storage.get_async("rnt-token")
        self.page.user_data = await self.login(token)
        if self.page.user_data:
            self.page.is_admin = self.page.user_data["is_admin"]
        else:
            self.page.is_admin = False
        await self.post_login(logout=logout)

    async def login(self, token):
        if token is None:
            return None

        headers = {"User-Agent": f"RenewedTroveTools/{self.page.metadata.version}"}
        try:
            response = requests.get(
                "https://kiwiapi.aallyn.xyz/v1/user/discord/get?pass_key=" + token,
                timeout=5,
                headers=headers,
            )
            if response.status_code != 200:
                return None
            await self.page.client_storage.set_async("rnt-token", token)
            return response.json()
        except requests.Timeout:
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
            "https://kiwiapi.aallyn.xyz/v1/user/discord/login"
        )

    async def execute_login_trovesaurus(self, e):
        await self.page.launch_url_async("https://trovesaurus.com/profile")

    async def execute_logout(self, e):
        await self.page.client_storage.remove_async("rnt-token")
        await self.stop_tasks()
        await self.process_login(logout=True)

    async def post_login(self, route=None, logout=False):
        await self.setup_appbar()
        await self.start_tasks()

        data = sys.argv[1:]
        if data and not logout:
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
            if logout:
                return await self.page.go_async("/")
            await self.page.go_async(route or "/")

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
        self.page.all_views.extend(all_views(self.page, self.page.web))
        Routing(self.page, self.page.all_views)

    async def handshake_api(self):
        await self.page.api.handshake(self.page)

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

    async def restart(self):
        await self.stop_tasks()
        await self.setup_appbar()
        await self.page.go_async("/test")
        await self.page.go_async("/")

    async def hide_window(self):
        try:
            hwnd = win32gui.FindWindow(None, "Renewed Trove Tools")
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            await self.send_notification(
                "Renewed Trove Tools",
                "The app is running in the background, close it from the tray icon.",
                "System Tray",
            )
        except ValueError:
            ...

    async def unhide_window(self):
        try:
            hwnd = win32gui.FindWindow(None, "Renewed Trove Tools")
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        except ValueError:
            ...
        await asyncio.sleep(2)
        await self.page.window_to_front()

    async def close_window(self):
        await self.page.window_destroy()

    def create_image(self):
        image = Image.open("assets/x48.png")
        return image

    def quit_app(self, icon, item):
        icon.stop()
        asyncio.run_coroutine_threadsafe(self.close_window(), self.loop)

    def show_app(self, *args, **kwargs):
        asyncio.run_coroutine_threadsafe(self.unhide_window(), self.loop)

    def run_tray_icon(self, loop):
        if os.name == "nt":
            self.icon = pystray.Icon(
                "Renewed Trove Tools",
                self.create_image(),
                menu=pystray.Menu(
                    pystray.MenuItem("Show", self.show_app, default=True),
                    pystray.MenuItem("Quit", self.quit_app),
                ),
            )
            self.icon.run()
        threading.Thread(
            target=loop.run_forever, name="Renewed Trove Tools", daemon=True
        ).start()

    async def send_notification(self, title, message, type, url=None):
        notification_settings = self.page.preferences.notifications
        enabled = notification_settings.enabled
        duration = notification_settings.duration
        sound = notification_settings.sound
        for notification_setting in notification_settings.notifications:
            if notification_setting.name.value == type:
                if sound:
                    sound = notification_setting.sound
                if enabled:
                    enabled = notification_setting.enabled
        if not enabled:
            return
        sound = str(sound).lower()
        ico_path = Path("assets/x256.png").absolute()
        button = None
        if url is not None:
            button = {
                "activationType": "protocol",
                "arguments": url[1],
                "content": url[0],
            }
        try:
            await win11toast.toast_async(
                title,
                message,
                icon={
                    "src": str(ico_path),
                    "placement": "appLogoOverride",
                },
                button=button,
                duration=duration or None,
                app_id="Renewed Trove Tools",
                on_click=self.show_app,
                audio={"silent": sound},
            )
        except Exception as e:
            print(e)

    async def add_start_with_windows(self):
        add_to_startup(sys.executable, "Renewed Trove Tools", "--minimized")

    async def remove_start_with_windows(self):
        remove_from_startup("Renewed Trove Tools")


if __name__ == "__main__":
    APP = App()
    APP.run()
