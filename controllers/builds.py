import asyncio
import itertools
import json

from aiohttp import ClientSession
from flet import (
    Text,
    ResponsiveRow,
    Dropdown,
    dropdown,
    DataTable,
    DataColumn,
    DataRow,
    DataCell,
    Column,
    Card,
    Row,
    Stack,
    Switch,
    Slider,
    Container,
    TextField,
    Divider,
    IconButton,
    ElevatedButton,
    Icon,
    Tooltip,
    TextStyle,
    Border,
    BorderSide,
)
from flet_core.icons import COPY, CALCULATE

from models.constants import files_cache
from models.interface import Controller, RTTImage, ScrollingFrame, AutoNumberField
from models.trove.builds import (
    TroveClass,
    Class,
    StatName,
    BuildConfig,
    BuildType,
    DamageType,
    AbilityType,
)
from models.trove.star_chart import get_star_chart
from utils.functions import get_attr, chunks
from utils.locale import loc


class GemBuildsController(Controller):
    def setup_controls(self):
        if not hasattr(self, "classes"):
            self.interface = ResponsiveRow(vertical_alignment="START")
        asyncio.create_task(self.setup())

    async def setup(self):
        if not hasattr(self, "classes"):
            self.star_chart = get_star_chart(files_cache["star_chart.json"])
            self.star_chart_abilities = []
            self.selected_build = None
            self.build_page = 0
            self.max_pages = 0
            self.classes = {}
            self.files = files_cache
            for trove_class in self.files["classes.json"]:
                self.classes[trove_class["name"]] = TroveClass(**trove_class)
            self.foods = self.files["builds/food.json"]
            self.allies = self.files["builds/ally.json"]
            self.face_damage = self.files["builds/face_damage.json"]["Face"]
            self.config = BuildConfig()
            self.character_data = ResponsiveRow()
            self.features = ResponsiveRow()
        self.interface.disabled = True
        await self.page.update_async()
        self.selected_class = self.classes.get(self.config.character.value, None)
        self.selected_subclass = self.classes.get(self.config.subclass.value, None)
        presets = await self.page.api.get_star_chart_presets()
        preset_builds = [
            [preset["build"], preset["preset"]["name"]] for preset in presets
        ]
        self.coeff_table = DataTable(
            columns=[
                DataColumn(label=Text("#")),
                DataColumn(label=Text(loc("Build"))),
                DataColumn(label=Text(loc("Light"))),
                DataColumn(label=Text(loc("Base Damage"))),
                DataColumn(label=Text(loc("Bonus Damage"))),
                DataColumn(label=Text(loc("Damage"))),
                DataColumn(label=Text(loc("Critical"))),
                DataColumn(label=Text(loc("Coefficient"))),
                DataColumn(label=Text(loc("Deviation"))),
                DataColumn(label=Text(loc("Actions"))),
            ],
            heading_row_height=40,
            data_row_min_height=40,
            bgcolor="#212223",
        )
        format_tooltip = loc("Build format") + ":\n  "
        if self.selected_class.damage_type == DamageType.magic:
            format_tooltip += loc("MD/CD/MD/CD")
        else:
            format_tooltip += loc("PD/CD/PD/CD")
        if self.config.build_type not in [BuildType.light]:
            if self.selected_class.damage_type == DamageType.magic:
                format_tooltip += " + " + loc("MD/CD/LT/MD/CD/LT")
            else:
                format_tooltip += " + " + loc("PD/CD/LT/PD/CD/LT")
        self.interface.controls = [
            Column(
                controls=[
                    Card(
                        content=ResponsiveRow(
                            controls=[
                                Stack(
                                    controls=[
                                        RTTImage(
                                            src=self.selected_class.image_path,
                                            scale=1.2,
                                            height=350,
                                        ),
                                        RTTImage(
                                            src=self.selected_subclass.icon_path,
                                            width=150,
                                            bottom=25,
                                            right=-10,
                                        ),
                                    ],
                                    col={"xxl": 6},
                                ),
                                Column(
                                    controls=[
                                        Dropdown(
                                            label=loc("Class"),
                                            value=self.selected_class.name.name,
                                            options=[
                                                dropdown.Option(
                                                    key=c.name,
                                                    text=loc(c.value),
                                                    disabled=c.name
                                                    == self.config.character.name,
                                                )
                                                for c in Class
                                            ],
                                            text_size=14,
                                            height=58,
                                            on_change=self.set_class,
                                        ),
                                        Tooltip(
                                            message=loc("WIP"),
                                            content=Dropdown(
                                                label=loc("Subclass"),
                                                value=self.selected_subclass.name.name,
                                                options=[
                                                    dropdown.Option(
                                                        key=c.name,
                                                        text=loc(c.value),
                                                        disabled=c.name
                                                        == self.config.subclass.name,
                                                    )
                                                    for c in Class
                                                ],
                                                text_size=14,
                                                height=58,
                                                on_change=self.set_subclass,
                                            ),
                                            border_radius=10,
                                            bgcolor="#1E1E28",
                                            text_style=TextStyle(color="#cccccc"),
                                            border=Border(
                                                BorderSide(width=2, color="#cccccc"),
                                                BorderSide(width=2, color="#cccccc"),
                                                BorderSide(width=2, color="#cccccc"),
                                                BorderSide(width=2, color="#cccccc"),
                                            ),
                                        ),
                                        Dropdown(
                                            label=loc("Build Type"),
                                            value=self.config.build_type.name,
                                            options=[
                                                dropdown.Option(
                                                    key=b.name,
                                                    text=loc(b.value),
                                                    disabled=b.name
                                                    == self.config.build_type.name,
                                                )
                                                for b in BuildType
                                                if b
                                                not in [
                                                    BuildType.health,
                                                    BuildType.farm,
                                                ]
                                            ],
                                            text_size=14,
                                            height=58,
                                            on_change=self.set_build_type,
                                        ),
                                        Tooltip(
                                            message="\n".join(
                                                [
                                                    loc("Stats"),
                                                    *[
                                                        " - "
                                                        + str(round(s["value"], 2))
                                                        + (
                                                            "% "
                                                            if s["percentage"]
                                                            else " "
                                                        )
                                                        + loc(s["name"])
                                                        for s in self.foods[
                                                            self.config.food
                                                        ]["stats"]
                                                    ],
                                                ]
                                            ),
                                            content=Column(
                                                controls=[
                                                    Dropdown(
                                                        label=loc("Auto-use"),
                                                        value=self.config.food,
                                                        options=[
                                                            dropdown.Option(
                                                                key=name,
                                                                text=loc(
                                                                    food[
                                                                        "qualified_name"
                                                                    ]
                                                                ),
                                                                disabled=name
                                                                == self.config.food,
                                                            )
                                                            for name, food in self.foods.items()
                                                        ],
                                                        text_size=14,
                                                        height=58,
                                                        on_change=self.set_food,
                                                    )
                                                ]
                                            ),
                                            border_radius=10,
                                            bgcolor="#1E1E28",
                                            text_style=TextStyle(color="#cccccc"),
                                            border=Border(
                                                BorderSide(width=2, color="#cccccc"),
                                                BorderSide(width=2, color="#cccccc"),
                                                BorderSide(width=2, color="#cccccc"),
                                                BorderSide(width=2, color="#cccccc"),
                                            ),
                                        ),
                                        Tooltip(
                                            message="\n".join(
                                                [
                                                    loc("Stats"),
                                                    *[
                                                        " - "
                                                        + str(round(s["value"], 2))
                                                        + (
                                                            "% "
                                                            if s["percentage"]
                                                            else " "
                                                        )
                                                        + loc(s["name"])
                                                        for s in self.allies[
                                                            self.config.ally
                                                        ]["stats"]
                                                    ],
                                                    loc("Abilities"),
                                                    *[
                                                        " - " + loc(a)
                                                        for a in self.allies[
                                                            self.config.ally
                                                        ]["abilities"]
                                                    ],
                                                ]
                                            ),
                                            content=Column(
                                                controls=[
                                                    Dropdown(
                                                        label=loc("Ally"),
                                                        value=self.config.ally,
                                                        options=[
                                                            dropdown.Option(
                                                                key=name,
                                                                text=ally[
                                                                    "qualified_name"
                                                                ],
                                                                disabled=name
                                                                == self.config.ally,
                                                            )
                                                            for name, ally in self.allies.items()
                                                        ],
                                                        text_size=14,
                                                        height=58,
                                                        on_change=self.set_ally,
                                                    )
                                                ]
                                            ),
                                            border_radius=10,
                                            bgcolor="#1E1E28",
                                            text_style=TextStyle(color="#cccccc"),
                                            border=Border(
                                                BorderSide(width=2, color="#cccccc"),
                                                BorderSide(width=2, color="#cccccc"),
                                                BorderSide(width=2, color="#cccccc"),
                                                BorderSide(width=2, color="#cccccc"),
                                            ),
                                        ),
                                    ],
                                    col={"xxl": 6},
                                ),
                            ],
                            vertical_alignment="CENTER",
                        )
                    ),
                    Card(
                        content=Column(
                            controls=[
                                Dropdown(
                                    value=(
                                        "custom"
                                        if self.star_chart.build_id
                                        not in [b[0] for b in preset_builds]
                                        else self.star_chart.build_id
                                    ),
                                    options=[
                                        dropdown.Option(key=b[0], text=b[1])
                                        for b in [
                                            (
                                                (["none", "none"])
                                                if self.star_chart.build_id
                                                else ([])
                                            ),
                                            (
                                                (
                                                    [
                                                        self.star_chart.build_id,
                                                        loc("Custom"),
                                                    ]
                                                )
                                                if self.star_chart.build_id
                                                else ([])
                                            ),
                                            *preset_builds,
                                        ]
                                        if b
                                    ],
                                    text_size=14,
                                    height=58,
                                    label=loc("Star Chart"),
                                    on_change=self.set_star_chart_build,
                                ),
                                TextField(
                                    hint_text=loc("Star Chart Build ID"),
                                    on_change=self.set_star_chart_build,
                                    text_size=14,
                                    height=58,
                                ),
                                *[
                                    Text(f"{loc(k)}: {v[0]}" + ("%" if v[1] else ""))
                                    for k, v in self.star_chart.activated_gem_stats.items()
                                ],
                                *[
                                    AutoNumberField(
                                        label=loc("Light"),
                                        value=str(self.config.light),
                                        on_change=self.set_light,
                                    )
                                    for _ in range(1)
                                    if self.config.build_type != BuildType.light
                                ],
                                ResponsiveRow(
                                    controls=[
                                        Column(
                                            controls=[
                                                Text(loc(ability["name"]), size=14),
                                                Text(
                                                    loc(ability["description"]), size=10
                                                ),
                                                Switch(
                                                    data=ability,
                                                    value=ability["active"],
                                                    on_change=self.switch_star_buff,
                                                ),
                                            ],
                                            col={"xxl": 6},
                                        )
                                        for ability in self.star_chart_abilities
                                    ]
                                ),
                            ],
                            spacing=11,
                        )
                    ),
                    Card(
                        content=Column(
                            controls=[
                                ResponsiveRow(
                                    controls=[
                                        Text(
                                            loc("Gear Critical Damage")
                                            + f": {self.config.critical_damage_count}",
                                            col={"xxl": 4},
                                        ),
                                        Slider(
                                            min=0,
                                            max=3,
                                            divisions=3,
                                            value=self.config.critical_damage_count,
                                            label="{value}",
                                            on_change_end=self.set_cd_count,
                                            col={"xxl": 8},
                                        ),
                                    ]
                                ),
                                Divider(thickness=1),
                                ResponsiveRow(
                                    controls=[
                                        ResponsiveRow(
                                            controls=[
                                                Switch(
                                                    value=not self.config.no_face,
                                                    on_change=self.toggle_face,
                                                ),
                                                Text(
                                                    loc("Face Damage"),
                                                    text_align="center",
                                                ),
                                            ],
                                            alignment="center",
                                            col={"xxl": 3},
                                        ),
                                        ResponsiveRow(
                                            controls=[
                                                Switch(
                                                    value=self.config.subclass_active,
                                                    on_change=self.toggle_subclass_active,
                                                ),
                                                Text(
                                                    loc("Subclass active"),
                                                    text_align="center",
                                                ),
                                            ],
                                            alignment="center",
                                            col={"xxl": 3},
                                        ),
                                        ResponsiveRow(
                                            controls=[
                                                Switch(
                                                    value=self.config.berserker_battler,
                                                    on_change=self.toggle_berserker_battler,
                                                ),
                                                Text(
                                                    loc("Berserker Battler"),
                                                    text_align="center",
                                                ),
                                            ],
                                            alignment="center",
                                            col={"xxl": 3},
                                        ),
                                        ResponsiveRow(
                                            controls=[
                                                Switch(
                                                    value=self.config.litany,
                                                    on_change=self.toggle_litany,
                                                ),
                                                Text(
                                                    loc("Enlightened"),
                                                    text_align="center",
                                                ),
                                            ],
                                            alignment="center",
                                            col={"xxl": 3},
                                        ),
                                    ],
                                ),
                            ],
                            spacing=5,
                        )
                    ),
                ],
                col={"xxl": 4},
            ),
            Column(
                controls=[
                    ResponsiveRow(controls=[ScrollingFrame(self.coeff_table)]),
                    self.features,
                ],
                col={"xxl": 8},
            ),
        ]
        self.features.controls.clear()
        self.features.controls = [
            ElevatedButton(
                loc("First"),
                data=0,
                on_click=self.change_build_page,
                col={"xs": 3, "xxl": 2},
            ),
            ElevatedButton(
                loc("Previous"),
                data=self.build_page - 1,
                on_click=self.change_build_page,
                col={"xs": 3, "xxl": 2},
            ),
            ElevatedButton(
                loc("Next"),
                data=self.build_page + 1,
                on_click=self.change_build_page,
                col={"xs": 3, "xxl": 2},
            ),
            ElevatedButton(
                loc("Last"),
                data=self.max_pages - 1,
                on_click=self.change_build_page,
                col={"xs": 3, "xxl": 2},
            ),
            TextField(
                label=loc("Insert Gem Build ID"),
                on_change=self.set_build_string,
                col={"xs": 6, "xxl": 2},
                visible=True,
            ),
            Container(
                content=Row(controls=[Icon(COPY), Text(loc("Copy Gem Build"))]),
                on_click=self.copy_build_string,
                on_hover=self.copy_build_hover,
                padding=15,
                border_radius=10,
                col={"xs": 6, "xxl": 2},
                visible=True,
            ),
        ]
        self.abilities = DataTable(
            columns=[
                DataColumn(Text("")),
                DataColumn(Text("")),
                DataColumn(
                    Row(
                        [
                            Text("", width=70, size=10),
                            Text(
                                loc("Critical"), width=70, size=10, text_align="center"
                            ),
                            Text(
                                loc("Emblem 2.5x"),
                                width=70,
                                size=10,
                                text_align="center",
                            ),
                        ]
                    )
                ),
            ],
            heading_row_height=15,
            data_row_min_height=80,
            col={"xxl": 4},
        )
        if not hasattr(self, "data_table"):
            self.abilities_table = Card(
                content=Column(
                    controls=[Text(loc("Abilities"), size=22), self.abilities],
                    horizontal_alignment="center",
                ),
                col={"xxl": 4},
            )
            self.data_table = Container(
                content=ResponsiveRow(
                    controls=[
                        ScrollingFrame(self.coeff_table),
                        self.abilities_table,
                    ]
                ),
                col={"xxl": 8},
            )
        self.abilities_table.visible = bool(self.selected_build)
        if self.config.character:
            self.coeff_table.rows.clear()
            builds = self.calculate_results()
            builds.sort(
                key=lambda x: (
                    [abs(x[3] - self.config.light), -x[-1]]
                    if self.config.light
                    else -x[-1]
                )
            )
            best = builds[0]
            builds = [[i] + b for i, b in enumerate(builds, 1)]
            paged_builds = chunks(builds, 15)
            self.max_pages = len(paged_builds)
            if self.build_page < 0:
                self.build_page = self.max_pages - 1
            elif self.build_page > self.max_pages - 1:
                self.build_page = 0
            for (
                rank,
                build,
                first,
                second,
                third,
                fourth,
                final,
                class_bonus,
                coefficient,
            ) in paged_builds[self.build_page]:
                boosts = []
                [boosts.extend(i) for i in build]
                if not self.config.light or (
                    self.config.light and self.config.build_type in [BuildType.health]
                ):
                    del boosts[6]
                    del boosts[8]
                if not self.config.light and self.config.build_type not in [
                    BuildType.health
                ]:
                    boosts = boosts[:4]
                build_text = "/".join([str(i) for i in boosts][:4]) + (
                    " + " + "/".join([str(i) for i in boosts][4:])
                    if len(boosts) > 4
                    else ""
                )
                build_data = [
                    build,
                    first,
                    second,
                    third,
                    fourth,
                    final,
                    class_bonus,
                    coefficient,
                ]
                self.coeff_table.rows.append(
                    DataRow(
                        cells=[
                            DataCell(content=Text(f"{rank}")),
                            DataCell(
                                content=Text(f"{build_text}", tooltip=format_tooltip),
                                on_tap=self.copy_to_clipboard,
                            ),
                            DataCell(content=Text(f"{third:,}")),
                            DataCell(content=Text(f"{round(first, 2):,}")),
                            DataCell(
                                content=Text(
                                    f"{round(fourth, 2):,}%"
                                    + (
                                        f" + {round(class_bonus, 1)}%"
                                        if class_bonus
                                        else ""
                                    )
                                )
                            ),
                            DataCell(content=Text(f"{round(final):,}")),
                            DataCell(content=Text(f"{round(second, 1):,}%")),
                            DataCell(
                                content=Text(f"{coefficient:,}"),
                                on_tap=self.copy_to_clipboard,
                            ),
                            DataCell(
                                content=Text(
                                    f"{round(abs(coefficient - best[-1]) / best[-1] * 100, 3)}%"
                                    if rank != 1
                                    else loc("Best")
                                )
                            ),
                            DataCell(
                                content=Row(
                                    controls=[
                                        IconButton(
                                            COPY,
                                            data=self.get_build_string(
                                                [
                                                    build_text,
                                                    first,
                                                    second,
                                                    third,
                                                    fourth,
                                                    final,
                                                    class_bonus,
                                                    coefficient,
                                                ]
                                            ),
                                            on_click=self.copy_build_clipboard,
                                        ),
                                        IconButton(
                                            CALCULATE,
                                            data=build_data,
                                            on_click=self.select_build,
                                        ),
                                    ],
                                    spacing=0,
                                )
                            ),
                        ],
                        color=(
                            "#156b16"
                            if build_data == self.selected_build
                            else ("#313233" if rank % 2 else "#414243")
                        ),
                    )
                )
        self.abilities.rows.clear()
        self.abilities_table.visible = bool(
            self.selected_build is not None and len(self.selected_class.abilities)
        )
        if self.abilities_table.visible:
            self.abilities.rows.extend(
                [
                    *[
                        DataRow(
                            cells=[
                                DataCell(
                                    content=Stack(
                                        controls=[
                                            RTTImage(a.icon_path, top=6, left=5),
                                            *[
                                                RTTImage(
                                                    "assets/images/abilities/gem_frame.png"
                                                )
                                                for i in range(1)
                                                if a.type == AbilityType.upgrade
                                            ],
                                        ],
                                    )
                                ),
                                DataCell(content=Text(a.name)),
                                DataCell(
                                    content=Column(
                                        controls=[
                                            Row(
                                                controls=[
                                                    Text(s.name, size=10, width=70),
                                                    Text(
                                                        f"{round(s.base + s.multiplier * self.selected_build[6]):,}",
                                                        size=10,
                                                        width=70,
                                                        text_align="center",
                                                    ),
                                                    Text(
                                                        f"{round(s.base + s.multiplier * self.selected_build[6]*2.5):,}",
                                                        size=10,
                                                        width=70,
                                                        text_align="center",
                                                    ),
                                                ],
                                            )
                                            for s in a.stages
                                        ],
                                        alignment="center",
                                        spacing=1,
                                    )
                                ),
                            ]
                        )
                        for a in self.selected_class.abilities
                    ]
                ]
            )
        self.features.controls.append(self.abilities_table)
        self.interface.disabled = False
        await self.page.update_async()

    def setup_events(self): ...

    def calculate_results(self):
        if self.config.build_type in [BuildType.health]:
            return list(self.calculate_health_build_stats())
        elif self.config.build_type in [BuildType.light, BuildType.farm]:
            return list(self.calculate_damage_build_stats())

    def calculate_health_build_stats(self):
        first = 0
        second = 0
        first += self.sum_file_values("health")
        second += self.sum_file_values("health_per")
        first += get_attr(
            self.selected_class.stats, name=StatName("Maximum Health")
        ).value
        second += get_attr(
            self.selected_class.stats, name=StatName("Maximum Health %")
        ).value
        if self.selected_class.subclass in [Class.chloromancer]:
            second += 60
        return first, second, 0, 0

    def calculate_damage_build_stats(self):
        first = 0
        second = 0
        third = 0
        fourth = 0
        fifth = 100
        sixth = 100
        first += self.sum_file_values("damage")
        second += self.sum_file_values("critical_damage")
        third += self.sum_file_values("light")
        fourth += self.sum_file_values("bonus_damage")
        damage_type = (
            StatName.magic_damage
            if self.selected_class.damage_type == DamageType.magic
            else StatName.physical_damage
        )
        first += get_attr(self.selected_class.stats, name=damage_type).value
        second += get_attr(
            self.selected_class.stats, name=StatName("Critical Damage")
        ).value
        if not self.config.no_face:
            first += self.face_damage
        # Dragon stats
        first += self.sum_file_values(f"{damage_type.name}/dragons_damage")
        first += self.sum_file_values(f"dragons_damage")
        second += self.sum_file_values("dragons_critical_damage")
        # Food stats
        food = self.foods[self.config.food]
        for stat in food["stats"]:
            if stat["name"] == damage_type.value:
                if stat["percentage"]:
                    fourth += stat["value"]
                else:
                    first += stat["value"]
            if stat["name"] == StatName.critical_damage.value:
                second += stat["value"]
            if stat["name"] == StatName.light.value:
                third += stat["value"]
        # Ally stats
        ally = self.allies[self.config.ally]
        for stat in ally["stats"]:
            if stat["name"] == damage_type.value:
                if stat["percentage"]:
                    fourth += stat["value"]
                else:
                    first += stat["value"]
            if stat["name"] == StatName.critical_damage.value:
                second += stat["value"]
            if stat["name"] == StatName.light.value:
                third += stat["value"]
        # Remove critical damage stats from equipments (movement speed builds)
        second -= 48.1 * (3 - self.config.critical_damage_count)
        # Solarion 140 Light
        if Class.solarion in [self.config.character, self.config.subclass]:
            third += 140
        # Lunar Lancer subclass
        if damage_type == StatName.physical_damage:
            if self.config.subclass in [Class.lunar_lancer]:
                first += 750
        # Shadow Hunter and Ice Sage
        if damage_type == StatName.magic_damage:
            if self.config.subclass in [Class.ice_sage, Class.shadow_hunter]:
                first += 750
        # Bard and Boomeranger subclasses
        if self.config.subclass in [Class.bard, Class.boomeranger]:
            second += 20
        # Active subclass boosts
        if self.config.subclass_active:
            # Bard
            if self.config.subclass in [Class.bard]:
                fourth += 45
                second += 45
            # Gunslinger
            if self.config.subclass in [Class.gunslinger]:
                fourth += 5.5
            # Lunar Lancer and Candy Barbarian
            if self.config.subclass in [Class.lunar_lancer, Class.candy_barbarian]:
                fourth += 30
        # Berserker battler stats
        if self.config.berserker_battler:
            third += 750
        builder = self.generate_combinations(
            farm=self.config.build_type in [BuildType.farm]
        )
        # Star Chart stats
        data = self.star_chart.activated_gem_stats
        first += data.get(damage_type.value, [0])[0]
        second += data.get("Critical Damage", [0])[0]
        third += data.get("Light", [0])[0]
        fourth += data.get(damage_type.value + " Bonus", [0])[0]
        fifth += data.get("Critical Damage Bonus", [0])[0]
        sixth += data.get("Light Bonus", [0])[0]
        # Star Chart ability stats
        for ability in self.star_chart_abilities:
            if ability["active"]:
                for value in ability["values"]:
                    if value["name"] == damage_type.value:
                        if value["percentage"]:
                            fourth += value["value"]
                        else:
                            first += value["value"]
                    if value["name"] == "Critical Damage":
                        second += value["value"]
                    if value["name"] == "Light":
                        third += value["value"]
        if self.config.litany:
            sixth += 1
        for build_tuple in builder:
            build = list(build_tuple)
            gem_first, gem_second, gem_third = self.calculate_gem_stats(
                self.config, build
            )
            cfirst = first + gem_first
            csecond = second + gem_second
            cthird = third + gem_third
            class_bonus = None
            for bonus in self.selected_class.bonuses:
                if bonus.name == damage_type:
                    class_bonus = bonus.value
            final = cfirst * (1 + fourth / 100)
            if class_bonus is not None:
                final *= 1 + (class_bonus / 100)
            coefficient = int(
                round(final) * (1 + (round(csecond, 1) * (fifth / 100)) / 100)
            )
            build_stats = [
                build,
                cfirst,
                csecond,
                int(cthird * (sixth / 100)),
                fourth,
                final,
                class_bonus,
                coefficient,
            ]
            yield build_stats

    def sum_file_values(self, path):
        data = self.files[f"builds/{path}.json"]
        return sum(data.values())

    def calculate_gem_stats(self, config: BuildConfig, build):
        first = 0
        second = 0
        third = 0
        cosmic_first = 0
        cosmic_second = 0
        if not hasattr(self, "gem_stats"):
            self.gem_stats = files_cache["gems/crystal.json"]
        if config.build_type == BuildType.health:
            first_lesser = self.gem_stats["Lesser"]["Maximum Health"]
            first_empowered = self.gem_stats["Empowered"]["Maximum Health"]
            second_lesser = self.gem_stats["Lesser"]["Maximum Health %"]
            second_empowered = self.gem_stats["Empowered"]["Maximum Health %"]
        else:
            first_lesser = self.gem_stats["Lesser"]["Damage"]
            first_empowered = self.gem_stats["Empowered"]["Damage"]
            second_lesser = self.gem_stats["Lesser"]["Critical Damage"]
            second_empowered = self.gem_stats["Empowered"]["Critical Damage"]
        third_lesser = self.gem_stats["Lesser"]["Light"]
        third_empowered = self.gem_stats["Empowered"]["Light"]
        # Add base stats from gems
        first += 3 * first_empowered[0]
        first += 6 * first_lesser[0]
        second += 3 * second_empowered[0]
        second += 6 * second_lesser[0]
        third += 1 * third_empowered[0]
        third += 2 * third_lesser[0]
        cosmic_first += 1 * first_empowered[0]
        cosmic_first += 2 * first_lesser[0]
        cosmic_second += 1 * second_empowered[0]
        cosmic_second += 2 * second_lesser[0]
        # Add stats from boosts
        first += first_empowered[1] * build[0][0]
        second += second_empowered[1] * build[0][1]
        first += first_lesser[1] * build[1][0]
        second += second_lesser[1] * build[1][1]
        cosmic_first += first_empowered[1] * build[2][0]
        cosmic_second += second_empowered[1] * build[2][1]
        third += third_empowered[1] * build[2][2]
        cosmic_first += first_lesser[1] * build[3][0]
        cosmic_second += second_lesser[1] * build[3][1]
        third += third_lesser[1] * build[3][2]
        first = (first + cosmic_first) * 1.1
        second = (second + cosmic_second) * 1.1
        third = third * 1.1
        return first, second, third

    def generate_combinations(self, farm=False):
        first_set = [[i, 9 - i] for i in range(10)]
        second_set = [[i, 18 - i] for i in range(19)]
        third_set = [
            [x, y, z]
            for x in range(4)
            for y in range(4)
            for z in range(4)
            if x + y + z == 3 and (z == 3 if not farm else True)
        ]
        fourth_set = [
            [x, y, z]
            for x in range(7)
            for y in range(7)
            for z in range(7)
            if x + y + z == 6 and (z == 6 if not farm else True)
        ]
        return itertools.product(first_set, second_set, third_set, fourth_set)

    async def set_class(self, event):
        self.selected_build = None
        old_class = self.config.character
        self.config.character = Class[event.control.value]
        if self.config.character == self.config.subclass:
            self.config.subclass = old_class
        self.selected_class = self.classes.get(self.config.character.value, None)
        damage_type = (
            StatName.magic_damage
            if self.selected_class.damage_type == DamageType.magic
            else StatName.physical_damage
        )
        if damage_type == DamageType.magic:
            self.config.ally = "Starry Skyfire"
        elif damage_type == DamageType.physical:
            self.config.ally = "Scorpius"
        await self.update_builds()

    async def set_subclass(self, event):
        old_subclass = self.config.subclass
        self.config.subclass = Class[event.control.value]
        if self.config.character == self.config.subclass:
            self.config.character = old_subclass
        await self.update_builds()

    async def set_build_type(self, event):
        self.config.build_type = BuildType[event.control.value]
        if self.config.build_type is BuildType.farm:
            self.config.light = 12000
        else:
            self.config.light = 0
        await self.update_builds()

    async def toggle_face(self, _):
        self.config.no_face = not self.config.no_face
        await self.update_builds()

    async def set_cd_count(self, event):
        self.config.critical_damage_count = int(event.control.value)
        await self.update_builds()

    async def toggle_subclass_active(self, _):
        self.config.subclass_active = not self.config.subclass_active
        await self.update_builds()

    async def set_food(self, event):
        self.config.food = event.control.value
        await self.update_builds()

    async def set_ally(self, event):
        self.config.ally = event.control.value
        await self.update_builds()

    async def toggle_berserker_battler(self, _):
        self.config.berserker_battler = not self.config.berserker_battler
        await self.update_builds()

    async def toggle_litany(self, _):
        self.config.litany = not self.config.litany
        await self.update_builds()

    async def toggle_star_chart(self, _):
        self.config.star_chart = not self.config.star_chart
        await self.update_builds()

    async def set_light(self, event):
        self.config.light = int(event.control.value)
        await self.update_builds()

    async def change_build_page(self, event):
        self.build_page = event.control.data
        await self.update_builds()

    async def set_build_string(self, event):
        build_id = event.control.value.strip().split("-")[-1].strip()
        async with ClientSession() as session:
            async with session.get(
                f"https://kiwiapi.aallyn.xyz/v1/gem_builds/build/{build_id}"
            ) as response:
                if response.status != 200:
                    await self.page.snack_bar.show(loc("Invalid build ID"))
                    return
                data = await response.json()
                self.config = BuildConfig(**json.loads(data)["config"])
                await self.update_builds()

    async def copy_build_string(self, _):
        async with ClientSession() as session:
            async with session.get(
                "https://kiwiapi.aallyn.xyz/v1/gem_builds/build_config",
                headers={"config": self.config.json()},
            ) as response:
                data = await response.json()
                build_id = json.loads(data)["build"]
                await self.page.set_clipboard_async("GB-" + build_id)
                await self.page.snack_bar.show(
                    loc("Copied build GB-{} to clipboard".format(build_id))
                )

    async def select_build(self, event):
        if self.selected_build == event.control.data:
            self.selected_build = None
        else:
            self.selected_build = event.control.data
        await self.page.snack_bar.show(loc("Ability build changed"))
        await self.update_builds()

    async def copy_to_clipboard(self, event):
        if value := event.control.content.value:
            await self.page.set_clipboard_async(str(value))
            await self.page.snack_bar.show(loc("Copied to clipboard"))
        await self.page.update_async()

    def get_build_string(self, data):
        string = ""
        string += loc("Build") + f": {data[0]}\n"
        string += loc("Light") + f": {data[3]}\n"
        string += loc("Base Damage") + f": {round(data[1], 2)}\n"
        string += loc("Bonus Damage") + f": {round(data[4], 2)}\n"
        string += loc("Damage") + f": {round(data[5])}\n"
        string += loc("Critical Damage") + f": {round(data[2], 1)}\n"
        if data[6] is not None:
            string += loc("Class Bonus") + f": {data[6]}\n"
        string += loc("Coefficient") + f": {data[7]}"
        return string

    async def copy_build_clipboard(self, event):
        await self.page.set_clipboard_async(event.control.data)
        await self.page.snack_bar.show(loc("Copied to clipboard"))

    async def copy_build_hover(self, event):
        event.control.ink = True
        await event.control.update_async()

    async def set_star_chart_build(self, event):
        build_id = event.control.value.strip().split("-")[-1].strip()
        self.star_chart = get_star_chart(files_cache["star_chart.json"])
        if build_id == "none":
            self.config.star_chart = None
            self.star_chart_abilities = []
            await self.update_builds()
            return
        if await self.star_chart.from_string(build_id):
            await self.page.snack_bar.show(
                loc("Loaded build with id {}").format(build_id)
            )
            self.config.star_chart = build_id
            self.star_chart_abilities = self.star_chart.activated_abilities_stats
            await self.update_builds()

    async def switch_star_buff(self, event):
        event.control.data["active"] = event.control.value
        await self.update_builds()

    async def update_builds(self):
        await self.setup()
