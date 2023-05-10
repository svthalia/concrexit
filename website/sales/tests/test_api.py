from unittest import mock

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from freezegun import freeze_time
from rest_framework.test import APIClient

from activemembers.models import Committee, MemberGroupMembership
from members.models import Member
from payments.models import Payment
from payments.services import create_payment
from sales import payables
from sales.models.order import Order, OrderItem
from sales.models.product import Product, ProductList
from sales.models.shift import SelfOrderPeriod, Shift


@freeze_time("2021-01-01")
class OrderAPITest(TestCase):
    fixtures = [
        "members.json",
        "bank_accounts.json",
        "member_groups.json",
        "products.json",
    ]

    @classmethod
    def setUpTestData(cls):
        """Create the following test data:

        o0: an empty order
        o1: an unpaid order of 2 beer
        o2: an order of 2 soda that doesn't need a payment
        o3: an unpaid order with 2 beer and 2 wine
        o4: a paid order with 2 wine
        o4: a paid order with 2 beer and 2 wine
        """
        payables.register()

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

        cls.cie = Committee.objects.get(pk=1)
        MemberGroupMembership.objects.create(group=cls.cie, member=cls.member)
        content_type = ContentType.objects.get_for_model(Order)
        permission1 = Permission.objects.get(
            content_type=content_type, codename="add_order"
        )
        permission2 = Permission.objects.get(
            content_type=content_type, codename="change_order"
        )
        permission3 = Permission.objects.get(
            content_type=content_type, codename="delete_order"
        )
        permission4 = Permission.objects.get(
            content_type=content_type, codename="view_order"
        )
        permission5 = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Shift), codename="view_shift"
        )
        cls.cie.permissions.add(permission1)
        cls.cie.permissions.add(permission2)
        cls.cie.permissions.add(permission3)
        cls.cie.permissions.add(permission4)
        cls.cie.permissions.add(permission5)

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(self.member)

    def test_detail_not_logged_in(self):
        self.client.logout()
        response = self.client.get(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o0.pk})
        )
        self.assertEqual(403, response.status_code)

    def test_detail_not_authorized__get(self):
        response = self.client.get(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o1.pk})
        )
        self.assertEqual(200, response.status_code)

        self.member.is_superuser = False
        self.member.save()

        response = self.client.get(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o1.pk})
        )
        self.assertEqual(404, response.status_code)

        self.shift.managers.add(self.cie)
        self.shift.save()

        response = self.client.get(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o1.pk})
        )
        self.assertEqual(200, response.status_code)

    def test_detail_not_authorized__patch(self):
        data = {"discount": "0.5"}

        response = self.client.patch(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o1.pk}), data
        )
        self.assertEqual(200, response.status_code)

        self.member.is_superuser = False
        self.member.save()

        response = self.client.patch(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o1.pk}), data
        )
        self.assertEqual(404, response.status_code)

        self.shift.managers.add(self.cie)
        self.shift.save()

        response = self.client.patch(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o1.pk}), data
        )
        self.assertEqual(200, response.status_code)

    def test_detail_not_authorized__put(self):
        data = {"discount": "0.5"}

        response = self.client.put(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o1.pk}), data
        )
        self.assertEqual(200, response.status_code)

        self.member.is_superuser = False
        self.member.save()

        response = self.client.put(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o1.pk}), data
        )
        self.assertEqual(404, response.status_code)

        self.shift.managers.add(self.cie)
        self.shift.save()

        response = self.client.put(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o1.pk}), data
        )
        self.assertEqual(200, response.status_code)

    def test_detail_not_authorized__delete(self):
        response = self.client.delete(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o1.pk})
        )
        self.assertEqual(204, response.status_code)

        self.member.is_superuser = False
        self.member.save()

        response = self.client.delete(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o2.pk})
        )
        self.assertEqual(404, response.status_code)

        self.shift.managers.add(self.cie)
        self.shift.save()

        response3 = self.client.delete(
            reverse("api:v2:admin:sales:order-detail", kwargs={"pk": self.o2.pk})
        )
        self.assertEqual(204, response3.status_code)

    def test_list_not_logged_in(self):
        self.client.logout()
        response = self.client.get(
            reverse("api:v2:admin:sales:shift-orders", kwargs={"pk": self.shift.pk})
        )
        self.assertEqual(403, response.status_code)

    def test_list_not_authorized__get(self):
        response = self.client.get(
            reverse("api:v2:admin:sales:shift-orders", kwargs={"pk": self.shift.pk})
        )
        self.assertEqual(200, response.status_code)

        self.member.is_superuser = False
        self.member.save()

        response = self.client.get(
            reverse("api:v2:admin:sales:shift-orders", kwargs={"pk": self.shift.pk})
        )
        self.assertEqual(403, response.status_code)

        self.shift.managers.add(self.cie)
        self.shift.save()

        response = self.client.get(
            reverse("api:v2:admin:sales:shift-orders", kwargs={"pk": self.shift.pk})
        )
        self.assertEqual(200, response.status_code)

    def test_list_not_authorized__post(self):
        data = {"order_items": [{"product": "beer", "amount": 4}]}

        response = self.client.post(
            reverse("api:v2:admin:sales:shift-orders", kwargs={"pk": self.shift.pk}),
            data,
        )
        self.assertEqual(201, response.status_code)

        self.member.is_superuser = False
        self.member.save()

        response = self.client.post(
            reverse("api:v2:admin:sales:shift-orders", kwargs={"pk": self.shift.pk}),
            data,
        )
        self.assertEqual(403, response.status_code)

        self.shift.managers.add(self.cie)
        self.shift.save()

        response = self.client.post(
            reverse("api:v2:admin:sales:shift-orders", kwargs={"pk": self.shift.pk}),
            data,
        )
        self.assertEqual(201, response.status_code)

    def test_create_order(self):
        self.maxDiff = None
        with self.subTest("Create new order with single item"):
            data = {"order_items": [{"product": "beer", "amount": 4}]}
            response = self.client.post(
                reverse(
                    "api:v2:admin:sales:shift-orders", kwargs={"pk": self.shift.pk}
                ),
                data,
                format="json",
            )
            self.assertEqual(201, response.status_code)
            pk = response.data["pk"]
            expected_response = {
                "pk": pk,
                "shift": self.shift.pk,
                "created_at": "2021-01-01T01:00:00+01:00",
                "order_items": [{"product": "beer", "amount": 4, "total": "2.00"}],
                "order_description": "4x beer",
                "age_restricted": True,
                "subtotal": "2.00",
                "discount": None,
                "total_amount": "2.00",
                "num_items": 4,
                "payment": None,
                "payer": None,
                "payment_url": f"http://localhost:8000/sales/order/{pk}/pay/",
            }
            self.assertJSONEqual(response.content, expected_response)

        with self.subTest("Add product item"):
            data = {
                "order_items": [
                    {"product": "beer", "amount": 5},
                    {"product": "soda", "amount": 2},
                ]
            }
            response = self.client.put(
                reverse("api:v2:admin:sales:order-detail", kwargs={"pk": pk}),
                data,
                format="json",
            )
            self.assertEqual(200, response.status_code)
            expected_response = {
                "pk": pk,
                "shift": self.shift.pk,
                "created_at": "2021-01-01T01:00:00+01:00",
                "order_items": [
                    {"product": "beer", "amount": 5, "total": "2.50"},
                    {"product": "soda", "amount": 2, "total": "0.00"},
                ],
                "order_description": "5x beer, 2x soda",
                "age_restricted": True,
                "subtotal": "2.50",
                "discount": None,
                "total_amount": "2.50",
                "num_items": 7,
                "payment": None,
                "payer": None,
                "payment_url": f"http://localhost:8000/sales/order/{pk}/pay/",
            }
            self.assertJSONEqual(response.content, expected_response)

        with self.subTest("Delete and add product item"):
            data = {
                "order_items": [
                    {"product": "wine", "amount": 1},
                    {"product": "soda", "amount": 2},
                ]
            }
            response = self.client.put(
                reverse("api:v2:admin:sales:order-detail", kwargs={"pk": pk}),
                data,
                format="json",
            )
            self.assertEqual(200, response.status_code)
            expected_response = {
                "pk": pk,
                "shift": self.shift.pk,
                "created_at": "2021-01-01T01:00:00+01:00",
                "order_items": [
                    {"product": "wine", "amount": 1, "total": "0.50"},
                    {"product": "soda", "amount": 2, "total": "0.00"},
                ],
                "order_description": "1x wine, 2x soda",
                "age_restricted": True,
                "subtotal": "0.50",
                "discount": None,
                "total_amount": "0.50",
                "num_items": 3,
                "payment": None,
                "payer": None,
                "payment_url": f"http://localhost:8000/sales/order/{pk}/pay/",
            }
            self.assertJSONEqual(response.content, expected_response)

        with self.subTest("Write discount"):
            data = {"discount": 0.2}
            response = self.client.patch(
                reverse("api:v2:admin:sales:order-detail", kwargs={"pk": pk}),
                data,
                format="json",
            )
            self.assertEqual(200, response.status_code)
            expected_response = {
                "pk": pk,
                "shift": self.shift.pk,
                "created_at": "2021-01-01T01:00:00+01:00",
                "order_items": [
                    {"product": "wine", "amount": 1, "total": "0.50"},
                    {"product": "soda", "amount": 2, "total": "0.00"},
                ],
                "order_description": "1x wine, 2x soda",
                "age_restricted": True,
                "subtotal": "0.50",
                "discount": "0.20",
                "total_amount": "0.30",
                "num_items": 3,
                "payment": None,
                "payer": None,
                "payment_url": f"http://localhost:8000/sales/order/{pk}/pay/",
            }
            self.assertJSONEqual(response.content, expected_response)

        with self.subTest("Reset discount"):
            data = {"discount": 0}
            response = self.client.patch(
                reverse("api:v2:admin:sales:order-detail", kwargs={"pk": pk}),
                data,
                format="json",
            )
            self.assertEqual(200, response.status_code)
            expected_response = {
                "pk": pk,
                "shift": self.shift.pk,
                "created_at": "2021-01-01T01:00:00+01:00",
                "order_items": [
                    {"product": "wine", "amount": 1, "total": "0.50"},
                    {"product": "soda", "amount": 2, "total": "0.00"},
                ],
                "order_description": "1x wine, 2x soda",
                "age_restricted": True,
                "subtotal": "0.50",
                "discount": "0.00",
                "total_amount": "0.50",
                "num_items": 3,
                "payment": None,
                "payer": None,
                "payment_url": f"http://localhost:8000/sales/order/{pk}/pay/",
            }
            self.assertJSONEqual(response.content, expected_response)

        with self.subTest("Override total field"):
            data = {
                "order_items": [
                    {"product": "wine", "amount": 1, "total": "1.30"},
                    {"product": "soda", "amount": 2, "total": "2.00"},
                ]
            }
            response = self.client.patch(
                reverse("api:v2:admin:sales:order-detail", kwargs={"pk": pk}),
                data,
                format="json",
            )
            self.assertEqual(200, response.status_code)
            expected_response = {
                "pk": pk,
                "shift": self.shift.pk,
                "created_at": "2021-01-01T01:00:00+01:00",
                "order_items": [
                    {"product": "wine", "amount": 1, "total": "1.30"},
                    {"product": "soda", "amount": 2, "total": "2.00"},
                ],
                "order_description": "1x wine, 2x soda",
                "age_restricted": True,
                "subtotal": "3.30",
                "discount": "0.00",
                "total_amount": "3.30",
                "num_items": 3,
                "payment": None,
                "payer": None,
                "payment_url": f"http://localhost:8000/sales/order/{pk}/pay/",
            }
            self.assertJSONEqual(response.content, expected_response)

        with self.subTest("Reset overridden total fields"):
            data = {
                "order_items": [
                    {"product": "wine", "amount": 1},
                    {"product": "soda", "amount": 2},
                ]
            }
            response = self.client.patch(
                reverse("api:v2:admin:sales:order-detail", kwargs={"pk": pk}),
                data,
                format="json",
            )
            self.assertEqual(200, response.status_code)
            expected_response = {
                "pk": pk,
                "shift": self.shift.pk,
                "created_at": "2021-01-01T01:00:00+01:00",
                "order_items": [
                    {"product": "wine", "amount": 1, "total": "0.50"},
                    {"product": "soda", "amount": 2, "total": "0.00"},
                ],
                "order_description": "1x wine, 2x soda",
                "age_restricted": True,
                "subtotal": "0.50",
                "discount": "0.00",
                "total_amount": "0.50",
                "num_items": 3,
                "payment": None,
                "payer": None,
                "payment_url": f"http://localhost:8000/sales/order/{pk}/pay/",
            }
            self.assertJSONEqual(response.content, expected_response)

        with self.subTest("Write discount without custom price permissions"):
            self.member.is_superuser = False
            self.member.save()
            self.shift.managers.add(self.cie)
            self.shift.save()

            data = {"discount": 0.2}
            response = self.client.patch(
                reverse("api:v2:admin:sales:order-detail", kwargs={"pk": pk}),
                data,
                format="json",
            )
            self.assertEqual(200, response.status_code)
            expected_response = {
                "pk": pk,
                "shift": self.shift.pk,
                "created_at": "2021-01-01T01:00:00+01:00",
                "order_items": [
                    {"product": "wine", "amount": 1, "total": "0.50"},
                    {"product": "soda", "amount": 2, "total": "0.00"},
                ],
                "order_description": "1x wine, 2x soda",
                "age_restricted": True,
                "subtotal": "0.50",
                "discount": "0.00",
                "total_amount": "0.50",
                "num_items": 3,
                "payment": None,
                "payer": None,
                "payment_url": f"http://localhost:8000/sales/order/{pk}/pay/",
            }
            self.assertJSONEqual(response.content, expected_response)

        with self.subTest("Write total field without custom price permissions"):
            data = {
                "order_items": [
                    {"product": "wine", "amount": 1, "total": "1.30"},
                    {"product": "soda", "amount": 2, "total": "2.00"},
                ]
            }
            response = self.client.patch(
                reverse("api:v2:admin:sales:order-detail", kwargs={"pk": pk}),
                data,
                format="json",
            )
            self.assertEqual(200, response.status_code)
            expected_response = {
                "pk": pk,
                "shift": self.shift.pk,
                "created_at": "2021-01-01T01:00:00+01:00",
                "order_items": [
                    {"product": "wine", "amount": 1, "total": "0.50"},
                    {"product": "soda", "amount": 2, "total": "0.00"},
                ],
                "order_description": "1x wine, 2x soda",
                "age_restricted": True,
                "subtotal": "0.50",
                "discount": "0.00",
                "total_amount": "0.50",
                "num_items": 3,
                "payment": None,
                "payer": None,
                "payment_url": f"http://localhost:8000/sales/order/{pk}/pay/",
            }
            self.assertJSONEqual(response.content, expected_response)

        with self.subTest("Delete one product item"):
            data = {
                "order_items": [
                    {"product": "wine", "amount": 1},
                ]
            }
            response = self.client.patch(
                reverse("api:v2:admin:sales:order-detail", kwargs={"pk": pk}),
                data,
                format="json",
            )
            self.assertEqual(200, response.status_code)
            expected_response = {
                "pk": pk,
                "shift": self.shift.pk,
                "created_at": "2021-01-01T01:00:00+01:00",
                "order_items": [
                    {"product": "wine", "amount": 1, "total": "0.50"},
                ],
                "order_description": "1x wine",
                "age_restricted": True,
                "subtotal": "0.50",
                "discount": "0.00",
                "total_amount": "0.50",
                "num_items": 1,
                "payment": None,
                "payer": None,
                "payment_url": f"http://localhost:8000/sales/order/{pk}/pay/",
            }
            self.assertJSONEqual(response.content, expected_response)

    def test_invalid_product(self):
        data = {"order_items": [{"product": "invalidproduct", "amount": 4}]}
        response = self.client.post(
            reverse("api:v2:admin:sales:shift-orders", kwargs={"pk": self.shift.pk}),
            data,
            format="json",
        )
        self.assertEqual(400, response.status_code)

    def test_user_self_order(self):
        SelfOrderPeriod.objects.create(
            shift=self.shift,
            start=(timezone.now() - timezone.timedelta(hours=1)),
            end=timezone.now() + timezone.timedelta(hours=1),
        )
        data = {"order_items": [{"product": "beer", "amount": 4}]}
        response = self.client.post(
            reverse("api:v2:sales:user-order-list", kwargs={"pk": self.shift.pk}),
            data,
            format="json",
        )
        self.assertEqual(201, response.status_code)
        order = Order.objects.get(pk=response.data["pk"])
        self.assertEqual(order.payer, self.member)

    def test_claim_order(self):
        with self.subTest("Claim a normal order"):
            response = self.client.patch(
                reverse("api:v2:sales:order-claim", kwargs={"pk": self.o3.pk})
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual(
                Order.objects.get(pk=response.data["pk"]).payer, self.member
            )

        self.o3.payer = None
        self.o3.save()

        with self.subTest("Claim an order that is already yours"):
            self.o3.payer = self.member
            self.o3.save()

            response = self.client.patch(
                reverse("api:v2:sales:order-claim", kwargs={"pk": self.o3.pk})
            )
            self.assertEqual(200, response.status_code)
            self.assertEqual(
                Order.objects.get(pk=response.data["pk"]).payer, self.member
            )

        self.o3.payer = None
        self.o3.save()

        with self.subTest("Claim an order that is not yours"):
            member = Member.objects.create(
                username="test1",
                first_name="Test1",
                last_name="Example",
                email="test1@example.org",
                is_staff=False,
                is_superuser=False,
            )
            self.o3.payer = member
            self.o3.save()

            response = self.client.patch(
                reverse("api:v2:sales:order-claim", kwargs={"pk": self.o3.pk})
            )
            self.assertEqual(403, response.status_code)
            self.o3.refresh_from_db()
            self.assertEqual(self.o3.payer, member)

        self.o3.payer = None
        self.o3.save()

        with self.subTest("Claim a paid order"):
            response = self.client.patch(
                reverse("api:v2:sales:order-claim", kwargs={"pk": self.o4.pk})
            )
            self.assertEqual(403, response.status_code)

        self.o3.payer = None
        self.o3.save()

        with self.subTest("Claim an age-restricted order as a minor"):
            with mock.patch("sales.services.is_adult") as is_adult:
                is_adult.return_value = False
                response = self.client.patch(
                    reverse("api:v2:sales:order-claim", kwargs={"pk": self.o3.pk})
                )
                self.assertEqual(403, response.status_code)
                self.o3.refresh_from_db()
                self.assertEqual(self.o3.payer, self.member)


class ShiftAPITest(TestCase):
    fixtures = [
        "members.json",
        "bank_accounts.json",
        "member_groups.json",
        "products.json",
    ]

    @classmethod
    def setUpTestData(cls):
        """Create the following test data:

        o0: an empty order
        o1: an unpaid order of 2 beer
        o2: an order of 2 soda that doesn't need a payment
        o3: an unpaid order with 2 beer and 2 wine
        o4: a paid order with 2 wine
        o4: a paid order with 2 beer and 2 wine
        """
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

        cls.shift2 = Shift.objects.create(
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=1),
            product_list=cls.free,
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

        cls.cie = Committee.objects.get(pk=1)
        MemberGroupMembership.objects.create(group=cls.cie, member=cls.member)
        content_type = ContentType.objects.get_for_model(Order)
        permission1 = Permission.objects.get(
            content_type=content_type, codename="add_order"
        )
        permission2 = Permission.objects.get(
            content_type=content_type, codename="change_order"
        )
        permission3 = Permission.objects.get(
            content_type=content_type, codename="delete_order"
        )
        permission4 = Permission.objects.get(
            content_type=content_type, codename="view_order"
        )
        permission5 = Permission.objects.get(
            content_type=ContentType.objects.get_for_model(Shift), codename="view_shift"
        )
        cls.cie.permissions.add(permission1)
        cls.cie.permissions.add(permission2)
        cls.cie.permissions.add(permission3)
        cls.cie.permissions.add(permission4)
        cls.cie.permissions.add(permission5)

    def setUp(self):
        self.client = APIClient()
        self.client.force_login(self.member)

    def test_detail_not_logged_in(self):
        self.client.logout()
        response = self.client.get(
            reverse("api:v2:admin:sales:shift-detail", kwargs={"pk": self.shift.pk})
        )
        self.assertEqual(403, response.status_code)

    def test_detail_not_authorized__get(self):
        response = self.client.get(
            reverse("api:v2:admin:sales:shift-detail", kwargs={"pk": self.shift.pk})
        )
        self.assertEqual(200, response.status_code)

        self.member.is_superuser = False
        self.member.save()

        response = self.client.get(
            reverse("api:v2:admin:sales:shift-detail", kwargs={"pk": self.shift.pk})
        )
        self.assertEqual(403, response.status_code)

        self.shift.managers.add(self.cie)
        self.shift.save()

        response = self.client.get(
            reverse("api:v2:admin:sales:shift-detail", kwargs={"pk": self.shift.pk})
        )
        self.assertEqual(200, response.status_code)

    def test_list_not_logged_in(self):
        self.client.logout()
        response = self.client.get(reverse("api:v2:admin:sales:shift-list"))
        self.assertEqual(403, response.status_code)

    def test_list_not_authorized__get(self):
        response = self.client.get(reverse("api:v2:admin:sales:shift-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.data["count"])

        self.member.is_superuser = False
        self.member.save()

        response = self.client.get(reverse("api:v2:admin:sales:shift-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(0, response.data["count"])

        self.shift.managers.add(self.cie)
        self.shift.save()

        response = self.client.get(reverse("api:v2:admin:sales:shift-list"))
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.data["count"])
