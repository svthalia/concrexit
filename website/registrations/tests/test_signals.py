from unittest import mock

from django.test import TestCase, override_settings
from django.utils import timezone

from members.models import Member, Membership
from payments.models import Payment
from payments.services import create_payment
from registrations.models import Entry, Registration


@override_settings(THALIA_PAY_ENABLED_PAYMENT_METHOD=True)
class ServicesTest(TestCase):
    fixtures = ["members.json"]

    @classmethod
    def setUpTestData(cls):
        import registrations.signals  # noqa: F401

        cls.registration = Registration.objects.create(
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
        cls.user = Member.objects.filter(last_name="Wiggers").first()

    @mock.patch("registrations.services.process_entry_save")
    def test_post_entry_save(self, process_entry_save):
        self.registration.save()

        process_entry_save.assert_called_with(self.registration)

    def test_entry_save_error(self):
        self.registration.status = Entry.STATUS_ACCEPTED
        with mock.patch(
            "registrations.services.process_entry_save"
        ) as process_entry_save:
            process_entry_save.side_effect = [
                Exception("An exception occurred"),
                mock.DEFAULT,
            ]
            with self.assertRaises(Exception):
                self.registration.save()
            self.registration.refresh_from_db()
            self.assertEqual(Entry.STATUS_REVIEW, self.registration.status)

        self.registration.status = Entry.STATUS_CONFIRM
        self.registration.save()

        with mock.patch(
            "registrations.services.process_entry_save"
        ) as process_entry_save:
            process_entry_save.side_effect = [
                Exception("An exception occurred"),
                mock.DEFAULT,
            ]
            with self.assertRaises(Exception):
                self.registration.save()
            self.registration.refresh_from_db()
            self.assertEqual(Entry.STATUS_CONFIRM, self.registration.status)

        self.registration.status = Entry.STATUS_ACCEPTED
        self.registration.save()

        with mock.patch(
            "registrations.services.process_entry_save"
        ) as process_entry_save:
            process_entry_save.side_effect = [Exception("An exception occurred"), None]
            self.registration.payment = create_payment(
                self.registration, self.user, Payment.CASH
            )
            with self.assertRaises(Exception):
                self.registration.save()
            self.registration.refresh_from_db()
            self.assertEqual(Entry.STATUS_REVIEW, self.registration.status)
            self.assertIsNone(self.registration.payment)
            self.assertQuerysetEqual(Payment.objects.all(), Payment.objects.none())
