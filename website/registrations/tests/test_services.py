from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from members.models import Member, Membership
from payments.exceptions import PaymentError
from payments.models import BankAccount, Payment
from payments.services import create_payment
from registrations import services
from registrations.models import Entry, Registration


class ServicesTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        cls.admin = Member.objects.get(pk=1)
        cls.member = Member.objects.get(pk=1)

        cls.member_registration = Registration.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            programme="computingscience",
            student_number="s1234567",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456789",
            birthday=timezone.now().replace(year=1990, day=1).date(),
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.5,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )

        cls.benefactor_registration = Registration.objects.create(
            first_name="Jane",
            last_name="Doe",
            username="janedoe",
            email="janedoe@example.com",
            student_number="s1234568",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456789",
            birthday=timezone.now().replace(year=1990, day=1).date(),
            length=Entry.MEMBERSHIP_YEAR,
            contribution=7.5,
            membership_type=Membership.BENEFACTOR,
            status=Entry.STATUS_CONFIRM,
        )

    def test_confirm_registration(self):
        with self.subTest("Member"):
            self.assertEqual(self.member_registration.status, Entry.STATUS_CONFIRM)
            services.confirm_registration(self.member_registration)
            self.assertEqual(self.member_registration.status, Entry.STATUS_REVIEW)
            self.assertEqual(len(mail.outbox), 1)  # Sends an email to the board.

        mail.outbox = []

        with self.subTest("Benefactor"):
            self.assertEqual(self.benefactor_registration.status, Entry.STATUS_CONFIRM)
            services.confirm_registration(self.benefactor_registration)
            self.assertEqual(self.benefactor_registration.status, Entry.STATUS_REVIEW)
            self.assertEqual(
                len(mail.outbox), 2
            )  # Also sends information about references.

    def test_accept_registration(self):
        with self.subTest("Not in review."):
            with self.assertRaises(ValueError):
                services.accept_registration(self.member_registration, actor=self.admin)

        self.member_registration.status = Entry.STATUS_REVIEW
        self.member_registration.save()

        # Existing member has the default username.
        self.member.username = "jdoe"
        self.member.save()

        with self.subTest("Username not unique"):
            # Raises and does not commit changes. Does not send email.
            with self.assertRaises(ValueError):
                services.accept_registration(self.member_registration, actor=self.admin)

            self.member_registration.refresh_from_db()
            self.assertEqual(self.member_registration.status, Entry.STATUS_REVIEW)
            self.assertEqual(len(mail.outbox), 0)

        self.member_registration.username = "johndoe"
        self.member_registration.save()

        self.member.email = self.member_registration.email
        self.member.save()
        mail.outbox = []

        with self.subTest("Email not unique"):
            # Raises and does not commit changes. Does not send email.
            with self.assertRaises(ValueError):
                services.accept_registration(self.member_registration, actor=self.admin)

            self.member_registration.refresh_from_db()
            self.assertEqual(self.member_registration.status, Entry.STATUS_REVIEW)
            self.assertEqual(len(mail.outbox), 0)

        self.member_registration.email = "unique@example.com"
        self.member_registration.save()
        mail.outbox = []

        with self.subTest("Normal"):
            # Succeeds and sends payment email.
            services.accept_registration(self.member_registration, actor=self.admin)

            self.member_registration.refresh_from_db()
            self.assertEqual(self.member_registration.status, Entry.STATUS_ACCEPTED)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(
                mail.outbox[0].subject,
                "[THALIA] Registration accepted",
            )

        services.revert_registration(self.member_registration, actor=self.admin)

        self.member_registration.direct_debit = True
        self.member_registration.iban = "NL12ABNA1234567890"
        self.member_registration.signature = "base64,png"
        self.member_registration.initials = "J."
        self.member_registration.save()
        mail.outbox = []

        with self.subTest("With Thalia Pay"):
            # Completes the registration, does not send payment email,
            # but sends final email after completing the registration.
            services.accept_registration(self.member_registration, actor=self.admin)

            self.member_registration.refresh_from_db()
            self.assertEqual(self.member_registration.status, Entry.STATUS_COMPLETED)
            self.assertIsNotNone(self.member_registration.membership)
            self.assertIsNotNone(self.member_registration.membership.user)
            member = self.member_registration.membership.user
            self.assertEqual(BankAccount.objects.filter(owner_id=member.id).count(), 1)
            self.assertEqual(self.member_registration.payment.amount, 7.5)
            self.assertEqual(self.member_registration.payment.type, Payment.TPAY)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(
                mail.outbox[0].subject,
                "[THALIA] Welcome to Study Association Thalia",
            )

    def test_reject_registration(self):
        self.member_registration.status = Entry.STATUS_REVIEW
        self.member_registration.save()

        services.reject_registration(self.member_registration, actor=self.admin)
        self.assertEqual(self.member_registration.status, Entry.STATUS_REJECTED)
        self.assertEqual(len(mail.outbox), 1)

    def test_revert_registration(self):
        self.member_registration.status = Entry.STATUS_REJECTED
        self.member_registration.save()
        with self.subTest("Revert rejected registration."):
            services.revert_registration(self.member_registration, actor=self.admin)
            self.assertEqual(self.member_registration.status, Entry.STATUS_REVIEW)

        self.member_registration.status = Entry.STATUS_ACCEPTED
        self.member_registration.save()

        with override_settings(SUSPEND_SIGNALS=True):
            payment = create_payment(self.member_registration, self.admin, Payment.CASH)
            # Signals are suspended, so this does not complete the registration.
            self.member_registration.refresh_from_db()
            self.assertEqual(self.member_registration.status, Entry.STATUS_ACCEPTED)

        with self.subTest("Revert paid, but somehow not completed registration."):
            # As of now, it should no longer be possible to create a payment without
            # completing the registration successfully, but still, revert_registration
            # should be able to handle this.
            services.revert_registration(self.member_registration, actor=self.admin)
            self.assertEqual(self.member_registration.status, Entry.STATUS_REVIEW)
            self.assertFalse(Payment.objects.filter(pk=payment.pk).exists())

    def test_complete_registration(self):
        self.member_registration.status = Entry.STATUS_ACCEPTED
        self.member_registration.save()

        with self.subTest("Complete member registration when payment is made."):
            # Signal triggers call to complete_registration.
            create_payment(self.member_registration, self.admin, Payment.CASH)

            self.member_registration.refresh_from_db()
            self.assertEqual(self.member_registration.status, Entry.STATUS_COMPLETED)
            membership = self.member_registration.membership
            self.assertIsNotNone(membership)
            member = membership.user
            self.assertEqual(member.first_name, "John")
            self.assertEqual(member.last_name, "Doe")
            self.assertEqual(member.username, "jdoe")
            # TODO: check membership since and until.
            # TODO: check bank account.
            # TODO: check sent emails.

        self.benefactor_registration.status = Entry.STATUS_ACCEPTED
        self.benefactor_registration.username = None  # Default 'jdoe' is taken already.
        self.benefactor_registration.save()
        mail.outbox = []

        with self.subTest("Username is not unique."):
            # Signal triggers call to complete_registration, which raises.
            # Creating the payment is rolled back. The registration remains accepted.
            with self.assertRaises(PaymentError):
                create_payment(self.benefactor_registration, self.admin, Payment.CASH)

            self.benefactor_registration.refresh_from_db()
            self.assertEqual(self.benefactor_registration.status, Entry.STATUS_ACCEPTED)
            self.assertIsNone(self.benefactor_registration.payment)
            self.assertEqual(len(mail.outbox), 0)

        self.benefactor_registration.status = Entry.STATUS_ACCEPTED
        self.benefactor_registration.username = "janedoe"
        self.benefactor_registration.save()
        mail.outbox = []

        with self.subTest("Complete benefactor registration when payment is made."):
            # Signal triggers call to complete_registration.
            create_payment(self.benefactor_registration, self.admin, Payment.CASH)

            self.benefactor_registration.refresh_from_db()
            self.assertEqual(
                self.benefactor_registration.status, Entry.STATUS_COMPLETED
            )
            membership = self.benefactor_registration.membership
            self.assertIsNotNone(membership)
            member = membership.user
            self.assertEqual(member.first_name, "Jane")
            self.assertEqual(member.last_name, "Doe")
            self.assertEqual(member.username, "janedoe")
            self.assertEqual(membership.type, Membership.BENEFACTOR)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(
                mail.outbox[0].subject,
                "[THALIA] Welcome to Study Association Thalia",
            )

    def test_accept_renewal(self):
        raise NotImplementedError

    def test_reject_renewal(self):
        raise NotImplementedError

    def test_revert_renewal(self):
        raise NotImplementedError

    def test_complete_renewal(self):
        raise NotImplementedError

    def test_data_minimisation(self):
        raise NotImplementedError
