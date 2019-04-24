from django.conf import settings

from rest_framework import permissions


class SentryIdentityPermission(permissions.BasePermission):
    """
    Permission check for Sentry secret key and access permission
    """

    def has_permission(self, request, view):
        if 'secret' in request.GET:
            return (request.GET['secret'] == settings.MEMBERS_SENTRY_API_SECRET
                    and request.user.has_perm('members.sentry_access'))
        return False
