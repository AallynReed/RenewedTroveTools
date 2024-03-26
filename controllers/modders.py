import asyncio
import os
from itertools import chain
from pathlib import Path

import humanize
from flet import (
    Divider,
    Card,
    Text,
    TextButton,
    Column,
    Row,
    Chip,
    IconButton,
    Image,
    TextField,
    ElevatedButton,
    ResponsiveRow,
    VerticalDivider,
    Tabs,
    Tab,
    Dropdown,
    dropdown,
    DataTable,
    DataRow,
    DataColumn,
    DataCell,
    BorderSide,
    colors,
    FilePicker,
)
from flet_core import padding, MainAxisAlignment, icons

from models.interface import Controller
from models.trove.directory import Directories
from models.trove.mod import TMod, TroveModFile
from utils.functions import throttle
from utils.kiwiapi import KiwiAPI
from utils.trove.registry import get_trove_locations
from utils.trove.yaml_mod import ModYaml


class ModdersController(Controller):
    def setup_controls(self):
        if not hasattr(self, "main"):
            self.setup_memory()
            self.api = KiwiAPI()
            self.main = Column(expand=True)
            self.tabs = Tabs(selected_index=2, on_change=self.load_tab)
            self.settings_tab = Tab(icon=icons.SETTINGS)
            self.extract_tab = Tab("Extract TMod")
            self.compile_tab = Tab("Build TMod")
            self.projects_tab = Tab("Projects")
            self.settings = Column(expand=True)
            self.extract = Column(expand=True)
            self.compile = Column(expand=True)
            self.projects = Column(expand=True)
            self.tabs.tabs.append(self.settings_tab)
            self.tabs.tabs.append(self.extract_tab)
            self.tabs.tabs.append(self.compile_tab)
            self.tabs.tabs.append(self.projects_tab)
            self.tab_map = {
                0: self.load_settings,
                1: self.load_extract,
                2: self.load_compile,
                3: self.load_projects,
            }
            self.tab_controls = {
                0: self.settings,
                1: self.extract,
                2: self.compile,
                3: self.projects,
            }
            self.main.controls.append(self.tabs)
            asyncio.create_task(self.load_tab(boot=True))

    def setup_events(self):
        pass

    def setup_memory(self):
        self.memory = {
            "compile": {
                "installation_path": None,
                "mod_data": ModYaml(),
            }
        }

    def check_memory(self):
        self.mod_folders = list(get_trove_locations())
        compile = self.memory["compile"]
        if not self.mod_folders:
            compile["installation_path"] = None
        else:
            if not compile["installation_path"]:
                compile["installation_path"] = self.mod_folders[0]
            else:
                if compile["installation_path"] not in self.mod_folders:
                    compile["installation_path"] = self.mod_folders[0]

    async def load_tab(self, event=None, boot=False):
        if boot or event:
            self.check_memory()
        tab = self.tab_map.get(self.tabs.selected_index)
        self.main.controls.clear()
        self.main.controls.append(self.tabs)
        tab_control = self.tab_controls.get(self.tabs.selected_index)
        tab_control.controls.clear()
        await self.lock_ui()
        self.main.controls.append(tab_control)
        await tab()
        await self.release_ui()

    async def lock_ui(self):
        self.main.disabled = True
        await self.main.update_async()

    async def release_ui(self):
        self.main.disabled = False
        await self.main.update_async()

    async def load_settings(self):
        self.settings.controls.append(Text("Settings"))
        self.settings.controls.append(Divider())

    async def load_extract(self):
        self.extract.controls.append(
            Row(
                controls=[
                    Column(
                        controls=[
                            TextField(label="TMod File", icon=icons.FOLDER, expand=True)
                        ],
                        expand=True,
                    ),
                    Column(
                        controls=[
                            ElevatedButton(
                                text="Extract",
                                icon=icons.ARROW_DOWNWARD,
                                on_click=lambda: print("Extracting TMod"),
                            )
                        ]
                    ),
                ],
                expand=True,
            )
        )

    async def load_compile(self):
        mod_types = await self.api.get_mod_types()
        mod_sub_types = await self.api.get_mod_sub_types(
            self.memory["compile"]["mod_data"].type
        )
        directories = Row(
            controls=[
                Chip(
                    data=mod_list,
                    leading=Image(src=mod_list.icon, width=24),
                    label=Text(mod_list.clean_name),
                    disabled=mod_list == self.memory["compile"]["installation_path"],
                    on_click=self.set_compile_installation_path,
                )
                for mod_list in self.mod_folders
            ],
        )
        self.sub_type_dropdown = Dropdown(
            label="Class",
            value=self.memory["compile"]["mod_data"].sub_type,
            options=[dropdown.Option(key=t, text=t) for t in mod_sub_types],
            icon=icons.CATEGORY,
            content_padding=padding.symmetric(4, 4),
            disabled=not bool(mod_sub_types),
            on_change=self.change_mod_sub_type,
            expand=True,
        )
        self.preview_image = Image(
            src=self.memory["compile"]["mod_data"].preview[0]
            or "https://i.imgur.com/1zOz177.png",
            width=400,
            height=230,
        )
        self.preview_row = Row(
            controls=[
                TextField(
                    value=self.memory["compile"]["mod_data"].preview[1],
                    label="Preview",
                    icon=icons.IMAGE,
                    hint_text="Select Preview image",
                    read_only=True,
                    expand=True,
                ),
                IconButton(
                    icon=icons.FOLDER,
                    tooltip="Select Preview image",
                    on_click=self.add_preview,
                ),
            ],
            expand=True,
        )
        self.config_row = Row(
            controls=[
                TextField(
                    value=self.memory["compile"]["mod_data"].config[1],
                    label="Config",
                    icon=icons.SETTINGS,
                    hint_text="Select Config file",
                    read_only=True,
                    expand=True,
                    disabled=not bool(
                        [
                            f[1]
                            for f in self.memory["compile"]["mod_data"].mod_files
                            if f[1].endswith(".swf")
                        ]
                    ),
                ),
                IconButton(
                    icon=icons.FOLDER,
                    tooltip="Select Config file",
                    on_click=self.add_config,
                    disabled=not bool(
                        [
                            f[1]
                            for f in self.memory["compile"]["mod_data"].mod_files
                            if f[1].endswith(".swf")
                        ]
                    ),
                ),
            ],
            expand=True,
        )
        header = ResponsiveRow(
            controls=[
                Column(
                    controls=[
                        self.preview_image,
                        self.preview_row,
                        self.config_row,
                    ],
                    expand=True,
                    alignment="center",
                    horizontal_alignment="center",
                    col=3.8,
                ),
                Column(controls=[VerticalDivider(visible=True)], col=0.4),
                Column(
                    controls=[
                        TextField(
                            value=self.memory["compile"]["mod_data"].title,
                            label="Title",
                            icon=icons.TITLE,
                            max_length=100,
                            on_change=self.add_mod_title,
                        ),
                        TextField(
                            value=self.memory["compile"]["mod_data"].authors_string,
                            label="Author",
                            icon=icons.PERSON,
                            max_length=256,
                            on_change=self.add_mod_authors,
                        ),
                        TextField(
                            value=self.memory["compile"]["mod_data"].description,
                            label="Description",
                            icon=icons.DESCRIPTION,
                            multiline=True,
                            max_lines=5,
                            max_length=200,
                            on_change=self.add_mod_description,
                        ),
                        Row(
                            controls=[
                                Dropdown(
                                    label="Category",
                                    value=self.memory["compile"]["mod_data"].type,
                                    options=[dropdown.Option(key=None, text="All")]
                                    + [
                                        dropdown.Option(key=t, text=t)
                                        for t in mod_types
                                    ],
                                    icon=icons.CATEGORY,
                                    content_padding=padding.symmetric(4, 4),
                                    on_change=self.change_mod_type,
                                    expand=True,
                                ),
                                self.sub_type_dropdown,
                            ],
                            expand=True,
                        ),
                    ],
                    expand=True,
                    col=7.8,
                ),
            ],
            expand=True,
            alignment=MainAxisAlignment.CENTER,
            vertical_alignment="center",
        )
        self.files_list = DataTable(
            columns=[
                DataColumn(label=Text("File Path")),
                DataColumn(label=Text("Size"), numeric=True),
                DataColumn(label=Text("Actions"), numeric=True),
            ],
            vertical_lines=BorderSide(1, colors.GREY_800),
        )
        await self.update_file_list(True)
        files = ResponsiveRow(
            controls=[
                Card(
                    content=Column(
                        controls=[self.files_list], expand=True, scroll=True
                    ),
                    col=10,
                ),
                Card(
                    content=Column(
                        controls=[
                            ElevatedButton(
                                "Detect overrides",
                                icon=icons.DETAILS,
                                on_click=self.detect_overrides,
                            ),
                            ElevatedButton(
                                "Add files",
                                icon=icons.ADD,
                                on_click=self.add_file,
                            ),
                            ElevatedButton(
                                "Clear files",
                                icon=icons.CLEAR,
                                on_click=self.clear_files_list,
                            ),
                            ElevatedButton(
                                "Clear preview",
                                icon=icons.IMAGE,
                                on_click=self.clear_preview,
                            ),
                            ElevatedButton(
                                "Clear config",
                                icon=icons.SETTINGS,
                                on_click=self.clear_config,
                            ),
                            ElevatedButton(
                                "Build TMod",
                                icon=icons.BUILD,
                                on_click=self.build_tmod,
                            ),
                        ],
                        alignment=MainAxisAlignment.CENTER,
                        horizontal_alignment="center",
                        expand=True,
                    ),
                    col=2,
                ),
            ],
            expand=True,
        )
        self.compile.controls.append(directories)
        self.compile.controls.append(header)
        self.compile.controls.append(files)

    async def set_compile_installation_path(self, event):
        self.memory["compile"]["installation_path"] = event.control.data
        await self.load_tab()

    async def add_mod_title(self, event):
        text = event.control.value
        if not ModYaml.validate_title(text):
            event.control.border_color = "red"
            self.memory["compile"]["mod_data"].title = None
        else:
            event.control.border_color = "green"
            self.memory["compile"]["mod_data"].title = text
        await event.control.update_async()

    @throttle
    async def add_mod_authors(self, event):
        text = event.control.value.strip()
        if not text.endswith(","):
            authors = []
            raw_authors = [a.strip() for a in text.split(",") if a.strip()]
            for author in raw_authors:
                if author not in authors:
                    authors.append(author)
            text = ",".join(authors)
        event.control.value = text
        self.memory["compile"]["mod_data"].authors_string = text or None
        if not text:
            event.control.border_color = "red"
        else:
            event.control.border_color = "green"
        await event.control.update_async()

    async def add_mod_description(self, event):
        text = event.control.value
        self.memory["compile"]["mod_data"].description = text or None
        await event.control.update_async()

    async def change_mod_type(self, event):
        value = event.control.value
        if value == "All":
            value = None
        self.memory["compile"]["mod_data"].type = value
        self.sub_type_dropdown.value = None
        if not value:
            self.memory["compile"]["mod_data"].sub_type = None
            self.sub_type_dropdown.disabled = True
            self.sub_type_dropdown.options = []
        else:
            mod_sub_types = await self.api.get_mod_sub_types(
                self.memory["compile"]["mod_data"].type
            )
            self.sub_type_dropdown.options = [
                dropdown.Option(key=t, text=t) for t in mod_sub_types
            ]
            self.sub_type_dropdown.disabled = not bool(mod_sub_types)
            if not mod_sub_types:
                self.memory["compile"]["mod_data"].sub_type = None
        await self.sub_type_dropdown.update_async()

    async def change_mod_sub_type(self, event):
        self.memory["compile"]["mod_data"].sub_type = event.control.value

    async def detect_overrides(self, event):
        directories = [d.value for d in Directories]
        installation_path = self.memory["compile"]["installation_path"]
        overrides = []
        for file in self.memory["compile"]["mod_data"].mod_files:
            if not file[0].exists():
                self.memory["compile"]["mod_data"].remove_file(file[0])
        for file in installation_path.path.iterdir():
            if file.is_dir() and file.name in directories:
                for sub_file in file.rglob("override"):
                    if sub_file.is_dir():
                        overrides.append(sub_file.iterdir())
        for override in chain(*overrides):
            if override.is_file():
                file_name = override.name
                true_override = override.parent.parent.joinpath(file_name).relative_to(
                    installation_path.path
                )
                self.memory["compile"]["mod_data"].add_file(
                    override, str(true_override).replace("\\", "/")
                )
        self.memory["compile"]["mod_data"].mod_files.sort(key=lambda x: x[1])
        value = not bool(
            [
                f[1]
                for f in self.memory["compile"]["mod_data"].mod_files
                if f[1].endswith(".swf")
            ]
        )
        for control in self.config_row.controls:
            control.disabled = value
            await control.update_async()
        await self.update_file_list()

    async def add_preview(self, event):
        self.page.overlay.clear()
        picker = FilePicker(on_result=self.add_preview_result)
        self.page.overlay.append(picker)
        await self.page.update_async()
        await picker.pick_files_async(
            dialog_title="Select preview image",
            initial_directory=str(
                self.memory["compile"]["installation_path"].path.absolute()
            ),
            allow_multiple=False,
            allowed_extensions=["png", "jpg", "jpeg"],
        )

    async def add_preview_result(self, result):
        if not result.files:
            return
        file = Path(result.files[0].path)
        file_name = file.name
        true_override = "ui/preview.png"
        self.memory["compile"]["mod_data"].preview = (file, true_override)
        self.preview_image.src = str(file)
        await self.preview_image.update_async()
        self.preview_row.controls[0].value = file_name
        await self.preview_row.controls[0].update_async()
        self.page.snack_bar.content = Text(f"Added {file_name}")
        self.page.snack_bar.bgcolor = colors.GREEN
        self.page.snack_bar.open = True
        await self.page.snack_bar.update_async()

    async def clear_preview(self, event):
        self.memory["compile"]["mod_data"].preview = (None, None)
        self.preview_image.src = "https://i.imgur.com/1zOz177.png"
        await self.preview_image.update_async()
        self.preview_row.controls[0].value = None
        await self.preview_row.controls[0].update_async()

    async def add_config(self, event):
        self.page.overlay.clear()
        picker = FilePicker(on_result=self.add_config_result)
        self.page.overlay.append(picker)
        await self.page.update_async()
        await picker.pick_files_async(
            dialog_title="Select config file",
            initial_directory=str(
                self.memory["compile"]["installation_path"].path.absolute()
            ),
            allow_multiple=False,
            allowed_extensions=["cfg"],
        )

    async def add_config_result(self, result):
        if not result.files:
            return
        file = Path(result.files[0].path)
        file_name = file.name
        true_override = "ui/config.cfg"
        self.memory["compile"]["mod_data"].config = (file, true_override)
        self.config_row.controls[0].value = file_name
        await self.config_row.controls[0].update_async()
        self.page.snack_bar.content = Text(f"Added {file_name}")
        self.page.snack_bar.bgcolor = colors.GREEN
        self.page.snack_bar.open = True
        await self.page.snack_bar.update_async()

    async def clear_config(self, event):
        self.memory["compile"]["mod_data"].config = (None, None)
        self.config_row.controls[0].value = None
        await self.config_row.controls[0].update_async()

    async def add_file(self, event):
        self.page.overlay.clear()
        picker = FilePicker(on_result=self.add_file_result)
        self.page.overlay.append(picker)
        await self.page.update_async()
        await picker.pick_files_async(
            dialog_title="Select files to add to mod",
            initial_directory=str(
                self.memory["compile"]["installation_path"].path.absolute()
            ),
            allow_multiple=True,
        )

    async def add_file_result(self, result):
        if not result.files:
            return
        for f in result.files:
            file = Path(f.path)
            file_name = file.name
            try:
                true_override = str(
                    file.relative_to(self.memory["compile"]["installation_path"].path)
                )
            except ValueError:
                trove_directory = self.memory["compile"]["installation_path"].name
                self.page.snack_bar.content = Text(
                    f"File is not within the Trove directory selected {trove_directory}"
                )
                self.page.snack_bar.bgcolor = colors.RED
                self.page.snack_bar.open = True
                await self.page.snack_bar.update_async()
                continue
            self.memory["compile"]["mod_data"].add_file(file, true_override)
            self.page.snack_bar.content = Text(f"Added {file_name}")
            self.page.snack_bar.bgcolor = colors.GREEN
            self.page.snack_bar.open = True
            await self.page.snack_bar.update_async()
        await self.update_file_list()

    async def remove_file(self, event):
        self.memory["compile"]["mod_data"].remove_file(event.control.data)
        await self.update_file_list()

    async def clear_files_list(self, event):
        self.memory["compile"]["mod_data"].mod_files.clear()
        self.memory["compile"]["mod_data"].config = (None, None)
        for control in self.config_row.controls:
            control.disabled = True
            await control.update_async()
        await self.update_file_list()

    async def update_file_list(self, boot=False):
        self.files_list.rows.clear()
        if not self.memory["compile"]["mod_data"].mod_files:
            self.files_list.rows.append(
                DataRow(
                    cells=[
                        DataCell(Text("No files added")),
                        DataCell(Text("")),
                        DataCell(Text("")),
                    ]
                )
            )
        else:
            for f in self.memory["compile"]["mod_data"].mod_files:
                self.files_list.rows.append(
                    DataRow(
                        cells=[
                            DataCell(
                                TextButton(
                                    data=f[0].parent,
                                    text=f[1],
                                    on_click=lambda x: os.startfile(x.data),
                                )
                            ),
                            DataCell(Text(humanize.naturalsize(f[0].stat().st_size))),
                            DataCell(
                                Row(
                                    controls=[
                                        IconButton(
                                            data=f[0],
                                            icon=icons.DELETE,
                                            tooltip="Delete",
                                            on_click=self.remove_file,
                                        ),
                                    ],
                                    alignment=MainAxisAlignment.END,
                                )
                            ),
                        ]
                    )
                )
        if not boot:
            await self.files_list.update_async()

    async def build_tmod(self, event):
        mod = TMod()
        mod.name = self.memory["compile"]["mod_data"].title
        mod.author = self.memory["compile"]["mod_data"].authors_string
        mod.add_property("notes", self.memory["compile"]["mod_data"].description)
        preview_path = self.memory["compile"]["mod_data"].preview[1]
        if preview_path:
            mod.preview_path = Path(preview_path)
            mod.add_file(
                TroveModFile(
                    "",
                    Path(mod.preview_path),
                    self.memory["compile"]["mod_data"].preview[0].read_bytes(),
                )
            )
        else:
            mod.add_property("previewPath", "")
        config_path = self.memory["compile"]["mod_data"].config[1] or None
        if config_path:
            mod.add_property("config_path", config_path)
            mod.add_file(
                TroveModFile(
                    "",
                    Path(config_path),
                    self.memory["compile"]["mod_data"].config[0].read_bytes(),
                )
            )
        mod.game_version = "313"
        type = self.memory["compile"]["mod_data"].type
        if type:
            mod.add_tag(type[:-1])
        sub_type = self.memory["compile"]["mod_data"].sub_type
        if sub_type:
            mod.add_tag(sub_type)
        for file in self.memory["compile"]["mod_data"].mod_files:
            mod_file = TroveModFile("", Path(file[1]), file[0].read_bytes())
            mod.add_file(mod_file)
        installation_path = self.memory["compile"]["installation_path"].path
        mod_location = installation_path.joinpath(f"mods/{mod.name}.tmod")
        mod_location.write_bytes(mod.tmod_content)
        self.page.snack_bar.content = Text(f"Built TMod {mod.name}")
        self.page.snack_bar.bgcolor = colors.GREEN
        self.page.snack_bar.open = True
        await self.page.snack_bar.update_async()

    async def load_projects(self):
        self.projects.controls.append(Text("Projects"))
        self.projects.controls.append(Divider())
        self.projects.controls.append(Text("Coming soon..."))
