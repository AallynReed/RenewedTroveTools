from flet import View
from flet_core.icons import UNARCHIVE

from controllers import ExtractorController


class ExtractorView(View):
    route = "/file_extractor"
    title = "File Extractor"
    icon = UNARCHIVE
    has_tab = True

    def __init__(self, page):
        ctrl = ExtractorController(page=page)
        super().__init__(
            route=self.route,
            controls=[ctrl.main],
            scroll="auto",
        )
