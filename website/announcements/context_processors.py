"""These context processors can be used to expand the context provided to admin views."""
from .models import Announcement


def announcements(request):
    """Get a list of announcements.

    Filters out announcements that have been closed already.

    :param request: the request object
    :return: a dict containing the list announcements
    :rtype: dict
    """
    closed_announcements = request.session.get("closed_announcements", [])
    announcements_list = [
        a
        for a in Announcement.objects.all()
        if a.is_visible and a.pk not in closed_announcements
    ]

    # Announcements set by AnnouncementMiddleware.
    persistent_announcements = getattr(request, "_announcements", [])
    return {
        "announcements": announcements_list,
        "persistent_announcements": persistent_announcements,
    }
