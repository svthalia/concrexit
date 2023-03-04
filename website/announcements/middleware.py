from django.apps import apps


class AnnouncementMiddleware:
    """Adds the _announcements attribute to requests.

    This middleware lets apps add announcements to a request, by providing an
    AppConfig.announcements method that takes the request as argument, and returns
    a list of announcements to add.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        announcements = []
        for app in apps.get_app_configs():
            if hasattr(app, "announcements"):
                announcements += app.announcements(request)
        setattr(request, "_announcements", announcements)

        return self.get_response(request)
