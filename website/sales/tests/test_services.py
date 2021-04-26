import datetime
from django.test import TestCase

from freezegun import freeze_time

from members.models import Member, Profile
from sales import services


class SalesServicesTest(TestCase):
    @freeze_time("2021-01-01")
    def test_adult_member(self):
        member = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
            is_staff=False,
            is_superuser=False,
        )
        Profile.objects.create(
            user=member,
            birthday=datetime.datetime.strptime("2003-01-01", "%Y-%m-%d").date(),
        )

        self.assertTrue(services.is_adult(member))

    @freeze_time("2021-01-01")
    def test_underage_member(self):
        member = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
            is_staff=False,
            is_superuser=False,
        )
        Profile.objects.create(
            user=member,
            birthday=datetime.datetime.strptime("2003-01-02", "%Y-%m-%d").date(),
        )

        self.assertFalse(services.is_adult(member))
