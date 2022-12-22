from django.apps import apps


class AnnouncementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        announcements = []
        for app in apps.get_app_configs():
            if hasattr(app, "announcements"):
                announcements += app.announcements(request)
        setattr(request, "_announcements", announcements)

        return self.get_response(request)
