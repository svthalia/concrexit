import hashlib

from rest_framework import permissions


class MailingListPermission(permissions.BasePermission):
    """
    Permission check for mailing list secret key
    """

    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        if 'secret' in request.GET:
            apihash = hashlib.sha1(request.GET['secret']
                                   .encode('utf-8')).hexdigest()
            return apihash == '356a192b7913b04c54574d18c28d46e6395428ab'
        return False
