import asyncio
import itertools
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
    Stack,
    Switch,
    Container,
    TextField,
    ElevatedButton,
    Tooltip,
)

from models.constants import files_cache
from models.interface import Controller, RTTImage, ScrollingFrame
from models.trove.builds import (
    TroveClass,
    Class,
    StatName,
    HealthOptimizerConfig,
)
from models.trove.star_chart import get_star_chart
from utils.functions import chunks
from utils.locale import loc


class HealthOptimizerController(Controller):
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
            self.config = HealthOptimizerConfig()
            self.character_data = ResponsiveRow()
            self.features = ResponsiveRow()
        self.interface.disabled = True
        await self.page.update_async()
        self.selected_class = self.classes.get(self.config.character.value, None)
        presets = await self.page.api.get_star_chart_presets()
        preset_builds = [
            [preset["build"], preset["preset"]["name"]] for preset in presets
        ]
        self.coeff_table = DataTable(
            columns=[
                DataColumn(label=Text("#")),
                DataColumn(label=Text(loc("Setup"))),
                DataColumn(label=Text(loc("Critical Hit"))),
                DataColumn(label=Text(loc("Flat Max Health"))),
                DataColumn(label=Text(loc("Bonus Max Health"))),
                DataColumn(label=Text(loc("Max Health"))),
                DataColumn(label=Text(loc("Health Deviation"))),
            ],
            heading_row_height=40,
            data_row_min_height=40,
            bgcolor="#212223",
        )
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
                                    for k, v in self.star_chart.alternate_gem_stats.items()
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
                                        ResponsiveRow(
                                            controls=[
                                                Switch(
                                                    value=self.config.weapon_ch,
                                                    on_change=self.toggle_weapon_ch,
                                                ),
                                                Text(
                                                    loc("Weapon CH"),
                                                    text_align="center",
                                                ),
                                            ],
                                            alignment="center",
                                            col={"xxl": 3},
                                        ),
                                        ResponsiveRow(
                                            controls=[
                                                Switch(
                                                    value=self.config.ring_ch,
                                                    on_change=self.toggle_ring_ch,
                                                ),
                                                Text(
                                                    loc("Ring CH"),
                                                    text_align="center",
                                                ),
                                            ],
                                            alignment="center",
                                            col={"xxl": 3},
                                        ),
                                        ResponsiveRow(
                                            controls=[
                                                Switch(
                                                    value=self.config.hat_health,
                                                    on_change=self.toggle_hat_health,
                                                ),
                                                Text(
                                                    loc("Hat MH%"),
                                                    text_align="center",
                                                ),
                                            ],
                                            alignment="center",
                                            col={"xxl": 3},
                                        ),
                                        ResponsiveRow(
                                            controls=[
                                                Switch(
                                                    value=self.config.face_health,
                                                    on_change=self.toggle_face_health,
                                                ),
                                                Text(
                                                    loc("Face MH%"),
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
        ]
        if not hasattr(self, "data_table"):
            self.data_table = Container(
                content=ResponsiveRow(controls=[ScrollingFrame(self.coeff_table)]),
                col={"xxl": 8},
            )
        if self.config.character:
            self.coeff_table.rows.clear()
            builds = self.calculate_gem_builds()
            best = builds[0]
            best_health = best[2] * (best[3] / 100 + 1)
            paged_builds = chunks(builds, 15)
            self.max_pages = len(paged_builds)
            if self.build_page < 0:
                self.build_page = self.max_pages - 1
            elif self.build_page > self.max_pages - 1:
                self.build_page = 0
            page = paged_builds[self.build_page]
            for build in page:
                rank = (builds.index(build)) + 1
                interpreted = self.interpret_gems(*build[0])
                build_health = build[2] * (build[3] / 100 + 1)
                diff = round(abs(build_health - best_health) / best_health * 100, 3)
                self.coeff_table.rows.append(
                    DataRow(
                        cells=[
                            DataCell(Text(rank)),
                            DataCell(
                                Tooltip(
                                    Text(
                                        " ".join(self.simplified_gem_format(*build[0]))
                                    ),
                                    message="\n".join(interpreted),
                                )
                            ),
                            DataCell(Text(round(build[1], 2))),
                            DataCell(Text(round(build[2], 2))),
                            DataCell(Text(f"{round(build[3], 2)}%")),
                            DataCell(Text(round(build_health))),
                            DataCell(Text(f"{diff}%" if rank != 1 else "Best")),
                        ]
                    )
                )
        self.interface.disabled = False
        await self.page.update_async()

    def setup_events(self): ...

    def simplified_gem_format(self, empowered_tuple, lesser_tuple):
        empowered_count = [empowered_tuple.count(i) for i in range(3)]
        lesser_count = [lesser_tuple.count(i) for i in range(3)]
        empowered_format = "/".join(map(str, empowered_count))
        lesser_format = "/".join(map(str, lesser_count))
        return empowered_format, lesser_format

    def interpret_gems(self, empowered_tuple, lesser_tuple):
        stat_map = {0: "CH", 1: "MH", 2: "MH%"}
        empowered_counts = {stat_map[i]: empowered_tuple.count(i) for i in range(3)}
        lesser_counts = {stat_map[i]: lesser_tuple.count(i) for i in range(3)}
        interpretation = []
        for stat, count in empowered_counts.items():
            if count > 0:
                interpretation.append(f"{count}x {stat} Empowered Gems")
        for stat, count in lesser_counts.items():
            if count > 0:
                interpretation.append(f"{count}x {stat} Lesser Gems")
        return interpretation

    def calculate_gem_builds(self):
        first = 0
        second = 0
        third = 0
        # Populate Class Bases
        for stat in self.selected_class.stats:
            if stat.name == StatName.critical_hit:
                first += stat.value
            elif stat.name == StatName.maximum_health:
                second += stat.value
            elif stat.name == StatName.maximum_health_per:
                third += stat.value
        # Add star chart stats
        for stat, value in self.star_chart.alternate_gem_stats.items():
            if stat == StatName.critical_hit.value:
                first += value[0]
            elif stat == StatName.maximum_health.value:
                second += value[0]
            elif stat == StatName.maximum_health_per.value:
                third += value[0]
        # Populate Base Critical Hit
        first += 8.8  # Dragons
        first += 10  # Club
        if self.config.weapon_ch:
            first += 7
        if self.config.ring_ch:
            first += 6.1  # Ring
        # Populate Base Max Health
        second += 50000  # Dragons
        second += 37700 * 2  # Gear
        # Populate Base Max Health %
        third += 137  # Dragons
        third += 100  # Club
        third += 500 * 0.6  # Mastery
        if self.config.hat_health:
            third += 312
        if self.config.face_health:
            third += 312
        eligible = []
        for combo, f, s, t in self.calculate_gem_stats(first, second, third):
            if f >= 100:
                eligible.append((combo, f, s, t))
        eligible.sort(key=lambda x: x[1])
        # lowest = eligible[0]
        # eligible = list(filter(lambda x: x[1] == lowest[1], eligible))
        eligible.sort(key=lambda x: (x[1], -(x[2] * x[3])))
        return eligible

    def gem_combinations(self):
        big_gems = list(itertools.product(range(3), repeat=3))
        small_gems = list(itertools.product(range(3), repeat=6))

        unique_big_gems = set(tuple(sorted(big_combo)) for big_combo in big_gems)
        unique_small_gems = set(
            tuple(sorted(small_combo)) for small_combo in small_gems
        )

        for big_combo in unique_big_gems:
            for small_combo in unique_small_gems:
                yield big_combo, small_combo

    def calculate_gem_stats(self, first, second, third):
        # Gem Stats (CH, MH, MH%)
        emp_gem_stats = [14, 36750, 367.5]
        lesser_gem_stats = [13, 33250, 332.5]
        for combo in self.gem_combinations():
            first_add, second_add, third_add = 0, 0, 0
            # Calculate empowered gem stats
            emp_combo = combo[0]
            first_add += emp_gem_stats[0] * emp_combo.count(0)
            second_add += emp_gem_stats[1] * emp_combo.count(1)
            third_add += emp_gem_stats[2] * emp_combo.count(2)
            # Calculate lesser gem stats
            lesser_combo = combo[1]
            first_add += lesser_gem_stats[0] * lesser_combo.count(0)
            second_add += lesser_gem_stats[1] * lesser_combo.count(1)
            third_add += lesser_gem_stats[2] * lesser_combo.count(2)
            # Apply Primordial dragons
            first_add *= 1.1
            second_add *= 1.1
            third_add *= 1.1
            yield combo, first + first_add, second + second_add, third + third_add

    async def set_class(self, event):
        self.config.character = Class[event.control.value]
        self.selected_class = self.classes.get(self.config.character.value, None)
        await self.update_builds()

    async def toggle_weapon_ch(self, _):
        self.config.weapon_ch = not self.config.weapon_ch
        await self.update_builds()

    async def set_cd_count(self, event):
        self.config.critical_damage_count = int(event.control.value)
        await self.update_builds()

    async def toggle_ring_ch(self, _):
        self.config.ring_ch = not self.config.ring_ch
        await self.update_builds()

    async def toggle_hat_health(self, _):
        self.config.hat_health = not self.config.hat_health
        await self.update_builds()

    async def toggle_face_health(self, _):
        self.config.face_health = not self.config.face_health
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

    async def copy_to_clipboard(self, event):
        if value := event.control.content.value:
            await self.page.set_clipboard_async(str(value))
            await self.page.snack_bar.show(loc("Copied to clipboard"))
        await self.page.update_async()

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
            self.star_chart_abilities = []
            await self.update_builds()

    async def switch_star_buff(self, event):
        event.control.data["active"] = event.control.value
        await self.update_builds()

    async def update_builds(self):
        await self.setup()
