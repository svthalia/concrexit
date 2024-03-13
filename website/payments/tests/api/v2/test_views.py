from unittest import mock

from django.apps import apps
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from freezegun import freeze_time

from payments.exceptions import PaymentError
from payments.models import BankAccount, Batch, Payment, PaymentUser
from payments.payables import payables
from payments.tests.__mocks__ import MockModel, MockPayable


@freeze_time("2019-04-01")
@override_settings(SUSPEND_SIGNALS=True)
class PaymentListViewTest(TestCase):
    """Test for the PaymentListView."""

    fixtures = ["members.json"]

    test_body = {
        "app_label": "mock_app",
        "model_name": "mock_model",
        "payable_pk": "mock_payable_pk",
    }

    @classmethod
    def setUpTestData(cls):
        cls.login_user = PaymentUser.objects.filter(last_name="Wiggers").first()
        cls.account1 = BankAccount.objects.create(
            owner=cls.login_user,
            initials="J1",
            last_name="Test",
            iban="NL91ABNA0417164300",
            valid_from="2019-03-01",
            signature="sig",
            mandate_no="11-2",
        )
        cls.payment1 = Payment.objects.create(
            created_at=timezone.datetime(year=2019, month=3, day=1),
            paid_by=cls.login_user,
            processed_by=cls.login_user,
            notes="Testing Payment 1",
            amount=10,
            type=Payment.TPAY,
        )

    def setUp(self):
        self.account1.refresh_from_db()
        self.payment1.refresh_from_db()
        self.client = Client()
        self.client.force_login(self.login_user)

        self.payable = MockPayable(MockModel(payer=self.login_user))
        self.original_get_payable = payables.get_payable
        payables.get_payable = mock.MagicMock()
        payables.get_payable.return_value = self.payable

        self.original_get_model = apps.get_model
        mock_get_model = mock_get_model = mock.MagicMock()

        def side_effect(*args, **kwargs):
            if "app_label" in kwargs and kwargs["app_label"] == "mock_app":
                return mock_get_model
            return self.original_get_model(*args, **kwargs)

        apps.get_model = mock.Mock(side_effect=side_effect)

    def test_settled_filter(self):
        """Test if the view shows payments."""
        response = self.client.get(
            reverse("api:v2:payments:payments-list"),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Testing Payment 1")

        response = self.client.get(
            reverse("api:v2:payments:payments-list") + "?settled=yes",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, "Testing Payment 1")

        response = self.client.get(
            reverse("api:v2:payments:payments-list") + "?settled=no",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Testing Payment 1")

        self.payment1.batch = Batch.objects.create(processed=False)
        self.payment1.save()
        self.payment1.batch.processed = True
        self.payment1.batch.save()

        response = self.client.get(
            reverse("api:v2:payments:payments-list"),
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Testing Payment 1")

        response = self.client.get(
            reverse("api:v2:payments:payments-list") + "?settled=yes",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertContains(response, "Testing Payment 1")

        response = self.client.get(
            reverse("api:v2:payments:payments-list") + "?settled=no",
            follow=True,
        )
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, "Testing Payment 1")

    def tearDown(self):
        apps.get_model = self.original_get_model
        payables.get_payable = self.original_get_payable

    def test_not_logged_in(self):
        self.client.logout()

        response = self.client.post(reverse("api:v2:payments:payments-list"))
        self.assertEqual(403, response.status_code)

    @override_settings(THALIA_PAY_ENABLED_PAYMENT_METHOD=False)
    def test_member_has_tpay_enabled(self):
        response = self.client.post(
            reverse("api:v2:payments:payments-list"), self.test_body, format="json"
        )
        self.assertEqual(
            405, response.status_code
        )  # used to be error 400 in previous versions of this test.

    def test_different_member(self):
        self.payable.model.payer = PaymentUser()

        response = self.client.post(
            reverse("api:v2:payments:payments-list"), self.test_body, format="json"
        )

        self.assertEqual(405, response.status_code)  # used to be 403
        self.assertEqual(
            {"detail": "You are not allowed to process this payment."}, response.data
        )

    def test_already_paid(self):
        self.payable.model.payment = Payment(amount=8)

        response = self.client.post(
            reverse("api:v2:payments:payments-list"), self.test_body, format="json"
        )

        self.assertEqual(
            405, response.status_code
        )  # used to be error code 409 in previous versions of this test.
        self.assertEqual(
            {"detail": "This object has already been paid for."}, response.data
        )

    @mock.patch("payments.services.create_payment")
    @mock.patch("payments.payables.payables.get_payable")
    def test_creates_payment(self, get_payable, create_payment):
        def set_payments_side_effect(*args, **kwargs):
            self.payable.model.payment = Payment.objects.create(amount=8)

        create_payment.side_effect = set_payments_side_effect
        get_payable.return_value = self.payable

        response = self.client.post(
            reverse("api:v2:payments:payments-list"), self.test_body, format="json"
        )

        create_payment.assert_called_with(self.payable, self.login_user, Payment.TPAY)

        self.assertEqual(201, response.status_code)
        self.assertEqual(
            reverse(
                "api:v2:payments:pk:payment-detail",
                kwargs={"pk": self.payable.payment.pk},
            ),
            response.headers["Location"],
        )

    @mock.patch("payments.services.create_payment")
    def test_payment_create_error(self, create_payment):
        create_payment.side_effect = PaymentError("Test error")

        response = self.client.post(
            reverse("api:v2:payments:payments-list"), self.test_body, format="json"
        )

        self.assertEqual(
            405, response.status_code
        )  # used to be error code 405 in previous versions of this test.
