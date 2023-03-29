from decimal import Decimal
from unittest import mock
from unittest.mock import MagicMock, Mock, PropertyMock, patch

from django.contrib import messages
from django.contrib.admin import AdminSite
from django.contrib.admin.utils import model_ngettext
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.http import HttpRequest
from django.test import (
    Client,
    RequestFactory,
    SimpleTestCase,
    TestCase,
    override_settings,
)
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from freezegun import freeze_time

from members.models import Member, Profile
from payments import admin
from payments.admin import BankAccountInline, PaymentInline, ValidAccountFilter
from payments.forms import BatchPaymentInlineAdminForm
from payments.models import BankAccount, Batch, Payment, PaymentUser


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


@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
@patch("payments.models.PaymentUser.tpay_allowed", PropertyMock, True)
class PaymentAdminTest(TestCase):
    fixtures = ["members.json", "bank_accounts.json"]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = PaymentUser.objects.get(pk=2)

    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(self.user)
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = admin.PaymentAdmin(Payment, admin_site=self.site)

        self._give_user_permissions()
        process_perm_batch = Permission.objects.get(
            content_type__model="batch", codename="process_batches"
        )
        self.user.user_permissions.remove(process_perm_batch)
        self.client.logout()
        self.client.force_login(self.user)

    def _give_user_permissions(self, batch_permissions=True) -> None:
        """Helper to give the user permissions."""
        content_type = ContentType.objects.get_for_model(Payment)
        permissions_p = content_type.permission_set.all()
        content_type = ContentType.objects.get_for_model(Batch)
        permissions_b = content_type.permission_set.all()
        for p in permissions_p:
            self.user.user_permissions.add(p)
        if batch_permissions:
            for p in permissions_b:
                self.user.user_permissions.add(p)

        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    def test_paid_by_link(self) -> None:
        """Tests that the right link for the paying user is returned."""
        payment = Payment.objects.create(
            amount=7.5, paid_by=self.user, processed_by=self.user, type=Payment.CASH
        )

        self.assertEqual(
            self.admin.paid_by_link(payment),
            f"<a href='/admin/payments/paymentuser/{self.user.pk}/change/'>Sébastiaan Versteeg</a>",
        )

    def test_processed_by_link(self) -> None:
        """Tests that the right link for the processing user is returned."""
        payment1 = Payment.objects.create(
            amount=7.5, processed_by=self.user, paid_by=self.user, type=Payment.CASH
        )

        self.assertEqual(
            self.admin.processed_by_link(payment1),
            f"<a href='/admin/payments/paymentuser/{self.user.pk}/change/'>Sébastiaan Versteeg</a>",
        )

    def test_delete_model_succeed(self) -> None:
        batch = Batch.objects.create()
        payment = Payment.objects.create(
            amount=1,
            paid_by=self.user,
            processed_by=self.user,
            type=Payment.TPAY,
            batch=batch,
        )
        self.client.post(
            reverse("admin:payments_payment_delete", args=(payment.id,)),
            {"post": "yes"},  # Add data to confirm deletion in admin
        )
        self.assertFalse(Payment.objects.filter(id=payment.id).exists())

    def test_delete_model_fail(self) -> None:
        batch = Batch.objects.create()
        payment = Payment.objects.create(
            amount=1,
            paid_by=self.user,
            processed_by=self.user,
            type=Payment.TPAY,
            batch=batch,
        )
        batch.processed = True
        batch.save()
        response = self.client.post(
            reverse("admin:payments_payment_delete", args=(payment.id,)),
            {"post": "yes"},  # Add data to confirm deletion in admin
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Payment.objects.filter(id=payment.id).exists())

    def test_delete_action_fail(self) -> None:
        batch = Batch.objects.create()
        batch_proc = Batch.objects.create()
        Payment.objects.create(
            amount=1,
            paid_by=self.user,
            processed_by=self.user,
            type=Payment.TPAY,
            batch=batch,
        )
        payment2 = Payment.objects.create(
            amount=1,
            paid_by=self.user,
            processed_by=self.user,
            type=Payment.TPAY,
            batch=batch_proc,
        )
        batch_proc.processed = True
        batch_proc.save()
        self.client.post(
            reverse("admin:payments_payment_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": Payment.objects.values_list("id", flat=True),
                "post": "yes",
            },
        )
        self.assertTrue(Payment.objects.filter(id=payment2.id).exists())

    def test_delete_action_success(self) -> None:
        batch = Batch.objects.create()
        payment1 = Payment.objects.create(
            amount=1,
            processed_by=self.user,
            paid_by=self.user,
            type=Payment.TPAY,
            batch=batch,
        )
        payment2 = Payment.objects.create(
            amount=1,
            processed_by=self.user,
            paid_by=self.user,
            type=Payment.TPAY,
            batch=batch,
        )
        self.client.post(
            reverse("admin:payments_payment_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": Payment.objects.values_list("id", flat=True),
                "post": "yes",
            },
        )
        self.assertFalse(
            Payment.objects.filter(id__in=[payment1.id, payment2.id]).exists()
        )

    def test_has_delete_permission_get(self) -> None:
        payment = Payment.objects.create(
            amount=10, paid_by=self.user, processed_by=self.user, type=Payment.CASH
        )
        request = self.factory.get(
            reverse("admin:payments_payment_delete", args=(payment.id,))
        )
        request.user = self.user
        self.admin.has_delete_permission(request)
        self.assertTrue(Payment.objects.filter(id=payment.id).exists())

    @freeze_time("2020-01-01")
    def test_batch_link(self) -> None:
        batch = Batch.objects.create(id=1)
        payment1 = Payment.objects.create(
            amount=7.5,
            processed_by=self.user,
            paid_by=self.user,
            type=Payment.TPAY,
            batch=batch,
        )
        payment2 = Payment.objects.create(
            amount=7.5, processed_by=self.user, paid_by=self.user, type=Payment.TPAY
        )
        payment3 = Payment.objects.create(
            amount=7.5, processed_by=self.user, paid_by=self.user, type=Payment.WIRE
        )
        self.assertEqual(
            "<a href='/admin/payments/batch/1/change/'>Thalia Pay payments for 2020-1 (not processed)</a>",
            str(self.admin.batch_link(payment1)),
        )
        self.assertEqual("No batch attached", self.admin.batch_link(payment2))
        self.assertEqual("", self.admin.batch_link(payment3))

    def test_add_to_new_batch(self) -> None:
        p1 = Payment.objects.create(
            amount=1, processed_by=self.user, paid_by=self.user, type=Payment.CARD
        )
        p2 = Payment.objects.create(
            amount=2, processed_by=self.user, paid_by=self.user, type=Payment.CASH
        )
        p3 = Payment.objects.create(
            amount=3, processed_by=self.user, paid_by=self.user, type=Payment.TPAY
        )

        change_url = reverse("admin:payments_payment_changelist")

        self._give_user_permissions(batch_permissions=False)
        self.client.post(
            change_url,
            {
                "action": "add_to_new_batch",
                "index": 1,
                "_selected_action": [x.id for x in [p1, p2, p3]],
            },
        )

        for p in Payment.objects.all():
            self.assertIsNone(p.batch)

        self._give_user_permissions()
        self.client.post(
            change_url,
            {
                "action": "add_to_new_batch",
                "index": 1,
                "_selected_action": [x.id for x in [p1, p2, p3]],
            },
        )

        for p in Payment.objects.filter(id__in=[p1.id, p2.id]):
            self.assertIsNone(p.batch)

        self.assertIsNotNone(Payment.objects.get(id=p3.id).batch.id)

        self._give_user_permissions()
        self.client.post(
            change_url,
            {
                "action": "add_to_new_batch",
                "index": 1,
                "_selected_action": [x.id for x in [p1, p2]],
            },
        )

    def test_add_to_last_batch(self) -> None:
        b = Batch.objects.create()
        p1 = Payment.objects.create(
            amount=1, processed_by=self.user, paid_by=self.user, type=Payment.CARD
        )
        p2 = Payment.objects.create(
            amount=2, processed_by=self.user, paid_by=self.user, type=Payment.CASH
        )
        p3 = Payment.objects.create(
            amount=3, processed_by=self.user, paid_by=self.user, type=Payment.TPAY
        )

        change_url = reverse("admin:payments_payment_changelist")

        self._give_user_permissions(batch_permissions=False)
        self.client.post(
            change_url,
            {
                "action": "add_to_last_batch",
                "index": 1,
                "_selected_action": [x.id for x in [p1, p2, p3]],
            },
        )

        for p in Payment.objects.all():
            self.assertIsNone(p.batch)

        self._give_user_permissions()
        self.client.post(
            change_url,
            {
                "action": "add_to_last_batch",
                "index": 1,
                "_selected_action": [x.id for x in [p1, p2, p3]],
            },
        )

        for p in Payment.objects.filter(id__in=[p1.id, p2.id]):
            self.assertIsNone(p.batch)

        self.assertEqual(Payment.objects.get(id=p3.id).batch.id, b.id)

        self.client.post(
            change_url,
            {
                "action": "add_to_last_batch",
                "index": 1,
                "_selected_action": [x.id for x in [p1, p2]],
            },
        )

        b.processed = True
        b.save()

        self.client.post(
            change_url,
            {
                "action": "add_to_last_batch",
                "index": 1,
                "_selected_action": [p3.id],
            },
        )

    def test_add_to_last_batch_no_batch(self):
        p3 = Payment.objects.create(
            amount=3, processed_by=self.user, paid_by=self.user, type=Payment.TPAY
        )

        change_url = reverse("admin:payments_payment_changelist")

        self._give_user_permissions()

        try:
            self.client.post(
                change_url,
                {
                    "action": "add_to_last_batch",
                    "index": 1,
                    "_selected_action": [p3.id],
                },
            )
        except ObjectDoesNotExist:
            self.fail("Add to last batch should work without a batch")

    def test_get_actions(self) -> None:
        """Test that the actions are added to the admin."""
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
                "add_to_new_batch",
                "add_to_last_batch",
                "export_csv",
            ],
        )

    def test_get_readonly_fields(self) -> None:
        """Test that the custom urls are added to the admin."""
        with self.subTest("No object"):
            urls = self.admin.get_readonly_fields(HttpRequest(), None)
            self.assertEqual(urls, ("created_at", "processed_by", "batch"))

        with self.subTest("With object"):
            urls = self.admin.get_readonly_fields(HttpRequest(), Payment())
            self.assertEqual(
                urls,
                (
                    "created_at",
                    "amount",
                    "paid_by",
                    "processed_by",
                    "type",
                    "topic",
                    "notes",
                    "batch",
                    "moneybird_invoice_id",
                    "moneybird_financial_statement_id",
                    "moneybird_financial_mutation_id",
                ),
            )

    def test_get_urls(self) -> None:
        """Test that the custom urls are added to the admin."""
        urls = self.admin.get_urls()
        self.assertEqual(urls[0].name, "payments_payment_create")

    @freeze_time("2019-01-01")
    def test_export_csv(self) -> None:
        """Test that the CSV export of payments is correct."""
        Payment.objects.create(
            amount=7.5, processed_by=self.user, paid_by=self.user, type=Payment.CARD
        ).save()
        Payment.objects.create(
            amount=17.5, processed_by=self.user, paid_by=self.user, type=Payment.CASH
        ).save()

        response = self.admin.export_csv(HttpRequest(), Payment.objects.all())

        self.assertEqual(
            f"Created,Amount,Type,Processor,Payer id,Payer name,"
            f"Notes\r\n2019-01-01 00:00:00+00:00,"
            f"7.50,Card payment,Sébastiaan Versteeg,{self.user.pk},Sébastiaan Versteeg,"
            f"\r\n2019-01-01 00:00:00+00:00,17.50,"
            f"Cash payment,Sébastiaan Versteeg,{self.user.pk},Sébastiaan Versteeg,"
            f"\r\n",
            response.content.decode("utf-8"),
        )

    def test_get_field_queryset(self) -> None:
        b1 = Batch.objects.create(id=1)
        Batch.objects.create(id=2, processed=True)
        p1 = Payment.objects.create(
            amount=5, paid_by=self.user, processed_by=self.user, type=Payment.TPAY
        )
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

        self.client.get(reverse("admin:payments_payment_add"))


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True)
class ValidAccountFilterTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.member = PaymentUser.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
            is_staff=True,
        )
        Profile.objects.create(user=cls.member)

        cls.member = PaymentUser.objects.get(pk=cls.member.pk)

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
        """Tests that the right options are implemented for lookups."""
        account_filter = ValidAccountFilter(
            model=BankAccount, model_admin=self.admin, params={}, request=None
        )

        self.assertEqual(
            (
                ("valid", "Valid"),
                ("invalid", "Invalid"),
                ("none", "None"),
            ),
            account_filter.lookups(None, None),
        )

    def test_queryset(self) -> None:
        """Tests that the right results are returned."""
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
@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
@patch("payments.models.PaymentUser.tpay_allowed", PropertyMock, True)
class BatchAdminTest(TestCase):
    fixtures = ["members.json", "bank_accounts.json"]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = PaymentUser.objects.get(pk=2)

    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(self.user)
        self.site = AdminSite()
        self.admin = admin.BatchAdmin(Batch, admin_site=self.site)
        self.rf = RequestFactory()

        self.user.refresh_from_db()

        self._give_user_permissions()
        process_perm_batch = Permission.objects.get(
            content_type__model="batch", codename="process_batches"
        )
        self.user.user_permissions.remove(process_perm_batch)
        self.client.logout()
        self.client.force_login(self.user)

    def _give_user_permissions(self, batch_permissions=True) -> None:
        """Helper to give the user permissions."""
        content_type = ContentType.objects.get_for_model(Payment)
        permissions_p = content_type.permission_set.all()
        content_type = ContentType.objects.get_for_model(Batch)
        permissions_b = content_type.permission_set.all()
        for p in permissions_p:
            self.user.user_permissions.add(p)
        if batch_permissions:
            for p in permissions_b:
                self.user.user_permissions.add(p)

        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    def test_delete_model_succeed(self) -> None:
        batch = Batch.objects.create()
        self.client.post(
            reverse("admin:payments_batch_delete", args=(batch.id,)),
            {"post": "yes"},  # Add data to confirm deletion in admin
        )
        self.assertFalse(Batch.objects.filter(id=batch.id).exists())

    def test_delete_model_fail(self) -> None:
        batch = Batch.objects.create(processed=True)
        response = self.client.post(
            reverse("admin:payments_batch_delete", args=(batch.id,)),
            {"post": "yes"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Batch.objects.filter(id=batch.id).exists())

    def test_delete_action_fail(self) -> None:
        Batch.objects.create()
        batch_proc = Batch.objects.create(processed=True)
        self.client.post(
            reverse("admin:payments_batch_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": Batch.objects.values_list("id", flat=True),
                "post": "yes",
            },
        )
        self.assertTrue(Batch.objects.filter(id=batch_proc.id).exists())

    def test_delete_action_success(self) -> None:
        batch = Batch.objects.create()
        batch_proc = Batch.objects.create()
        self.client.post(
            reverse("admin:payments_batch_changelist"),
            {
                "action": "delete_selected",
                "_selected_action": Batch.objects.values_list("id", flat=True),
                "post": "yes",
            },
        )
        self.assertFalse(
            Batch.objects.filter(id__in=[batch_proc.id, batch.id]).exists()
        )

    def test_has_delete_permission_get(self) -> None:
        batch = Batch.objects.create()
        request = self.rf.get(reverse("admin:payments_batch_delete", args=(batch.id,)))
        request.user = self.user
        self.admin.has_delete_permission(request)
        self.assertTrue(Batch.objects.filter(id=batch.id).exists())

    def test_get_readonly_fields(self) -> None:
        b = Batch.objects.create()
        self.assertCountEqual(
            self.admin.get_readonly_fields(None, b),
            [
                "id",
                "processed",
                "processing_date",
                "total_amount",
            ],
        )

        b.processed = True
        b.save()
        self.assertCountEqual(
            self.admin.get_readonly_fields(None, b),
            [
                "id",
                "description",
                "processed",
                "processing_date",
                "total_amount",
                "withdrawal_date",
            ],
        )

    def test_save_formset(self) -> None:
        batch = Batch.objects.create()
        batch_processed = Batch.objects.create()
        Payment.objects.create(
            amount=1,
            paid_by=self.user,
            processed_by=self.user,
            type=Payment.TPAY,
            batch=batch,
        )
        Payment.objects.create(
            amount=1,
            paid_by=self.user,
            processed_by=self.user,
            type=Payment.TPAY,
            batch=batch_processed,
        )
        batch_processed.processed = True
        batch_processed.save()

        formset = BatchPaymentInlineAdminForm()
        formset.save = MagicMock(return_value=Payment.objects.all())
        formset.save_m2m = MagicMock()

        with self.assertRaises(ValidationError):
            self.admin.save_formset(None, None, formset, None)

        batch_processed.processed = False
        batch_processed.save()

        formset.save.return_value = Payment.objects.all()
        self.admin.save_formset(None, None, formset, None)

    @mock.patch("django.contrib.admin.ModelAdmin.changeform_view")
    def test_change_form_view(self, changeform_view_mock) -> None:
        self._give_user_permissions()

        b = Batch.objects.create(processed=True)
        request = self.rf.get(f"/admin/payments/batch/{b.id}/change/")
        request.user = self.user
        self.admin.changeform_view(request, b.id)

        changeform_view_mock.assert_called_once_with(request, b.id, "", {"batch": b})

        changeform_view_mock.reset_mock()

        self.admin.changeform_view(request)

        changeform_view_mock.assert_called_once_with(request, None, "", {"batch": None})


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

        cls.user = PaymentUser.objects.get(pk=cls.user.pk)

    def setUp(self) -> None:
        self.site = AdminSite()
        self.admin = admin.BankAccountAdmin(BankAccount, admin_site=self.site)
        self.rf = RequestFactory()

    def test_owner_link(self) -> None:
        """Test that the link to a member profile is correct."""
        bank_account1 = BankAccount.objects.create(
            owner=self.user, initials="J", last_name="Test", iban="NL91ABNA0417164300"
        )

        self.assertEqual(
            self.admin.owner_link(bank_account1),
            f"<a href='/admin/auth/user/{self.user.pk}/change/'>Test1 Example</a>",
        )

        bank_account2 = BankAccount.objects.create(
            owner=None, initials="J2", last_name="Test", iban="NL91ABNA0417164300"
        )

        self.assertEqual(self.admin.owner_link(bank_account2), "")

    def test_can_be_revoked(self) -> None:
        """Test that the revocation value of a bank account is correct."""
        bank_account1 = BankAccount.objects.create(
            owner=self.user, initials="J", last_name="Test", iban="NL91ABNA0417164300"
        )

        with patch(
            "payments.models.BankAccount.can_be_revoked", new_callable=PropertyMock
        ) as mock:
            mock.return_value = True
            self.assertTrue(self.admin.can_be_revoked(bank_account1))
            mock.return_value = False
            self.assertFalse(
                self.admin.can_be_revoked(bank_account1),
            )

    def test_export_csv(self) -> None:
        """Test that the CSV export of accounts is correct."""
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
        """Tests that the last used value is updated."""
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


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
class PaymentUserAdminTest(TestCase):
    fixtures = ["members.json", "bank_accounts.json"]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.user = Member.objects.get(pk=2)

    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(self.user)
        self.site = AdminSite()
        self.admin = admin.PaymentUserAdmin(PaymentUser, admin_site=self.site)
        self.rf = RequestFactory()
        self.user = PaymentUser.objects.first()

    def test_has_add_permissions(self):
        request = self.rf.get(reverse("admin:payments_paymentuser_add"))
        request.user = self.user
        self.assertFalse(self.admin.has_add_permission(request))

    def test_has_delete_permissions(self):
        request = self.rf.get(
            reverse("admin:payments_paymentuser_delete", args=[self.user.pk])
        )
        request.user = self.user
        self.assertFalse(self.admin.has_delete_permission(request))

    @mock.patch("payments.models.PaymentUser.tpay_balance", new_callable=PropertyMock)
    @mock.patch("payments.models.PaymentUser.tpay_enabled", new_callable=PropertyMock)
    def test_get_tpay_balance(self, tpay_enabled, tpay_balance):
        tpay_balance.return_value = Decimal(-10)
        tpay_enabled.return_value = True
        self.assertEqual(self.admin.get_tpay_balance(self.user), "€ -10.00")

    @mock.patch("payments.models.PaymentUser.tpay_enabled", new_callable=PropertyMock)
    def test_get_tpay_enabled(self, tpay_enabled):
        tpay_enabled.return_value = True
        self.assertTrue(self.admin.get_tpay_enabled(self.user))

    @mock.patch("payments.models.PaymentUser.tpay_allowed", new_callable=PropertyMock)
    def test_get_tpay_allowed(self, tpay_allowed):
        tpay_allowed.return_value = True
        self.assertTrue(self.admin.get_tpay_allowed(self.user))

    def test_get_queryset(self):
        self.assertQuerysetEqual(
            self.admin.get_queryset(None).all(),
            PaymentUser.objects.all(),
            ordered=False,
        )

    def test_tpay_allowed_filter(self):
        filter_all = admin.ThaliaPayAllowedFilter(
            None, {}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertQuerysetEqual(
            filter_all.queryset(
                None, PaymentUser.objects.select_properties("tpay_allowed")
            ),
            PaymentUser.objects.select_properties("tpay_allowed"),
            ordered=False,
        )

        filter_true = admin.ThaliaPayAllowedFilter(
            None, {"tpay_allowed": "1"}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertQuerysetEqual(
            filter_true.queryset(
                None, PaymentUser.objects.select_properties("tpay_allowed")
            )
            .values_list("pk", flat=True)
            .all(),
            [3, 4, 2, 1],
            ordered=False,
        )
        filter_false = admin.ThaliaPayAllowedFilter(
            None, {"tpay_allowed": "0"}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertQuerysetEqual(
            filter_false.queryset(
                None, PaymentUser.objects.select_properties("tpay_allowed")
            )
            .values_list("pk", flat=True)
            .all(),
            [],
            ordered=False,
        )

    def test_tpay_enabled_filter(self):
        filter_all = admin.ThaliaPayEnabledFilter(
            None, {}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertEqual(
            filter_all.queryset(None, PaymentUser.objects), PaymentUser.objects
        )

        filter_true = admin.ThaliaPayEnabledFilter(
            None, {"tpay_enabled": "1"}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertQuerysetEqual(
            filter_true.queryset(None, PaymentUser.objects)
            .values_list("pk", flat=True)
            .all(),
            [2, 1],
            ordered=False,
        )
        filter_false = admin.ThaliaPayEnabledFilter(
            None, {"tpay_enabled": "0"}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertQuerysetEqual(
            filter_false.queryset(None, PaymentUser.objects)
            .values_list("pk", flat=True)
            .all(),
            [3, 4],
            ordered=False,
        )

    def test_tpay_balance_filter(self):
        filter_all = admin.ThaliaPayBalanceFilter(
            None, {}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertQuerysetEqual(
            filter_all.queryset(
                None, PaymentUser.objects.select_properties("tpay_balance")
            ),
            PaymentUser.objects.select_properties("tpay_balance"),
            ordered=False,
        )

        filter_true = admin.ThaliaPayBalanceFilter(
            None, {"tpay_balance": "0"}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertQuerysetEqual(
            filter_true.queryset(
                None, PaymentUser.objects.select_properties("tpay_balance")
            )
            .values_list("pk", flat=True)
            .all(),
            [3, 4, 2, 1],
            ordered=False,
        )
        filter_false = admin.ThaliaPayBalanceFilter(
            None, {"tpay_balance": "1"}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertQuerysetEqual(
            filter_false.queryset(
                None, PaymentUser.objects.select_properties("tpay_balance")
            )
            .values_list("pk", flat=True)
            .all(),
            [],
            ordered=False,
        )
        filter_true = admin.ThaliaPayBalanceFilter(
            None, {"tpay_balance": "0"}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertQuerysetEqual(
            filter_true.queryset(
                None, PaymentUser.objects.select_properties("tpay_balance")
            )
            .values_list("pk", flat=True)
            .all(),
            [1, 2, 3, 4],
            ordered=False,
        )
        filter_false = admin.ThaliaPayBalanceFilter(
            None, {"tpay_balance": "1"}, PaymentUser, admin.PaymentUserAdmin
        )
        self.assertQuerysetEqual(
            filter_false.queryset(
                None, PaymentUser.objects.select_properties("tpay_balance")
            )
            .values_list("pk", flat=True)
            .all(),
            [],
            ordered=False,
        )

    def test_user_link(self):
        self.assertEqual(
            self.admin.user_link(self.user),
            f"<a href='/admin/auth/user/{self.user.pk}/change/'>{self.user.get_full_name()}</a>",
        )

    def test_bankaccount_inline_permissions(self):
        request = self.rf.get(reverse("admin:payments_paymentuser_add"))
        request.user = self.user
        self.assertFalse(
            BankAccountInline(BankAccount, self.admin.admin_site).has_add_permission(
                request
            )
        )
        self.assertFalse(
            BankAccountInline(BankAccount, self.admin.admin_site).has_change_permission(
                request
            )
        )
        self.assertFalse(
            BankAccountInline(BankAccount, self.admin.admin_site).has_delete_permission(
                request
            )
        )

    def test_payment_inline_permissions(self):
        request = self.rf.get(reverse("admin:payments_paymentuser_add"))
        request.user = self.user
        self.assertFalse(
            PaymentInline(Payment, self.admin.admin_site).has_add_permission(request)
        )
        self.assertFalse(
            PaymentInline(Payment, self.admin.admin_site).has_change_permission(request)
        )
        self.assertFalse(
            PaymentInline(Payment, self.admin.admin_site).has_delete_permission(request)
        )

    def test_disallow_tpay_action(self):
        request = self.rf.get(reverse("admin:payments_paymentuser_changelist"))
        request.user = self.user
        with patch("payments.models.PaymentUser.disallow_tpay") as mock:
            request._messages = Mock()
            self.admin.disallow_thalia_pay(request, PaymentUser.objects.all())
            mock.assert_called()

    def test_allow_tpay_action(self):
        request = self.rf.get(reverse("admin:payments_paymentuser_changelist"))
        request.user = self.user
        with patch("payments.models.PaymentUser.allow_tpay") as mock:
            request._messages = Mock()
            self.admin.allow_thalia_pay(request, PaymentUser.objects.all())
            mock.assert_called()

    def test_paymentuser_two_bankaccounts(self):
        p = PaymentUser.objects.get(pk=self.user.pk)
        self.user.is_superuser = True
        self.user.save()
        self.client = Client()
        self.client.force_login(self.user)
        response = self.client.get(f"/admin/payments/paymentuser/{p.pk}/change/")
        self.assertEqual(response.status_code, 200)
        b1 = BankAccount.objects.create(
            owner=p,
            initials="J",
            last_name="Test2",
            iban="NL91ABNA0417164300",
            mandate_no="test1",
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            valid_until=timezone.now().date() - timezone.timedelta(days=3),
            last_used=timezone.now().date() - timezone.timedelta(days=4),
            signature="base64,png",
        )
        b2 = BankAccount.objects.create(
            owner=p,
            initials="J",
            last_name="Test2",
            iban="NL91ABNA0417164300",
            mandate_no="test2",
            valid_from=timezone.now().date() - timezone.timedelta(days=3),
            last_used=timezone.now().date() - timezone.timedelta(days=2),
            signature="base64,png",
        )
        response = self.client.get(f"/admin/payments/paymentuser/{p.pk}/change/")
        self.assertEqual(response.status_code, 200)
