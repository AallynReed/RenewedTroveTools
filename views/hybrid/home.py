from flet import View
from flet_core.icons import HOME_SHARP

from controllers import HomeController


class HomeView(View):
    route = "/"
    title = "Home"
    icon = HOME_SHARP

    def __init__(self, page):
        ctrl = HomeController(page)
        page.appbar.leading.controls[0].name = self.icon
        super().__init__(
            route=self.route,
            controls=[ctrl.widgets],
        )
