from django.core.exceptions import PermissionDenied

from events import services
from events.models import Event


def organiser_only(view_function):
    return OrganiserOnly(view_function)


class OrganiserOnly(object):
    def __init__(self, view_function):
        self.view_function = view_function

    def __call__(self, request, *args, **kwargs):
        event_id = kwargs.get('event_id')
        if event_id:
            event = None
            try:
                event = Event.objects.get(pk=event_id)
            except Event.DoesNotExist:
                pass

            if event and services.is_organiser(request.user, event):
                return self.view_function(request, *args, **kwargs)

        raise PermissionDenied
