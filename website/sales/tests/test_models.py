from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time

from activemembers.models import Committee, MemberGroupMembership
from members.models import Member
from payments import PaymentError
from payments.models import Payment
from payments.services import create_payment
from sales.models.order import Order, OrderItem
from sales.models.product import Product, ProductList, ProductListItem
from sales.models.shift import Shift
from sales.services import is_manager


class ProductTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.beer = Product.objects.create(name="beer", age_restricted=True)
        cls.wine = Product.objects.create(name="wine", age_restricted=True)
        cls.soda = Product.objects.create(name="soda", age_restricted=False)

    def test_str(self):
        self.assertEqual("beer", str(self.beer))
        self.assertEqual("wine", str(self.wine))
        self.assertEqual("soda", str(self.soda))


class ProductListTest(TestCase):
    fixtures = ["members.json", "products.json"]

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

    def test_str(self):
        self.assertEqual("normal", str(self.normal))
        self.assertEqual("free", str(self.free))


@freeze_time("2021-01-01")
class OrderTest(TestCase):
    fixtures = ["members.json", "bank_accounts.json", "products.json"]

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

    def test_age_restricted(self):
        order = Order.objects.create(shift=self.shift)
        self.assertFalse(order.age_restricted)
        i1 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.soda),
            amount=1,
        )
        self.assertFalse(order.age_restricted)
        i2 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=1,
        )
        self.assertTrue(order.age_restricted)
        i2.delete()
        self.assertFalse(order.age_restricted)

    def test_subtotal(self):
        order = Order.objects.create(shift=self.shift)
        self.assertEqual(order.subtotal, 0)
        i1 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.soda),
            amount=2,
        )
        self.assertEqual(order.subtotal, 0)
        i2 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        self.assertEqual(order.subtotal, 1)
        i3 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.wine),
            amount=3,
        )
        self.assertEqual(order.subtotal, 2.5)
        i2.delete()
        self.assertEqual(order.subtotal, 1.5)
        i3.total = 4
        i3.save()
        self.assertEqual(order.subtotal, 4)

    def test_total_amount(self):
        order = Order.objects.create(shift=self.shift)
        self.assertEqual(order.total_amount, 0)
        i1 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.soda),
            amount=2,
        )
        self.assertEqual(order.total_amount, 0)
        i2 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        self.assertEqual(order.total_amount, 1)
        i3 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.wine),
            amount=3,
        )
        self.assertEqual(order.total_amount, 2.5)
        i2.delete()
        self.assertEqual(order.total_amount, 1.5)
        i3.total = 4
        i3.save()
        self.assertEqual(order.total_amount, 4)
        order.discount = 2
        order.save()
        self.assertEqual(order.total_amount, 2)

    def test_num_items(self):
        order = Order.objects.create(shift=self.shift)
        self.assertEqual(order.num_items, 0)
        i1 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.soda),
            amount=2,
        )
        self.assertEqual(order.num_items, 2)
        i2 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        self.assertEqual(order.num_items, 4)
        i3 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.wine),
            amount=3,
        )
        self.assertEqual(order.num_items, 7)
        i2.delete()
        self.assertEqual(order.num_items, 5)

    def test_create_order_shift_locked(self):
        self.shift.locked = True
        self.shift.save()

        with self.assertRaises(ValueError):
            Order.objects.create(shift=self.shift)

    def test_create_order_shift_not_started(self):
        self.shift.start = self.shift.start + timezone.timedelta(days=2)
        self.shift.end = self.shift.end + timezone.timedelta(days=2)
        self.shift.save()

        with self.assertRaises(ValueError):
            Order.objects.create(shift=self.shift)

    def test_update_order_shift_locked(self):
        order = Order.objects.create(shift=self.shift)
        OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )

        self.shift.locked = True
        self.shift.save()

        order.discount = 0.5

        with self.assertRaises(Order.DoesNotExist):
            order.refresh_from_db()

    def test_update_order_paid(self):
        order = Order.objects.create(shift=self.shift)
        i1 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        self.assertEqual(order.total_amount, 1)
        self.assertEqual(i1.total, 1)
        order.payment = create_payment(
            order, processed_by=self.member, pay_type=Payment.CASH
        )
        order.save()

        order.refresh_from_db()
        self.assertIsNotNone(order.payment)

        order.discount = 0.5

        with self.assertRaises(PaymentError):
            order.save()

        with self.assertRaises(ValueError):
            OrderItem.objects.create(
                order=order,
                product=self.shift.product_list.product_items.get(product=self.wine),
                amount=1,
            )

        i1.amount = 3
        with self.assertRaises(ValueError):
            i1.save()

        i1.refresh_from_db()
        self.assertEqual(i1.amount, 2)

    def test_discount_amount(self):
        order = Order.objects.create(shift=self.shift)
        i1 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        order.discount = 2
        with self.assertRaises(ValidationError):
            order.clean()

        order.discount = 1
        order.clean()
        order.save()
        self.assertEqual(order.total_amount, 0)

    def test_order_item_total(self):
        order = Order.objects.create(shift=self.shift)
        i1 = OrderItem.objects.create(
            order=order,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        i1.refresh_from_db()
        self.assertEqual(i1.total, 1)

        i1.total = None
        i1.save()
        i1.refresh_from_db()
        self.assertEqual(i1.total, 1)

        i1.total = 2
        i1.save()
        i1.refresh_from_db()
        self.assertEqual(i1.total, 2)

    def test_nonexistent_product(self):
        order = Order.objects.create(shift=self.shift)
        i1 = OrderItem.objects.create(
            order=order,
            product=self.free.product_items.get(product=self.beer),
            amount=2,
        )
        with self.assertRaises(ValidationError):
            i1.clean()


@freeze_time("2021-01-01")
class ShiftTest(TestCase):
    fixtures = [
        "members.json",
        "bank_accounts.json",
        "member_groups.json",
        "products.json",
    ]

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

    def test_time(self):
        self.assertTrue(self.shift.active)
        self.shift.start = self.shift.end
        with self.assertRaises(ValidationError):
            self.shift.clean()

    def test_remove_orders_on_locked(self):
        order1 = Order.objects.create(shift=self.shift)
        order1.save()

        order2 = Order.objects.create(shift=self.shift)
        OrderItem.objects.create(
            order=order2,
            product=self.shift.product_list.product_items.get(product=self.soda),
            amount=2,
        )
        order2.save()

        order3 = Order.objects.create(shift=self.shift)
        OrderItem.objects.create(
            order=order3,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        order3.save()

        order4 = Order.objects.create(shift=self.shift)
        OrderItem.objects.create(
            order=order4,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        order4.save()
        order4.payment = create_payment(
            order4, processed_by=self.member, pay_type=Payment.CASH
        )
        order4.save()

        self.shift.locked = True
        self.shift.save()

        with self.assertRaises(Order.DoesNotExist):
            order1.refresh_from_db()

        order2.refresh_from_db()

        with self.assertRaises(Order.DoesNotExist):
            order3.refresh_from_db()

        order4.refresh_from_db()

    def test_active(self):
        self.assertTrue(self.shift.active)
        self.shift.start = self.shift.start + timezone.timedelta(minutes=10)
        self.assertFalse(self.shift.active)

    def test_shift_statistics(self):
        self.assertEqual(self.shift.total_revenue, 0)
        self.assertEqual(self.shift.total_revenue_paid, 0)

        self.assertEqual(self.shift.num_orders, 0)
        self.assertEqual(self.shift.num_orders_paid, 0)

        self.assertDictEqual(self.shift.product_sales, {})

        o1 = Order.objects.create(shift=self.shift)
        OrderItem.objects.create(
            order=o1,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        o2 = Order.objects.create(shift=self.shift)
        OrderItem.objects.create(
            order=o2,
            product=self.shift.product_list.product_items.get(product=self.soda),
            amount=2,
        )
        o3 = Order.objects.create(shift=self.shift)
        OrderItem.objects.create(
            order=o3,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        OrderItem.objects.create(
            order=o3,
            product=self.shift.product_list.product_items.get(product=self.wine),
            amount=2,
        )
        o4 = Order.objects.create(shift=self.shift)
        OrderItem.objects.create(
            order=o4,
            product=self.shift.product_list.product_items.get(product=self.wine),
            amount=2,
        )
        o5 = Order.objects.create(shift=self.shift)
        OrderItem.objects.create(
            order=o5,
            product=self.shift.product_list.product_items.get(product=self.beer),
            amount=2,
        )
        OrderItem.objects.create(
            order=o5,
            product=self.shift.product_list.product_items.get(product=self.wine),
            amount=2,
        )
        o4.payment = create_payment(o4, processed_by=self.member, pay_type=Payment.CASH)
        o4.save()
        o5.payment = create_payment(o5, processed_by=self.member, pay_type=Payment.CASH)
        o5.save()

        # The test was accidentally passing because orders had the same created at,
        # resulting in the distinct seeing them as the same order
        o2.created_at += timezone.timedelta(minutes=1)
        o3.created_at += timezone.timedelta(minutes=2)
        o4.created_at += timezone.timedelta(minutes=3)
        o5.created_at += timezone.timedelta(minutes=4)
        o2.save()
        o3.save()
        o4.save()
        o5.save()

        self.assertEqual(self.shift.total_revenue, 6)
        self.assertEqual(self.shift.total_revenue_paid, 3)

        self.assertEqual(self.shift.num_orders, 5)
        self.assertEqual(self.shift.num_orders_paid, 3)

        self.assertDictEqual(
            self.shift.product_sales,
            {self.beer.name: 6, self.soda.name: 2, self.wine.name: 6},
        )

    def test_is_manager(self):
        # @todo Move this test to test_services
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
