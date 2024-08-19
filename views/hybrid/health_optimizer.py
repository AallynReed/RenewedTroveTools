from flet import View, Column, ScrollMode
from flet_core.icons import FAVORITE

from controllers import HealthOptimizerController


class HealthOptimizerView(View):
    route = "/health_optimizer"
    title = "Health Optimizer"
    icon = FAVORITE
    has_tab = True

    def __init__(self, page):
        ctrl = HealthOptimizerController(page)
        super().__init__(
            route=self.route,
            controls=[
                Column(
                    controls=[ctrl.interface], expand=True, scroll=ScrollMode.ADAPTIVE
                )
            ],
        )
