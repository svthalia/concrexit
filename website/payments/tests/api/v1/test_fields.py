from unittest import mock

from django.test import TestCase, override_settings

from freezegun import freeze_time

from payments.api.v1.fields import PaymentTypeField
from payments.models import Payment


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True)
class PaymentTypeFieldTest(TestCase):
    """Test for the payment type field."""

    fixtures = ["members.json"]

    @mock.patch("rest_framework.serializers.ChoiceField.get_attribute")
    def test_get_attribute(self, mock_super):
        field = PaymentTypeField(choices=Payment.PAYMENT_TYPE)

        obj = Payment()
        obj.payment = False

        self.assertEqual(field.get_attribute(obj), PaymentTypeField.NO_PAYMENT)

        obj.payment = True

        field.get_attribute(obj)
        mock_super.assert_called()
