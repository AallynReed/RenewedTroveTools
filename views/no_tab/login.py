from flet import View, Column, Row
from flet_core.icons import LOGIN

from controllers import LoginController


class LoginView(View):
    route = "/login"
    title = "Login"
    icon = LOGIN
    has_tab = False

    def __init__(self, page):
        ctrl = LoginController(page)
        super().__init__(
            route=self.route,
            controls=[
                Column(
                    controls=[
                        Row(
                            controls=[ctrl.main],
                            alignment="center",
                        )
                    ],
                    alignment="center",
                    expand=True,
                )
            ],
        )
