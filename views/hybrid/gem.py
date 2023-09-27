from flet import View
from flet_core.icons import SCIENCE_SHARP

from controllers import GemController


class GemView(View):
    route = "/gem_simulator"
    title = "tabs.3"
    icon = SCIENCE_SHARP

    def __init__(self, page):
        ctrl = GemController(page=page)
        page.appbar.leading.controls[0].name = self.icon
        super().__init__(route=self.route, controls=[ctrl.header_row], scroll="auto")
