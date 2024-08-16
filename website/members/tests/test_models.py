from datetime import datetime

from django.test import TestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time

from members.models import Member, Profile
from members.models.membership import Membership


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

    def test_membership_properties(self):
        member = Member.objects.get(pk=1)
        member.membership_set.all().delete()

        old_membership = Membership.objects.create(
            user=member,
            since="2022-09-01",
            until="2023-09-01",
            type=Membership.MEMBER,
        )
        middle_membership = Membership.objects.create(
            user=member,
            since="2023-09-01",
            until="2024-09-01",
            type=Membership.MEMBER,
        )
        latest_membership = Membership.objects.create(
            user=member,
            since="2024-09-01",
            until="2025-09-01",
            type=Membership.MEMBER,
        )

        with freeze_time("2022-08-25"):
            member.refresh_from_db()
            self.assertFalse(member.has_active_membership())
            self.assertIsNone(member.current_membership)
            self.assertEqual(member.latest_membership, latest_membership)

        with freeze_time("2022-09-01"):
            member.refresh_from_db()
            self.assertTrue(member.has_active_membership())
            self.assertEqual(member.current_membership, old_membership)
            self.assertEqual(member.latest_membership, latest_membership)

        with freeze_time("2024-08-25"):
            # A membership has been renewed before the end of the current one.
            member.refresh_from_db()
            self.assertTrue(member.has_active_membership())
            self.assertEqual(member.current_membership, middle_membership)
            self.assertEqual(member.latest_membership, latest_membership)

        with freeze_time("2024-09-01"):
            member.refresh_from_db()
            self.assertTrue(member.has_active_membership())
            self.assertEqual(member.current_membership, latest_membership)
            self.assertEqual(member.latest_membership, latest_membership)

        with freeze_time("2025-09-01"):
            member.refresh_from_db()
            self.assertFalse(member.has_active_membership())
            self.assertIsNone(member.current_membership)
            self.assertEqual(member.latest_membership, latest_membership)


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
