from flet import View, Column, ScrollMode
from flet_core.icons import SCIENCE_SHARP

from controllers import GemController


class GemView(View):
    route = "/gem_simulator"
    title = "tabs.3"
    icon = SCIENCE_SHARP
    has_tab = True

    def __init__(self, page):
        ctrl = GemController(page=page)
        super().__init__(
            route=self.route,
            controls=[
                Column(
                    controls=[
                        ctrl.header_row,
                    ],
                    expand=True,
                    scroll=ScrollMode.ADAPTIVE
                )
            ],
        )
