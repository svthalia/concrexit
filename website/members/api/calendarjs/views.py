import copy

from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from members.api.calendarjs.serializers import MemberBirthdaySerializer
from members.models import Member
from utils.snippets import extract_date_range


class CalendarJSBirthdayListView(ListAPIView):
    """Define a custom route that outputs the correctly formatted events information for CalendarJS, published events only."""

    serializer_class = MemberBirthdaySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

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

    def get_queryset(self):
        start, end = extract_date_range(self.request)

        queryset = Member.current_members.with_birthdays_in_range(start, end).filter(
            profile__show_birthday=True
        )

        all_birthdays = [self._get_birthdays(m, start, end) for m in queryset.all()]
        birthdays = [x for sublist in all_birthdays for x in sublist]

        return birthdays
