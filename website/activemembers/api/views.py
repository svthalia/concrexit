import datetime

from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils import timezone
from rest_framework.generics import ListAPIView

from activemembers.api.permissions import NextCloudPermission
from activemembers.api.serializers import (
    NextCloudMemberSerializer,
    NextCloudGroupSerializer
)
from activemembers.models import MemberGroupMembership, MemberGroup, Board
from members.models import Member
from utils.snippets import datetime_to_lectureyear


class NextCloudUsersView(ListAPIView):
    permission_classes = [NextCloudPermission]
    queryset = Member.current_members.all()
    serializer_class = NextCloudMemberSerializer

    def get_queryset(self):
        perm = Permission.objects.get(content_type__app_label='members',
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
    queryset = (MemberGroup.objects
                .exclude(name_en='admin')
                .exclude(active=False)
                .all())
    serializer_class = NextCloudGroupSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        perm = Permission.objects.get(content_type__app_label='members',
                                      codename='nextcloud_admin')
        admin_users = Member.current_members.filter(
            Q(is_superuser=True) |
            Q(groups__permissions=perm) |
            Q(user_permissions=perm) |
            (Q(membergroup__permissions=perm) &
             (Q(membergroupmembership__until=None) |
              Q(membergroupmembership__until__gte=timezone.now())))
        ).distinct().values_list('username', flat=True)

        current_year = datetime_to_lectureyear(datetime.date.today())
        try:
            board = Board.objects.get(
                since__year=current_year, until__year=current_year + 1)
            board_users = board.members.values_list('username', flat=True)
        except Board.DoesNotExist:
            board_users = []

        committee_chair_users = (MemberGroupMembership.active_objects
                                 .filter(group__board=None)
                                 .filter(group__society=None)
                                 .filter(chair=True)
                                 .values_list('member__username', flat=True))

        response.data = list(response.data) + [
            {
                'pk': -1,
                'name': 'admin',
                'members': admin_users
            },
            {
                'pk': -2,
                'name': 'Board',
                'members': board_users
            },
            {
                'pk': -3,
                'name': 'Committee Chairs',
                'members': committee_chair_users
            }
        ]
        return response
