from django.core import mail
from django.test import TestCase
from django.utils import timezone

from members.models import Member, Membership
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

        with self.subTest("Username not unique"):
            raise NotImplementedError
            # Raises, and does not commit any changes.

        with self.subTest("Email not unique"):
            raise NotImplementedError
            # Raises, and does not commit any changes.

        with self.subTest("Normal"):
            raise NotImplementedError
            # Changes status and sends email.

        with self.subTest("With Thalia Pay"):
            raise NotImplementedError
            # Completes, does not send payment email.

    def test_reject_registration(self):
        self.member_registration.status = Entry.STATUS_REVIEW
        self.member_registration.save()

        services.reject_registration(self.member_registration, actor=self.admin)
        self.assertEqual(self.member_registration.status, Entry.STATUS_REJECTED)
        self.assertEqual(len(mail.outbox), 1)

    def test_revert_registration(self):
        raise NotImplementedError

    def test_complete_registration(self):
        raise NotImplementedError

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
