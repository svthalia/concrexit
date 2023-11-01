from datetime import datetime
from unittest.mock import MagicMock

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from members.models import Membership
from members.models.member import Member
from payments.exceptions import PaymentError
from payments.models import Payment
from payments.payables import payables
from payments.services import create_payment
from registrations.models import Registration, Renewal
from registrations.payables import RegistrationPayable, RenewalPayable


class RenewalPayableTest(TestCase):
    def setUp(self):
        self.model = MagicMock()
        self.model.contribution = 20
        self.model.membership = MagicMock()
        self.model.member = "member"
        self.model.length = Renewal.MEMBERSHIP_YEAR
        self.model.membership_type = Membership.BENEFACTOR
        self.model.created_at = datetime(2018, 3, 4, 12, 0, 0)
        self.model.updated_at = datetime(2018, 3, 5, 12, 0, 0)

        self.payable = RenewalPayable(self.model)

    def test_attributes(self):
        self.assertEqual(self.payable.payment_amount, 20)
        self.assertEqual(self.payable.payment_payer, "member")
        self.assertEqual(
            self.payable.payment_topic, "Membership renewal benefactor (year)"
        )
        self.assertEqual(
            self.payable.payment_notes,
            "Membership renewal benefactor (year). Creation date: March 4, 2018. Completion date: March 5, 2018",
        )
        self.assertFalse(self.payable.can_manage_payment(None))


class RegistrationPayableTest(TestCase):
    fixtures = ["members.json"]

    def setUp(self):
        self.model = MagicMock()
        self.model.contribution = 20
        self.model.membership = MagicMock()
        self.model.membership.user = "member"
        self.model.length = Registration.MEMBERSHIP_YEAR
        self.model.membership_type = Membership.BENEFACTOR
        self.model.created_at = datetime(2018, 3, 4, 12, 0, 0)
        self.model.updated_at = datetime(2018, 3, 5, 12, 0, 0)

        self.payable = RegistrationPayable(self.model)

    def test_attributes(self):
        self.assertEqual(self.payable.payment_amount, 20)
        self.assertEqual(self.payable.payment_payer, "member")
        self.payable.model.membership = None
        self.assertEqual(self.payable.payment_payer, None)
        self.assertEqual(
            self.payable.payment_topic, "Membership registration benefactor (year)"
        )
        self.assertEqual(
            self.payable.payment_notes,
            "Membership registration benefactor (year). Creation date: March 4, 2018. Completion date: March 5, 2018",
        )
        self.assertFalse(self.payable.can_manage_payment(None))

    def test_immutable_fields_after_payment(self):
        payables.register(Registration, RegistrationPayable)
        registration = Registration.objects.create(
            first_name="John",
            last_name="Doe",
            email="johndoe@example.com",
            programme="computingscience",
            starting_year=2014,
            address_street="Heyendaalseweg 135",
            address_street2="",
            address_postal_code="6525AJ",
            address_city="Nijmegen",
            address_country="NL",
            phone_number="06123456789",
            birthday=timezone.now().replace(year=1990),
            length=Registration.MEMBERSHIP_YEAR,
            membership_type=Membership.MEMBER,
            status=Registration.STATUS_ACCEPTED,
            contribution=settings.MEMBERSHIP_PRICES[Registration.MEMBERSHIP_YEAR],
        )

        create_payment(registration, Member.objects.get(pk=1), Payment.CASH)

        registration.contribution = 0

        with self.assertRaises(PaymentError):
            registration.save()
