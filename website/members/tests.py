from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from members.models import (Member, Membership,
                            gen_stats_member_type, gen_stats_year)
from utils.snippets import datetime_to_lectureyear


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
        self.assertEqual(len(members), 0)

    def _assert_thom(self, start, end):
        members = self._get_members(start, end)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].get_full_name(), 'Thom Wiggers')

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


class StatisticsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Add 10 members with default membership
        users = [get_user_model()(id=i, username=i) for i in range(10)]
        get_user_model().objects.bulk_create(users)
        memberships = [Membership(user_id=i, type="member")
                       for i in range(10)]
        Membership.objects.bulk_create(memberships)
        members = [Member(user_id=i) for i in range(10)]
        Member.objects.bulk_create(members)

    def sum_members(self, members, type=None):
        if type is None:
            return sum(sum(i.values()) for i in members)
        else:
            return sum(map(lambda x: x[type], members))

    def sum_member_types(self, members):
        return sum(members.values())

    def test_gen_stats_year_no_members(self):
        member_types = ["member", "supporter", "honorary"]
        result = gen_stats_year(member_types)
        self.assertEqual(0, self.sum_members(result))

    def test_gen_stats_active(self):
        """
        Testing if active and non-active objects are counted correctly
        """
        member_types = ["member", "supporter", "honorary"]
        current_year = datetime_to_lectureyear(date.today())

        # Set start date to current year - 1:
        for m in Member.objects.all():
            m.starting_year = current_year - 1
            m.save()
        result = gen_stats_year(member_types)
        self.assertEqual(10, self.sum_members(result))
        self.assertEqual(10, self.sum_members(result, "member"))

        result = gen_stats_member_type(member_types)
        self.assertEqual(10, self.sum_member_types(result))

        # Change one membership to supporter should decrease amount of members
        m = Membership.objects.all()[0]
        m.type = "supporter"
        m.save()

        result = gen_stats_year(member_types)
        self.assertEqual(10, self.sum_members(result))
        self.assertEqual(9, self.sum_members(result, "member"))
        self.assertEqual(1, self.sum_members(result, "supporter"))

        result = gen_stats_member_type(member_types)
        self.assertEqual(10, self.sum_member_types(result))
        self.assertEqual(9, result["member"])
        self.assertEqual(1, result["supporter"])

        # Same for honorary members
        m = Membership.objects.all()[1]
        m.type = "honorary"
        m.save()

        result = gen_stats_year(member_types)
        self.assertEqual(10, self.sum_members(result))
        self.assertEqual(8, self.sum_members(result, "member"))
        self.assertEqual(1, self.sum_members(result, "supporter"))
        self.assertEqual(1, self.sum_members(result, "honorary"))

        result = gen_stats_member_type(member_types)
        self.assertEqual(10, self.sum_member_types(result))
        self.assertEqual(8, result["member"])
        self.assertEqual(1, result["supporter"])
        self.assertEqual(1, result["honorary"])

        # Terminate one membership by setting end date to current_year -1,
        # should decrease total amount and total members
        m = Membership.objects.all()[2]
        m.until = timezone.now() - timedelta(days=365)
        m.save()
        result = gen_stats_year(member_types)
        self.assertEqual(9, self.sum_members(result))
        self.assertEqual(7, self.sum_members(result, "member"))
        self.assertEqual(1, self.sum_members(result, "supporter"))
        self.assertEqual(1, self.sum_members(result, "honorary"))

        result = gen_stats_member_type(member_types)
        self.assertEqual(9, self.sum_member_types(result))
        self.assertEqual(7, result["member"])
        self.assertEqual(1, result["supporter"])
        self.assertEqual(1, result["honorary"])

    def test_gen_stats_different_years(self):
        member_types = ["member", "supporter", "honorary"]
        current_year = datetime_to_lectureyear(date.today())

        # postgres does not define random access directly on unsorted querysets
        members = [member for member in Member.objects.all()]

        # one first year student
        m = members[0]
        m.starting_year = current_year
        m.save()

        # one second year student
        m = members[1]
        m.starting_year = current_year - 1
        m.save()

        # no third year students

        # one fourth year student
        m = members[2]
        m.starting_year = current_year - 3
        m.save()

        # no fifth year students

        # one >5 year student
        m = members[3]
        m.starting_year = current_year - 5
        m.save()

        # 4 active members
        result = gen_stats_year(member_types)
        self.assertEqual(4, self.sum_members(result))
        self.assertEqual(4, self.sum_members(result, "member"))

        # one first year student
        self.assertEqual(1, result[0]['member'])

        # one second year student
        self.assertEqual(1, result[1]['member'])

        # no third year students
        self.assertEqual(0, result[2]['member'])

        # one fourth year student
        self.assertEqual(1, result[3]['member'])

        # no fifth year students
        self.assertEqual(0, result[4]['member'])

        # one >5 year student
        self.assertEqual(1, result[5]['member'])
