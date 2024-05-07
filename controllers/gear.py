from flet import (
    Text,
    Card,
    ResponsiveRow,
    Row,
    padding,
    Container,
    Dropdown,
    dropdown,
    icons,
    Icon,
)
from utils.locale import loc

from models.interface import Controller
from models.constants import files_cache


class GearBuildsController(Controller):
    def setup_controls(self):
        self.main = ResponsiveRow()
        self.gear_builds = files_cache["builds/builds.json"]
        self.load_interface()

    def setup_events(self): ...

    def setup_memory(self):
        self.memory = {"class": None, "build": None}

    def load_interface(self):
        if not hasattr(self, "memory"):
            self.setup_memory()
            classes = sorted(self.gear_builds.keys())
            self.memory["class"] = classes[0]
            self.class_select = Dropdown(
                label="Class",
                value=classes[0],
                options=[dropdown.Option(key=cl, text=loc(cl)) for cl in classes],
                on_change=self.set_class,
            )
            self.build_type_select = Dropdown(
                label="Build Type",
                options=[
                    dropdown.Option(key=build, text=loc(build.capitalize()))
                    for build, data in self.gear_builds[classes[0]].items()
                    if data["enabled"]
                ],
                on_change=self.set_type,
            )
            self.main.controls.append(
                Row(controls=[self.class_select, self.build_type_select])
            )
            self.gear_interface = ResponsiveRow()
            self.main.controls.append(self.gear_interface)

    async def set_class(self, event):
        self.memory["class"] = event.control.value
        self.build_type_select.value = None
        self.build_type_select.options.clear()
        self.build_type_select.options.extend(
            [
                dropdown.Option(key=build, text=build.capitalize())
                for build, data in self.gear_builds[event.control.value].items()
                if data["enabled"]
            ]
        )
        await self.build_type_select.update_async()
        self.gear_interface.controls.clear()
        await self.gear_interface.update_async()

    async def set_type(self, event):
        self.memory["build"] = event.control.value
        cl = self.memory["class"]
        build_type = self.memory["build"]
        build_data = self.gear_builds[cl][build_type]
        self.gear_interface.controls = self.get_build_ui(build_data)
        await self.gear_interface.update_async()

    def get_build_ui(self, data):
        interface = []
        stars = 6 - data["tier"]
        outlines = data["tier"] - 1
        interface.append(
            Row(
                controls=[Text(loc("Rating") + ":", size=24)]
                + [Icon(icons.STAR) for i in range(stars)]
                + [Icon(icons.STAR_OUTLINE) for i in range(outlines)]
            )
        )
        for equip in [
            "hat",
            "weapon",
            "face",
            "ring",
            "banner",
            "ally",
            "flask",
            "emblem",
            "food",
            "subclass",
            "gems",
        ]:
            interface.append(
                Card(
                    content=Container(
                        ResponsiveRow(
                            controls=[
                                Text(
                                    loc(equip.capitalize()),
                                    text_align="center",
                                    size=28,
                                ),
                                ResponsiveRow(
                                    controls=[
                                        *(
                                            [
                                                Text(loc(stat), selectable=True)
                                                for stat in data[equip]
                                            ]
                                        ),
                                    ],
                                ),
                            ],
                        ),
                        padding=padding.symmetric(6, 6),
                    ),
                    height=220,
                    col=3,
                )
            )
        return interface
