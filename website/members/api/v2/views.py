"""API views of the activemembers app."""

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

from members.api.v2.serializers.member import MemberSerializer, MemberListSerializer
from members.models import Member


class MemberListView(ListAPIView):
    """Returns an overview of all members."""

    serializer_class = MemberListSerializer
    queryset = Member.current_members.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["members:read"]
    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    ordering_fields = ("first_name", "last_name", "username")
    search_fields = (
        "profile__nickname",
        "profile__starting_year",
        "first_name",
        "last_name",
        "username",
    )


class MemberDetailView(RetrieveAPIView):
    """Returns details of a member."""

    serializer_class = MemberSerializer
    queryset = Member.current_members.all()
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes = ["activemembers:read"]
