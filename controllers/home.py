import asyncio
from datetime import datetime, UTC

import humanize
from aiohttp import ClientSession
from flet import (
    ListTile,
    Text,
    TextButton,
    Column,
    Divider,
    VerticalDivider,
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
    TextSpan,
    IconButton,
    Icon,
    icons,
    ButtonStyle,
    ResponsiveRow,
    TextField,
)
from sympy import sympify

from models.constants import files_cache
from models.interface import Controller
from models.interface import HomeWidget, RTTChip
from utils import tasks
from utils.kiwiapi import KiwiAPI
from utils.trove.mastery import points_to_mr


class HomeController(Controller):
    def setup_controls(self):
        if not hasattr(self, "widgets"):
            self.api = KiwiAPI()
            self.main = ResponsiveRow()
            self.daily_data = files_cache["daily_buffs.json"]
            self.weekly_data = files_cache["weekly_buffs.json"]
            self.date = Text("Trove Time", size=20, col={"xxl": 6})
        asyncio.create_task(self.post_setup())

    async def post_setup(self):
        self.streams_widget = HomeWidget(
            image="assets/icons/brands/twitch.png",
            title="Twitch Streams",
            title_size=20,
            title_url="https://www.twitch.tv/directory/category/trove",
            controls=[Text("Loading...")],
        )
        self.daily_widget = HomeWidget(
            icon=icons.CALENDAR_VIEW_DAY,
            title="Daily Bonuses",
            title_size=20,
            controls=[Text("Loading...")],
            column_spacing=0,
        )
        self.weekly_widget = HomeWidget(
            icon=icons.CALENDAR_VIEW_WEEK,
            title="Weekly Bonuses",
            title_size=20,
            controls=[Text("Loading...")],
        )
        self.events_widget = HomeWidget(
            icon=icons.EVENT,
            title="Events",
            title_size=20,
            controls=[Text("Loading...")],
        )
        self.dragons_widget = HomeWidget(
            icon=icons.STORE,
            title="Dragon Merchants",
            title_size=20,
            controls=[Text("Loading...")],
        )
        self.mastery_widget = HomeWidget(
            icon=icons.QUERY_STATS,
            title="Max Mastery",
            title_size=20,
            controls=[Text("Loading...")],
        )
        self.main.controls = [
            Column(
                controls=[
                    self.streams_widget,
                    Divider(height=1),
                    self.weekly_widget,
                    Divider(height=1),
                    ResponsiveRow(
                        controls=[
                            Row(
                                controls=[self.daily_widget, VerticalDivider()], col=2.5
                            ),
                            Column(
                                controls=[
                                    self.dragons_widget,
                                    Divider(height=1),
                                    self.mastery_widget,
                                ],
                                col=4.25,
                            ),
                            Row(
                                controls=[VerticalDivider(), self.events_widget],
                                col=5.25,
                            ),
                        ]
                    ),
                ],
                expand=True,
            )
        ]
        tasks = [
            self.update_twitch_streams,
            self.update_weekly,
            self.update_daily,
            self.update_dragons,
            self.update_mastery,
            self.update_events,
        ]
        for task in tasks:
            if not task.is_running():
                task.start()
        await self.main.update_async()

    def setup_events(self): ...

    @tasks.loop(seconds=60)
    async def update_daily(self):
        buffs = self.page.trove_time.daily_buffs
        current = self.page.trove_time.current_daily_buffs
        self.daily_widget.set_controls(
            [
                Tooltip(
                    vertical_offset=50,
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
                                color="black" if v != current else None,
                                color_blend_mode=(
                                    BlendMode.SATURATION if v != current else None
                                ),
                                src=v["banner"],
                                left=-125,
                            ),
                            Container(
                                gradient=LinearGradient(
                                    begin=alignment.center_left,
                                    end=alignment.center_right,
                                    colors=["#ff000000", "#00000000"],
                                ),
                                width=300,
                                height=55,
                            ),
                            Text(
                                v["weekday"], color="#cccccc", left=10, top=3, size=16
                            ),
                            Text(v["name"], color="#cccccc", left=10, top=23),
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
                for k, v in buffs.items()
            ]
        )
        await self.daily_widget.update_async()

    @tasks.loop(seconds=60)
    async def update_weekly(self):
        buffs = self.page.trove_time.weekly_buffs
        current = self.page.trove_time.current_weekly_buffs
        self.weekly_widget.set_controls(
            Row(
                controls=[
                    Tooltip(
                        data=k,
                        message="\n".join(
                            ["Buffs", *[" \u2022 " + b for b in v["buffs"]]]
                        ),
                        content=Stack(
                            controls=[
                                Image(
                                    color="black" if v != current else None,
                                    color_blend_mode=(
                                        BlendMode.SATURATION if v != current else None
                                    ),
                                    src=v["banner"],
                                    width=200,
                                ),
                                Container(
                                    gradient=LinearGradient(
                                        begin=alignment.center_left,
                                        end=alignment.center_right,
                                        colors=["#ff000000", "#00000000"],
                                    ),
                                    width=100,
                                    height=113,
                                ),
                                Text(
                                    v["name"], color="#cccccc", size=16, left=10, top=3
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
                    for k, v in buffs.items()
                ]
            )
        )
        await self.weekly_widget.update_async()

    @tasks.loop(seconds=60)
    async def update_dragons(self):
        trove_time = self.page.trove_time
        dragons = (
            ("Luxion", trove_time.first_luxion, "lux"),
            ("Corruxion", trove_time.first_corruxion, "nlux"),
        )
        dragon_controls = []
        for name, first, image_name in dragons:
            if trove_time.is_dragon(first):
                image_src = f"assets/images/dragons/{image_name}.png"
                text = Text(
                    "Leaving in "
                    + humanize.naturaltime(-trove_time.until_end_dragon(first)).replace(
                        " from now", ""
                    )
                )
            else:
                image_src = f"assets/images/dragons/{image_name}_out.png"
                text = Text(
                    "Arriving in "
                    + humanize.naturaltime(
                        -trove_time.until_next_dragon(first)
                    ).replace(" from now", "")
                )
            image = Image(src=image_src, width=40, height=40)
            dragon_control = Card(
                Container(
                    Column(
                        controls=[
                            image,
                            TextButton(
                                content=Text(name, size=20),
                                url=f"https://trovesaurus.com/{name.lower()}",
                                style=ButtonStyle(padding=padding.symmetric(0, 0)),
                            ),
                            text,
                        ],
                        horizontal_alignment=CrossAxisAlignment.CENTER,
                        spacing=0,
                    ),
                    padding=padding.symmetric(5, 15),
                )
            )
            dragon_controls.append(dragon_control)
        if trove_time.is_fluxion():
            image_src = "assets/images/dragons/fluxion.png"
            phase_text = "Voting" if trove_time.is_fluxion_voting() else "Selling"
            text = Text(
                "Leaving in "
                + humanize.naturaltime(-trove_time.until_end_fluxion()).replace(
                    " from now", ""
                )
            )
        else:
            image_src = "assets/images/dragons/fluxion_out.png"
            phase_text = "Voting" if trove_time.is_fluxion_selling() else "Selling"
            text = Text(
                "Arriving in "
                + humanize.naturaltime(-trove_time.until_next_fluxion()).replace(
                    " from now", ""
                )
            )
        image = Image(src=image_src, width=40, height=40)
        dragon_control = Card(
            Container(
                Column(
                    controls=[
                        image,
                        TextButton(
                            content=Text(f"[{phase_text}] Fluxion", size=20),
                            url="https://trovesaurus.com/fluxion/list",
                            style=ButtonStyle(padding=padding.symmetric(0, 0)),
                        ),
                        text,
                    ],
                    horizontal_alignment=CrossAxisAlignment.CENTER,
                    spacing=0,
                ),
                width=180,
                padding=padding.symmetric(5, 15),
            )
        )
        dragon_controls.append(dragon_control)
        self.dragons_widget.set_controls(
            Row(controls=dragon_controls, alignment=MainAxisAlignment.SPACE_AROUND)
        )
        await self.dragons_widget.update_async()

    @tasks.loop(seconds=60)
    async def update_twitch_streams(self):
        streams = await self.api.get_twitch_streams()
        self.streams_widget.set_controls(
            Row(
                controls=[
                    Container(
                        Column(
                            controls=[
                                Container(
                                    Stack(
                                        controls=[
                                            Image(
                                                src=stream["thumbnail_url"]
                                                .replace("{width}", "160")
                                                .replace("{height}", "90"),
                                                width=160,
                                                height=90,
                                            ),
                                            IconButton(
                                                content=Row(
                                                    controls=[
                                                        Icon(icons.VISIBILITY),
                                                        Text(
                                                            f"{stream['viewer_count']:,}"
                                                        ),
                                                    ]
                                                )
                                            ),
                                        ]
                                    ),
                                    url=f"https://twitch.tv/{stream['user_name']}",
                                ),
                                Tooltip(
                                    message=stream["title"],
                                    content=TextButton(
                                        stream["title"][:30],
                                        width=160,
                                        url=f"https://twitch.tv/{stream['user_name']}",
                                        style=ButtonStyle(
                                            padding=padding.symmetric(0, 0)
                                        ),
                                    ),
                                    prefer_below=True,
                                ),
                            ]
                        ),
                        padding=padding.all(10),
                    )
                    for stream in streams
                ],
                scroll=True,
            )
        )
        await self.streams_widget.update_async()

    @tasks.loop(seconds=60)
    async def update_mastery(self):
        is_admin = self.page.user_data["is_admin"] if self.page.user_data else False
        mastery_data = await self.api.get_mastery()
        live_mastery = mastery_data["normal"]["live"]
        pts_mastery = mastery_data["normal"]["pts"]
        live_g_mastery = mastery_data["geode"]["live"]
        pts_g_mastery = mastery_data["geode"]["pts"]
        x, y, z = points_to_mr(live_mastery)
        live = {
            "points": live_mastery,
            "level": x,
            "remaining": y,
            "needed": z,
            "percentage": round(y / z, 2),
        }
        x, y, z = points_to_mr(live_g_mastery)
        geode = {
            "points": live_g_mastery,
            "level": x,
            "remaining": y,
            "needed": z,
            "percentage": round(y / z, 2),
        }
        mastery_widgets = Row(
            controls=[
                Card(
                    content=Container(
                        Column(
                            controls=[
                                Text("Live Trove Mastery", size=20),
                                Row(
                                    controls=[
                                        Text(
                                            f"{live['level']}",
                                            spans=[
                                                TextSpan(
                                                    text=f"  ({live['points']:,})",
                                                    style=TextStyle(size=11),
                                                )
                                            ],
                                            size=16,
                                        ),
                                        IconButton(
                                            data=("live", "normal", live["points"]),
                                            icon=icons.EDIT,
                                            icon_size=16,
                                            padding=padding.all(0),
                                            style=ButtonStyle(padding=padding.all(0)),
                                            on_click=self.edit_mastery,
                                            visible=is_admin,
                                        ),
                                    ]
                                ),
                                ProgressBar(
                                    width=200,
                                    value=live["percentage"],
                                    color=colors.YELLOW_600,
                                    bar_height=10,
                                ),
                                Row(
                                    controls=[
                                        Text(live["remaining"]),
                                        Text(f"{round(live['percentage'] * 100, 2)}%"),
                                        Text(live["needed"]),
                                    ],
                                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                                    width=180,
                                ),
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                        ),
                        padding=padding.symmetric(10, 10),
                    )
                ),
                Card(
                    content=Container(
                        Column(
                            controls=[
                                Text("Live Geode Mastery", size=20),
                                Row(
                                    controls=[
                                        Text(
                                            f"{geode['level']}",
                                            spans=[
                                                TextSpan(
                                                    text=f"  ({geode['points']:,})",
                                                    style=TextStyle(size=11),
                                                )
                                            ],
                                            size=16,
                                        ),
                                        IconButton(
                                            data=("live", "geode", geode["points"]),
                                            icon=icons.EDIT,
                                            icon_size=16,
                                            padding=padding.all(0),
                                            style=ButtonStyle(padding=padding.all(0)),
                                            on_click=self.edit_mastery,
                                            visible=is_admin,
                                        ),
                                    ]
                                ),
                                ProgressBar(
                                    width=200,
                                    value=geode["percentage"],
                                    color=colors.CYAN_400,
                                    bar_height=10,
                                ),
                                Row(
                                    controls=[
                                        Text(geode["remaining"]),
                                        Text(f"{round(geode['percentage'] * 100, 2)}%"),
                                        Text(geode["needed"]),
                                    ],
                                    alignment=MainAxisAlignment.SPACE_BETWEEN,
                                    width=180,
                                ),
                            ],
                            horizontal_alignment=CrossAxisAlignment.CENTER,
                        ),
                        padding=padding.symmetric(10, 10),
                    )
                ),
            ],
            alignment=MainAxisAlignment.SPACE_AROUND,
        )
        x, y, z = points_to_mr(pts_mastery)
        live = {
            "points": pts_mastery,
            "level": x,
            "remaining": y,
            "needed": z,
            "percentage": round(y / z, 2),
        }
        x, y, z = points_to_mr(pts_g_mastery)
        geode = {
            "points": pts_g_mastery,
            "level": x,
            "remaining": y,
            "needed": z,
            "percentage": round(y / z, 2),
        }
        if (
            bool(live_mastery < pts_mastery or live_g_mastery < pts_g_mastery)
            or is_admin
        ):
            mastery_widgets.controls[0].content.content.controls.extend(
                [
                    Divider(height=1),
                    Text("PTS Trove Mastery", size=20),
                    Row(
                        controls=[
                            Text(
                                f"{live['level']}",
                                spans=[
                                    TextSpan(
                                        text=f"  ({live['points']:,})",
                                        style=TextStyle(size=11),
                                    )
                                ],
                                size=16,
                            ),
                            IconButton(
                                data=("pts", "normal", live["points"]),
                                icon=icons.EDIT,
                                icon_size=16,
                                padding=padding.all(0),
                                style=ButtonStyle(padding=padding.all(0)),
                                on_click=self.edit_mastery,
                                visible=is_admin,
                            ),
                        ]
                    ),
                    ProgressBar(
                        width=200,
                        value=live["percentage"],
                        color=colors.YELLOW_600,
                        bar_height=10,
                    ),
                    Row(
                        controls=[
                            Text(live["remaining"]),
                            Text(f"{round(live['percentage'] * 100, 2)}%"),
                            Text(live["needed"]),
                        ],
                        alignment=MainAxisAlignment.SPACE_BETWEEN,
                        width=180,
                    ),
                ]
            )
            mastery_widgets.controls[1].content.content.controls.extend(
                [
                    Divider(height=1),
                    Text("PTS Geode Mastery", size=20),
                    Row(
                        controls=[
                            Text(
                                f"{geode['level']}",
                                spans=[
                                    TextSpan(
                                        text=f"  ({geode['points']:,})",
                                        style=TextStyle(size=11),
                                    )
                                ],
                                size=16,
                            ),
                            IconButton(
                                data=("pts", "geode", geode["points"]),
                                icon=icons.EDIT,
                                icon_size=16,
                                padding=padding.all(0),
                                style=ButtonStyle(padding=padding.all(0)),
                                on_click=self.edit_mastery,
                                visible=is_admin,
                            ),
                        ]
                    ),
                    ProgressBar(
                        width=200,
                        value=geode["percentage"],
                        color=colors.CYAN_400,
                        bar_height=10,
                    ),
                    Row(
                        controls=[
                            Text(geode["remaining"]),
                            Text(f"{round(geode['percentage'] * 100, 2)}%"),
                            Text(geode["needed"]),
                        ],
                        alignment=MainAxisAlignment.SPACE_BETWEEN,
                        width=180,
                    ),
                ]
            )
        self.mastery_widget.set_controls(mastery_widgets)
        await self.mastery_widget.update_async()

    @tasks.loop(seconds=60)
    async def update_events(self):
        async with ClientSession() as session:
            async with session.get("https://trovesaurus.com/calendar/feed") as response:
                events = await response.json()
                self.events_widget.set_controls(
                    [
                        ListTile(
                            title=Row(
                                controls=[
                                    TextButton(
                                        content=Text(event["name"], size=20),
                                        style=ButtonStyle(padding=padding.all(0)),
                                        url=event["url"],
                                    ),
                                    RTTChip(
                                        label=Text(event["category"]),
                                        label_padding=padding.all(0),
                                        padding=padding.symmetric(0, 5),
                                    ),
                                ]
                            ),
                            subtitle=Row(
                                controls=[
                                    Text(
                                        humanize.naturalday(
                                            datetime.fromtimestamp(
                                                int(event["startdate"]), UTC
                                            ),
                                            "%B %d",
                                        )
                                    ),
                                    Text(" - "),
                                    Text(
                                        humanize.naturalday(
                                            datetime.fromtimestamp(
                                                int(event["enddate"]), UTC
                                            ),
                                            "%B %d",
                                        )
                                    ),
                                ]
                            ),
                            leading=Image(src=event["image"], height=150, width=150),
                        )
                        for event in events
                    ]
                )
                await self.events_widget.update_async()

    async def edit_mastery(self, event):
        server, mastery_type, points = event.control.data
        await self.page.dialog.set_data(
            title=Text("Edit Mastery"),
            modal=True,
            actions=[
                TextButton("Save", data=event.control.data, on_click=self.save_mastery),
                TextButton("Cancel", on_click=self.page.RTT.close_dialog),
            ],
            content=Column(
                controls=[
                    Text("Server: " + server.upper()),
                    Text("Type: " + ("Trove" if mastery_type == "normal" else "Geode")),
                    TextField(label="Points", value=points),
                ],
                expand=True,
            ),
        )

    async def save_mastery(self, event):
        value = self.page.dialog.dialog.content.controls[2].value
        server, mastery_type, _ = event.control.data
        final_value = int(sympify(value).evalf())
        mastery_data = await self.api.get_mastery()
        for m_t in mastery_data:
            mastery_data[m_t]["updated"] = int(
                datetime.fromisoformat(mastery_data[m_t]["updated"]).timestamp()
            )
        mastery_data[mastery_type][server] = final_value
        mastery_data[mastery_type]["updated"] = int(datetime.now(UTC).timestamp())
        if server == "live":
            if mastery_data[mastery_type]["pts"] < final_value:
                mastery_data[mastery_type]["pts"] = final_value
        await self.api.update_mastery(
            self.page.user_data["internal_token"], mastery_data
        )
        await self.page.dialog.hide()
        self.update_mastery.cancel()
        while self.update_mastery.is_running():
            await asyncio.sleep(1)
        self.update_mastery.start()
