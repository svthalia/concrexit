from django.test import TestCase

from payments.models import Payment


class PaymentTest(TestCase):
    """Tests Payments"""

    @classmethod
    def setUpTestData(cls):
        cls.payment = Payment.objects.create(
            amount=10,
        )

    def test_full_clean_works(self):
        self.payment.full_clean()

    def test_clean_works(self):
        self.payment.clean()

    def test_change_processed_sets_processing_date(self):
        self.assertFalse(self.payment.processed)
        self.assertIsNone(self.payment.processing_date)
        self.payment.processed = True
        self.payment.save()
        self.assertTrue(self.payment.processed)
        self.assertIsNotNone(self.payment.processing_date)

        # Make sure date doesn't change on new save
        date = self.payment.processing_date
        self.payment.save()
        self.assertEqual(self.payment.processing_date, date)

    def test_get_admin_url(self):
        self.assertEqual(
            self.payment.get_admin_url(),
            '/admin/payments/payment/{}/change/'.format(self.payment.pk)
        )
