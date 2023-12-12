from django.core import mail
from django.test import TestCase, override_settings
from django.utils import timezone

from freezegun import freeze_time

from members.models import Member, Membership
from payments.exceptions import PaymentError
from payments.models import BankAccount, Payment
from payments.services import create_payment
from registrations import services
from registrations.models import Entry, Registration, Renewal


class ServicesTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    @freeze_time("2023-08-25")
    def setUpTestData(cls):
        cls.admin = Member.objects.get(pk=2)
        cls.admin.is_superuser = True
        cls.admin.save()

        cls.member = Member.objects.get(pk=1)
        cls.member.email = "test@example.com"
        cls.member.save()

        cls.membership = cls.member.membership_set.first()
        cls.membership.until = "2023-09-01"
        cls.membership.save()

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

        cls.study_time_member_registration = Registration.objects.create(
            first_name="Foo",
            last_name="Bar",
            email="foobar@example.com",
            programme="computingscience",
            student_number="s1234569",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456789",
            birthday=timezone.now().replace(year=1990, day=1).date(),
            length=Entry.MEMBERSHIP_STUDY,
            contribution=30,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_CONFIRM,
        )

        cls.renewal = Renewal.objects.create(
            member=cls.member,
            length=Entry.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Entry.STATUS_REVIEW,
            contribution=7.5,
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

        mail.outbox = []

        with self.subTest("Already confirmed."):
            with self.assertRaises(ValueError):
                services.confirm_registration(self.member_registration)

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
        with self.subTest("Not in review."):
            with self.assertRaises(ValueError):
                services.reject_registration(self.member_registration, actor=self.admin)

        self.member_registration.status = Entry.STATUS_REVIEW
        self.member_registration.save()

        services.reject_registration(self.member_registration, actor=self.admin)
        self.assertEqual(self.member_registration.status, Entry.STATUS_REJECTED)
        self.assertEqual(len(mail.outbox), 1)

    def test_revert_registration(self):
        with self.subTest("Not accepted or rejected."):
            with self.assertRaises(ValueError):
                services.revert_registration(self.member_registration, actor=self.admin)

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
        with self.subTest("Not accepted."):
            with self.assertRaises(ValueError):
                services.complete_registration(self.member_registration)

        self.member_registration.status = Entry.STATUS_ACCEPTED
        self.member_registration.save()

        with self.subTest("No payment."):
            with self.assertRaises(ValueError):
                services.complete_registration(self.member_registration)

        with self.subTest("Complete member registration when payment is made."):
            # Signal triggers call to complete_registration.
            with freeze_time("2023-08-28"):
                create_payment(self.member_registration, self.admin, Payment.CASH)

            self.member_registration.refresh_from_db()
            self.assertEqual(self.member_registration.status, Entry.STATUS_COMPLETED)
            membership = self.member_registration.membership
            self.assertIsNotNone(membership)
            member = membership.user
            self.assertEqual(member.first_name, "John")
            self.assertEqual(member.last_name, "Doe")
            self.assertEqual(member.username, "jdoe")
            self.assertEqual(
                membership.since,
                timezone.now().replace(year=2023, month=9, day=1).date(),
            )
            self.assertEqual(
                membership.until,
                timezone.now().replace(year=2024, month=9, day=1).date(),
            )
            self.assertEqual(membership.type, Membership.MEMBER)
            self.assertFalse(member.bank_accounts.all().exists())

            self.assertEqual(len(mail.outbox), 1)

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

        self.study_time_member_registration.status = Entry.STATUS_ACCEPTED
        self.study_time_member_registration.save()
        mail.outbox = []

        with self.subTest("Complete study time registration when payment is made."):
            create_payment(
                self.study_time_member_registration, self.admin, Payment.CASH
            )

            self.study_time_member_registration.refresh_from_db()
            self.assertEqual(
                self.study_time_member_registration.status, Entry.STATUS_COMPLETED
            )
            membership = self.study_time_member_registration.membership
            self.assertIsNotNone(membership)
            member = membership.user
            self.assertEqual(member.first_name, "Foo")
            self.assertEqual(member.last_name, "Bar")
            self.assertEqual(member.username, "fbar")
            self.assertEqual(membership.type, Membership.MEMBER)
            self.assertIsNone(membership.until)
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(
                mail.outbox[0].subject,
                "[THALIA] Welcome to Study Association Thalia",
            )

    def test_accept_renewal(self):
        services.accept_renewal(self.renewal, actor=self.admin)

        self.renewal.refresh_from_db()
        self.assertEqual(self.renewal.status, Entry.STATUS_ACCEPTED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "[THALIA] Renewal accepted",
        )

        mail.outbox = []

        with self.subTest("Not in review."):
            with self.assertRaises(ValueError):
                services.accept_renewal(self.renewal, actor=self.admin)

            self.assertEqual(self.renewal.status, Entry.STATUS_ACCEPTED)
            self.assertEqual(len(mail.outbox), 0)

    def test_reject_renewal(self):
        services.reject_renewal(self.renewal, actor=self.admin)

        self.renewal.refresh_from_db()
        self.assertEqual(self.renewal.status, Entry.STATUS_REJECTED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            "[THALIA] Renewal rejected",
        )

        mail.outbox = []

        with self.subTest("Not in review."):
            with self.assertRaises(ValueError):
                services.reject_renewal(self.renewal, actor=self.admin)

            self.assertEqual(self.renewal.status, Entry.STATUS_REJECTED)
            self.assertEqual(len(mail.outbox), 0)

    def test_revert_renewal(self):
        with self.subTest("Not accepted or rejected."):
            with self.assertRaises(ValueError):
                services.revert_renewal(self.member_registration, actor=self.admin)

        self.renewal.status = Entry.STATUS_REJECTED
        self.renewal.save()

        with self.subTest("Revert rejected renewal."):
            services.revert_renewal(self.renewal, actor=self.admin)
            self.assertEqual(self.renewal.status, Entry.STATUS_REVIEW)

        self.renewal.status = Entry.STATUS_ACCEPTED
        self.renewal.save()

        with override_settings(SUSPEND_SIGNALS=True):
            payment = create_payment(self.renewal, self.admin, Payment.CASH)
            # Signals are suspended, so this does not complete the renewal.
            self.renewal.refresh_from_db()
            self.assertEqual(self.renewal.status, Entry.STATUS_ACCEPTED)

        with self.subTest("Revert paid, but somehow not completed renewal."):
            # As of now, it should no longer be possible to create a payment without
            # completing the renewal successfully, but still, revert_renewal
            # should be able to handle this.
            services.revert_renewal(self.renewal, actor=self.admin)
            self.assertEqual(self.renewal.status, Entry.STATUS_REVIEW)
            self.assertFalse(Payment.objects.filter(pk=payment.pk).exists())

    def test_complete_renewal(self):
        with self.subTest("Not accepted."):
            with self.assertRaises(ValueError):
                services.complete_renewal(self.renewal)

        self.renewal.status = Entry.STATUS_ACCEPTED
        self.renewal.save()

        with self.subTest("No payment."):
            with self.assertRaises(ValueError):
                services.complete_renewal(self.renewal)

        with self.subTest("Complete renewal before end of latest membership."):
            with freeze_time("2023-08-27"):
                create_payment(self.renewal, self.admin, Payment.CASH)

            self.renewal.refresh_from_db()
            self.assertEqual(self.renewal.status, Entry.STATUS_COMPLETED)
            membership = self.renewal.membership
            self.assertIsNotNone(membership)
            self.assertEqual(self.member.membership_set.all().count(), 2)

            self.assertEqual(
                membership.since,
                timezone.now().replace(year=2023, month=9, day=1).date(),
            )
            self.assertEqual(
                membership.until,
                timezone.now().replace(year=2024, month=9, day=1).date(),
            )

        # Restore data.
        with freeze_time("2023-08-25"):
            membership.delete()
            self.renewal.delete()
            self.renewal = Renewal.objects.create(
                member=self.member,
                length=Entry.MEMBERSHIP_YEAR,
                membership_type=Membership.MEMBER,
                contribution=7.5,
            )

        self.renewal.status = Entry.STATUS_ACCEPTED
        self.renewal.save()

        with self.subTest("Complete renewal after end of latest membership."):
            with freeze_time("2023-09-10"):
                create_payment(self.renewal, self.admin, Payment.CASH)

            self.renewal.refresh_from_db()
            self.assertEqual(self.renewal.status, Entry.STATUS_COMPLETED)
            membership = self.renewal.membership
            self.assertIsNotNone(membership)

            self.assertEqual(
                membership.since,
                timezone.now().replace(year=2023, month=9, day=10).date(),
            )
            self.assertEqual(
                membership.until,
                timezone.now().replace(year=2024, month=9, day=1).date(),
            )

        # Restore data.
        with freeze_time("2023-08-25"):
            membership.delete()
            self.renewal.delete()
            self.renewal = Renewal.objects.create(
                member=self.member,
                length=Entry.MEMBERSHIP_STUDY,
                membership_type=Membership.MEMBER,
                contribution=22.5,
            )

        self.renewal.status = Entry.STATUS_ACCEPTED
        self.renewal.save()

        with freeze_time("2023-08-27"):
            with self.subTest(
                "Discounted membership upgrade before membership expiry."
            ):
                create_payment(self.renewal, self.admin, Payment.CASH)

                self.renewal.refresh_from_db()
                self.assertEqual(self.renewal.status, Entry.STATUS_COMPLETED)
                membership = self.renewal.membership
                self.assertIsNotNone(membership)
                self.assertEqual(self.membership.pk, membership.pk)
                self.assertIsNone(membership.until)

        # Restore data.
        with freeze_time("2023-08-25"):
            self.membership.until = "2023-09-01"
            self.membership.save()
            self.renewal.delete()
            self.renewal = Renewal.objects.create(
                member=self.member,
                length=Entry.MEMBERSHIP_STUDY,
                membership_type=Membership.MEMBER,
                contribution=22.5,
            )

        self.renewal.status = Entry.STATUS_ACCEPTED
        self.renewal.save()

        with freeze_time("2023-09-10"):
            with self.subTest("Discounted membership upgrade after membership expiry."):
                create_payment(self.renewal, self.admin, Payment.CASH)

                self.renewal.refresh_from_db()
                self.assertEqual(self.renewal.status, Entry.STATUS_COMPLETED)
                membership = self.renewal.membership
                self.assertIsNotNone(membership)
                self.assertEqual(self.membership.pk, membership.pk)
                self.assertIsNone(membership.until)

        # Restore data.
        with freeze_time("2023-08-25"):
            self.membership.until = None
            self.membership.save()
            self.renewal.delete()
            self.renewal = Renewal.objects.create(
                member=self.member,
                length=Entry.MEMBERSHIP_STUDY,
                membership_type=Membership.MEMBER,
                contribution=22.5,
            )

        self.renewal.status = Entry.STATUS_ACCEPTED
        self.renewal.save()

        with freeze_time("2023-09-10"):
            with self.subTest("Already has study-time membership."):
                with self.assertRaises(PaymentError):
                    create_payment(self.renewal, self.admin, Payment.CASH)

            self.renewal.length = Entry.MEMBERSHIP_YEAR
            self.renewal.save()

            with self.subTest("Already has study-time membership."):
                with self.assertRaises(PaymentError):
                    create_payment(self.renewal, self.admin, Payment.CASH)

        # Restore data.
        with freeze_time("2023-09-05"):
            self.membership.until = "2023-09-01"
            self.membership.save()
            self.renewal.delete()
            self.renewal = Renewal.objects.create(
                member=self.member,
                length=Entry.MEMBERSHIP_STUDY,
                membership_type=Membership.MEMBER,
                contribution=30,
            )

        self.renewal.status = Entry.STATUS_ACCEPTED
        self.renewal.save()

        with freeze_time("2023-09-10"):
            with self.subTest("Non-discounted membership upgrade."):
                create_payment(self.renewal, self.admin, Payment.CASH)

                self.renewal.refresh_from_db()
                self.assertEqual(self.renewal.status, Entry.STATUS_COMPLETED)
                membership = self.renewal.membership
                self.assertIsNotNone(membership)
                self.assertNotEqual(self.membership.pk, membership.pk)
                self.assertIsNone(membership.until)

        # Restore data.
        with freeze_time("2023-09-05"):
            membership.delete()
            self.membership.until = "2023-09-01"
            self.membership.type = Membership.BENEFACTOR
            self.membership.save()
            self.renewal.delete()
            self.renewal = Renewal.objects.create(
                member=self.member,
                length=Entry.MEMBERSHIP_YEAR,
                membership_type=Membership.BENEFACTOR,
                contribution=30,
            )

        self.renewal.status = Entry.STATUS_ACCEPTED
        self.renewal.save()

        with freeze_time("2023-09-10"):
            with self.subTest("Complete benefactor renewal."):
                create_payment(self.renewal, self.admin, Payment.CASH)

                self.renewal.refresh_from_db()
                self.assertEqual(self.renewal.status, Entry.STATUS_COMPLETED)
                membership = self.renewal.membership
                self.assertIsNotNone(membership)
                self.assertNotEqual(self.membership.pk, membership.pk)

                self.assertEqual(membership.since, timezone.now().date())
                self.assertEqual(
                    membership.until,
                    timezone.now().replace(year=2024, month=9, day=1).date(),
                )
                self.assertEqual(membership.type, Membership.BENEFACTOR)

    def test_data_minimisation(self):
        with freeze_time("2025-01-01"):
            with self.subTest("No old completed registrations."):
                self.assertEqual(services.execute_data_minimisation(), 0)

        with freeze_time("2024-09-10"):
            self.renewal.status = Entry.STATUS_COMPLETED
            self.renewal.updated_at = timezone.now()
            self.renewal.save()
            self.member_registration.status = Entry.STATUS_COMPLETED
            self.member_registration.updated_at = timezone.now()
            self.member_registration.save()

        self.assertEqual(Registration.objects.count(), 3)
        self.assertEqual(Renewal.objects.count(), 1)

        with freeze_time("2024-09-15"):
            with self.subTest("A recent completed registration and renewal."):
                services.execute_data_minimisation()
                self.assertEqual(Registration.objects.count(), 3)
                self.assertEqual(Renewal.objects.count(), 1)

        with freeze_time("2024-10-15"):
            with self.subTest("Dry run."):
                services.execute_data_minimisation(dry_run=True)
                self.assertEqual(Registration.objects.count(), 3)
                self.assertEqual(Renewal.objects.count(), 1)

            with self.subTest("An old completed registration and renewal."):
                services.execute_data_minimisation()
                self.assertEqual(Registration.objects.count(), 2)
                self.assertEqual(Renewal.objects.count(), 0)
