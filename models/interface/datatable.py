from typing import Optional, Callable

from flet import (
    UserControl,
    DataTable,
    DataColumn,
    DataRow,
    Column,
    Row,
    IconButton,
    TextField,
    Text,
)
from flet_core import icons


class PagedDataTable(UserControl):
    def __init__(
        self,
        is_async: bool,
        columns: list[DataColumn],
        page_size: int = 10,
        single_select: bool = False,
        on_selection_changed: Optional[Callable] = None,
        **kwargs,
    ):
        self.is_async = is_async
        self._page_size = page_size
        self._columns = columns
        self._rows = []
        self.single_select = single_select
        self._page = 0
        self._on_selection_changed = on_selection_changed
        super().__init__(**kwargs)

    def build(self):
        self.table = DataTable(
            columns=self._columns,
        )
        self._text_indicator = TextField(
            value=str(self.current_page + 1),
            width=100,
            scale=0.75,
            on_submit=(self.to_page if not self.is_async else self.to_page_async),
        )
        self.put_page(self.current_page)
        return Column(
            controls=[
                self.table,
                Row(
                    controls=[
                        IconButton(
                            icons.FIRST_PAGE,
                            on_click=(
                                self.to_first_page
                                if not self.is_async
                                else self.to_first_page_async
                            ),
                        ),
                        IconButton(
                            icons.NAVIGATE_BEFORE,
                            on_click=(
                                self.to_previous_page
                                if not self.is_async
                                else self.to_previous_page_async
                            ),
                        ),
                        self._text_indicator,
                        Text(
                            f"/ {self.page_count}",
                            scale=0.75,
                        ),
                        IconButton(
                            icons.NAVIGATE_NEXT,
                            on_click=(
                                self.to_next_page
                                if not self.is_async
                                else self.to_next_page_async
                            ),
                        ),
                        IconButton(
                            icons.LAST_PAGE,
                            on_click=(
                                self.to_last_page
                                if not self.is_async
                                else self.to_last_page_async
                            ),
                        ),
                    ],
                    alignment="SPACE_BETWEEN",
                ),
            ],
            expand=True,
        )

    def _update_indicator(self):
        self._text_indicator.value = str(self._page + 1)

    def update(self):
        self._update_indicator()
        super().update()

    async def update_async(self):
        self._update_indicator()
        await super().update_async()

    def set_table_arguments(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self.table, key, value)

    @property
    def page_size(self):
        return self._page_size

    @page_size.setter
    def page_size(self, value: int):
        self._page_size = value

    @property
    def page_count(self):
        return len(self._rows) // self.page_size

    @property
    def current_page(self):
        return self._page

    @current_page.setter
    def current_page(self, value: int):
        self._page = value if value < self.page_count else self.last_page

    def to_page(self, e):
        page = int(e.control.value) - 1
        if 0 <= page < self.page_count:
            self.current_page = page
            self.put_page(self.current_page)
            self.update()
        else:
            self.current_page = self.last_page
            self.put_page(self.current_page)
            self.update()

    async def to_page_async(self, e):
        page = int(e.control.value) - 1
        if 0 <= page < self.page_count:
            self.current_page = page
            self.put_page(self.current_page)
            await self.update_async()
        else:
            self.current_page = self.last_page
            self.put_page(self.current_page)
            await self.update_async()

    @property
    def previous_page(self):
        return (self.page - 1) % self.page_count

    @property
    def next_page(self):
        return (self.page + 1) % self.page_count

    @property
    def first_page(self):
        return 0

    @property
    def last_page(self):
        return self.page_count - 1

    def get_page(self, page: int):
        return self._rows[
            page * self.page_size : page * self.page_size + self.page_size
        ]

    def put_page(self, page: int):
        self.table.rows = self.get_page(page)

    def to_first_page(self, e):
        self.current_page = 0
        self.put_page(self.current_page)
        self.update()

    def to_last_page(self, e):
        self.current_page = self.page_count - 1
        self.put_page(self.current_page)
        self.update()

    def to_previous_page(self, e):
        self.current_page = (self.current_page - 1) % self.page_count
        self.put_page(self.current_page)
        self.update()

    def to_next_page(self, e):
        self.current_page = (self.current_page + 1) % self.page_count
        self.put_page(self.current_page)
        self.update()

    async def to_first_page_async(self, e):
        self.current_page = 0
        self.put_page(self.current_page)
        await self.update_async()

    async def to_last_page_async(self, e):
        self.current_page = self.page_count - 1
        self.put_page(self.current_page)
        await self.update_async()

    async def to_previous_page_async(self, e):
        self.current_page = (self.current_page - 1) % self.page_count
        self.put_page(self.current_page)
        await self.update_async()

    async def to_next_page_async(self, e):
        self.current_page = (self.current_page + 1) % self.page_count
        self.put_page(self.current_page)
        await self.update_async()

    def add_row(self, row: DataRow):
        row.on_select_changed = self.on_row_select_changed
        self._rows.append(row)

    async def add_row_async(self, row: DataRow):
        row.on_select_changed = self.on_row_select_changed_async
        self._rows.append(row)

    def remove_row(self, row: DataRow):
        self._rows.remove(row)

    def clear_rows(self):
        self._rows.clear()

    @property
    def on_selection_changed(self):
        return self._on_selection_changed

    @on_selection_changed.setter
    def on_selection_changed(self, value):
        self._on_selection_changed = value

    def on_row_select_changed(self, e):
        e.control.selected = True
        if self.single_select:
            for row in self._rows:
                if row != e.control:
                    row.selected = False
        self.update()
        if self.on_selection_changed:
            self.on_selection_changed(e)

    async def on_row_select_changed_async(self, e):
        e.control.selected = True
        if self.single_select:
            for row in self._rows:
                if row != e.control:
                    row.selected = False
        await self.update_async()
        if self.on_selection_changed:
            await self.on_selection_changed(e)

    @property
    def selected_row(self) -> Optional[DataRow]:
        if self.single_select:
            for row in self._rows:
                if row.selected:
                    return row
            return None
        else:
            raise Exception("Cannot get selected row from a multi-select table")

    @property
    def selected_rows(self) -> list[DataRow]:
        if self.single_select:
            raise Exception("Cannot get selected rows from a single-select table")
        else:
            return [row for row in self._rows if row.selected]
