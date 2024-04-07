import asyncio
import ctypes
import json
import os
import re
import shutil
from itertools import chain
from pathlib import Path

import humanize
import packaging.version as pv
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
    ScrollMode,
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
    Icon,
    Container,
    Switch,
    Stack,
    PopupMenuButton,
    PopupMenuItem,
)
from flet_core import padding, MainAxisAlignment, icons

from models.custom.projects import ProjectConfig, VersionConfig
from models.interface import Controller
from models.interface.controls import RegexField, PathViewer
from models.trove.directory import Directories
from models.trove.mod import TMod, TroveModFile
from utils.functions import throttle
from utils.kiwiapi import KiwiAPI
from utils.trove.extractor import find_all_indexes
from utils.trove.registry import get_trove_locations
from utils.trove.yaml_mod import ModYaml


class ModdersController(Controller):
    def setup_controls(self):
        if not hasattr(self, "main"):
            self.setup_memory()
            self.api = KiwiAPI()
            self.main = Column(expand=True)
            self.tabs = Tabs(selected_index=1, on_change=self.load_tab)
            self.settings_tab = Tab(icon=icons.SETTINGS)
            self.extract_tab = Tab("Extract TMod")
            self.compile_tab = Tab("Build TMod")
            self.projects_tab = Tab("Projects (BETA)")
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
            "extract": {
                "installation_path": None,
                "tmod_file": None,
                "output_path": None,
            },
            "compile": {"installation_path": None, "mod_data": ModYaml()},
            "projects": {
                "installation_path": None,
                "project_path": None,
                "selected_project": None,
                "config": None,
                "version": None,
            },
        }

    def check_memory(self):
        self.mod_folders = list(get_trove_locations())
        extract = self.memory["extract"]
        compile = self.memory["compile"]
        projects = self.memory["projects"]
        if not self.mod_folders:
            compile["installation_path"] = None
            extract["installation_path"] = None
            projects["installation_path"] = None
        else:
            if not compile["installation_path"]:
                compile["installation_path"] = self.mod_folders[0]
            else:
                if compile["installation_path"] not in self.mod_folders:
                    compile["installation_path"] = self.mod_folders[0]
            if not extract["installation_path"]:
                extract["installation_path"] = self.mod_folders[0]
            else:
                if extract["installation_path"] not in self.mod_folders:
                    extract["installation_path"] = self.mod_folders[0]
            if not projects["installation_path"]:
                projects["installation_path"] = self.mod_folders[0]
            else:
                if projects["installation_path"] not in self.mod_folders:
                    projects["installation_path"] = self.mod_folders[0]

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
        path = self.page.preferences.modders_tools.project_path
        self.project_folder_text_field = TextField(
            value=path.as_posix() if path else None,
            label="Project folder",
            hint_text="Select a project folder",
            read_only=True,
            expand=True,
            icon=icons.FOLDER,
            on_focus=self.select_project_folder,
        )
        self.clear_project_folder_button = IconButton(
            icons.CLEAR,
            on_click=self.clear_project_folder,
            tooltip="Clear project folder",
        )
        self.settings.controls.append(
            Row(
                controls=[
                    self.project_folder_text_field,
                    self.clear_project_folder_button,
                ]
            )
        )

    async def select_project_folder(self, event):
        self.page.overlay.clear()
        picker = FilePicker(on_result=self.select_project_folder_result)
        self.page.overlay.append(picker)
        await self.page.update_async()
        await picker.get_directory_path_async(dialog_title="Select Project Folder")

    async def select_project_folder_result(self, result):
        if not result.path:
            return
        path = Path(result.path)
        self.page.preferences.modders_tools.project_path = path
        self.project_folder_text_field.value = path.as_posix()
        await self.project_folder_text_field.update_async()
        self.page.preferences.save()
        await self.page.snack_bar.show("Project folder selected: " + path.as_posix())

    async def clear_project_folder(self, event):
        self.page.preferences.modders_tools.project_path = None
        self.project_folder_text_field.value = None
        await self.project_folder_text_field.update_async()
        self.page.preferences.save()
        await self.page.snack_bar.show("Project folder cleared")

    async def load_extract(self):
        directories = Row(
            controls=[
                IconButton(
                    icons.FOLDER_OPEN,
                    on_click=lambda x: os.startfile(
                        self.memory["extract"]["installation_path"].path
                    ),
                ),
                *(
                    [
                        Chip(
                            data=mod_list,
                            leading=Image(src=mod_list.icon, width=24),
                            label=Text(mod_list.clean_name),
                            disabled=mod_list
                            == self.memory["extract"]["installation_path"],
                            on_click=self.set_extract_installation_path,
                        )
                        for mod_list in self.mod_folders
                    ]
                ),
            ]
        )
        self.extract.controls.append(directories)
        self.tmod_text_field = TextField(
            label="TMod File",
            icon=icons.FOLDER,
            read_only=True,
            expand=True,
            on_focus=self.select_tmod_file,
        )
        self.extract.controls.append(Row(controls=[self.tmod_text_field]))
        self.output_path_text_field = TextField(
            label="Output Directory",
            read_only=True,
            expand=True,
            icon=icons.FOLDER,
            on_focus=self.select_output_directory,
        )
        self.extract.controls.append(Row(controls=[self.output_path_text_field]))
        self.extract.controls.append(
            Row(
                controls=[
                    ElevatedButton(
                        "Clear", icon=icons.CLEAR, on_click=self.clear_extract
                    ),
                    ElevatedButton(
                        "Extract TMod", icon=icons.BUILD, on_click=self.extract_tmod
                    ),
                    ElevatedButton(
                        "Extract overrides",
                        icon=icons.DETAILS,
                        on_click=self.extract_overrides,
                    ),
                ]
            )
        )

    async def set_extract_installation_path(self, event):
        self.memory["extract"]["installation_path"] = event.control.data
        await self.load_tab()

    async def select_tmod_file(self, _):
        self.page.overlay.clear()
        picker = FilePicker(on_result=self.extract_tmod_result)
        self.page.overlay.append(picker)
        await self.page.update_async()
        await picker.pick_files_async(
            dialog_title="Select TMod file",
            initial_directory=str(
                self.memory["extract"]["installation_path"].path.absolute()
            ),
            allow_multiple=False,
            allowed_extensions=["tmod", "tmod.disabled"],
        )

    async def extract_tmod_result(self, result):
        if not result.files:
            return
        file = Path(result.files[0].path)
        file_name = file.name
        self.memory["extract"]["tmod_file"] = file
        self.tmod_text_field.value = file_name
        await self.tmod_text_field.update_async()

    async def select_output_directory(self, event):
        self.page.overlay.clear()
        picker = FilePicker(on_result=self.extract_output_result)
        self.page.overlay.append(picker)
        await self.page.update_async()
        await picker.get_directory_path_async(
            dialog_title="Select Output Directory",
            initial_directory=str(
                self.memory["extract"]["installation_path"].path.absolute()
            ),
        )

    async def extract_output_result(self, result):
        if not result.path:
            return
        path = Path(result.path)
        self.memory["extract"]["output_path"] = path
        self.output_path_text_field.value = path.as_posix()
        await self.output_path_text_field.update_async()

    async def clear_extract(self, _):
        self.memory["extract"]["tmod_file"] = None
        self.memory["extract"]["output_path"] = None
        self.tmod_text_field.value = None
        self.output_path_text_field.value = None
        await self.tmod_text_field.update_async()
        await self.output_path_text_field.update_async()

    async def extract_tmod(self, _):
        if not self.memory["extract"]["tmod_file"]:
            return await self.page.snack_bar.show("TMod file is required", color="red")
        if not self.memory["extract"]["output_path"]:
            return await self.page.snack_bar.show(
                "Output directory is required", color="red"
            )
        tmod_file = self.memory["extract"]["tmod_file"]
        tmod = TMod.read_bytes(tmod_file, tmod_file.read_bytes())
        output = self.memory["extract"]["output_path"]
        for file in tmod.files:
            file_path = output.joinpath(file.trove_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(file.data)
        await self.page.snack_bar.show("TMod extracted")

    async def extract_overrides(self, _):
        if not self.memory["extract"]["tmod_file"]:
            return await self.page.snack_bar.show("TMod file is required", color="red")
        tmod_file = self.memory["extract"]["tmod_file"]
        tmod = TMod.read_bytes(tmod_file, tmod_file.read_bytes())
        game_path = self.memory["extract"]["installation_path"].path
        for file in tmod.files:
            trove_path = Path(file.trove_path)
            file_path = game_path.joinpath(
                trove_path.parent.joinpath("override").joinpath(trove_path.name)
            )
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(file.data)
        await self.page.snack_bar.show("TMod overrides extracted")

    async def load_compile(self):
        mod_types = await self.api.get_mod_types()
        mod_sub_types = await self.api.get_mod_sub_types(
            self.memory["compile"]["mod_data"].type
        )
        directories = Row(
            controls=[
                IconButton(
                    icons.FOLDER_OPEN,
                    on_click=lambda x: os.startfile(
                        self.memory["compile"]["installation_path"].path
                    ),
                ),
                *(
                    [
                        Chip(
                            data=mod_list,
                            leading=Image(src=mod_list.icon, width=24),
                            label=Text(mod_list.clean_name),
                            disabled=mod_list
                            == self.memory["compile"]["installation_path"],
                            on_click=self.set_compile_installation_path,
                        )
                        for mod_list in self.mod_folders
                    ]
                ),
            ]
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
            or "assets/images/no_preview.png",
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
                    on_focus=self.add_preview,
                )
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
                    on_focus=self.add_config,
                    disabled=not bool(
                        [
                            f[1]
                            for f in self.memory["compile"]["mod_data"].mod_files
                            if f[1].endswith(".swf")
                        ]
                    ),
                )
            ],
            expand=True,
        )
        header = ResponsiveRow(
            controls=[
                Column(
                    controls=[self.preview_image, self.preview_row, self.config_row],
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
                                "Clear all overrides",
                                icon=icons.CLEAR_ALL,
                                on_click=self.clear_overrides,
                            ),
                            ElevatedButton(
                                "Detect overrides",
                                icon=icons.SEARCH,
                                on_click=self.detect_overrides,
                            ),
                            ElevatedButton(
                                "Add files", icon=icons.ADD, on_click=self.add_file
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
                                "Build TMod", icon=icons.BUILD, on_click=self.build_tmod
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

    async def clear_overrides(self, event):
        install_path = self.memory["compile"]["installation_path"].path.as_posix()
        message = "Are you sure you want to clear all overrides?"
        message += "\n\nThis will remove all files in the 'override' directories within the Trove directory:"
        message += f"\n -> {install_path}"
        await self.page.dialog.set_data(
            modal=True,
            title=Text("Clear all overrides"),
            content=Text(message),
            actions=[
                ElevatedButton("No", on_click=self.close_dialog),
                ElevatedButton("Yes", on_click=self.clear_overrides_folders),
            ],
            actions_alignment=MainAxisAlignment.END,
        )

    async def clear_overrides_folders(self, _):
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
                try:
                    override.unlink()
                except Exception:
                    pass
        await self.page.dialog.hide()
        await self.page.snack_bar.show("Overrides cleared")

    async def close_dialog(self, _):
        await self.page.dialog.hide()

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
                if all(
                    [
                        self.memory["compile"]["mod_data"].preview,
                        self.memory["compile"]["mod_data"].preview[0] == override,
                    ]
                ):
                    continue
                if all(
                    [
                        self.memory["compile"]["mod_data"].config,
                        self.memory["compile"]["mod_data"].config[0] == override,
                    ]
                ):
                    continue
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
        true_override = f"ui/{file_name}"
        self.memory["compile"]["mod_data"].preview = (file, true_override)
        self.preview_image.src = str(file)
        await self.preview_image.update_async()
        self.preview_row.controls[0].value = file_name
        for f in self.memory["compile"]["mod_data"].mod_files:
            if f[0] == file:
                self.memory["compile"]["mod_data"].mod_files.remove(f)
        await self.update_file_list()
        await self.preview_row.controls[0].update_async()
        await self.page.snack_bar.show(f"Added {file_name}")

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
        for f in self.memory["compile"]["mod_data"].mod_files:
            if f[0] == file:
                self.memory["compile"]["mod_data"].mod_files.remove(f)
        await self.update_file_list()
        await self.page.snack_bar.show(f"Added {file_name}")

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
                    file.parent.parent.joinpath(file_name).relative_to(
                        self.memory["compile"]["installation_path"].path
                    )
                )
            except ValueError:
                trove_directory = self.memory["compile"]["installation_path"].name
                await self.page.snack_bar.show(
                    "File is not within the Trove directory selected "
                    + trove_directory,
                    color="red",
                )
                continue
            self.memory["compile"]["mod_data"].add_file(file, true_override)
            await self.page.snack_bar.show(f"Added {file_name}")
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
                                        )
                                    ],
                                    alignment=MainAxisAlignment.END,
                                )
                            ),
                        ]
                    )
                )
        if not boot:
            await self.files_list.update_async()

    async def build_tmod(self, _):
        mod = TMod()
        try:
            self.memory["compile"]["mod_data"].sanity_check()
        except (ValueError, FileNotFoundError) as e:
            message = Text("Mod data is not valid: " + str(e))
            if isinstance(e, FileNotFoundError):
                message += f" not found"
            return await self.page.snack_bar.show(message, color="red")
        mod.name = self.memory["compile"]["mod_data"].title
        mod.author = self.memory["compile"]["mod_data"].authors_string
        mod.add_property("notes", self.memory["compile"]["mod_data"].description)
        mod.add_property("tags", "")
        preview_path = self.memory["compile"]["mod_data"].preview[1]
        if preview_path:
            mod.preview_path = Path(preview_path)
            mod.add_file(
                TroveModFile(
                    Path(mod.preview_path),
                    self.memory["compile"]["mod_data"].preview[0].read_bytes(),
                )
            )
        else:
            mod.add_property("previewPath", "")
        config_path = self.memory["compile"]["mod_data"].config[1] or None
        if config_path:
            mod.add_property("configPath", config_path)
            mod.add_file(
                TroveModFile(
                    Path(config_path),
                    self.memory["compile"]["mod_data"].config[0].read_bytes(),
                )
            )
        try:
            mod.game_version = self.get_mod_version()
        except Exception:
            return await self.page.snack_bar.show(
                "Failed to get game version, please open trove at least once",
                color="red",
            )
        type = self.memory["compile"]["mod_data"].type
        if type:
            mod.add_tag(type)
        sub_type = self.memory["compile"]["mod_data"].sub_type
        if sub_type:
            mod.add_tag(sub_type)
        for file in self.memory["compile"]["mod_data"].mod_files:
            mod_file = TroveModFile(Path(file[1]), file[0].read_bytes())
            mod.add_file(mod_file)
        installation_path = self.memory["compile"]["installation_path"].path
        mod_location = installation_path.joinpath(f"mods/{mod.name}.tmod")
        mod_location.write_bytes(mod.tmod_content)
        await self.page.snack_bar.show(f"Built TMod {mod.name}")

    def get_mod_version(self):
        app_data = os.getenv("APPDATA")
        trove_path = Path(app_data).joinpath("Trove")
        config = trove_path.joinpath("Trove.cfg")
        version = re.findall("LastModVersion = (\d+)", config.read_text(), re.MULTILINE)
        return version[0]

    async def load_projects(self):
        if not self.page.preferences.modders_tools.project_path:
            self.projects.controls.append(
                Text(
                    "No project folder selected, please select one in the settings tab",
                    size=24,
                )
            )
            return
        project_path = self.page.preferences.modders_tools.project_path
        projects = []
        for folder in project_path.iterdir():
            if folder.is_dir():
                rtt = folder.joinpath(".rtt")
                config = rtt.joinpath("config.json")
                if rtt.exists() and config.exists():
                    projects.append(folder)
        if not projects:
            self.projects.controls.append(
                Text("No projects found in selected folder", size=24)
            )
            self.projects.controls.append(
                ElevatedButton(
                    "Create project", icon=icons.ADD, on_click=self.create_project
                )
            )
            return
        self.projects.controls.append(
            Row(
                controls=[
                    IconButton(
                        icons.FOLDER_OPEN,
                        on_click=lambda x: os.startfile(
                            self.memory["extract"]["installation_path"].path
                        ),
                    ),
                    *(
                        [
                            Chip(
                                data=mod_list,
                                leading=Image(src=mod_list.icon, width=24),
                                label=Text(mod_list.clean_name),
                                disabled=mod_list
                                == self.memory["extract"]["installation_path"],
                                on_click=self.set_extract_installation_path,
                            )
                            for mod_list in self.mod_folders
                        ]
                    ),
                ]
            )
        )
        self.projects_list = Tabs(on_change=self.project_tab_loader, expand=True)
        for project in projects:
            config = ProjectConfig.parse_obj(
                json.loads(project.joinpath(".rtt/config.json").read_text())
            )
            self.projects_list.tabs.append(
                Tab(
                    tab_content=Row(
                        data=project,
                        controls=[
                            IconButton(
                                icons.FOLDER_OPEN,
                                on_click=lambda x: os.startfile(project),
                            ),
                            Text(config.name),
                        ],
                    )
                )
            )
        self.projects.controls.append(
            Row(
                controls=[
                    ElevatedButton(
                        "Create project", icon=icons.ADD, on_click=self.create_project
                    ),
                    self.projects_list,
                ]
            )
        )
        self.project_control = Column(expand=True)
        self.projects.controls.append(self.project_control)
        await self.project_tab_loader()

    async def project_tab_loader(self, event=None):
        if event:
            project = event.tab_content.data
        else:
            selected_tab = self.projects_list.selected_index
            project = self.projects_list.tabs[selected_tab].tab_content.data
        installation_path = self.memory["extract"]["installation_path"].path
        self.project_control.controls.clear()
        config = ProjectConfig.parse_obj(
            json.loads(project.joinpath(".rtt/config.json").read_text())
        )
        self.memory["projects"]["config"] = config
        self.memory["projects"]["selected_project"] = project
        versions_folder = project.joinpath("versions")
        if not versions_folder.exists():
            versions_folder.mkdir(exist_ok=True)
        versions = []
        for version in versions_folder.iterdir():
            if version.is_dir():
                if version.joinpath("version.json").exists():
                    version_config = VersionConfig.parse_obj(
                        json.loads(version.joinpath("version.json").read_text())
                    )
                    versions.append((version, version_config))
        versions.reverse()
        if not self.memory["projects"]["version"]:
            self.memory["projects"]["version"] = versions[0] if versions else None
        else:
            if self.memory["projects"]["version"] not in versions:
                self.memory["projects"]["version"] = versions[0] if versions else None
        if not versions:
            self.project_control.controls.append(Text("No versions found", size=24))
            self.project_control.controls.append(
                ElevatedButton(
                    "Create version", icon=icons.ADD, on_click=self.create_version
                )
            )
            return
        version, version_config = self.memory["projects"]["version"]
        self.project_control.controls.append(
            Row(
                controls=[
                    Row(
                        controls=[
                            ElevatedButton(
                                "New version",
                                icon=icons.ADD,
                                on_click=self.create_version,
                            ),
                            *(
                                [
                                    Chip(
                                        data=(version, config),
                                        leading=Icon(icons.FOLDER),
                                        label=Text(config.version),
                                        disabled=config.version
                                        == version_config.version,
                                        on_click=self.set_version,
                                    )
                                    for version, config in versions
                                ]
                            ),
                        ]
                    ),
                    PopupMenuButton(
                        content=Row(
                            controls=[Icon(icons.API), Text("Get Modding Software")]
                        ),
                        items=[
                            PopupMenuItem(
                                data="blueprints",
                                text="Blueprints (.blueprint)",
                                icon=icons.SQUARE_FOOT,
                                on_click=self.show_software,
                            ),
                            PopupMenuItem(
                                data="vfx",
                                text="Particles (.pkfx)",
                                icon=icons.LOCAL_FIRE_DEPARTMENT,
                                on_click=self.show_software,
                            ),
                            PopupMenuItem(
                                data="textures",
                                text="Textures (.dds)",
                                icon=icons.BRUSH,
                                on_click=self.show_software,
                            ),
                            PopupMenuItem(
                                data="ui",
                                text="UI (.swf)",
                                icon=icons.GRID_VIEW,
                                on_click=self.show_software,
                            ),
                            PopupMenuItem(
                                data="sound",
                                text="Audio (.bnk)",
                                icon=icons.MUSIC_NOTE,
                                on_click=self.show_software,
                            ),
                        ],
                    ),
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
            )
        )
        mod_types = await self.api.get_mod_types()
        sub_types = await self.api.get_mod_sub_types(config.type)
        self.version_type_picker = Dropdown(
            label="Type",
            value=config.type,
            options=[dropdown.Option(key=t, text=t) for t in mod_types],
            icon=icons.CATEGORY,
            content_padding=padding.symmetric(4, 4),
            on_change=self.version_change_mod_type,
        )
        self.version_sub_type_picker = Dropdown(
            label="Class",
            value=config.sub_type,
            options=[dropdown.Option(key=t, text=t) for t in sub_types],
            icon=icons.CATEGORY,
            content_padding=padding.symmetric(4, 4),
            on_change=self.version_change_mod_sub_type,
            disabled=not bool(sub_types),
        )
        version_path = project.joinpath(f"versions/{version_config.version}")
        preview = None
        for file in chain(
            version_path.glob("*.png"),
            version_path.glob("*.jpg"),
            version_path.glob("*.jpeg"),
        ):
            preview = str(file)
            break
        config_file = None
        for file in version_path.glob("*.cfg"):
            config_file = file
            break
        self.project_control.controls.append(
            Row(
                controls=[
                    Container(
                        image_src=preview or "assets/images/no_preview.png",
                        content=Stack(
                            controls=[
                                *(
                                    [
                                        IconButton(
                                            icons.ADD, on_click=self.add_project_preview
                                        )
                                    ]
                                    if not preview
                                    else [
                                        IconButton(
                                            icons.CLEAR,
                                            on_click=self.clear_project_preview,
                                        )
                                    ]
                                )
                            ]
                        ),
                        width=400,
                        height=230,
                    ),
                    Column(
                        controls=[
                            Row(
                                controls=[
                                    Icon(icons.PERSON),
                                    *(
                                        [
                                            Chip(
                                                data=author,
                                                label=Text(author),
                                                on_click=self.remove_author,
                                            )
                                            for author in config.authors
                                        ]
                                    ),
                                    IconButton(
                                        icons.ADD,
                                        on_click=self.add_author,
                                        visible=len(config.authors) < 8,
                                    ),
                                ]
                            ),
                            TextField(
                                value=config.description,
                                label="Description",
                                icon=icons.DESCRIPTION,
                                multiline=True,
                                max_lines=3,
                                max_length=200,
                                content_padding=padding.symmetric(4, 8),
                                on_change=self.version_change_description,
                            ),
                            Row(
                                controls=[
                                    self.version_type_picker,
                                    self.version_sub_type_picker,
                                    TextField(
                                        value=(
                                            config_file.relative_to(
                                                version_path
                                            ).as_posix()
                                            if config_file
                                            else None
                                        ),
                                        label="Config file (.cfg)",
                                        icon=icons.SETTINGS,
                                        read_only=True,
                                        content_padding=padding.symmetric(4, 8),
                                    ),
                                ]
                            ),
                            TextField(
                                value=version_config.changes,
                                label="Changes",
                                hint_text="Enter changes",
                                icon=icons.TRACK_CHANGES,
                                multiline=True,
                                max_lines=3,
                                max_length=200,
                                content_padding=padding.symmetric(4, 8),
                                on_change=self.version_change_changes,
                            ),
                        ],
                        expand=True,
                        alignment=MainAxisAlignment.CENTER,
                    ),
                ],
                vertical_alignment="center",
            )
        )
        files = []
        if self.memory["projects"]["version"]:
            version_path = project.joinpath(
                f"versions/{self.memory['projects']['version'][1].version}"
            )
            for d in Directories:
                directory = version_path.joinpath(d.value)
                if not directory.exists():
                    continue
                for file in directory.rglob("*"):
                    if file.is_file():
                        files.append(file)
        self.project_control.controls.append(
            ResponsiveRow(
                controls=[
                    Card(
                        content=Column(
                            controls=[
                                DataTable(
                                    columns=[
                                        DataColumn(label=Text("File Path")),
                                        DataColumn(label=Text("Size"), numeric=True),
                                    ],
                                    vertical_lines=BorderSide(1, colors.GREY_800),
                                    rows=[
                                        *(
                                            [
                                                DataRow(
                                                    cells=[
                                                        DataCell(
                                                            TextButton(
                                                                data=file.parent,
                                                                text=file.relative_to(
                                                                    version_path
                                                                ),
                                                                on_click=lambda x: os.startfile(
                                                                    x.control.data
                                                                ),
                                                            )
                                                        ),
                                                        DataCell(
                                                            Text(
                                                                humanize.naturalsize(
                                                                    file.stat().st_size
                                                                )
                                                            )
                                                        ),
                                                    ]
                                                )
                                                for file in files
                                            ]
                                            if files
                                            else [
                                                DataRow(
                                                    cells=[
                                                        DataCell(
                                                            Text("No files found")
                                                        ),
                                                        DataCell(Text("")),
                                                    ]
                                                )
                                            ]
                                        )
                                    ],
                                )
                            ],
                            expand=True,
                            scroll=ScrollMode.ADAPTIVE,
                        ),
                        expand=True,
                        col=10,
                    ),
                    Card(
                        content=Container(
                            content=Column(
                                controls=[
                                    ElevatedButton(
                                        "Open version folder",
                                        icon=icons.FOLDER_OPEN,
                                        on_click=lambda x: os.startfile(version_path),
                                    ),
                                    ElevatedButton(
                                        "Refresh files list",
                                        icon=icons.REFRESH,
                                        on_click=self.refresh_files_list,
                                    ),
                                    ElevatedButton(
                                        "Fix files paths",
                                        icon=icons.FOLDER,
                                        on_click=self.fix_files_paths,
                                    ),
                                    ElevatedButton(
                                        "Extract from archives",
                                        icon=icons.DOWNLOAD,
                                        on_click=self.extract_from_archives,
                                    ),
                                    ElevatedButton(
                                        "Test overrides",
                                        icon=icons.LOGO_DEV,
                                        on_click=self.test_project_overrides,
                                    ),
                                    ElevatedButton(
                                        "Clear overrides",
                                        icon=icons.CLEAR_ALL,
                                        on_click=self.clear_project_overrides,
                                    ),
                                    ElevatedButton(
                                        "Build TMod",
                                        icon=icons.BUILD,
                                        on_click=self.build_project_tmod,
                                    ),
                                ],
                                expand=True,
                                alignment=MainAxisAlignment.CENTER,
                                horizontal_alignment="center",
                            ),
                            expand=True,
                        ),
                        expand=True,
                        col=2,
                    ),
                ],
                expand=True,
            )
        )
        if event:
            await self.projects.update_async()

    async def show_software(self, event):
        types_data = json.load(open("data/modding_software.json"))
        await self.page.dialog.set_data(
            modal=True,
            title=Text(event.control.text),
            content=Column(
                controls=[
                    Text(types_data[event.control.data]["description"]),
                    Text("Software:"),
                    *(
                        [
                            Column(
                                controls=[
                                    Row(
                                        controls=[
                                            Icon(
                                                icons.ATTACH_MONEY
                                                if not software["free"]
                                                else icons.MONEY_OFF
                                            ),
                                            TextButton(
                                                text=software["name"],
                                                url=software["url"],
                                            ),
                                        ]
                                    ),
                                    Text(software["description"]),
                                ]
                            )
                            for software in types_data[event.control.data]["software"]
                        ]
                    ),
                ],
                width=500,
            ),
            actions=[ElevatedButton("Close", on_click=self.page.RTT.close_dialog)],
        )

    async def create_project(self, event):
        types = await self.api.get_mod_types()
        sub_types = await self.api.get_mod_sub_types(types[0])
        await self.page.dialog.set_data(
            modal=True,
            title=Text("Create project"),
            content=Column(
                controls=[
                    TextField(
                        label="Project name (Mod name)",
                        hint_text="Enter project name (Mod name)",
                        icon=icons.TITLE,
                        max_length=100,
                    ),
                    TextField(
                        label="Author(s)",
                        hint_text="Enter author name (separate by comma for multiple authors)",
                        icon=icons.PERSON,
                        max_length=256,
                    ),
                    TextField(
                        label="Description",
                        hint_text="Enter project description",
                        icon=icons.DESCRIPTION,
                        multiline=True,
                        max_lines=5,
                        max_length=200,
                    ),
                    Dropdown(
                        label="Type",
                        options=[dropdown.Option(key=t, text=t) for t in types],
                        icon=icons.CATEGORY,
                        content_padding=padding.symmetric(4, 4),
                        on_change=self.project_change_mod_type,
                    ),
                    Dropdown(
                        label="Class",
                        options=[dropdown.Option(key=t, text=t) for t in sub_types],
                        icon=icons.CATEGORY,
                        content_padding=padding.symmetric(4, 4),
                        disabled=not bool(sub_types),
                    ),
                ],
                width=500,
            ),
            actions=[
                ElevatedButton("Cancel", on_click=self.page.RTT.close_dialog),
                ElevatedButton("Create", on_click=self.create_project_result),
            ],
        )

    async def project_change_mod_type(self, event):
        value = event.control.value
        if value == "None":
            value = None
        sub_types = await self.api.get_mod_sub_types(value)
        self.page.dialog.content.controls[4].options = [
            dropdown.Option(key=t, text=t) for t in sub_types
        ]
        self.page.dialog.content.controls[4].disabled = not bool(sub_types)
        if not sub_types:
            self.page.dialog.content.controls[4].value = None
        await self.page.dialog.content.controls[4].update_async()

    async def create_project_result(self, event):
        self.page.dialog.open = False
        await self.page.update_async()
        project_name = self.page.dialog.content.controls[0].value
        author_string = self.page.dialog.content.controls[1].value
        authors = [a.strip() for a in author_string.split(",") if a.strip()]
        description = self.page.dialog.content.controls[2].value
        project_path = self.page.preferences.modders_tools.project_path
        if not project_path.exists():
            self.page.preferences.modders_tools.project_path = None
            self.page.preferences.save()
            await self.page.snack_bar.show("Project folder not found", color="red")
            await self.load_tab()
            return
        project_folder = project_path.joinpath(project_name)
        self.memory["projects"]["selected_project"] = project_folder
        rtt = project_folder.joinpath(".rtt")
        rtt.mkdir(exist_ok=True, parents=True)
        try:
            ctypes.windll.kernel32.SetFileAttributesW(str(rtt), 2)
        except Exception:
            ...
        config = rtt.joinpath("config.json")
        tags = []
        tags.append(self.page.dialog.content.controls[3].value)
        tags.append(self.page.dialog.content.controls[4].value)
        config.write_text(
            ProjectConfig(
                name=project_name,
                authors=authors,
                description=description or "",
                tags=[t for t in tags if t is not None],
            ).json()
        )
        await self.page.snack_bar.show("Project created")
        await self.load_tab()
        await self.page.dialog.hide()

    async def create_version(self, event):
        await self.page.dialog.set_data(
            modal=True,
            title=Text("Create version"),
            content=Column(
                controls=[
                    RegexField(
                        pattern=re.compile(r"^(?:[0-9]+(?:\.[0-9]+)*)$", re.MULTILINE),
                        label="Version",
                        hint_text="Enter version number (e.g. 1.0.0)",
                        icon=icons.TRACK_CHANGES,
                        max_length=16,
                        autofocus=True,
                        on_change=lambda x: x.control.update_async(),
                    ),
                    Switch(label="Copy previous version", value=True),
                ],
                width=500,
            ),
            actions=[
                ElevatedButton("Cancel", on_click=self.page.RTT.close_dialog),
                ElevatedButton("Create", on_click=self.create_version_result),
            ],
        )

    async def create_version_result(self, event):
        await self.page.dialog.hide()
        versions = []
        for version in (
            self.memory["projects"]["selected_project"].joinpath("versions").iterdir()
        ):
            if version.is_dir():
                if version.joinpath("version.json").exists():
                    version_config = VersionConfig.parse_obj(
                        json.loads(version.joinpath("version.json").read_text())
                    )
                    versions.append((version, version_config))
        version_codes = [v[1].version for v in versions]
        version_codes.sort(key=lambda x: pv.parse(x), reverse=True)
        versions.sort(key=lambda x: version_codes.index(x[1].version))
        if not version_codes:
            latest_version = pv.parse("0.0.0")
            latest_version_data = None
        else:
            latest_version = pv.parse(version_codes[0])
            latest_version_data = versions[0]
        version = pv.parse(self.page.dialog.content.controls[0].value)
        if version < latest_version:
            return await self.page.snack_bar.show(
                "Version must be higher than latest", color="red"
            )
        for v, c in versions:
            if c.version == version:
                await self.page.dialog.hide()
                return await self.page.snack_bar.show(
                    "Version already exists", color="red"
                )
        copy_old = self.page.dialog.content.controls[1].value
        active_tab = self.projects_list.selected_index
        project = self.projects_list.tabs[active_tab].tab_content.data
        versions_folder = project.joinpath("versions")
        version_folder = versions_folder.joinpath(str(version))
        version_folder.mkdir(exist_ok=True, parents=True)
        for directory in Directories:
            version_folder.joinpath(directory.value).mkdir(exist_ok=True)
        if copy_old and version_codes:
            for file in latest_version_data[0].rglob("*"):
                if file.is_file():
                    new_file = version_folder.joinpath(
                        file.relative_to(latest_version_data[0])
                    )
                    new_file.parent.mkdir(exist_ok=True, parents=True)
                    new_file.write_bytes(file.read_bytes())
        version_config = VersionConfig(version=str(version), changes="")
        self.memory["projects"]["version"] = (version_folder, version_config)
        version_folder.joinpath("version.json").write_text(version_config.json())
        await self.page.snack_bar.show("Version created")
        await self.load_tab()

    async def set_version(self, event):
        self.memory["projects"]["version"] = event.control.data
        await self.load_tab()

    async def version_change_mod_type(self, event):
        value = event.control.value
        if value == "None":
            value = None
            self.memory["projects"]["config"].tags = []
        else:
            self.memory["projects"]["config"].tags = [value]
        sub_types = await self.api.get_mod_sub_types(value)
        self.version_sub_type_picker.options = [
            dropdown.Option(key=t, text=t) for t in sub_types
        ]
        self.version_sub_type_picker.value = None
        self.version_sub_type_picker.disabled = not bool(sub_types)
        self.save_project_config()
        await self.version_sub_type_picker.update_async()

    async def version_change_mod_sub_type(self, event):
        value = event.control.value
        tags = self.memory["projects"]["config"].tags
        self.memory["projects"]["config"].tags = (
            tags[:1] + [value] if value else tags[:1]
        )
        self.save_project_config()

    async def add_author(self, event):
        await self.page.dialog.set_data(
            modal=True,
            title=Text("Add author"),
            content=TextField(
                label="Author",
                hint_text="Enter author name",
                icon=icons.PERSON,
                max_length=24,
            ),
            actions=[
                ElevatedButton("Cancel", on_click=self.page.RTT.close_dialog),
                ElevatedButton("Add", on_click=self.add_author_result),
            ],
        )

    async def add_author_result(self, event):
        author = self.page.dialog.content.value
        author = "".join([a.strip() for a in author.split(",")][0])
        if author and author not in self.memory["projects"]["config"].authors:
            self.memory["projects"]["config"].authors.append(author)
            self.save_project_config()
        await self.page.dialog.hide()
        await self.load_tab()
        await self.page.snack_bar.show(f"Added {author}")

    async def remove_author(self, event):
        if len(self.memory["projects"]["config"].authors) == 1:
            return await self.page.snack_bar.show(
                "Cannot remove last author", color="red"
            )
        author = event.control.data
        await self.page.dialog.set_data(
            modal=True,
            title=Text("Remove author"),
            content=Text("Are you sure you want to remove this author?"),
            actions=[
                ElevatedButton("Cancel", on_click=self.page.RTT.close_dialog),
                ElevatedButton(
                    "Remove", data=author, on_click=self.remove_author_result
                ),
            ],
        )

    async def remove_author_result(self, event):
        author = event.control.data
        self.memory["projects"]["config"].authors.remove(author)
        self.save_project_config()
        await self.page.dialog.hide()
        await self.load_tab()
        await self.page.snack_bar.show(f"Removed {author}")

    @throttle
    async def version_change_description(self, event):
        self.memory["projects"]["config"].description = event.control.value
        self.save_project_config()

    @throttle
    async def version_change_changes(self, event):
        version, config = self.memory["projects"]["version"]
        config.changes = event.control.value
        version.joinpath("version.json").write_text(config.json())

    def save_project_config(self):
        self.memory["projects"]["selected_project"].joinpath(
            ".rtt/config.json"
        ).write_text(self.memory["projects"]["config"].json())

    async def refresh_files_list(self, event):
        await self.load_tab()

    async def test_project_overrides(self, event):
        project = self.memory["projects"]["selected_project"]
        version, version_config = self.memory["projects"]["version"]
        directories = [d.value for d in Directories]
        files = []
        version_folder = project.joinpath(f"versions/{version_config.version}")
        for d in directories:
            directory = version_folder.joinpath(d)
            if not directory.exists():
                continue
            for file in directory.rglob("*"):
                if file.is_file():
                    files.append(file)
        installation_path = self.memory["extract"]["installation_path"].path
        for file in files:
            file_name = file.name
            override = installation_path.joinpath(
                file.parent.relative_to(version_folder)
                .joinpath("override")
                .joinpath(file_name)
            )
            override.parent.mkdir(exist_ok=True, parents=True)
            shutil.copy(file, override)
        await self.page.snack_bar.show("Overrides copied")

    async def clear_project_overrides(self, event):
        project = self.memory["projects"]["selected_project"]
        version, version_config = self.memory["projects"]["version"]
        directories = [d.value for d in Directories]
        files = []
        version_folder = project.joinpath(f"versions/{version_config.version}")
        for d in directories:
            directory = version_folder.joinpath(d)
            if not directory.exists():
                continue
            for file in directory.rglob("*"):
                if file.is_file():
                    files.append(file)
        installation_path = self.memory["extract"]["installation_path"].path
        for file in files:
            file_name = file.name
            override = installation_path.joinpath(
                file.parent.relative_to(version_folder)
                .joinpath("override")
                .joinpath(file_name)
            )
            if override.exists():
                try:
                    override.unlink()
                except Exception:
                    pass
        await self.page.snack_bar.show("Overrides cleared")

    async def extract_from_archives(self, event):
        installation_path = self.memory["extract"]["installation_path"].path
        project_path = self.memory["projects"]["version"][0]
        await self.page.dialog.set_data(
            modal=True,
            title=Text("Extract from archives"),
            content=Column(
                controls=[PathViewer(installation_path, project_path=project_path)],
                width=500,
            ),
            actions=[ElevatedButton("Done", on_click=self.page.RTT.close_dialog)],
        )

    async def add_project_preview(self, event):
        self.page.overlay.clear()
        picker = FilePicker(on_result=self.add_project_preview_result)
        self.page.overlay.append(picker)
        await self.page.update_async()
        await picker.pick_files_async(dialog_title="Select preview image")

    async def add_project_preview_result(self, result):
        if not result.files:
            return
        file = Path(result.files[0].path)
        project = self.memory["projects"]["selected_project"]
        version, version_config = self.memory["projects"]["version"]
        version_folder = project.joinpath(f"versions/{version_config.version}")
        preview = version_folder.joinpath(file.name)
        shutil.copy(file, preview)
        await self.page.snack_bar.show("Preview added")
        await self.load_tab()

    async def clear_project_preview(self, event):
        project = self.memory["projects"]["selected_project"]
        version, version_config = self.memory["projects"]["version"]
        version_folder = project.joinpath(f"versions/{version_config.version}")
        for file in chain(
            version_folder.glob("*.png"),
            version_folder.glob("*.jpg"),
            version_folder.glob("*.jpeg"),
        ):
            try:
                file.unlink()
            except Exception:
                pass
        await self.page.snack_bar.show("Preview cleared")
        await self.load_tab()

    async def fix_files_paths(self, event):
        await self.lock_ui()
        project = self.memory["projects"]["selected_project"]
        version, version_config = self.memory["projects"]["version"]
        directories = [d.value for d in Directories]
        files = []
        version_folder = project.joinpath(f"versions/{version_config.version}")
        for d in directories:
            directory = version_folder.joinpath(d)
            if not directory.exists():
                continue
            for file in directory.rglob("*"):
                if file.is_file():
                    files.append(file)
        installation_path = self.memory["extract"]["installation_path"].path
        file_names = [f.name for f in files]
        async for index in find_all_indexes(installation_path, {}, False):
            for f in await index.files_list:
                if f["name"] in file_names:
                    for file in files:
                        if file.name == f["name"]:
                            f_rel_path = (
                                f["path"].relative_to(installation_path).as_posix()
                            )
                            file_rel_path = file.relative_to(version_folder).as_posix()
                            if f_rel_path != file_rel_path:
                                files.remove(file)
                                new_file_path = version_folder.joinpath(f_rel_path)
                                new_file_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.move(file, new_file_path)
                                files.append(new_file_path)
                                break
        await self.page.snack_bar.show("Files paths fixed")
        await self.load_tab()

    async def build_project_tmod(self, event):
        mod = TMod()
        installation_path = self.memory["projects"]["installation_path"].path
        project = self.memory["projects"]["selected_project"]
        config = self.memory["projects"]["config"]
        version, version_config = self.memory["projects"]["version"]
        mod.name = config.name
        mod.author = config.authors_string
        mod.notes = config.description or ""
        if config.type:
            mod.add_tag(config.type)
        if config.sub_type:
            mod.add_tag(config.sub_type)
        game_version = self.get_mod_version()
        mod.game_version = game_version
        mod.add_property("modVersion", version_config.version)
        mod.add_property("changes", version_config.changes)
        mod.add_property("modLoader", "RTT")
        files = []
        version_folder = project.joinpath(f"versions/{version_config.version}")
        for d in Directories:
            directory = version_folder.joinpath(d.value)
            if not directory.exists():
                continue
            for file in directory.rglob("*"):
                if file.is_file():
                    files.append(file)
        trove_files = [
            TroveModFile(file.relative_to(version_folder), file.read_bytes())
            for file in files
        ]
        for file in trove_files:
            mod.add_file(file)
        preview = None
        for file in chain(
            version_folder.glob("*.png"),
            version_folder.glob("*.jpg"),
            version_folder.glob("*.jpeg"),
        ):
            preview = file
            break
        if preview:
            preview_path = Path("ui").joinpath(preview.relative_to(version_folder))
            mod.preview_path = preview_path
            mod.add_file(TroveModFile(preview_path, preview.read_bytes()))
        cfg = None
        for file in version_folder.glob("*.cfg"):
            cfg = file
            break
        if cfg:
            mod.add_property("configPath", cfg.relative_to(version_folder).as_posix())
            mod.add_file(
                TroveModFile(cfg.relative_to(version_folder), cfg.read_bytes())
            )
        version_folder.joinpath(f"{mod.name}.tmod").write_bytes(mod.tmod_content)
        installation_path.joinpath(f"mods/{mod.name}.tmod").write_bytes(
            mod.tmod_content
        )
        await self.page.snack_bar.show(f"Built TMod {mod.name}")
