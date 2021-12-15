from datetime import datetime
import doctest
from itertools import groupby

from django.test import TestCase, override_settings
from django.utils import timezone

from members import models
from members.models import Profile, Member


def load_tests(loader, tests, ignore):
    """Load doctests."""
    tests.addTests(doctest.DocTestSuite(models))


@override_settings(SUSPEND_SIGNALS=True)
class MemberBirthdayTest(TestCase):
    fixtures = ["members.json"]

    def _make_date(self, date):
        return timezone.make_aware(datetime.strptime(date, "%Y-%m-%d"))

    def _get_members(self, start, end):
        start_date = self._make_date(start)
        end_date = self._make_date(end)
        return Member.current_members.with_birthdays_in_range(start_date, end_date)

    def _assert_none(self, start, end):
        members = self._get_members(start, end)
        self.assertEqual(len(members), 0)

    def _assert_thom(self, start, end):
        members = self._get_members(start, end)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0].get_full_name(), "Thom Wiggers")

    def test_one_year_contains_birthday(self):
        self._assert_thom("2016-03-02", "2016-08-08")

    def test_one_year_not_contains_birthday(self):
        self._assert_none("2016-01-01", "2016-02-01")

    def test_span_year_contains_birthday(self):
        self._assert_thom("2015-08-09", "2016-08-08")

    def test_span_year_not_contains_birthday(self):
        self._assert_none("2015-12-25", "2016-03-01")

    def test_span_multiple_years_contains_birthday(self):
        self._assert_thom("2012-12-31", "2016-01-01")

    def test_range_before_person_born(self):
        self._assert_none("1985-12-12", "1985-12-13")

    def test_person_born_in_range_in_one_year(self):
        self._assert_thom("1993-01-01", "1993-04-01")

    def test_person_born_in_range_spanning_one_year(self):
        self._assert_thom("1992-12-31", "1993-04-01")

    def test_person_born_in_range_spanning_multiple_years(self):
        self._assert_thom("1992-12-31", "1995-01-01")


@override_settings(SUSPEND_SIGNALS=True)
class MemberTest(TestCase):
    fixtures = ["members.json"]

    def test_has_been_member(self):
        member = Member.objects.get(pk=1)

        self.assertTrue(member.has_been_member())

        m1 = member.membership_set.all()[0]
        m1.type = "honorary"
        m1.save()
        self.assertFalse(member.has_been_member())

    def test_has_been_honorary_member(self):
        member = Member.objects.get(pk=1)

        self.assertFalse(member.has_been_honorary_member())

        m1 = member.membership_set.all()[0]
        m1.type = "honorary"
        m1.save()
        self.assertTrue(member.has_been_honorary_member())

    def test_memberships_grouped(self):
        member = Member.objects.get(pk=1)

        memberships = ["member", "benefactor", "member", "member"]
        lengths = [1, 1, 2]
        _set = member.membership_set

        to_check = []
        for m in memberships:
            membership = _set.next()
            membership.type = m
            to_check.append((membership.since, membership.type))
        _set.save()

        to_check = [list(group) for key, group in groupby(to_check, key=lambda x: x[1])]
        for check, length in zip(to_check, lengths):
            self.assertEqual(len(check), length, "Test is faulty")

        for grouped, check_grouped in zip(member.memberships_grouped(), to_check):
            self.assertEqual(len(grouped), len(check_grouped), "Group length is wrong")
            for membership, check_membership in zip(grouped, check_grouped):
                self.assertTrue(
                    membership.since == check_membership[0] and membership.type == check_membership[1],
                    "membership order was not maintained in groups"
                )


class MemberDisplayNameTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.create(
            username="johnnytest", first_name="", last_name=""
        )
        cls.profile = Profile.objects.create(
            user_id=cls.member.pk,
            initials=None,
            nickname=None,
            display_name_preference="full",
        )

    def setUp(self):
        self.profile.display_name_preference = "full"
        # Assuming we always have a first and last name
        self.profile.user.first_name = "Johnny"
        self.profile.user.last_name = "Test"
        self.profile.nickname = None
        self.profile.initials = None

    def test_check_display_name_full(self):
        self.assertEqual("Johnny Test", self.profile.display_name())
        self.assertEqual("Johnny", self.profile.short_display_name())

    def test_check_display_name_nickname(self):
        self.profile.display_name_preference = "nickname"
        self.assertEqual("Johnny Test", self.profile.display_name())
        self.assertEqual("Johnny", self.profile.short_display_name())
        self.profile.nickname = "John"
        self.assertEqual("'John'", self.profile.display_name())
        self.assertEqual("'John'", self.profile.short_display_name())

    def test_check_display_name_firstname(self):
        self.profile.display_name_preference = "firstname"
        self.assertEqual("Johnny", self.profile.display_name())
        self.assertEqual("Johnny", self.profile.short_display_name())

    def test_check_display_name_initials(self):
        self.profile.display_name_preference = "initials"
        self.assertEqual("Test", self.profile.display_name())
        self.assertEqual("Test", self.profile.short_display_name())
        self.profile.initials = "J"
        self.assertEqual("J Test", self.profile.display_name())
        self.assertEqual("J Test", self.profile.short_display_name())

    def test_check_display_name_fullnick(self):
        self.profile.display_name_preference = "fullnick"
        self.assertEqual("Johnny Test", self.profile.display_name())
        self.assertEqual("Johnny", self.profile.short_display_name())
        self.profile.nickname = "John"
        self.assertEqual("Johnny 'John' Test", self.profile.display_name())
        self.assertEqual("Johnny", self.profile.short_display_name())

    def test_check_display_name_nicklast(self):
        self.profile.display_name_preference = "nicklast"
        self.assertEqual("Johnny Test", self.profile.display_name())
        self.assertEqual("Johnny", self.profile.short_display_name())
        self.profile.nickname = "John"
        self.assertEqual("'John' Test", self.profile.display_name())
        self.assertEqual("'John'", self.profile.short_display_name())
