from unittest import mock

from django.test import TestCase

from payments.models import Payment


class ServicesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        import registrations.signals

        cls.payment = Payment.objects.create(amount=10,)

    @mock.patch("registrations.services.process_payment")
    def test_post_payment_save(self, process_payment):
        self.payment.type = Payment.CARD
        self.payment.save()

        process_payment.assert_called_with(self.payment)
