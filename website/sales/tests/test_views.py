from unittest import mock

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from freezegun import freeze_time

from members.models import Member
from payments.models import Payment
from payments.services import create_payment
from sales.models.order import OrderItem, Order
from sales.models.product import Product, ProductList, ProductListItem
from sales.models.shift import Shift


@freeze_time("2019-01-01")
class SalesOrderPaymentView(TestCase):

    fixtures = ["members.json", "bank_accounts.json", "member_groups.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(last_name="Wiggers").first()

        cls.beer = Product.objects.create(name="beer", age_restricted=True)
        cls.wine = Product.objects.create(name="wine", age_restricted=True)
        cls.soda = Product.objects.create(name="soda", age_restricted=False)

        cls.normal = ProductList.objects.create(
            name="normal",
        )
        cls.free = ProductList.objects.create(
            name="free",
        )

        cls.normal.product_items.bulk_create(
            [
                ProductListItem(product=cls.beer, product_list=cls.normal, price=0.50),
                ProductListItem(product=cls.wine, product_list=cls.normal, price=0.50),
                ProductListItem(product=cls.soda, product_list=cls.normal, price=0.00),
            ]
        )
        cls.free.product_items.bulk_create(
            [
                ProductListItem(product=cls.beer, product_list=cls.free, price=0.00),
                ProductListItem(product=cls.wine, product_list=cls.free, price=0.00),
                ProductListItem(product=cls.soda, product_list=cls.free, price=0.00),
            ]
        )

        cls.shift = Shift.objects.create(
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=1),
            product_list=cls.normal,
        )

        cls.o0 = Order.objects.create(shift=cls.shift)
        cls.o1 = Order.objects.create(shift=cls.shift)
        OrderItem.objects.create(
            order=cls.o1,
            product=cls.shift.product_list.product_items.get(product=cls.beer),
            amount=2,
        )
        cls.o2 = Order.objects.create(shift=cls.shift)
        OrderItem.objects.create(
            order=cls.o2,
            product=cls.shift.product_list.product_items.get(product=cls.soda),
            amount=2,
        )
        cls.o3 = Order.objects.create(shift=cls.shift)
        OrderItem.objects.create(
            order=cls.o3,
            product=cls.shift.product_list.product_items.get(product=cls.beer),
            amount=2,
        )
        OrderItem.objects.create(
            order=cls.o3,
            product=cls.shift.product_list.product_items.get(product=cls.wine),
            amount=2,
        )
        cls.o4 = Order.objects.create(shift=cls.shift)
        OrderItem.objects.create(
            order=cls.o4,
            product=cls.shift.product_list.product_items.get(product=cls.wine),
            amount=2,
        )
        cls.o5 = Order.objects.create(shift=cls.shift)
        OrderItem.objects.create(
            order=cls.o5,
            product=cls.shift.product_list.product_items.get(product=cls.beer),
            amount=2,
        )
        OrderItem.objects.create(
            order=cls.o5,
            product=cls.shift.product_list.product_items.get(product=cls.wine),
            amount=2,
        )
        cls.o4.payment = create_payment(
            cls.o4, processed_by=cls.member, pay_type=Payment.CASH
        )
        cls.o4.save()
        cls.o5.payment = create_payment(
            cls.o5, processed_by=cls.member, pay_type=Payment.CASH
        )
        cls.o5.save()
        cls.o6 = Order.objects.create(shift=cls.shift)
        OrderItem.objects.create(
            order=cls.o6,
            product=cls.shift.product_list.product_items.get(product=cls.soda),
            amount=2,
            total=1,
        )

        """
        o0: an empty order
        o1: an unpaid order of 2 beer
        o2: an order of 2 soda that doesn't need a payment
        o3: an unpaid order with 2 beer and 2 wine
        o4: a paid order with 2 wine
        o5: a paid order with 2 beer and 2 wine
        o6: an unpaid order of 2 soda that does need a payment (custom)
        """

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.member)

    def test_not_logged_in(self):
        self.client.logout()

        response = self.client.get(
            reverse("sales:order-pay", kwargs={"pk": self.o1.pk}), follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [
                (
                    "/user/login/?next="
                    + reverse("sales:order-pay", kwargs={"pk": self.o1.pk}),
                    302,
                )
            ],
            response.redirect_chain,
        )

    def test_paid_order(self):
        response = self.client.get(
            reverse("sales:order-pay", kwargs={"pk": self.o4.pk}), follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [("/", 302)],
            response.redirect_chain,
        )

    def test_other_persons_order(self):
        member = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
            is_staff=False,
            is_superuser=False,
        )
        self.o1.payer = member
        self.o1.save()

        response = self.client.get(
            reverse("sales:order-pay", kwargs={"pk": self.o1.pk}), follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [("/", 302)],
            response.redirect_chain,
        )

    def test_empty_order(self):
        response = self.client.get(
            reverse("sales:order-pay", kwargs={"pk": self.o0.pk}), follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [("/", 302)],
            response.redirect_chain,
        )

    def test_free_order(self):
        response = self.client.get(
            reverse("sales:order-pay", kwargs={"pk": self.o2.pk}), follow=True
        )
        self.assertEqual(200, response.status_code)
        self.assertEqual(
            [("/", 302)],
            response.redirect_chain,
        )
        self.o2.refresh_from_db()
        self.assertEqual(self.o2.payer, self.member)

    def test_age_restricted_order__unauthorized(self):
        with mock.patch("sales.services.is_adult") as is_adult:
            is_adult.return_value = False
            response = self.client.get(
                reverse("sales:order-pay", kwargs={"pk": self.o1.pk}), follow=True
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual(
                [("/", 302)],
                response.redirect_chain,
            )
            self.o1.refresh_from_db()
            self.assertEqual(self.o1.payer, self.member)

    def test_age_restricted_order__okay(self):
        with mock.patch("sales.services.is_adult") as is_adult:
            is_adult.return_value = False
            response = self.client.get(
                reverse("sales:order-pay", kwargs={"pk": self.o6.pk}), follow=False
            )
            self.assertEqual(200, response.status_code)
            self.o6.refresh_from_db()
            self.assertEqual(self.o6.payer, self.member)

    def test_normal(self):
        with mock.patch("sales.services.is_adult") as is_adult:
            is_adult.return_value = True
            response = self.client.get(
                reverse("sales:order-pay", kwargs={"pk": self.o1.pk}), follow=False
            )
            self.assertEqual(200, response.status_code)
            self.o1.refresh_from_db()
            self.assertEqual(self.o1.payer, self.member)
