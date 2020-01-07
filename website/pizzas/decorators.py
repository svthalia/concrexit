"""The decorators defined by the pizzas package"""
from django.core.exceptions import PermissionDenied

from events import services
from pizzas.models import PizzaEvent


def organiser_only(view_function):
    """See OrganiserOnly"""
    return OrganiserOnly(view_function)


class OrganiserOnly(object):
    """
    Decorator that denies access to the page if:
    1. There is no `pk` in the request
    2. The specified pizza event does not exist
    3. The user is no organiser of the specified pizza event
    """

    def __init__(self, view_function):
        self.view_function = view_function

    def __call__(self, request, *args, **kwargs):
        pizza_event = None

        if "pk" in kwargs:
            try:
                pizza_event = PizzaEvent.objects.get(pk=kwargs.get("pk"))
            except PizzaEvent.DoesNotExist:
                pass

        if pizza_event and services.is_organiser(request.member, pizza_event.event):
            return self.view_function(request, *args, **kwargs)

        raise PermissionDenied
