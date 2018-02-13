"""
These context processors can be used to expand the context provided
to admin views.
"""
from .models import Announcement


def announcements(request):
    """
    Gets a list of announcements.

    Filters out announcements that have been closed already.

    :param request: the request object
    :return: a dict containing the list announcements
    :rtype: dict
    """
    closed_announcements = request.session.get('closed_announcements', [])
    announcements_list = [a for a in Announcement.objects.all()
                          if a.is_visible and a.pk not in closed_announcements]
    return {'announcements': announcements_list}
