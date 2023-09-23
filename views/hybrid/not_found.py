from flet import View, Column, Text
from flet_core.icons import QUESTION_MARK


class View404(View):
    route = "/404"
    title = Text("404 - Not Found")
    icon = QUESTION_MARK

    def __init__(self, page):
        page.appbar.leading.controls[0].name = self.icon
        super().__init__(
            route=self.route,
            controls=[
                Column(
                    controls=[
                        Text("404 - Page not found", size=50),
                        Text("Looks like you are lost", size=50),
                    ]
                ),
            ],
        )
