"""API views of the activemembers app."""
from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters as framework_filters
from rest_framework.generics import ListAPIView, RetrieveAPIView, get_object_or_404

from activemembers.api.v2 import filters
from activemembers.api.v2.serializers.member_group import (
    MemberGroupListSerializer,
    MemberGroupSerializer,
)
from activemembers.models import Board, MemberGroup, MemberGroupMembership


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
    ]
    required_scopes = ["activemembers:read"]


class MemberGroupDetailView(RetrieveAPIView):
    """Returns details of a member group."""

    serializer_class = MemberGroupSerializer
    queryset = MemberGroup.active_objects.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
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


class BoardDetailView(MemberGroupDetailView):
    """Returns details of a board group."""

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = get_object_or_404(
            queryset,
            since__year=self.kwargs.get("since"),
            until__year=self.kwargs.get("until"),
        )

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)
        return obj
