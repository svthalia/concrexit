from unittest import mock
from unittest.mock import MagicMock, Mock, PropertyMock, patch

from django.apps import apps
from django.contrib.admin.utils import model_ngettext
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from freezegun import freeze_time

from members.models import Member, Profile
from payments import admin_views
from payments.models import BankAccount, Batch, Payment, PaymentUser
from payments.payables import payables
from payments.tests.__mocks__ import MockModel
from payments.tests.test_services import MockPayable


@override_settings(SUSPEND_SIGNALS=True)
class PaymentAdminViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(
            user=cls.user,
        )
        cls.user = PaymentUser.objects.get(pk=cls.user.pk)
        cls.payment = Payment.objects.create(
            amount=7.5, processed_by=cls.user, paid_by=cls.user, type=Payment.CARD
        )

    def setUp(self):
        payables.register(MockModel, MockPayable)
        self.client = Client()
        self.client.force_login(self.user)
        self.view = admin_views.PaymentAdminView()

    def _give_user_permissions(self):
        content_type = ContentType.objects.get_for_model(Payment)
        permissions = Permission.objects.filter(
            content_type__app_label=content_type.app_label,
        )
        for p in permissions:
            self.user.user_permissions.add(p)
        self.user.is_staff = True
        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    def test_redirect_without_permissions(self):
        url = "/admin/payments/payment/app_label/model/pk/create/"
        response = self.client.post(
            url,
            {
                "type": "cash_payment",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, f"/admin/login/?next={url}")

    @mock.patch("django.contrib.messages.error")
    @mock.patch("django.contrib.messages.success")
    @mock.patch("django.shortcuts.resolve_url")
    @mock.patch("payments.services.create_payment")
    @mock.patch("payments.payables.payables.get_payable")
    def test_post(
        self, get_payable, create_payment, resolve_url, messages_success, messages_error
    ):
        url = "/admin/payments/payment/mock_label/model/pk/create/"
        self._give_user_permissions()
        payable = MockPayable(MockModel(payer=self.user))

        original_get_model = apps.get_model
        mock_get_model = MagicMock()

        def side_effect(*args, **kwargs):
            if "app_label" in kwargs and kwargs["app_label"] == "mock_label":
                return mock_get_model
            return original_get_model(*args, **kwargs)

        apps.get_model = Mock(side_effect=side_effect)
        get_payable.return_value = payable
        create_payment.return_value = self.payment
        resolve_url.return_value = "/resolved_url"

        with self.subTest("Send post without payload"):
            response = self.client.post(url)

            self.assertEqual(response.status_code, 400)

            create_payment.assert_not_called()
            messages_error.assert_not_called()
            messages_success.assert_not_called()

        with self.subTest("Send post with successful processing, no next"):
            payment_type = "cash_payment"
            response = self.client.post(
                url,
                {
                    "type": payment_type,
                },
            )

            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/resolved_url")

            create_payment.assert_called_once_with(payable, self.user, payment_type)
            resolve_url.assert_called_once_with(
                "admin:payments_payment_change", self.payment.pk
            )

            messages_success.assert_called_once_with(
                response.wsgi_request, "Successfully paid MockPayable."
            )

        create_payment.reset_mock()
        messages_success.reset_mock()
        resolve_url.reset_mock()

        with self.subTest("Send post with successful processing and next"):
            payment_type = "cash_payment"
            response = self.client.post(
                url,
                {"type": payment_type, "next": "/admin/events/"},
            )

            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/resolved_url")

            create_payment.assert_called_once_with(payable, self.user, payment_type)
            resolve_url.assert_called_once_with("/admin/events/")

            messages_success.assert_called_once_with(
                response.wsgi_request,
                "Successfully paid MockPayable.",
            )

        create_payment.reset_mock()
        messages_success.reset_mock()
        resolve_url.reset_mock()

        with self.subTest("Send post with insecure next"):
            response = self.client.post(
                url,
                {"type": "cash_payment", "next": "https://ru.nl/"},
            )

            self.assertEqual(response.status_code, 400)

            create_payment.assert_not_called()
            messages_error.assert_not_called()
            messages_success.assert_not_called()

        with self.subTest("Send post without permission to process the payment"):
            payable.model.can_manage = False
            response = self.client.post(
                url,
                {
                    "type": payment_type,
                },
                follow=True,
            )
            self.assertEqual(response.status_code, 403)
            payable.model.can_manage = True

        with self.subTest("Send post with failed processing"):
            create_payment.return_value = None
            response = self.client.post(
                url,
                {
                    "type": payment_type,
                },
            )

            messages_error.assert_called_once_with(
                response.wsgi_request,
                "Could not pay MockPayable.",
            )

        with self.subTest("Send post with exception during processing"):
            create_payment.side_effect = Exception("A test exception was thrown.")
            response = self.client.post(
                url,
                {
                    "type": payment_type,
                },
            )

            messages_error.assert_called_with(
                response.wsgi_request,
                "Something went wrong paying MockPayable: A test exception was thrown.",
            )


@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
@patch("payments.models.PaymentUser.tpay_allowed", PropertyMock, True)
class BatchProcessAdminViewTest(TestCase):
    fixtures = ["members.json", "bank_accounts.json"]

    @classmethod
    @patch("payments.models.PaymentUser.tpay_allowed", PropertyMock, True)
    def setUpTestData(cls):
        cls.batch = Batch.objects.create()
        cls.user = PaymentUser.objects.get(pk=2)
        Payment.objects.create(
            amount=99,
            paid_by=cls.user,
            processed_by=cls.user,
            batch=cls.batch,
            type=Payment.TPAY,
        )

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        self.view = admin_views.PaymentAdminView()

    def _give_user_permissions(self):
        content_type = ContentType.objects.get_for_model(Batch)
        permissions = Permission.objects.filter(
            content_type__app_label=content_type.app_label,
        )
        for p in permissions:
            self.user.user_permissions.add(p)
        self.user.is_staff = True
        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    def test_permissions(self):
        url = f"/admin/payments/batch/{self.batch.id}/process/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"/user/account/login/?next={url}")

        self._give_user_permissions()

        response = self.client.post(url, follow=True)
        self.assertRedirects(response, f"/admin/payments/batch/{self.batch.id}/change/")

    def test_next_validation(self):
        self._give_user_permissions()

        response = self.client.post(
            f"/admin/payments/batch/{self.batch.id}/process/",
            {"next": "https://google.com"},
        )

        self.assertEqual(response.status_code, 400)

    @mock.patch("django.contrib.messages.error")
    @mock.patch("django.contrib.messages.success")
    def test_post(self, message_success, message_error):
        self._give_user_permissions()

        response = self.client.post(
            f"/admin/payments/batch/{self.batch.id}/process/",
            {"next": "/admin/events/"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/admin/events/")

        self.assertEqual(Batch.objects.get(id=self.batch.id).processed, True)

        message_success.assert_called_once_with(
            response.wsgi_request,
            _("Successfully processed {}.").format(model_ngettext(self.batch, 1)),
        )

        response = self.client.post(f"/admin/payments/batch/{self.batch.id}/process/")

        self.assertEqual(Batch.objects.get(id=self.batch.id).processed, True)

        message_error.assert_called_once_with(
            response.wsgi_request,
            _("{} already processed.").format(model_ngettext(self.batch, 1)),
        )


@override_settings(SUSPEND_SIGNALS=True)
@freeze_time("2020-01-01")
class BatchExportAdminViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.batch = Batch.objects.create()
        cls.user = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(user=cls.user)
        cls.user = PaymentUser.objects.get(pk=cls.user.pk)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        self.view = admin_views.BatchExportAdminView()

    def _give_user_permissions(self):
        content_type = ContentType.objects.get_for_model(Batch)
        permissions = Permission.objects.filter(
            content_type__app_label=content_type.app_label,
        )
        for p in permissions:
            self.user.user_permissions.add(p)
        self.user.is_staff = True
        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    def test_permission(self):
        url = f"/admin/payments/batch/{self.batch.id}/export/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, f"/admin/login/?next={url}")

        self._give_user_permissions()

        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self._give_user_permissions()

        user2 = Member.objects.create(
            username="test2",
            first_name="Test2",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(user=user2)
        user2 = PaymentUser.objects.get(pk=user2.pk)

        BankAccount.objects.create(
            last_used=timezone.now(),
            owner=self.user,
            iban="DE75512108001245126199",
            mandate_no="2",
            valid_from=timezone.now(),
            initials="T.E.S.T.",
            last_name="ersssss",
        )
        BankAccount.objects.create(
            last_used=timezone.now(),
            owner=user2,
            iban="NL02ABNA0123456789",
            mandate_no="1",
            valid_from=timezone.now(),
            initials="T.E.S.T.",
            last_name="ersssss2",
        )

        Payment.objects.bulk_create(
            [
                Payment(
                    amount=1, paid_by=self.user, type=Payment.TPAY, batch=self.batch
                ),
                Payment(
                    amount=2, paid_by=self.user, type=Payment.TPAY, batch=self.batch
                ),
                Payment(amount=4, paid_by=user2, type=Payment.TPAY, batch=self.batch),
                Payment(amount=2, paid_by=user2, type=Payment.TPAY, batch=self.batch),
            ]
        )

        response = self.client.post(f"/admin/payments/batch/{self.batch.id}/export/")

        self.assertEqual(
            response.content,
            b"Account holder,IBAN,Mandate Reference,Amount,Description,Mandate Date\r\n"
            b"T.E.S.T. ersssss,DE75512108001245126199,2,3.00,Thalia Pay payments for 2020-1,2020-01-01\r\n"
            b"T.E.S.T. ersssss2,NL02ABNA0123456789,1,6.00,Thalia Pay payments for 2020-1,2020-01-01\r\n",
        )


@override_settings(SUSPEND_SIGNALS=True)
@freeze_time("2020-01-01")
class BatchTopicExportAdminViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.batch = Batch.objects.create()
        cls.user = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(user=cls.user)
        cls.user = PaymentUser.objects.get(pk=cls.user.pk)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        self.view = admin_views.BatchTopicExportAdminView()

    def _give_user_permissions(self):
        content_type = ContentType.objects.get_for_model(Batch)
        permissions = Permission.objects.filter(
            content_type__app_label=content_type.app_label,
        )
        for p in permissions:
            self.user.user_permissions.add(p)
        self.user.is_staff = True
        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    def test_permission(self):
        url = f"/admin/payments/batch/{self.batch.id}/export-topic/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, f"/admin/login/?next={url}")

        self._give_user_permissions()

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self._give_user_permissions()

        user2 = Member.objects.create(
            username="test2",
            first_name="Test2",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(user=user2)
        user2 = PaymentUser.objects.get(pk=user2.pk)

        BankAccount.objects.create(
            last_used=timezone.now(),
            owner=self.user,
            iban="DE75512108001245126199",
            mandate_no="2",
            valid_from=timezone.now(),
        )
        BankAccount.objects.create(
            last_used=timezone.now(),
            owner=user2,
            iban="NL02ABNA0123456789",
            mandate_no="1",
            valid_from=timezone.now(),
        )

        Payment.objects.bulk_create(
            [
                Payment(
                    amount=1,
                    paid_by=self.user,
                    type=Payment.TPAY,
                    batch=self.batch,
                    topic="test1",
                ),
                Payment(
                    amount=2,
                    paid_by=self.user,
                    type=Payment.TPAY,
                    batch=self.batch,
                    topic="test2",
                ),
                Payment(
                    amount=4,
                    paid_by=user2,
                    type=Payment.TPAY,
                    batch=self.batch,
                    topic="test1",
                ),
                Payment(
                    amount=2,
                    paid_by=user2,
                    type=Payment.TPAY,
                    batch=self.batch,
                    topic="test2",
                ),
            ]
        )

        response = self.client.post(
            f"/admin/payments/batch/{self.batch.id}/export-topic/"
        )

        self.assertEqual(
            response.content,
            b"Topic,No. of payments,First payment,Last payment,Total amount\r\n"
            b"test1,2,2020-01-01,2020-01-01,5.00\r\n"
            b"test2,2,2020-01-01,2020-01-01,4.00\r\n",
        )


@override_settings(SUSPEND_SIGNALS=True)
@freeze_time("2020-01-01")
class BatchTopicDescriptionAdminViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.batch = Batch.objects.create()
        cls.user = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(user=cls.user)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        self.view = admin_views.BatchTopicDescriptionAdminView()

    def _give_user_permissions(self):
        content_type = ContentType.objects.get_for_model(Batch)
        permissions = Permission.objects.filter(
            content_type__app_label=content_type.app_label,
        )
        for p in permissions:
            self.user.user_permissions.add(p)
        self.user.is_staff = True
        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    def test_permission(self):
        url = f"/admin/payments/batch/{self.batch.id}/topic-description/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, f"/admin/login/?next={url}")

        self._give_user_permissions()

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        self._give_user_permissions()

        self.user2 = Member.objects.create(
            username="test2",
            first_name="Test2",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(user=self.user2)

        BankAccount.objects.create(
            last_used=timezone.now(),
            owner=self.user,
            iban="DE75512108001245126199",
            mandate_no="2",
            valid_from=timezone.now(),
        )
        BankAccount.objects.create(
            last_used=timezone.now(),
            owner=self.user2,
            iban="NL02ABNA0123456789",
            mandate_no="1",
            valid_from=timezone.now(),
        )

        Payment.objects.bulk_create(
            [
                Payment(
                    amount=1,
                    paid_by=self.user,
                    type=Payment.TPAY,
                    batch=self.batch,
                    topic="test1",
                ),
                Payment(
                    amount=2,
                    paid_by=self.user,
                    type=Payment.TPAY,
                    batch=self.batch,
                    topic="test2",
                ),
                Payment(
                    amount=4,
                    paid_by=self.user2,
                    type=Payment.TPAY,
                    batch=self.batch,
                    topic="test1",
                ),
                Payment(
                    amount=2,
                    paid_by=self.user2,
                    type=Payment.TPAY,
                    batch=self.batch,
                    topic="test2",
                ),
            ]
        )

        response = self.client.post(
            f"/admin/payments/batch/{self.batch.id}/topic-description/"
        )

        self.assertContains(
            response,
            "- test1 (2x) [2020-01-01 -- 2020-01-01], total €5.00\n- test2 (2x) [2020-01-01 -- 2020-01-01], total €4.00\n",
        )


@override_settings(SUSPEND_SIGNALS=True)
class BatchNewFilledAdminViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.batch = Batch.objects.create()
        cls.user = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(user=cls.user)
        cls.user = PaymentUser.objects.get(pk=cls.user.pk)

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.user)
        self.view = admin_views.BatchExportAdminView()

    def _give_user_permissions(self):
        content_type = ContentType.objects.get_for_model(Batch)
        permissions = Permission.objects.filter(
            content_type__app_label=content_type.app_label,
        )
        for p in permissions:
            self.user.user_permissions.add(p)
        self.user.is_staff = True
        self.user.save()

        self.client.logout()
        self.client.force_login(self.user)

    def test_permission(self):
        url = "/admin/payments/batch/new_filled/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertURLEqual(response.url, f"/admin/login/?next={url}")

        self._give_user_permissions()

        response = self.client.post(url)

        b = Batch.objects.exclude(id=self.batch.id).first()
        self.assertRedirects(response, f"/admin/payments/batch/{b.id}/change/")

    @freeze_time("2020-03-01")
    def test_post(self):
        self._give_user_permissions()

        Payment.objects.bulk_create(
            [
                Payment(
                    amount=1,
                    type=Payment.TPAY,
                    created_at=timezone.datetime(
                        2020, 1, 31, tzinfo=timezone.timezone.utc
                    ),
                ),
                Payment(
                    amount=2,
                    type=Payment.TPAY,
                    created_at=timezone.datetime(
                        2020, 2, 1, tzinfo=timezone.timezone.utc
                    ),
                ),
                Payment(
                    amount=3,
                    type=Payment.TPAY,
                    created_at=timezone.datetime(
                        2020, 2, 10, tzinfo=timezone.timezone.utc
                    ),
                    batch=self.batch,
                ),
                Payment(
                    amount=4,
                    type=Payment.TPAY,
                    created_at=timezone.datetime(
                        2020, 2, 28, tzinfo=timezone.timezone.utc
                    ),
                ),
                Payment(
                    amount=5,
                    type=Payment.TPAY,
                    created_at=timezone.datetime(
                        2020, 2, 29, tzinfo=timezone.timezone.utc
                    ),
                ),
                Payment(
                    amount=6,
                    type=Payment.TPAY,
                    created_at=timezone.datetime(
                        2020, 3, 1, tzinfo=timezone.timezone.utc
                    ),
                ),
                Payment(
                    amount=7,
                    type=Payment.WIRE,
                    created_at=timezone.datetime(
                        2020, 1, 1, tzinfo=timezone.timezone.utc
                    ),
                ),
            ]
        )

        self.client.post("/admin/payments/batch/new_filled/")

        b = Batch.objects.exclude(id=self.batch.id).first()

        self.assertEqual(Payment.objects.get(amount=1).batch.id, b.id)
        self.assertEqual(Payment.objects.get(amount=2).batch.id, b.id)
        self.assertEqual(Payment.objects.get(amount=3).batch.id, self.batch.id)
        self.assertEqual(Payment.objects.get(amount=4).batch.id, b.id)
        self.assertEqual(Payment.objects.get(amount=5).batch.id, b.id)
        self.assertEqual(Payment.objects.get(amount=6).batch.id, b.id)
        self.assertIsNone(Payment.objects.get(amount=7).batch)
