"""
Authentication backend to check permissions
"""
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils import timezone

from members.models import Member


class CommitteeBackend(object):
    """Check permissions against committees"""

    def authenticate(self, *args, **kwargs):
        """Not implemented in this backend"""
        return

    def get_user(self, *args, **kwargs):
        """Not implemented in this backend"""
        return

    def _get_permissions(self, user, obj):
        if not user.is_active or user.is_anonymous or obj is not None:
            return set()
        perm_cache_name = '_committee_perm_cache'
        try:
            committees = user.member.committee_set.filter(
                Q(committeemembership__until=None) |
                Q(committeemembership__until__gte=timezone.now())
            )
        except Member.DoesNotExist:
            return set()
        if not hasattr(user, perm_cache_name):
            perms = (Permission.objects
                     .filter(committee__in=committees)
                     .values_list('content_type__app_label', 'codename')
                     .order_by())
            setattr(user, perm_cache_name,
                    set("{}.{}".format(ct, name) for ct, name in perms))
        return getattr(user, perm_cache_name)

    def get_all_permissions(self, user, obj=None):
        return self._get_permissions(user, obj)

    def get_group_permissions(self, user, obj=None):
        return self._get_permissions(user, obj)

    def has_perm(self, user, perm, obj=None):
        if not user.is_active:
            return False
        return perm in self.get_all_permissions(user, obj)

    def has_module_perms(self, user, app_label):
        """Returns True if user has any permissions in the given app_label"""
        if not user.is_active:
            return False
        for perm in self.get_all_permissions(user):
            if perm[:perm.index('.')] == app_label:
                return True
        return False
