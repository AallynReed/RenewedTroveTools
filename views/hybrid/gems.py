from flet import View, Column, ScrollMode
from flet_core.icons import DIAMOND_SHARP

from controllers import GemSetController


class GemSetView(View):
    route = "/gem_calculator"
    title = "Gem Set Calculator"
    icon = DIAMOND_SHARP
    has_tab = True

    def __init__(self, page):
        ctrl = GemSetController(page=page)
        super().__init__(
            route=self.route,
            controls=[
                Column(
                    controls=[ctrl.gem_report, ctrl.general_controls, ctrl.gem_altar],
                    expand=True,
                    scroll=ScrollMode.ADAPTIVE,
                )
            ],
        )
