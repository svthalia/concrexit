"""API views of the activemembers app."""

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    get_object_or_404,
)
from rest_framework.permissions import (
    DjangoModelPermissions,
    DjangoModelPermissionsOrAnonReadOnly,
)

from activemembers.api.v2.serializers.member_group import (
    MemberGroupSerializer,
    MemberGroupListSerializer,
)
from activemembers.models import (
    MemberGroupMembership,
    Committee,
    Society,
    Board,
    MemberGroup,
)


class MemberGroupListView(ListAPIView):
    """Returns an overview of all member groups."""

    serializer_class = MemberGroupListSerializer
    queryset = MemberGroup.active_objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["activemembers:read"]


class MemberGroupDetailView(RetrieveAPIView):
    """Returns details of a member group."""

    serializer_class = MemberGroupSerializer
    queryset = MemberGroup.active_objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["activemembers:read"]

    def _get_memberships(self, group):
        if hasattr(group, "board"):
            return MemberGroupMembership.objects.filter(group=group)
        return MemberGroupMembership.active_objects.filter(group=group)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["get_memberships"] = self._get_memberships
        return context


class CommitteeListView(MemberGroupListView):
    """Returns an overview of all committees."""

    queryset = Committee.active_objects.all()


class CommitteeDetailView(MemberGroupDetailView):
    """Returns details of a committee."""

    queryset = Committee.active_objects.all()


class SocietyListView(MemberGroupListView):
    """Returns an overview of all societies."""

    queryset = Society.active_objects.all()


class SocietyDetailView(MemberGroupDetailView):
    """Returns details of a society."""

    queryset = Society.active_objects.all()


class BoardListView(MemberGroupListView):
    """Returns an overview of all boards."""

    queryset = Board.objects.all()


class BoardDetailView(MemberGroupDetailView):
    """Returns details of a board."""

    queryset = Board.objects.all()

    def get_object(self) -> Board:
        if self.kwargs.get("since") and self.kwargs.get("until"):
            return get_object_or_404(
                Board,
                since__year=self.kwargs.get("since"),
                until__year=self.kwargs.get("until"),
            )
        return super().get_object()
