from django.test import TestCase, override_settings

from members.models import Member
from payments.models import Payment
from payments.widgets import PaymentWidget


@override_settings(SUSPEND_SIGNALS=True)
class PaymentWidgetTest(TestCase):
    """Tests widgets"""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.payment = Payment.objects.create(
            amount=10, paid_by=cls.member, processed_by=cls.member,
        )

    def test_get_context(self):
        widget = PaymentWidget()

        with self.subTest("With payment primary key"):
            context = widget.get_context("payment", self.payment.pk, {})
            self.assertEqual(
                context["url"],
                "/admin/payments/payment/{}/change/".format(self.payment.pk),
            )
            self.assertEqual(context["payment"], self.payment)

        with self.subTest("Empty value"):
            context = widget.get_context("payment", None, {})
            self.assertNotIn("url", context)
            self.assertNotIn("payment", context)
