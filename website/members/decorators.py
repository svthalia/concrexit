from django.core.exceptions import PermissionDenied


def membership_required(view_function):
    return ActiveMembershipRequired(view_function)


class ActiveMembershipRequired:
    """Decorator that checks if the user has an active membership."""

    def __init__(self, view_function):
        self.view_function = view_function

    def __call__(self, request, *args, **kwargs):
        if request.member and request.member.has_active_membership():
            return self.view_function(request, *args, **kwargs)

        raise PermissionDenied
