import asyncio

from flet import (
    ElevatedButton,
    TextButton,
    Stack,
    Row,
    Column,
    Card,
    Text,
    ResponsiveRow,
    canvas,
    Paint,
    PaintingStyle,
    DataTable,
    DataColumn,
    DataRow,
    DataCell,
    Divider,
    Dropdown,
    dropdown,
    ButtonStyle,
    MaterialState,
    BorderSide,
    TextField,
    Switch,
)
from utils.locale import loc

from models.constants import files_cache
from models.interface import Controller
from models.interface.decorative_button import RTTIconDecoButton


class MaxStatsController(Controller):
    def setup_controls(self):
        self.interface = ResponsiveRow()
        self.max_power_rank_stats = files_cache["stats/max_power_rank.json"]
        self.max_light_stats = files_cache["stats/max_light.json"]
        self.max_light_stats.sort(key=lambda x: (x["perm"], x["value"]), reverse=True)
        self.interface.controls.append(self.get_max_power_rank_interface())
        self.interface.controls.append(self.get_max_light_interface())

    def get_max_power_rank_interface(self):
        mprb = Column(expand=True)
        mprb.controls.append(Text(loc("Max Power Rank") + " (Coming Soon)", size=24))
        return Card(mprb, expand=True, col=6)

    def get_max_light_interface(self):
        mlb = Column(expand=True)
        mlb.controls.append(
            Row(controls=[Text(loc("Max Light"), size=24)], alignment="center")
        )
        self.mlbi = Column(spacing=0)
        total = 0
        for x in self.max_light_stats:
            x["enabled"] = x.get("enabled", x["perm"])
            value = abs(x["value"])
            if value < 1:
                if x["enabled"]:
                    total *= 1 + x["value"]
                value = int(x["value"] * 100)
                value = f"{value}%"
            else:
                if x["enabled"]:
                    total += x["value"]
                value = str(value)
            self.mlbi.controls.append(
                Row(
                    controls=[
                        Switch(
                            data=x,
                            value=x["enabled"],
                            on_change=self.update_light_point,
                        ),
                        RTTIconDecoButton(
                            image="https://trovesaurus.com/images/logos/Sage_64.png?1"
                        ),
                        TextButton(value, width=70),
                        Text(loc(x["name"])),
                    ]
                )
            )
        mlb.controls.append(self.mlbi)
        self.total_light = Text(str(round(total)), size=24)
        mlb.controls[0].controls.append(self.total_light)
        return Card(mlb, expand=True, col=6)

    async def update_light_point(self, event):
        event.control.data["enabled"] = event.control.value
        self.interface.controls.clear()
        self.interface.controls.append(self.get_max_power_rank_interface())
        self.interface.controls.append(self.get_max_light_interface())
        await self.interface.update_async()

    def setup_events(self): ...
