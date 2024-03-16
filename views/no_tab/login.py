from flet import View, Column, Row
from flet_core.icons import TABLE_VIEW

from controllers import LoginController


class LoginView(View):
    route = "/login"
    title = "Login"
    icon = TABLE_VIEW

    def __init__(self, page):
        ctrl = LoginController(page)
        page.appbar.leading.controls[0].name = self.icon
        super().__init__(
            route=self.route,
            controls=[
                Column(
                    controls=[
                        Row(
                            controls=[
                                ctrl.main
                            ],
                            alignment="center",
                        )
                    ],
                    alignment="center",
                    expand=True,
                )
            ],
        )