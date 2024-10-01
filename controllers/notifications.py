import asyncio
import os

import flet_core.icons as icons
from flet import (
    Column,
    Row,
    Tabs,
    Tab,
    Icon,
    Text,
    Divider,
    Card,
    ResponsiveRow,
    Switch,
)

from models.interface import Controller
from models.interface.inputs import AutoNumberField
from utils.locale import loc


class NotificationsController(Controller):
    def setup_controls(self):
        if not hasattr(self, "main"):
            self.main = Column(expand=True)
            self.mod_submenus = Tabs()
            self.mod_submenus.on_change = self.tab_loader
            self.settings_tab = Tab(
                tab_content=Row(controls=[Icon(icons.SETTINGS, size=24)])
            )
            self.notifications_tab = Tab(
                tab_content=Row(
                    controls=[
                        Icon(icons.NOTIFICATIONS, size=24),
                        Text(loc("Notifications")),
                    ]
                )
            )
            self.settings = Column(expand=True)
            self.notifications = Column(expand=True)
            self.mod_submenus.tabs.append(self.settings_tab)
            # self.mod_submenus.tabs.append(self.notifications_tab)
            self.tabs = {
                0: self.settings,
                # 1: self.notifications,
            }
            self.tab_map = {
                0: self.load_settings,
                # 1: self.load_notifications,
            }
            self.mod_submenus.selected_index = 0  # 1
            asyncio.create_task(self.post_setup())

    def setup_events(self): ...

    async def post_setup(self):
        self.main.controls.append(
            Row(
                controls=[
                    self.mod_submenus,
                ]
            )
        )
        await self.release_ui()
        await self.tab_loader(boot=True)

    async def tab_loader(self, event=None, index=None, boot=False):
        if index is None:
            if event is not None:
                index = event.control.selected_index
            else:
                index = self.mod_submenus.selected_index
        self.main.controls.clear()
        self.main.controls.append(
            Row(
                controls=[
                    self.mod_submenus,
                ]
            )
        )
        self.main.controls.append(self.tabs[index])
        await self.tab_map[index](boot=boot or bool(event))

    async def reload_tab(self, event):
        await self.tab_loader(index=self.mod_submenus.selected_index)

    async def lock_ui(self):
        self.main.disabled = True
        await self.main.update_async()
        await asyncio.sleep(0.1)

    async def release_ui(self):
        self.main.disabled = False
        await self.main.update_async()

    # Settings Tab

    async def load_settings(self, boot=False):
        await self.lock_ui()
        self.settings.controls.clear()
        notification_settings = self.page.preferences.notifications
        self.settings.controls.append(
            ResponsiveRow(
                controls=[
                    Card(
                        content=Column(
                            controls=[
                                Text(loc("All Notifications"), size=18),
                                Row(
                                    controls=[
                                        Switch(
                                            data=notification_settings,
                                            value=notification_settings.enabled,
                                            on_change=self.switch_enabled,
                                        ),
                                        Text(loc("Enable notifications")),
                                    ]
                                ),
                                Row(
                                    controls=[
                                        Switch(
                                            data=notification_settings,
                                            value=notification_settings.sound,
                                            on_change=self.switch_sound,
                                        ),
                                        Text(loc("Play sound")),
                                    ]
                                ),
                                Row(
                                    controls=[
                                        AutoNumberField(
                                            data=notification_settings,
                                            value=int(notification_settings.duration),
                                            on_change=self.switch_duration,
                                            min=0,
                                            step=1,
                                            max=10,
                                            width=40,
                                            type=int,
                                        ),
                                        Text(loc("Notification duration")),
                                    ]
                                ),
                                Row(
                                    controls=[
                                        Switch(
                                            data=notification_settings,
                                            value=notification_settings.start_with_windows,
                                            on_change=self.switch_start_with_windows,
                                            disabled=os.name != "nt",
                                        ),
                                        Text(loc("Start with Windows")),
                                    ]
                                ),
                            ]
                        ),
                    ),
                    Divider(),
                    *(
                        [
                            Card(
                                content=Column(
                                    controls=[
                                        Text(loc(ns.name.value), size=18),
                                        Row(
                                            controls=[
                                                Switch(
                                                    data=ns,
                                                    value=ns.enabled,
                                                    on_change=self.switch_enabled,
                                                ),
                                                Text(loc("Show notifications")),
                                            ]
                                        ),
                                        Row(
                                            controls=[
                                                Switch(
                                                    data=ns,
                                                    value=ns.sound,
                                                    on_change=self.switch_sound,
                                                ),
                                                Text(loc("Play sound")),
                                            ]
                                        ),
                                    ]
                                ),
                                col=3,
                            )
                            for ns in notification_settings.notifications
                        ]
                    ),
                ]
            )
        )
        await self.release_ui()

    async def switch_enabled(self, event):
        ns = event.control.data
        ns.enabled = event.control.value
        self.page.preferences.save()
        await self.reload_tab(event)

    async def switch_sound(self, event):
        ns = event.control.data
        ns.sound = event.control.value
        self.page.preferences.save()
        await self.reload_tab(event)

    async def switch_duration(self, event):
        ns = event.control.data
        ns.duration = int(event.control.value)
        self.page.preferences.save()
        await self.reload_tab(event)

    async def switch_start_with_windows(self, event):
        ns = event.control.data
        ns.start_with_windows = event.control.value
        if ns.start_with_windows:
            await self.page.RTT.add_start_with_windows()
        else:
            await self.page.RTT.remove_start_with_windows()
        self.page.preferences.save()
        await self.reload_tab(event)

    async def load_notifications(self, boot=False):
        await self.lock_ui()
        self.notifications.controls.clear()
        ...
        await self.release_ui()
