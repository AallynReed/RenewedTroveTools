import asyncio
from datetime import datetime, timedelta
from utils.kiwiapi import KiwiAPI

from flet import (
    Text,
    TextButton,
    Column,
    Divider,
    Container,
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
    CrossAxisAlignment,
    Card,
    ProgressBar,
    colors,
    padding,
    TextSpan
)
from pytz import UTC
import humanize
from models.interface import Controller
from utils import tasks
from utils.trove.mastery import points_to_mr


class HomeController(Controller):
    def setup_controls(self):
        if not hasattr(self, "widgets"):
            self.api = KiwiAPI()
            self.main = Column(expand=True)
            self.daily_data = self.page.data_files["daily_buffs.json"]
            self.weekly_data = self.page.data_files["weekly_buffs.json"]
            self.date = Text("Trove Time", size=20, col={"xxl": 6})
        asyncio.create_task(self.post_setup())

    async def post_setup(self):
        self.daily_widgets = Column(
            controls=[
                Tooltip(
                    data=k,
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
                                scale=1.5,
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
                                width=300,
                                height=55,
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
                        ],
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
                for k, v in self.daily_data.items()
            ],
            spacing=0
        )
        self.weekly_widgets = Row(
            controls=[
                Tooltip(
                    data=k,
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
                for k, v in self.weekly_data.items()
            ],
            alignment=MainAxisAlignment.CENTER,
        )
        mastery_data = await self.api.get_mastery()
        x, y, z = points_to_mr(mastery_data["normal"]["live"])
        live = {
            "points": mastery_data["normal"]["live"],
            "level": x,
            "remaining": y,
            "needed": z,
            "percentage": round(y / z, 2)
        }
        x, y, z = points_to_mr(mastery_data["geode"]["live"])
        geode = {
            "points": mastery_data["geode"]["live"],
            "level": x,
            "remaining": y,
            "needed": z,
            "percentage": round(y / z, 2)
        }
        self.live_mastery_widgets = Row(
            controls=[
                Card(
                    content=Container(
                        Column(
                            controls=[
                                Text("Live Trove Mastery", size=20),
                                Text(
                                    f"{live['level']}",
                                    spans=[
                                        TextSpan(
                                            text=f"  ({live['points']:,})",
                                            style=TextStyle(size=11)
                                        )
                                    ],
                                    size=16,
                                ),
                                ProgressBar(
                                    width=200,
                                    value=live['percentage'],
                                    color=colors.BLUE_500,
                                    bar_height=10
                                ),
                                Row(
                                    controls=[
                                        Text(live['remaining']),
                                        Text(f"{round(live['percentage'] * 100, 2)}%"),
                                        Text(live['needed'])
                                    ],
                                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                                    width=180
                                )
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER
                        ),
                        padding=padding.symmetric(10, 10)
                    )
                ),
                Card(
                    content=Container(
                        Column(
                            controls=[
                                Text("Live Geode Mastery", size=20),
                                Text(
                                    f"{geode['level']}",
                                    spans=[
                                        TextSpan(
                                            text=f"  ({geode['points']:,})",
                                            style=TextStyle(size=11)
                                        )
                                    ],
                                    size=16,
                                ),
                                ProgressBar(
                                    width=200,
                                    value=geode['percentage'],
                                    color=colors.BLUE_500,
                                    bar_height=10
                                ),
                                Row(
                                    controls=[
                                        Text(geode['remaining']),
                                        Text(f"{round(geode['percentage'] * 100, 2)}%"),
                                        Text(geode['needed'])
                                    ],
                                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                                    width=180
                                )
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER
                        ),
                        padding=padding.symmetric(10, 10)
                    ),
                )
            ]
        )
        x, y, z = points_to_mr(mastery_data["normal"]["live"])
        live = {
            "points": mastery_data["normal"]["live"],
            "level": x,
            "remaining": y,
            "needed": z,
            "percentage": round(y / z, 2)
        }
        x, y, z = points_to_mr(mastery_data["geode"]["live"])
        geode = {
            "points": mastery_data["geode"]["live"],
            "level": x,
            "remaining": y,
            "needed": z,
            "percentage": round(y / z, 2)
        }
        self.pts_mastery_widgets = Row(
            controls=[
                Card(
                    content=Container(
                        Column(
                            controls=[
                                Text("PTS Trove Mastery", size=20),
                                Text(
                                    f"{live['level']}",
                                    spans=[
                                        TextSpan(
                                            text=f"  ({live['points']:,})",
                                            style=TextStyle(size=11)
                                        )
                                    ],
                                    size=16,
                                ),
                                ProgressBar(
                                    width=200,
                                    value=live['percentage'],
                                    color=colors.BLUE_500,
                                    bar_height=10
                                ),
                                Row(
                                    controls=[
                                        Text(live['remaining']),
                                        Text(f"{round(live['percentage'] * 100, 2)}%"),
                                        Text(live['needed'])
                                    ],
                                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                                    width=180
                                )
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER
                        ),
                        padding=padding.symmetric(10, 10)
                    )
                ),
                Card(
                    content=Container(
                        Column(
                            controls=[
                                Text("PTS Geode Mastery", size=20),
                                Text(
                                    f"{geode['level']}",
                                    spans=[
                                        TextSpan(
                                            text=f"  ({geode['points']:,})",
                                            style=TextStyle(size=11)
                                        )
                                    ],
                                    size=16,
                                ),
                                ProgressBar(
                                    width=200,
                                    value=geode['percentage'],
                                    color=colors.BLUE_500,
                                    bar_height=10
                                ),
                                Row(
                                    controls=[
                                        Text(geode['remaining']),
                                        Text(f"{round(geode['percentage'] * 100, 2)}%"),
                                        Text(geode['needed'])
                                    ],
                                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                                    width=180
                                )
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER
                        ),
                        padding=padding.symmetric(10, 10)
                    )
                )
            ]
        )
        self.luxion = Card()
        self.corruxion = Card()
        self.dragons = Row(
            controls=[
                self.luxion,
                self.corruxion
            ]
        )
        self.widgets = Row(
            controls=[
                Container(
                    content=Column(
                        controls=[
                            Row(
                                controls=[
                                    self.live_mastery_widgets,
                                    self.pts_mastery_widgets
                                ]
                            ),
                            self.dragons
                        ]
                    ),
                    expand=True
                ),
                self.daily_widgets,
            ],
            alignment=MainAxisAlignment.END,
            vertical_alignment="start",
        )
        self.main.controls = [
            Column(controls=[self.weekly_widgets, Divider(), self.widgets], expand=True),
        ]
        tasks = [
            self.update_daily,
            self.update_weekly,
            self.update_luxion,
            self.update_corruxion,
        ]
        for task in tasks:
            if not task.is_running():
                task.start()
        await self.main.update_async()

    def setup_events(self): ...

    @tasks.loop(seconds=60)
    async def update_daily(self):
        while True:
            try:
                now = datetime.utcnow() - timedelta(hours=11)
                for control in self.daily_widgets.controls:
                    stack = control.content
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
                    stack = control.content
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

    @tasks.loop(seconds=60)
    async def update_luxion(self):
        try:
            trove_time = self.page.trove_time
            luxion = trove_time.first_luxion
            image = Image(
                src="assets/images/dragons/lux.png",
                width=50,
                height=50
            )
            self.luxion.content = Container(
                Column(
                    controls=[
                        image,
                        TextButton(
                            content=Text("Luxion", size=20),
                            url="https://trovesaurus.com/luxion",
                        ),
                    ],
                    horizontal_alignment=CrossAxisAlignment.CENTER
                ),
                padding=padding.all(10),
            )
            if trove_time.is_dragon(luxion):
                self.luxion.content.content.controls.append(
                    Text(
                        "Leaving " +
                        humanize.naturaltime(-trove_time.until_end_dragon(luxion))
                    )
                )
            else:
                image.color = "black"
                image.color_blend_mode = BlendMode.SATURATION
                self.luxion.content.content.controls.append(
                    Text(
                        "Arriving " +
                        humanize.naturaltime(-trove_time.until_next_dragon(luxion))
                    )
                )
            await self.luxion.update_async()
        except Exception as e:
            print(e)

    @tasks.loop(seconds=60)
    async def update_corruxion(self):
        try:
            trove_time = self.page.trove_time
            corruxion = trove_time.first_corruxion
            image = Image(
                src="assets/images/dragons/nlux.png",
                width=50,
                height=50
            )
            self.corruxion.content = Container(
                Column(
                    controls=[
                        image,
                        TextButton(
                            content=Text("Corruxion", size=20),
                            url="https://trovesaurus.com/corruxion",
                        ),
                    ],
                    horizontal_alignment=CrossAxisAlignment.CENTER
                ),
                padding=padding.all(10),
            )
            if trove_time.is_dragon(corruxion):
                self.corruxion.content.content.controls.append(
                    Text(
                        "Leaving " +
                        humanize.naturaltime(-trove_time.until_end_dragon(corruxion))
                    )
                )
            else:
                image.color = "black"
                image.color_blend_mode = BlendMode.SATURATION
                self.corruxion.content.content.controls.append(
                    Text(
                        "Arriving " +
                        humanize.naturaltime(-trove_time.until_next_dragon(corruxion))
                    )
                )
            await self.corruxion.update_async()
        except Exception as e:
            print(e)
