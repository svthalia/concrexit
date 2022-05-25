"""Middleware provided by the members package."""
from django.utils.functional import SimpleLazyObject

from members.models import Member


def get_member(request):
    try:
        return Member.objects.get(pk=request.user.pk)
    except AttributeError:
        return None
    except Member.DoesNotExist:
        return None


class MemberMiddleware:
    """Adds the member attribute to requests."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # This needs to be a lazy object as Django REST Frameworks calls the
        # the middleware before setting request.user
        # This also avoids unnecessary queries when request.member is not used
        request.member = SimpleLazyObject(lambda: get_member(request))

        print("---------------\nHost:", request.get_host())

        return self.get_response(request)
