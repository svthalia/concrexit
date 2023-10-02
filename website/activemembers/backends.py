"""Authentication backend to check permissions."""
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils import timezone

from members.models import Member


class MemberGroupBackend:
    """Check permissions against MemberGroups."""

    def authenticate(self, *args, **kwargs):
        """Not implemented in this backend."""
        return

    def get_user(self, *args, **kwargs):
        """Not implemented in this backend."""
        return

    @staticmethod
    def _get_permissions(user, obj):
        if not user.is_active or user.is_anonymous or obj is not None:
            return set()
        try:
            member = Member.objects.get(pk=user.pk)
        except Member.DoesNotExist:
            return set()

        now = timezone.now()
        groups = member.membergroup_set.filter(
            Q(membergroupmembership__until=None)
            | Q(
                membergroupmembership__since__lte=now,
                membergroupmembership__until__gte=now,
            )
        )

        perm_cache_name = "_membergroup_perm_cache"
        if not hasattr(user, perm_cache_name):
            perms = (
                Permission.objects.filter(membergroup__in=groups)
                .values_list("content_type__app_label", "codename")
                .order_by()
            )
            setattr(
                user,
                perm_cache_name,
                set(f"{ct}.{name}" for ct, name in perms),
            )
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
        """Return True if user has any permissions in the given app_label."""
        if not user.is_active:
            return False
        for perm in self.get_all_permissions(user):
            if perm[: perm.index(".")] == app_label:
                return True
        return False
