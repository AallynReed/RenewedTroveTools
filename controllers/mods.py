import asyncio
from pathlib import Path
from aiohttp import ClientSession
from hashlib import md5

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
    ExpansionPanelList,
    ExpansionPanel,
    Dropdown,
    dropdown,
    Tooltip,
)

from models.interface import Controller
from models.interface import PagedDataTable
from models.interface import ScrollingFrame
from models.trove.mod import TroveModList, TMod, ZMod
from models.trovesaurus.mods import ModFileType

# from utils.trove.directory import Cfg
from utils.trove.registry import get_trove_locations
from utils.kiwiapi import KiwiAPI, ModAuthorRoleColors
from utils.functions import throttle


class ModsController(Controller):
    def setup_controls(self):
        if not hasattr(self, "main"):
            self.api = KiwiAPI()
            self.memory = {
                "trovesaurus": {
                    "page": 0,
                    "page_size": 8,
                    "installation_path": None,
                    "selected_tile": None,
                    "selected_file": None,
                }
            }
            self.main = ResponsiveRow(alignment=MainAxisAlignment.START)
            self.loading = Column(controls=[ProgressRing(), Text("Loading...")])
            self.mod_submenus = Tabs(visible=False)
            self.mod_submenus.on_change = self.tab_loader
            self.settings_tab = Tab(
                tab_content=Row(
                    controls=[
                        Icon(icons.SETTINGS, size=24),
                    ]
                ),
            )
            self.my_mods_tab = Tab(
                tab_content=Row(
                    controls=[
                        Icon(icons.FOLDER, size=24),
                        Text("My Mods"),
                    ]
                ),
            )
            self.trovesaurus_tab = Tab(
                tab_content=Row(
                    controls=[
                        Image(src="https://trovesaurus.com/favicon.ico"),
                        Text("Trovesaurus"),
                    ]
                )
            )
            self.settings = Column()
            self.my_mods = Column()
            self.trovesaurus = Column()
            self.settings_tab.content = self.settings
            self.my_mods_tab.content = self.my_mods
            self.trovesaurus_tab.content = self.trovesaurus
            self.mod_submenus.tabs.append(self.settings_tab)
            self.mod_submenus.tabs.append(self.my_mods_tab)
            self.mod_submenus.tabs.append(self.trovesaurus_tab)
            my_mods_index = self.mod_submenus.tabs.index(self.my_mods_tab)
            trovesaurus_index = self.mod_submenus.tabs.index(self.trovesaurus_tab)
            self.my_mods_tab.tab_content.controls.append(
                IconButton(
                    data=my_mods_index,
                    icon=icons.REFRESH,
                    on_click=self.reload_tab,
                )
            )
            self.trovesaurus_tab.tab_content.controls.append(
                IconButton(
                    data=trovesaurus_index,
                    icon=icons.REFRESH,
                    on_click=self.reload_tab,
                )
            )
            self.tab_map = {
                0: self.load_settings,
                1: self.load_my_mods,
                2: self.load_trovesaurus_mods,
            }
            self.mod_submenus.selected_index = 2
            self.main.controls.append(self.loading)
            self.main.controls.append(self.mod_submenus)
            asyncio.create_task(self.post_setup())

    def setup_events(self): ...

    async def post_setup(self):
        self.loading.visible = False
        self.mod_submenus.visible = True
        await self.tab_loader(boot=True)

    @throttle
    async def tab_loader(self, event=None, index=None, boot=False):
        self.mod_folders = list(get_trove_locations())
        if self.mod_folders:
            if not self.memory["trovesaurus"]["installation_path"]:
                self.memory["trovesaurus"]["installation_path"] = self.mod_folders[0]
            else:
                if (
                    self.memory["trovesaurus"]["installation_path"]
                    not in self.mod_folders
                ):
                    self.memory["trovesaurus"]["installation_path"] = self.mod_folders[
                        0
                    ]
        else:
            self.memory["trovesaurus"]["installation_path"] = None
        self.mod_folder_lists = {
            folder: TroveModList(path=folder) for folder in self.mod_folders
        }
        for mod_list in self.mod_folder_lists.values():
            await mod_list.update_trovesaurus_data()
        if index is None:
            if event is not None:
                index = event.control.selected_index
            else:
                index = self.mod_submenus.selected_index
        await self.tab_map[index](boot=boot)

    async def reload_tab(self, event):
        await self.tab_loader(index=event.control.data)

    async def load_settings(self, boot=False):
        if self.settings.data is None:
            self.settings.controls.append(TextButton("Clear Cache"))
            self.main.disabled = False
            self.settings.data = True
        await self.main.update_async()

    async def load_my_mods(self, boot=False):
        if self.my_mods.data is None:
            self.my_mods.controls.append(ProgressRing())
            self.my_mods.controls.append(Text("Loading..."))
            self.my_mods.data = True
        await self.main.update_async()

    async def load_trovesaurus_mods(self, boot=False):
        self.trovesaurus.controls.clear()
        self.memory["trovesaurus"]["selected_file"] = None
        if not self.mod_folders:
            self.trovesaurus.controls.append(Text("No Trove installation found"))
            await self.main.update_async()
            return
        self.trovesaurus.controls.append(
            Row(
                controls=[
                    TextButton(
                        data=mod_list_path,
                        content=Text(mod_list_path.name),
                        disabled=mod_list_path
                        == self.memory["trovesaurus"]["installation_path"],
                        on_click=self.set_installation_path,
                    )
                    for mod_list_path in self.mod_folders
                ]
            )
        )
        self.mods_list = ExpansionPanelList(on_change=self.update_selected_tile)
        self.cached_trovesaurus_mods = await self.api.get_mods_list_chunk(
            self.memory["trovesaurus"]["page_size"],
            self.memory["trovesaurus"]["page"],
        )
        for i, mod in enumerate(self.cached_trovesaurus_mods):
            installed = False
            ts_mod = None
            mod_l = self.mod_folder_lists[
                self.memory["trovesaurus"]["installation_path"]
            ]
            for ts_mod in mod_l.mods:
                if ts_mod.trovesaurus_data.id == mod.id:
                    installed = True
                    break
            selected_tile = self.memory["trovesaurus"]["selected_tile"]
            self.mods_list.controls.append(
                ExpansionPanel(
                    ListTile(
                        leading=Image(
                            src=(
                                mod.image_url
                                or "https://trovesaurus.com/images/logos/Sage_64.png?1"
                            ),
                            width=64,
                            height=64,
                        ),
                        title=Row(
                            controls=[
                                TextButton(
                                    content=Text(mod.name, color="#bbbbbb", size=18),
                                    url=f"https://trovesaurus.com/mod={mod.id}",
                                ),
                                *(
                                    [
                                        Tooltip(
                                            message="Installed",
                                            content=Icon(icons.CHECK, color="green"),
                                        )
                                    ]
                                    if installed
                                    else []
                                ),
                            ]
                        ),
                        subtitle=Row(
                            controls=[
                                Row(
                                    controls=[
                                        *(
                                            [
                                                TextButton(
                                                    content=Row(
                                                        controls=[
                                                            Image(
                                                                src=author.Avatar,
                                                                width=24,
                                                            ),
                                                            Tooltip(
                                                                message=(
                                                                    author.Role.value
                                                                    if author.Role.value
                                                                    else "User"
                                                                ),
                                                                content=Text(
                                                                    author.Username,
                                                                    color=ModAuthorRoleColors[
                                                                        author.Role.name
                                                                    ].value,
                                                                ),
                                                            ),
                                                        ]
                                                    ),
                                                    url=f"https://trovesaurus.com/user={author.ID}",
                                                )
                                                for author in mod.authors
                                            ]
                                            if [
                                                author
                                                for author in mod.authors
                                                if author.ID
                                            ]
                                            else [
                                                TextButton(
                                                    content=Text(
                                                        "No authors", color="red"
                                                    ),
                                                    disabled=True,
                                                )
                                            ]
                                        )
                                    ]
                                )
                            ]
                        ),
                    ),
                    Column(
                        controls=[
                            Text(mod.description) or Text("No description"),
                            Row(
                                controls=[
                                    Tooltip(
                                        message="Downloads",
                                        content=Row(
                                            controls=[
                                                Icon(icons.DOWNLOAD),
                                                Text(f"{mod.downloads}"),
                                            ]
                                        ),
                                    ),
                                    Tooltip(
                                        message="Likes",
                                        content=Row(
                                            controls=[
                                                Icon(icons.FAVORITE),
                                                Text(f"{mod.likes}"),
                                            ]
                                        ),
                                    ),
                                ]
                            ),
                            ResponsiveRow(
                                controls=[
                                    Dropdown(
                                        data=[
                                            (mod, file)
                                            for file in mod.file_objs
                                            if file.hash
                                        ],
                                        options=[
                                            dropdown.Option(
                                                key=file.hash,
                                                text=file.version
                                                + f" ({file.type.value})",
                                            )
                                            for file in mod.file_objs
                                            if file.hash
                                        ],
                                        on_change=self.select_mod_file,
                                        col=4,
                                    ),
                                    IconButton(
                                        data=i,
                                        content=Row(
                                            controls=[
                                                Icon(icons.DOWNLOAD),
                                                Text("Install"),
                                            ],
                                            alignment="center",
                                        ),
                                        height=64,
                                        on_click=self.install_mod,
                                        col=1,
                                    ),
                                    IconButton(
                                        data=i,
                                        content=Row(
                                            controls=[
                                                Icon(icons.ADD),
                                                Text("Add to profile"),
                                            ],
                                            alignment="center",
                                        ),
                                        height=64,
                                        on_click=...,
                                        col=1.4,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    expanded=i == selected_tile,
                    can_tap_header=True,
                )
            )
        self.trovesaurus.controls.append(self.mods_list)
        page_count = await self.api.get_mods_page_count(
            self.memory["trovesaurus"]["page_size"]
        )
        self.trovesaurus.controls.append(
            Row(
                controls=[
                    IconButton(
                        icon=icons.ARROW_LEFT,
                        on_click=self.previous_trovesaurus_page,
                    ),
                    Row(
                        controls=[
                            Text(f"Page"),
                            TextField(
                                value=str(self.memory["trovesaurus"]["page"] + 1),
                                on_submit=self.set_trovesaurus_page,
                                width=80,
                                height=48,
                            ),
                            Text(f"of {page_count}"),
                        ]
                    ),
                    IconButton(
                        icon=icons.ARROW_RIGHT,
                        on_click=self.next_trovesaurus_page,
                    ),
                ]
            )
        )
        if not boot:
            self.page.snack_bar.content = Text(f"Refreshed Trovesaurus")
            self.page.snack_bar.bgcolor = "green"
            self.page.snack_bar.open = True
        await self.main.update_async()
        await self.page.snack_bar.update_async()

    async def previous_trovesaurus_page(self, event):
        self.memory["trovesaurus"]["page"] -= 1
        page_size = self.memory["trovesaurus"]["page_size"]
        count = await self.api.get_mods_page_count(page_size)
        if self.memory["trovesaurus"]["page"] < 0:
            self.memory["trovesaurus"]["page"] = count - 1
        self.memory["trovesaurus"]["selected_tile"] = None
        await self.load_trovesaurus_mods(boot=True)

    async def next_trovesaurus_page(self, event):
        self.memory["trovesaurus"]["page"] += 1
        page_size = self.memory["trovesaurus"]["page_size"]
        count = await self.api.get_mods_page_count(page_size)
        if self.memory["trovesaurus"]["page"] >= count:
            self.memory["trovesaurus"]["page"] = 0
        self.memory["trovesaurus"]["selected_tile"] = None
        await self.load_trovesaurus_mods(boot=True)

    async def set_trovesaurus_page(self, event):
        try:
            page = int(event.control.value) - 1
            page_size = self.memory["trovesaurus"]["page_size"]
            if page < 0:
                page = 0
            count = await self.api.get_mods_page_count(page_size)
            if page >= count:
                page = count - 1
            self.memory["trovesaurus"]["page"] = page
            await self.load_trovesaurus_mods()
        except ValueError:
            pass
        await self.main.update_async()

    async def set_installation_path(self, event):
        self.memory["trovesaurus"]["installation_path"] = event.control.data
        await self.load_trovesaurus_mods()

    async def update_selected_tile(self, event):
        selected = int(event.data)
        for i, tile in enumerate(self.mods_list.controls):
            if i == selected:
                if tile.expanded:
                    self.memory["trovesaurus"]["selected_tile"] = i
                else:
                    self.memory["trovesaurus"]["selected_tile"] = None
            else:
                tile.expanded = False
        await self.mods_list.update_async()

    async def select_mod_file(self, event):
        for mod, file in event.control.data:
            if file.hash == event.control.value:
                self.memory["trovesaurus"]["selected_file"] = (
                    mod,
                    file,
                    [f.hash for m, f in event.control.data],
                )
                break

    async def install_mod(self, _):
        if self.memory["trovesaurus"]["selected_file"] is None:
            return
        mod_data, file_data, hashes = self.memory["trovesaurus"]["selected_file"]
        installation_path = self.memory["trovesaurus"]["installation_path"].joinpath(
            "mods"
        )
        for mod_file in installation_path.iterdir():
            if mod_file.is_file():
                hash = md5(mod_file.read_bytes()).hexdigest()
                if hash in hashes:
                    mod_file.unlink()
        url = f"https://trovesaurus.com/client/downloadfile.php?fileid={file_data.file_id}"
        async with ClientSession() as session:
            async with session.get(url) as response:
                data = await response.read()
                try:
                    mod = TMod().read_bytes(Path(""), data)
                    mod_name = mod.name
                except:
                    mod_name = mod_data.name.replace("/", "-")
                file_name = r"{0}.{1}".format(mod_name, file_data.type.value)
                file_path = installation_path.joinpath(file_name)
                file_path.write_bytes(data)
        await self.tab_loader(index=self.mod_submenus.selected_index)
        self.page.snack_bar.content = Text(f"Installed {mod_name}")
        self.page.snack_bar.bgcolor = "green"
        self.page.snack_bar.open = True
        await self.page.snack_bar.update_async()
