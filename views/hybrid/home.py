from flet import View
from flet_core.icons import HOME_SHARP

from controllers import HomeController


class HomeView(View):
    route = "/"
    title = "Home"
    icon = HOME_SHARP
    has_tab = True

    def __init__(self, page):
        ctrl = HomeController(page)
        super().__init__(
            route=self.route,
            controls=[ctrl.widgets],
        )
