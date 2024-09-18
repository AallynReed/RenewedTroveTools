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
from utils.locale import loc

from utils.functions import get_attr


class Routing:
    def __init__(
        self,
        page: Page,
        views: list[Type[View]],
    ):
        self.page = page
        self.views = views
        self.page.on_route_change = self.handle_route_change_async
        self.cached_routes = {}

    async def handle_route_change_async(self, event):
        if event is None:
            return
        routes = [v.route for v in self.views]
        if self.page.route.split("?")[0] not in routes:
            await self.page.go_async("/404")
            return
        self.current_views = [
            v for v in self.views if v.route == self.page.route or v.has_tab
        ]
        view = self.get_view(event)
        await self.change_view_async(view)

    def get_view(self, event):
        url = urlparse("https://trovetools.aallyn.xyz" + event.route, scheme="https")
        self.page.params = {
            k: v
            for kv in url.query.split("&")
            for k, v in re.findall(r"^(.*?)=(.*?)$", kv)
        }
        view = get_attr(self.current_views, route=url.path)
        cached_view = self.cached_routes.get(view, None)
        if cached_view is None:
            cached_view = view(self.page)
            if not self.page.web:
                self.cached_routes[view] = cached_view
        self.page.appbar.leading.controls[0].name = view.icon
        return cached_view

    async def change_view_async(self, view: Type[View]):
        self.page.controls = [
            Row(
                controls=[
                    NavigationRail(
                        selected_index=self.current_views.index(view.__class__),
                        label_type=NavigationRailLabelType.ALL,
                        extended=False,
                        min_width=100,
                        min_extended_width=200,
                        destinations=[
                            NavigationRailDestination(icon=v.icon, label=loc(v.title))
                            for v in self.current_views
                        ],
                        on_change=self.change_navigation,
                    ),
                    VerticalDivider(),
                    Column(controls=view.controls, expand=True),
                ],
                expand=True,
            )
        ]
        await self.page.update_async()

    async def change_navigation(self, event):
        route = self.current_views[event.control.selected_index].route
        await self.page.go_async(route)
