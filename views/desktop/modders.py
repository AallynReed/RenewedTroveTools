from flet import View
from flet_core.icons import CONSTRUCTION

from controllers import ModdersController


class ModdersView(View):
    route = "/modders"
    title = "Modder Tools (WIP)"
    icon = CONSTRUCTION
    has_tab = True

    def __init__(self, page):
        ctrl = ModdersController(page=page)
        super().__init__(route=self.route, controls=[ctrl.main])
