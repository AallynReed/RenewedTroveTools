from views.desktop import *
from views.hybrid import *
from views.web import *
from views.no_tab import *


def all_views(web_mode=False):
    views = list()
    views.append(HomeView)
    if not web_mode:
        views.append(ModsView)
        views.append(ExtractorView)
        views.append(LoginView)
    views.append(StarView)
    views.append(GemBuildsView)
    views.append(GemView)
    views.append(GemSetView)
    views.append(MasteryView)
    views.append(MagicFindView)
    if web_mode:
        views.append(View404)
    return views
