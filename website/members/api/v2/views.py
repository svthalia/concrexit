"""API views of the activemembers app."""

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from django.shortcuts import get_object_or_404
from rest_framework import filters
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    UpdateAPIView,
)
from rest_framework.permissions import DjangoModelPermissionsOrAnonReadOnly

from thaliawebsite.api.openapi import OAuthAutoSchema
from members.api.v2.serializers.member import (
    MemberSerializer,
    MemberListSerializer,
    MemberCurrentSerializer,
)
from members.models import Member
from thaliawebsite.api.v2.permissions import IsAuthenticatedOrTokenHasScopeForMethod


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
    required_scopes = ["members:read"]


class MemberCurrentView(MemberDetailView, UpdateAPIView):
    """Returns details of the authenticated member."""

    serializer_class = MemberCurrentSerializer
    schema = OAuthAutoSchema(operation_id_base="CurrentMember")
    permission_classes = [
        IsAuthenticatedOrTokenHasScopeForMethod,
        DjangoModelPermissionsOrAnonReadOnly,
    ]
    required_scopes_per_method = {
        "GET": ["profile:read"],
        "PATCH": ["profile:write"],
        "PUT": ["profile:write"],
    }

    def get_object(self):
        return get_object_or_404(Member, pk=self.request.user.pk)
