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
    queryset = Member.current_members.filter(
        pk__in=MemberGroupMembership.active_objects.values_list(
            'member_id', flat=True)
    )
    serializer_class = NextCloudMemberSerializer


class NextCloudGroupsView(ListAPIView):
    permission_classes = [NextCloudPermission]
    queryset = MemberGroup.objects.all()
    serializer_class = NextCloudGroupSerializer
