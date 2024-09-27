from flet import View
from flet_core.icons import NOTIFICATIONS

from controllers import NotificationsController


class NotificationsView(View):
    route = "/notifications"
    title = "Notifications"
    icon = NOTIFICATIONS
    has_tab = False

    def __init__(self, page):
        ctrl = NotificationsController(page=page)
        super().__init__(route=self.route, controls=[ctrl.main])
