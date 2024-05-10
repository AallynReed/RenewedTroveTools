import asyncio
import json
import traceback
from datetime import datetime
from pathlib import Path
from time import perf_counter

from flet import (
    Column,
    ResponsiveRow,
    Row,
    Switch,
    Text,
    TextField,
    DataTable,
    DataColumn,
    IconButton,
    ElevatedButton,
    ProgressBar,
    Dropdown,
    dropdown,
    DataRow,
    DataCell,
    MainAxisAlignment,
    FilePicker,
) 
from utils.locale import loc
from flet_core import icons
from humanize import naturalsize
from yaml import dump

from models.interface import Controller
from models.interface.inputs import PathField
from utils import tasks
from utils.functions import long_throttle, throttle
from utils.trove.extractor import find_all_indexes, FileStatus
from utils.trove.registry import get_trove_locations


class ExtractorController(Controller):
    def setup_controls(self):
        if not hasattr(self.page, "main"):
            self.tfi_list = []
            self.main = ResponsiveRow(alignment=MainAxisAlignment.START)
            self.cancel_extraction = False
        self.trove_locations = list(get_trove_locations())
        self.locations = self.page.preferences.directories
        if self.trove_locations:
            directory = self.trove_locations[0]
            if self.locations.extract_from is None:
                self.locations.extract_from = directory.path
            if self.locations.extract_to is None:
                self.locations.extract_to = directory.path.joinpath("extracted")
            if self.locations.changes_to is None:
                self.locations.changes_to = directory.path.joinpath("changes")
            if self.locations.changes_from is None:
                self.locations.changes_from = directory.path.joinpath("extracted")
        self.extract_from = PathField(
            data="extract_from",
            label=f"{loc("Trove directory")}:",
            value=self.locations.extract_from,
            on_change=self.avoid_text_edit,
            col=10,
        )
        self.extract_to = PathField(
            data="extract_to",
            label=f"{loc("Extract to")}:",
            value=self.locations.extract_to,
            on_change=self.avoid_text_edit,
            # on_submit=self.set_text_directory,
            col=11,
        )
        self.changes_from = PathField(
            data="changes_from",
            label=f"{loc("Compare changes with")}:",
            value=self.locations.changes_from,
            on_change=self.avoid_text_edit,
            disabled=not self.page.preferences.advanced_mode,
            col=11,
        )
        self.changes_to = PathField(
            data="changes_to",
            label=f"{loc("Save changes to")}:",
            value=self.locations.changes_to,
            on_change=self.avoid_text_edit,
            disabled=not self.page.preferences.advanced_mode,
            col=7,
        )
        self.change_format = TextField(
            value=self.page.preferences.changes_name_format,
            on_change=self.set_changes_format,
            disabled=not self.page.preferences.advanced_mode,
            col=4,
        )
        self.changes_from_pick = IconButton(
            icons.FOLDER,
            data="changes_from",
            on_click=self.pick_directory,
            col=1,
            disabled=not self.page.preferences.advanced_mode,
        )
        self.changes_to_pick = IconButton(
            icons.FOLDER,
            data="changes_to",
            on_click=self.pick_directory,
            col=1,
            disabled=not self.page.preferences.advanced_mode,
        )
        self.extract_changes_button = ElevatedButton(
            loc("Extract changed files"), on_click=self.extract_changes, disabled=True, col=6
        )
        self.extract_selected_button = ElevatedButton(
            loc("Extract selected directories"),
            on_click=self.extract_selected,
            disabled=True,
            col=6,
        )
        self.extract_all_button = ElevatedButton(
            loc("Extract all"), on_click=self.extract_all, disabled=True, col=6
        )
        self.cancel_extraction_button = ElevatedButton(
            loc("Cancel extraction"),
            on_click=self.cancel_ongoing_extraction,
            visible=False,
            col=2,
        )
        self.directory_dropdown = Dropdown(
            value=(
                self.locations.extract_from
                if self.locations.extract_from in [g.path for g in self.trove_locations]
                else "none"
            ),
            options=[
                dropdown.Option(key=location, text=location.name)
                for location in self.trove_locations
            ]
            + [dropdown.Option(key="none", text="Custom", disabled=True)],
            on_change=self.change_directory_dropdown,
            col=6,
        )
        self.refresh_with_changes_button = ElevatedButton(
            loc("Refresh changed/added files list"),
            on_click=self.refresh_changes,
            disabled=not self.page.preferences.advanced_mode,
            col=6,
        )
        self.main_controls = ResponsiveRow(
            controls=[
                ResponsiveRow(
                    controls=[
                        ResponsiveRow(
                            controls=[
                                ResponsiveRow(
                                    controls=[
                                        IconButton(
                                            icons.FOLDER,
                                            data="extract_from",
                                            on_click=self.pick_directory,
                                            col=2,
                                        ),
                                        self.extract_from,
                                    ],
                                    vertical_alignment="center",
                                    col=6,
                                ),
                                self.directory_dropdown,
                            ]
                        ),
                        ResponsiveRow(
                            controls=[
                                IconButton(
                                    icons.FOLDER,
                                    data="extract_to",
                                    on_click=self.pick_directory,
                                    col=1,
                                ),
                                self.extract_to,
                            ],
                            vertical_alignment="center",
                            col=12,
                        ),
                        ElevatedButton(
                            loc("Refresh directory list"),
                            on_click=self.refresh_directories,
                            col=6,
                        ),
                        self.refresh_with_changes_button,
                        Row(
                            controls=[
                                Switch(
                                    value=self.page.preferences.advanced_mode,
                                    on_change=self.switch_advanced_mode,
                                ),
                                Text(loc("Advanced Settings")),
                            ],
                            col=6,
                        ),
                        Row(
                            controls=[
                                Switch(
                                    value=self.page.preferences.performance_mode,
                                    on_change=self.switch_performance_mode,
                                ),
                                Text(loc("Performance Mode")),
                            ],
                            col=6,
                        ),
                    ],
                    col=6,
                ),
                ResponsiveRow(
                    controls=[
                        ResponsiveRow(
                            controls=[
                                self.changes_from_pick,
                                self.changes_from,
                                ResponsiveRow(
                                    controls=[
                                        self.changes_to_pick,
                                        self.changes_to,
                                        self.change_format,
                                    ],
                                    vertical_alignment="center",
                                ),
                            ],
                            vertical_alignment="center",
                        ),
                        self.extract_changes_button,
                        self.extract_selected_button,
                        self.extract_all_button,
                    ],
                    col=6,
                ),
            ]
        )
        self.directory_progress = Column(
            controls=[
                Row(controls=[Text(loc("Loading files...")), Text("")]),
                ProgressBar(value=0, expand=False),
            ],
            visible=False,
        )
        self.directory_list = DataTable(
            columns=[
                DataColumn(Text(loc("Path")), on_sort=self.sort_by_path),
                DataColumn(Text(loc("Size")), on_sort=self.sort_by_size),
                DataColumn(Text(loc("Changed files")), on_sort=self.sort_by_changes),
            ],
            column_spacing=15,
            heading_row_height=35,
            data_row_min_height=25,
            sort_column_index=2,
            visible=False,
        )
        self.files_list = DataTable(
            columns=[DataColumn(Text(loc("Path"))), DataColumn(Text(loc("Size")))],
            column_spacing=15,
            heading_row_height=35,
            data_row_min_height=25,
            visible=False,
        )
        self.metrics = Column(
            controls=[
                Row(controls=[Text(f"{loc("Update Size")}:"), Text(naturalsize(0, gnu=True))])
            ]
        )
        self.extraction_progress = Column(
            controls=[
                Row(controls=[Text(loc("Extractor Idle")), Text("")], expand=False),
                ResponsiveRow(
                    controls=[
                        ProgressBar(height=30, value=0, col=10),
                        self.cancel_extraction_button,
                    ]
                ),
            ],
            horizontal_alignment="center",
        )
        self.select_all_button = ElevatedButton(
            loc("Select all"), on_click=self.select_all, disabled=True
        )
        self.unselect_all_button = ElevatedButton(
            loc("Unselect all"), on_click=self.unselect_all, disabled=True
        )
        self.main.controls = [
            Column(controls=[self.main_controls]),
            Column(controls=[self.extraction_progress]),
            Column(
                controls=[
                    Row(
                        controls=[
                            Text(loc("Directory List"), size=20),
                            self.select_all_button,
                            self.unselect_all_button,
                        ]
                    ),
                    self.directory_progress,
                    Column(controls=[self.directory_list], height=475, scroll="auto"),
                ],
                height=475,
                col=6,
                alignment=MainAxisAlignment.START,
            ),
            Column(
                controls=[
                    Text(loc("Changed/Added Files List"), size=20),
                    Column(controls=[self.files_list], height=475, scroll="auto"),
                ],
                height=475,
                col=6,
                alignment=MainAxisAlignment.START,
            ),
        ]

    def setup_events(self): ...

    @long_throttle
    async def set_changes_format(self, event):
        self.page.preferences.changes_name_format = event.control.value
        self.page.preferences.save()
        return await self.page.snack_bar.show(
            loc("Changed the format for changes folder"), color="green"
        )

    async def cancel_ongoing_extraction(self, _):
        self.cancel_extraction = True

    async def select_all(self, _):
        for row in self.directory_list.rows:
            row.selected = True
        self.extract_selected_button.disabled = False
        selected_size = sum(
            [
                f["size"]
                for r in self.directory_list.rows
                for f in await r.data.files_list
                if r.selected
            ]
        )
        self.extract_selected_button.text = (
            loc("Extract Selected [{Value}]".format(naturalsize(selected_size, gnu=True)))
        )
        await self.page.update_async()

    async def unselect_all(self, _):
        for row in self.directory_list.rows:
            row.selected = False
        self.extract_selected_button.disabled = True
        selected_size = sum(
            [
                f["size"]
                for r in self.directory_list.rows
                for f in await r.data.files_list
                if r.selected
            ]
        )
        self.extract_selected_button.text = (
            loc("Extract Selected [{Value}]".format(naturalsize(selected_size, gnu=True)))
        )
        await self.page.update_async()

    @throttle
    async def avoid_text_edit(self, event):
        event.control.value = getattr(self.locations, event.control.data)
        event.control.border_color = "red"
        event.control.error_text = loc("Please use directory selection button")
        await event.control.update_async()
        await asyncio.sleep(3)
        event.control.border_color = None
        event.control.error_text = None
        await event.control.update_async()

    async def sort_by_path(self, event):
        self.main.disabled = True
        await self.page.update_async()
        await asyncio.sleep(0.5)
        self.directory_list.rows.sort(
            key=lambda x: x.data.path, reverse=not event.ascending
        )
        self.directory_list.sort_ascending = event.ascending
        self.directory_list.sort_column_index = event.column_index
        self.main.disabled = False
        await self.page.update_async()

    async def sort_by_size(self, event):
        self.main.disabled = True
        await self.page.update_async()
        await asyncio.sleep(0.5)
        self.directory_list.rows.sort(
            key=lambda x: x.cells[2].data, reverse=not event.ascending
        )
        self.directory_list.sort_ascending = event.ascending
        self.directory_list.sort_column_index = event.column_index
        self.main.disabled = False
        await self.page.update_async()

    async def sort_by_changes(self, event):
        self.main.disabled = True
        await self.page.update_async()
        await asyncio.sleep(0.5)
        self.directory_list.rows.sort(
            key=lambda x: int(x.cells[event.column_index].content.value),
            reverse=not event.ascending,
        )
        self.directory_list.sort_ascending = event.ascending
        self.directory_list.sort_column_index = event.column_index
        self.main.disabled = False
        await self.page.update_async()

    async def pick_directory(self, event):
        file_picker = FilePicker(data=event.control.data, on_result=self.set_directory)
        self.page.overlay.append(file_picker)
        await self.page.update_async()
        await file_picker.get_directory_path_async(
            # initial_directory=str(
            #     Path(getattr(self.locations, event.control.data)).parent
            # )
        )

    async def set_directory(self, event):
        if event.path is None:
            return
        if event.control.data == "extract_from":
            known_directories = [
                "audio",
                "blueprints",
                "fonts",
                "languages",
                "models",
                "movies",
                "particles",
                "prefabs",
                "shadersunified",
                "textures",
                "ui",
            ]
            for directory in known_directories:
                if not Path(event.path).joinpath(directory).exists():
                    return await self.page.snack_bar.show(
                        loc("Please select a valid trove directory"), color="red"
                    )
            trove_path = Path(event.path)
            self.directory_dropdown.value = (
                trove_path
                if trove_path in [x[1] for x in self.trove_locations]
                else "none"
            )
        if event.control.data in ["extract_from", "changes_from"]:
            self.directory_list.rows.clear()
            self.files_list.rows.clear()
        setattr(self.locations, event.control.data, Path(event.path))
        control = getattr(self, event.control.data)
        setattr(control, "value", Path(event.path))
        self.page.preferences.save()
        await self.page.update_async()

    async def change_directory_dropdown(self, event):
        new_path = Path(event.control.value)
        old_path = Path(self.extract_from.value)
        self.extract_from.value = str(new_path)
        self.locations.extract_from = new_path
        for field in self.locations.__fields__:
            if field in ["extract_from", "changes_to"]:
                continue
            path = getattr(self.locations, field)
            try:
                final_path = new_path.joinpath(path.relative_to(old_path))
                setattr(self.locations, field, final_path)
                setattr(getattr(self, field), "value", final_path)
            except ValueError:
                continue
        self.page.preferences.save()
        await self.page.update_async()

    async def switch_advanced_mode(self, event):
        if event.control.value:
            if not self.page.preferences.dismissables.advanced_mode:
                await self.warn_advanced_mode()
        self.page.preferences.advanced_mode = event.control.value
        self.changes_to.disabled = not event.control.value
        self.changes_to_pick.disabled = not event.control.value
        self.changes_from.disabled = not event.control.value
        self.changes_from_pick.disabled = not event.control.value
        self.refresh_with_changes_button.disabled = not event.control.value
        self.change_format.disabled = not event.control.value
        self.page.preferences.save()
        await self.page.update_async()

    async def switch_performance_mode(self, event):
        if event.control.value:
            if not self.page.preferences.dismissables.performance_mode:
                await self.warn_performance_mode()
        self.page.preferences.performance_mode = event.control.value
        self.page.preferences.save()

    async def directory_selection(self, event):
        event.control.selected = not event.control.selected
        for row in self.files_list.rows:
            if row.data is not None:
                if row.data.archive.index == event.control.data:
                    row.visible = event.control.selected
        selected_indexes = [r.data for r in self.directory_list.rows if r.selected]
        changes = [f for f in self.changed_files if f.archive.index in selected_indexes]
        changes_size = sum([f.size for f in changes])
        selected_size = sum(
            [
                f["size"]
                for r in self.directory_list.rows
                for f in await r.data.files_list
                if r.selected
            ]
        )
        all_size = sum(
            [
                f["size"]
                for r in self.directory_list.rows
                for f in await r.data.files_list
            ]
        )
        self.extract_changes_button.text = (
            loc("Extract Changes [{Value}]".format(naturalsize(changes_size, gnu=True)))
        )
        self.extract_selected_button.text = (
            loc("Extract Selected [{Value}]".format(naturalsize(selected_size, gnu=True)))
        )
        self.extract_all_button.text = (
            loc("Extract All [{Value}]".format(naturalsize(all_size, gnu=True)))
        )
        self.extract_selected_button.disabled = not bool(
            [r for r in self.directory_list.rows if r.selected]
        )
        await self.page.update_async()

    async def refresh_directories(self, _):
        self.main.disabled = True
        self.refresh_lists.start()

    async def refresh_changes(self, _):
        self.main.disabled = True
        self.refresh_lists.start(True)

    @tasks.loop(seconds=1)
    async def refresh_lists(self, with_changes=False):
        try:
            self.directory_list.rows.clear()
            self.files_list.rows.clear()
            self.extract_changes_button.disabled = False
            self.extract_selected_button.disabled = False
            self.directory_progress.visible = True
            self.directory_list.visible = False
            self.files_list.visible = False
            await self.page.update_async()
            await asyncio.sleep(0.5)
            self.hashes = dict()
            if self.page.preferences.performance_mode:
                hashes_path = self.locations.extract_to.joinpath("hashes.json")
                if hashes_path.exists():
                    try:
                        self.hashes = json.loads(hashes_path.read_text())
                    except json.JSONDecodeError:
                        print(loc("Failed to load hashes, malformed file."))
            self.changed_files = []
            indexes = []
            i = 0
            async for index in find_all_indexes(
                self.locations.extract_from, self.hashes, False
            ):
                indexes.append([index, len(await index.files_list), 0])
            if with_changes:
                total_files = sum([index[1] for index in indexes])
                progress = 0
                start = perf_counter()
                for index, files_count, _ in indexes:
                    index_hash = self.hashes.get(
                        str(index.path.relative_to(self.locations.extract_from))
                    )
                    if index_hash is None or (await index.content_hash) != index_hash:
                        for archive in index.archives:
                            archive_hash = self.hashes.get(
                                archive.path.relative_to(self.locations.extract_from)
                            )
                            if (
                                archive_hash is None
                                or (await archive.content_hash) != archive_hash
                            ):
                                async for file in archive.files():
                                    i += 1
                                    if progress < (
                                        new_progress := round(i / total_files * 1000)
                                        / 1000
                                    ):
                                        elapsed = perf_counter() - start
                                        remaining = round(
                                            elapsed * (total_files / i - 1)
                                        )
                                        self.directory_progress.controls[0].controls[
                                            1
                                        ].value = f"[{round(i / total_files * 100, 1)}%] | Elapsed: {round(elapsed):>3}s | Estimated {remaining:>3}s remaining\r"
                                        progress = new_progress
                                        self.directory_progress.controls[1].value = (
                                            new_progress
                                        )
                                        await self.directory_progress.update_async()
                                    if (
                                        await file.compare(
                                            self.locations.extract_from,
                                            self.locations.changes_from,
                                        )
                                    ) in [FileStatus.added, FileStatus.changed]:
                                        self.changed_files.append(file)
                            else:
                                i += len(
                                    [
                                        f
                                        for f in archive.index.files_list()
                                        if int(f["archive_index"]) == archive.id
                                    ]
                                )
                    else:
                        i += files_count
            if self.changed_files:
                self.changed_files.sort(key=lambda x: [x.archive.index.path, x.path])
                for file in self.changed_files:
                    for index in indexes:
                        if index[0] == file.archive.index:
                            index[2] += 1
                            break
            else:
                self.extract_changes_button.disabled = True
                self.extract_selected_button.disabled = True
            indexes.sort(key=lambda x: [-x[2], str(x[0].directory)])
            for index, files_count, changes_count in indexes:
                self.directory_list.rows.append(
                    DataRow(
                        data=index,
                        cells=[
                            DataCell(
                                Text(
                                    str(
                                        index.directory.relative_to(
                                            self.locations.extract_from
                                        )
                                    ),
                                    color="green" if changes_count else None,
                                    size=12,
                                )
                            ),
                            DataCell(
                                Text(
                                    naturalsize(
                                        sum(
                                            [f["size"] for f in await index.files_list]
                                        ),
                                        gnu=True,
                                    ),
                                    color="green" if changes_count else None,
                                    size=12,
                                ),
                                data=sum([f["size"] for f in await index.files_list]),
                            ),
                            DataCell(
                                Text(
                                    changes_count,
                                    color="green" if changes_count else None,
                                    size=12,
                                )
                            ),
                        ],
                        selected=bool(changes_count),
                        on_select_changed=self.directory_selection,
                    )
                )
            if len(self.changed_files) > 2000:
                self.files_list.rows.append(
                    DataRow(
                        cells=[
                            DataCell(
                                Text(loc("Too many changes to be displayed."), color="red")
                            ),
                            DataCell(Text("")),
                        ]
                    )
                )
            elif not with_changes:
                self.files_list.rows.append(
                    DataRow(
                        cells=[
                            DataCell(Text(loc("No changes were queried."))),
                            DataCell(Text("")),
                        ]
                    )
                )
                self.extract_changes_button.disabled = True
            elif len(self.changed_files) == 0:
                self.files_list.rows.append(
                    DataRow(
                        cells=[
                            DataCell(Text(loc("No changed files found."))),
                            DataCell(Text("")),
                        ]
                    )
                )
                self.extract_changes_button.disabled = True
            else:
                for file in self.changed_files:
                    self.files_list.rows.append(
                        DataRow(
                            data=file,
                            cells=[
                                DataCell(
                                    Text(
                                        file.path.relative_to(
                                            self.locations.extract_from
                                        ),
                                        color=file.color,
                                        size=12,
                                    )
                                ),
                                DataCell(
                                    Text(
                                        naturalsize(file.size, gnu=True),
                                        color=file.color,
                                        size=12,
                                    )
                                ),
                            ],
                        )
                    )
                self.extract_changes_button.disabled = False
            selected_indexes = [r.data for r in self.directory_list.rows if r.selected]
            changes = [
                f for f in self.changed_files if f.archive.index in selected_indexes
            ]
            changes_size = sum([f.size for f in changes])
            selected_size = sum(
                [
                    f["size"]
                    for r in self.directory_list.rows
                    for f in await r.data.files_list
                    if r.selected
                ]
            )
            all_size = sum(
                [
                    f["size"]
                    for r in self.directory_list.rows
                    for f in await r.data.files_list
                ]
            )
            self.extract_changes_button.text = (
                loc("Extract Changes [{Value}]".format(naturalsize(changes_size, gnu=True)))
            )
            self.extract_selected_button.text = (
                loc("Extract Selected [{Value}]".format(naturalsize(selected_size, gnu=True)))
            )
            self.extract_all_button.text = (
                loc("Extract All [{Value}]".format(naturalsize(all_size, gnu=True)))
            )
            self.metrics.controls[0].controls[1].value = naturalsize(
                sum([f.size for f in self.changed_files]), gnu=True
            )
            self.directory_progress.controls[0].controls[1].value = ""
            self.directory_progress.controls[1].value = 0
            self.extract_selected_button.disabled = not bool(
                [r for r in self.directory_list.rows if r.selected]
            )
            self.select_all_button.disabled = False
            self.unselect_all_button.disabled = False
            self.extract_all_button.disabled = False
            self.directory_progress.visible = False
            self.directory_list.visible = True
            self.files_list.visible = True
            self.main.disabled = False
            await self.page.update_async()
            self.refresh_lists.cancel()
        except Exception as e:
            print("".join(traceback.format_exception(type(e), e, e.__traceback__)))

    async def warn_advanced_mode(self):
        task_lines = [
            loc("Advanced mode allows for people to have old vs new changed files in a separate directory"),
            loc("This will provide a better way to compare updates whilst having no real hustle to separate these changes"),
            loc("Eliminating the need of 1gb folders for each update and keeping it streamlined to the true changes"),
        ]
        task = "\n\n".join(task_lines)
        await self.page.dialog.set_data(
            modal=False,
            title=Text(loc("Advanced mode enabled")),
            content=Text(task),
            actions=[
                ElevatedButton(loc("Don't show again"), on_click=self.am_dont_show),
                ElevatedButton(loc("Ok"), on_click=self.page.RTT.close_dialog),
            ],
            actions_alignment=MainAxisAlignment.END,
        )

    async def warn_performance_mode(self):
        task_lines = [
            "Performance mode is a very sensitive mode, it will create a cache of some of the file's data and improve "
            "performance of changes detection beyond imaginable",
            "But it comes with the caveat that it will have the wrong results if you use any other tool, "
            "this is because it won't have the information that an extraction or update happened, so when trying to "
            "track changes through this cache it will assume a state that may not match."
            "If you only plan to use this tool as your only extraction method, you may enable this with no worry"
            "If you plan on using any other extraction method however, be weary of the issues this cache may present "
            "to the accuracy of change tracking."
            "Even out of performance mode, this app will most likely manage faster speeds than other methods (I know "
            "of).",
        ]
        task = "\n\n".join(task_lines)
        await self.page.dialog.set_data(
            modal=False,
            title=Text(loc("Performance mode enabled")),
            content=Text(task),
            actions=[
                ElevatedButton(loc("Don't show again"), on_click=self.pm_dont_show),
                ElevatedButton(loc("Ok"), on_click=self.page.RTT.close_dialog),
            ],
            actions_alignment=MainAxisAlignment.END,
        )

    async def pm_dont_show(self, _):
        self.page.preferences.dismissables.performance_mode = True
        self.page.preferences.save()
        await self.page.dialog.hide()

    async def am_dont_show(self, _):
        self.page.preferences.dismissables.advanced_mode = True
        self.page.preferences.save()
        await self.page.dialog.hide()

    async def warn_extraction(self, extraction_type: str):
        task = loc("Do you really wish to extract {ExtractionType} from {ExtractFrom} into {ExtractTo}".format(ExtractionType=extraction_type,ExtractFrom=self.locations.extract_from,ExtractTo=self.locations.extract_to))
        if self.page.preferences.advanced_mode:
            task += loc("\nWhilst keeping track of changes in a versioned folder in {Value}".format(self.locations.changes_to))
        await self.page.dialog.set_data(
            modal=False,
            title=Text(loc("Extraction confirmation")),
            content=Text(task),
            actions=[
                ElevatedButton(loc("Cancel"), on_click=self.page.RTT.close_dialog),
                ElevatedButton(
                    loc("Confirm extraction"), data=extraction_type, on_click=self.extract
                ),
            ],
            actions_alignment=MainAxisAlignment.END,
        )

    async def extract_changes(self, _):
        await self.warn_extraction("changes")

    async def extract_selected(self, _):
        await self.warn_extraction("selected")

    async def extract_all(self, _):
        await self.warn_extraction("all")

    async def extract(self, event):
        self.main_controls.disabled = True
        await self.page.dialog.hide()
        await asyncio.sleep(0.5)
        if event.control.data == "changes":
            self.cancel_extraction_button.visible = False
            if self.page.preferences.advanced_mode:
                dated_folder = self.locations.changes_to.joinpath(
                    datetime.now().strftime(
                        self.page.preferences.changes_name_format.replace(
                            "$dir", self.locations.extract_from.name
                        ).strip()
                    )
                )
                old_changes = dated_folder.joinpath("old")
                new_changes = dated_folder.joinpath("new")
                dated_folder.mkdir(parents=True, exist_ok=True)
                old_changes.mkdir(parents=True, exist_ok=True)
                new_changes.mkdir(parents=True, exist_ok=True)
                # This in case they want to re-run the extraction, possible
                with open(old_changes.joinpath("hashes.json"), "w+") as f:
                    f.write(json.dumps(self.hashes, indent=4))
            selected_indexes = [r.data for r in self.directory_list.rows if r.selected]
            changes = [
                f for f in self.changed_files if f.archive.index in selected_indexes
            ]
            selected_archives = [f.archive for f in changes]
            total = len(changes)
            start = perf_counter()
            for i, file in enumerate(changes, 1):
                old_pro = self.extraction_progress.controls[1].controls[0].value
                i += 1
                if old_pro != (progress := round(i / total * 1000) / 1000):
                    elapsed = perf_counter() - start
                    remaining = round(elapsed * (total / i - 1))
                    self.extraction_progress.controls[0].controls[
                        0
                    ].value = f"[{round(i / total * 100, 1)}%] | Elapsed: {round(elapsed):>3}s | Estimated {remaining:>3}s remaining | Extracting {event.control.data}:\r"
                    self.extraction_progress.controls[0].controls[1].value = file.name
                    self.extraction_progress.controls[1].controls[0].value = progress
                    await self.extraction_progress.update_async()
                if self.page.preferences.advanced_mode:
                    await file.copy_old(
                        self.locations.extract_from,
                        self.locations.changes_from,
                        old_changes,
                    )
                    await file.save(self.locations.extract_from, new_changes)
                await file.save(self.locations.extract_from, self.locations.extract_to)
                index_relative_path = file.archive.index.path.relative_to(
                    self.locations.extract_from
                )
                archive_relative_path = file.archive.path.relative_to(
                    self.locations.extract_from
                )
                self.hashes[str(index_relative_path)] = (
                    await file.archive.index.content_hash
                )
                self.hashes[str(archive_relative_path)] = (
                    await file.archive.content_hash
                )
            wrote = sum([f.size for f in changes])
            saved = (
                sum(
                    [
                        f["size"]
                        for r in self.directory_list.rows
                        for f in await r.data.files_list
                    ]
                )
                - wrote
            )
            metadata = {
                "Extracted From": str(self.locations.extract_from),
                "Extracted To": str(self.locations.extract_to),
                "Compared with": str(self.locations.changes_from),
                "Changes to": str(self.locations.changes_to),
                "Date": datetime.now().isoformat(),
                "Byte writes": wrote,
                "Bytes saved": saved,
                "Byte writes (Readable)": naturalsize(wrote, gnu=True),
                "Bytes saved (Readable)": naturalsize(saved, gnu=True),
                "Time elapsed (Seconds)": round(perf_counter() - start, 2),
                "Extraction": {
                    "Type": "Changes",
                    "Indexes": sorted(
                        list(
                            set(
                                [
                                    str(
                                        index.path.relative_to(
                                            self.locations.extract_from
                                        )
                                    )
                                    for index in selected_indexes
                                ]
                            )
                        )
                    ),
                    "Archives": (
                        list(
                            set(
                                [
                                    str(
                                        archive.path.relative_to(
                                            self.locations.extract_from
                                        )
                                    )
                                    for archive in selected_archives
                                ]
                            )
                        )
                    ),
                    "Files": (
                        list(
                            set(
                                [
                                    str(f.path.relative_to(self.locations.extract_from))
                                    for f in changes
                                ]
                            )
                        )
                    ),
                },
            }
            with open(new_changes.joinpath("metadata.yml"), "w+") as f:
                dump(metadata, f, sort_keys=False)
        elif event.control.data in ["all", "selected"]:
            self.cancel_extraction_button.visible = True
            await self.cancel_extraction_button.update_async()
            if event.control.data == "all":
                indexes = [r.data for r in self.directory_list.rows]
            elif event.control.data == "selected":
                indexes = [r.data for r in self.directory_list.rows if r.selected]
            number_of_files = sum([len(await index.files_list) for index in indexes])
            i = 0
            start = perf_counter()
            for index in indexes:
                index_relative_path = index.path.relative_to(
                    self.locations.extract_from
                )
                self.hashes[str(index_relative_path)] = await index.content_hash
                for archive in index.archives:
                    archive_relative_path = archive.path.relative_to(
                        self.locations.extract_from
                    )
                    self.hashes[str(archive_relative_path)] = await archive.content_hash
                    async for file in archive.files():
                        if self.cancel_extraction:
                            self.cancel_extraction = False
                            self.extraction_progress.controls[0].controls[
                                0
                            ].value = "Extractor Idle"
                            self.extraction_progress.controls[0].controls[1].value = ""
                            self.extraction_progress.controls[1].controls[0].value = 0
                            return await self.page.snack_bar.show(
                                loc("Extraction cancelled"), color="red"
                            )
                        old_pro = self.extraction_progress.controls[1].controls[0].value
                        i += 1
                        if old_pro != (
                            progress := round(i / number_of_files * 1000) / 1000
                        ):
                            elapsed = perf_counter() - start
                            remaining = round(elapsed * (number_of_files / i - 1))
                            self.extraction_progress.controls[0].controls[
                                0
                            ].value = f"[{round(i / number_of_files * 100, 1)}%] | Elapsed: {round(elapsed):>3}s | Estimated {remaining:>3}s remaining | Extracting {event.control.data}:\r"
                            self.extraction_progress.controls[0].controls[
                                1
                            ].value = file.name
                            self.extraction_progress.controls[1].controls[
                                0
                            ].value = progress
                            await self.extraction_progress.update_async()
                        await file.save(
                            self.locations.extract_from, self.locations.extract_to
                        )
        hashes_path = self.locations.extract_to.joinpath("hashes.json")
        hashes_path.write_text(json.dumps(self.hashes, indent=4))
        self.main_controls.disabled = False
        self.cancel_extraction_button.visible = False
        self.extraction_progress.controls[0].controls[0].value = "Extractor Idle"
        self.extraction_progress.controls[0].controls[1].value = ""
        self.extraction_progress.controls[1].controls[0].value = 0
        await self.page.snack_bar.show(loc("Extraction Complete"))
        self.refresh_lists.start()
