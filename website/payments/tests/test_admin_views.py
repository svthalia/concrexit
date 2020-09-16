from unittest import mock
from unittest.mock import Mock

from django.contrib.admin.utils import model_ngettext
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from members.models import Member, Profile
from payments import admin_views
from payments.models import Payment


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
        Profile.objects.create(user=cls.user,)

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
