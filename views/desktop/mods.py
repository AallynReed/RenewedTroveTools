from flet import View
from flet_core.icons import DIAMOND_SHARP

from controllers import ModsController


class ModsView(View):
    route = "/mods_manager"
    title = "Mods Manager"
    icon = DIAMOND_SHARP

    def __init__(self, page):
        ctrl = ModsController(page=page)
        page.appbar.leading.controls[0].name = self.icon
        super().__init__(
            route=self.route,
            controls=[ctrl.main],
            scroll="auto",
        )
