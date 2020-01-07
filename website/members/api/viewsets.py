"""DRF viewsets defined by the members package"""
import copy

from rest_framework import permissions
from rest_framework import viewsets, filters, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from members.api.serializers import (
    MemberBirthdaySerializer,
    MemberListSerializer,
    ProfileRetrieveSerializer,
    ProfileEditSerializer,
)
from members.models import Member
from utils.snippets import extract_date_range


class MemberViewset(viewsets.ReadOnlyModelViewSet, mixins.UpdateModelMixin):
    """Viewset that renders or edits a member"""

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
            if self.is_self_reference() or self.request.user.has_perm(
                "members.change_profile"
            ):
                return ProfileEditSerializer
            return ProfileRetrieveSerializer
        elif self.action.endswith("update"):
            return ProfileEditSerializer
        return MemberListSerializer

    def get_queryset(self):
        if self.action == "list":
            return Member.current_members.get_queryset()
        return Member.objects.all()

    def is_self_reference(self):
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        lookup_arg = self.kwargs.get(lookup_url_kwarg)

        return self.request.user.is_authenticated and lookup_arg in (
            "me",
            str(self.request.member.pk),
        )

    def get_permissions(self):
        if self.action and (
            not self.action.endswith("update") or self.is_self_reference()
        ):
            return [permissions.IsAuthenticated()]
        else:
            return [permissions.DjangoModelPermissions()]

    def get_object(self):
        if self.is_self_reference():
            return self.request.member.profile
        else:
            return super().get_object().profile

    def _get_birthdays(self, member, start, end):
        birthdays = []

        start_year = max(start.year, member.profile.birthday.year)
        for year in range(start_year, end.year + 1):
            bday = copy.deepcopy(member)
            try:
                bday.profile.birthday = bday.profile.birthday.replace(year=year)
            except ValueError as e:
                if bday.profile.birthday.month == 2 and bday.profile.birthday.day == 29:
                    bday.profile.birthday = bday.profile.birthday.replace(
                        year=year, day=28
                    )
                else:
                    raise e
            if start.date() <= bday.profile.birthday <= end.date():
                birthdays.append(bday)
        return birthdays

    @action(detail=False)
    def birthdays(self, request):
        start, end = extract_date_range(request)

        queryset = Member.current_members.with_birthdays_in_range(start, end).filter(
            profile__show_birthday=True
        )

        all_birthdays = [self._get_birthdays(m, start, end) for m in queryset.all()]
        birthdays = [x for sublist in all_birthdays for x in sublist]

        serializer = MemberBirthdaySerializer(birthdays, many=True)
        return Response(serializer.data)
