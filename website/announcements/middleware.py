from announcements.services import get_announcements


class AnnouncementMiddleware:
    """Adds the _announcements attribute to requests.

    This middleware lets apps add announcements to a request, by providing an
    AppConfig.announcements method that takes the request as argument, and returns
    a list of announcements to add.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._announcements = get_announcements(request)

        return self.get_response(request)
