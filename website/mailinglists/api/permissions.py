from django.conf import settings

from rest_framework import permissions


class MailingListPermission(permissions.BasePermission):
    """
    Permission check for mailing list secret key
    """

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if 'secret' in request.GET:
            return (request.GET['secret']
                    == settings.MAILINGLIST_API_SECRET)
        return False
