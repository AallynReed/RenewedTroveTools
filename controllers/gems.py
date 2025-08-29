import asyncio
from copy import copy
from random import choice

import flet_core.colors
from flet import (
    ResponsiveRow,
    Column,
    Row,
    Container,
    Card,
    Text,
    Border,
    BorderSide,
    Dropdown,
    dropdown,
    Slider,
    Switch,
    ElevatedButton,
    Draggable,
    DragTarget,
    DataTable,
    DataRow,
    DataColumn,
    DataCell,
    Tabs,
    Tab,
    Stack,
)
from utils.locale import loc
from models.interface import Controller, RTTImage
from models.trove.gem import (
    LesserGem,
    EmpoweredGem,
    GemElement,
    GemTier,
    GemType,
    GemRestriction,
    Stat,
)
from models.trove.gems import max_levels, augment_costs
from utils.functions import throttle


class GemSetController(Controller):
    def setup_controls(self, gem=None):
        self.selected_gem = gem
        used_abilities = []
        if not hasattr(self, "gem_report"):
            self.gem_report = ResponsiveRow(controls=[])
        # Build a gem set
        if not hasattr(self, "gem_set"):
            self.gem_set = []
            for element in [
                GemElement.fire,
                GemElement.water,
                GemElement.air,
                GemElement.cosmic,
            ]:
                element_set = []
                for gem_builder in [EmpoweredGem, LesserGem, LesserGem]:
                    while gem := gem_builder.random_gem(element=element):
                        if isinstance(gem, EmpoweredGem):
                            if gem.ability in used_abilities:
                                continue
                            else:
                                used_abilities.append(gem.ability)
                        element_set.append(gem)
                        break
                self.gem_set.append(element_set)
        if not hasattr(self, "general_controls"):
            self.general_controls = Column(
                controls=[
                    ResponsiveRow(
                        controls=[
                            ResponsiveRow(
                                controls=[
                                    Text(loc("Gem Tier"), size=18),
                                    ElevatedButton(
                                        loc("Radiant"),
                                        on_click=self.on_full_radiant,
                                        col=4,
                                    ),
                                    ElevatedButton(
                                        loc("Stellar"),
                                        on_click=self.on_full_stellar,
                                        col=4,
                                    ),
                                    ElevatedButton(
                                        loc("Crystal"),
                                        on_click=self.on_full_crystal,
                                        col=4,
                                    ),
                                    ElevatedButton(
                                        loc("Mystic"),
                                        on_click=self.on_full_mystic,
                                        col=4,
                                    ),
                                ],
                                col={"xxl": 3},
                            ),
                            ResponsiveRow(
                                controls=[
                                    Text(loc("Gem Levels"), size=18),
                                    ElevatedButton(
                                        loc("Min"),
                                        on_click=self.on_min_level,
                                        col=6,
                                    ),
                                    ElevatedButton(
                                        loc("Max"),
                                        on_click=self.on_max_level,
                                        col=6,
                                    ),
                                    ElevatedButton(
                                        loc("5 Level"),
                                        on_click=self.on_five_level,
                                        col=4,
                                    ),
                                    ElevatedButton(
                                        loc("10 Level"),
                                        on_click=self.on_ten_level,
                                        col=4,
                                    ),
                                    ElevatedButton(
                                        loc("15 Level"),
                                        on_click=self.on_fifteen_level,
                                        col=4,
                                    ),
                                ],
                                col={"xxl": 3},
                            ),
                            ResponsiveRow(
                                controls=[
                                    Text(loc("Augmentation"), size=18),
                                    ElevatedButton(
                                        loc("Zero"),
                                        on_click=self.zero_augmentation,
                                        col=4,
                                    ),
                                    ElevatedButton(
                                        loc("Min"),
                                        on_click=self.on_min_augmentation,
                                        col=4,
                                    ),
                                    ElevatedButton(
                                        loc("Max"),
                                        on_click=self.on_max_augmentation,
                                        col=4,
                                    ),
                                ],
                                col={"xxl": 3},
                            ),
                            ResponsiveRow(
                                controls=[
                                    Text(loc("Stats"), size=18),
                                    ElevatedButton(
                                        loc("Magic"),
                                        on_click=self.on_all_magic,
                                        col=6,
                                    ),
                                    ElevatedButton(
                                        loc("Physical"),
                                        on_click=self.on_all_physical,
                                        col=6,
                                    ),
                                    ElevatedButton(
                                        loc("Damage"),
                                        on_click=self.on_full_damage,
                                        col=6,
                                    ),
                                    ElevatedButton(
                                        loc("Health"),
                                        on_click=self.on_full_health,
                                        col=6,
                                    ),
                                ],
                                col={"xxl": 3},
                            ),
                        ],
                        data="shortcuts_bar",
                    ),
                    ResponsiveRow(
                        controls=[
                            Switch(
                                value=True,
                                label=loc(element.value + " Primordial"),
                                data=element,
                                on_change=self.on_primordial_change,
                                col={"xxl": 3},
                            )
                            for element in GemElement
                        ],
                        data="dragon_controls",
                    ),
                ]
            )
        if not hasattr(self, "gem_altar"):
            self.gem_altar = ResponsiveRow()
        self.gem_altar.controls = [
            Column(
                data="gem_holder",
                controls=[
                    ResponsiveRow(
                        controls=[
                            Card(
                                Container(
                                    Row(
                                        controls=[
                                            RTTImage(
                                                "assets/images/empty.png", width=1
                                            ),
                                            Stack(
                                                controls=[
                                                    RTTImage(
                                                        f"assets/images/rarity/{gem.tier.name}_frame.png",
                                                        width=44,
                                                    ),
                                                    RTTImage(
                                                        f"assets/images/gems/old_{gem.element.name}_{gem.type.name}.png",
                                                        width=32,
                                                        left=6,
                                                        top=7,
                                                    ),
                                                ],
                                            ),
                                            Text(
                                                loc("Lvl")
                                                + f": {gem.level} "
                                                + loc(gem.name),
                                                size=15,
                                            ),
                                        ],
                                    ),
                                    data=gem,
                                    on_click=self.on_gem_click,
                                    border=Border(
                                        BorderSide(
                                            2,
                                            color=(
                                                "transparent"
                                                if self.selected_gem != gem
                                                else "green"
                                            ),
                                        ),
                                        BorderSide(
                                            2,
                                            color=(
                                                "transparent"
                                                if self.selected_gem != gem
                                                else "green"
                                            ),
                                        ),
                                        BorderSide(
                                            2,
                                            color=(
                                                "transparent"
                                                if self.selected_gem != gem
                                                else "green"
                                            ),
                                        ),
                                        BorderSide(
                                            4 if self.selected_gem != gem else 2,
                                            color=(
                                                "#" + gem.color.value
                                                if self.selected_gem != gem
                                                else "green"
                                            ),
                                        ),
                                    ),
                                    border_radius=1,
                                ),
                                col={"xxl": 4},
                            )
                            for gem in gem_row
                        ],
                    )
                    for gem_row in self.gem_set
                ],
                col={"xxl": 7},
            ),
            Column(
                data="gem_editor",
                controls=[
                    ResponsiveRow(
                        controls=[
                            ability_editor := Column(col={"xxl": 4}),
                            level_editor := Column(col={"xxl": 8}),
                            gem_editor := Column(),
                        ]
                    )
                ],
                col={"xxl": 5},
                disabled=self.selected_gem is None,
            ),
        ]
        if isinstance(self.selected_gem, EmpoweredGem):
            unused_abilities = [
                a
                for a in self.selected_gem.possible_abilities
                if a
                not in [
                    g.ability
                    for gs in self.gem_set
                    for g in gs
                    if isinstance(g, EmpoweredGem)
                ]
            ]
            unused_abilities.append(self.selected_gem.ability)
            options = [
                dropdown.Option(key=a.name, text=loc(a.value)) for a in unused_abilities
            ]
            ability_editor.controls.append(
                Dropdown(
                    value=self.selected_gem.ability.name,
                    options=options,
                    label=loc("Change Ability"),
                    on_change=self.on_gem_ability_change,
                    col=3,
                )
            )
        elif isinstance(self.selected_gem, LesserGem):
            ability_editor.controls.append(
                Dropdown(
                    value=self.selected_gem.restriction.value,
                    options=[
                        dropdown.Option(r.value, loc(f"{r.value}"))
                        for r in GemRestriction
                    ],
                    label=loc("Change Restriction"),
                    on_change=self.on_restriction_change,
                    col=3,
                )
            )
        else:
            ability_editor.controls.append(Dropdown(label=loc("Change Restriction")))
        if self.selected_gem:
            level_editor.controls.append(
                Slider(
                    min=1,
                    max=self.selected_gem.max_level,
                    value=self.selected_gem.level,
                    divisions=self.selected_gem.max_level - 1,
                    label=loc("Level") + " {value}",
                    on_change_end=self.on_gem_level_change,
                    col=8,
                )
            )
            for i, stat in enumerate(self.selected_gem.stats, 1):
                stat_row = ResponsiveRow(
                    controls=[
                        Dropdown(
                            value=stat.name.value,
                            data=stat,
                            options=[
                                dropdown.Option(s.value, text=loc(f"{s.value}"))
                                for s in self.selected_gem.possible_change_stats(stat)
                            ]
                            + [
                                dropdown.Option(
                                    stat.name.value,
                                    text=loc(stat.name.value),
                                )
                            ],
                            disabled=stat.name == Stat.light,
                            on_change=self.on_stat_change,
                            col={"xxl": 4},
                        ),
                        Text(
                            data=stat,
                            value=f"{stat.display_percentage}" + loc("% Augmentation"),
                            col={"xxl": 3, "xs": 5},
                        ),
                        Row(
                            controls=[
                                Container(
                                    RTTImage(
                                        src="assets/images/gems/augment_01.png",
                                        width=25,
                                    ),
                                    data=stat,
                                    tooltip=loc("Builder's Rough Focus"),
                                    on_click=self.on_rough_augment,
                                    disabled=stat.is_maxed,
                                ),
                                Container(
                                    RTTImage(
                                        src="assets/images/gems/augment_02.png",
                                        width=23,
                                    ),
                                    data=stat,
                                    tooltip=loc("Builder's Precise Focus"),
                                    on_click=self.on_precise_augment,
                                    disabled=stat.is_maxed,
                                ),
                                Container(
                                    RTTImage(
                                        src="assets/images/gems/augment_03.png",
                                        width=23,
                                    ),
                                    data=stat,
                                    tooltip=loc("Builder's Superior Focus"),
                                    on_click=self.on_superior_augment,
                                    disabled=stat.is_maxed,
                                ),
                                Container(
                                    RTTImage(
                                        src="assets/images/gems/chaosspark.png",
                                        width=23,
                                    ),
                                    data=stat.uuid,
                                    tooltip=loc("Chaos Contained Spark"),
                                    on_click=self.on_stat_random_change,
                                    disabled=stat.name == Stat.light,
                                ),
                                Container(
                                    RTTImage(
                                        src="assets/images/gems/chaosflare.png",
                                        width=23,
                                    ),
                                    data=stat,
                                    tooltip=loc("Chaos Contained Flare"),
                                    on_click=self.on_stat_boost_change,
                                    disabled=not bool(stat.boosts),
                                ),
                                DragTarget(
                                    data=stat.uuid,
                                    group=str(gem.uuid),
                                    content=Container(
                                        Row(
                                            controls=[
                                                Draggable(
                                                    data=stat.uuid,
                                                    group=str(gem.uuid),
                                                    content=RTTImage(
                                                        src="assets/images/gems/boost.png",
                                                        width=18,
                                                    ),
                                                )
                                                for i in range(stat.boosts)
                                            ]
                                            + [
                                                Draggable(
                                                    content=RTTImage(
                                                        src="assets/images/empty.png",
                                                        width=18,
                                                    ),
                                                    disabled=True,
                                                )
                                                for i in range(3 - stat.boosts)
                                            ]
                                        )
                                    ),
                                    on_accept=self.drop_boost,
                                    on_will_accept=self.will_drop_boost,
                                    on_leave=self.cancel_drop_boost,
                                ),
                            ],
                            col={"xxl": 5, "xs": 7},
                        ),
                    ],
                    col={"xxl": 4},
                )
                gem_editor.controls.append(stat_row)
        else:
            level_editor.controls.append(
                Slider(min=1, max=3, value=2, divisions=2, label="Level {value}")
            )
            for i in range(3):
                stat_row = ResponsiveRow(
                    controls=[
                        Dropdown(label=loc("Change Stat"), col={"xxl": 4}),
                        Text(
                            value=f"0" + loc("% Augmentation"),
                            col={"xxl": 3, "xs": 6},
                        ),
                        Row(
                            controls=[
                                Container(
                                    RTTImage(
                                        src="assets/images/gems/augment_01.png",
                                        width=25,
                                    )
                                ),
                                Container(
                                    RTTImage(
                                        src="assets/images/gems/augment_02.png",
                                        width=23,
                                    )
                                ),
                                Container(
                                    RTTImage(
                                        src="assets/images/gems/augment_03.png",
                                        width=23,
                                    )
                                ),
                                Container(
                                    RTTImage(
                                        src="assets/images/gems/chaosspark.png",
                                        width=23,
                                    )
                                ),
                                Container(
                                    RTTImage(
                                        src="assets/images/gems/chaosflare.png",
                                        width=23,
                                    )
                                ),
                            ],
                            col={"xxl": 5, "xs": 6},
                        ),
                    ],
                    vertical_alignment="center",
                    col={"xxl": 7},
                )
                gem_editor.controls.append(stat_row)
        self.calculate_gem_report()

    async def drop_boost(self, event):
        src = self.page.get_control(event.src_id)
        for gs in self.gem_set:
            for gem in gs:
                if str(gem.uuid) == event.control.group:
                    src_stat = [s for s in gem.stats if s.uuid == event.control.data][0]
                    target_stat = [s for s in gem.stats if s.uuid == src.data][0]
                    target_stat.move_boost_to(src_stat)
                    break
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def will_drop_boost(self, event):
        event.control.content.border = flet_core.border.all(2, "#2c749e")
        await self.page.update_async()

    async def cancel_drop_boost(self, event):
        event.control.content.border = None
        await self.page.update_async()

    def setup_events(self): ...

    def calculate_gem_report(self):
        self.gem_report.controls.clear()
        stats = {"Power Rank": [0, 0]}
        gems = [g for gs in self.gem_set for g in gs]
        dragon_controls = [
            c for c in self.general_controls.controls if c.data == "dragon_controls"
        ][0]
        for gem in gems:
            primordial = gem.element in [
                c.data for c in dragon_controls.controls if c.value
            ]
            for stat in gem.stats:
                if stat.name.value not in stats.keys():
                    stats[stat.name.value] = [0, 0]
                stats[stat.name.value][0] += stat.value * (1.1 if primordial else 1)
                stats[stat.name.value][1] += stat.max_value * (1.1 if primordial else 1)
            stats["Power Rank"][0] += gem.power_rank * (1.1 if primordial else 1)
        stats_card = Card(
            Column(
                controls=[
                    DataTable(
                        columns=[
                            DataColumn(Text(loc("Stats"), size=18)),
                            DataColumn(Text(loc("Value"), size=18), numeric=True),
                        ],
                        rows=[
                            DataRow(
                                cells=[
                                    DataCell(Text(loc(stat), size=13)),
                                    DataCell(
                                        Text(str(round(value[0], 2)), size=13),
                                        on_tap=self.copy_to_clipboard,
                                    ),
                                ]
                            )
                            for stat, value in stats.items()
                        ],
                        data_row_min_height=35,
                        heading_row_height=30,
                    )
                ],
            ),
            col={"xxl": 4},
        )
        low = {"rough": 0}
        medium = {"rough": 0, "precise": 0}
        high = {"rough": 0, "precise": 0, "superior": 0}
        for gs in self.gem_set:
            for gem in gs:
                for stat in gem.stats:
                    # Low cost calculation
                    difference = stat.max_augments - stat.current_augments
                    value, _ = divmod(difference, augment_costs["rough"]["weight"])
                    low["rough"] += value
                    # Medium cost calculation
                    value, diff = divmod(difference, augment_costs["precise"]["weight"])
                    medium["precise"] += value
                    value, _ = divmod(diff, augment_costs["rough"]["weight"])
                    medium["rough"] += value
                    # High cost calculation
                    value, diff = divmod(
                        difference, augment_costs["superior"]["weight"]
                    )
                    high["superior"] += value
                    value, diff = divmod(diff, augment_costs["precise"]["weight"])
                    high["precise"] += value
                    value, _ = divmod(diff, augment_costs["rough"]["weight"])
                    high["rough"] += value
        costs = {}
        for augment, _ in low.items():
            costs["low"] = {}
            for key, value in augment_costs[augment]["costs"].items():
                costs["low"][key] = value * low[augment]
        for augment, _ in medium.items():
            costs["medium"] = {}
            for key, value in augment_costs[augment]["costs"].items():
                costs["medium"][key] = value * medium[augment]
        for augment, _ in high.items():
            costs["high"] = {}
            for key, value in augment_costs[augment]["costs"].items():
                costs["high"][key] = value * high[augment]
        costs_card = Column(
            controls=[
                Text(loc("Augmentation Costs"), size=18),
                Tabs(
                    tabs=[
                        Tab(
                            text=loc("Low Cost"),
                            # content=DataTable(
                            #     columns=[
                            #         DataColumn(Text("Item")),
                            #         DataColumn(Text("Amount")),
                            #     ],
                            #     rows=[
                            #         DataRow(
                            #             cells=[
                            #                 DataCell(Text(f"{item}")),
                            #                 DataCell(Text(f"{round(cost)}"))
                            #             ]
                            #         )
                            #         for item, cost in costs["low"].items()
                            #     ]
                            # )
                        ),
                        Tab(
                            text=loc("Medium Cost"),
                        ),
                        Tab(
                            text=loc("High Cost"),
                        ),
                    ],
                ),
            ],
            horizontal_alignment="center",
            col={"xxl": 4},
        )
        self.gem_report.controls.extend(
            [
                stats_card,
                costs_card,
                Card(Text(loc("WIP"), size=18), col={"xxl": 4}),
            ]
        )
        asyncio.create_task(self.page.update_async())

    @throttle
    async def on_min_level(self, _):
        for gs in self.gem_set:
            for gem in gs:
                gem.set_level(1)
        self.setup_controls(self.selected_gem)
        await self.page.snack_bar.show(loc("All gems have had their level set to 1."))
        await self.page.update_async()

    @throttle
    async def on_five_level(self, _):
        for gs in self.gem_set:
            for gem in gs:
                gem.set_level(5)
        await self.page.snack_bar.show(loc("All gems have had their level set to 5."))
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    @throttle
    async def on_ten_level(self, _):
        for gs in self.gem_set:
            for gem in gs:
                gem.set_level(10)
        await self.page.snack_bar.show(loc("All gems have had their level set to 10."))
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    @throttle
    async def on_fifteen_level(self, _):
        for gs in self.gem_set:
            for gem in gs:
                gem.set_level(15)
        await self.page.snack_bar.show(loc("All gems have had their level set to 15."))
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    @throttle
    async def on_max_level(self, _):
        for gs in self.gem_set:
            for gem in gs:
                gem.set_level(max_levels[gem.tier.name])
        self.setup_controls(self.selected_gem)
        await self.page.snack_bar.show(loc("All gems have had their level maxed out."))

    @throttle
    async def zero_augmentation(self, _):
        for gs in self.gem_set:
            for gem in gs:
                for stat in gem.stats:
                    stat.zero_augments()
        self.setup_controls(self.selected_gem)
        await self.page.snack_bar.show(
            loc(
                "All gems have been zero-ed in augmentation (This is irreversible, reroll gems to get new ones)"
            )
        )

    @throttle
    async def on_min_augmentation(self, _):
        for gs in self.gem_set:
            for gem in gs:
                for stat in gem.stats:
                    stat.reset_augments()
        self.setup_controls(self.selected_gem)
        await self.page.snack_bar.show(loc("All gems have been de-augmented."))

    @throttle
    async def on_max_augmentation(self, _):
        for gs in self.gem_set:
            for gem in gs:
                for stat in gem.stats:
                    while not stat.is_maxed:
                        stat.add_superior_focus()
        self.setup_controls(self.selected_gem)
        await self.page.snack_bar.show(loc("All gems have fully augmented."))

    @throttle
    async def on_all_magic(self, _):
        for gs in self.gem_set:
            for gem in gs:
                if gem.type == GemType.lesser:
                    gem.change_restriction(GemRestriction.arcane)
                else:
                    for stat in gem.stats:
                        if stat.name == Stat.physical_damage:
                            stat.name = Stat.magic_damage
        self.setup_controls(self.selected_gem)
        await self.page.snack_bar.show(
            loc("All gems have had their Physical damage stat changed to Magic Damage")
        )

    @throttle
    async def on_all_physical(self, _):
        for gs in self.gem_set:
            for gem in gs:
                if gem.type == GemType.lesser:
                    gem.change_restriction(GemRestriction.fierce)
                else:
                    for stat in gem.stats:
                        if stat.name == Stat.magic_damage:
                            stat.name = Stat.physical_damage
        self.setup_controls(self.selected_gem)
        await self.page.snack_bar.show(
            loc("All gems have had their Magic damage stat changed to Physical Damage")
        )

    @throttle
    async def on_full_damage(self, _):
        stats = []
        lesser_gems = [
            gem for gs in self.gem_set for gem in gs if gem.type == GemType.lesser
        ]
        restrictions = len(
            [g for g in lesser_gems if g.restriction == GemRestriction.arcane]
        )
        if restrictions == len(lesser_gems):
            restriction = GemRestriction.arcane
            stats.append(Stat.magic_damage)
        elif not restrictions:
            restriction = GemRestriction.fierce
            stats.append(Stat.physical_damage)
        else:
            stats.append(choice([Stat.physical_damage, Stat.magic_damage]))
            if stats[0] == Stat.magic_damage:
                restriction = GemRestriction.arcane
            else:
                restriction = GemRestriction.fierce
        stats.append(Stat.critical_damage)
        stats.append(Stat.critical_hit)
        for gs in self.gem_set:
            for gem in gs:
                if gem.element == GemElement.cosmic:
                    zipped_stats = zip(gem.stats[1:], stats[:-1])
                else:
                    zipped_stats = zip(gem.stats, stats)
                if gem.type == GemType.lesser:
                    gem.change_restriction(restriction)
                    for stat, new_stat in zipped_stats:
                        stat.name = new_stat
                elif gem.type == GemType.empowered:
                    for stat, new_stat in zipped_stats:
                        stat.name = new_stat
        self.setup_controls(self.selected_gem)
        await self.page.snack_bar.show(
            loc("All gems have had their stats tuned for damage.")
        )

    @throttle
    async def on_full_health(self, _):
        stats = []
        stats.append(Stat.maximum_health)
        stats.append(Stat.maximum_health_per)
        stats.append(Stat.critical_hit)
        for gs in self.gem_set:
            for gem in gs:
                if gem.element == GemElement.cosmic:
                    zipped_stats = zip(gem.stats[1:], stats[:-1])
                else:
                    zipped_stats = zip(gem.stats, stats)
                if gem.type == GemType.lesser:
                    for stat, new_stat in zipped_stats:
                        stat.name = new_stat
                elif gem.type == GemType.empowered:
                    for stat, new_stat in zipped_stats:
                        stat.name = new_stat
        self.setup_controls(self.selected_gem)
        await self.page.snack_bar.show(
            loc("All gems have had their stats tuned for health.")
        )

    async def on_full_radiant(self, event):
        for gs in self.gem_set:
            for i, gem in enumerate(copy(gs)):
                if gem.tier != GemTier.radiant:
                    if gem.type == GemType.empowered:
                        gem = EmpoweredGem.random_gem(
                            tier=GemTier.radiant, element=gem.element
                        )
                    elif gem.type == GemType.lesser:
                        gem = LesserGem.random_gem(
                            tier=GemTier.radiant, element=gem.element
                        )
                    gs[i] = gem
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def on_full_stellar(self, event):
        for gs in self.gem_set:
            for i, gem in enumerate(copy(gs)):
                if gem.tier != GemTier.stellar:
                    if gem.type == GemType.empowered:
                        gem = EmpoweredGem.random_gem(
                            tier=GemTier.stellar, element=gem.element
                        )
                    elif gem.type == GemType.lesser:
                        gem = LesserGem.random_gem(
                            tier=GemTier.stellar, element=gem.element
                        )
                    gs[i] = gem
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def on_full_crystal(self, event):
        for gs in self.gem_set:
            for i, gem in enumerate(copy(gs)):
                if gem.tier != GemTier.crystal:
                    if gem.type == GemType.empowered:
                        gem = EmpoweredGem.random_gem(
                            tier=GemTier.crystal, element=gem.element
                        )
                    elif gem.type == GemType.lesser:
                        gem = LesserGem.random_gem(
                            tier=GemTier.crystal, element=gem.element
                        )
                    gs[i] = gem
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def on_full_mystic(self, event):
        for gs in self.gem_set:
            for i, gem in enumerate(copy(gs)):
                if gem.tier != GemTier.mystic:
                    if gem.type == GemType.empowered:
                        gem = EmpoweredGem.random_gem(
                            tier=GemTier.mystic, element=gem.element
                        )
                    elif gem.type == GemType.lesser:
                        gem = LesserGem.random_gem(
                            tier=GemTier.mystic, element=gem.element
                        )
                    gs[i] = gem
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def on_primordial_change(self, _):
        self.calculate_gem_report()

    async def on_gem_click(self, event):
        if self.selected_gem == event.control.data:
            self.setup_controls()
        else:
            self.setup_controls(event.control.data)
        await self.page.update_async()

    @throttle
    async def on_gem_level_change(self, event):
        self.selected_gem.set_level(int(event.control.value))
        await self.page.snack_bar.show(
            loc("Gem level changed to {level}").format(level=self.selected_gem.level)
        )
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def on_restriction_change(self, event):
        self.selected_gem.change_restriction(GemRestriction(event.control.value))
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def on_gem_ability_change(self, event):
        self.selected_gem.ability = [
            a
            for a in self.selected_gem.possible_abilities
            if a.name == event.control.value
        ][0]
        self.setup_controls(self.selected_gem)
        await self.page.snack_bar.show(loc("Updated Ability"))
        await self.page.update_async()

    async def on_stat_change(self, event):
        event.control.data.name = Stat(event.control.value)
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    @throttle
    async def on_stat_random_change(self, event):
        stat = [s for s in self.selected_gem.stats if s.uuid == event.control.data][0]
        possible_stats = [s for s in self.selected_gem.possible_change_stats(stat)]
        stat.name = choice(possible_stats)
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def on_stat_boost_change(self, event):
        stats = [s for s in self.selected_gem.stats if s != event.control.data]
        event.control.data.move_boost_to(choice(stats))
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def on_rough_augment(self, event):
        event.control.data.add_rough_focus()
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def on_precise_augment(self, event):
        event.control.data.add_precise_focus()
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def on_superior_augment(self, event):
        event.control.data.add_superior_focus()
        self.setup_controls(self.selected_gem)
        await self.page.update_async()

    async def copy_to_clipboard(self, event):
        if value := event.control.content.value:
            await self.page.set_clipboard_async(str(value))
            await self.page.snack_bar.show(loc("Copied to clipboard"))
        await self.page.update_async()
