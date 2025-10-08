from django.test import TestCase
from django.utils import timezone

from members.models import Member
from payments.apps import PaymentsConfig
from payments.models import BankAccount, Payment


class DataMinimisationTests(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.get(pk=1)

    def test_data_minimisation(self):
        with self.subTest("Payments that are 7 years old must be minimised"):
            p = Payment.objects.create(
                paid_by=self.member,
                amount=1,
                created_at=timezone.now() - timezone.timedelta(days=(365 * 7) + 1),
                topic="test",
                notes="to be deleted",
            )
            PaymentsConfig.execute_data_minimisation(dry_run=False)
            payment = Payment.objects.get(pk=p.pk)
            self.assertIsNone(payment.paid_by)

        with self.subTest("Payments that are not 7 years old must not be minimised"):
            p = Payment.objects.create(
                paid_by=self.member,
                amount=1,
                created_at=timezone.now() - timezone.timedelta(days=(365 * 7) - 1),
                topic="test",
                notes="to be deleted",
            )
            PaymentsConfig.execute_data_minimisation(dry_run=False)
            payment = Payment.objects.get(pk=p.pk)
            self.assertIsNotNone(payment.paid_by)

        with self.subTest("Dry run should not actually delete"):
            p = Payment.objects.create(
                paid_by=self.member,
                amount=1,
                created_at=timezone.now() - timezone.timedelta(days=(365 * 7) + 1),
                topic="test",
                notes="to be deleted",
            )
            PaymentsConfig.execute_data_minimisation(dry_run=True)
            payment = Payment.objects.get(pk=p.pk)
            self.assertIsNotNone(payment.paid_by)


class UserMinimisationTests(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.get(pk=1)

    def test_minimise_user_raises_with_unprocessed_payment(self):
        Payment.objects.create(
            paid_by=self.member,
            amount=1,
            created_at=timezone.now(),
            topic="test",
            notes="unprocessed",
            processed_by=None,
        )
        with self.assertRaises(ValueError):
            PaymentsConfig.minimise_user(self.member, dry_run=False)

    def test_minimise_user_dry_run(self):
        """Test dry run returns correct querysets without modifying data."""
        # processed payment that should be anonymised in actual run
        payment = Payment.objects.create(
            paid_by=self.member,
            amount=1,
            created_at=timezone.now(),
            topic="test",
            notes="processed",
            processed_by=self.member,
        )

        # regular bank account (should be included in deletion)
        b = BankAccount.objects.create(
            owner=self.member,
            initials="J",
            last_name="Test2",
            iban="NL91ABNA0417164300",
            mandate_no="11-2",
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            last_used=timezone.now().date() - timezone.timedelta(days=5),
            signature="base64,png",
        )

        thalia_pay_payment = Payment.objects.create(
            paid_by=self.member,
            amount=1,
            type=getattr(Payment, "TPAY", None),
            created_at=timezone.now(),
            topic="thalia pay",
            notes="processed",
            processed_by=self.member,
        )

        mandate = BankAccount.objects.create(
            owner=self.member,
            iban="NL00BANK9876543210",
            valid_until=None,
            mandate_no="MANDATE123",
        )

        result = PaymentsConfig.minimise_user(self.member, dry_run=True)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)

        payments_qs, banks_qs, mandates_qs = result

        self.assertIn(payment, payments_qs)
        self.assertIn(b, banks_qs)
        self.assertIn(mandate, mandates_qs)

        self.assertEqual(Payment.objects.filter(paid_by=self.member).count(), 2)
        self.assertEqual(BankAccount.objects.filter(owner=self.member).count(), 2)
        self.assertIsNone(BankAccount.objects.get(pk=mandate.pk).valid_until)
        self.assertIsNotNone(Payment.objects.get(pk=payment.pk).paid_by)
        self.assertIsNotNone(Payment.objects.get(pk=payment.pk).processed_by)
