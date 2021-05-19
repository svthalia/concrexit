from unittest import mock
from unittest.mock import MagicMock, Mock

from django.apps import apps
from django.test import TestCase, override_settings, Client
from django.urls import reverse
from freezegun import freeze_time
from rest_framework.test import APIClient

from members.models import Member
from payments.exceptions import PaymentError
from payments.models import BankAccount, PaymentUser, Payment
from payments.tests.__mocks__ import MockPayable, MockModel


@freeze_time("2020-09-01")
@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
class PaymentProcessViewTest(TestCase):
    """Test for the PaymentProcessView."""

    fixtures = ["members.json"]

    test_body = {
        "app_label": "mock_app",
        "model_name": "mock_model",
        "payable_pk": "mock_payable_pk",
    }

    @classmethod
    def setUpTestData(cls):
        cls.user = Member.objects.filter(last_name="Wiggers").first()
        cls.account1 = BankAccount.objects.create(
            owner=cls.user,
            initials="J1",
            last_name="Test",
            iban="NL91ABNA0417164300",
            valid_from="2019-03-01",
            signature="sig",
            mandate_no="11-2",
        )
        cls.user = PaymentUser.objects.get(pk=cls.user.pk)

    def setUp(self):
        self.account1.refresh_from_db()
        self.client = APIClient()
        self.client.force_login(self.user)

        self.payable = MockPayable(MockModel(payer=self.user))

        self.original_get_model = apps.get_model
        mock_get_model = mock_get_model = MagicMock()

        def side_effect(*args, **kwargs):
            if "app_label" in kwargs and kwargs["app_label"] == "mock_app":
                return mock_get_model
            return self.original_get_model(*args, **kwargs)

        apps.get_model = Mock(side_effect=side_effect)
        mock_get_model.objects.get.return_value = self.payable

    def tearDown(self):
        apps.get_model = self.original_get_model

    def test_not_logged_in(self):
        self.client.logout()

        response = self.client.post(reverse("api:v1:payment-list"))
        self.assertEqual(403, response.status_code)

    @override_settings(THALIA_PAY_ENABLED_PAYMENT_METHOD=False)
    def test_member_has_tpay_enabled(self):
        response = self.client.post(
            reverse("api:v1:payment-list"), self.test_body, format="json"
        )
        self.assertEqual(400, response.status_code)

    def test_different_member(self):
        self.payable.model.payer = PaymentUser()

        response = self.client.post(
            reverse("api:v1:payment-list"), self.test_body, format="json"
        )

        self.assertEqual(403, response.status_code)
        self.assertEqual(
            {"detail": "You are not allowed to process this payment."}, response.data
        )

    def test_already_paid(self):
        self.payable.model.payment = Payment(amount=8)

        response = self.client.post(
            reverse("api:v1:payment-list"), self.test_body, format="json"
        )

        self.assertEqual(409, response.status_code)
        self.assertEqual(
            {"detail": "This object has already been paid for."}, response.data
        )

    @mock.patch("payments.services.create_payment")
    def test_creates_payment(self, create_payment):
        def set_payments_side_effect(*args, **kwargs):
            self.payable.model.payment = Payment.objects.create(amount=8)

        create_payment.side_effect = set_payments_side_effect

        response = self.client.post(
            reverse("api:v1:payment-list"), self.test_body, format="json"
        )

        create_payment.assert_called_with(self.payable, self.user, Payment.TPAY)

        self.assertEqual(201, response.status_code)
        self.assertEqual(
            reverse("api:v1:payment-detail", kwargs={"pk": self.payable.payment.pk}),
            response.headers["Location"],
        )

    @mock.patch("payments.services.create_payment")
    def test_payment_create_error(self, create_payment):
        create_payment.side_effect = PaymentError("Test error")

        response = self.client.post(
            reverse("api:v1:payment-list"), self.test_body, format="json"
        )

        self.assertEqual(400, response.status_code)
