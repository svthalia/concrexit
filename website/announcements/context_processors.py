from .models import Announcement


def announcements(request):
    closed_announcements = request.session.get('closed_announcements', [])
    announcements = [a for a in Announcement.objects.all()
                     if a.is_visible and a.pk not in closed_announcements]
    return {'announcements': announcements}
