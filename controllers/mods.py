import asyncio
import os
from pathlib import Path

import flet_core.icons as icons
from flet import Container, Column, Row, Tabs, Tab, TextButton, IconButton, Icon, Image, Padding, Text, Switch, \
    MainAxisAlignment, Divider, Stack, Card, ProgressRing, ListView, ListTile, DataColumn, DataRow, DataCell, \
    ResponsiveRow, FilledButton, padding

from models.interface import Controller
from models.interface import PagedDataTable
from models.interface import ScrollingFrame
from models.trove.mod import TMod
from models.trovesaurus.mods import ModFileType
from utils.trove.directory import get_mods_from_directory, Cfg
from utils.trove.registry import GetTroveLocations
from utils.trovesaurus import get_mods_list


class ModsController(Controller):
    def setup_controls(self, refresh=False):
        if not hasattr(self, "locations") or refresh:
            appdata = Path(os.getenv("APPDATA"))
            trove_appdata = appdata.joinpath("Trove")
            trove_cfg_path = trove_appdata.joinpath("Trove.cfg")
            trove_cfg = Cfg.from_file(trove_cfg_path)
            self.location_names = list(GetTroveLocations())
            if not hasattr(self, "locations"):
                self.selected_tab = 0
                self.main = Column(controls=[Row(controls=[ProgressRing(), Text("Loading mod manager...")])])
                self.selected_location = str(self.location_names[0][1])
            self.locations = {}
            for name, path in self.location_names:
                mods_list = get_mods_from_directory(path)
                mods_list.sort(key=lambda x: x.name)
                self.locations[str(path)] = mods_list
                break
            self.refresh_locations = False
        asyncio.create_task(self.post_setup(refresh))

    async def post_setup(self, refresh):
        if not hasattr(self, "trovesaurus_mods"):
            self.trovesaurus_mods = await get_mods_list()
        self.mod_list = ListView()
        for mod in self.locations[self.selected_location]:
            trovesaurus_mod = next(
                (
                    tmod
                    for tmod in self.trovesaurus_mods
                    if mod.name == tmod.name
                ),
                None
            )
            trovesaurus_file = None
            if trovesaurus_mod:
                trovesaurus_mod, trovesaurus_file = next(
                    ((trovesaurus_mod, file) for file in trovesaurus_mod.file_objs if file.hash == mod.tmod_hash),
                    (None, None)
                )
            if trovesaurus_mod:
                trovesaurus_mod.installed = True
                trovesaurus_mod.installed_file = trovesaurus_file
            mod.check_conflicts(
                self.selected_location,
                self.locations[self.selected_location]
            )
            self.mod_list.controls.append(
                ListTile(
                    on_click=self.select_tile,
                    title=Row(
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
                                                                                        Icon(icons.FOLDER_ZIP_SHARP)
                                                                                    ]
                                                                                ),
                                                                                Text(
                                                                                    mod.name,
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
                                                                        icons.WARNING_SHARP,
                                                                        color=(
                                                                            "red"
                                                                            if mod.enabled
                                                                            else "yellow"
                                                                        ),
                                                                        visible=mod.has_conflicts,
                                                                        tooltip="Conflicts with: \n" + "\n".join(
                                                                            [
                                                                                "\t" + cmod.name
                                                                                for cmod in mod.conflicts
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
                                                                    Icon(icons.PERSON_SHARP),
                                                                    Text(mod.author)
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
                                                            Icon(icons.NOTES_SHARP),
                                                            Container(
                                                                Text(
                                                                    mod.notes,
                                                                )
                                                            ),
                                                        ]
                                                    ),
                                                    visible=bool(
                                                        mod.notes
                                                    ),
                                                    padding=Padding(5, 2, 5, 2)
                                                )
                                            )
                                        ]
                                    ),
                                    Row(
                                        controls=[
                                            Switch(
                                                data=mod,
                                                value=mod.enabled,
                                                tooltip=(
                                                    "Enable mod"
                                                    if not mod.enabled else
                                                    "Disable mod"
                                                ),
                                                disabled=mod.has_conflicts and not mod.enabled,
                                                on_change=self.toggle_mod,
                                            ),
                                        ]
                                    )
                                ],
                                alignment=MainAxisAlignment.SPACE_BETWEEN,
                                expand=True
                            )
                        ]
                    ),
                )
            )
            self.mod_list.controls.append(
                Divider()
            )
        directories_tab = Tab(
            text="Directories",
            content=Column(
                controls=[
                    self.mod_list
                ]
            )
        )
        browse_mods_list = PagedDataTable(
            is_async=True,
            page_size=12,
            columns=[
                DataColumn(
                    label=Text("Installed"),
                ),
                DataColumn(
                    label=Text("Name"),
                ),
                DataColumn(
                    label=Text("Author"),
                ),
                DataColumn(
                    label=Text("Views"),
                ),
                DataColumn(
                    label=Text("Downloads"),
                ),
                DataColumn(
                    label=Text("Likes"),
                ),
            ],
            single_select=True,
            on_selection_changed=self.selected_mod_changed,
            col=9
        )
        for mod in sorted(self.trovesaurus_mods, key=lambda mod: mod.downloads, reverse=True):
            await browse_mods_list.add_row_async(
                DataRow(
                    data=mod,
                    cells=[
                        DataCell(
                            Icon(
                                icons.DONE if mod.installed else icons.CLOSE,
                                color="green" if mod.installed else "red"
                            )
                        ),
                        DataCell(
                            Text(mod.name)
                        ),
                        DataCell(
                            Text(mod.author)
                        ),
                        DataCell(
                            Text(f"{mod.views:,}")
                        ),
                        DataCell(
                            Text(f"{mod.downloads:,}")
                        ),
                        DataCell(
                            Text(f"{mod.likes:,}")
                        ),
                    ]
                )
            )
        self.selected_mod_control = Column(
            alignment="center",
            col=3
        )
        browse_mods = Tab(
            text="Browse Mods",
            content=ResponsiveRow(
                controls=[
                    browse_mods_list,
                    self.selected_mod_control
                ]
            )
        )
        self.main.controls = [
            Container(
                Row(
                    controls=[
                        IconButton(
                            icons.REFRESH,
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
            Tabs(
                tabs=[
                    directories_tab,
                    browse_mods
                ],
                selected_index=self.selected_tab,
                on_change=lambda e: setattr(self, "selected_tab", e.control.selected_index)
            ),
        ]
        self.main.disabled = False
        await self.page.update_async()

    def setup_events(self):
        ...

    async def refresh_directories(self, event):
        self.main.disabled = True
        self.refresh_locations = True
        self.setup_controls(refresh=True)

    async def change_directory(self, event):
        if self.selected_location != event.control.data:
            self.selected_location = event.control.data
            self.setup_controls()

    async def fix_bad_name(self, event):
        mod = event.control.data
        new_file_name = mod.path.parent.joinpath(mod.name + "".join(mod.path.suffixes))
        mod.path.rename(new_file_name)
        mod.path = new_file_name
        event.control.disabled = True
        await self.page.update_async()

    async def select_tile(self, event):
        event.control.selected = not event.control.selected
        await self.page.update_async()

    async def toggle_mod(self, event):
        mod = event.control.data
        if event.control.value:
            new_file_name = mod.path.parent.joinpath(mod.name + "".join(mod.path.suffixes[:-1]))
        else:
            new_file_name = mod.path.parent.joinpath(mod.name + "".join(mod.path.suffixes) + ".disabled")
        mod.path.rename(new_file_name)
        mod.path = new_file_name

    async def selected_mod_changed(self, e):
        self.selected_mod = e.control.data
        self.selected_mod_control.controls = [
            Image(src=self.selected_mod.thumbnail_url, width=200, height=100),
            Text(self.selected_mod.name, size=18, weight="bold"),
            ResponsiveRow(
                controls=[
                    Row(
                        controls=[
                            Row(
                                controls=[
                                    Icon(icons.REMOVE_RED_EYE, size=13),
                                    Text(f"{self.selected_mod.views:,}")
                                ]
                            ),
                            Row(
                                controls=[
                                    Icon(icons.THUMB_UP, size=13),
                                    Text(f"{self.selected_mod.likes:,}")
                                ]
                            ),
                            Row(
                                controls=[
                                    Icon(icons.DOWNLOAD, size=13),
                                    Text(f"{self.selected_mod.downloads:,}")
                                ]
                            )
                        ],
                        alignment="center"
                    ),
                    *(
                        [
                            Card(
                                Container(
                                    Column(
                                        controls=[
                                            Text("Description:", size=16),
                                            Column(
                                                controls=[
                                                    Text(self.selected_mod.clean_description)
                                                ],
                                                height=150,
                                                scroll="auto"
                                            )
                                        ]
                                    ),
                                    padding=padding.only(top=5, left=10, right=15, bottom=5)
                                )
                            )
                        ] if self.selected_mod.clean_description else []
                    ),
                    Card(
                        Container(
                            ResponsiveRow(
                                controls=[
                                    Text("Versions:"),
                                    ScrollingFrame(
                                        Container(
                                            Row(
                                                controls=[
                                                    FilledButton(
                                                        icon=(
                                                            icons.INSERT_DRIVE_FILE
                                                            if file.type == ModFileType.TMOD else
                                                            (
                                                                icons.FOLDER_ZIP
                                                                if file.type == ModFileType.ZIP else
                                                                icons.SETTINGS_APPLICATIONS
                                                            )
                                                        ),
                                                        data=file,
                                                        disabled=self.selected_mod.installed_file == file,
                                                        text=file.version,
                                                        on_click=self.download_mod_file
                                                    )
                                                    for file in filter(
                                                        lambda m: m.type == ModFileType.TMOD,
                                                        sorted(
                                                            self.selected_mod.file_objs,
                                                            key=lambda x: -x.file_id
                                                        )
                                                    )
                                                ]
                                            ),
                                            padding=padding.only(bottom=15)
                                        )
                                    )
                                ]
                            ),
                            padding=padding.only(top=5, left=10, right=15)
                        )
                    ),
                    # *(
                    #     [
                    #         Card(
                    #             Container(
                    #                 Column(
                    #                     controls=[
                    #                         Text("Change Log:", size=16),
                    #                         Column(
                    #                             controls=[
                    #                                 Text(self.selected_file.clean_changes)
                    #                             ],
                    #                             height=80,
                    #                             scroll="auto"
                    #                         )
                    #                     ]
                    #                 ),
                    #                 padding=padding.only(top=5, left=10, right=15, bottom=5)
                    #             )
                    #         )
                    #     ] if self.selected_file.clean_changes else []
                    # ),
                    # *(
                    #     [
                    #         Card(
                    #             Container(
                    #                 Column(
                    #                     controls=[
                    #                         Text("Replaces:", size=16),
                    #                         Column(
                    #                             controls=[
                    #                                 Text(self.selected_file.clean_replacements)
                    #                             ],
                    #                             height=50,
                    #                             scroll="auto"
                    #                         )
                    #                     ]
                    #                 ),
                    #                 padding=padding.only(top=5, left=10, right=15, bottom=5)
                    #             )
                    #         )
                    #     ] if self.selected_file.clean_replacements else []
                    # )
                ]
            )
        ]
        await self.selected_mod_control.update_async()

    async def download_mod_file(self, event):
        self.page.controls[0].disabled = True
        await self.page.update_async()
        file = event.control.data
        file_data = await file.download()
        mod = TMod.read_bytes(Path(r"G:\Glyph\Games\Trove\Live\mods"), file_data)
        print(mod.name)
        self.page.controls[0].disabled = False
        await self.page.update_async()
