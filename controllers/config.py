from flet import Column, Dropdown, dropdown, Text

from models.config import Locale
from models.interface import Controller


class ConfigController(Controller):
    def setup_controls(self):
        self.settings = Column(
            controls=[
                Column(
                    controls=[
                        Dropdown(
                            value=self.page.app_config.locale.value,
                            options=[
                                dropdown.Option(key=loc.value, text=loc.name.replace("_", " "))
                                for loc in Locale
                            ],
                            label="Language",
                            on_change=self.on_language_change,
                        ),
                    ]
                ),
                Column(
                    controls=[
                        Text("This application was developed by Sly#0511.\nIt's use is free and")
                    ]
                )
            ],
            expand=True,
            spacing=400
        )

    def setup_events(self):
        ...

    async def on_language_change(self, event):
        lang = Locale(event.control.value)
        self.page.app_config.locale = lang
        for control in self.page.controls:
            control.disabled = True
        await self.page.update_async()
        await self.page.restart()
