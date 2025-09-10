from django.test import TestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time

from members.apps import MembersConfig as Config
from members.models import Member, Membership, Profile


@freeze_time("2018-12-2")
@override_settings(SUSPEND_SIGNALS=True)
class DataMinimisationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m1 = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(user=cls.m1, student_number="s1234567")
        cls.s1 = Membership.objects.create(
            user=cls.m1,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=9, day=1),
        )
        cls.m2 = Member.objects.create(
            username="test2",
            first_name="Test2",
            last_name="Example",
            email="test2@example.org",
        )
        Profile.objects.create(user=cls.m2, student_number="s7654321")
        cls.s2 = Membership.objects.create(
            user=cls.m2,
            type=Membership.MEMBER,
            since=timezone.now().replace(year=2017, month=9, day=1),
            until=timezone.now().replace(year=2018, month=9, day=1),
        )

    def test_removes_after_31_days_or_no_membership(self):
        with self.subTest("Deletes after 90 days"):
            processed = Config.execute_data_minimisation(True)
            self.assertEqual(len(processed), 2)
            self.assertEqual(processed[0], self.m1)

        with self.subTest("Deletes after 90 days"):
            self.s1.until = timezone.now().replace(year=2018, month=11, day=1)
            self.s1.save()
            processed = Config.execute_data_minimisation(True)
            self.assertEqual(len(processed), 1)

        with self.subTest("Deletes when no memberships"):
            self.s1.delete()
            processed = Config.execute_data_minimisation(True)
            self.assertEqual(len(processed), 2)

    def test_provided_queryset(self):
        processed = Config.execute_data_minimisation(True, members=Member.objects)
        self.assertEqual(len(processed), 2)
        self.assertEqual(processed[0], self.m1)

    def test_does_not_affect_current_members(self):
        with self.subTest("Membership ends in future"):
            self.s1.until = timezone.now().replace(year=2019, month=9, day=1)
            self.s1.save()
            processed = Config.execute_data_minimisation(True)
            self.assertEqual(len(processed), 1)
        with self.subTest("Never ending membership"):
            self.s1.until = None
            self.s1.save()
            processed = Config.execute_data_minimisation(True)
            self.assertEqual(len(processed), 1)
            self.s1.until = timezone.now().replace(year=2018, month=9, day=1)
            self.s1.save()
        with self.subTest("Newer year membership after expired one"):
            m = Membership.objects.create(
                user=self.m1,
                type=Membership.MEMBER,
                since=timezone.now().replace(year=2018, month=9, day=10),
                until=timezone.now().replace(year=2019, month=8, day=31),
            )
            processed = Config.execute_data_minimisation(True)
            self.assertEqual(len(processed), 1)
            m.delete()
        with self.subTest("Newer study membership after expired one"):
            m = Membership.objects.create(
                user=self.m1,
                type=Membership.MEMBER,
                since=timezone.now().replace(year=2018, month=9, day=10),
                until=None,
            )
            processed = Config.execute_data_minimisation(True)
            self.assertEqual(len(processed), 1)
            m.delete()
