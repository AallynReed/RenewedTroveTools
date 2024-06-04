from flet import View, Column, ScrollMode
from flet_core.icons import BAR_CHART

from controllers import MaxStatsController


class MaxStatsView(View):
    route = "/max_stats"
    title = "Max Stats"
    icon = BAR_CHART
    has_tab = True

    def __init__(self, page):
        ctrl = MaxStatsController(page)
        super().__init__(
            route=self.route,
            controls=[
                Column(
                    controls=[ctrl.interface], expand=True, scroll=ScrollMode.ADAPTIVE
                )
            ],
        )
