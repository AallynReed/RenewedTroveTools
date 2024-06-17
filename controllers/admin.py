import asyncio
import json
import traceback
from datetime import datetime
from pathlib import Path
from time import perf_counter

from flet import (
    Column,
    ResponsiveRow,
    Row,
    Switch,
    Text,
    TextField,
    DataTable,
    DataColumn,
    IconButton,
    ElevatedButton,
    ProgressBar,
    Dropdown,
    dropdown,
    DataRow,
    DataCell,
    MainAxisAlignment,
    FilePicker,
    Card,
)
from utils.locale import loc
from flet_core import icons
from humanize import naturalsize
from yaml import dump

from models.interface import Controller
from models.interface.inputs import PathField
from utils import tasks
from utils.functions import long_throttle, throttle
from utils.trove.extractor import find_all_indexes, FileStatus
from utils.trove.registry import get_trove_locations


class AdminController(Controller):
    def setup_controls(self):
        if not hasattr(self.page, "main"):
            self.main = ResponsiveRow(alignment=MainAxisAlignment.START)
            asyncio.create_task(self.build_admin_panel())

    def setup_events(self): ...

    async def build_admin_panel(self):
        self.main.controls.append(
            Column(controls=[Text("Still building this shit")], col=4)
        )
        await self.main.update_async()
