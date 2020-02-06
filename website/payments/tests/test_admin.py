from unittest import mock
from unittest.mock import Mock, MagicMock

from django.contrib import messages
from django.contrib.admin import AdminSite
from django.contrib.admin.utils import model_ngettext
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest
from django.test import (
    TestCase,
    SimpleTestCase,
    Client,
    RequestFactory,
    override_settings,
)
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from freezegun import freeze_time

from members.models import Member, Profile
from payments import admin
from payments.admin import ValidAccountFilter
from payments.models import Payment, BankAccount, Batch

from payments.admin import PaymentAdmin


class GlobalAdminTest(SimpleTestCase):
    @mock.patch("registrations.admin.RegistrationAdmin")
    def test_show_message(self, admin_mock) -> None:
        admin_mock.return_value = admin_mock
        request = Mock(spec=HttpRequest)

        admin._show_message(admin_mock, request, 0, "message", "error")
        admin_mock.message_user.assert_called_once_with(
            request, "error", messages.ERROR
        )
        admin_mock.message_user.reset_mock()
        admin._show_message(admin_mock, request, 1, "message", "error")
        admin_mock.message_user.assert_called_once_with(
            request, "message", messages.SUCCESS
        )


@override_settings(SUSPEND_SIGNALS=True)
class PaymentAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = Member.objects.create(
            pk=1,
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
            is_staff=True,
        )
        Profile.objects.create(user=cls.user)

    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(self.user)
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = admin.PaymentAdmin(Payment, admin_site=self.site)

        self._give_user_permissions()
        process_perm = Permission.objects.get(
            content_type__model="payment", codename="process_payments"
        )
        self.user.user_permissions.remove(process_perm)
        process_perm_batch = Permission.objects.get(
            content_type__model="batch", codename="process_batches"
        )
        self.user.user_permissions.remove(process_perm_batch)
        self.client.logout()
        self.client.force_login(self.user)

    def _give_user_permissions(self) -> None:
        """
        Helper to give the user permissions
        """
        content_type = ContentType.objects.get_for_model(Payment)
        permissions_p = content_type.permission_set.all()
        content_type = ContentType.objects.get_for_model(Batch)
        permissions_b = content_type.permission_set.all()
        for p in permissions_p:
            self.user.user_permissions.add(p)
        for p in permissions_b:
            self.user.user_permissions.add(p)

        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    @mock.patch("payments.models.Payment.objects.get")
    def test_changeform_view(self, payment_get) -> None:
        """
        Tests that the right context data is added to the response
        """
        object_id = "c85ea333-3508-46f1-8cbb-254f8c138020"
        payment = Payment.objects.create(pk=object_id, amount=7.5)
        payment_get.return_value = payment

        response = self.client.get("/admin/payments/payment/add/")
        self.assertFalse(payment_get.called)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["payment"], None)
        response = self.client.get(
            "/admin/payments/payment/{}/change/".format(object_id), follow=True
        )
        self.assertFalse(payment_get.called)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["payment"], None)

        self._give_user_permissions()

        response = self.client.get(
            "/admin/payments/payment/{}/change/".format(object_id)
        )
        self.assertTrue(payment_get.called)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["payment"], payment)

        payment.type = Payment.CARD

        response = self.client.get(
            "/admin/payments/payment/{}/change/".format(object_id)
        )
        self.assertTrue(payment_get.called)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["payment"], None)

    def test_paid_by_link(self) -> None:
        """
        Tests that the right link for the paying user is returned
        """
        payment = Payment.objects.create(amount=7.5, paid_by=self.user)

        self.assertEqual(
            self.admin.paid_by_link(payment),
            f"<a href='/members/profile/{self.user.pk}'>" f"Test1 Example</a>",
        )

        payment2 = Payment.objects.create(amount=7.5)
        self.assertEqual(self.admin.paid_by_link(payment2), "-")

    def test_processed_by_link(self) -> None:
        """
        Tests that the right link for the processing user is returned
        """
        payment1 = Payment.objects.create(amount=7.5, processed_by=self.user)

        self.assertEqual(
            self.admin.processed_by_link(payment1),
            f"<a href='/members/profile/{self.user.pk}'>" f"Test1 Example</a>",
        )

        payment2 = Payment.objects.create(amount=7.5)
        self.assertEqual(self.admin.processed_by_link(payment2), "-")

    def test_batch_link(self) -> None:
        batch = Batch.objects.create(id=1)
        payment1 = Payment.objects.create(
            amount=7.5, processed_by=self.user, type=Payment.TPAY, batch=batch
        )
        payment2 = Payment.objects.create(
            amount=7.5, processed_by=self.user, type=Payment.TPAY
        )
        self.assertEqual(
            "<a href='/admin/payments/batch/1/change/'>your Thalia payments for 2019-12 (not processed)</a>",
            str(self.admin.batch_link(payment1)),
        )
        self.assertEqual("-", self.admin.batch_link(payment2))

    @mock.patch("django.contrib.admin.ModelAdmin.message_user")
    @mock.patch("payments.services.process_payment")
    def test_process_cash(self, process_payment, message_user) -> None:
        """
        Tests that a cash payment is processed correctly
        """
        object_id = "c85ea333-3508-46f1-8cbb-254f8c138020"
        payment = Payment.objects.create(pk=object_id, amount=7.5)
        queryset = Payment.objects.filter(pk=object_id)
        process_payment.return_value = [payment]
        change_url = reverse("admin:payments_payment_changelist")

        request_noperms = self.client.post(
            change_url,
            {
                "action": "process_cash_selected",
                "index": 1,
                "_selected_action": [object_id],
            },
        ).wsgi_request
        self._give_user_permissions()
        request_hasperms = self.client.post(
            change_url,
            {
                "action": "process_cash_selected",
                "index": 1,
                "_selected_action": [object_id],
            },
        ).wsgi_request

        process_payment.reset_mock()
        message_user.reset_mock()

        self.admin.process_cash_selected(request_noperms, queryset)
        process_payment.assert_not_called()

        self.admin.process_cash_selected(request_hasperms, queryset)
        process_payment.assert_called_once_with(queryset, self.user, Payment.CASH)
        message_user.assert_called_once_with(
            request_hasperms,
            _("Successfully processed %(count)d %(items)s.")
            % {"count": 1, "items": model_ngettext(Payment(), 1)},
            messages.SUCCESS,
        )

    @mock.patch("django.contrib.admin.ModelAdmin.message_user")
    @mock.patch("payments.services.process_payment")
    def test_process_card(self, process_payment, message_user) -> None:
        """
        Tests that a card payment is processed correctly
        """
        object_id = "c85ea333-3508-46f1-8cbb-254f8c138020"
        payment = Payment.objects.create(pk=object_id, amount=7.5)
        queryset = Payment.objects.filter(pk=object_id)
        process_payment.return_value = [payment]
        change_url = reverse("admin:payments_payment_changelist")

        request_noperms = self.client.post(
            change_url,
            {
                "action": "process_card_selected",
                "index": 1,
                "_selected_action": [object_id],
            },
        ).wsgi_request
        self._give_user_permissions()
        request_hasperms = self.client.post(
            change_url,
            {
                "action": "process_card_selected",
                "index": 1,
                "_selected_action": [object_id],
            },
        ).wsgi_request

        process_payment.reset_mock()
        message_user.reset_mock()

        self.admin.process_card_selected(request_noperms, queryset)
        process_payment.assert_not_called()

        self.admin.process_card_selected(request_hasperms, queryset)
        process_payment.assert_called_once_with(queryset, self.user, Payment.CARD)
        message_user.assert_called_once_with(
            request_hasperms,
            _("Successfully processed %(count)d %(items)s.")
            % {"count": 1, "items": model_ngettext(Payment(), 1)},
            messages.SUCCESS,
        )

    @mock.patch("django.contrib.admin.ModelAdmin.message_user")
    @mock.patch("payments.services.process_payment")
    def test_process_tpay(self, process_payment, message_user) -> None:
        """
        Tests that a Thalia Pay payment is processed correctly
        """
        object_id = "c85ea333-3508-46f1-8cbb-254f8c138020"
        payment = Payment.objects.create(pk=object_id, amount=7.5)
        queryset = Payment.objects.filter(pk=object_id)
        process_payment.return_value = [payment]
        change_url = reverse("admin:payments_payment_changelist")

        request_noperms = self.client.post(
            change_url,
            {
                "action": "process_tpay_selected",
                "index": 1,
                "_selected_action": [object_id],
            },
        ).wsgi_request
        self._give_user_permissions()
        request_hasperms = self.client.post(
            change_url,
            {
                "action": "process_tpay_selected",
                "index": 1,
                "_selected_action": [object_id],
            },
        ).wsgi_request

        process_payment.reset_mock()
        message_user.reset_mock()

        self.admin.process_tpay_selected(request_noperms, queryset)
        process_payment.assert_not_called()

        self.admin.process_tpay_selected(request_hasperms, queryset)
        process_payment.assert_called_once_with(queryset, self.user, Payment.TPAY)
        message_user.assert_called_once_with(
            request_hasperms,
            _("Successfully processed %(count)d %(items)s.")
            % {"count": 1, "items": model_ngettext(Payment(), 1)},
            messages.SUCCESS,
        )

    @mock.patch("django.contrib.admin.ModelAdmin.message_user")
    @mock.patch("payments.services.process_payment")
    def test_process_wire(self, process_payment, message_user) -> None:
        """
        Tests that a wire payment is processed correctly
        """
        object_id = "c85ea333-3508-46f1-8cbb-254f8c138020"
        payment = Payment.objects.create(pk=object_id, amount=7.5)
        queryset = Payment.objects.filter(pk=object_id)
        process_payment.return_value = [payment]
        change_url = reverse("admin:payments_payment_changelist")

        request_noperms = self.client.post(
            change_url,
            {
                "action": "process_wire_selected",
                "index": 1,
                "_selected_action": [object_id],
            },
        ).wsgi_request
        self._give_user_permissions()
        request_hasperms = self.client.post(
            change_url,
            {
                "action": "process_wire_selected",
                "index": 1,
                "_selected_action": [object_id],
            },
        ).wsgi_request

        process_payment.reset_mock()
        message_user.reset_mock()

        self.admin.process_wire_selected(request_noperms, queryset)
        process_payment.assert_not_called()

        self.admin.process_wire_selected(request_hasperms, queryset)
        process_payment.assert_called_once_with(queryset, self.user, Payment.WIRE)
        message_user.assert_called_once_with(
            request_hasperms,
            _("Successfully processed %(count)d %(items)s.")
            % {"count": 1, "items": model_ngettext(Payment(), 1)},
            messages.SUCCESS,
        )

    def test_add_to_new_batch(self) -> None:
        p1 = Payment.objects.create(amount=1)
        p2 = Payment.objects.create(amount=2, processed_by=self.user, type=Payment.CASH)
        p3 = Payment.objects.create(amount=3, processed_by=self.user, type=Payment.TPAY)
        queryset = Payment.objects.all()

        change_url = reverse("admin:payments_payment_changelist")

        request_noperms = self.client.post(
            change_url,
            {
                "action": "add_to_new_batch",
                "index": 1,
                "_selected_action": [x.id for x in [p1, p2, p3]],
            },
        ).wsgi_request
        self._give_user_permissions()
        request_hasperms = self.client.post(
            change_url,
            {
                "action": "add_to_new_batch",
                "index": 1,
                "_selected_action": [x.id for x in [p1, p2, p3]],
            },
        ).wsgi_request

        self.admin.add_to_new_batch(request_noperms, queryset)
        for p in Payment.objects.all():
            self.assertIsNone(p.batch)

        self.admin.add_to_new_batch(request_hasperms, queryset)
        for p in Payment.objects.filter(id__in=[p1.id, p2.id]):
            self.assertIsNone(p.batch)

        self.assertIsNotNone(Payment.objects.get(p3.id).batch)

    def test_add_to_last_batch(self) -> None:
        b = Batch.objects.create()
        p1 = Payment.objects.create(amount=1)
        p2 = Payment.objects.create(amount=2, processed_by=self.user, type=Payment.CASH)
        p3 = Payment.objects.create(amount=3, processed_by=self.user, type=Payment.TPAY)
        queryset = Payment.objects.all()

        change_url = reverse("admin:payments_payment_changelist")

        request_noperms = self.client.post(
            change_url,
            {
                "action": "add_to_last_batch",
                "index": 1,
                "_selected_action": [x.id for x in [p1, p2, p3]],
            },
        ).wsgi_request
        self._give_user_permissions()
        request_hasperms = self.client.post(
            change_url,
            {
                "action": "add_to_last_batch",
                "index": 1,
                "_selected_action": [x.id for x in [p1, p2, p3]],
            },
        ).wsgi_request

        self.admin.add_to_new_batch(request_noperms, queryset)
        for p in Payment.objects.all():
            self.assertIsNone(p.batch)

        self.admin.add_to_new_batch(request_hasperms, queryset)
        for p in Payment.objects.filter(id__in=[p1.id, p2.id]):
            self.assertIsNone(p.batch)

        self.assertEqual(Payment.objects.get(p3.id).batch, b.id)

    def test_get_actions(self) -> None:
        """
        Test that the actions are added to the admin
        """
        response = self.client.get(reverse("admin:payments_payment_changelist"))

        actions = self.admin.get_actions(response.wsgi_request)
        self.assertCountEqual(actions, ["delete_selected", "export_csv"])

        self._give_user_permissions()
        response = self.client.get(reverse("admin:payments_payment_changelist"))

        actions = self.admin.get_actions(response.wsgi_request)
        self.assertCountEqual(
            actions,
            [
                "delete_selected",
                "process_cash_selected",
                "process_card_selected",
                "process_wire_selected",
                "process_tpay_selected",
                "add_to_new_batch",
                "add_to_last_batch",
                "export_csv",
            ],
        )

    def test_get_urls(self) -> None:
        """
        Test that the custom urls are added to the admin
        """
        urls = self.admin.get_urls()
        self.assertEqual(urls[0].name, "payments_payment_process")

    @freeze_time("2019-01-01")
    def test_export_csv(self) -> None:
        """
        Test that the CSV export of payments is correct
        """
        Payment.objects.create(
            amount=7.5, processed_by=self.user, paid_by=self.user, type=Payment.CARD
        ).save()
        Payment.objects.create(
            amount=17.5, processed_by=self.user, paid_by=self.user, type=Payment.CASH
        ).save()
        Payment.objects.create(amount=9, notes="This is a test").save()

        response = self.admin.export_csv(HttpRequest(), Payment.objects.all())

        self.assertEqual(
            f"Created,Processed,Amount,Type,Processor,Payer id,Payer name,"
            f"Notes\r\n2019-01-01 00:00:00+00:00,2019-01-01 00:00:00+00:00,"
            f"7.50,Card payment,Test1 Example,{self.user.pk},Test1 Example,"
            f"\r\n2019-01-01 00:00:00+00:00,2019-01-01 00:00:00+00:00,17.50,"
            f"Cash payment,Test1 Example,{self.user.pk},Test1 Example,"
            f"\r\n2019-01-01 00:00:00+00:00,,9.00,No payment,-,-,-,This is a "
            f"test\r\n",
            response.content.decode("utf-8"),
        )

    def test_formfield_for_foreignkey(self) -> None:
        b1 = Batch.objects.create(id=1)
        b2 = Batch.objects.create(id=2, processed=True)
        p1 = Payment.objects.create(amount=5, processed_by=self.user, type=Payment.TPAY)
        response = self.client.get(
            reverse("admin:payments_payment_change", args=(p1.id,))
        )
        self.assertCountEqual(
            [
                int(x.id)
                for x in response.context_data["adminform"]
                .form.fields["batch"]
                .choices.queryset
            ],
            [b1.id],
        )


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True)
class ValidAccountFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.member = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
            is_staff=True,
        )
        Profile.objects.create(user=cls.member)

        cls.no_mandate = BankAccount.objects.create(
            owner=cls.member, initials="J", last_name="Test", iban="NL91ABNA0417164300"
        )
        cls.valid_mandate = BankAccount.objects.create(
            owner=cls.member,
            initials="J",
            last_name="Test",
            iban="NL91ABNA0417164300",
            mandate_no="11-1",
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            signature="base64,png",
        )
        cls.invalid_mandate = BankAccount.objects.create(
            owner=cls.member,
            initials="J",
            last_name="Test",
            iban="NL91ABNA0417164300",
            mandate_no="11-2",
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            valid_until=timezone.now().date(),
            signature="base64,png",
        )

    def setUp(self) -> None:
        self.site = AdminSite()
        self.admin = admin.BankAccountAdmin(BankAccount, admin_site=self.site)

    def test_lookups(self) -> None:
        """
        Tests that the right options are implemented for lookups
        """
        account_filter = ValidAccountFilter(
            model=BankAccount, model_admin=self.admin, params={}, request=None
        )

        self.assertEqual(
            (("valid", "Valid"), ("invalid", "Invalid"), ("none", "None"),),
            account_filter.lookups(None, None),
        )

    def test_queryset(self) -> None:
        """
        Tests that the right results are returned
        """
        for param, item in [
            ("valid", self.valid_mandate),
            ("invalid", self.invalid_mandate),
            ("none", self.no_mandate),
        ]:
            with self.subTest(f"Status {param}"):
                account_filter = ValidAccountFilter(
                    model=BankAccount,
                    model_admin=self.admin,
                    params={"active": param},
                    request=None,
                )

                result = account_filter.queryset(None, BankAccount.objects.all())

                self.assertEqual(result.count(), 1)
                self.assertEqual(result.first().pk, item.pk)

        with self.subTest("No known param"):
            account_filter = ValidAccountFilter(
                model=BankAccount,
                model_admin=self.admin,
                params={"active": "bla"},
                request=None,
            )

            result = account_filter.queryset(None, BankAccount.objects.all())

            self.assertEqual(result.count(), 3)


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True)
class BatchAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
            is_staff=True,
            is_superuser=True,
        )

    def setUp(self) -> None:
        self.site = AdminSite()
        self.admin = admin.BankAccountAdmin(BankAccount, admin_site=self.site)
        self.rf = RequestFactory()

    # def


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True)
class BankAccountAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
            is_staff=True,
            is_superuser=True,
        )
        Profile.objects.create(user=cls.user)

    def setUp(self) -> None:
        self.site = AdminSite()
        self.admin = admin.BankAccountAdmin(BankAccount, admin_site=self.site)
        self.rf = RequestFactory()

    def test_owner_link(self) -> None:
        """
        Test that the link to a member profile is correct
        """
        bank_account1 = BankAccount.objects.create(
            owner=self.user, initials="J", last_name="Test", iban="NL91ABNA0417164300"
        )

        self.assertEqual(
            self.admin.owner_link(bank_account1),
            f"<a href='/admin/auth/user/{self.user.pk}/change/'>" f"Test1 Example</a>",
        )

        bank_account2 = BankAccount.objects.create(
            owner=None, initials="J2", last_name="Test", iban="NL91ABNA0417164300"
        )

        self.assertEqual(self.admin.owner_link(bank_account2), "")

    def test_export_csv(self) -> None:
        """
        Test that the CSV export of accounts is correct
        """
        BankAccount.objects.create(
            owner=self.user, initials="J", last_name="Test", iban="NL91ABNA0417164300"
        )
        BankAccount.objects.create(
            owner=self.user, initials="J2", last_name="Test", iban="NL91ABNA0417164300"
        )
        BankAccount.objects.create(
            owner=self.user,
            initials="J3",
            last_name="Test",
            iban="NL91ABNA0417164300",
            mandate_no="12-1",
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            valid_until=timezone.now().date(),
            signature="sig",
        )
        BankAccount.objects.create(
            owner=self.user,
            initials="J4",
            last_name="Test",
            iban="DE12500105170648489890",
            bic="NBBEBEBB",
            mandate_no="11-1",
            valid_from=timezone.now().date(),
            valid_until=timezone.now().date() + timezone.timedelta(days=5),
            signature="sig",
        )

        response = self.admin.export_csv(HttpRequest(), BankAccount.objects.all())

        self.assertEqual(
            b"Created,Name,Reference,IBAN,BIC,Valid from,Valid until,"
            b"Signature\r\n2019-01-01 00:00:00+00:00,J Test,,"
            b"NL91ABNA0417164300,,,,\r\n2019-01-01 00:00:00+00:00,J2 Test,,"
            b"NL91ABNA0417164300,,,,\r\n2019-01-01 00:00:00+00:00,J3 Test,"
            b"12-1,NL91ABNA0417164300,,2018-12-27,2019-01-01,"
            b"sig\r\n2019-01-01 00:00:00+00:00,J4 Test,11-1,"
            b"DE12500105170648489890,NBBEBEBB,2019-01-01,2019-01-06,sig\r\n",
            response.content,
        )

    @mock.patch("django.contrib.admin.ModelAdmin.message_user")
    @mock.patch("payments.services.update_last_used")
    def test_set_last_used(self, update_last_used, message_user) -> None:
        """
        Tests that the last used value is updated
        """
        update_last_used.return_value = 1

        request_noperms = self.rf.post(
            "/", {"action": "set_last_used", "index": 1, "_selected_action": ["bla"]}
        )
        request_noperms.user = MagicMock()
        request_noperms.user.has_perm = lambda _: False

        request_hasperms = self.rf.post(
            "/", {"action": "set_last_used", "index": 1, "_selected_action": ["bla"]}
        )
        request_hasperms.user = MagicMock()
        request_hasperms.user.has_perm = lambda _: True

        update_last_used.reset_mock()
        message_user.reset_mock()

        queryset_mock = MagicMock()

        self.admin.set_last_used(request_noperms, queryset_mock)
        update_last_used.assert_not_called()

        self.admin.set_last_used(request_hasperms, queryset_mock)
        update_last_used.assert_called_once_with(queryset_mock)

        message_user.assert_called_once_with(
            request_hasperms,
            _("Successfully updated %(count)d %(items)s.")
            % {"count": 1, "items": model_ngettext(BankAccount(), 1)},
            messages.SUCCESS,
        )
