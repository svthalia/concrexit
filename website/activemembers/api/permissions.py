from django.conf import settings

from rest_framework import permissions


class NextCloudPermission(permissions.BasePermission):
    """
    Permission check for Nextcloud secret key
    """

    def has_permission(self, request, view):
        if "HTTP_AUTHORIZATION" in request.META:
            token = request.META["HTTP_AUTHORIZATION"]
            return token == ("Secret " + settings.ACTIVEMEMBERS_NEXTCLOUD_API_SECRET)
        return request.user.is_superuser
