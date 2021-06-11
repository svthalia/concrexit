import datetime
from decimal import Decimal
from unittest.mock import PropertyMock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from payments import services, Payable
from payments.models import (
    Payment,
    BankAccount,
    Batch,
    PaymentUser,
    BlacklistedPaymentUser,
)
from payments.tests.__mocks__ import MockPayable, MockModel


class PayableTest(TestCase):
    """Tests for the Payable class."""

    def test_payment_amount_not_implemented(self):
        p = Payable(None)
        with self.assertRaises(NotImplementedError):
            _ = p.payment_amount

    def test_payment_topic_not_implemented(self):
        p = Payable(None)
        with self.assertRaises(NotImplementedError):
            _ = p.payment_topic

    def test_payment_notes_not_implemented(self):
        p = Payable(None)
        with self.assertRaises(NotImplementedError):
            _ = p.payment_notes

    def test_payment_payer_not_implemented(self):
        p = Payable(None)
        with self.assertRaises(NotImplementedError):
            _ = p.payment_payer

    def test_can_create_payment_not_implemented(self):
        p = Payable(None)
        with self.assertRaises(NotImplementedError):
            p.can_manage_payment(None)

    def test_tpay_allowed_by_default(self):
        p = Payable(None)
        self.assertTrue(p.tpay_allowed)


@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
class PaymentTest(TestCase):
    """Tests for the Payment model."""

    fixtures = ["members.json", "bank_accounts.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = PaymentUser.objects.filter(last_name="Wiggers").first()
        cls.payment = Payment.objects.create(
            amount=10, paid_by=cls.member, processed_by=cls.member, type=Payment.CASH
        )
        cls.batch = Batch.objects.create()

    def setUp(self) -> None:
        self.batch.processed = False
        self.batch.save()

    def test_get_admin_url(self):
        """Tests that the right admin url is returned."""
        self.assertEqual(
            self.payment.get_admin_url(),
            "/admin/payments/payment/{}/change/".format(self.payment.pk),
        )

    def test_add_payment_from_processed_batch_to_new_batch(self) -> None:
        """Test that a payment that is in a processed batch cannot be added to another batch."""
        self.payment.type = Payment.TPAY
        self.payment.batch = self.batch
        self.payment.save()
        self.batch.processed = True
        self.batch.save()

        b = Batch.objects.create()
        self.payment.batch = b
        with self.assertRaises(ValidationError):
            self.payment.save()

    def test_deleting_member_who_made_a_payment_doesnt_crach(self) -> None:
        """Check that https://github.com/svthalia/concrexit/issues/1328 is fixed."""
        self.member.delete()

    def test_clean(self):
        """Tests the model clean functionality."""
        with self.subTest("Block Thalia Pay creation when it is disabled for user"):
            with override_settings(THALIA_PAY_ENABLED_PAYMENT_METHOD=False):
                self.payment.type = Payment.TPAY
                self.payment.batch = self.batch
                with self.assertRaises(ValidationError):
                    self.payment.clean()

            self.payment.type = Payment.TPAY
            self.payment.batch = self.batch
            self.payment.clean()

        with self.subTest("Zero euro payments cannot exist"):
            self.payment.amount = 0
            with self.assertRaises(ValidationError):
                self.payment.clean()
            self.payment.refresh_from_db()

        with self.subTest("Test that only Thalia Pay can be added to a batch"):
            for payment_type in [Payment.CASH, Payment.CARD, Payment.WIRE]:
                self.payment.type = payment_type
                self.payment.batch = self.batch
                with self.assertRaises(ValidationError):
                    self.payment.clean()

            for payment_type in [Payment.CASH, Payment.CARD, Payment.WIRE]:
                self.payment.type = payment_type
                self.payment.batch = None
                self.payment.clean()

            self.payment.type = Payment.TPAY
            self.payment.batch = self.batch
            self.payment.clean()

        with self.subTest("Block payment change with when batch is processed"):
            batch = Batch.objects.create()
            payment = Payment.objects.create(
                amount=10,
                paid_by=self.member,
                processed_by=self.member,
                batch=batch,
                type=Payment.TPAY,
            )
            batch.processed = True
            batch.save()
            payment.amount = 5
            with self.assertRaisesMessage(
                ValidationError,
                "Cannot change a payment that is part of a processed batch",
            ):
                payment.clean()

        with self.subTest("Block payment connect with processed batch"):
            payment = Payment.objects.create(
                amount=10,
                paid_by=self.member,
                processed_by=self.member,
                type=Payment.TPAY,
            )
            payment.batch = Batch.objects.create(processed=True)
            with self.assertRaisesMessage(
                ValidationError, "Cannot add a payment to a processed batch"
            ):
                payment.clean()

    def test_str(self) -> None:
        """Tests that the output is a description with the amount."""
        self.assertEqual("Payment of 10.00", str(self.payment))


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
@patch("payments.models.PaymentUser.tpay_allowed", PropertyMock, True)
class BatchModelTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user1 = PaymentUser.objects.create(
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
            is_staff=False,
        )
        cls.user2 = PaymentUser.objects.create(
            username="test2",
            first_name="Test2",
            last_name="Example",
            email="test2@example.org",
            is_staff=True,
        )

        BankAccount.objects.create(
            owner=cls.user1,
            initials="J",
            last_name="Test",
            iban="NL91ABNA0417164300",
            mandate_no="11-1",
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            signature="base64,png",
        )

    def setUp(self):
        self.user1.refresh_from_db()
        self.user2.refresh_from_db()

    def test_start_date_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        Payment.objects.create(
            created_at=timezone.now() + datetime.timedelta(days=1),
            type=Payment.TPAY,
            amount=37,
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        Payment.objects.create(
            created_at=timezone.now(),
            type=Payment.TPAY,
            amount=36,
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        self.assertEqual(batch.start_date(), timezone.now())

    def test_end_date_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        Payment.objects.create(
            created_at=timezone.now() + datetime.timedelta(days=1),
            type=Payment.TPAY,
            amount=37,
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        Payment.objects.create(
            created_at=timezone.now(),
            type=Payment.TPAY,
            amount=36,
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        self.assertEqual(batch.end_date(), timezone.now() + datetime.timedelta(days=1))

    def test_description_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        self.assertEqual(
            batch.description, "Thalia Pay payments for 2019-1",
        )

    def test_process_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        batch.processed = True
        batch.save()
        self.assertEqual(batch.processing_date, timezone.now())

    def test_total_amount_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        Payment.objects.create(
            created_at=timezone.now() + datetime.timedelta(days=1),
            type=Payment.TPAY,
            amount=37,
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        Payment.objects.create(
            created_at=timezone.now(),
            type=Payment.TPAY,
            amount=36,
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        self.assertEqual(batch.total_amount(), 36 + 37)

    def test_count_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        Payment.objects.create(
            created_at=timezone.now() + datetime.timedelta(days=1),
            type=Payment.TPAY,
            amount=37,
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        Payment.objects.create(
            created_at=timezone.now(),
            type=Payment.TPAY,
            amount=36,
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        self.assertEqual(batch.payments_count(), 2)

    def test_absolute_url(self) -> None:
        b1 = Batch.objects.create(id=1)
        self.assertEqual("/admin/payments/batch/1/change/", b1.get_absolute_url())

    def test_str(self) -> None:
        b1 = Batch.objects.create(id=1)
        self.assertEqual("Thalia Pay payments for 2019-1 (not processed)", str(b1))
        b2 = Batch.objects.create(id=2, processed=True)
        self.assertEqual("Thalia Pay payments for 2019-1 (processed)", str(b2))


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
class BankAccountTest(TestCase):
    """Tests for the BankAccount model."""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.member = PaymentUser.objects.filter(last_name="Wiggers").first()
        cls.no_mandate = BankAccount.objects.create(
            owner=cls.member, initials="J", last_name="Test", iban="NL91ABNA0417164300"
        )
        cls.with_mandate = BankAccount.objects.create(
            owner=cls.member,
            initials="J",
            last_name="Test",
            iban="NL91ABNA0417164300",
            mandate_no="11-1",
            valid_from=timezone.now().date() - timezone.timedelta(days=5),
            signature="base64,png",
        )

    def setUp(self) -> None:
        self.no_mandate.refresh_from_db()
        self.with_mandate.refresh_from_db()

    def test_name(self) -> None:
        """Tests that the property returns initials concatenated with last name."""
        self.assertEqual("J Test", self.no_mandate.name)
        self.no_mandate.initials = "R"
        self.no_mandate.last_name = "Hood"
        self.assertEqual("R Hood", self.no_mandate.name)

    def test_valid(self) -> None:
        """Tests that the property returns the right validity of the mandate."""
        self.assertFalse(self.no_mandate.valid)
        self.assertTrue(self.with_mandate.valid)
        self.with_mandate.valid_until = timezone.now().date()
        self.assertFalse(self.with_mandate.valid)

    def test_can_be_revoked(self) -> None:
        """
        Tests the correct property value for bank accounts that have unprocessed
        or unbatched Thalia Pay payments that hence cannot be revoked by users directly
        """
        self.assertTrue(self.with_mandate.can_be_revoked)
        self.member.refresh_from_db()
        payment = Payment.objects.create(
            paid_by=self.member, type=Payment.TPAY, topic="test", amount=3
        )
        self.assertFalse(self.with_mandate.can_be_revoked)
        batch = Batch.objects.create()
        payment.batch = batch
        payment.save()
        self.assertFalse(self.with_mandate.can_be_revoked)
        batch.processed = True
        batch.save()
        self.assertTrue(self.with_mandate.can_be_revoked)

    def test_str(self) -> None:
        """
        Tests that the output is the IBAN concatenated
        with the name of the owner
        """
        self.assertEqual("NL91ABNA0417164300 - J Test", str(self.no_mandate))

    def test_clean(self) -> None:
        """Tests that the model is validated correctly."""
        self.no_mandate.clean()
        self.with_mandate.clean()

        with self.subTest("Owner required"):
            self.no_mandate.owner = None
            with self.assertRaises(ValidationError):
                self.no_mandate.clean()

        self.no_mandate.refresh_from_db()
        self.with_mandate.refresh_from_db()

        with self.subTest("All mandate fields are non-empty"):
            for field in ["valid_from", "signature", "mandate_no"]:
                val = getattr(self.with_mandate, field)
                setattr(self.with_mandate, field, None)
                with self.assertRaises(ValidationError):
                    self.with_mandate.clean()
                setattr(self.with_mandate, field, val)
                self.with_mandate.clean()

        self.no_mandate.refresh_from_db()
        self.with_mandate.refresh_from_db()

        with self.subTest("Valid until not before valid from"):
            self.with_mandate.valid_until = timezone.now().date() - timezone.timedelta(
                days=6
            )
            with self.assertRaises(ValidationError):
                self.with_mandate.clean()

        self.no_mandate.refresh_from_db()
        self.with_mandate.refresh_from_db()

        with self.subTest("Valid from required to fill valid until"):
            self.with_mandate.valid_until = timezone.now().date()
            self.with_mandate.clean()
            self.with_mandate.valid_from = None
            with self.assertRaises(ValidationError):
                self.with_mandate.clean()

        self.no_mandate.refresh_from_db()
        self.with_mandate.refresh_from_db()

        with self.subTest("BIC required for non-NL IBANs"):
            self.with_mandate.iban = "DE12500105170648489890"
            with self.assertRaises(ValidationError):
                self.with_mandate.clean()
            self.with_mandate.bic = "NBBEBEBB"
            self.with_mandate.clean()


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True, THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
class PaymentUserTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.member = PaymentUser.objects.filter(last_name="Wiggers").first()

    def test_tpay_enabled(self):
        self.assertFalse(self.member.tpay_enabled)
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
        self.assertTrue(self.member.tpay_enabled)

        b.valid_until = timezone.now().date() - timezone.timedelta(days=1)
        b.save()
        self.assertFalse(self.member.tpay_enabled)

    def test_tpay_balance(self):
        self.assertEqual(self.member.tpay_balance, 0)
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
        p1 = services.create_payment(
            MockPayable(MockModel(self.member)), self.member, Payment.TPAY
        )
        self.assertEqual(self.member.tpay_balance, Decimal(-5))

        p2 = services.create_payment(
            MockPayable(MockModel(self.member)), self.member, Payment.TPAY
        )
        self.assertEqual(self.member.tpay_balance, Decimal(-10))

        batch = Batch.objects.create()
        p1.batch = batch
        p1.save()

        p2.batch = batch
        p2.save()

        self.assertEqual(self.member.tpay_balance, Decimal(-10))

        batch.processed = True
        batch.save()

        self.assertEqual(self.member.tpay_balance, 0)

    def test_allow_disallow_tpay(self):
        self.assertTrue(self.member.tpay_allowed)
        self.member.allow_tpay()
        self.assertTrue(self.member.tpay_allowed)
        self.member.disallow_tpay()
        self.member.refresh_from_db()
        self.assertFalse(self.member.tpay_allowed)


class BlacklistedPaymentUserTest(TestCase):
    fixtures = ["members.json"]

    def test_str(self):
        member = PaymentUser.objects.filter(last_name="Wiggers").first()
        member.disallow_tpay()
        self.assertEqual(
            str(member.blacklistedpaymentuser),
            "Thom Wiggers (thom) (blacklisted from using Thalia Pay)",
        )
