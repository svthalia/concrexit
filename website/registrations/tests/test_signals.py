from unittest import mock

from django.test import TestCase
from django.utils import timezone

from members.models import Membership
from registrations.models import Registration, Entry


class ServicesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        import registrations.signals

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

    @mock.patch("registrations.services.process_entry_save")
    def test_post_entry_save(self, process_entry_save):
        self.registration.save()

        process_entry_save.assert_called_with(self.registration)
