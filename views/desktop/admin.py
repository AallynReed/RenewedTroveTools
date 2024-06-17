from flet import View
from flet_core.icons import ADMIN_PANEL_SETTINGS

from controllers import AdminController


class AdminView(View):
    route = "/admin"
    title = "Admin Panel"
    icon = ADMIN_PANEL_SETTINGS
    has_tab = False

    def __init__(self, page):
        ctrl = AdminController(page=page)
        super().__init__(
            route=self.route,
            controls=[ctrl.main],
            scroll="auto",
        )
