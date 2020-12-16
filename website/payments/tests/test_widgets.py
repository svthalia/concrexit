from django.contrib.contenttypes.models import ContentType
from django.test import TestCase, override_settings

from payments.models import Payment, PaymentUser
from payments.widgets import PaymentWidget


@override_settings(SUSPEND_SIGNALS=True)
class PaymentWidgetTest(TestCase):
    """Tests widgets."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = PaymentUser.objects.filter(last_name="Wiggers").first()
        cls.payment = Payment.objects.create(
            amount=10, paid_by=cls.member, processed_by=cls.member, type=Payment.CASH
        )

    def test_get_context(self):
        obj = Payment.objects.create(
            amount=8, paid_by=self.member, processed_by=self.member, type=Payment.CASH
        )
        widget = PaymentWidget(obj=obj)

        with self.subTest("With object only"):
            context = widget.get_context("payment", None, {})
            self.assertEqual(context["obj"], obj)
            self.assertEqual(
                context["content_type"],
                ContentType.objects.get(app_label="payments", model="payment"),
            )

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
