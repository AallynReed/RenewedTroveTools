from flet import ResponsiveRow, Column, Switch, Card, Text, TextField, Row

from models.interface import AutoNumberField, NumberField
from models.interface import Controller
from models.trove.star_chart import get_star_chart


class MagicFindController(Controller):
    def setup_controls(self):
        if not hasattr(self, "interface"):
            self.star_chart = get_star_chart(self.page.data_files["star_chart.json"])
            self.interface = ResponsiveRow(vertical_alignment="START")
            self.control_values = {"mastery": 250, "Sunday": True, "Patron": True}
        self.magic_find_data = self.page.data_files["builds/magic_find.json"]
        buttons = [
            ResponsiveRow(
                controls=[
                    NumberField(
                        data="mastery",
                        type=int,
                        value=self.control_values["mastery"] + 500,
                        min=500,
                        max=1000,
                        on_change=self.mastery_stat,
                        label="Mastery Level",
                        col={"xxl": 6},
                    )
                ]
            )
        ]
        for source in self.magic_find_data:
            if source["name"] not in self.control_values:
                self.control_values[source["name"]] = (
                    True if source["type"] == "switch" else source["value"]
                )
            if source["type"] == "switch":
                control = Row(
                    controls=[
                        Switch(
                            data=source["name"],
                            value=self.control_values[source["name"]],
                            on_change=self.switch_stat,
                        ),
                        Text(
                            (
                                source["name"]
                                + " \u2022 "
                                + str(
                                    source["value"]
                                    if not source["percentage"]
                                    else f"{round(source['value'], 2)}%"
                                )
                            ),
                        ),
                    ]
                )
            elif source["type"] == "slider":
                control = ResponsiveRow(
                    controls=[
                        AutoNumberField(
                            data=source["name"],
                            type=int,
                            value=self.control_values[source["name"]],
                            min=0,
                            max=source["value"],
                            step=50,
                            on_change=self.slider_stat,
                            label=source["name"],
                        )
                    ]
                )
            else:
                continue
            control.col = {"xxl": 6}
            buttons.append(control)
        buttons.append(
            Row(
                controls=[
                    Switch(
                        data="Sunday",
                        value=self.control_values["Sunday"],
                        col=3,
                        on_change=self.switch_stat,
                    ),
                    Text(
                        f"Sunday Loot Day \u2022 {400 if self.control_values['Patron'] else 100}",
                        col=9,
                    ),
                ],
                col={"xxl": 6},
            )
        )
        buttons.append(
            Row(
                controls=[
                    Switch(
                        data="Patron",
                        value=self.control_values["Patron"],
                        col=3,
                        on_change=self.switch_stat,
                    ),
                    Text("Patron \u2022 200%", col=9),
                ],
                col={"xxl": 6},
            )
        )
        buttons.append(
            TextField(
                hint_text='Star Chart Build ID | "none" to remove',
                on_change=self.set_star_chart_build,
                text_size=14,
                height=58,
                col={"xxl": 6},
            )
        )
        buttons.append(
            Column(
                controls=[
                    Text(f"{k}: {v[0]}" + ("%" if v[1] else ""))
                    for k, v in self.star_chart.activated_select_stats(
                        "Magic Find"
                    ).items()
                ]
            )
        )
        result = 0
        result += self.control_values["mastery"]
        for k, v in self.star_chart.activated_select_stats("Magic Find").items():
            if not v[1]:
                result += v[0]
        bonus = 0
        for (_, v), source in zip(
            list(self.control_values.items())[3:], self.magic_find_data
        ):
            if isinstance(v, bool):
                v = source["value"] if v else 0
            if not source["percentage"]:
                result += v
            else:
                bonus += v
        for k, v in self.star_chart.activated_select_stats("Magic Find").items():
            if v[1]:
                bonus += v[0]
        result *= 1 + bonus / 100
        result *= 2 if self.control_values["Patron"] else 1
        sunday_bonus = (
            (400 if self.control_values["Patron"] else 100)
            if self.control_values["Sunday"]
            else 0
        )
        sunday_bonus *= 1 + bonus / 100
        result += sunday_bonus
        self.results = Card(
            Text(f"Magic Find: {round(result)}", size=50), col={"xxl": 3.5}
        )
        self.interface.controls = [
            Card(
                content=Column(controls=[ResponsiveRow(controls=buttons)]),
                col={"xxl": 5},
            ),
            self.results,
        ]

    def setup_events(self): ...

    async def switch_stat(self, event):
        self.control_values[event.control.data] = event.control.value
        self.page.snack_bar.content.value = f"Updated {event.control.data}"
        self.page.snack_bar.open = True
        self.setup_controls()
        await self.page.update_async()

    async def slider_stat(self, event):
        self.control_values[event.control.data] = int(event.control.value)
        self.page.snack_bar.content.value = f"Updated {event.control.data}"
        self.page.snack_bar.open = True
        self.setup_controls()
        await self.page.update_async()

    async def mastery_stat(self, event):
        self.control_values[event.control.data] = int(event.control.value) - 500
        self.page.snack_bar.content.value = f"Updated {event.control.data}"
        self.page.snack_bar.open = True
        self.setup_controls()
        await self.page.update_async()

    async def set_star_chart_build(self, event):
        build_id = event.control.value.strip().split("-")[-1].strip()
        self.star_chart = get_star_chart(self.page.data_files["star_chart.json"])
        if build_id == "none":
            self.setup_controls()
            await self.page.update_async()
            return
        if await self.star_chart.from_string(build_id):
            self.page.snack_bar.content.value = f"Loaded build with id {build_id}"
            self.page.snack_bar.open = True
            self.setup_controls()
            await self.page.update_async()
