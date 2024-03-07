import asyncio
from datetime import datetime, timedelta

from flet import (
    Text,
    Column,
    Container,
    ResponsiveRow,
    Image,
    Stack,
    TextStyle,
    LinearGradient,
    alignment,
    Tooltip,
    Border,
    BorderSide,
    BlendMode,
    Row,
    MainAxisAlignment,
)
from pytz import UTC

from models.interface import Controller
from utils import tasks


class Widget(Container):
    def __init__(self, controls: list = [], **kwargs):
        super().__init__(
            content=Column(
                controls=[*controls],
                horizontal_alignment="center",
            ),
            on_hover=None,
            **kwargs
        )


class RowWidget(Container):
    def __init__(self, controls: list = [], **kwargs):
        super().__init__(
            content=Row(
                controls=[*controls],
                vertical_alignment="center",
                alignment=MainAxisAlignment.SPACE_BETWEEN,
            ),
            on_hover=None,
            **kwargs
        )


class HomeController(Controller):
    def setup_controls(self):
        if not hasattr(self, "widgets"):
            self.widgets = ResponsiveRow(spacing=0, vertical_alignment="start")
            self.daily_data = self.page.data_files["daily_buffs.json"]
            self.weekly_data = self.page.data_files["weekly_buffs.json"]
            self.date = Text("Trove Time", size=20, col={"xxl": 6})
        self.daily_widgets = ResponsiveRow(
            controls=[
                RowWidget(
                    data=k,
                    controls=[
                        Tooltip(
                            message="\n".join(
                                [
                                    "Normal",
                                    *[" \u2022 " + b for b in v["normal_buffs"]],
                                    "Patreon",
                                    *[" \u2022 " + b for b in v["premium_buffs"]],
                                ]
                            ),
                            content=Stack(
                                controls=[
                                    Image(
                                        color="black",
                                        color_blend_mode=BlendMode.SATURATION,
                                        src=v["banner"],
                                        left=-125,
                                    ),
                                    Container(
                                        gradient=LinearGradient(
                                            begin=alignment.center_left,
                                            end=alignment.center_right,
                                            colors=[
                                                "#ff000000",
                                                "#00000000",
                                            ],
                                        ),
                                        width=200,
                                        height=46,
                                    ),
                                    Text(
                                        v["weekday"],
                                        color="#cccccc",
                                        left=10,
                                        top=3,
                                        size=16,
                                    ),
                                    Text(
                                        v["name"],
                                        color="#cccccc",
                                        left=10,
                                        top=23,
                                    ),
                                ]
                            ),
                            border_radius=10,
                            bgcolor="#1E1E28",
                            text_style=TextStyle(color="#cccccc"),
                            border=Border(
                                BorderSide(width=2, color="#" + v["color"]),
                                BorderSide(width=2, color="#" + v["color"]),
                                BorderSide(width=2, color="#" + v["color"]),
                                BorderSide(width=2, color="#" + v["color"]),
                            ),
                            prefer_below=False,
                            wait_duration=250,
                        )
                    ],
                    col=12 / 7,
                )
                for k, v in self.daily_data.items()
            ],
        )
        self.weekly_widgets = ResponsiveRow(
            controls=[
                RowWidget(
                    data=k,
                    controls=[
                        Tooltip(
                            message="\n".join(
                                ["Buffs", *[" \u2022 " + b for b in v["buffs"]]]
                            ),
                            content=Stack(
                                controls=[
                                    Image(
                                        color="black",
                                        color_blend_mode=BlendMode.SATURATION,
                                        src=v["banner"],
                                    ),
                                    Container(
                                        gradient=LinearGradient(
                                            begin=alignment.center_left,
                                            end=alignment.center_right,
                                            colors=[
                                                "#ff000000",
                                                "#00000000",
                                            ],
                                        ),
                                        width=200,
                                        height=182,
                                    ),
                                    Text(
                                        v["name"],
                                        color="#cccccc",
                                        size=16,
                                        left=10,
                                        top=3,
                                    ),
                                ]
                            ),
                            border_radius=10,
                            bgcolor="#1E1E28",
                            text_style=TextStyle(color="#cccccc"),
                            border=Border(
                                BorderSide(width=2, color="#" + v["color"]),
                                BorderSide(width=2, color="#" + v["color"]),
                                BorderSide(width=2, color="#" + v["color"]),
                                BorderSide(width=2, color="#" + v["color"]),
                            ),
                            prefer_below=False,
                            wait_duration=250,
                        )
                    ],
                    col={"xxl": 3},
                )
                for k, v in self.weekly_data.items()
            ],
        )
        self.widgets.controls = [
            Column(controls=[self.daily_widgets, self.weekly_widgets], col={"xxl": 12}),
        ]
        tasks = [
            self.update_daily,
            self.update_weekly,
        ]
        for task in tasks:
            if not task.is_running():
                task.start()

    def setup_events(self): ...

    @tasks.loop(seconds=1)
    async def update_clock(self):
        try:
            now = datetime.utcnow() - timedelta(hours=11)
            self.date.value = now.strftime("%Y-%m-%d")
            self.clock.value = now.strftime("%H:%M:%S")
            await self.date.update_async()
            await self.clock.update_async()
        except AssertionError:
            ...
        except Exception as e:
            print(e)

    @tasks.loop(seconds=60)
    async def update_daily(self):
        while True:
            try:
                now = datetime.utcnow() - timedelta(hours=11)
                for control in self.daily_widgets.controls:
                    stack = control.content.controls[0].content
                    if int(control.data) == now.weekday():
                        stack.controls[0].color = None
                        stack.controls[0].color_blend_mode = None
                    else:
                        stack.controls[0].color = "black"
                        stack.controls[0].color_blend_mode = BlendMode.SATURATION
                await self.daily_widgets.update_async()
            except AssertionError:
                await asyncio.sleep(1)
                continue
            except Exception as e:
                print(e)
            await asyncio.sleep(3)
            break

    @tasks.loop(seconds=60)
    async def update_weekly(self):
        while True:
            try:
                initial = datetime(2020, 3, 23, tzinfo=UTC) - timedelta(hours=11)
                now = datetime.utcnow() - timedelta(hours=11)
                week_length = 60 * 60 * 24 * 7
                weeks = (now.timestamp() - initial.timestamp()) // week_length
                time_split = weeks / 4
                time_find = (time_split - int(time_split)) * 4
                for control in self.weekly_widgets.controls:
                    stack = control.content.controls[0].content
                    if int(control.data) == int(time_find):
                        stack.controls[0].color = None
                        stack.controls[0].color_blend_mode = None
                    else:
                        stack.controls[0].color = "black"
                        stack.controls[0].color_blend_mode = BlendMode.SATURATION
                await self.weekly_widgets.update_async()
            except AssertionError:
                await asyncio.sleep(1)
                continue
            except Exception as e:
                print(e)
            await asyncio.sleep(3)
            break
