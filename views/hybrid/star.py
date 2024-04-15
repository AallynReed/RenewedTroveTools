from flet import View, Column, ScrollMode
from flet_core.icons import STARS_SHARP

from controllers import StarChartController


class StarView(View):
    route = "/star_chart"
    title = "Star Chart"
    icon = STARS_SHARP
    has_tab = True

    def __init__(self, page):
        ctrl = StarChartController(page=page)
        super().__init__(
            route=self.route,
            controls=[
                Column(controls=[ctrl.map], expand=True, scroll=ScrollMode.ADAPTIVE)
            ],
        )
