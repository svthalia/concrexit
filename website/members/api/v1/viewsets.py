"""DRF viewsets defined by the members package."""

from oauth2_provider.contrib.rest_framework import IsAuthenticatedOrTokenHasScope
from rest_framework import filters, mixins, permissions, viewsets

from members.models import Member

from .serializers import (
    MemberListSerializer,
    ProfileEditSerializer,
    ProfileRetrieveSerializer,
)


class MemberViewset(viewsets.ReadOnlyModelViewSet, mixins.UpdateModelMixin):
    """Viewset that renders or edits a member."""

    required_scopes = ["members:read"]
    queryset = Member.objects.all()
    filter_backends = (
        filters.OrderingFilter,
        filters.SearchFilter,
    )
    ordering_fields = ("profile__starting_year", "first_name", "last_name")
    search_fields = ("profile__nickname", "first_name", "last_name", "username")
    lookup_field = "pk"

    def get_serializer_class(self):
        if self.action == "retrieve":
            if self.is_self_reference() or (
                self.request.user
                and self.request.user.has_perm("members.change_profile")
            ):
                return ProfileEditSerializer
            return ProfileRetrieveSerializer
        if self.action.endswith("update"):
            return ProfileEditSerializer
        return MemberListSerializer

    def get_queryset(self):
        if self.action == "list":
            return Member.current_members.get_queryset()
        return Member.objects.all()

    def is_self_reference(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_arg = self.kwargs.get(lookup_url_kwarg)

        return (
            self.request.user
            and self.request.user.is_authenticated
            and lookup_arg
            in (
                "me",
                str(self.request.member.pk),
            )
        )

    def get_permissions(self):
        if self.action and (
            not self.action.endswith("update") or self.is_self_reference()
        ):
            return [IsAuthenticatedOrTokenHasScope()]
        return [IsAuthenticatedOrTokenHasScope(), permissions.DjangoModelPermissions()]

    def get_object(self):
        if self.is_self_reference():
            return self.request.member.profile
        return super().get_object().profile
