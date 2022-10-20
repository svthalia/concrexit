"""API views of the activemembers app."""

from django.shortcuts import get_object_or_404

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters as framework_filters
from rest_framework.generics import ListAPIView, RetrieveAPIView, UpdateAPIView

from members.api.v2 import filters
from members.api.v2.serializers.member import (
    MemberCurrentSerializer,
    MemberListSerializer,
    MemberSerializer,
)
from members.models import Member
from thaliawebsite.api.openapi import OAuthAutoSchema
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod


class MemberListView(ListAPIView):
    """Returns an overview of all members."""

    serializer_class = MemberListSerializer
    queryset = Member.current_members.all().select_related("profile")
    permission_classes = [
        IsAuthenticatedOrTokenHasScope,
    ]
    required_scopes = ["members:read"]
    filter_backends = (
        framework_filters.OrderingFilter,
        framework_filters.SearchFilter,
        filters.MembershipTypeFilter,
        filters.StartingYearFilter,
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
    ]
    required_scopes = ["members:read"]


class MemberCurrentView(MemberDetailView, UpdateAPIView):
    """Returns details of the authenticated member."""

    serializer_class = MemberCurrentSerializer
    schema = OAuthAutoSchema(operation_id_base="CurrentMember")
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
    ]
    required_scopes_per_method = {
        "GET": ["profile:read"],
        "PATCH": ["profile:write"],
        "PUT": ["profile:write"],
    }

    def get_object(self):
        return get_object_or_404(Member, pk=self.request.user.pk)
