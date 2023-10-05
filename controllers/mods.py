import asyncio
import os
import re
from pathlib import Path

from flet import Container, Column, Row, Tabs, Tab, TextButton, IconButton, Icon, Image, Padding, DataTable, \
    DataColumn, DataRow, DataCell, Text, Switch, MainAxisAlignment, Divider, Stack, Card
from flet_core.icons import (REFRESH, DRIVE_FILE_RENAME_OUTLINE_SHARP, PERSON_SHARP,
                             FOLDER_ZIP_SHARP, NOTES_SHARP, CONSTRUCTION_SHARP, WARNING_SHARP)

from models.interface import Controller
from models.trove.mods import TMod
from utils.functions import get_attr
from utils.trove.registry import GetTroveLocations
from utils.trovesaurus import get_mods_list


class ModsController(Controller):
    def setup_controls(self):
        if not hasattr(self, "locations") or self.refresh_locations:
            trove_cfg = Path(os.getenv("APPDATA")).joinpath("Trove/Trove.cfg").read_text()
            disabled_mods = re.findall(r"^DisabledMods ?= ?(.*)$", trove_cfg, re.MULTILINE)[0].split("|")
            self.disabled_mods = [re.findall("^Trove-(.*?)-(\w+)$", mod)[0] for mod in disabled_mods if mod != ""]
            self.location_names = list(GetTroveLocations())
            if not hasattr(self, "locations"):
                self.main = Column()
                self.selected_location = str(self.location_names[0][1])
            self.locations = {}
            for name, path in self.location_names:
                used_files = {}
                mods_path = path.joinpath("mods")
                enabled = []
                disabled = []
                cfg_disabled = []
                conflicts = {}
                bad_name = []
                for mod in list(mods_path.glob("*.tmod")) + list(mods_path.glob("*.tmod.disabled")):
                    try:
                        tmod = TMod.read(mod)
                    except:
                        print("Failed to read mod:", mod)
                        continue
                    suffixes = "".join(mod.suffixes)
                    data = re.findall(f"(.*){suffixes}$", str(mod.name), re.IGNORECASE)
                    title = get_attr(tmod.metadata.properties, name="title")
                    author = get_attr(tmod.metadata.properties, name="author")
                    previewPath = get_attr(tmod.metadata.properties, name="previewPath")
                    if title.value != data[0]:
                        bad_name.append(tmod)
                    for file in tmod.files:
                        if file.name != previewPath.value:
                            if file.name not in used_files:
                                used_files[file.name] = []
                            used_files[file.name].append(tmod)
                    for file, mods in used_files.items():
                        if len(mods) > 1:
                            for cmod in mods:
                                if cmod not in conflicts:
                                    conflicts[cmod] = []
                                for ccmod in mods:
                                    if ccmod != cmod and ccmod not in conflicts[cmod]:
                                        conflicts[cmod].append(ccmod)
                    if mod.suffix == ".tmod":
                        enabled.append(tmod)
                    elif (get_attr(tmod.metadata.properties, name="title").value,
                         get_attr(tmod.metadata.properties, name="author").value) not in self.disabled_mods:
                        cfg_disabled.append(tmod)
                    else:
                        disabled.append(tmod)
                mods = enabled + disabled + cfg_disabled
                mods.sort(key=lambda mod: get_attr(mod.metadata.properties, name="title").value)
                self.locations[str(path)] = {
                    "type": name,
                    "mods": mods,
                    "enabled": enabled,
                    "disabled": disabled,
                    "cfg_disabled": cfg_disabled,
                    "conflicts": conflicts,
                    "bad_name": bad_name
                }
            self.refresh_locations = False
        asyncio.create_task(self.post_setup())

    async def post_setup(self):
        if not hasattr(self, "trovesaurus_mods"):
            self.trovesaurus_mods = await get_mods_list()
        self.mods_list = DataTable(
            columns=[
                DataColumn(
                    label=Text("Image"),
                ),
                DataColumn(
                    label=Text("Name"),
                ),
                DataColumn(
                    label=Text("Author"),
                ),
                DataColumn(
                    label=Text("Actions"),
                ),
            ],
            rows=[
                DataRow(
                    cells=[
                        DataCell(
                            content=Text("Image")
                        ),
                        DataCell(
                            content=Text(get_attr(mod.metadata.properties, name="title").value)
                        ),
                        DataCell(
                            content=Text(get_attr(mod.metadata.properties, name="author").value)
                        ),
                        DataCell(
                            content=Row(
                                controls=[
                                    Switch(
                                        value=mod in self.locations[self.selected_location]["enabled"]
                                    ),
                                    *(
                                        [
                                            IconButton(
                                                DRIVE_FILE_RENAME_OUTLINE_SHARP,
                                                data=mod,
                                                on_click=self.fix_bad_name,
                                            ),
                                        ]
                                        if mod in self.locations[self.selected_location]["bad_name"]
                                        else []

                                    )
                                ]
                            )
                        ),
                    ]
                )
                for mod in sorted(self.locations[self.selected_location]["mods"],
                    key=lambda mod: get_attr(mod.metadata.properties, name="title").value)
            ]
        )

        self.mod_list = Column(
            expand=True
        )

        for mod in self.locations[self.selected_location]["mods"]:
            mod_name = get_attr(mod.metadata.properties, name="title").value
            trovesaurus_mod = next(
                (
                    tmod
                    for tmod in self.trovesaurus_mods
                    if mod_name == tmod.name
                ),
                None
            )
            trovesaurus_file = None
            if trovesaurus_mod:
                trovesaurus_mod, trovesaurus_file = next(
                    ((trovesaurus_mod, file) for file in trovesaurus_mod.file_objs if file.hash == mod.hash),
                    (None, None)
                )
            self.mod_list.controls.append(
                Row(
                    controls=[
                        Stack(
                            controls=[
                                (
                                    Image(src_base64=mod.image, height=60, width=60, fit="contain")
                                )
                            ]
                        ),
                        Row(
                            controls=[
                                Column(
                                    controls=[
                                        Row(
                                            controls=[
                                                Card(
                                                    content=Container(
                                                        Row(
                                                            controls=[
                                                                Container(
                                                                    Row(
                                                                        controls=[
                                                                            *(
                                                                                [
                                                                                    Image(
                                                                                        src="assets/icons/brands/trovesaurus.png",
                                                                                        height=24,
                                                                                        width=24,
                                                                                    ) if bool(trovesaurus_mod) else
                                                                                    Icon(FOLDER_ZIP_SHARP)
                                                                                ]
                                                                            ),
                                                                            Text(
                                                                                get_attr(
                                                                                    mod.metadata.properties,
                                                                                    name="title"
                                                                                ).value,
                                                                                weight="bold"
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    url=(
                                                                        "https://trovesaurus.com/mod=" + str(
                                                                            trovesaurus_mod.id)
                                                                        if trovesaurus_mod else
                                                                        None
                                                                    )
                                                                ),
                                                                Icon(
                                                                    WARNING_SHARP,
                                                                    color=(
                                                                        "red"
                                                                        if mod in
                                                                           self.locations[self.selected_location][
                                                                               "enabled"]
                                                                        else "yellow"
                                                                    ),
                                                                    visible=bool(
                                                                        self.locations[self.selected_location][
                                                                            "conflicts"].get(mod)
                                                                    ) and mod not in
                                                                            self.locations[self.selected_location][
                                                                                "enabled"],
                                                                    tooltip="Conflicts with: \n" + "\n".join(
                                                                        [
                                                                            " - " + get_attr(cmod.metadata.properties,
                                                                                             name="title").value
                                                                            for cmod in
                                                                            self.locations[self.selected_location][
                                                                                "conflicts"].get(
                                                                                mod, [])
                                                                        ]
                                                                    )
                                                                )
                                                            ]
                                                        ),
                                                        padding=Padding(5, 2, 5, 2)
                                                    )
                                                ),
                                                Card(
                                                    Container(
                                                        Row(
                                                            controls=[
                                                                *(
                                                                    [
                                                                        Text(trovesaurus_file.version)
                                                                    ]
                                                                    if trovesaurus_file else
                                                                    []
                                                                ),
                                                            ]
                                                        ),
                                                        padding=Padding(5, 2, 5, 2)
                                                    ),
                                                    visible=bool(trovesaurus_file)
                                                ),
                                                Card(
                                                    content=Container(
                                                        Row(
                                                            controls=[
                                                                Icon(PERSON_SHARP),
                                                                Text(get_attr(mod.metadata.properties,
                                                                              name="author").value),
                                                            ]
                                                        ),
                                                        url=(
                                                            "https://trovesaurus.com/user=" + str(
                                                                trovesaurus_mod.user_id)
                                                            if trovesaurus_mod else
                                                            None
                                                        ),
                                                        padding=Padding(5, 2, 5, 2)
                                                    )
                                                )
                                            ]
                                        ),
                                        Card(
                                            Container(
                                                content=Row(
                                                    controls=[
                                                        Icon(NOTES_SHARP),
                                                        Text(get_attr(mod.metadata.properties,
                                                                      name="notes").value),
                                                    ]
                                                ),
                                                visible=bool(
                                                    get_attr(mod.metadata.properties, name="notes").value
                                                ),
                                                padding=Padding(5, 2, 5, 2)
                                            )
                                        )
                                    ]
                                ),
                                Row(
                                    controls=[
                                        IconButton(
                                            CONSTRUCTION_SHARP,
                                            disabled=not self.locations[self.selected_location]["bad_name"],
                                            data=mod,
                                            tooltip="Fix Bad Name",
                                            on_click=self.fix_bad_name,
                                        ),
                                        Switch(
                                            data=mod,
                                            value=mod in self.locations[self.selected_location]["enabled"],
                                            tooltip=(
                                                "Enable mod"
                                                if mod in self.locations[self.selected_location]["disabled"]else
                                                "Disable mod"
                                            ),
                                            on_change=self.toggle_mod,
                                        ),
                                    ]
                                ),
                            ],
                            alignment=MainAxisAlignment.SPACE_BETWEEN,
                            expand=True
                        )
                    ]
                )
            )
            self.mod_list.controls.append(
                Divider()
            )
        directories_tab = Tab(
            text="Directories",
            content=Column(
                controls=[
                    Container(
                        Row(
                            controls=[
                                IconButton(
                                    REFRESH,
                                    on_click=self.refresh_directories,
                                ),
                                *[
                                    TextButton(
                                        data=str(path),
                                        text=name.capitalize(),
                                        on_click=self.change_directory
                                    )
                                    for name, path in self.location_names
                                ]
                            ]
                        ),
                        padding=Padding(0, 20, 0, 0)
                    ),
                    self.mod_list
                ]
            )
        )
        self.main.controls = [
            Tabs(
                tabs=[
                    directories_tab
                ]
            )
        ]
        await self.page.update_async()

    def setup_events(self):
        ...

    async def refresh_directories(self, event):
        self.refresh_locations = True
        self.setup_controls()

    async def change_directory(self, event):
        if self.selected_location != event.control.data:
            self.selected_location = event.control.data
            self.setup_controls()

    async def fix_bad_name(self, event):
        mod = event.control.data
        title = get_attr(mod.metadata.properties, name="title")
        new_file_name = mod.path.parent.joinpath(title.value + "".join(mod.path.suffixes))
        mod.path.rename(new_file_name)
        self.refresh_locations = True
        self.setup_controls()

    async def select_tile(self, event):
        event.control.selected = not event.control.selected
        await self.page.update_async()

    async def toggle_mod(self, event):
        mod = event.control.data
        title = get_attr(mod.metadata.properties, name="title")
        if event.control.value:
            new_file_name = mod.path.parent.joinpath(title.value + "".join(mod.path.suffixes[:-1]))
        else:
            new_file_name = mod.path.parent.joinpath(title.value + "".join(mod.path.suffixes) + ".disabled")
        mod.path.rename(new_file_name)
        self.refresh_locations = True
        self.setup_controls()
