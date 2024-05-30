import asyncio
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from aiohttp import ClientSession
from flet import (
    AppBar,
    IconButton,
    PopupMenuButton,
    PopupMenuItem,
    Divider,
    Column,
    Row,
    Text,
    Container,
    TextButton,
    MainAxisAlignment,
    Icon,
    Theme,
    ButtonStyle,
    TextField,
)
from flet_core.colors import SURFACE_VARIANT
from flet_core.icons import (
    LIGHT_MODE,
    DARK_MODE,
    LANGUAGE,
    BUG_REPORT,
    HELP,
    DOWNLOAD,
    PALETTE,
    SAVINGS,
    PERSON,
    FEEDBACK,
    PEST_CONTROL,
    HISTORY_EDU,
    DESKTOP_WINDOWS,
)

from models.preferences import AccentColor
from models.interface.image import RTTImage
from utils.functions import check_update
from utils.tasks import loop
from utils.locale import ENGINE, loc, Locale


async def check_update(current_version, debug=False, force=False):
    async with ClientSession() as session:
        async with session.get(
            "https://api.github.com/repos/Sly0511/RenewedTroveTools/releases"
        ) as response:
            version_data = await response.json()
            try:
                version = version_data[0]
            except IndexError:
                return None
            if current_version != version.get("name") or force:
                if os.name == "nt":
                    for asset in version.get("assets"):
                        if "debug" not in asset.get("name") and not debug:
                            return asset.get("browser_download_url"), os.name == "nt"
                        elif "debug" in asset.get("name") and debug:
                            return asset.get("browser_download_url"), os.name == "nt"
                else:
                    return version.get("html_url"), os.name == "nt"
    return None, os.name == "nt"


class CustomAppBar(AppBar):
    def __init__(self, page, **kwargs):
        self.page = page
        self.update_notified = False
        actions = self.build_actions(kwargs)
        super().__init__(
            bgcolor=SURFACE_VARIANT, actions=actions, center_title=True, **kwargs
        )
        self.i = 0
        if not page.web:
            self.check_updates.start()

    @loop(seconds=120)
    async def check_updates(self):
        await self.check_for_update()

    def build_actions(self, kwargs):
        actions = []
        actions.extend(
            [
                *(
                    [
                        IconButton(
                            icon=DESKTOP_WINDOWS,
                            url="https://kiwiapi.slynx.xyz/v1/misc/latest_release/download/redirect",
                            tooltip=loc("Get Windows Application"),
                        )
                    ]
                    if self.page.web
                    else []
                ),
                IconButton(
                    icon=DOWNLOAD,
                    on_click=self.go_to_update_page,
                    visible=False,
                    tooltip=loc("A newer version is available."),
                ),
                IconButton(
                    icon=HISTORY_EDU,
                    on_click=self.display_changelog,
                    tooltip=loc("Change Log"),
                ),
                IconButton(
                    icon=FEEDBACK,
                    on_click=self.feedback_modal,
                    tooltip=loc("Send feedback"),
                ),
                IconButton(
                    data="theme_switcher",
                    icon=DARK_MODE if self.page.dark_theme else LIGHT_MODE,
                    on_click=self.change_theme,
                    tooltip=loc("Change theme"),
                ),
                PopupMenuButton(
                    icon=PALETTE,
                    items=[
                        PopupMenuItem(
                            data=color,
                            content=Row(
                                controls=[
                                    Icon(PALETTE, color=color.value),
                                    Text(
                                        value=" ".join(
                                            [
                                                loc(w.capitalize())
                                                for w in color.value.split("_")
                                            ]
                                        )
                                    ),
                                ]
                            ),
                            on_click=self.change_color,
                        )
                        for color in AccentColor
                    ],
                ),
                PopupMenuButton(
                    content=Container(
                        Row(
                            controls=[
                                Icon(LANGUAGE),
                                Text(loc(self.page.preferences.locale.value)),
                            ]
                        )
                    ),
                    items=[
                        PopupMenuItem(
                            data=loc,
                            text=loc.value,
                            on_click=self.change_locale,
                        )
                        for loc in Locale
                        if loc in ENGINE.available_translations
                    ],
                    tooltip=loc("Change language"),
                ),
                PopupMenuButton(
                    data="donate-buttons",
                    icon=SAVINGS,
                    tooltip=loc("Donate"),
                    items=[
                        PopupMenuItem(
                            data="paypal",
                            content=Row(
                                controls=[
                                    RTTImage(
                                        src="assets/icons/brands/paypal-mark.png",
                                        width=19,
                                    ),
                                    Text("Paypal"),
                                ]
                            ),
                            on_click=self.go_url,
                        ),
                        PopupMenuItem(
                            data="buy_me_a_coffee",
                            content=Row(
                                controls=[
                                    RTTImage(
                                        src="assets/icons/brands/bmc.png", width=12
                                    ),
                                    Text("Buy me a Coffee"),
                                ]
                            ),
                            on_click=self.go_url,
                        ),
                        PopupMenuItem(
                            data="kofi",
                            content=Row(
                                controls=[
                                    RTTImage(
                                        src="assets/icons/brands/kofi-mark.png",
                                        width=24,
                                    ),
                                    Text("Kofi"),
                                ]
                            ),
                            on_click=self.go_url,
                        ),
                    ],
                ),
                *(
                    [
                        PopupMenuButton(
                            data="user-buttons",
                            content=Row(
                                controls=(
                                    [
                                        RTTImage(
                                            src=self.page.user_data["avatar_url"],
                                            error_content=Icon(PERSON),
                                            width=40,
                                            border_radius=50,
                                        ),
                                        Text(self.page.user_data["username"]),
                                    ]
                                    if self.page.user_data is not None
                                    else [
                                        TextButton(
                                            icon=PERSON,
                                            text=loc("Login"),
                                            style=ButtonStyle(color="secondary"),
                                            on_click=self.page.RTT.display_login_screen,
                                        )
                                    ]
                                )
                            ),
                            items=(
                                [
                                    PopupMenuItem(
                                        data="logout",
                                        text=loc("Logout"),
                                        on_click=self.page.RTT.execute_logout,
                                    )
                                ]
                                if self.page.user_data is not None
                                else []
                            ),
                        )
                    ]
                    if not self.page.web
                    else []
                ),
                PopupMenuButton(
                    data="other-buttons",
                    items=[
                        PopupMenuItem(
                            data="discord",
                            content=Row(
                                controls=[
                                    RTTImage(
                                        src=(
                                            "assets/icons/brands/discord-mark-black.png"
                                            if not self.page.dark_theme
                                            else "assets/icons/brands/discord-mark-white.png"
                                        ),
                                        width=19,
                                    ),
                                    Text("Discord"),
                                ]
                            ),
                            on_click=self.go_url,
                        ),
                        PopupMenuItem(
                            data="github",
                            content=Row(
                                controls=[
                                    RTTImage(
                                        (
                                            "assets/icons/brands/github-mark-black.png"
                                            if not self.page.dark_theme
                                            else "assets/icons/brands/github-mark-white.png"
                                        ),
                                        width=19,
                                    ),
                                    Text("Github"),
                                ]
                            ),
                            on_click=self.go_url,
                        ),
                        Divider(),
                        PopupMenuItem(
                            icon=BUG_REPORT,
                            data="discord",
                            text=loc("Report a bug"),
                            on_click=self.go_url,
                        ),
                        *(
                            [
                                PopupMenuItem(
                                    icon=PEST_CONTROL,
                                    text=(
                                        loc(
                                            "Switch to debug version"
                                            if not self.page.metadata.dev
                                            else "Switch to release version"
                                        )
                                    ),
                                    on_click=self.switch_debug,
                                )
                            ]
                            if not self.page.web
                            else []
                        ),
                        PopupMenuItem(
                            icon=HELP, text=loc("About"), on_click=self.open_about
                        ),
                    ],
                    tooltip=loc("Others"),
                ),
            ]
        )
        actions.extend(kwargs.get("actions", []))
        return actions

    async def change_theme(self, _):
        self.page.theme_mode = "LIGHT" if not self.page.dark_theme else "DARK"
        await self.page.client_storage.set_async("theme", self.page.theme_mode)
        for action in self.actions:
            if action.data == "theme_switcher":
                action.icon = (
                    DARK_MODE if self.page.theme_mode == "LIGHT" else LIGHT_MODE
                )
            if action.data == "other-buttons":
                for item in action.items:
                    if item.data in ["discord", "github"] and item.content is not None:
                        item.content.controls[0].src = (
                            f"assets/icons/brands/{item.data}-mark-black.png"
                            if self.page.theme_mode == "LIGHT"
                            else f"assets/icons/brands/{item.data}-mark-white.png"
                        )

        await self.page.update_async()

    async def display_changelog(self, event):
        content = Column(expand=True, scroll=True)
        async with ClientSession() as session:
            async with session.get(
                "https://kiwiapi.slynx.xyz/v1/misc/change_log"
            ) as response:
                data = await response.json()
                for version, version_data in sorted(
                    data.items(),
                    key=lambda x: -datetime.fromisoformat(x[1]["time"]).timestamp(),
                ):
                    content.controls.append(
                        Column(
                            controls=[
                                Text(loc("Version {}").format(version), size=20),
                                *(
                                    [
                                        Text(
                                            " " * 5
                                            + f"{change['author']} - {change['message']}",
                                            size=15,
                                        )
                                        for change in version_data["commits"]
                                    ]
                                ),
                            ]
                        )
                    )
        await self.page.dialog.set_data(
            modal=True,
            title=Text(loc("Change Log")),
            actions=[TextButton(loc("Close"), on_click=self.page.RTT.close_dialog)],
            actions_alignment=MainAxisAlignment.END,
            content=content,
        )

    async def check_for_update(self):
        await asyncio.sleep(1)
        update = await check_update(self.page.metadata.version, self.page.metadata.dev)
        if update[0] is not None:
            if not self.update_notified:
                await self.page.dialog.set_data(
                    modal=True,
                    title=Text(loc("Update available")),
                    content=Text(
                        loc("A new update is available, do you want to download it?")
                        + "\n"
                        + loc(
                            "The application will download update and close itself to install it."
                        )
                        + "\n"
                        + loc(
                            "After the installation is complete, the application will be automatically restarted."
                        )
                        + "\n\n"
                        + loc(
                            "Keeping the app up to date is important to ensure that you have the latest features and bug fixes."
                        )
                    ),
                    actions=[
                        TextButton(loc("Later"), on_click=self.page.RTT.close_dialog),
                        TextButton(loc("Update"), on_click=self.go_to_update_page),
                    ],
                    actions_alignment=MainAxisAlignment.END,
                )
                self.update_notified = True
            self.page.appbar.actions[0].visible = True
            await self.page.snack_bar.show(
                loc("A new update is available, click on the download icon to update."),
                "yellow",
            )
            await self.page.appbar.update_async()

    async def feedback_modal(self, event):
        self.feedback_text = TextField(
            width=800, expand=True, multiline=True, max_lines=10, min_lines=5
        )
        await self.page.dialog.set_data(
            modal=True,
            title=Text(loc("Feedback")),
            actions=[
                TextButton(loc("Close"), on_click=self.page.RTT.close_dialog),
                TextButton(loc("Send"), on_click=self.send_feedback),
            ],
            actions_alignment=MainAxisAlignment.END,
            content=self.feedback_text,
        )
        await self.page.update_async()

    async def send_feedback(self, event):
        async with ClientSession() as session:
            data = {"message": self.feedback_text.value}
            await session.post("https://kiwiapi.slynx.xyz/v1/misc/feedback", json=data)
        await self.page.dialog.hide()
        await self.page.snack_bar.show(loc("Feedback sent"))

    async def switch_debug(self, event):
        await self.go_to_update_page(event, True)

    async def go_to_update_page(self, event, invert=False):
        dev = self.page.metadata.dev
        if invert:
            dev = not dev
        update_url, is_windows = await check_update(
            self.page.metadata.version, dev, True
        )
        await self.page.dialog.hide()
        if is_windows:
            self.page.controls = [
                Column(
                    controls=[
                        Text(
                            loc("Downloading update, please wait..."),
                            text_align="center",
                            size=40,
                        )
                    ],
                    alignment="center",
                    horizontal_alignment="center",
                    expand=True,
                )
            ]
            event.control.disabled = True
            await self.page.update_async()
            async with ClientSession() as session:
                async with session.get(update_url) as response:
                    if response.status == 200:
                        exe_path = Path(sys.executable)
                        exe_location = exe_path.parent
                        appdata = Path(os.getenv("APPDATA"))
                        rtt_path = appdata.joinpath("Trove/sly.dev").joinpath(
                            self.page.metadata.tech_name
                        )
                        update_file = rtt_path / "update.msi"
                        update_file.write_bytes(await response.read())
                        subprocess.Popen(
                            ["update.bat", str(exe_location), str(update_file)],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                        )
                        await self.page.window_close_async()
        else:
            await self.page.launch_url_async(update_url)

    async def change_theme(self, _):
        self.page.theme_mode = "light" if self.page.theme_mode == "dark" else "dark"
        for action in self.actions:
            if action.data == "theme_switcher":
                action.icon = (
                    DARK_MODE if self.page.theme_mode == "light" else LIGHT_MODE
                )
            if action.data == "other-buttons":
                for item in action.items:
                    if item.data in ["discord", "github"] and item.content is not None:
                        item.content.controls[0].src = (
                            f"assets/icons/brands/{item.data}-mark-black.png"
                            if self.page.theme_mode == "light"
                            else f"assets/icons/brands/{item.data}-mark-white.png"
                        )
        self.page.preferences.theme = self.page.theme_mode
        self.page.preferences.save()
        await self.page.update_async()

    async def change_locale(self, event):
        self.page.preferences.locale = event.control.data
        ENGINE.locale = event.control.data
        await self.page.client_storage.set_async("locale", event.control.data.value)
        await self.page.RTT.restart()

    async def update_appbar(self):
        self.actions = self.build_actions(dict())
        await self.update_async()

    async def go_url(self, event):
        urls = {
            "discord": "https://kiwiapi.slynx.xyz/v1/misc/support",
            "github": "https://kiwiapi.slynx.xyz/v1/misc/github",
            "paypal": "https://kiwiapi.slynx.xyz/v1/misc/paypal",
            "kofi": "https://kiwiapi.slynx.xyz/v1/misc/kofi",
            "buy_me_a_coffee": "https://kiwiapi.slynx.xyz/v1/misc/bmc",
        }
        await self.page.launch_url_async(urls[event.control.data])

    async def open_about(self, event):
        await self.page.dialog.set_data(
            modal=True,
            title=Text(loc("About")),
            actions=[TextButton(loc("Close"), on_click=self.page.RTT.close_dialog)],
            actions_alignment=MainAxisAlignment.END,
            content=Text(
                loc(
                    (
                        "This application was developed by Sly. Interface design improved by Cr0nicl3 D3str0y3r.\n\n"
                        "I am coding this as an hobby with the goal of achieving greater front-end building skills,"
                        " at the same time I also improve code making and organization skills.\n\nI have the goal to"
                        " not only build something that is usable but mostly updatable with little effort or code"
                        " knowledge this however may be a challenge if newer updates come with changes on behavior"
                        " of previous content.\n\nI don't promise to keep this up to date forever, but as long as I"
                        " am around I should be able to.\n\nThanks for using my application. <3"
                    )
                )
            ),
        )

    async def change_color(self, event):
        color = event.control.data
        self.page.theme = Theme(color_scheme_seed=color)
        self.page.preferences.accent_color = color
        self.page.preferences.save()
        await self.page.update_async()
