from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from members.models import Member
from payments.models import Payment, BankAccount


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

    def test_change_processed_sets_processing_date(self):
        """
        Tests that the processed date is set when the type of payment is set
        """
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

    def test_str(self) -> None:
        """
        Tests that the output is a description with the amount
        """
        self.assertEqual("Payment of 10", str(self.payment))


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
