import copy
from datetime import datetime

from django.utils import timezone
from rest_framework import permissions
from rest_framework import viewsets, filters
from rest_framework.decorators import list_route
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from members.api.serializers import (MemberBirthdaySerializer,
                                     MemberRetrieveSerializer,
                                     MemberListSerializer)
from members.models import Member


class MemberViewset(viewsets.ReadOnlyModelViewSet):
    queryset = Member.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.OrderingFilter, filters.SearchFilter,)
    ordering_fields = ('profile__starting_year', 'first_name', 'last_name')
    search_fields = ('profile__nickname', 'first_name', 'last_name',
                     'username')
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'me':
            return MemberRetrieveSerializer
        return MemberListSerializer

    def get_queryset(self):
        if self.action == 'list':
            return Member.active_members.get_queryset()
        return Member.objects.all()

    def _get_birthdays(self, member, start, end):
        birthdays = []

        start_year = max(start.year, member.profile.birthday.year)
        for year in range(start_year, end.year + 1):
            bday = copy.deepcopy(member)
            try:
                bday.profile.birthday = \
                        bday.profile.birthday.replace(year=year)
            except ValueError as e:
                if (bday.profile.birthday.month == 2 and
                        bday.profile.birthday.day == 29):
                    bday.profile.birthday = \
                            bday.profile.birthday.replace(year=year, day=28)
                else:
                    raise e
            if start.date() <= bday.profile.birthday <= end.date():
                birthdays.append(bday)

        return birthdays

    @list_route()
    def birthdays(self, request):
        try:
            start = timezone.make_aware(
                datetime.strptime(request.query_params['start'], '%Y-%m-%d')
            )
            end = timezone.make_aware(
                datetime.strptime(request.query_params['end'], '%Y-%m-%d')
            )
        except:
            raise ParseError(detail='start or end query parameters invalid')

        queryset = (
            Member.active_members
                  .with_birthdays_in_range(start, end)
                  .filter(profile__show_birthday=True)
        )

        all_birthdays = [
            self._get_birthdays(m, start, end)
            for m in queryset.all()
        ]
        birthdays = [x for sublist in all_birthdays for x in sublist]

        serializer = MemberBirthdaySerializer(birthdays, many=True)
        return Response(serializer.data)

    @list_route()
    def me(self, request):
        serializer = self.get_serializer_class()(request.member)
        return Response(serializer.data)
