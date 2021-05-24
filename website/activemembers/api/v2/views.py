"""API views of the activemembers app."""
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters as framework_filters
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

from activemembers.api.v2 import filters
from activemembers.api.v2.serializers.member_group import (
    MemberGroupSerializer,
    MemberGroupListSerializer,
)
from activemembers.models import (
    MemberGroupMembership,
    MemberGroup,
)


class MemberGroupListView(ListAPIView):
    """Returns an overview of all member groups."""

    serializer_class = MemberGroupListSerializer
    queryset = MemberGroup.active_objects.all()
    filter_backends = (
        framework_filters.SearchFilter,
        filters.MemberGroupTypeFilter,
        filters.MemberGroupDateFilter,
    )
    search_fields = ("name",)
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
