from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings

from payments import payables
from payments.models import Payment, PaymentUser
from payments.tests.__mocks__ import MockModel, MockPayable
from payments.widgets import PaymentWidget


@override_settings(SUSPEND_SIGNALS=True)
class PaymentWidgetTest(TestCase):
    """Tests widgets."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        payables.register(MockModel, MockPayable)
        cls.member = PaymentUser.objects.filter(last_name="Wiggers").first()
        cls.payment = Payment.objects.create(
            amount=10, paid_by=cls.member, processed_by=cls.member, type=Payment.CASH
        )
        cls.obj = MockModel(payer=cls.member, payment=cls.payment)

    def test_get_context(self):
        widget = PaymentWidget(obj=self.obj)

        with self.subTest("With object only"):
            context = widget.get_context("payment", None, {})
            self.assertEqual(context["obj"].pk, payables.get_payable(self.obj).pk)
            self.assertEqual(context["app_label"], "mock_app")
            self.assertEqual(context["model_name"], "mock_model")

        with self.subTest("Trying to set payment to none"):
            self.obj.payment = None
            widget = PaymentWidget(obj=self.obj)
            context = widget.get_context("payment", None, {})
            self.assertEqual(context["obj"].pk, payables.get_payable(self.obj).pk)
            self.assertEqual(context["app_label"], "mock_app")
            self.assertEqual(context["model_name"], "mock_model")

        with self.subTest("With payment primary key"):
            context = widget.get_context("payment", self.payment.pk, {})
            self.assertEqual(
                context["url"],
                "/admin/payments/payment/{}/change/".format(self.payment.pk),
            )
            self.assertEqual(context["payment"], self.payment)

        with self.subTest("Empty value"):
            widget = PaymentWidget()
            context = widget.get_context("payment", None, {})
            self.assertNotIn("url", context)
            self.assertNotIn("payment", context)
