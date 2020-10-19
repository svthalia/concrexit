from unittest.mock import MagicMock, patch, PropertyMock

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from payments import services
from payments.exceptions import PaymentError
from payments.models import BankAccount, Payment, Batch, PaymentUser
from payments.tests.__mocks__ import MockPayable


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
@patch("payments.models.PaymentUser.tpay_allowed", PropertyMock, True)
class ServicesTest(TestCase):
    """
    Test for the services
    """

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = PaymentUser.objects.filter(last_name="Wiggers").first()

    def test_create_payment(self):
        with self.subTest("Creates new payment with right payment type"):
            p = services.create_payment(
                MockPayable(self.member), self.member, Payment.CASH
            )
            self.assertEqual(p.amount, 5)
            self.assertEqual(p.topic, "mock topic")
            self.assertEqual(p.notes, "mock notes")
            self.assertEqual(p.paid_by, self.member)
            self.assertEqual(p.processed_by, self.member)
            self.assertEqual(p.type, Payment.CASH)
        with self.subTest("Updates payment if one already exists"):
            existing_payment = Payment(amount=2)
            p = services.create_payment(
                MockPayable(payer=self.member, payment=existing_payment),
                self.member,
                Payment.CASH,
            )
            self.assertEqual(p, existing_payment)
            self.assertEqual(p.amount, 5)
        with self.subTest("Does not allow Thalia Pay when not enabled"):
            with self.assertRaises(PaymentError):
                services.create_payment(
                    MockPayable(payer=self.member), self.member, Payment.TPAY
                )

    def test_delete_payment(self):
        existing_payment = MagicMock(batch=None)
        payable = MockPayable(payer=self.member, payment=existing_payment)
        payable.save.reset_mock()

        with self.subTest("Within deletion window"):
            payable.payment = existing_payment
            existing_payment.created_at = timezone.now()
            services.delete_payment(payable)
            self.assertIsNone(payable.payment)
            payable.save.assert_called_once()
            existing_payment.delete.assert_called_once()

        with self.subTest("Outside deletion window"):
            payable.payment = existing_payment
            existing_payment.created_at = timezone.now() - timezone.timedelta(
                seconds=settings.PAYMENT_CHANGE_WINDOW + 60
            )
            with self.assertRaisesMessage(
                PaymentError, "You are not authorized to delete this payment."
            ):
                services.delete_payment(payable)
            self.assertIsNotNone(payable.payment)

        existing_payment.created_at = timezone.now()

        with self.subTest("Already processed"):
            payable.payment = existing_payment
            existing_payment.batch = Batch.objects.create(processed=True)
            with self.assertRaisesMessage(
                PaymentError, "This payment has already been processed."
            ):
                services.delete_payment(payable)
            self.assertIsNotNone(payable.payment)

    def test_update_last_used(self):
        BankAccount.objects.create(
            owner=self.member,
            initials="J",
            last_name="Test",
            iban="NL91ABNA0417164300",
            mandate_no="11-1",
            valid_from=timezone.now().date() - timezone.timedelta(days=2000),
            valid_until=timezone.now().date() - timezone.timedelta(days=1500),
            signature="base64,png",
        )
        BankAccount.objects.create(
            owner=self.member,
            initials="J",
            last_name="Test",
            iban="NL91ABNA0417164300",
            mandate_no="11-2",
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            last_used=timezone.now().date() - timezone.timedelta(days=5),
            signature="base64,png",
        )

        self.assertEqual(services.update_last_used(BankAccount.objects), 1)

        self.assertEqual(
            BankAccount.objects.filter(mandate_no="11-2").first().last_used,
            timezone.now().date(),
        )

        self.assertEqual(
            services.update_last_used(
                BankAccount.objects, timezone.datetime(year=2018, month=12, day=12)
            ),
            1,
        )

        self.assertEqual(
            BankAccount.objects.filter(mandate_no="11-2").first().last_used,
            timezone.datetime(year=2018, month=12, day=12).date(),
        )

    def test_revoke_old_mandates(self):
        BankAccount.objects.create(
            owner=self.member,
            initials="J",
            last_name="Test1",
            iban="NL91ABNA0417164300",
            mandate_no="11-1",
            valid_from=timezone.now().date() - timezone.timedelta(days=2000),
            last_used=timezone.now().date() - timezone.timedelta(days=2000),
            signature="base64,png",
        )
        BankAccount.objects.create(
            owner=self.member,
            initials="J",
            last_name="Test2",
            iban="NL91ABNA0417164300",
            mandate_no="11-2",
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            last_used=timezone.now().date() - timezone.timedelta(days=5),
            signature="base64,png",
        )

        self.assertEqual(BankAccount.objects.filter(valid_until=None).count(), 2)

        services.revoke_old_mandates()

        self.assertEqual(BankAccount.objects.filter(valid_until=None).count(), 1)
