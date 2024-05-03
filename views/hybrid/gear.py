from flet import View, Column, ScrollMode
from flet_core.icons import SHIELD

from controllers import GearBuildsController


class GearBuildsView(View):
    route = "/gear_builds"
    title = "Gear Builds"
    icon = SHIELD
    has_tab = True

    def __init__(self, page):
        ctrl = GearBuildsController(page)
        super().__init__(
            route=self.route,
            controls=[
                Column(controls=[ctrl.main], expand=True, scroll=ScrollMode.ADAPTIVE)
            ],
        )
