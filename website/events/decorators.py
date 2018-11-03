"""The decorators defined by the events package"""
from django.core.exceptions import PermissionDenied

from events import services
from events.models import Event


def organiser_only(view_function):
    """See OrganiserOnly"""
    return OrganiserOnly(view_function)


class OrganiserOnly(object):
    """
    Decorator that denies access to the page if:
    1. There is no `pk` in the request
    2. The specified event does not exist
    3. The user is no organiser of the specified event
    """
    def __init__(self, view_function):
        self.view_function = view_function

    def __call__(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if pk:
            event = None
            try:
                event = Event.objects.get(pk=pk)
            except Event.DoesNotExist:
                pass

            if event and services.is_organiser(request.member, event):
                return self.view_function(request, *args, **kwargs)

        raise PermissionDenied
