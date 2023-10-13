import asyncio
import logging
import os
import sys
from datetime import datetime
from datetime import timedelta
from pathlib import Path

from flet import app, WEB_BROWSER, FLET_APP, Theme, SnackBar, Row, Icon, Text

from models import Metadata, Preferences
from models.interface import CustomAppBar
from utils import tasks
from utils.localization import LocalizationManager
from utils.logger import Logger
from utils.routing import Routing
from views import all_views, View404


class App:
    def __init__(self, web=False):
        self.web = web

    def run(self):
        app(
            target=self.start,
            assets_dir="assets",
            view=WEB_BROWSER if self.web else FLET_APP,
            port=13010
        )

    async def start(self, page):
        self.page = page
        await self.load_configurations()
        self.setup_logging()
        self.setup_localization()
        await self.setup_page()
        await self.setup_appbar()
        await self.gather_views()
        await self.start_tasks()
        await page.go_async("/")

    async def load_configurations(self):
        self.page.metadata = Metadata.load_from_file(Path("data/metadata.json"))
        APPDATA = Path(os.environ.get("APPDATA"))
        app_data = APPDATA.joinpath("Trove/sly.dev").joinpath(self.page.metadata.tech_name)
        self.page.preferences = Preferences.load_from_json(app_data.joinpath("preferences.json"))
        self.page.theme_mode = self.page.preferences.theme
        self.page.theme = Theme(color_scheme_seed=str(self.page.preferences.accent_color))

    def setup_logging(self):
        self.page.logger = Logger("Trove Builds Core")
        APPDATA = Path(os.environ.get("APPDATA"))
        app_data = APPDATA.joinpath("Trove/sly.dev").joinpath(self.page.metadata.tech_name)
        logs = app_data.joinpath("logs")
        logs.mkdir(parents=True, exist_ok=True)
        latest_log = logs.joinpath("latest.log")
        latest_log.unlink(missing_ok=True)
        dated_log = logs.joinpath(datetime.now().strftime("%Y-%m-%d %H-%M-%S.log"))
        targets = (
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(latest_log),
            logging.FileHandler(dated_log),
        )
        logging.basicConfig(format="%(message)s", level=logging.INFO, handlers=targets)

    def setup_localization(self):
        LocalizationManager(self.page).update_all_translations()
        self.page.logger.info("Updated localization strings")

    async def setup_page(self):
        self.page.title = self.page.metadata.app_name
        self.page.window_min_width = 1630
        self.page.window_min_height = 950
        self.page.window_width = 1630
        self.page.window_height = 950
        self.page.snack_bar = SnackBar(content=Text())
        self.page.clock = Text(
            (datetime.utcnow() - timedelta(hours=11)).strftime("%a, %b %d\t\t%H:%M")
        )

    async def setup_appbar(self):
        self.page.appbar = CustomAppBar(
            page=self.page,
            leading=Row(controls=[Icon("Star"), self.page.clock]),
        )

    async def gather_views(self):
        self.page.all_views = []
        self.page.all_views.extend(all_views(self.page.web))
        Routing(self.page, self.page.all_views, not_found=View404)

    async def start_tasks(self):
        self.update_clock.start()

    async def restart_app(self):
        ...

    @tasks.loop(seconds=60)
    async def update_clock(self):
        self.page.clock.value = (datetime.utcnow() - timedelta(hours=11)).strftime(
            "%a, %b %d\t\t%H:%M"
        )
        try:
            await self.page.clock.update_async()
        except Exception:
            ...

    @update_clock.before_loop
    async def sync_clock(self):
        now = datetime.utcnow()
        await asyncio.sleep(60 - now.second)


if __name__ == "__main__":
    APP = App()
    APP.run()
