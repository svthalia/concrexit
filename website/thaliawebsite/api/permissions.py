from django.core.exceptions import ImproperlyConfigured
from rest_framework import exceptions
from rest_framework.permissions import BasePermission


class DjangoCustomPermissions(BasePermission):
    """
    The request is authenticated using `django.contrib.auth` permissions.
    See: https://docs.djangoproject.com/en/dev/topics/auth/#permissions

    It ensures that the user is authenticated, and has the appropriate
    `add`/`change`/`delete` permissions on the model.

    The permissions should be defined as follows:
    required_permissions = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': [],
        'PUT': [],
        'PATCH': [],
        'DELETE': [],
    }
    """

    authenticated_users_only = True

    def get_required_permissions(self, method, view):
        """
        Given a model and an HTTP method, return the list of permission
        codes that the user is required to have.
        """
        try:
            perms_map = getattr(view, "required_permissions")
        except AttributeError:
            raise ImproperlyConfigured(
                "DjangoCustomPermissions requires the view to"
                " define the required_permissions attribute"
            )

        if method not in perms_map:
            raise exceptions.MethodNotAllowed(method)

        return perms_map[method]

    def has_permission(self, request, view):
        if not request.user or (
            not request.user.is_authenticated and self.authenticated_users_only
        ):
            return False

        perms = self.get_required_permissions(request.method, view)

        return request.user.has_perms(perms)


class DjangoCustomPermissionsOrAnonReadOnly(DjangoCustomPermissions):
    """
    Similar to DjangoModelPermissions, except that anonymous users are
    allowed read-only access.
    """

    authenticated_users_only = False
