import asyncio
from pathlib import Path

import flet_core.icons as icons
from flet import (
    Container,
    Column,
    Row,
    Tabs,
    Tab,
    TextButton,
    IconButton,
    Icon,
    Image,
    Padding,
    Text,
    Switch,
    MainAxisAlignment,
    Divider,
    Stack,
    Card,
    ProgressRing,
    ListView,
    ListTile,
    DataColumn,
    DataRow,
    DataCell,
    ResponsiveRow,
    FilledButton,
    padding,
    TextField,
)

from models.interface import Controller
from models.interface import PagedDataTable
from models.interface import ScrollingFrame
from models.trove.mod import TroveModList, TMod
from models.trovesaurus.mods import ModFileType

# from utils.trove.directory import Cfg
from utils.trove.registry import get_trove_locations
from utils.trovesaurus import get_mods_list


class ModsController(Controller):
    def setup_controls(self):
        if not hasattr(self, "main"):
            self.locations = [TroveModList(path) for path in get_trove_locations()]
            self.selected_location = self.locations[0]
            self.selected_tab = 0
            self.reloading = Row(controls=[ProgressRing(), Text("Loading...")])
            self.main = Column(disabled=True)
            self.main_controls = Container(
                Row(
                    controls=[
                        IconButton(
                            icons.REFRESH,
                            on_click=self.refresh_directories,
                        ),
                        *[
                            TextButton(
                                data=location,
                                text=location.name,
                                on_click=self.change_directory,
                            )
                            for location in self.locations
                        ],
                    ]
                ),
                padding=Padding(0, 20, 0, 0),
            )
            self.tabs = Tabs(
                selected_index=self.selected_tab, on_change=self.tab_change
            )
            self.main.controls.append(self.main_controls)
            self.main.controls.append(self.tabs)
            self.main.controls.append(self.reloading)
            # appdata = Path(os.getenv("APPDATA"))
            # trove_appdata = appdata.joinpath("Trove")
            # trove_cfg_path = trove_appdata.joinpath("Trove.cfg")
            # self.trove_cfg = Cfg.from_file(trove_cfg_path)
            return asyncio.create_task(self.post_setup(True))
        asyncio.create_task(self.post_setup())

    async def post_setup(self, boot=False):
        if boot:
            self.mod_list = ListView()
            self.search_bar = TextField(
                hint_text="Search", on_submit=self.search_mod, col=5, border_radius=30
            )
            self.browse_mods_list = PagedDataTable(
                is_async=True,
                page_size=10,
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
                col=9,
            )
            self.selected_mod_control = Column(alignment="center", col=3)
            self.directories_tab = Tab(
                text="Directories", content=Column(controls=[self.mod_list])
            )
            self.browse_mods = Tab(
                text="Browse Mods",
                content=ResponsiveRow(
                    controls=[
                        self.search_bar,
                        self.browse_mods_list,
                        self.selected_mod_control,
                    ]
                ),
            )
            self.directories_tab._reload = self.reload_mods_list
            self.browse_mods._reload = self.reload_mods_store
            self.tabs.tabs.append(self.directories_tab)
            self.tabs.tabs.append(self.browse_mods)
        await self.tabs.tabs[self.selected_tab]._reload()
        for tab in self.tabs.tabs:
            for control in tab.content.controls:
                control.visible = True
            self.reloading.visible = False
        self.main.disabled = False
        await self.main.update_async()

    async def reload_mods_list(self):
        await self.selected_location.update_trovesaurus_data()
        for mod in self.selected_location:
            trovesaurus_mod = next(
                (tmod for tmod in self.trovesaurus_mods if mod.name == tmod.name), None
            )
            trovesaurus_file = None
            self.mod_list.controls.append(
                ListTile(
                    on_click=self.select_tile,
                    title=Row(
                        controls=[
                            Stack(
                                controls=[
                                    (
                                        Image(
                                            src_base64=mod.image,
                                            height=60,
                                            width=60,
                                            fit="contain",
                                        )
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
                                                                                        )
                                                                                        if bool(
                                                                                            trovesaurus_mod
                                                                                        )
                                                                                        else Icon(
                                                                                            icons.FOLDER_ZIP_SHARP
                                                                                        )
                                                                                    ]
                                                                                ),
                                                                                Text(
                                                                                    mod.name,
                                                                                    weight="bold",
                                                                                ),
                                                                            ]
                                                                        ),
                                                                        url=(
                                                                            "https://trovesaurus.com/mod="
                                                                            + str(
                                                                                trovesaurus_mod.id
                                                                            )
                                                                            if trovesaurus_mod
                                                                            else None
                                                                        ),
                                                                    ),
                                                                    Icon(
                                                                        icons.WARNING_SHARP,
                                                                        color=(
                                                                            "red"
                                                                            if mod.enabled
                                                                            else "yellow"
                                                                        ),
                                                                        visible=mod.has_conflicts,
                                                                        tooltip="Conflicts with: \n"
                                                                        + "\n".join(
                                                                            [
                                                                                "\t"
                                                                                + cmod.name
                                                                                for cmod in mod.conflicts
                                                                            ]
                                                                        ),
                                                                    ),
                                                                ]
                                                            ),
                                                            padding=Padding(5, 2, 5, 2),
                                                        )
                                                    ),
                                                    Card(
                                                        Container(
                                                            Row(
                                                                controls=[
                                                                    *(
                                                                        [
                                                                            Text(
                                                                                trovesaurus_file.version
                                                                            )
                                                                        ]
                                                                        if trovesaurus_file
                                                                        else []
                                                                    ),
                                                                ]
                                                            ),
                                                            padding=Padding(5, 2, 5, 2),
                                                        ),
                                                        visible=bool(trovesaurus_file),
                                                    ),
                                                    Card(
                                                        content=Container(
                                                            Row(
                                                                controls=[
                                                                    Icon(
                                                                        icons.PERSON_SHARP
                                                                    ),
                                                                    Text(mod.author),
                                                                ]
                                                            ),
                                                            url=(
                                                                "https://trovesaurus.com/user="
                                                                + str(
                                                                    trovesaurus_mod.user_id
                                                                )
                                                                if trovesaurus_mod
                                                                else None
                                                            ),
                                                            padding=Padding(5, 2, 5, 2),
                                                        )
                                                    ),
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
                                                    visible=bool(mod.notes),
                                                    padding=Padding(5, 2, 5, 2),
                                                )
                                            ),
                                        ]
                                    ),
                                    Row(
                                        controls=[
                                            Switch(
                                                data=mod,
                                                value=mod.enabled,
                                                tooltip=(
                                                    "Enable mod"
                                                    if not mod.enabled
                                                    else "Disable mod"
                                                ),
                                                disabled=mod.has_conflicts
                                                and not mod.enabled,
                                                on_change=self.toggle_mod,
                                            ),
                                        ]
                                    ),
                                ],
                                alignment=MainAxisAlignment.SPACE_BETWEEN,
                                expand=True,
                            ),
                        ]
                    ),
                )
            )
            self.mod_list.controls.append(Divider())

    async def reload_mods_store(self):
        for mod in sorted(
            self.trovesaurus_mods, key=lambda m: m.downloads, reverse=True
        ):
            if self.search_bar.value:
                if (
                    self.search_bar.value.lower()
                    not in mod.name.lower() + mod.author.lower()
                ):
                    continue
            await self.browse_mods_list.add_row_async(
                DataRow(
                    data=mod,
                    cells=[
                        DataCell(
                            Icon(
                                icons.DONE if mod.installed else icons.CLOSE,
                                color="green" if mod.installed else "red",
                            )
                        ),
                        DataCell(Text(mod.name)),
                        DataCell(Text(mod.author)),
                        DataCell(Text(f"{mod.views:,}")),
                        DataCell(Text(f"{mod.downloads:,}")),
                        DataCell(Text(f"{mod.likes:,}")),
                    ],
                )
            )
        await self.browse_mods_list.to_first_page_async(None)

    def setup_events(self):
        ...

    async def refresh_directories(self, event):
        self.main.disabled = True
        for tab in self.tabs.tabs:
            for control in tab.content.controls:
                control.visible = False
            self.reloading.visible = True
        await self.main.update_async()
        for location in self.locations:
            location.refresh()
        self.setup_controls()

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
        event.control.data.toggle()
        self.setup_controls()

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
                                    Text(f"{self.selected_mod.views:,}"),
                                ]
                            ),
                            Row(
                                controls=[
                                    Icon(icons.THUMB_UP, size=13),
                                    Text(f"{self.selected_mod.likes:,}"),
                                ]
                            ),
                            Row(
                                controls=[
                                    Icon(icons.DOWNLOAD, size=13),
                                    Text(f"{self.selected_mod.downloads:,}"),
                                ]
                            ),
                        ],
                        alignment="center",
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
                                                    Text(
                                                        self.selected_mod.clean_description
                                                    )
                                                ],
                                                height=150,
                                                scroll="auto",
                                            ),
                                        ]
                                    ),
                                    padding=padding.only(
                                        top=5, left=10, right=15, bottom=5
                                    ),
                                )
                            )
                        ]
                        if self.selected_mod.clean_description
                        else []
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
                                                            if file.type
                                                            == ModFileType.TMOD
                                                            else (
                                                                icons.FOLDER_ZIP
                                                                if file.type
                                                                == ModFileType.ZIP
                                                                else icons.SETTINGS_APPLICATIONS
                                                            )
                                                        ),
                                                        data=file,
                                                        disabled=self.selected_mod.installed_file
                                                        == file,
                                                        text=file.version,
                                                        on_click=self.download_mod_file,
                                                    )
                                                    for file in filter(
                                                        lambda m: m.type
                                                        == ModFileType.TMOD,
                                                        sorted(
                                                            self.selected_mod.file_objs,
                                                            key=lambda x: -x.file_id,
                                                        ),
                                                    )
                                                ]
                                            ),
                                            padding=padding.only(bottom=15),
                                        )
                                    ),
                                ]
                            ),
                            padding=padding.only(top=5, left=10, right=15),
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
            ),
        ]
        await self.selected_mod_control.update_async()

    async def tab_change(self, event):
        self.main.disabled = True
        for tab in self.tabs.tabs:
            for control in tab.content.controls:
                control.visible = False
            self.reloading.visible = True
        await self.main.update_async()
        self.selected_tab = event.control.selected_index
        self.setup_controls()

    async def search_mod(self, event):
        self.main.disabled = True
        for tab in self.tabs.tabs:
            for control in tab.content.controls:
                control.visible = False
            self.reloading.visible = True
        await self.main.update_async()
        self.setup_controls()

    async def download_mod_file(self, event):
        self.main.disabled = True
        await self.page.update_async()
        file = event.control.data
        file_data = await file.download()
        mod = TMod.read_bytes(Path(r"G:\Glyph\Games\Trove\Live\mods"), file_data)
        print(mod.name)
        self.setup_controls()
