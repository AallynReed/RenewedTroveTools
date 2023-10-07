from views.desktop import *
from views.web import *
from views.hybrid import *


def all_views(web_mode=False):
    views = list()
    views.append(HomeView)
    if not web_mode:
        views.append(ModsView)
        views.append(ExtractorView)
    views.append(StarView)
    views.append(GemBuildsView)
    views.append(GemView)
    views.append(GemSetView)
    views.append(MasteryView)
    views.append(MagicFindView)
    return views
