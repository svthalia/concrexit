from datetime import datetime

from django.test import TestCase
from django.utils import timezone

from members.models import Member


class MemberBirthdayTest(TestCase):
    fixtures = ['members.json']

    def _make_date(self, date):
        return timezone.make_aware(datetime.strptime(date, '%Y-%m-%d'))

    def _get_members(self, start, end):
        start_date = self._make_date(start)
        end_date = self._make_date(end)
        return Member.active_members.with_birthdays_in_range(
            start_date, end_date
        )

    def _assert_none(self, start, end):
        members = self._get_members(start, end)
        self.assertEquals(len(members), 0)

    def _assert_thom(self, start, end):
        members = self._get_members(start, end)
        self.assertEquals(len(members), 1)
        self.assertEquals(members[0].get_full_name(), 'Thom Wiggers')

    def test_one_year_contains_birthday(self):
        self._assert_thom('2016-03-02', '2016-08-08')

    def test_one_year_not_contains_birthday(self):
        self._assert_none('2016-01-01', '2016-02-01')

    def test_span_year_contains_birthday(self):
        self._assert_thom('2015-08-09', '2016-08-08')

    def test_span_year_not_contains_birthday(self):
        self._assert_none('2015-12-25', '2016-03-01')

    def test_span_multiple_years_contains_birthday(self):
        self._assert_thom('2012-12-31', '2016-01-01')

    def test_range_before_person_born(self):
        self._assert_none('1985-12-12', '1985-12-13')

    def test_person_born_in_range_in_one_year(self):
        self._assert_thom('1993-01-01', '1993-04-01')

    def test_person_born_in_range_spanning_one_year(self):
        self._assert_thom('1992-12-31', '1993-04-01')

    def test_person_born_in_range_spanning_multiple_years(self):
        self._assert_thom('1992-12-31', '1995-01-01')
