from flet import View, Icon, Text
from flet_core.icons import STARS_SHARP

from controllers import StarChartController


class StarView(View):
    route = "/star_chart"
    title = Text("Star Chart")
    icon = STARS_SHARP

    def __init__(self, page):
        ctrl = StarChartController(page=page)
        page.appbar.leading.controls[0].name = self.icon
        super().__init__(self.route, controls=[ctrl.map], spacing=0, padding=0)
