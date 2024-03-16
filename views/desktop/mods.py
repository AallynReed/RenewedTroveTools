from flet import View
from flet_core.icons import EXTENSION

from controllers import ModsController


class ModsView(View):
    route = "/mods_manager"
    title = "Mods Manager"
    icon = EXTENSION
    has_tab = True

    def __init__(self, page):
        ctrl = ModsController(page=page)
        super().__init__(route=self.route, controls=[ctrl.main])
