import datetime
from unittest.mock import MagicMock

from django.test import TestCase
from django.utils import timezone

from freezegun import freeze_time

from activemembers.models import Committee, MemberGroupMembership
from members.models import Member, Profile
from sales import services
from sales.models.product import Product, ProductList
from sales.models.shift import Shift
from sales.services import is_manager


@freeze_time("2021-01-01")
class SalesServicesTest(TestCase):
    fixtures = ["members.json", "member_groups.json", "products.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(last_name="Wiggers").first()

        cls.beer = Product.objects.get(name="beer")
        cls.wine = Product.objects.get(name="wine")
        cls.soda = Product.objects.get(name="soda")

        cls.normal = ProductList.objects.get(
            name="normal",
        )
        cls.free = ProductList.objects.get(
            name="free",
        )

        cls.shift = Shift.objects.create(
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=1),
            product_list=cls.normal,
        )

    def test_adult_member(self):
        Profile.objects.filter(user=self.member).update(
            birthday=datetime.datetime.strptime("2003-01-01", "%Y-%m-%d").date(),
        )

        self.assertTrue(services.is_adult(self.member))

    def test_underage_member(self):
        Profile.objects.filter(user=self.member).update(
            birthday=datetime.datetime.strptime("2003-01-02", "%Y-%m-%d").date(),
        )

        self.assertFalse(services.is_adult(self.member))

    def test_is_manager(self):
        self.member.is_superuser = False
        self.assertFalse(is_manager(self.member, self.shift))

        cie = Committee.objects.get(pk=1)
        MemberGroupMembership.objects.create(group=cie, member=self.member)
        self.shift.managers.add(cie)
        self.assertTrue(is_manager(self.member, self.shift))

        self.shift.managers.remove(cie)
        self.assertFalse(is_manager(self.member, self.shift))

        self.member.is_superuser = True
        self.assertTrue(is_manager(self.member, self.shift))
        self.member.is_superuser = False
        self.member.has_perm = MagicMock()
        self.member.has_perm.return_value = True
        self.assertTrue(is_manager(self.member, self.shift))
