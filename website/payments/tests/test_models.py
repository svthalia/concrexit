import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from members.models import Member
from payments.models import Payment, BankAccount, Batch, Payable


class PayableTest(TestCase):
    """Tests for the Payable class"""

    def test_payment_amount_not_implemented(self):
        p = Payable()
        with self.assertRaises(NotImplementedError):
            _ = p.payment_amount

    def test_payment_topic_not_implemented(self):
        p = Payable()
        with self.assertRaises(NotImplementedError):
            _ = p.payment_topic

    def test_payment_notes_not_implemented(self):
        p = Payable()
        with self.assertRaises(NotImplementedError):
            _ = p.payment_notes

    def test_payment_payer_not_implemented(self):
        p = Payable()
        with self.assertRaises(NotImplementedError):
            _ = p.payment_payer

    def test_save_not_implemented(self):
        p = Payable()
        with self.assertRaises(NotImplementedError):
            p.save()


@override_settings(SUSPEND_SIGNALS=True)
class PaymentTest(TestCase):
    """Tests for the Payment model"""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.member = Member.objects.filter(last_name="Wiggers").first()
        cls.payment = Payment.objects.create(
            amount=10, paid_by=cls.member, processed_by=cls.member,
        )
        cls.batch = Batch.objects.create()

    def test_change_processed_sets_processing_date(self):
        """
        Tests that the processed date is set when the type of payment is set
        """
        self.payment.type = Payment.NONE
        self.payment.save()
        self.assertFalse(self.payment.processed)
        self.assertIsNone(self.payment.processing_date)
        self.payment.type = Payment.CARD
        self.payment.save()
        self.assertTrue(self.payment.processed)
        self.assertIsNotNone(self.payment.processing_date)

        # Make sure date doesn't change on new save
        date = self.payment.processing_date
        self.payment.save()
        self.assertEqual(self.payment.processing_date, date)

    def test_get_admin_url(self):
        """
        Tests that the right admin url is returned
        """
        self.assertEqual(
            self.payment.get_admin_url(),
            "/admin/payments/payment/{}/change/".format(self.payment.pk),
        )

    def test_add_payment_from_processed_batch_to_new_batch(self) -> None:
        """
        Test that a payment that is in a processed batch cannot be added to another batch
        """
        self.batch.processed = True
        self.batch.save()
        self.payment.type = Payment.TPAY
        self.payment.batch = self.batch
        self.payment.save()

        b = Batch.objects.create()
        self.payment.batch = b
        self.payment.save()

        self.assertEqual(self.payment.batch, self.batch)

    def test_clean(self):
        """
        Tests that non thalia pay payments cannot be added to a batch
        """
        for payment_type in [Payment.NONE, Payment.CASH, Payment.CARD, Payment.WIRE]:
            self.payment.type = payment_type
            self.payment.batch = self.batch
            with self.assertRaises(ValidationError):
                self.payment.clean()

        for payment_type in [Payment.NONE, Payment.CASH, Payment.CARD, Payment.WIRE]:
            self.payment.type = payment_type
            self.payment.batch = None
            self.payment.clean()

        self.payment.type = Payment.TPAY
        self.payment.batch = self.batch
        self.payment.clean()

    def test_str(self) -> None:
        """
        Tests that the output is a description with the amount
        """
        self.assertEqual("Payment of 10", str(self.payment))


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True)
class BatchModelTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.user1 = Member.objects.create(
            pk=1,
            username="test1",
            first_name="Test1",
            last_name="Example",
            email="test1@example.org",
            is_staff=False,
        )
        cls.user2 = Member.objects.create(
            pk=2,
            username="test2",
            first_name="Test2",
            last_name="Example",
            email="test2@example.org",
            is_staff=True,
        )

    def test_start_date_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        payment1 = Payment.objects.create(
            type=Payment.TPAY,
            amount=37,
            processing_date=timezone.now() + datetime.timedelta(days=1),
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        payment2 = Payment.objects.create(
            type=Payment.TPAY,
            amount=36,
            processing_date=timezone.now(),
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        self.assertEqual(batch.start_date, timezone.now())

    def test_end_date_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        payment1 = Payment.objects.create(
            type=Payment.TPAY,
            amount=37,
            processing_date=timezone.now() + datetime.timedelta(days=1),
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        payment2 = Payment.objects.create(
            type=Payment.TPAY,
            amount=36,
            processing_date=timezone.now(),
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        self.assertEqual(batch.end_date, timezone.now() + datetime.timedelta(days=1))

    def test_description_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        now = timezone.now()
        last_month = datetime.datetime(now.year, now.month, 1) - datetime.timedelta(
            days=1
        )
        self.assertEqual(
            batch.description,
            f"your Thalia payments for {last_month.year}-{last_month.month}",
        )

    def test_proccess_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        batch.processed = True
        batch.save()
        self.assertEqual(batch.processing_date, timezone.now())

    def test_total_amount_batch(self) -> None:
        batch = Batch.objects.create(id=1)
        payment1 = Payment.objects.create(
            type=Payment.TPAY,
            amount=37,
            processing_date=timezone.now() + datetime.timedelta(days=1),
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        payment2 = Payment.objects.create(
            type=Payment.TPAY,
            amount=36,
            processing_date=timezone.now(),
            paid_by=self.user1,
            processed_by=self.user2,
            batch=batch,
        )
        self.assertEqual(batch.total_amount, 36 + 37)

    def test_absolute_url(self) -> None:
        b1 = Batch.objects.create(id=1)
        self.assertEqual("/admin/payments/batch/1/change/", b1.get_absolute_url())

    def test_str(self) -> None:
        b1 = Batch.objects.create(id=1)
        self.assertEqual("your Thalia payments for 2018-12 (not processed)", str(b1))
        b2 = Batch.objects.create(id=2, processed=True)
        self.assertEqual("your Thalia payments for 2018-12 (processed)", str(b2))


@freeze_time("2019-01-01")
@override_settings(SUSPEND_SIGNALS=True)
class BankAccountTest(TestCase):
    """Tests for the BankAccount model"""

    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls) -> None:
        cls.member = Member.objects.filter(last_name="Wiggers").first()
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
        """
        Tests that the property returns initials concatenated with last name
        """
        self.assertEqual("J Test", self.no_mandate.name)
        self.no_mandate.initials = "R"
        self.no_mandate.last_name = "Hood"
        self.assertEqual("R Hood", self.no_mandate.name)

    def test_valid(self) -> None:
        """
        Tests that the property returns the right validity of the mandate
        """
        self.assertFalse(self.no_mandate.valid)
        self.assertTrue(self.with_mandate.valid)
        self.with_mandate.valid_until = timezone.now().date()
        self.assertFalse(self.with_mandate.valid)

    def test_str(self) -> None:
        """
        Tests that the output is the IBAN concatenated
        with the name of the owner
        """
        self.assertEqual("NL91ABNA0417164300 - J Test", str(self.no_mandate))

    def test_clean(self) -> None:
        """
        Tests that the model is validated correctly
        """
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
