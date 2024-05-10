import asyncio
import os
from copy import deepcopy
from hashlib import md5
from pathlib import Path

import flet_core.icons as icons
from aiohttp import ClientSession
from flet import (
    MainAxisAlignment,
    Column,
    Row,
    Tabs,
    Chip,
    Tab,
    TextButton,
    IconButton,
    Icon,
    Image,
    Text,
    Divider,
    VerticalDivider,
    Card,
    ListView,
    ListTile,
    ResponsiveRow,
    padding,
    TextField,
    ExpansionTile,
    Dropdown,
    dropdown,
    Tooltip,
    FilePicker,
    ScrollMode,
    ButtonStyle,
    Switch,
    ImageFit,
    PopupMenuButton,
    PopupMenuItem,
    WebView,
    ElevatedButton,
    TextStyle,
)
from models.interface import RTTChip, RTTIconDecoButton
from models.interface import Controller
from models.interface.inputs import NumberField
from models.trove.mod import TroveModList, TMod
from utils.kiwiapi import KiwiAPI, ImageSize, ModAuthorRole, ModAuthorRoleColors
from utils.trove.registry import get_trove_locations, TroveGamePath


class ModsController(Controller):
    def setup_controls(self):
        if not hasattr(self, "main"):
            self.api = KiwiAPI()
            self.setup_memory()
            self.main = Column(expand=True)
            self.mod_submenus = Tabs()
            self.mod_submenus.on_change = self.tab_loader
            self.settings_tab = Tab(
                tab_content=Row(controls=[Icon(icons.SETTINGS, size=24)])
            )
            self.my_mods_tab = Tab(
                tab_content=Row(controls=[Icon(icons.FOLDER, size=24), Text("My Mods")])
            )
            self.trovesaurus_tab = Tab(
                tab_content=Row(
                    controls=[
                        Image(src="https://trovesaurus.com/favicon.ico"),
                        Text("Trovesaurus"),
                    ]
                )
            )
            self.mod_profiles_tab = Tab(
                tab_content=Row(
                    controls=[
                        Icon(
                            icons.PERSON,
                            size=24,
                            color="red" if not self.page.user_data else "default",
                        ),
                        Text(
                            "Mod Profiles (Not working yet)",
                            color="red" if not self.page.user_data else "default",
                        ),
                    ]
                )
            )
            self.settings = Column(expand=True)
            self.my_mods = Column(expand=True)
            self.trovesaurus = Column(expand=True)
            self.mod_profiles = Column(expand=True)
            self.mod_submenus.tabs.append(self.settings_tab)
            self.mod_submenus.tabs.append(self.my_mods_tab)
            self.mod_submenus.tabs.append(self.trovesaurus_tab)
            self.mod_submenus.tabs.append(self.mod_profiles_tab)
            self.tabs = {
                0: self.settings,
                1: self.my_mods,
                2: self.trovesaurus,
                3: self.mod_profiles,
            }
            self.tab_map = {
                0: self.load_settings,
                1: self.load_my_mods,
                2: self.load_trovesaurus_mods,
                3: self.load_mod_profiles,
            }
            self.mod_submenus.selected_index = 1
            if self.page.params:
                mod_id = self.page.params.get("mod_id")
                if mod_id:
                    self.memory["trovesaurus"]["search"]["query"] = mod_id
                    self.mod_submenus.selected_index = 2
                    self.page.params.clear()
            asyncio.create_task(self.post_setup())

    def setup_events(self): ...

    async def post_setup(self):
        self.main.controls.append(
            Row(
                controls=[
                    IconButton(icons.REFRESH, on_click=self.reload_tab),
                    self.mod_submenus,
                ]
            )
        )
        await self.release_ui()
        await self.tab_loader(boot=True)

    def setup_memory(self):
        self.memory = {
            "settings": {"picked_custom_dir_name": None, "picked_custom_dir": None},
            "my_mods": {"installation_path": None, "filter": None},
            "trovesaurus": {
                "page": 0,
                "page_size": self.page.preferences.mod_manager.page_size,
                "installation_path": None,
                "selected_tile": None,
                "selected_file": None,
                "search": {
                    "query": None,
                    "type": None,
                    "sub_type": None,
                    "sort_by": [
                        ("downloads", "desc"),
                        ("likes", "desc"),
                        ("name", "asc"),
                        ("last_update", "desc"),
                    ],
                },
            },
        }

    def check_memory(self):
        self.mod_folders = list(get_trove_locations())
        custom_mod_folders = self.page.preferences.mod_manager.custom_directories
        for name, path in custom_mod_folders:
            self.mod_folders.append(TroveGamePath(path=Path(path), name=name))
        my_mods = self.memory["my_mods"]
        trovesarus = self.memory["trovesaurus"]
        if not self.mod_folders:
            my_mods["installation_path"] = None
            trovesarus["installation_path"] = None
        else:
            if not my_mods["installation_path"]:
                my_mods["installation_path"] = self.mod_folders[0]
            else:
                if my_mods["installation_path"] not in self.mod_folders:
                    my_mods["installation_path"] = self.mod_folders[0]
            if not trovesarus["installation_path"]:
                trovesarus["installation_path"] = self.mod_folders[0]
            else:
                if trovesarus["installation_path"] not in self.mod_folders:
                    trovesarus["installation_path"] = self.mod_folders[0]

    async def tab_loader(self, event=None, index=None, boot=False):
        if boot or event:
            self.check_memory()
        if index is None:
            if event is not None:
                index = event.control.selected_index
            else:
                index = self.mod_submenus.selected_index
        self.main.controls.clear()
        self.main.controls.append(
            Row(
                controls=[
                    IconButton(icons.REFRESH, on_click=self.reload_tab),
                    self.mod_submenus,
                ]
            )
        )
        self.main.controls.append(self.tabs[index])
        await self.tab_map[index](boot=boot or bool(event))

    async def reload_tab(self, event):
        await self.tab_loader(index=self.mod_submenus.selected_index)

    async def lock_ui(self):
        self.main.disabled = True
        await self.main.update_async()
        await asyncio.sleep(0.1)

    async def release_ui(self):
        self.main.disabled = False
        await self.main.update_async()

    # Settings Tab

    async def load_settings(self, boot=False):
        await self.lock_ui()
        self.settings.controls.clear()
        custom_directories = self.page.preferences.mod_manager.custom_directories
        self.settings.controls.append(
            ResponsiveRow(
                controls=[
                    Card(
                        content=Column(
                            controls=[
                                Text("Settings"),
                                Divider(),
                                Row(
                                    controls=[
                                        Switch(
                                            value=self.page.preferences.mod_manager.show_previews,
                                            on_change=self.settings_toggle_show_previews,
                                            tooltip="Show mod image previews",
                                        ),
                                        Text("Show Previews"),
                                    ]
                                ),
                                Row(
                                    controls=[
                                        Switch(
                                            value=self.page.preferences.mod_manager.auto_fix_mod_names,
                                            on_change=self.settings_toggle_auto_fix_mod_names,
                                            tooltip="Automatically fix mod names on directory reading",
                                        ),
                                        Text("Auto Fix Mod Names"),
                                    ]
                                ),
                                Row(
                                    controls=[
                                        Switch(
                                            value=self.page.preferences.mod_manager.auto_generate_and_fix_cfg,
                                            on_change=self.settings_toggle_auto_generate_and_fix_cfg,
                                            tooltip="Automatically generate and fix cfg files for UI mods",
                                        ),
                                        Text(
                                            "Auto Generate and Fix CFG files for UI mods"
                                        ),
                                    ]
                                ),
                                Row(
                                    controls=[
                                        Switch(
                                            value=self.page.preferences.mod_manager.tile_toggle,
                                            on_change=self.settings_toggle_tile_toggle_cfg,
                                            tooltip="Whether mod tiles in My Mods enable/disable mods",
                                        ),
                                        Text("My Mods tiles toggle mods"),
                                    ]
                                ),
                            ]
                        )
                    ),
                    Card(
                        content=Column(
                            controls=[
                                Text("Custom Directories"),
                                Divider(),
                                Row(
                                    controls=[
                                        TextButton(
                                            text="Add custom directory",
                                            on_click=self.settings_add_custom_directory,
                                        )
                                    ]
                                ),
                                ListView(
                                    controls=[
                                        *(
                                            [
                                                ListTile(
                                                    leading=Icon(icons.FOLDER),
                                                    title=TextButton(
                                                        data=mod_list_path,
                                                        content=Row(
                                                            controls=[
                                                                Text(name),
                                                                Text(mod_list_path),
                                                                IconButton(
                                                                    data=mod_list_path,
                                                                    icon=icons.DELETE,
                                                                    on_click=self.settings_delete_custom_directory,
                                                                ),
                                                            ]
                                                        ),
                                                    ),
                                                )
                                                for name, mod_list_path in custom_directories
                                            ]
                                            if custom_directories
                                            else [
                                                ListTile(
                                                    leading=Icon(icons.FOLDER),
                                                    title=Text("No custom directories"),
                                                )
                                            ]
                                        )
                                    ]
                                ),
                            ]
                        )
                    ),
                ]
            )
        )
        await self.release_ui()

    async def settings_toggle_show_previews(self, event):
        self.page.preferences.mod_manager.show_previews = event.control.value
        self.page.preferences.save()

    async def settings_toggle_auto_fix_mod_names(self, event):
        self.page.preferences.mod_manager.auto_fix_mod_names = event.control.value
        self.page.preferences.save()

    async def settings_toggle_auto_generate_and_fix_cfg(self, event):
        self.page.preferences.mod_manager.auto_generate_and_fix_cfg = (
            event.control.value
        )
        self.page.preferences.save()

    async def settings_toggle_tile_toggle_cfg(self, event):
        self.page.preferences.mod_manager.tile_toggle = event.control.value
        self.page.preferences.save()

    async def settings_pick_custom_dir(self, event):
        await self.settings_custom_dir_pick.get_directory_path_async()

    async def settings_set_custom_dir(self, event):
        self.memory["settings"]["picked_custom_dir"] = Path(event.path)
        self.settings_picked_dir.value = (
            self.memory["settings"]["picked_custom_dir"]
            or "No picked directory (Pick your mods folder)"
        )
        await self.settings_picked_dir.update_async()

    async def settings_set_custom_dir_name(self, event):
        self.memory["settings"]["picked_custom_dir_name"] = event.control.value or None

    async def settings_add_custom_directory(self, event):
        self.settings_custom_dir_name = TextField(
            hint_text="Name",
            helper_style=TextStyle(color="red"),
            on_change=self.settings_set_custom_dir_name,
            autofocus=True,
        )
        self.settings_custom_dir_pick = FilePicker(
            on_result=self.settings_set_custom_dir
        )
        self.settings_picked_dir = Text("No picked directory (Pick your mods folder)")
        self.commit_custom_dir_button = IconButton(
            icon=icons.FOLDER,
            on_click=self.settings_pick_custom_dir,
        )
        await self.page.dialog.set_data(
            modal=False,
            title=Text("Add custom directory"),
            content=Column(
                controls=[
                    self.settings_custom_dir_name,
                    self.settings_custom_dir_pick,
                    Row(
                        controls=[
                            self.commit_custom_dir_button,
                            self.settings_picked_dir,
                        ]
                    ),
                ]
            ),
            actions=[
                ElevatedButton("Cancel", on_click=self.page.RTT.close_dialog),
                ElevatedButton(
                    "Confirm", on_click=self.settings_add_custom_directory_confirm
                ),
            ],
            actions_alignment=MainAxisAlignment.END,
        )

    async def settings_add_custom_directory_confirm(self, event):
        custom_directories = self.page.preferences.mod_manager.custom_directories
        picked_dir = self.memory["settings"]["picked_custom_dir"]
        picked_name = self.memory["settings"]["picked_custom_dir_name"]
        self.settings_custom_dir_name.helper_text = None
        if not picked_name or not picked_dir:
            self.settings_custom_dir_name.helper_text = (
                "A name and a directory are required"
            )
            await self.settings_custom_dir_name.update_async()
            return
        custom_dirs = [d for n, d in custom_directories]
        if picked_dir not in custom_dirs:
            custom_directories.append((picked_name, picked_dir))
            self.page.preferences.mod_manager.custom_directories = custom_directories
            self.page.preferences.save()
        self.memory["settings"]["picked_custom_dir"] = None
        self.memory["settings"]["picked_custom_dir_name"] = None
        await self.load_settings()
        await self.page.dialog.hide()

    async def settings_delete_custom_directory(self, event):
        custom_directories = deepcopy(
            self.page.preferences.mod_manager.custom_directories
        )
        for name, path in custom_directories:
            if path == event.control.data:
                self.page.preferences.mod_manager.custom_directories.remove(
                    (name, path)
                )
                break
        self.page.preferences.save()
        await self.load_settings()

    # My Mods Tab

    async def load_my_mods(self, boot=False):
        await self.lock_ui()
        self.my_mods.controls.clear()
        if not self.mod_folders:
            self.my_mods.controls.append(
                Text(
                    "No Trove installation found"
                    "\nTry running program as administrator or go to settings and add the directory manually."
                )
            )
            await self.release_ui()
            return
        self.my_mods.controls.append(
            Row(
                controls=[
                    IconButton(
                        icons.FOLDER_OPEN,
                        on_click=lambda x: os.startfile(
                            self.memory["my_mods"]["installation_path"].path
                        ),
                    ),
                    *(
                        [
                            Chip(
                                data=mod_list,
                                leading=Image(src=mod_list.icon, width=24),
                                label=Text(mod_list.clean_name),
                                disabled=mod_list
                                == self.memory["my_mods"]["installation_path"],
                                on_click=self.set_my_mods_installation_path,
                            )
                            for mod_list in self.mod_folders
                        ]
                    ),
                    TextField(
                        value=self.memory["my_mods"]["filter"],
                        label="Filter mods",
                        on_submit=self.filter_my_mods,
                        content_padding=padding.symmetric(0, 20),
                    ),
                ]
            )
        )
        installation_path = self.memory["my_mods"]["installation_path"]
        self.my_mod_list = TroveModList(
            path=installation_path,
            fix_names=self.page.preferences.mod_manager.auto_fix_mod_names,
            fix_configs=self.page.preferences.mod_manager.auto_generate_and_fix_cfg,
        )
        await self.my_mod_list.update_trovesaurus_data()
        await self.my_mod_list.cloud_check()
        if not self.my_mod_list.mods:
            self.my_mods.controls.append(Text("No mods in this directory"))
            await self.release_ui()
            return
        updates = [mod for mod in self.my_mod_list.mods if mod.has_update]
        self.my_mods.controls[0].controls.insert(
            1,
            IconButton(
                data=updates,
                icon=icons.DOWNLOAD,
                tooltip=f"Update {len(updates)} mods",
                on_click=self.update_mods,
                disabled=not bool(updates),
            ),
        )
        self.my_mods_list_maps = {
            i: [
                ExpansionTile(
                    title=Row(
                        controls=[
                            Image(
                                src="https://trovesaurus.com/images/logos/Sage_64.png?1",
                                width=24,
                            ),
                            Text("Trovesaurus"),
                        ]
                    ),
                    tile_padding=padding.symmetric(0, 10),
                    initially_expanded=True,
                    dense=True,
                ),
                ExpansionTile(
                    title=Row(controls=[Icon(icons.FOLDER), Text("Local")]),
                    tile_padding=padding.symmetric(0, 10),
                    initially_expanded=True,
                    dense=True,
                ),
            ]
            for i in range(2)
        }
        my_mods_list = ResponsiveRow(expand=True)
        self.enabled_mods_list = Column(
            controls=[
                Column(
                    controls=[self.my_mods_list_maps[0][0]],
                    spacing=0,
                    scroll=ScrollMode.ADAPTIVE,
                    expand=True,
                ),
                Divider(),
                Column(
                    controls=[self.my_mods_list_maps[0][1]],
                    spacing=0,
                    scroll=ScrollMode.ADAPTIVE,
                    expand=True,
                ),
            ],
            spacing=0,
            alignment="start",
            expand=True,
        )
        self.disabled_mods_list = Column(
            controls=[
                Column(
                    controls=[self.my_mods_list_maps[1][0]],
                    scroll=ScrollMode.ADAPTIVE,
                    expand=True,
                ),
                Divider(height=1),
                Column(
                    controls=[self.my_mods_list_maps[1][1]],
                    scroll=ScrollMode.ADAPTIVE,
                    expand=True,
                ),
            ],
            expand=True,
        )
        enabled_count = len(self.my_mod_list.enabled)
        disabled_count = len(self.my_mod_list.disabled)
        self.enabled_counter = Text(f"Enabled ({enabled_count})")
        self.disabled_counter = Text(f"Disabled ({disabled_count})")
        my_mods_list.controls.append(
            Column(
                controls=[
                    Row(
                        controls=[
                            Icon(icons.CHECK, color="green"),
                            self.enabled_counter,
                        ],
                        alignment="center",
                    ),
                    self.enabled_mods_list,
                ],
                expand=True,
                col=5.9,
            )
        )
        my_mods_list.controls.append(
            Row(controls=[VerticalDivider()], expand=True, col=0.2)
        )
        my_mods_list.controls.append(
            Column(
                controls=[
                    Row(
                        controls=[
                            Icon(icons.CANCEL, color="red"),
                            self.disabled_counter,
                        ],
                        alignment="center",
                    ),
                    self.disabled_mods_list,
                ],
                expand=True,
                col=5.9,
            )
        )
        self.my_mod_tiles = []
        filter = self.memory["my_mods"]["filter"]
        for mod in self.my_mod_list.mods:
            if (
                filter is not None
                and filter.lower() not in (mod.name + mod.author).lower()
            ):
                continue
            mod_frame = (
                self.my_mods_list_maps[0] if mod.enabled else self.my_mods_list_maps[1]
            )
            mod_frame_tile = mod_frame[0] if mod.trovesaurus_data else mod_frame[1]
            mt = self.get_mod_tile(mod)
            mod_frame_tile.controls.append(mt)
            if not mod.enabled:
                mt.controls.reverse()
            self.my_mod_tiles.append(mt)
        self.my_mods.controls.append(my_mods_list)
        await self.release_ui()

    async def filter_my_mods(self, event):
        self.memory["my_mods"]["filter"] = event.control.value or None
        await self.load_my_mods()

    def get_mod_tile(self, mod):
        mod_tile = ListTile(
            data=mod,
            content_padding=padding.symmetric(0, 5),
            expand=True,
            dense=True,
        )
        if self.page.preferences.mod_manager.tile_toggle:
            mod_tile.on_click = self.toggle_mod
        if mod.trovesaurus_data:
            if self.page.preferences.mod_manager.show_previews:
                mod_tile.leading = IconButton(
                    data=mod,
                    content=Image(
                        src=self.api.get_resized_image_url(
                            (
                                mod.trovesaurus_data.image_url
                                or f"https://kiwiapi.slynx.xyz/v1/mods/preview_image/{mod.hash}"
                            ),
                            ImageSize.SMALL,
                        ),
                        fit=ImageFit.FIT_HEIGHT,
                        expand=True,
                    ),
                    tooltip="Click to preview image",
                    style=ButtonStyle(padding=padding.symmetric(0, 0)),
                    on_click=self.go_to_image_preview,
                    width=64,
                    expand=True,
                )
            mod_tile.title = Row(
                controls=[
                    TextButton(
                        content=Text(mod.name),
                        height=28,
                        style=ButtonStyle(padding=padding.symmetric(4, 4)),
                        url=f"https://trovesaurus.com/mod={mod.trovesaurus_data.id}",
                    ),
                    RTTChip(label=Text(mod.trovesaurus_data.installed_version)),
                    *(
                        [
                            Tooltip(
                                data="update",
                                message="Update available",
                                content=IconButton(
                                    icons.DOWNLOAD,
                                    data=mod,
                                    icon_size=24,
                                    on_click=self.update_my_mods_mod,
                                ),
                            )
                        ]
                        if mod.has_update
                        else []
                    ),
                ]
            )
            mod_tile.subtitle = Row(
                controls=[
                    *(
                        [
                            Tooltip(
                                message=(author.Role if author.Role else "User"),
                                content=TextButton(
                                    content=Row(
                                        controls=[
                                            Image(
                                                src=self.api.get_resized_image_url(
                                                    author.avatar_url, ImageSize.MINI
                                                ),
                                                width=24,
                                            ),
                                            Text(
                                                author.Username,
                                                color=ModAuthorRoleColors[
                                                    ModAuthorRole(author.Role).name
                                                ].value,
                                            ),
                                        ]
                                    ),
                                    height=28,
                                    style=ButtonStyle(padding=padding.symmetric(4, 4)),
                                    url=f"https://trovesaurus.com/user={author.ID}",
                                ),
                            )
                            for author in mod.trovesaurus_data.authors
                        ]
                    )
                ]
            )
        else:
            if self.page.preferences.mod_manager.show_previews:
                mod_tile.leading = IconButton(
                    data=mod,
                    content=Image(
                        src=self.api.get_resized_image_url(
                            f"https://kiwiapi.slynx.xyz/v1/mods/preview_image/{mod.hash}",
                            ImageSize.SMALL,
                        ),
                        fit=ImageFit.FIT_HEIGHT,
                        expand=True,
                    ),
                    tooltip="Click to preview image",
                    style=ButtonStyle(padding=padding.symmetric(0, 0)),
                    on_click=self.go_to_image_preview,
                    width=64,
                    expand=True,
                )
            mod_tile.title = Row(controls=[Text(mod.name, height=28)])
            mod_tile.subtitle = Row(
                controls=[
                    TextButton(
                        content=Row(controls=[Icon(icons.PERSON), Text(mod.author)]),
                        height=28,
                        style=ButtonStyle(padding=padding.symmetric(4, 4)),
                        disabled=True,
                    )
                ]
            )
        if mod.has_conflicts:
            mod_tile.title.controls.append(
                Tooltip(
                    data="conflicts",
                    message=(
                        "One or more mods conflict with this mod:\n"
                        + (
                            f"(Conflicts may happen in game)\n\n"
                            if bool([c for c in mod.conflicts if c.enabled])
                            and mod.enabled
                            else "(Conflicts won't happen in game)\n\n"
                        )
                        + "\n".join([conflict.name for conflict in mod.conflicts])
                    ),
                    content=IconButton(
                        icons.WARNING,
                        icon_color=(
                            "red"
                            if bool([c for c in mod.conflicts if c.enabled])
                            and mod.enabled
                            else "yellow"
                        ),
                    ),
                )
            )
        return Row(
            data=mod,
            controls=[
                mod_tile,
                Tooltip(
                    message="Add to Profile",
                    content=IconButton(
                        icons.ADD,
                        on_click=self.add_my_mod_to_profile,
                        data=mod,
                        disabled=not bool(self.page.user_data),
                    ),
                ),
                Tooltip(
                    message="Uninstall",
                    content=IconButton(
                        icons.DELETE, on_click=self.delete_mod, data=mod
                    ),
                ),
                Tooltip(
                    message="Enable" if not mod.enabled else "Disable",
                    content=IconButton(
                        icons.ARROW_RIGHT if mod.enabled else icons.ARROW_LEFT,
                        on_click=self.toggle_mod,
                        data=mod,
                    ),
                ),
            ],
            expand=True,
            spacing=0,
        )

    async def go_to_image_preview(self, event):
        mod = event.control.data
        await self.page.dialog.set_data(
            modal=False,
            actions=[TextButton("Close", on_click=self.page.RTT.close_dialog)],
            content=Image(
                src=self.api.get_resized_image_url(
                    (f"https://kiwiapi.slynx.xyz/v1/mods/preview_image/{mod.hash}"),
                    ImageSize.MAX,
                ),
                fit=ImageFit.FIT_WIDTH,
                expand=True,
            ),
        )

    async def add_my_mod_to_profile(self, event):
        mod = event.control.data
        profiles = await self.api.list_profiles(self.page.user_data["internal_token"])
        if not profiles:
            return await self.page.snack_bar.show(
                "You don't have any profiles yet", color="red"
            )
        await self.page.dialog.set_data(
            modal=True,
            actions=[
                TextButton("Close", on_click=self.page.RTT.close_dialog),
            ],
            content=Column(
                controls=[
                    Text("Add to Profile"),
                    ListView(
                        controls=[
                            *(
                                [
                                    ListTile(
                                        leading=Icon(icons.PERSON),
                                        title=Text(profile["name"]),
                                        on_click=self.add_my_mod_to_profile_confirm,
                                        data=(profile, mod),
                                    )
                                    for profile in profiles
                                ]
                            )
                        ]
                    ),
                ]
            ),
        )

    async def add_my_mod_to_profile_confirm(self, event):
        profile, mod = event.control.data
        if mod.trovesaurus_data:
            await self.api.remove_mods_from_profile(
                self.page.user_data["internal_token"],
                profile["profile_id"],
                [f.hash for f in mod.trovesaurus_data.file_objs],
            )
        await self.api.add_mods_to_profile(
            self.page.user_data["internal_token"],
            profile["profile_id"],
            [mod.hash],
        )
        await self.page.dialog.hide()
        await self.page.snack_bar.show(f"Added {mod.name} to {profile['name']}")

    async def update_mods(self, event):
        await self.lock_ui()
        mods = event.control.data
        for mod in mods:
            await mod.update()
            await mod.update()
        await self.tab_loader(boot=True)
        await self.page.snack_bar.show(f"Updated {len(mods)} mods")

    async def update_my_mods_mod(self, event=None, mod=None):
        await self.lock_ui()
        mod = event.control.data or mod
        if not mod:
            return await self.release_ui()
        await mod.update()
        installation_path = self.memory["my_mods"]["installation_path"]
        self.my_mod_list = TroveModList(
            path=installation_path,
            fix_names=self.page.preferences.mod_manager.auto_fix_mod_names,
            fix_configs=self.page.preferences.mod_manager.auto_generate_and_fix_cfg,
        )
        await self.my_mod_list.update_trovesaurus_data()
        for tile in self.my_mod_tiles:
            if tile.data == mod:
                self.my_mod_tiles.remove(tile)
        for mod_frame_tile in self.my_mods_list_maps[0] + self.my_mods_list_maps[1]:
            mod_frame_tile.controls.clear()
        for mod in self.my_mod_list.mods:
            mod_frame = (
                self.my_mods_list_maps[0] if mod.enabled else self.my_mods_list_maps[1]
            )
            mod_frame_tile = mod_frame[0] if mod.trovesaurus_data else mod_frame[1]
            tile = self.get_mod_tile(mod)
            if not mod.enabled:
                tile.controls.reverse()
            self.my_mod_tiles.append(tile)
            mod_frame_tile.controls.append(tile)
            mod_frame_tile.controls.sort(
                key=lambda x: self.my_mod_list.mods.index(x.data)
            )
        await self.release_ui()

    async def toggle_mod(self, event):
        mod = event.control.data
        mod.toggle()
        for m in mod.file_conflicts:
            m.check_conflicts(self.my_mod_list.mods, True)
            await self.update_mod_tile_ui(m)
        mod.check_conflicts(self.my_mod_list.mods, True)
        await self.update_mod_tile_ui(mod, True)
        mod_frame = (
            self.my_mods_list_maps[0] if mod.enabled else self.my_mods_list_maps[1]
        )
        mod_frame_tile = mod_frame[0] if mod.trovesaurus_data else mod_frame[1]
        mod_frame_tile.controls.sort(key=lambda x: self.my_mod_list.mods.index(x.data))
        self.enabled_counter.value = f"Enabled ({len(self.my_mod_list.enabled)})"
        self.disabled_counter.value = f"Disabled ({len(self.my_mod_list.disabled)})"
        await self.page.snack_bar.show(
            f"{mod.name} {'enabled' if mod.enabled else 'disabled'}"
        )
        return await self.release_ui()

    async def update_mod_tile_ui(self, mod, move=False):
        if move:
            tile_index = -1 if mod.enabled else 0
        else:
            tile_index = 0 if mod.enabled else -1
        tile = next((t for t in self.my_mod_tiles if t.data == mod))
        for c in tile.controls[tile_index].title.controls:
            if c.data == "conflicts":
                c.content.icon_color = (
                    "red"
                    if bool([c for c in mod.conflicts if c.enabled]) and mod.enabled
                    else "yellow"
                )
        if move:
            icon_index = 0 if mod.enabled else -1
            icon = icons.ARROW_RIGHT if mod.enabled else icons.ARROW_LEFT
            start = (
                self.my_mods_list_maps[1] if mod.enabled else self.my_mods_list_maps[0]
            )
            end = (
                self.my_mods_list_maps[0] if mod.enabled else self.my_mods_list_maps[1]
            )
            start_mod_frame_tile = start[0] if mod.trovesaurus_data else start[1]
            end_mod_frame_tile = end[0] if mod.trovesaurus_data else end[1]
            start_mod_frame_tile.controls.remove(tile)
            end_mod_frame_tile.controls.append(tile)
            tile.controls[icon_index].content.icon = icon
            tile.controls.reverse()
            if mod.enabled:
                tile.controls[-1].message = "Disable"
            else:
                tile.controls[0].message = "Enable"

    async def delete_mod(self, event):
        mod = event.control.data
        mod.mod_path.unlink()
        tile = next((t for t in self.my_mod_tiles if t.data == mod))
        mod_frame = (
            self.my_mods_list_maps[0] if mod.enabled else self.my_mods_list_maps[1]
        )
        mod_frame_tile = mod_frame[0] if mod.trovesaurus_data else mod_frame[1]
        mod_frame_tile.controls.remove(tile)
        self.my_mod_tiles.remove(tile)
        self.my_mod_list.mods.remove(mod)
        self.enabled_counter.value = f"Enabled ({len(self.my_mod_list.enabled)})"
        self.disabled_counter.value = f"Disabled ({len(self.my_mod_list.disabled)})"
        await self.release_ui()
        await self.page.snack_bar.show(f"Uninstalled {mod.name}", color="red")

    async def set_my_mods_installation_path(self, event):
        self.memory["my_mods"]["installation_path"] = event.control.data
        await self.load_my_mods()

    # Trovesaurus Tab

    async def load_trovesaurus_mods(self, boot=False):
        await self.lock_ui()
        self.trovesaurus.controls.clear()
        if not self.mod_folders:
            self.trovesaurus.controls.append(
                Text(
                    "No Trove installation found"
                    "\nTry running program as administrator or go to settings and add the directory manually."
                )
            )
            await self.release_ui()
            return
        self.memory["trovesaurus"]["selected_file"] = None
        self.trovesaurus.controls.append(
            Row(
                controls=[
                    IconButton(
                        icons.FOLDER_OPEN,
                        on_click=lambda x: os.startfile(
                            self.memory["trovesaurus"]["installation_path"].path
                        ),
                    ),
                    *(
                        [
                            Chip(
                                data=mod_list,
                                leading=Image(src=mod_list.icon, width=24),
                                label=Text(mod_list.clean_name),
                                disabled=mod_list
                                == self.memory["trovesaurus"]["installation_path"],
                                on_click=self.set_trovesaurus_installation_path,
                            )
                            for mod_list in self.mod_folders
                        ]
                    ),
                ]
            )
        )
        self.trovesaurus_search_bar = TextField(
            value=self.memory["trovesaurus"]["search"]["query"],
            hint_text="Search",
            on_submit=self.trovesaurus_search_bar_submit,
            height=48,
            content_padding=padding.symmetric(0, 20),
        )
        mod_types = await self.api.get_mod_types()
        mod_sub_types = await self.api.get_mod_sub_types(
            str(self.memory["trovesaurus"]["search"]["type"])
        )
        sort_by = self.memory["trovesaurus"]["search"]["sort_by"]
        self.trovesaurus.controls.append(
            # Search bar
            Row(
                controls=[
                    self.trovesaurus_search_bar,
                    IconButton(
                        icon=icons.SEARCH, on_click=self.trovesaurus_search_bar_submit
                    ),
                    VerticalDivider(visible=True),
                    Text("Type:"),
                    Dropdown(
                        value=self.memory["trovesaurus"]["search"]["type"],
                        options=[dropdown.Option(key=None, text="All")]
                        + [dropdown.Option(key=t, text=t) for t in mod_types],
                        width=200,
                        height=48,
                        content_padding=padding.symmetric(4, 4),
                        on_change=self.set_trovesaurus_search_type,
                    ),
                    VerticalDivider(visible=True),
                    Text("Class:"),
                    Dropdown(
                        value=self.memory["trovesaurus"]["search"]["sub_type"],
                        options=[dropdown.Option(key=None, text="All")]
                        + [dropdown.Option(key=t, text=t) for t in mod_sub_types],
                        on_change=self.set_trovesaurus_search_sub_type,
                        width=200,
                        height=48,
                        content_padding=padding.symmetric(4, 4),
                        disabled=not bool(mod_sub_types),
                    ),
                    Row(
                        controls=[
                            Chip(
                                data=sorter,
                                label=Row(
                                    controls=[
                                        (
                                            Icon(icons.ARROW_UPWARD, color="green")
                                            if order == "asc"
                                            else Icon(icons.ARROW_DOWNWARD, color="red")
                                        ),
                                        # IconButton(
                                        #     data=((sorter, order), i - 1),
                                        #     icon=icons.ARROW_LEFT,
                                        #     icon_color="secondary",
                                        #     width=16,
                                        #     visible=i != 0,
                                        #     on_click=self.set_trovesaurus_sorter_reorder,
                                        # ),
                                        Text(sorter.replace("_", " ").capitalize()),
                                        # IconButton(
                                        #     data=((sorter, order), i + 1),
                                        #     icon=icons.ARROW_RIGHT,
                                        #     icon_color="secondary",
                                        #     width=16,
                                        #     visible=i != len(sort_by) - 1,
                                        #     on_click=self.set_trovesaurus_sorter_reorder,
                                        # ),
                                    ],
                                    alignment="center",
                                    run_spacing=4,
                                ),
                                on_click=self.set_trovesaurus_sorter_switch,
                            )
                            for i, (sorter, order) in enumerate(sort_by)
                        ]
                    ),
                ]
            )
        )
        self.mods_list = Column(scroll=ScrollMode.ADAPTIVE, expand=True)
        page_count = await self.api.get_mods_page_count(
            self.memory["trovesaurus"]["page_size"],
            self.memory["trovesaurus"]["search"]["query"],
            self.memory["trovesaurus"]["search"]["type"],
            self.memory["trovesaurus"]["search"]["sub_type"],
        )
        if self.memory["trovesaurus"]["page"] >= page_count:
            self.memory["trovesaurus"]["page"] = 0
        self.cached_trovesaurus_mods = await self.api.get_mods_list_chunk(
            self.memory["trovesaurus"]["page_size"],
            self.memory["trovesaurus"]["page"],
            self.memory["trovesaurus"]["search"]["query"],
            self.memory["trovesaurus"]["search"]["type"],
            self.memory["trovesaurus"]["search"]["sub_type"],
            self.memory["trovesaurus"]["search"]["sort_by"],
        )
        installation_path = self.memory["trovesaurus"]["installation_path"]
        mod_l = TroveModList(
            path=installation_path,
            fix_names=self.page.preferences.mod_manager.auto_fix_mod_names,
            fix_configs=self.page.preferences.mod_manager.auto_generate_and_fix_cfg,
        )
        await mod_l.update_trovesaurus_data()
        for i, mod in enumerate(self.cached_trovesaurus_mods):
            installed = False
            ts_mod = None
            for ts_mod in mod_l.mods:
                if ts_mod.trovesaurus_data:
                    if ts_mod.trovesaurus_data.id == mod.id:
                        installed = True
                        break
            self.mods_list.controls.append(
                ExpansionTile(
                    leading=Image(
                        src=(
                            self.api.get_resized_image_url(
                                mod.image_url, ImageSize.SMALL
                            )
                            or "https://trovesaurus.com/images/logos/Sage_64.png?1"
                        ),
                        width=64,
                        height=64,
                    ),
                    title=ResponsiveRow(
                        controls=[
                            Row(
                                alignment="start",
                                controls=[
                                    TextButton(
                                        content=Text(
                                            mod.name, color="#bbbbbb", size=18
                                        ),
                                        url=f"https://trovesaurus.com/mod={mod.id}",
                                    ),
                                    *(
                                        [
                                            RTTChip(
                                                label=Text(
                                                    ts_mod.trovesaurus_data.installed_version
                                                )
                                            ),
                                            Tooltip(
                                                message="Installed",
                                                content=Icon(
                                                    icons.CHECK, color="green"
                                                ),
                                            ),
                                        ]
                                        if installed
                                        else []
                                    ),
                                ],
                                col=6,
                            ),
                            Row(
                                controls=[
                                    RTTIconDecoButton(
                                        icon=icons.DOWNLOAD,
                                        text=Text(f"{mod.downloads:,}"),
                                        icon_color="primary",
                                        tooltip="Downloads",
                                    ),
                                    RTTIconDecoButton(
                                        icon=icons.FAVORITE,
                                        text=Text(f"{mod.likes:,}"),
                                        icon_color="pink",
                                        tooltip="Likes",
                                    ),
                                ],
                                alignment="end",
                                col=6,
                            ),
                        ],
                        alignment="SPACE_BETWEEN",
                        expand=True,
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
                                                            src=self.api.get_resized_image_url(
                                                                author.avatar_url,
                                                                ImageSize.MINI,
                                                            ),
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
                                                content=Text("No authors", color="red"),
                                                disabled=True,
                                            )
                                        ]
                                    )
                                ]
                            )
                        ]
                    ),
                    controls=[
                        Column(
                            controls=[
                                Text(mod.description) or Text("No description"),
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
                                            on_click=self.add_trovesaurus_mod_to_profile,
                                            col=1.4,
                                            disabled=not bool(self.page.user_data),
                                        ),
                                    ]
                                ),
                            ]
                        )
                    ],
                )
            )
        self.trovesaurus.controls.append(self.mods_list)
        self.trovesaurus.controls.append(
            Row(
                controls=[
                    IconButton(
                        icon=icons.ARROW_LEFT,
                        on_click=self.previous_trovesaurus_page,
                        disabled=page_count <= 1,
                    ),
                    Row(
                        controls=[
                            Text(f"Page"),
                            TextField(
                                value=str(self.memory["trovesaurus"]["page"] + 1),
                                on_submit=self.set_trovesaurus_page,
                                width=80,
                                height=48,
                                content_padding=padding.symmetric(0, 30),
                                disabled=page_count <= 1,
                            ),
                            Text(f"of {page_count}"),
                        ]
                    ),
                    IconButton(
                        icon=icons.ARROW_RIGHT,
                        on_click=self.next_trovesaurus_page,
                        disabled=page_count <= 1,
                    ),
                    VerticalDivider(visible=True),
                    Text("Mods per page:"),
                    NumberField(
                        value=self.memory["trovesaurus"]["page_size"],
                        hint_text="Mods per page",
                        on_submit=self.set_trovesaurus_page_size,
                        width=80,
                        height=48,
                        content_padding=padding.symmetric(0, 30),
                    ),
                ]
            )
        )
        if not boot:
            await self.page.snack_bar.show(f"Refreshed Trovesaurus")
        await self.release_ui()

    async def set_trovesaurus_sorter_reorder(self, event):
        pill, direction = event.control.data
        sort_by = self.memory["trovesaurus"]["search"]["sort_by"]
        index = sort_by.index(pill)
        sort_by.pop(index)
        new_order = []
        for i, p in enumerate(sort_by):
            if i == direction:
                new_order.append(pill)
            new_order.append(p)
        self.memory["trovesaurus"]["search"]["sort_by"] = new_order
        await self.load_trovesaurus_mods(boot=True)

    async def set_trovesaurus_sorter_switch(self, event):
        sorter = event.control.data
        new_order = [
            (s, o)
            for s, o in self.memory["trovesaurus"]["search"]["sort_by"]
            if s != sorter
        ]
        for s, o in self.memory["trovesaurus"]["search"]["sort_by"]:
            if s == sorter:
                new_order.insert(0, (s, "asc" if o == "desc" else "desc"))
        self.memory["trovesaurus"]["search"]["sort_by"] = new_order
        await self.load_trovesaurus_mods(boot=True)

    async def set_trovesaurus_search_type(self, event):
        selected_type = event.control.value
        if selected_type == "All":
            selected_type = None
        if selected_type is not None:
            sub_types = await self.api.get_mod_sub_types(selected_type)
            if not sub_types:
                self.memory["trovesaurus"]["search"]["sub_type"] = None
        else:
            self.memory["trovesaurus"]["search"]["sub_type"] = None

        self.memory["trovesaurus"]["search"]["type"] = selected_type
        await self.load_trovesaurus_mods(boot=True)

    async def set_trovesaurus_search_sub_type(self, event):
        self.memory["trovesaurus"]["search"]["sub_type"] = event.control.value
        await self.load_trovesaurus_mods(boot=True)

    async def trovesaurus_search_bar_submit(self, event):
        query = self.trovesaurus_search_bar.value
        self.memory["trovesaurus"]["search"]["query"] = query or None
        self.memory["trovesaurus"]["page"] = 0
        await self.load_trovesaurus_mods(boot=True)

    async def set_trovesaurus_page_size(self, event):
        page_size = int(event.control.value)
        if page_size > 25:
            page_size = 25
        if page_size < 5:
            page_size = 5
        self.page.preferences.mod_manager.page_size = page_size
        self.memory["trovesaurus"]["page_size"] = page_size
        self.page.preferences.save()
        await self.load_trovesaurus_mods(boot=True)

    async def previous_trovesaurus_page(self, event):
        self.memory["trovesaurus"]["page"] -= 1
        count = await self.api.get_mods_page_count(
            self.memory["trovesaurus"]["page_size"],
            self.memory["trovesaurus"]["search"]["query"],
            self.memory["trovesaurus"]["search"]["type"],
            self.memory["trovesaurus"]["search"]["sub_type"],
        )
        if self.memory["trovesaurus"]["page"] < 0:
            self.memory["trovesaurus"]["page"] = count - 1
        self.memory["trovesaurus"]["selected_tile"] = None
        await self.load_trovesaurus_mods(boot=True)

    async def next_trovesaurus_page(self, event):
        self.memory["trovesaurus"]["page"] += 1
        count = await self.api.get_mods_page_count(
            self.memory["trovesaurus"]["page_size"],
            self.memory["trovesaurus"]["search"]["query"],
            self.memory["trovesaurus"]["search"]["type"],
            self.memory["trovesaurus"]["search"]["sub_type"],
        )
        if self.memory["trovesaurus"]["page"] >= count:
            self.memory["trovesaurus"]["page"] = 0
        self.memory["trovesaurus"]["selected_tile"] = None
        await self.load_trovesaurus_mods(boot=True)

    async def set_trovesaurus_page(self, event):
        try:
            page = int(event.control.value) - 1
            if page < 0:
                page = 0
            count = await self.api.get_mods_page_count(
                self.memory["trovesaurus"]["page_size"],
                self.memory["trovesaurus"]["search"]["query"],
                self.memory["trovesaurus"]["search"]["type"],
                self.memory["trovesaurus"]["search"]["sub_type"],
            )
            if page >= count:
                page = count - 1
            self.memory["trovesaurus"]["page"] = page
            await self.load_trovesaurus_mods()
        except ValueError:
            pass

    async def set_trovesaurus_installation_path(self, event):
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

    async def add_trovesaurus_mod_to_profile(self, _):
        selected_file = self.memory["trovesaurus"]["selected_file"]
        if selected_file is None:
            return
        profiles = await self.api.list_profiles(self.page.user_data["internal_token"])
        if not profiles:
            return await self.page.snack_bar.show("No profiles found", color="red")
        await self.page.dialog.set_data(
            title=Text("Add to profile"),
            modal=True,
            actions=[TextButton("Cancel", on_click=self.page.RTT.close_dialog)],
            content=Column(
                controls=[
                    ListTile(
                        data=(selected_file, profile),
                        title=Text(profile["name"]),
                        subtitle=Text(profile["description"]),
                        leading=Image(
                            src="https://trovesaurus.com/images/logos/Sage_64.png?1",
                            width=24,
                        ),
                        on_click=self.add_trovesaurus_mod_to_profile_submit,
                    )
                    for profile in profiles
                ]
            ),
        )

    async def add_trovesaurus_mod_to_profile_submit(self, event):
        (mod_data, file_data, hashes), profile = event.control.data
        await self.api.remove_mods_from_profile(
            self.page.user_data["internal_token"], profile["profile_id"], hashes
        )
        await self.api.add_mods_to_profile(
            self.page.user_data["internal_token"],
            profile["profile_id"],
            [file_data.hash],
        )
        await self.page.dialog.hide()
        await self.tab_loader(index=self.mod_submenus.selected_index)
        await self.page.snack_bar.show(f"Added {mod_data.name} to {profile['name']}")

    async def install_mod(self, _):
        selected_file = self.memory["trovesaurus"]["selected_file"]
        if selected_file is None:
            return
        mod_data, file_data, hashes = selected_file
        installation_path = self.memory["trovesaurus"]["installation_path"]
        for mod_file in installation_path.mods_path.iterdir():
            if mod_file.is_file():
                hash = md5(mod_file.read_bytes()).hexdigest()
                if hash in hashes:
                    mod_file.unlink()
        url = f"https://trovesaurus.com/client/downloadfile.php?fileid={file_data.file_id}"
        async with ClientSession() as session:
            async with session.get(url) as response:
                data = await response.read()
                try:
                    mod = TMod.read_bytes(Path(""), data)
                    mod_name = mod.name
                except:
                    mod_name = mod_data.name.replace("/", "-")
                file_name = r"{0}.{1}".format(mod_name, file_data.type.value)
                file_path = installation_path.mods_path.joinpath(file_name)
                file_path.write_bytes(data)
        await self.tab_loader(index=self.mod_submenus.selected_index)
        await self.page.snack_bar.show(f"Installed {mod_name}")

    # Mod Profiles Tab

    async def load_mod_profiles(self, boot=False):
        await self.lock_ui()
        self.mod_profiles.controls.clear()
        if not self.page.user_data:
            self.mod_profiles.controls.append(
                Text("You need to be logged in to use this feature")
            )
            await self.release_ui()
            return
        self.mod_profiles.controls.append(
            TextButton(
                content=Text("Create new profile"), on_click=self.create_new_profile
            )
        )
        mod_profiles = await self.api.list_profiles(
            self.page.user_data["internal_token"]
        )
        if not mod_profiles:
            self.mod_profiles.controls.append(Text("No profiles found"))
            await self.release_ui()
            return
        for profile in mod_profiles:
            self.mod_profiles.controls.append(self.get_mod_profile_tile(profile))
        await self.release_ui()

    def get_mod_profile_tile(self, profile):
        return ExpansionTile(
            data=profile,
            title=Row(
                controls=[
                    Row(
                        controls=[
                            Icon(icons.PEOPLE if profile["shared"] else icons.LOCK),
                            Text(profile["name"], size=22),
                            Chip(
                                data=profile["profile_id"],
                                label=Text(f"Copy ID"),
                                visible=profile["shared"],
                                on_click=self.copy_profile_id,
                            ),
                            RTTChip(label=Text(f"{len(profile['mods'])} mods")),
                        ]
                    ),
                    Row(
                        controls=[
                            RTTIconDecoButton(
                                icon=icons.COPY,
                                icon_color="blue",
                                text=Text(f"{profile['clones']}"),
                                visible=profile["shared"],
                            ),
                            RTTIconDecoButton(
                                icon=icons.FAVORITE,
                                icon_color="pink",
                                text=Text(f"{len(profile['likes'])}"),
                                visible=profile["shared"],
                            ),
                        ]
                    ),
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
            ),
            subtitle=Text(profile["description"]),
            trailing=PopupMenuButton(
                icon=icons.MORE_VERT,
                items=[
                    PopupMenuItem(
                        icon=(icons.SHARE if not profile["shared"] else icons.LOCK),
                        text="Share" if not profile["shared"] else "Private",
                        data=profile,
                        on_click=self.toggle_share_profile,
                    ),
                    PopupMenuItem(
                        icon=icons.EDIT,
                        text="Edit",
                        data=profile,
                        on_click=self.edit_profile,
                    ),
                    PopupMenuItem(
                        icon=icons.DELETE,
                        text="Delete",
                        data=profile,
                        on_click=self.delete_profile,
                    ),
                ],
            ),
            controls=[
                ListTile(
                    leading=Image(
                        src=f"https://kiwiapi.slynx.xyz/v1/mods/preview_image/{mod['hash']}"
                    ),
                    title=Row(
                        controls=[
                            *(
                                [
                                    TextButton(
                                        mod["name"],
                                        url=f"https://trovesaurus.com/mod={mod['mod_id']}",
                                    )
                                ]
                                if mod.get("mod_id") is not None
                                else [Text(mod["name"])]
                            ),
                            *(
                                [
                                    RTTChip(
                                        leading=Image(
                                            src="https://trovesaurus.com/images/logos/Sage_64.png?1"
                                        ),
                                        label=Text("Trovesaurus"),
                                    )
                                ]
                                if mod.get("mod_id") is not None
                                else [
                                    RTTChip(
                                        leading=Icon(icons.FOLDER), label=Text("Local")
                                    )
                                ]
                            ),
                            RTTChip(label=Text(mod["format"].upper())),
                        ]
                    ),
                    subtitle=Column(
                        controls=[
                            Text(mod["description"], visible=bool(mod["description"])),
                            Row(
                                controls=[
                                    *(
                                        (
                                            TextButton(
                                                content=Row(
                                                    controls=[
                                                        Image(
                                                            src=author["Avatar"],
                                                            width=24,
                                                        ),
                                                        Tooltip(
                                                            message=(
                                                                author["Role"]
                                                                if author["Role"]
                                                                else "User"
                                                            ),
                                                            content=Text(
                                                                author["Username"],
                                                                color=ModAuthorRoleColors[
                                                                    author[
                                                                        "Role"
                                                                    ].lower()
                                                                ].value,
                                                            ),
                                                        ),
                                                    ]
                                                ),
                                                url=f"https://trovesaurus.com/user={author['ID']}",
                                            )
                                            if author["ID"]
                                            else TextButton(
                                                content=Row(
                                                    controls=[
                                                        Icon(icons.PERSON),
                                                        Text(author["Username"]),
                                                    ]
                                                ),
                                                disabled=True,
                                            )
                                        )
                                        for author in mod["authors"]
                                    )
                                ]
                            ),
                        ]
                    ),
                    trailing=IconButton(
                        data=mod,
                        icon=icons.DELETE,
                        on_click=self.remove_mod_from_profile,
                    ),
                )
                for mod in profile["mods"]
            ],
        )

    async def remove_mod_from_profile(self, event):
        holder = event.control.parent.parent
        profile = holder.data
        mod = event.control.data
        await self.api.remove_mods_from_profile(
            self.page.user_data["internal_token"], profile["profile_id"], [mod["hash"]]
        )
        profiles = await self.api.list_profiles(self.page.user_data["internal_token"])
        for profile in profiles:
            if profile["profile_id"] == holder.data["profile_id"]:
                new_holder = self.get_mod_profile_tile(profile)
                holder.title = new_holder.title
                holder.subtitle = new_holder.subtitle
                holder.controls = new_holder.controls
                break
        await event.control.update_async()
        await self.page.snack_bar.show(f"Removed {mod['name']} from {profile['name']}")

    async def copy_profile_id(self, event):
        profile_id = event.control.data
        await self.page.set_clipboard_async(profile_id)
        await self.page.snack_bar.show("Profile ID copied to clipboard")

    async def toggle_share_profile(self, event):
        profile = event.control.data
        shared = not profile["shared"]
        if shared:
            await self.api.share_profile(
                self.page.user_data["internal_token"], profile["profile_id"]
            )
        else:
            await self.api.private_profile(
                self.page.user_data["internal_token"], profile["profile_id"]
            )
        await self.load_mod_profiles()

    async def create_new_profile(self, event):
        await self.page.dialog.set_data(
            title=Text("Create new mod profile"),
            modal=True,
            actions=[
                TextButton("Cancel", on_click=self.page.RTT.close_dialog),
                TextButton("Create", on_click=self.create_profile),
            ],
            content=Column(
                controls=[
                    TextField(label="Profile name"),
                    TextField(label="Profile description"),
                ],
                spacing=20,
            ),
        )

    async def create_profile(self, event):
        profile_name = self.page.dialog.content.controls[0].value
        profile_description = self.page.dialog.content.controls[1].value
        await self.api.create_profile(
            self.page.user_data["internal_token"], profile_name, profile_description
        )
        await self.load_mod_profiles()
        await self.page.dialog.hide()

    async def edit_profile(self, event):
        profile = event.control.data
        await self.page.dialog.set_data(
            title=Text("Edit mod profile"),
            modal=True,
            actions=[
                TextButton("Cancel", on_click=self.page.RTT.close_dialog),
                TextButton("Save", data=profile, on_click=self.edit_profile_save),
            ],
            content=Column(
                controls=[
                    TextField(label="Profile name", value=profile["name"]),
                    TextField(
                        label="Profile description", value=profile["description"]
                    ),
                    TextField(label="Profile Image URL", value=profile["image_url"]),
                ],
                spacing=20,
            ),
        )

    async def edit_profile_save(self, event):
        profile = event.control.data
        profile_name = self.page.dialog.content.controls[0].value
        profile_description = self.page.dialog.content.controls[1].value or ""
        profile_image_url = self.page.dialog.content.controls[2].value or ""
        update = {}
        if profile_name and profile_name != profile["name"]:
            update["name"] = profile_name
        if (
            profile_description is not None
            and profile_description != profile["description"]
        ):
            update["description"] = profile_description or None
        if profile_image_url is not None and profile_image_url != profile["image_url"]:
            update["image_url"] = profile_image_url
        await self.api.update_profile(
            self.page.user_data["internal_token"], profile["profile_id"], **update
        )
        await self.load_mod_profiles()
        await self.page.dialog.hide()
        await self.page.snack_bar.show("Profile updated")

    async def delete_profile(self, event):
        await self.page.dialog.set_data(
            title=Text("Delete profile"),
            modal=True,
            actions=[
                TextButton("Cancel", on_click=self.page.RTT.close_dialog),
                TextButton(
                    "Delete",
                    data=event.control.data,
                    on_click=self.delete_profile_confirm,
                ),
            ],
            content=Text("Are you sure you want to delete this profile?"),
        )

    async def delete_profile_confirm(self, event):
        profile_id = event.control.data["profile_id"]
        await self.api.delete_profile(self.page.user_data["internal_token"], profile_id)
        await self.load_mod_profiles()
        await self.page.dialog.hide()
