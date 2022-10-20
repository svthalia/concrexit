from django.contrib.admin import AdminSite
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from activemembers.models import Committee, MemberGroupMembership
from members.models import Member
from payments.models import Payment
from payments.services import create_payment
from sales import payables
from sales.admin.order_admin import OrderAdmin
from sales.admin.shift_admin import ShiftAdmin
from sales.models.order import Order, OrderItem
from sales.models.product import Product, ProductList
from sales.models.shift import Shift


class OrderAdminTest(TestCase):
    fixtures = [
        "members.json",
        "bank_accounts.json",
        "member_groups.json",
        "products.json",
    ]

    @classmethod
    def setUpTestData(cls) -> None:
        """Create the following test data:

        o0: an empty order
        o1: an unpaid order of 2 beer
        o2: an order of 2 soda that doesn't need a payment
        o3: an unpaid order with 2 beer and 2 wine
        o4: a paid order with 2 wine
        o5: a paid order with 2 beer and 2 wine
        o6: an unpaid order of 2 soda that does need a payment (custom)
        """
        payables.register()

        cls.user = Member.objects.filter(last_name="Wiggers").first()

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
            cls.o4, processed_by=cls.user, pay_type=Payment.CASH
        )
        cls.o4.save()
        cls.o5.payment = create_payment(
            cls.o5, processed_by=cls.user, pay_type=Payment.CASH
        )
        cls.o5.save()
        cls.o6 = Order.objects.create(shift=cls.shift)
        OrderItem.objects.create(
            order=cls.o6,
            product=cls.shift.product_list.product_items.get(product=cls.soda),
            amount=2,
            total=1,
        )

        cls.cie = Committee.objects.get(pk=1)
        MemberGroupMembership.objects.create(group=cls.cie, member=cls.user)
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
        cls.cie.permissions.add(permission1)
        cls.cie.permissions.add(permission2)
        cls.cie.permissions.add(permission3)
        cls.cie.permissions.add(permission4)

    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(self.user)
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = OrderAdmin(Order, admin_site=self.site)
        self.rf = RequestFactory()

        self.client.logout()
        self.client.force_login(self.user)

    def test_change_form_view_rendering_correctly(self) -> None:
        for o in [self.o0, self.o1, self.o2, self.o3, self.o4, self.o5, self.o6]:
            response = self.client.get(f"/admin/sales/order/{o.id}/change/")
            self.assertEqual(200, response.status_code)

    def test_change_list_view_rendering_correctly(self) -> None:
        response = self.client.get("/admin/sales/order/")
        self.assertEqual(200, response.status_code)

    def test_view_permissions(self):
        with self.subTest("View as super user"):
            request = self.rf.get(
                reverse("admin:sales_order_change", args=[self.o1.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_view_permission(request, self.o1))

        with self.subTest("View without permissions"):
            self.user.is_superuser = False
            self.user.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_order_change", args=[self.o1.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertFalse(self.admin.has_view_permission(request, self.o1))

        with self.subTest("View as shift manager"):
            self.shift.managers.add(self.cie)
            self.shift.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_order_change", args=[self.o1.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_view_permission(request, self.o1))

    def test_change_permissions(self):
        with self.subTest("Change as super user"):
            request = self.rf.get(
                reverse("admin:sales_order_change", args=[self.o1.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_change_permission(request, self.o1))
            self.assertTrue(
                self.admin.inlines[0].has_change_permission(
                    self.admin, request, self.o1
                )
            )

        with self.subTest("Change without permissions"):
            self.user.is_superuser = False
            self.user.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_order_change", args=[self.o1.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertFalse(self.admin.has_change_permission(request, self.o1))
            self.assertFalse(
                self.admin.inlines[0].has_change_permission(
                    self.admin, request, self.o1
                )
            )

        with self.subTest("Change as shift manager"):
            self.shift.managers.add(self.cie)
            self.shift.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_order_change", args=[self.o1.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_change_permission(request, self.o1))
            self.assertTrue(
                self.admin.inlines[0].has_change_permission(
                    self.admin, request, self.o1
                )
            )

    def test_change_permission_paid(self):
        request = self.rf.get(reverse("admin:sales_order_change", args=[self.o4.pk]))
        request.user = self.user
        request.member = self.user
        self.assertFalse(self.admin.has_change_permission(request, self.o4))
        self.assertFalse(
            self.admin.inlines[0].has_change_permission(self.admin, request, self.o4)
        )

    def test_change_permission_locked(self):
        self.shift.locked = True
        self.shift.save()

        request = self.rf.get(reverse("admin:sales_order_change", args=[self.o1.pk]))
        request.user = self.user
        request.member = self.user
        self.assertFalse(self.admin.has_change_permission(request, self.o1))
        self.assertFalse(self.admin.has_change_permission(request, self.o1))

    def test_delete_permissions(self):
        with self.subTest("Delete as super user"):
            request = self.rf.get(
                reverse("admin:sales_order_delete", args=[self.o1.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_delete_permission(request, self.o1))
            self.assertTrue(
                self.admin.inlines[0].has_delete_permission(
                    self.admin, request, self.o1
                )
            )

        with self.subTest("Delete without permissions"):
            self.user.is_superuser = False
            self.user.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_order_delete", args=[self.o1.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertFalse(self.admin.has_delete_permission(request, self.o1))
            self.assertFalse(
                self.admin.inlines[0].has_delete_permission(
                    self.admin, request, self.o1
                )
            )

        with self.subTest("Delete as shift manager"):
            self.shift.managers.add(self.cie)
            self.shift.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_order_delete", args=[self.o1.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_delete_permission(request, self.o1))
            self.assertTrue(
                self.admin.inlines[0].has_delete_permission(
                    self.admin, request, self.o1
                )
            )

    def test_delete_permission_paid(self):
        request = self.rf.get(reverse("admin:sales_order_delete", args=[self.o4.pk]))
        request.user = self.user
        request.member = self.user
        self.assertFalse(self.admin.has_delete_permission(request, self.o4))
        self.assertFalse(
            self.admin.inlines[0].has_delete_permission(self.admin, request, self.o4)
        )

    def test_delete_permission_locked(self):
        self.shift.locked = True
        self.shift.save()

        request = self.rf.get(reverse("admin:sales_order_delete", args=[self.o1.pk]))
        request.user = self.user
        request.member = self.user
        self.assertFalse(self.admin.has_delete_permission(request, self.o1))
        self.assertFalse(
            self.admin.inlines[0].has_delete_permission(self.admin, request, self.o4)
        )

    def test_add_permission(self):
        with self.subTest("Create as super user"):
            request = self.rf.get(reverse("admin:sales_order_add"))
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_add_permission(request))

        with self.subTest("Create without permissions"):
            self.user.is_superuser = False
            self.user.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(reverse("admin:sales_order_add"))
            request.user = self.user
            request.member = self.user
            self.assertFalse(self.admin.has_add_permission(request))

        with self.subTest("Create as shift manager"):
            self.shift.managers.add(self.cie)
            self.shift.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(reverse("admin:sales_order_add"))
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_add_permission(request))

        with self.subTest("Create as shift manager no active shift"):
            self.shift.locked = True
            self.shift.save()
            request = self.rf.get(reverse("admin:sales_order_add"))
            request.user = self.user
            request.member = self.user
            self.assertFalse(self.admin.has_add_permission(request))

    def test_custom_prices_readonly(self):
        with self.subTest("Custom prices as super user"):
            request = self.rf.get(reverse("admin:sales_order_add"))
            request.user = self.user
            request.member = self.user

            self.assertFalse("discount" in self.admin.get_readonly_fields(request))
            self.assertFalse(
                "total"
                in self.admin.inlines[0].get_readonly_fields(self.admin, request)
            )

        with self.subTest("Custom prices regular user"):
            self.user.is_superuser = False
            self.user.save()
            self.shift.managers.add(self.cie)
            self.shift.save()
            self.client.logout()
            self.client.force_login(self.user)

            request = self.rf.get(reverse("admin:sales_order_add"))
            request.user = self.user
            request.member = self.user

            self.assertTrue("discount" in self.admin.get_readonly_fields(request))
            self.assertTrue(
                "total"
                in self.admin.inlines[0].get_readonly_fields(self.admin, request)
            )


class ShiftAdminTest(TestCase):
    fixtures = [
        "members.json",
        "bank_accounts.json",
        "member_groups.json",
        "products.json",
    ]

    @classmethod
    def setUpTestData(cls) -> None:
        """Create the following test data:

        o0: an empty order
        o1: an unpaid order of 2 beer
        o2: an order of 2 soda that doesn't need a payment
        o3: an unpaid order with 2 beer and 2 wine
        o4: a paid order with 2 wine
        o5: a paid order with 2 beer and 2 wine
        o6: an unpaid order of 2 soda that does need a payment (custom)
        """
        payables.register()

        cls.user = Member.objects.filter(last_name="Wiggers").first()

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
            cls.o4, processed_by=cls.user, pay_type=Payment.CASH
        )
        cls.o4.save()
        cls.o5.payment = create_payment(
            cls.o5, processed_by=cls.user, pay_type=Payment.CASH
        )
        cls.o5.save()
        cls.o6 = Order.objects.create(shift=cls.shift)
        OrderItem.objects.create(
            order=cls.o6,
            product=cls.shift.product_list.product_items.get(product=cls.soda),
            amount=2,
            total=1,
        )

        cls.cie = Committee.objects.get(pk=1)
        MemberGroupMembership.objects.create(group=cls.cie, member=cls.user)
        content_type = ContentType.objects.get_for_model(Shift)
        permission1 = Permission.objects.get(
            content_type=content_type, codename="add_shift"
        )
        permission2 = Permission.objects.get(
            content_type=content_type, codename="change_shift"
        )
        permission3 = Permission.objects.get(
            content_type=content_type, codename="delete_shift"
        )
        permission4 = Permission.objects.get(
            content_type=content_type, codename="view_shift"
        )
        cls.cie.permissions.add(permission1)
        cls.cie.permissions.add(permission2)
        cls.cie.permissions.add(permission3)
        cls.cie.permissions.add(permission4)

    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(self.user)
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = ShiftAdmin(Shift, admin_site=self.site)
        self.rf = RequestFactory()

        self.client.logout()
        self.client.force_login(self.user)

    def test_change_form_view_rendering_correctly(self) -> None:
        response = self.client.get(f"/admin/sales/shift/{self.shift.id}/change/")
        self.assertEqual(200, response.status_code)

    def test_change_list_view_rendering_correctly(self) -> None:
        response = self.client.get("/admin/sales/shift/")
        self.assertEqual(200, response.status_code)

    def test_view_permissions(self):
        with self.subTest("View as super user"):
            request = self.rf.get(
                reverse("admin:sales_shift_change", args=[self.shift.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_view_permission(request, self.shift))

        with self.subTest("View without permissions"):
            self.user.is_superuser = False
            self.user.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_shift_change", args=[self.shift.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertFalse(self.admin.has_view_permission(request, self.shift))

        with self.subTest("View as shift manager"):
            self.shift.managers.add(self.cie)
            self.shift.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_shift_change", args=[self.shift.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_view_permission(request, self.shift))

    def has_change_permission(self):
        with self.subTest("Change as super user"):
            request = self.rf.get(
                reverse("admin:sales_shift_change", args=[self.shift.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_change_permission(request, self.shift))

        with self.subTest("Change without permissions"):
            self.user.is_superuser = False
            self.user.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_shift_change", args=[self.shift.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertFalse(self.admin.has_change_permission(request, self.shift))

        with self.subTest("Change as shift manager"):
            self.shift.managers.add(self.cie)
            self.shift.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_shift_change", args=[self.shift.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_change_permission(request, self.shift))

    def test_change_permission_locked(self):
        self.shift.locked = True
        self.shift.save()

        request = self.rf.get(reverse("admin:sales_shift_change", args=[self.shift.pk]))
        request.user = self.user
        request.member = self.user
        self.assertFalse(self.admin.has_change_permission(request, self.shift))

    def test_delete_permissions(self):
        with self.subTest("Delete as super user"):
            request = self.rf.get(
                reverse("admin:sales_shift_delete", args=[self.shift.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_delete_permission(request, self.shift))

        with self.subTest("Delete without permissions"):
            self.user.is_superuser = False
            self.user.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_shift_delete", args=[self.shift.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertFalse(self.admin.has_delete_permission(request, self.shift))

        with self.subTest("Delete as shift manager"):
            self.shift.managers.add(self.cie)
            self.shift.save()
            self.client.logout()
            self.client.force_login(self.user)
            request = self.rf.get(
                reverse("admin:sales_shift_delete", args=[self.shift.pk])
            )
            request.user = self.user
            request.member = self.user
            self.assertTrue(self.admin.has_delete_permission(request, self.shift))
