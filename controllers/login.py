from models.interface import Controller
from flet import (
    Divider,
    Card,
    Text,
    TextStyle,
    Column,
    Row,
    Chip,
    Icon,
    Image,
    TextField,
    Container,
)
from flet_core import padding, MainAxisAlignment


class LoginController(Controller):
    def setup_controls(self):
        self.token_input = TextField(
            data="input",
            label="Insert pass key here",
            text_align="center",
            password=True,
            can_reveal_password=True,
            helper_style=TextStyle(color="red"),
            on_change=self.execute_login,
            content_padding=10,
            autofocus=True,
        )
        self.main = Card(
            Container(
                Column(
                    controls=[
                        Text(value="Login", size=40, width=460, text_align="center"),
                        self.token_input,
                        Text("Get pass key from:", width=460, text_align="center"),
                        Row(
                            controls=[
                                Chip(
                                    leading=Icon("discord"),
                                    label=Text("Discord"),
                                    on_click=self.execute_login_discord,
                                ),
                                Chip(
                                    leading=Image(
                                        src="https://trovesaurus.com/images/logos/Sage_64.png?1",
                                        width=24,
                                    ),
                                    label=Text("Trovesaurus"),
                                    on_click=self.execute_login_trovesaurus,
                                ),
                            ],
                            width=400,
                            alignment=MainAxisAlignment.SPACE_EVENLY,
                        ),
                        Divider(),
                        Chip(
                            label=Text("Go back"),
                            on_click=self.cancel_login,
                            width=460,
                        ),
                    ],
                    horizontal_alignment="center",
                ),
                padding=padding.all(20),
            ),
            width=500,
        )

    def setup_events(self):
        pass

    async def execute_login(self, e):
        if self.token_input.value.strip():
            self.page.user_data = await self.page.RTT.login(
                self.token_input.value.strip()
            )
            if self.page.user_data is None:
                self.token_input.helper_text = "Invalid pass key"
                return await self.token_input.update_async()
            else:
                await self.page.RTT.setup_appbar()
                await self.page.go_async("/")
        else:
            return

    async def execute_login_discord(self, e):
        await self.page.launch_url_async(
            "https://kiwiapi.slynx.xyz/v1/user/discord/login"
        )

    async def execute_login_trovesaurus(self, e):
        await self.page.launch_url_async("https://trovesaurus.com/profile")

    async def cancel_login(self, e):
        await self.page.go_async("/")
