from flet import View, Column, ScrollMode
from flet_core.icons import TABLE_VIEW

from controllers import GemBuildsController


class GemBuildsView(View):
    route = "/gem_builds"
    title = "Gem Builds"
    icon = TABLE_VIEW
    has_tab = True

    def __init__(self, page):
        ctrl = GemBuildsController(page)
        super().__init__(
            route=self.route,
            controls=[
                Column(
                    controls=[ctrl.interface], expand=True, scroll=ScrollMode.ADAPTIVE
                )
            ],
        )
