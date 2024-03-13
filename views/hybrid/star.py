from flet import View, Column, ScrollMode
from flet_core.icons import STARS_SHARP

from controllers import StarChartController


class StarView(View):
    route = "/star_chart"
    title = "Star Chart"
    icon = STARS_SHARP

    def __init__(self, page):
        ctrl = StarChartController(page=page)
        page.appbar.leading.controls[0].name = self.icon
        super().__init__(
            self.route,
            controls=[
                Column(
                    controls=[ctrl.map],
                    expand=True,
                    scroll=ScrollMode.ADAPTIVE
                )
            ],
        )
