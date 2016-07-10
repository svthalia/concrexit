from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from django.test import TestCase
from django.utils import timezone

from committees.models import Committee, CommitteeMembership
from members.models import Member


class CommitteeMembersTest(TestCase):
    fixtures = ['members.json', 'committees.json']

    @classmethod
    def setUpTestData(cls):
        cls.testcie = Committee.objects.get(name='testcie1')
        cls.testuser = Member.objects.get(pk=1)

        cls.m = CommitteeMembership(committee=cls.testcie,
                                    member=cls.testuser,
                                    chair=False)
        cls.m.save()

    def test_unique(self):
        with self.assertRaises(IntegrityError):
            Committee.objects.create(name="testcie1",
                                     description="desc3",
                                     photo="")

    def test_join(self):
        testuser2 = Member.objects.get(pk=2)
        m = CommitteeMembership(committee=self.testcie,
                                member=testuser2)
        m.full_clean()
        m.save()

    def test_join_unique(self):
        m = CommitteeMembership(committee=self.testcie,
                                member=self.testuser)
        with self.assertRaises(ValidationError):
            m.full_clean()

    def test_until_date(self):
        m = CommitteeMembership(committee=self.testcie,
                                member=self.testuser,
                                until=timezone.now().replace(year=2000),
                                chair=False)
        with self.assertRaises(ValidationError):
            m.clean()
        m.since = timezone.now().replace(year=1900)
        m.clean()

    def test_inactive(self):
        self.assertTrue(self.m.is_active)
        self.m.until = timezone.now().replace(year=1900)
        self.assertFalse(self.m.is_active)


class CommitteeMembersChairTest(TestCase):
    fixtures = ['members.json', 'committees.json']

    @classmethod
    def setUpTestData(cls):
        testcie = Committee.objects.get(name='testcie1')
        testuser = Member.objects.get(pk=1)
        cls.m1 = CommitteeMembership(committee=testcie,
                                     member=testuser,
                                     chair=True)
        cls.m1.full_clean()
        cls.m1.save()

    def setUp(self):
        self.testcie = Committee.objects.get(name='testcie1')
        self.testuser = Member.objects.get(pk=1)

    def test_second_chair_fails(self):
        testuser2 = Member.objects.get(pk=2)

        m = CommitteeMembership(committee=self.testcie,
                                member=testuser2,
                                chair=True)
        with self.assertRaises(ValidationError):
            m.full_clean()

    def test_inactive_chair(self):
        testuser2 = Member.objects.get(pk=2)
        self.m1.until = timezone.now().replace(year=1900)
        self.m1.save()
        m = CommitteeMembership(committee=self.testcie,
                                member=testuser2,
                                chair=True)
        m.full_clean()


class BackendTest(TestCase):
    fixtures = ['members.json', 'committees.json']

    @classmethod
    def setUpTestData(cls):
        cls.u1 = Member.objects.get(pk=1)
        cls.u1.user.is_superuser = False
        cls.u1.save()
        cls.u2 = Member.objects.get(pk=2)
        cls.u3 = Member.objects.get(pk=3)
        cls.c1 = Committee.objects.get(pk=1)
        cls.c2 = Committee.objects.get(pk=2)
        cls.m1 = CommitteeMembership.objects.create(committee=cls.c1,
                                                    member=cls.u1)
        cls.m2 = CommitteeMembership.objects.create(committee=cls.c2,
                                                    member=cls.u2)

    def test_permissions(self):
        self.assertEqual(3, len(self.u1.user.get_all_permissions()))
        self.assertEqual(set(), self.u2.user.get_all_permissions())
        self.assertEqual(set(), self.u3.user.get_all_permissions())

    def test_nonmember_user(self):
        u = get_user_model().objects.create(username='foo')
        self.assertEqual(set(), u.get_all_permissions())
