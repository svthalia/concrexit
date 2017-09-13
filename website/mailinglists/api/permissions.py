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
            return apihash == 'cb004452d9c80e295bebfc778871b3b082d70ad8'
        return False
