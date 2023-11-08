from unittest.mock import MagicMock, Mock

from django.apps import apps
from django.test import TestCase, override_settings

from freezegun import freeze_time
from rest_framework.test import APIClient

from members.models import Member
from payments.models import BankAccount, PaymentUser
from payments.payables import payables
from payments.tests.__mocks__ import MockModel, MockPayable


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
        payables.register(MockModel, MockPayable)

        self.account1.refresh_from_db()
        self.client = APIClient()
        self.client.force_login(self.user)

        self.payable = MockPayable(MockModel(payer=self.user))
        self.original_get_payable = payables.get_payable
        payables.get_payable = MagicMock()
        payables.get_payable.return_value = self.payable

        self.original_get_model = apps.get_model
        mock_get_model = mock_get_model = MagicMock()

        def side_effect(*args, **kwargs):
            if "app_label" in kwargs and kwargs["app_label"] == "mock_app":
                return mock_get_model
            return self.original_get_model(*args, **kwargs)

        apps.get_model = Mock(side_effect=side_effect)
