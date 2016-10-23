import copy
from datetime import datetime

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from members.api.serializers import MemberBirthdaySerializer
from members.models import Member


class MemberViewset(viewsets.ViewSet):
    queryset = Member.objects.all()

    def _get_birthdays(self, member, start, end):
        birthdays = []

        start_year = max(start.year, member.birthday.year)
        for year in range(start_year, end.year + 1):
            bday = copy.deepcopy(member)
            bday.birthday = bday.birthday.replace(year=year)
            if start.date() <= bday.birthday <= end.date():
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
            Member
            .active_members
            .with_birthdays_in_range(start, end)
            .filter(show_birthday=True)
        )
        queryset.prefetch_related('membership_get')

        all_birthdays = [
            self._get_birthdays(m, start, end)
            for m in queryset.all()
        ]
        birthdays = [x for sublist in all_birthdays for x in sublist]

        serializer = MemberBirthdaySerializer(birthdays, many=True)
        return Response(serializer.data)
