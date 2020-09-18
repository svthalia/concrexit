from unittest import mock
from unittest.mock import Mock, MagicMock

from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.test import Client, TestCase, override_settings

from members.models import Member, Profile
from payments import admin_views
from payments.models import Payment
from payments.tests.test_services import MockPayable


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

    def test_redirect_without_permissions(self):
        url = "/admin/payments/payment/app_label/model/pk/create/"
        response = self.client.post(url, {"type": "cash_payment",})
        self.assertRedirects(response, "/admin/login/?next=%s" % url)

    @mock.patch("django.contrib.messages.error")
    @mock.patch("django.contrib.messages.success")
    @mock.patch("django.shortcuts.resolve_url")
    @mock.patch("payments.services.create_payment")
    def test_post(self, create_payment, resolve_url, messages_success, messages_error):
        url = "/admin/payments/payment/mock_label/model/pk/create/"
        self._give_user_permissions()
        payable = MockPayable(payer=self.user)

        original_get_model = apps.get_model
        mock_get_model = MagicMock()

        def side_effect(*args, **kwargs):
            if "app_label" in kwargs and kwargs["app_label"] == "mock_label":
                return mock_get_model
            else:
                return original_get_model(*args, **kwargs)

        apps.get_model = Mock(side_effect=side_effect)
        mock_get_model.objects.get.return_value = payable
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
            response = self.client.post(url, {"type": payment_type,},)

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
                url, {"type": payment_type, "next": "/admin/events/"},
            )

            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, "/resolved_url")

            create_payment.assert_called_once_with(payable, self.user, payment_type)
            resolve_url.assert_called_once_with("/admin/events/")

            messages_success.assert_called_once_with(
                response.wsgi_request, "Successfully paid MockPayable.",
            )

        create_payment.reset_mock()
        messages_success.reset_mock()
        resolve_url.reset_mock()

        with self.subTest("Send post with insecure next"):
            response = self.client.post(
                url, {"type": "cash_payment", "next": "https://ru.nl/"},
            )

            self.assertEqual(response.status_code, 400)

            create_payment.assert_not_called()
            messages_error.assert_not_called()
            messages_success.assert_not_called()

        with self.subTest("Send post with failed processing"):
            create_payment.return_value = None
            response = self.client.post(url, {"type": payment_type,})

            messages_error.assert_called_once_with(
                response.wsgi_request, "Could not pay MockPayable.",
            )
