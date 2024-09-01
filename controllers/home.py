import asyncio
from datetime import datetime, UTC, timedelta

import humanize
from aiohttp import ClientSession
from utils.locale import loc
from flet import (
    ListTile,
    Text,
    TextButton,
    Column,
    Divider,
    VerticalDivider,
    Container,
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
from models.interface import Controller, RTTImage, HomeWidget, RTTChip
from utils import tasks
from utils.kiwiapi import KiwiAPI
from utils.trove.mastery import points_to_mr
from models.trove.star_chart import rotate


class HomeController(Controller):
    def setup_controls(self):
        if not hasattr(self, "widgets"):
            self.api = KiwiAPI()
            self.main = ResponsiveRow()
            self.daily_data = files_cache["daily_buffs.json"]
            self.weekly_data = files_cache["weekly_buffs.json"]
            self.date = Text(loc("Trove Time"), size=20, col={"xxl": 6})
        asyncio.create_task(self.post_setup())

    async def post_setup(self):
        self.streams_widget = HomeWidget(
            image="icons/brands/twitch.png",
            title=loc("Twitch Streams"),
            title_size=20,
            title_url="https://www.twitch.tv/directory/category/trove",
            controls=[Text("Loading...")],
        )
        self.daily_widget = HomeWidget(
            icon=icons.CALENDAR_VIEW_DAY,
            title=loc("Daily Bonuses"),
            title_size=20,
            controls=[Text(loc("Loading..."))],
            column_spacing=0,
        )
        self.weekly_widget = HomeWidget(
            icon=icons.CALENDAR_VIEW_WEEK,
            title=loc("Weekly Bonuses"),
            title_size=20,
            controls=[Text(loc("Loading..."))],
        )
        self.events_widget = HomeWidget(
            icon=icons.EVENT,
            title=loc("Events"),
            title_size=20,
            controls=[Text(loc("Loading..."))],
        )
        self.biomes_widget = HomeWidget(
            icon=icons.LANDSCAPE,
            title=loc("D15 Biomes"),
            title_size=20,
            title_url="https://trove.aallyn.xyz/long_shade_rotation",
            # on_click=lambda x: print(x), TODO: Modal with history of biomes
            controls=[Text(loc("Loading..."))],
        )
        self.dragons_widget = HomeWidget(
            icon=icons.STORE,
            title=loc("Dragon Merchants"),
            title_size=20,
            controls=[Text(loc("Loading..."))],
        )
        self.mastery_widget = HomeWidget(
            icon=icons.QUERY_STATS,
            title=loc("Max Mastery"),
            title_size=20,
            controls=[Text(loc("Loading..."))],
        )
        self.main.controls = [
            Column(
                controls=[
                    # self.streams_widget,
                    # Divider(height=1),
                    self.weekly_widget,
                    Divider(height=1),
                    ResponsiveRow(
                        controls=[
                            Row(
                                controls=[self.daily_widget, VerticalDivider()], col=2.5
                            ),
                            Column(
                                controls=[
                                    self.biomes_widget,
                                    Divider(height=1),
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
            # self.update_twitch_streams,
            self.update_weekly,
            self.update_daily,
            self.update_biomes,
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
                            loc("Normal"),
                            *[" \u2022 " + loc(b) for b in v["normal_buffs"]],
                            loc("Patron"),
                            *[" \u2022 " + loc(b) for b in v["premium_buffs"]],
                        ]
                    ),
                    content=Stack(
                        controls=[
                            RTTImage(
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
                                loc(v["weekday"]),
                                color="#cccccc",
                                left=10,
                                top=3,
                                size=16,
                            ),
                            Text(loc(v["name"]), color="#cccccc", left=10, top=23),
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
                            [loc("Buffs"), *[" \u2022 " + loc(b) for b in v["buffs"]]]
                        ),
                        content=Stack(
                            controls=[
                                RTTImage(
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
                                    loc(v["name"]),
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
                    for k, v in buffs.items()
                ]
            )
        )
        await self.weekly_widget.update_async()

    @tasks.loop(seconds=60, log_errors=True)
    async def update_biomes(self):
        async with ClientSession() as session:
            async with session.get(
                "https://kiwiapi.aallyn.xyz/v1/misc/d15_biomes"
            ) as response:
                if response.status != 200:
                    self.biomes_widget.set_controls(Text("API is unreachable"))
                    await self.biomes_widget.update_async()
                    return
                now = int(datetime.now(UTC).timestamp())
                data = await response.json()
                current = data["current"]
                _next = data["next"]
                start, end, first, second, third, _ = current
                biome_pills = [
                    Card(
                        Container(
                            Row(
                                controls=[
                                    RTTImage(
                                        f"images/biomes/{b['icon']}.png", width=20
                                    ),
                                    Text(b["final_name"], size=13),
                                ],
                            ),
                            padding=padding.symmetric(5, 15),
                        )
                    )
                    for b in (first, second, third)
                ]
                start, end, first, second, third, _ = _next
                next_biome_pills = [
                    Card(
                        Container(
                            Row(
                                controls=[
                                    RTTImage(
                                        f"images/biomes/{b['icon']}.png", width=20
                                    ),
                                    Text(b["final_name"], size=13),
                                ],
                            ),
                            padding=padding.symmetric(5, 15),
                        )
                    )
                    for b in (first, second, third)
                ]
                self.biomes_widget.set_controls(
                    ResponsiveRow(
                        controls=[
                            Text(loc("Current")),
                            Row(
                                controls=biome_pills,
                                alignment=MainAxisAlignment.SPACE_AROUND,
                            ),
                            Text(
                                loc("Next in {}").format(
                                    "{:02d}:{:02d}".format(
                                        (start - now) // 3600,
                                        (start - now) % 3600 // 60,
                                    )
                                )
                            ),
                            Row(
                                controls=next_biome_pills,
                                alignment=MainAxisAlignment.SPACE_AROUND,
                            ),
                            # biomes,
                        ]
                    )
                )
                await self.biomes_widget.update_async()

    @tasks.loop(seconds=60)
    async def update_dragons(self):
        trove_time = self.page.trove_time
        dragons = (
            (loc("Luxion"), trove_time.first_luxion, "lux"),
            (loc("Corruxion"), trove_time.first_corruxion, "nlux"),
        )
        dragon_controls = []
        for name, first, image_name in dragons:
            if trove_time.is_dragon(first):
                image_src = f"images/dragons/{image_name}.png"
                text = Text(
                    loc("Leaving in {}").format(
                        humanize.naturaltime(
                            -trove_time.until_end_dragon(first)
                        ).replace(" from now", "")
                    )
                )
            else:
                image_src = f"images/dragons/{image_name}_out.png"
                text = Text(
                    loc("Arriving in {}").format(
                        humanize.naturaltime(
                            -trove_time.until_next_dragon(first)
                        ).replace(" from now", "")
                    )
                )
            image = RTTImage(src=image_src, width=40, height=40)
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
            image_src = "images/dragons/fluxion.png"
            phase_text = (
                loc("Voting") if trove_time.is_fluxion_voting() else loc("Selling")
            )
            text = Text(
                loc("Leaving in {}").format(
                    humanize.naturaltime(-trove_time.until_end_fluxion()).replace(
                        " from now", ""
                    )
                )
            )
        else:
            image_src = "images/dragons/fluxion_out.png"
            phase_text = (
                loc("Voting") if trove_time.is_fluxion_selling() else loc("Selling")
            )
            text = Text(
                loc("Arriving in {}").format(
                    humanize.naturaltime(-trove_time.until_next_fluxion()).replace(
                        " from now", ""
                    )
                )
            )
        image = RTTImage(src=image_src, width=40, height=40)
        dragon_control = Card(
            Container(
                Column(
                    controls=[
                        image,
                        TextButton(
                            content=Text(f"[{phase_text}] " + loc("Fluxion"), size=20),
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
                                            RTTImage(
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
                                        (stream["title"] or "")[:30],
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
        is_admin = self.page.is_admin
        mastery_data = await self.api.get_mastery()
        if mastery_data is None:
            self.mastery_widget.set_controls(Text("API is unreachable"))
            await self.mastery_widget.update_async()
            return
        now = datetime.now(UTC)
        mastery_updated = humanize.naturaltime(
            now
            - datetime.fromisoformat(mastery_data["normal"]["updated"]).astimezone(UTC)
        )
        live_mastery = mastery_data["normal"]["live"]
        pts_mastery = mastery_data["normal"]["pts"]
        geode_updated = humanize.naturaltime(
            now
            - datetime.fromisoformat(mastery_data["normal"]["updated"]).astimezone(UTC)
        )
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
                                Row(
                                    controls=[
                                        Icon(icons.UPDATE, tooltip=mastery_updated),
                                        Text(loc("Live Trove Mastery"), size=20),
                                    ]
                                ),
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
                                Row(
                                    controls=[
                                        Icon(icons.UPDATE, tooltip=geode_updated),
                                        Text(loc("Live Geode Mastery"), size=20),
                                    ]
                                ),
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
                    Text(loc("PTS Trove Mastery"), size=20),
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
                    Text(loc("PTS Geode Mastery"), size=20),
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
                            leading=RTTImage(
                                src=event["image"] or event["icon"] or None,
                                height=150,
                                width=150,
                            ),
                        )
                        for event in events
                    ]
                )
                if not events:
                    self.events_widget.set_controls(
                        [
                            ListTile(
                                title=Row(
                                    controls=[
                                        Text(loc("No events are currently going on."))
                                    ]
                                )
                            )
                        ]
                    )
                await self.events_widget.update_async()

    async def edit_mastery(self, event):
        server, mastery_type, points = event.control.data
        await self.page.dialog.set_data(
            title=Text(loc("Edit Mastery")),
            modal=True,
            actions=[
                TextButton(
                    loc("Save"), data=event.control.data, on_click=self.save_mastery
                ),
                TextButton(loc("Cancel"), on_click=self.page.RTT.close_dialog),
            ],
            content=Column(
                controls=[
                    Text(loc("Server") + ": " + server.upper()),
                    Text(
                        f"{loc('Type')}:"
                        + ("Trove" if mastery_type == "normal" else "Geode")
                    ),
                    TextField(label=loc("Points"), value=points),
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
