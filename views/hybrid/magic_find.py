from flet import View
from flet_core.icons import MENU_BOOK_SHARP

from controllers import MagicFindController


class MagicFindView(View):
    route = "/magic_find"
    title = "Magic Find"
    icon = MENU_BOOK_SHARP
    has_tab = True

    def __init__(self, page):
        ctrl = MagicFindController(page=page)
        super().__init__(
            route=self.route,
            controls=[ctrl.interface],
        )
