from django.core.exceptions import PermissionDenied

from events import services
from events.models import Event


def organiser_only(view_function):
    """See OrganiserOnly."""
    return OrganiserOnly(view_function)


class OrganiserOnly:
    """Decorator that denies access to the page under certain conditions.

    Under these conditions access is denied:
    1. There is no `pk` or `registration` in the request
    2. The specified event does not exist
    3. The user is no organiser of the specified event
    """

    def __init__(self, view_function):
        self.view_function = view_function

    def __call__(self, request, *args, **kwargs):
        event = None

        if "pk" in kwargs:
            try:
                event = Event.objects.get(pk=kwargs.get("pk"))
            except Event.DoesNotExist:
                pass
        elif "registration" in kwargs:
            try:
                event = Event.objects.get(
                    eventregistration__pk=kwargs.get("registration")
                )
            except Event.DoesNotExist:
                pass

        if event and services.is_organiser(request.member, event):
            return self.view_function(request, *args, **kwargs)

        raise PermissionDenied
