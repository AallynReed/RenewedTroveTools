import re
from typing import Type
from urllib.parse import urlparse

from flet import (
    Page,
    View,
    Row,
    Column,
    VerticalDivider,
    NavigationRail,
    NavigationRailLabelType,
    NavigationRailDestination,
)
from i18n import t

from utils.functions import get_attr


class Routing:
    def __init__(
        self,
        page: Page,
        views: list[Type[View]],
        not_found: Type[View] = None,
    ):
        self.page = page
        self.views = views
        self.not_found = not_found
        self.page.on_route_change = self.handle_route_change_async

    async def handle_route_change_async(self, event):
        view = self.get_view(event)
        await self.change_view_async(view)

    def get_view(self, event):
        url = urlparse("https://trovetools.slynx.xyz" + event.route, scheme="https")
        params = {
            k: v
            for kv in url.query.split("&")
            for k, v in re.findall(r"^(.*?)=(.*?)$", kv)
        }
        self.page.params = params
        view = get_attr(self.views, route=url.path)
        if view is None:
            view = self.not_found
        return view(self.page)

    async def change_view_async(self, view: Type[View]):
        self.page.controls = [
            Row(
                controls=[
                    NavigationRail(
                        selected_index=self.views.index(view.__class__),
                        label_type=NavigationRailLabelType.ALL,
                        extended=False,
                        min_width=100,
                        min_extended_width=200,
                        destinations=[
                            NavigationRailDestination(
                                icon=view.icon, label=t(view.title)
                            )
                            for view in self.views
                        ],
                        on_change=self.change_navigation,
                    ),
                    VerticalDivider(),
                    Column(controls=view.controls, expand=True, scroll=None),
                ],
                expand=True,
            )
        ]
        await self.page.update_async()

    async def change_navigation(self, event):
        route = self.views[event.control.selected_index].route
        await self.page.go_async(route)
