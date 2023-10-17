from datetime import datetime
from unittest.mock import MagicMock

from django.test import TestCase

from members.models import Membership
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
