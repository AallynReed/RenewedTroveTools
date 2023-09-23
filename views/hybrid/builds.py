from flet import View, Text, Column
from flet_core.icons import TABLE_VIEW

from controllers import GemBuildsController


class GemBuildsView(View):
    route = "/gem_builds"
    title = Text("Gem Builds")
    icon = TABLE_VIEW

    def __init__(self, page):
        ctrl = GemBuildsController(page)
        page.appbar.leading.controls[0].name = self.icon
        super().__init__(
            route=self.route,
            controls=[Column(controls=[ctrl.interface])],
        )
