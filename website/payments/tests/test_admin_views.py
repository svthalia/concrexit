from unittest import mock
from unittest.mock import Mock

from django.contrib.admin.utils import model_ngettext
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from freezegun import freeze_time

from members.models import Member, Profile
from payments import admin_views
from payments.models import Payment, Batch, BankAccount


@override_settings(SUSPEND_SIGNALS=True)
class PaymentAdminViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.payment = Payment.objects.create(amount=7.5)
        cls.user = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(
            user=cls.user, language="nl",
        )

    def setUp(self):
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

    def test_permissions(self):
        url = "/admin/payments/payment/{}/process/".format(self.payment.pk)
        response = self.client.post(url, {"type": "cash_payment",})
        self.assertRedirects(response, "/admin/login/?next=%s" % url)

        self._give_user_permissions()

        url = "/admin/payments/payment/{}/process/".format(self.payment.pk)
        response = self.client.post(url, {"type": "cash_payment",})
        self.assertRedirects(
            response, "/admin/payments/payment/%s/change/" % self.payment.pk
        )

    @mock.patch("django.contrib.messages.error")
    @mock.patch("django.contrib.messages.success")
    @mock.patch("payments.services.process_payment")
    def test_post(self, process_payment, messages_success, messages_error):
        process_payment.return_value = [self.payment]
        payment_qs = Payment.objects.filter(pk=self.payment.pk)

        with mock.patch("payments.models.Payment.objects.filter") as qs_mock:
            qs_mock.return_value = payment_qs
            qs_mock.get = Mock(return_value=payment_qs)

            self._give_user_permissions()

            with self.subTest("Send post without payload"):
                response = self.client.post(
                    "/admin/payments/payment/{}/process/".format(self.payment.pk)
                )

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.url, "/admin/payments/payment/%s/change/" % self.payment.pk
                )

                process_payment.assert_not_called()
                messages_error.assert_not_called()
                messages_success.assert_not_called()

            with self.subTest("Send post with successful processing, no next"):
                payment_type = "cash_payment"
                response = self.client.post(
                    "/admin/payments/payment/{}/process/".format(self.payment.pk),
                    {"type": payment_type,},
                )

                self.assertEqual(response.status_code, 302)
                self.assertEqual(
                    response.url, "/admin/payments/payment/%s/change/" % self.payment.pk
                )

                process_payment.assert_called_once_with(
                    payment_qs, self.user, payment_type
                )

                messages_success.assert_called_once_with(
                    response.wsgi_request,
                    _("Successfully processed %s.") % model_ngettext(self.payment, 1),
                )

            process_payment.reset_mock()
            messages_success.reset_mock()

            with self.subTest("Send post with successful processing and next"):
                payment_type = "cash_payment"
                response = self.client.post(
                    "/admin/payments/payment/{}/process/".format(self.payment.pk),
                    {"type": payment_type, "next": "/admin/events/"},
                )

                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.url, "/admin/events/")

                process_payment.assert_called_once_with(
                    payment_qs, self.user, payment_type
                )

                messages_success.assert_called_once_with(
                    response.wsgi_request,
                    _("Successfully processed %s.") % model_ngettext(self.payment, 1),
                )

            with self.subTest("Send post with failed processing"):
                process_payment.return_value = []
                response = self.client.post(
                    "/admin/payments/payment/{}/process/".format(self.payment.pk),
                    {"type": payment_type,},
                )

                messages_error.assert_called_once_with(
                    response.wsgi_request,
                    _("Could not process %s.") % model_ngettext(self.payment, 1),
                )


@override_settings(SUSPEND_SIGNALS=True)
class BatchAdminViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.batch = Batch.objects.create()
        cls.user = Member.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(
            user=cls.user, language="nl",
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
        self.assertRedirects(response, "/admin/login/?next=%s" % url)

        self._give_user_permissions()

        response = self.client.post(url)
        self.assertRedirects(response, f"/admin/payments/batch/{self.batch.id}/change/")

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
        Profile.objects.create(
            user=cls.user, language="nl",
        )

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
        self.assertRedirects(response, "/admin/login/?next=%s" % url)

        self._give_user_permissions()

        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)

    @freeze_time("2020-01-01")
    def test_post(self):
        self._give_user_permissions()

        self.user2 = Member.objects.create(
            username="test2",
            first_name="Test2",
            last_name="Example",
            email="test1@example.org",
        )
        Profile.objects.create(
            user=self.user2, language="nl",
        )

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
                    amount=1, paid_by=self.user, type=Payment.TPAY, batch=self.batch
                ),
                Payment(
                    amount=2, paid_by=self.user, type=Payment.TPAY, batch=self.batch
                ),
                Payment(
                    amount=4, paid_by=self.user2, type=Payment.TPAY, batch=self.batch
                ),
                Payment(
                    amount=2, paid_by=self.user2, type=Payment.TPAY, batch=self.batch
                ),
            ]
        )

        response = self.client.post(f"/admin/payments/batch/{self.batch.id}/export/")

        self.assertEqual(
            response.content,
            b"Account holder name,IBAN,Mandate id,Amount,Description,Mandate date\r\n"
            b"Test1 Example,DE75512108001245126199,2,3,your Thalia payments for 2020-1,2020-01-01\r\n"
            b"Test2 Example,NL02ABNA0123456789,1,6,your Thalia payments for 2020-1,2020-01-01\r\n",
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
        Profile.objects.create(
            user=cls.user, language="nl",
        )

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
        response = self.client.get(url)
        self.assertRedirects(response, f"/admin/login/?next={url}")

        self._give_user_permissions()

        response = self.client.get(url)
        self.assertRedirects(
            response, f"/admin/payments/batch/{Batch.objects.last().id}/change/"
        )

    @freeze_time("2020-03-01")
    def test_get(self):
        self._give_user_permissions()

        Payment.objects.bulk_create(
            [
                Payment(
                    amount=1,
                    type=Payment.TPAY,
                    processing_date=timezone.datetime(2020, 1, 31, tzinfo=timezone.utc),
                ),
                Payment(
                    amount=2,
                    type=Payment.TPAY,
                    processing_date=timezone.datetime(2020, 2, 1, tzinfo=timezone.utc),
                ),
                Payment(
                    amount=3,
                    type=Payment.TPAY,
                    processing_date=timezone.datetime(2020, 2, 10, tzinfo=timezone.utc),
                    batch=self.batch,
                ),
                Payment(
                    amount=4,
                    type=Payment.TPAY,
                    processing_date=timezone.datetime(2020, 2, 28, tzinfo=timezone.utc),
                ),
                Payment(
                    amount=5,
                    type=Payment.TPAY,
                    processing_date=timezone.datetime(2020, 2, 29, tzinfo=timezone.utc),
                ),
                Payment(
                    amount=6,
                    type=Payment.TPAY,
                    processing_date=timezone.datetime(2020, 3, 1, tzinfo=timezone.utc),
                ),
            ]
        )

        self.client.get("/admin/payments/batch/new_filled/")

        b = Batch.objects.first()

        self.assertIsNone(Payment.objects.get(amount=1).batch)
        self.assertEqual(Payment.objects.get(amount=2).batch.id, b.id)
        self.assertEqual(Payment.objects.get(amount=3).batch.id, self.batch.id)
        self.assertEqual(Payment.objects.get(amount=4).batch.id, b.id)
        self.assertEqual(Payment.objects.get(amount=5).batch.id, b.id)
        self.assertIsNone(Payment.objects.get(amount=6).batch)
