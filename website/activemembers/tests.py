from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone

from activemembers.models import Board, Committee, MemberGroupMembership
from mailinglists.models import MailingList
from members.models import Member


@override_settings(SUSPEND_SIGNALS=True)
class CommitteeMembersTest(TestCase):
    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.testcie = Committee.objects.get(pk=1)
        cls.testuser = Member.objects.get(pk=1)
        cls.m = MemberGroupMembership.objects.create(
            group=cls.testcie, member=cls.testuser, chair=False
        )

    def setUp(self):
        self.testcie.refresh_from_db()
        self.testuser.refresh_from_db()
        self.m.refresh_from_db()

    def test_unique(self):
        with self.assertRaises(IntegrityError):
            Committee.objects.create(
                name="testcie1",
                description="desc3",
                photo="",
            )

    def test_join(self):
        testuser2 = Member.objects.get(pk=2)
        m = MemberGroupMembership(group=self.testcie, member=testuser2)
        m.full_clean()
        m.save()

    def test_join_unique(self):
        m = MemberGroupMembership(group=self.testcie, member=self.testuser)
        with self.assertRaises(ValidationError):
            m.full_clean()

    def test_join_unique2(self):
        m = MemberGroupMembership(
            group=self.testcie,
            member=self.testuser,
            since=timezone.now().date().replace(year=2014, month=1),
        )
        with self.assertRaises(ValidationError):
            m.full_clean()

    def test_join_unique_period(self):
        m1 = MemberGroupMembership(
            group=self.testcie,
            member=self.testuser,
            since=timezone.now().date().replace(year=2014, month=1, day=1),
            until=timezone.now().date().replace(year=2014, month=3, day=1),
        )
        m1.save()

        m2 = MemberGroupMembership(
            group=self.testcie,
            member=self.testuser,
            since=timezone.now().date().replace(year=2014, month=1, day=1),
            until=timezone.now().date().replace(year=2014, month=2, day=1),
        )
        with self.assertRaises(ValidationError):
            m2.full_clean()

    def test_until_date(self):
        m = MemberGroupMembership(
            group=self.testcie,
            member=self.testuser,
            until=timezone.now().date().replace(year=2000),
            chair=False,
        )
        with self.assertRaises(ValidationError):
            m.clean()
        m.since = timezone.now().date().replace(year=1900)
        m.clean()

    def test_inactive(self):
        self.assertTrue(self.m.is_active)
        self.m.until = timezone.now().date().replace(year=1900)
        self.assertFalse(self.m.is_active)


@override_settings(SUSPEND_SIGNALS=True)
class CommitteeMembersChairTest(TestCase):
    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.testcie = Committee.objects.get(pk=1)
        cls.testuser = Member.objects.get(pk=1)
        cls.testuser2 = Member.objects.get(pk=2)

    def setUp(self):
        self.m1 = MemberGroupMembership(
            group=self.testcie,
            since=timezone.now().date().replace(day=1, year=1900),
            member=self.testuser,
            chair=True,
        )
        self.m1.full_clean()
        self.m1.save()

    def test_second_chair_fails(self):
        m = MemberGroupMembership(group=self.testcie, member=self.testuser2, chair=True)
        with self.assertRaises(ValidationError):
            m.full_clean()

    def test_inactive_chair(self):
        self.m1.until = timezone.now().date().replace(day=1, year=1900)
        self.m1.save()

        m = MemberGroupMembership(group=self.testcie, member=self.testuser2, chair=True)
        m.full_clean()

    def test_clean_self_chair(self):
        self.m1.chair = True
        self.m1.full_clean()


@override_settings(SUSPEND_SIGNALS=True)
class PermissionsBackendTest(TestCase):
    fixtures = ["members.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.u1 = Member.objects.get(pk=1)
        cls.u1.is_superuser = False
        cls.u1.save()
        cls.u2 = Member.objects.get(pk=2)
        cls.u3 = Member.objects.get(pk=3)
        cls.c1 = Committee.objects.get(pk=1)
        cls.c2 = Committee.objects.get(pk=2)
        cls.m1 = MemberGroupMembership.objects.create(group=cls.c1, member=cls.u1)
        cls.m2 = MemberGroupMembership.objects.create(group=cls.c2, member=cls.u2)

    def test_permissions(self):
        self.assertEqual(3, len(self.u1.get_all_permissions()))
        self.assertEqual(set(), self.u2.get_all_permissions())
        self.assertEqual(set(), self.u3.get_all_permissions())

    def test_nonmember_user(self):
        u = get_user_model().objects.create(username="foo")
        self.assertEqual(set(), u.get_all_permissions())


class CommitteeMailingListTest(TestCase):
    fixtures = ["mailinglists.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.testcie1 = Committee.objects.get(pk=1)
        cls.testcie2 = Committee.objects.get(pk=2)
        cls.mailtest1 = MailingList.objects.get(pk=1)
        cls.mailtest2 = MailingList.objects.get(pk=2)

    def setUp(self):
        self.testcie1.refresh_from_db()
        self.testcie2.refresh_from_db()
        self.mailtest1.refresh_from_db()
        self.mailtest2.refresh_from_db()

    def test_one_to_one(self):
        self.testcie1.contact_mailinglist = self.mailtest1
        self.testcie1.save()

        self.testcie2.contact_mailinglist = self.mailtest1

        with self.assertRaises(ValidationError):
            self.testcie2.full_clean()

        self.testcie2.contact_mailinglist = self.mailtest2

        self.testcie2.full_clean()

    def test_exactly_one_address(self):
        with self.assertRaises(ValidationError):
            self.testcie1.contact_mailinglist = self.mailtest1
            self.testcie1.contact_email = "test@test.com"
            self.testcie1.full_clean()

        with self.assertRaises(ValidationError):
            self.testcie1.contact_mailinglist = None
            self.testcie1.contact_email = None
            self.testcie1.full_clean()

        self.testcie1.contact_mailinglist = self.mailtest1
        self.testcie1.contact_email = None
        self.testcie1.full_clean()

        self.testcie1.contact_mailinglist = None
        self.testcie1.contact_email = "test@test.com"
        self.testcie1.full_clean()


class BoardTest(TestCase):
    fixtures = ["member_groups.json"]

    def setUp(self):
        self.testboard = Board.objects.get(pk=3)

    def test_validate_unique_works(self):
        self.testboard.validate_unique()
        self.testboard.until = None
        self.testboard.validate_unique()
        self.testboard.since = None
        self.testboard.validate_unique()

    def test_create_unique_period1(self):
        """Check uniqueness with since before period of testboard."""
        b = Board(
            name="testbo",
            contact_email="board@example.org",
            description="descen",
            since=timezone.now().date().replace(year=1990, month=2, day=1),
            until=timezone.now().date().replace(year=1990, month=9, day=1),
        )

        with self.assertRaises(ValidationError):
            b.full_clean()

        b.until = b.until.replace(year=1990, month=8, day=31)
        b.full_clean()

        b.until = None
        with self.assertRaises(ValidationError):
            b.full_clean()

    def test_create_unique_period2(self):
        """Check uniqueness with until after period of testboard."""
        b = Board(
            name="testbo",
            contact_email="board@example.org",
            description="descen",
            since=timezone.now().date().replace(year=1991, month=8, day=1),
            until=timezone.now().date().replace(year=1992, month=9, day=1),
        )

        with self.assertRaises(ValidationError):
            b.full_clean()

        b.since = b.since.replace(year=1991, month=9, day=2)
        b.full_clean()

    def test_get_absolute_url(self):
        self.testboard.get_absolute_url()
