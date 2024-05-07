import asyncio
from random import choice

from flet import (
    ResponsiveRow,
    Column,
    Row,
    Container,
    Card,
    Image,
    Text,
    Border,
    BorderSide,
    Switch,
    ElevatedButton,
    Draggable,
    DragTarget,
    Stack,
)
from utils.locale import loc

from models.interface import Controller
from models.trove.gem import (
    LesserGem,
    EmpoweredGem,
    GemTier,
    GemTierColor,
    Stat,
)


class GemController(Controller):
    def setup_controls(self, gem=None, stat=None):
        if not hasattr(self, "header_row"):
            self.header_row = ResponsiveRow()
        if not hasattr(self, "selected_gem"):
            self.empower = False
            self.selected_gem = LesserGem.random_gem()
        if gem:
            self.selected_gem = gem
        self.selected_stat = stat
        self.header_row.controls.clear()
        self.header_row.controls.append(
            Column(
                controls=[
                    Row(
                        controls=[
                            ElevatedButton(
                                text=loc("Radiant"),
                                on_click=self.reroll_radiant,
                                bgcolor=GemTierColor.radiant.value,
                                color="black",
                            ),
                            ElevatedButton(
                                text=loc("Stellar"),
                                on_click=self.reroll_stellar,
                                bgcolor=GemTierColor.stellar.value,
                                color="black",
                            ),
                            ElevatedButton(
                                text=loc("Crystal"),
                                on_click=self.reroll_crystal,
                                bgcolor=GemTierColor.crystal.value,
                                color="black",
                            ),
                            Text(loc("Lesser")),
                            Switch(value=self.empower, on_change=self.switch_empower),
                            Text(loc("Empowered")),
                        ],
                        alignment="center",
                    ),
                    Text(
                        value=loc(self.selected_gem.name)
                        + ": "
                        + loc("Level")
                        + f" {self.selected_gem.level}",
                        size=22,
                        color=f"#{self.selected_gem.color.value}",
                    ),
                    Text(
                        value=loc("Power Rank")
                        + f": {round(self.selected_gem.power_rank)}",
                        size=19,
                    ),
                    DragTarget(
                        content=Stack(
                            controls=[
                                Image(
                                    f"assets/images/rarity/{self.selected_gem.tier.name}_frame.png",
                                    scale=5,
                                    left=89,
                                    top=89,
                                ),
                                Draggable(
                                    data=self.selected_gem,
                                    content=Image(
                                        f"assets/images/gems/old_{self.selected_gem.element.name}_{self.selected_gem.type.name}.png",
                                        scale=1.25,
                                    ),
                                    content_feedback=Image(
                                        f"assets/images/gems/old_{self.selected_gem.element.name}_{self.selected_gem.type.name}.png",
                                        scale=0.40,
                                    ),
                                ),
                            ],
                            scale=0.5,
                        ),
                    ),
                    Row(
                        controls=[
                            ElevatedButton(
                                loc("Min"),
                                on_click=self.max_level_down,
                                disabled=self.selected_gem.level == 1,
                            ),
                            ElevatedButton(
                                loc("Level Down"),
                                on_click=self.level_down,
                                disabled=self.selected_gem.level == 1,
                            ),
                            ElevatedButton(
                                loc("Level 15"),
                                on_click=self.level_fifteen,
                                disabled=self.selected_gem.level == 15,
                            ),
                            ElevatedButton(
                                loc("Level Up"),
                                on_click=self.level_up,
                                disabled=self.selected_gem.level
                                == self.selected_gem.max_level,
                            ),
                            ElevatedButton(
                                loc("Max"),
                                on_click=self.max_level_up,
                                disabled=self.selected_gem.level
                                == self.selected_gem.max_level,
                            ),
                        ],
                        alignment="center",
                    ),
                    *[
                        Stack(
                            controls=[
                                Container(
                                    Card(
                                        Container(
                                            Column(
                                                controls=[
                                                    Row(
                                                        controls=[
                                                            Text(
                                                                str(
                                                                    round(stat.value, 3)
                                                                ),
                                                                color="green",
                                                            ),
                                                            Text(
                                                                loc(
                                                                    f"{stat.name.value}"
                                                                ),
                                                                weight="bold",
                                                            ),
                                                            Text(
                                                                f"({stat.display_percentage}%)",
                                                                expand=True,
                                                                color=(
                                                                    "red"
                                                                    if stat.percentage
                                                                    < 1 / 3
                                                                    else (
                                                                        "yellow"
                                                                        if stat.percentage
                                                                        < 1 / 3 * 2
                                                                        else "green"
                                                                    )
                                                                ),
                                                            ),
                                                            Text(
                                                                f"{stat.min_value} - {stat.max_value}"
                                                            ),
                                                        ],
                                                    ),
                                                    ResponsiveRow(
                                                        controls=[
                                                            *[
                                                                Container(
                                                                    Text(
                                                                        f"{round(container.percentage * 100, 2)}%",
                                                                        text_align="center",
                                                                    ),
                                                                    border=Border(
                                                                        *(
                                                                            [
                                                                                BorderSide(
                                                                                    2,
                                                                                    "blue",
                                                                                )
                                                                            ]
                                                                            * 4
                                                                        )
                                                                    ),
                                                                    border_radius=0,
                                                                    col=3,
                                                                )
                                                                for container in stat.containers
                                                            ],
                                                            *[
                                                                Container(
                                                                    Text(
                                                                        text_align="center"
                                                                    ),
                                                                    border=Border(
                                                                        *(
                                                                            [
                                                                                BorderSide(
                                                                                    2,
                                                                                    "black",
                                                                                )
                                                                            ]
                                                                            * 4
                                                                        )
                                                                    ),
                                                                    border_radius=0,
                                                                    col=3,
                                                                )
                                                                for _ in range(
                                                                    3 - stat.boosts
                                                                )
                                                            ],
                                                        ],
                                                        spacing=0,
                                                    ),
                                                ]
                                            ),
                                            padding=18,
                                            border=Border(
                                                *(
                                                    [
                                                        BorderSide(
                                                            2,
                                                            (
                                                                "transparent"
                                                                if stat
                                                                != self.selected_stat
                                                                else "green"
                                                            ),
                                                        )
                                                    ]
                                                    * 4
                                                )
                                            ),
                                            border_radius=5,
                                            disabled=not bool(self.selected_gem),
                                            on_click=self.select_stat,
                                            data=stat,
                                        )
                                    ),
                                ),
                                *[
                                    Image(
                                        "assets/images/gems/boost.png",
                                        width=18,
                                        left=20 * i,
                                        top=0,
                                    )
                                    for i in range(stat.boosts)
                                ],
                            ],
                        )
                        for stat in self.selected_gem.stats
                    ],
                    ResponsiveRow(
                        controls=[
                            Column(
                                controls=[
                                    ResponsiveRow(
                                        controls=[
                                            Container(col={"xs": 3}),
                                            Text(
                                                loc("Improve Stat"),
                                                text_align="center",
                                                col={"xs": 5},
                                            ),
                                            Container(col={"xs": 4}),
                                        ],
                                        alignment="center",
                                    ),
                                    ResponsiveRow(
                                        controls=[
                                            Container(col={"xs": 3.3}),
                                            Container(
                                                content=Image(
                                                    "assets/images/gems/augment_01.png",
                                                    width=40,
                                                ),
                                                disabled=not bool(self.selected_stat)
                                                or self.selected_stat.is_maxed,
                                                on_click=self.rough_augment,
                                                col={"xs": 1.5},
                                            ),
                                            Container(
                                                content=Image(
                                                    "assets/images/gems/augment_02.png",
                                                    width=40,
                                                ),
                                                disabled=not bool(self.selected_stat)
                                                or self.selected_stat.is_maxed,
                                                on_click=self.precise_augment,
                                                col={"xs": 1.5},
                                            ),
                                            Container(
                                                content=Image(
                                                    "assets/images/gems/augment_03.png",
                                                    width=40,
                                                ),
                                                disabled=not bool(self.selected_stat)
                                                or self.selected_stat.is_maxed,
                                                on_click=self.superior_augment,
                                                col={"xs": 1.5},
                                            ),
                                            Container(col={"xs": 3}),
                                        ],
                                    ),
                                    ResponsiveRow(
                                        controls=[
                                            Container(col={"xs": 3.3}),
                                            Container(
                                                content=Text(
                                                    f"{round(2.5/(stat.boosts + 1), 2)}%"
                                                    if stat
                                                    else "2.50%"
                                                ),
                                                col={"xs": 1.5},
                                            ),
                                            Container(
                                                content=Text(
                                                    f"{round(5.0/(stat.boosts + 1), 2)}%"
                                                    if stat
                                                    else "5.00%"
                                                ),
                                                col={"xs": 1.5},
                                            ),
                                            Container(
                                                content=Text(
                                                    f"{round(12.5/(stat.boosts + 1), 2)}%"
                                                    if stat
                                                    else "12.5%"
                                                ),
                                                col={"xs": 1.5},
                                            ),
                                            Container(col={"xs": 3}),
                                        ],
                                    ),
                                    Container(col={"xs": 1}),
                                ],
                                col={"xs": 8},
                            ),
                            Column(
                                controls=[
                                    ResponsiveRow(
                                        controls=[
                                            Text(
                                                loc("Reroll Stat"),
                                                text_align="center",
                                                col={"xs": 5},
                                            ),
                                            Container(col={"xs": 6}),
                                        ],
                                        alignment="center",
                                    ),
                                    ResponsiveRow(
                                        controls=[
                                            Container(
                                                content=Image(
                                                    "assets/images/gems/chaosspark.png",
                                                    width=43,
                                                ),
                                                disabled=(
                                                    not bool(self.selected_stat)
                                                    or (
                                                        self.selected_stat
                                                        and self.selected_stat.name
                                                        == Stat.light
                                                    )
                                                ),
                                                on_click=self.change_stat,
                                                col={"xs": 3.5},
                                            ),
                                            Container(
                                                content=Image(
                                                    "assets/images/gems/chaosflare.png",
                                                    width=43,
                                                ),
                                                disabled=not bool(self.selected_stat)
                                                or not self.selected_stat.boosts,
                                                on_click=self.move_boost,
                                                col={"xs": 3.5},
                                            ),
                                        ],
                                    ),
                                    ResponsiveRow(
                                        controls=[
                                            Container(
                                                content=Text(
                                                    loc("Change Stat"),
                                                    size=11,
                                                    text_align="center",
                                                ),
                                                col={"xs": 3.5},
                                            ),
                                            Container(
                                                content=Text(
                                                    loc("Move Boost"),
                                                    size=11,
                                                    text_align="center",
                                                ),
                                                col={"xs": 3.5},
                                            ),
                                        ],
                                    ),
                                ],
                                horizontal_alignment="top",
                                col={"xs": 4},
                            ),
                        ],
                        alignment="center",
                    ),
                ],
                horizontal_alignment="center",
                col={"xxl": 4},
                spacing=2,
            )
        )
        asyncio.create_task(self.page.update_async())

    def setup_events(self): ...

    async def select_stat(self, event):
        if self.selected_stat == event.control.data:
            self.selected_stat = None
        else:
            self.selected_stat = event.control.data
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def switch_empower(self, event):
        self.empower = event.control.value
        if self.empower:
            gem = EmpoweredGem.random_gem(
                element=self.selected_gem.element, tier=self.selected_gem.tier
            )
        else:
            gem = LesserGem.random_gem(
                element=self.selected_gem.element, tier=self.selected_gem.tier
            )
        self.setup_controls(gem, None)

    async def reroll_radiant(self, _):
        gem_type = EmpoweredGem if self.empower else LesserGem
        self.setup_controls(gem_type.random_gem(GemTier.radiant), None)

    async def reroll_stellar(self, _):
        gem_type = EmpoweredGem if self.empower else LesserGem
        self.setup_controls(gem_type.random_gem(GemTier.stellar), None)

    async def reroll_crystal(self, _):
        gem_type = EmpoweredGem if self.empower else LesserGem
        self.setup_controls(gem_type.random_gem(GemTier.crystal), None)

    async def max_level_down(self, _):
        self.selected_gem.set_level(1)
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def level_down(self, _):
        self.selected_gem.set_level(self.selected_gem.level - 1)
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def level_fifteen(self, _):
        self.selected_gem.set_level(15)
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def level_up(self, _):
        self.selected_gem.set_level(self.selected_gem.level + 1)
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def max_level_up(self, _):
        self.selected_gem.set_level(self.selected_gem.max_level)
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def rough_augment(self, _):
        self.selected_stat.add_rough_focus()
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def precise_augment(self, _):
        self.selected_stat.add_precise_focus()
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def superior_augment(self, _):
        self.selected_stat.add_superior_focus()
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def change_stat(self, _):
        possible_stats = [
            s for s in self.selected_gem.possible_change_stats(self.selected_stat)
        ]
        self.selected_stat.name = choice(possible_stats)
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def move_boost(self, _):
        stats = [s for s in self.selected_gem.stats if s != self.selected_stat]
        self.selected_stat.move_boost_to(choice(stats))
        self.setup_controls(self.selected_gem, self.selected_stat)

    async def copy_to_clipboard(self, event):
        if value := event.control.content.value:
            await self.page.set_clipboard_async(str(value))
            await self.page.snack_bar.show("Copied to clipboard")
        await self.page.update_async()
