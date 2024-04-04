import asyncio

from flet import (
    UserControl,
    Column,
    Row,
    ExpansionTile,
    ListTile,
    Text,
    TextField,
    Icon,
    IconButton,
    icons,
    ProgressRing,
    ScrollMode
)

from utils.trove.extractor import find_all_files
from aiohttp import ClientSession
from urllib.parse import quote_plus


class PathViewer(UserControl):
    def __init__(self, installation_path, project_path):
        super().__init__(expand=True)
        self.installation_path = installation_path
        self.project_path = project_path
        self.query = None
        self.search_bar = TextField(
            label="Search",
            hint_text="Search for files in archives (Minimum characters: 5)",
            on_submit=self.search
        )
        self.directories = {}

    def get_folder_tile(self, name, index):
        return ExpansionTile(
            data=index,
            title=Row(
                controls=[
                    Icon(icons.FOLDER),
                    Text(name),
                ],
                expand=True
            ),
            controls=[
                *(
                    [
                        self.get_folder_tile(directory, data)
                        for directory, data in index.items()
                        if directory not in ["index", "files"]
                    ]
                ),
                *(
                    [
                        self.get_file_tile(index["files"])
                    ]
                    if index["files"]
                    else []
                )
            ]
        )

    def get_file_tile(self, files):
        tile = ExpansionTile(
            leading=Icon(icons.FILE_COPY),
            title=Text("Files"),
        )
        for file in files:
            icon = icons.DOWNLOAD
            icon_color = None
            relative_path = file.path.relative_to(self.installation_path)
            project_path = self.project_path.joinpath(relative_path)
            if project_path.exists():
                icon = icons.CHECK
                icon_color = "green"
            tile.controls.append(
                ListTile(
                    leading=Icon(icons.FILE_COPY),
                    title=Text(file.name),
                    trailing=IconButton(
                        icon,
                        icon_color=icon_color,
                        data=file,
                        on_click=self.extract_file
                    )
                )
            )
        return tile

    async def get_viewer(self):
        viewer = Column(scroll=ScrollMode.ADAPTIVE, expand=True)
        if self.query is not None:
            viewer.controls.clear()
            await self._load_files()
            for directory, data in self.directories.items():
                viewer.controls.append(
                    self.get_folder_tile(directory, data)
                )
        return Column(
            controls=[
                self.search_bar,
                viewer
            ],
            width=800,
            expand=True
        )

    async def _load_files(self):
        self.directories = {}
        files = find_all_files(self.installation_path, {})
        file_names = None
        if "_" not in self.query:
            file_names = []
            async with ClientSession() as session:
                query = quote_plus(self.query)
                async with session.get(
                        f"https://trovesaurus.com/search/collections?q={query}.json&full&parts"
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("error") is None:
                            collections = data.get("collections")
                            results = collections.get("results")
                            for _, result in results.items():
                                for part in result.get("parts"):
                                    file_names.append(part.lower() + ".blueprint")
                                for vfx in result.get("vfx"):
                                    file_names.append(vfx)
        async for file in files:
            if not self.query:
                break
            if file.path.name not in file_names:
                if self.query.lower() not in file.path.name.lower():
                    continue
            index = file.index
            cursor = self.directories
            path_parts = index.path.parent.relative_to(self.installation_path).as_posix().split("/")
            for path_part in path_parts:
                if path_part not in cursor:
                    cursor[path_part] = {
                        "index": index,
                        "files": []
                    }
                cursor = cursor[path_part]
            cursor["files"].append(file)

    def build(self, control=None):
        if not control:
            asyncio.create_task(self.reload_path())
            return Column(
                controls=[
                    ProgressRing(),
                    Text("Loading Virtual Directory...")
                ]
            )
        return control

    async def reload_path(self):
        await self.display()

    async def search(self, event):
        event.control.border_color = None
        self.query = event.control.value or None
        if self.query and len(self.query) < 5:
            self.query = None
        if self.query is None:
            event.control.border_color = "red"
        await self.display()

    async def display(self):
        self.search_bar.disabled = True
        self.controls = [
            Column(
                controls=[
                    self.search_bar,
                    ProgressRing(),
                    Text("Loading Virtual Directory...please wait a second.")
                ]
            )
        ]
        await self.update_async()
        self.search_bar.disabled = False
        self.controls = [await self.get_viewer()]
        await self.update_async()

    async def extract_file(self, event):
        file = event.control.data
        relative_path = file.path.relative_to(self.installation_path)
        project_path = self.project_path.joinpath(relative_path)
        project_path.parent.mkdir(parents=True, exist_ok=True)
        project_path.write_bytes(await file.content)
        event.control.disabled = True
        event.control.icon = icons.CHECK
        event.control.icon_color = "green"
        await event.control.update_async()


class IntField(UserControl):
    def __init__(self, min_value=None, max_value=None, on_change=None, on_submit=None, **kwargs):
        super().__init__()
        self._on_change = None
        self._on_submit = None
        self.text_field = TextField(**kwargs)
        self.on_change = on_change
        self.on_submit = on_submit
        self.min_value = min_value
        self.max_value = max_value

    def build(self):
        return self.text_field

    @property
    def on_change(self):
        return self._on_change

    @on_change.setter
    def on_change(self, value):
        if value is None:
            self.text_field.on_change = None
            return

        async def on_change(event):
            if event.control.value == "" or event.control.value is None:
                event.control.border_color = None
                event.control.helper_text = None
                await event.control.update_async()
                return
            try:
                await self.validate(event.control.value)
            except ValueError as e:
                event.control.border_color = "red"
                event.control.helper_text = str(e)
                await event.control.update_async()
                return
            event.control.border_color = "green"
            event.control.helper_text = None
            await event.control.update_async()
            await value(event)

        self._on_change = on_change
        self.text_field.on_change = self._on_change

    @property
    def on_submit(self):
        return self._on_submit

    @on_submit.setter
    def on_submit(self, value):
        if value is None:
            self.text_field.on_submit = None
            return

        async def on_submit(event):
            if event.control.value == "" or event.control.value is None:
                event.control.border_color = None
                event.control.helper_text = None
                await event.control.update_async()
                return
            try:
                await self.validate(event.control.value)
            except ValueError as e:
                event.control.border_color = "red"
                event.control.helper_text = str(e)
                await event.control.update_async()
                return
            event.control.border_color = "green"
            event.control.helper_text = None
            await event.control.update_async()
            await value(event)

        self._on_submit = on_submit
        self.text_field.on_submit = self._on_submit

    async def validate(self, value):
        try:
            value = int(value)
        except ValueError:
            raise ValueError("Please enter a valid integer value")
        if self.min_value is not None and value < self.min_value:
            raise ValueError(f"Value is less than min value: {self.min_value}")
        if self.max_value is not None and value > self.max_value:
            raise ValueError(f"Value is greater than max value: {self.max_value}")
        return value


class RegexField(UserControl):
    def __init__(self, pattern, on_change=None, on_submit=None, **kwargs):
        super().__init__()
        self._on_change = None
        self._on_submit = None
        self.text_field = TextField(**kwargs)
        self.on_change = on_change
        self.on_submit = on_submit
        self.pattern = pattern

    def build(self):
        return self.text_field

    @property
    def on_change(self):
        return self._on_change

    @on_change.setter
    def on_change(self, value):
        if value is None:
            self.text_field.on_change = None
            return

        async def on_change(event):
            if event.control.value == "" or event.control.value is None:
                event.control.border_color = None
                event.control.helper_text = None
                await event.control.update_async()
                return
            try:
                await self.validate(event.control.value)
            except ValueError as e:
                event.control.border_color = "red"
                event.control.helper_text = str(e)
                await event.control.update_async()
                return
            event.control.border_color = "green"
            event.control.helper_text = None
            await event.control.update_async()
            await value(event)

        self._on_change = on_change
        self.text_field.on_change = self._on_change

    @property
    def on_submit(self):
        return self._on_submit

    @on_submit.setter
    def on_submit(self, value):
        if value is None:
            self.text_field.on_submit = None
            return

        async def on_submit(event):
            if event.control.value == "" or event.control.value is None:
                event.control.border_color = None
                event.control.helper_text = None
                await event.control.update_async()
                return
            try:
                await self.validate(event.control.value)
            except ValueError as e:
                event.control.border_color = "red"
                event.control.helper_text = str(e)
                await event.control.update_async()
                return
            event.control.border_color = "green"
            event.control.helper_text = None
            await event.control.update_async()
            await value(event)

        self._on_submit = on_submit
        self.text_field.on_submit = self._on_submit

    async def validate(self, value, error_message="Please enter a valid value"):
        if not self.pattern.match(value):
            raise ValueError(error_message)
        return value

    @property
    def value(self):
        if self.text_field.value is None:
            return None
        return self.pattern.match(self.text_field.value).group(0)