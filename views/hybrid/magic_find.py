from flet import View, Text
from flet_core.icons import MENU_BOOK_SHARP

from controllers import MagicFindController


class MagicFindView(View):
    route = "/magic_find"
    title = Text("Magic Find")
    icon = MENU_BOOK_SHARP

    def __init__(self, page):
        ctrl = MagicFindController(page=page)
        page.appbar.leading.controls[0].name = self.icon
        super().__init__(
            route=self.route,
            controls=[ctrl.interface],
        )
