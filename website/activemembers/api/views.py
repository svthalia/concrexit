from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils import timezone
from rest_framework.generics import ListAPIView

from activemembers.api.permissions import NextCloudPermission
from activemembers.api.serializers import (
    NextCloudMemberSerializer,
    NextCloudGroupSerializer
)
from activemembers.models import MemberGroupMembership, MemberGroup
from members.models import Member


class NextCloudUsersView(ListAPIView):
    permission_classes = [NextCloudPermission]
    queryset = Member.current_members.all()
    serializer_class = NextCloudMemberSerializer

    def get_queryset(self):
        perm = Permission.objects.get(content_type__app_label='auth',
                                      codename='nextcloud_admin')
        return super().get_queryset().filter(
            Q(pk__in=MemberGroupMembership.active_objects.values_list(
                'member_id', flat=True)) |
            Q(is_superuser=True) |
            Q(groups__permissions=perm) |
            Q(user_permissions=perm) |
            (Q(membergroup__permissions=perm) &
             (Q(membergroupmembership__until=None) |
              Q(membergroupmembership__until__gte=timezone.now())))
        ).distinct()


class NextCloudGroupsView(ListAPIView):
    permission_classes = [NextCloudPermission]
    queryset = MemberGroup.objects.exclude(
        name_en='admin', name_nl='admin').all()
    serializer_class = NextCloudGroupSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        perm = Permission.objects.get(content_type__app_label='auth',
                                      codename='nextcloud_admin')
        users = Member.current_members.filter(
            Q(is_superuser=True) |
            Q(groups__permissions=perm) |
            Q(user_permissions=perm) |
            (Q(membergroup__permissions=perm) &
             (Q(membergroupmembership__until=None) |
              Q(membergroupmembership__until__gte=timezone.now())))
        ).distinct().values_list('username', flat=True)

        if users.count() > 0:
            response.data = list(response.data) + [
                {
                    'pk': -1,
                    'name': 'admin',
                    'members': users
                }
            ]
        return response
